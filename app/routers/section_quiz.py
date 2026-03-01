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
    db: AsyncSession = Depends(get_db),
):
    """Check a section inline question answer and return result fragment."""
    sq = await db.get(SectionQuestion, sq_id)
    if sq is None or sq.topic_slug != slug:
        raise HTTPException(status_code=404)

    form = await request.form()
    try:
        chosen = int(form.get("answer", -1))
    except (ValueError, TypeError):
        chosen = -1

    choices = json.loads(sq.choices_json)
    is_correct = chosen == sq.correct_index

    return templates.TemplateResponse(
        request=request,
        name="fragments/section_question_result.html",
        context={
            "sq": sq,
            "choices": choices,
            "chosen": chosen,
            "is_correct": is_correct,
        },
    )
