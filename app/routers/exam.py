import asyncio
import json
import logging
from datetime import datetime, timezone
from random import sample

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.models import ExamQuestion, PracticeTestAnswer, PracticeTestAttempt
from app.services import fsrs_service
from app.api_key import get_user_api_key
from app.services.claude import generate_exam_explanation
from app.templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter()


async def _prefetch_exam_explanations(question_ids: list[int], api_key: str | None = None) -> None:
    """Background task: generate explanations for exam questions that don't have them yet."""
    if not api_key:
        return
    async with AsyncSessionLocal() as bg_db:
        for qid in question_ids:
            q = await bg_db.get(ExamQuestion, qid)
            if q and q.explanation_json is None:
                try:
                    choices = json.loads(q.choices_json)
                    exp = await generate_exam_explanation(q.question_it, choices, q.correct_index, api_key=api_key)
                    q.explanation_json = json.dumps(exp, ensure_ascii=False)
                    q.generated_at = datetime.now(timezone.utc)
                    await bg_db.commit()
                except Exception as e:
                    logger.error(f"Prefetch exam explanation failed for q{qid}: {e}")

EXAM_DURATION_SECONDS = 40 * 60   # 40 minutes
EXAM_QUESTION_COUNT = 20           # Questions per practice session


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

    # Fire background task to pre-generate explanations for selected questions
    question_ids = [q.id for q in questions]
    user_api_key = get_user_api_key(request)
    asyncio.ensure_future(_prefetch_exam_explanations(question_ids, api_key=user_api_key))

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


@router.get("/exam/submit", response_class=HTMLResponse)
async def exam_submit_get(request: Request):
    """Redirect bookmarks/back-navigation to /exam (submit is POST-only)."""
    return RedirectResponse("/exam", status_code=302)


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

    user_api_key = get_user_api_key(request)
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
                    q.question_it, choices, q.correct_index, api_key=user_api_key
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

    return RedirectResponse(f"/exam/results/{attempt.id}", status_code=303)


@router.get("/exam/results/{attempt_id}", response_class=HTMLResponse)
async def exam_results(
    request: Request,
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Results page for a completed practice test — loadable by GET (bookmark-safe)."""
    attempt = await db.get(PracticeTestAttempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Tentativo non trovato")

    answers_result = await db.execute(
        select(PracticeTestAnswer).where(PracticeTestAnswer.attempt_id == attempt_id)
    )
    answers = {a.question_id: a for a in answers_result.scalars().all()}

    questions_result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.id.in_(answers.keys()))
    )
    questions = {q.id: q for q in questions_result.scalars().all()}

    results_data = []
    for qid, answer in answers.items():
        q = questions.get(qid)
        if q is None:
            continue
        chosen = answer.chosen_index
        is_correct = bool(answer.is_correct) if chosen is not None else False

        choices = json.loads(q.choices_json)
        explanation = json.loads(q.explanation_json) if q.explanation_json else {}

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

    wrong_count = sum(1 for r in results_data if not r["is_correct"] and not r["skipped"])

    exam_context = json.dumps({
        "score": attempt.score or 0,
        "max": len(answers),
        "wrong_count": wrong_count,
        "time_expired": attempt.time_expired,
        "wrong": [r["question_it"][:60] for r in results_data if not r["is_correct"] and not r["skipped"]],
    }, ensure_ascii=False)

    due_count = await fsrs_service.get_due_count(db)
    return templates.TemplateResponse(
        request=request,
        name="exam_results.html",
        context={
            "score": attempt.score or 0,
            "max_score": len(answers),
            "time_expired": attempt.time_expired,
            "results": results_data,
            "attempt_id": attempt.id,
            "wrong_count": wrong_count,
            "active_tab": "exam",
            "due_count": due_count,
            "exam_context": exam_context,
        },
    )


@router.get("/exam/review", response_class=HTMLResponse)
async def exam_review(
    request: Request,
    subject: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Review page — all questions answered incorrectly across all past attempts.
    Shows each wrong question once (most recent incorrect attempt).
    Filterable by subject.
    """
    # Subquery: for each question answered wrong, get most recent attempt date
    wrong_answers = await db.execute(
        select(
            PracticeTestAnswer.question_id,
            func.max(PracticeTestAttempt.submitted_at).label("last_wrong_at"),
            func.count(PracticeTestAnswer.id).label("times_wrong"),
        )
        .join(PracticeTestAttempt, PracticeTestAnswer.attempt_id == PracticeTestAttempt.id)
        .where(PracticeTestAnswer.is_correct == False)  # noqa: E712
        .group_by(PracticeTestAnswer.question_id)
    )
    wrong_rows = wrong_answers.all()

    if not wrong_rows:
        due_count = await fsrs_service.get_due_count(db)
        return templates.TemplateResponse(
            request=request,
            name="exam_review.html",
            context={
                "questions": [],
                "subject_filter": subject,
                "subjects": [],
                "active_tab": "exam",
                "due_count": due_count,
            },
        )

    wrong_qids = {row.question_id: row for row in wrong_rows}

    q_query = select(ExamQuestion).where(ExamQuestion.id.in_(wrong_qids.keys()))
    if subject:
        q_query = q_query.where(ExamQuestion.subject == subject)
    q_result = await db.execute(q_query)
    questions_raw = q_result.scalars().all()

    # Build display data
    questions_data = []
    for q in sorted(questions_raw, key=lambda x: wrong_qids[x.id].last_wrong_at, reverse=True):
        choices = json.loads(q.choices_json)
        explanation = json.loads(q.explanation_json) if q.explanation_json else {}
        wrong_idx = 0
        choices_data = []
        for i, text in enumerate(choices):
            is_correct = i == q.correct_index
            choices_data.append({
                "text": text,
                "is_correct": is_correct,
                "explanation": explanation.get("correct" if is_correct else f"wrong_{wrong_idx}", ""),
            })
            if not is_correct:
                wrong_idx += 1
        questions_data.append({
            "id": q.id,
            "question_it": q.question_it,
            "subject": q.subject,
            "topic_slug": q.topic_slug,
            "choices": choices_data,
            "correct_index": q.correct_index,
            "times_wrong": wrong_qids[q.id].times_wrong,
            "last_wrong_at": wrong_qids[q.id].last_wrong_at,
            "has_explanation": bool(q.explanation_json),
        })

    # Available subjects for filter tabs
    all_subjects_result = await db.execute(
        select(ExamQuestion.subject)
        .where(ExamQuestion.id.in_(wrong_qids.keys()))
        .distinct()
    )
    subjects = sorted([r[0] for r in all_subjects_result.all()])

    due_count = await fsrs_service.get_due_count(db)
    return templates.TemplateResponse(
        request=request,
        name="exam_review.html",
        context={
            "questions": questions_data,
            "subject_filter": subject,
            "subjects": subjects,
            "total_wrong": len(wrong_qids),
            "active_tab": "exam",
            "due_count": due_count,
        },
    )
