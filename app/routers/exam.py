import json
import logging
from datetime import datetime, timezone
from random import sample

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ExamQuestion, PracticeTestAnswer, PracticeTestAttempt
from app.services import fsrs_service
from app.services.claude import generate_exam_explanation
from app.templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter()

EXAM_DURATION_SECONDS = 90 * 60   # 90 minutes
EXAM_QUESTION_COUNT = 20           # Use all 20 seeded questions (or min of available)


@router.get("/exam", response_class=HTMLResponse)
async def exam_landing(request: Request, db: AsyncSession = Depends(get_db)):
    """Exam landing page — explains format, start button."""
    result = await db.execute(select(ExamQuestion))
    total_questions = len(result.scalars().all())

    # Fetch recent attempt history (last 5)
    history_result = await db.execute(
        select(PracticeTestAttempt)
        .order_by(PracticeTestAttempt.started_at.desc())
        .limit(5)
    )
    history = history_result.scalars().all()

    due_count = await fsrs_service.get_due_count(db)
    return templates.TemplateResponse(
        request=request,
        name="exam.html",
        context={
            "total_questions": total_questions,
            "history": history,
            "exam_duration_minutes": EXAM_DURATION_SECONDS // 60,
            "active_tab": "exam",
            "due_count": due_count,
        },
    )


@router.get("/exam/practice", response_class=HTMLResponse)
async def exam_practice(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Start a timed practice test.
    Randomly samples up to EXAM_QUESTION_COUNT questions.
    Embeds start_time_epoch in form for accurate countdown on slow connections.
    """
    result = await db.execute(select(ExamQuestion))
    all_questions = result.scalars().all()

    if not all_questions:
        due_count = await fsrs_service.get_due_count(db)
        return templates.TemplateResponse(
            request=request,
            name="exam.html",
            context={
                "total_questions": 0,
                "history": [],
                "exam_duration_minutes": EXAM_DURATION_SECONDS // 60,
                "no_questions": True,
                "active_tab": "exam",
                "due_count": due_count,
            },
        )

    questions = sample(all_questions, min(EXAM_QUESTION_COUNT, len(all_questions)))
    questions_data = []
    for q in questions:
        choices = json.loads(q.choices_json)
        questions_data.append({
            "id": q.id,
            "question_it": q.question_it,
            "choices": choices,
        })

    # Server-side start time — used by JS timer for accurate countdown
    start_time_epoch = int(datetime.now(timezone.utc).timestamp())

    due_count = await fsrs_service.get_due_count(db)
    return templates.TemplateResponse(
        request=request,
        name="exam_practice.html",
        context={
            "questions": questions_data,
            "start_time_epoch": start_time_epoch,
            "duration_seconds": EXAM_DURATION_SECONDS,
            "question_count": len(questions_data),
            "active_tab": "exam",
            "due_count": due_count,
        },
    )


@router.post("/exam/submit", response_class=HTMLResponse)
async def exam_submit(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Process exam submission:
    1. Parse form data: answer_{question_id} -> chosen_index, time_expired flag
    2. Create PracticeTestAttempt (before scoring)
    3. Score each question
    4. Generate-once-cache explanations (check explanation_json IS NULL per question)
    5. Save PracticeTestAnswer rows
    6. Update attempt score
    7. Return results page
    """
    form = await request.form()
    time_expired = form.get("time_expired", "0") == "1"

    # Parse submitted answers: form fields named "answer_{question_id}"
    submitted = {}
    for key, value in form.items():
        if key.startswith("answer_"):
            try:
                qid = int(key[7:])
                submitted[qid] = int(value)
            except ValueError:
                pass

    if not submitted:
        # Timer expired with no answers — still create attempt record
        submitted = {}

    question_ids = list(submitted.keys())

    # Load all questions that were in this exam (from hidden question_ids field if present)
    # Fallback: load from submitted answers + hidden field
    all_question_ids_raw = form.get("question_ids", "")
    if all_question_ids_raw:
        try:
            all_question_ids = [int(x) for x in all_question_ids_raw.split(",") if x.strip()]
        except ValueError:
            all_question_ids = question_ids
    else:
        all_question_ids = question_ids

    # Create attempt FIRST (before scoring, for referential integrity)
    now_utc = datetime.now(timezone.utc)
    attempt = PracticeTestAttempt(
        started_at=now_utc,   # approximation — actual start was at GET /exam/practice
        submitted_at=now_utc,
        time_expired=time_expired,
        score=None,           # filled in after scoring
    )
    db.add(attempt)
    await db.flush()   # get attempt.id without committing

    # Load questions and generate/fetch explanations
    result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.id.in_(all_question_ids))
    )
    questions = {q.id: q for q in result.scalars().all()}

    score = 0
    results_data = []
    answer_rows = []

    for qid in all_question_ids:
        q = questions.get(qid)
        if q is None:
            continue
        chosen = submitted.get(qid)   # None = skipped/timed out
        is_correct = chosen is not None and chosen == q.correct_index
        if is_correct:
            score += 1

        choices = json.loads(q.choices_json)

        # Generate-once-cache explanation
        if q.explanation_json is None:
            try:
                explanation = await generate_exam_explanation(
                    q.question_it, choices, q.correct_index
                )
                q.explanation_json = json.dumps(explanation, ensure_ascii=False)
                q.generated_at = datetime.now(timezone.utc)
                await db.flush()
            except Exception as e:
                logger.error(f"Exam explanation generation failed for q{qid}: {e}")
                explanation = {
                    "correct": "Spiegazione non disponibile.",
                    "wrong_0": "Spiegazione non disponibile.",
                    "wrong_1": "Spiegazione non disponibile.",
                    "wrong_2": "Spiegazione non disponibile.",
                }
        else:
            explanation = json.loads(q.explanation_json)

        # Map explanations to choices
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
            "skipped": chosen is None,
            "choices": per_choice_explanations,
        })

        answer_rows.append(PracticeTestAnswer(
            attempt_id=attempt.id,
            question_id=qid,
            chosen_index=chosen,
            is_correct=is_correct if chosen is not None else None,
        ))

    # Persist all answer rows
    for row in answer_rows:
        db.add(row)

    # Update attempt score
    attempt.score = score
    await db.commit()

    due_count = await fsrs_service.get_due_count(db)
    return templates.TemplateResponse(
        request=request,
        name="exam_results.html",
        context={
            "score": score,
            "max_score": len(all_question_ids),
            "time_expired": time_expired,
            "results": results_data,
            "attempt_id": attempt.id,
            "active_tab": "exam",
            "due_count": due_count,
        },
    )
