import json
import logging
from datetime import datetime, timezone
from random import sample

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import QuizAttempt, QuizQuestion, Topic

VALID_SUBJECTS = {"biology", "chemistry", "physics", "logic"}
SUBJECT_NAMES = {
    "biology": "Biologia",
    "chemistry": "Chimica",
    "physics": "Fisica e Matematica",
    "logic": "Logica",
}
from app.services import fsrs_service
from app.services.claude import generate_quiz_explanation
from app.templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter()


def _parse_questions(questions: list) -> list[dict]:
    """Parse a list of QuizQuestion ORM objects into template-ready dicts."""
    return [
        {
            "id": q.id,
            "question_it": q.question_it,
            "choices": json.loads(q.choices_json),
            "correct_index": q.correct_index,
        }
        for q in questions
    ]


async def _score_quiz(submitted: dict, questions: dict) -> tuple[int, list[dict]]:
    """Score submitted answers against questions. Returns (score, results_data)."""
    score = 0
    results_data = []
    for qid in submitted:
        q = questions.get(qid)
        if q is None:
            continue
        chosen = submitted[qid]
        is_correct = chosen == q.correct_index
        if is_correct:
            score += 1
        choices = json.loads(q.choices_json)
        results_data.append({
            "q": q,
            "chosen": chosen,
            "is_correct": is_correct,
            "choices_raw": choices,
        })
    return score, results_data


@router.get("/topic/{slug}/quiz", response_class=HTMLResponse)
async def quiz_page(request: Request, slug: str, count: int = 5, db: AsyncSession = Depends(get_db)):
    """Show randomly sampled MCQ questions for the topic. count param: 2-5."""
    count = max(2, min(5, count))
    topic = await db.scalar(select(Topic).where(Topic.slug == slug))
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.topic_slug == slug)
    )
    all_questions = result.scalars().all()

    due_count = await fsrs_service.get_due_count(db)

    # Handle zero-question state — friendly empty state, never 404 or 500
    if not all_questions:
        return templates.TemplateResponse(
            request=request,
            name="quiz.html",
            context={
                "topic": topic,
                "quiz_title": f"Quiz: {topic.title_it}",
                "questions": [],
                "no_questions": True,
                "question_count": 0,
                "active_tab": "topics",
                "due_count": due_count,
                "back_url": f"/topic/{slug}",
                "quiz_submit_url": f"/topic/{slug}/quiz/submit",
                "retry_url": f"/topic/{slug}/quiz",
            },
        )

    questions = sample(list(all_questions), min(count, len(all_questions)))
    questions_data = _parse_questions(questions)

    return templates.TemplateResponse(
        request=request,
        name="quiz.html",
        context={
            "topic": topic,
            "quiz_title": f"Quiz: {topic.title_it}",
            "questions": questions_data,
            "no_questions": False,
            "question_count": len(questions_data),
            "active_tab": "topics",
            "due_count": due_count,
            "back_url": f"/topic/{slug}",
            "quiz_submit_url": f"/topic/{slug}/quiz/submit",
            "retry_url": f"/topic/{slug}/quiz",
        },
    )


async def _build_results_data(
    submitted: dict,
    questions: dict,
    db,
) -> tuple[int, list[dict]]:
    """Score answers and generate/fetch explanations. Returns (score, results_data)."""
    score = 0
    results_data = []

    for qid, chosen in submitted.items():
        q = questions.get(qid)
        if q is None:
            continue
        is_correct = chosen == q.correct_index
        if is_correct:
            score += 1

        choices = json.loads(q.choices_json)

        # Generate-once-cache: only call Claude if explanation_json is NULL
        if q.explanation_json is None:
            try:
                explanation = await generate_quiz_explanation(
                    q.question_it, choices, q.correct_index
                )
                q.explanation_json = json.dumps(explanation, ensure_ascii=False)
                q.generated_at = datetime.now(timezone.utc)
                await db.flush()
            except Exception as e:
                logger.error(f"Quiz explanation generation failed for q{qid}: {e}")
                explanation = {
                    "correct": "Spiegazione non disponibile.",
                    "wrong_0": "Spiegazione non disponibile.",
                    "wrong_1": "Spiegazione non disponibile.",
                    "wrong_2": "Spiegazione non disponibile.",
                }
        else:
            explanation = json.loads(q.explanation_json)

        wrong_idx = 0
        per_choice_explanations = []
        for i, choice_text in enumerate(choices):
            if i == q.correct_index:
                per_choice_explanations.append({
                    "text": choice_text,
                    "is_correct": True,
                    "is_chosen": chosen == i,
                    "explanation": explanation.get("correct", ""),
                })
            else:
                per_choice_explanations.append({
                    "text": choice_text,
                    "is_correct": False,
                    "is_chosen": chosen == i,
                    "explanation": explanation.get(f"wrong_{wrong_idx}", ""),
                })
                wrong_idx += 1

        results_data.append({
            "question_it": q.question_it,
            "chosen_index": chosen,
            "correct_index": q.correct_index,
            "is_correct": is_correct,
            "choices": per_choice_explanations,
        })

    return score, results_data


