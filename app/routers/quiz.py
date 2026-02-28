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
from app.services import fsrs_service
from app.services.claude import generate_quiz_explanation
from app.templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/topic/{slug}/quiz", response_class=HTMLResponse)
async def quiz_page(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    """Show 5 randomly sampled MCQ questions for the topic."""
    topic = await db.scalar(select(Topic).where(Topic.slug == slug))
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.topic_slug == slug)
    )
    all_questions = result.scalars().all()

    # Handle zero-question state — friendly empty state, never 404 or 500
    if not all_questions:
        due_count = await fsrs_service.get_due_count(db)
        return templates.TemplateResponse(
            request=request,
            name="quiz.html",
            context={
                "topic": topic,
                "questions": [],
                "no_questions": True,
                "active_tab": "topics",
                "due_count": due_count,
            },
        )

    # Randomly sample up to 5 questions
    questions = sample(list(all_questions), min(5, len(all_questions)))

    # Parse choices_json for template rendering
    questions_data = []
    for q in questions:
        choices = json.loads(q.choices_json)
        questions_data.append({
            "id": q.id,
            "question_it": q.question_it,
            "choices": choices,
            "correct_index": q.correct_index,
        })

    due_count = await fsrs_service.get_due_count(db)
    return templates.TemplateResponse(
        request=request,
        name="quiz.html",
        context={
            "topic": topic,
            "questions": questions_data,
            "no_questions": False,
            "active_tab": "topics",
            "due_count": due_count,
        },
    )


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

    # Parse submitted answers: form fields named "answer_{question_id}"
    submitted = {}
    for key, value in form.items():
        if key.startswith("answer_"):
            try:
                qid = int(key[7:])  # strip "answer_"
                submitted[qid] = int(value)
            except ValueError:
                pass

    if not submitted:
        raise HTTPException(status_code=400, detail="No answers submitted")

    # Load questions from DB in submitted order
    question_ids = list(submitted.keys())
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.id.in_(question_ids))
    )
    questions = {q.id: q for q in result.scalars().all()}

    # Score and generate/fetch explanations
    score = 0
    results_data = []

    for qid in question_ids:
        q = questions.get(qid)
        if q is None:
            continue
        chosen = submitted[qid]
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
                await db.flush()  # persist before results render
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

        # Map explanations back to choices in original order
        # wrong_N keys correspond to wrong choices in order, skipping correct_index
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

    # Persist QuizAttempt BEFORE rendering results
    attempt = QuizAttempt(
        topic_slug=slug,
        score=score,
        max_score=len(question_ids),
        attempted_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    await db.commit()

    # Fetch score history (all past attempts for this topic, newest first)
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
            "score": score,
            "max_score": len(question_ids),
            "results": results_data,
            "history": history,
            "active_tab": "topics",
            "due_count": due_count,
        },
    )
