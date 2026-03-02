import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SectionQuestion
from app.templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/topic/{slug}/section-check/{sq_id}", response_class=HTMLResponse)
async def section_check(
    request: Request,
    slug: str,
    sq_id: int,
    q_index: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Check a section inline question answer and return result fragment.

    q_index selects which question from questions_json to evaluate (0-based).
    Falls back to legacy single question when questions_json is null.
    """
    sq = await db.get(SectionQuestion, sq_id)
    if sq is None or sq.topic_slug != slug:
        raise HTTPException(status_code=404)

    # Determine which question to evaluate
    if sq.questions_json:
        questions = json.loads(sq.questions_json)
        if q_index >= len(questions):
            raise HTTPException(status_code=400, detail="Invalid question index")
        q_data = questions[q_index]
        question_it = q_data["question_it"]
        choices = q_data["choices"]
        correct_index = q_data["correct_index"]
    else:
        # Legacy single question
        question_it = sq.question_it
        choices = json.loads(sq.choices_json)
        correct_index = sq.correct_index

    form = await request.form()
    try:
        chosen = int(form.get("answer", -1))
    except (ValueError, TypeError):
        chosen = -1

    is_correct = chosen == correct_index

    return templates.TemplateResponse(
        request=request,
        name="fragments/section_question_result.html",
        context={
            "sq": sq,
            "q_index": q_index,
            "question_it": question_it,
            "choices": choices,
            "chosen": chosen,
            "correct_index": correct_index,
            "is_correct": is_correct,
            "topic_slug": slug,
        },
    )