@router.post("/topic/{slug}/quiz/submit", response_class=HTMLResponse)
async def quiz_submit(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    """
    Process quiz submission:
    1. Parse submitted answers from form data (answer_{question_id} -> chosen_index)
    2. Score the quiz
    3. Generate-once-cache explanations for each question (check explanation_json IS NULL)
    4. Save QuizAttempt to DB
    5. Return results page with per-question breakdown and score history
    """
    topic = await db.scalar(select(Topic).where(Topic.slug == slug))
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    form = await request.form()

    submitted = {}
    for key, value in form.items():
        if key.startswith("answer_"):
            try:
                qid = int(key[7:])
                submitted[qid] = int(value)
            except ValueError:
                pass

    if not submitted:
        raise HTTPException(status_code=400, detail="No answers submitted")

    question_ids = list(submitted.keys())
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.id.in_(question_ids))
    )
    questions = {q.id: q for q in result.scalars().all()}

    score, results_data = await _build_results_data(submitted, questions, db)

    attempt = QuizAttempt(
        topic_slug=slug,
        score=score,
        max_score=len(question_ids),
        attempted_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    await db.commit()

    history_result = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.topic_slug == slug)
        .order_by(QuizAttempt.attempted_at.desc())
        .limit(10)
    )
    history = history_result.scalars().all()

    due_count = await fsrs_service.get_due_count(db)
    return templates.TemplateResponse(
        request=request,
        name="quiz_results.html",
        context={
            "topic": topic,
            "quiz_title": f"Risultati: {topic.title_it}",
            "score": score,
            "max_score": len(question_ids),
            "results": results_data,
            "history": history,
            "active_tab": "topics",
            "due_count": due_count,
            "back_url": f"/topic/{slug}",
            "retry_url": f"/topic/{slug}/quiz",
        },
    )


@router.get("/subject/{subject}/quiz", response_class=HTMLResponse)
async def subject_quiz_page(
    request: Request,
    subject: str,
    count: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Show randomly sampled MCQ questions from all topics in a subject."""
    if subject not in VALID_SUBJECTS:
        raise HTTPException(status_code=404, detail="Subject not found")

    count = max(2, min(10, count))
    subject_name = SUBJECT_NAMES.get(subject, subject)

    result = await db.execute(
        select(QuizQuestion)
        .join(Topic, QuizQuestion.topic_slug == Topic.slug)
        .where(Topic.subject == subject)
    )
    all_questions = result.scalars().all()

    due_count = await fsrs_service.get_due_count(db)

    if not all_questions:
        return templates.TemplateResponse(
            request=request,
            name="quiz.html",
            context={
                "topic": None,
                "quiz_title": f"Quiz {subject_name}",
                "questions": [],
                "no_questions": True,
                "question_count": 0,
                "active_tab": "topics",
                "due_count": due_count,
                "back_url": "/",
                "quiz_submit_url": f"/subject/{subject}/quiz/submit",
                "retry_url": f"/subject/{subject}/quiz",
            },
        )

    questions = sample(list(all_questions), min(count, len(all_questions)))
    questions_data = _parse_questions(questions)

    return templates.TemplateResponse(
        request=request,
        name="quiz.html",
        context={
            "topic": None,
            "quiz_title": f"Quiz {subject_name} — {len(questions_data)} domande miste",
            "questions": questions_data,
            "no_questions": False,
            "question_count": len(questions_data),
            "active_tab": "topics",
            "due_count": due_count,
            "back_url": "/",
            "quiz_submit_url": f"/subject/{subject}/quiz/submit",
            "retry_url": f"/subject/{subject}/quiz",
        },
    )


@router.post("/subject/{subject}/quiz/submit", response_class=HTMLResponse)
async def subject_quiz_submit(
    request: Request,
    subject: str,
    db: AsyncSession = Depends(get_db),
):
    """Process subject-level quiz submission."""
    if subject not in VALID_SUBJECTS:
        raise HTTPException(status_code=404, detail="Subject not found")

    subject_name = SUBJECT_NAMES.get(subject, subject)

    form = await request.form()
    submitted = {}
    for key, value in form.items():
        if key.startswith("answer_"):
            try:
                qid = int(key[7:])
                submitted[qid] = int(value)
            except ValueError:
                pass

    if not submitted:
        raise HTTPException(status_code=400, detail="No answers submitted")

    question_ids = list(submitted.keys())
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.id.in_(question_ids))
    )
    questions = {q.id: q for q in result.scalars().all()}

    score, results_data = await _build_results_data(submitted, questions, db)

    attempt = QuizAttempt(
        topic_slug=None,
        subject=subject,
        score=score,
        max_score=len(question_ids),
        attempted_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    await db.commit()

    history_result = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.subject == subject)
        .where(QuizAttempt.topic_slug.is_(None))
        .order_by(QuizAttempt.attempted_at.desc())
        .limit(10)
    )
    history = history_result.scalars().all()

    due_count = await fsrs_service.get_due_count(db)
    return templates.TemplateResponse(
        request=request,
        name="quiz_results.html",
        context={
            "topic": None,
            "quiz_title": f"Risultati Quiz {subject_name}",
            "score": score,
            "max_score": len(question_ids),
            "results": results_data,
            "history": history,
            "active_tab": "topics",
            "due_count": due_count,
            "back_url": "/",
            "retry_url": f"/subject/{subject}/quiz",
        },
    )
