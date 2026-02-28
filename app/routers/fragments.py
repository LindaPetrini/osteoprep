import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Topic
from app.templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/subjects/{subject}/topics", response_class=HTMLResponse)
async def subject_topics_fragment(
    request: Request,
    subject: str,
    db: AsyncSession = Depends(get_db),
):
    """HTMX fragment: topic list for a subject, lazy-loaded when accordion opens."""
    topics_result = await db.execute(
        select(Topic)
        .where(Topic.subject == subject)
        .order_by(Topic.order_in_subject)
    )
    topics = topics_result.scalars().all()
    return templates.TemplateResponse(
        request=request,
        name="fragments/topic_list.html",
        context={"topics": topics, "subject": subject},
    )


@router.get("/topic/{slug}/content", response_class=HTMLResponse)
async def topic_content_fragment(
    request: Request,
    slug: str,
    lang: str = "it",
    db: AsyncSession = Depends(get_db),
):
    """
    HTMX fragment: explainer content body.
    - If content is ready: returns rendered markdown.
    - If still generating: returns a polling skeleton (HTMX retries every 2s).
    Language toggle also uses this endpoint.
    """
    topic = await db.scalar(select(Topic).where(Topic.slug == slug))
    if topic is None:
        raise HTTPException(status_code=404)

    if lang not in ("it", "en"):
        lang = "it"

    return templates.TemplateResponse(
        request=request,
        name="fragments/explainer_content.html",
        context={"topic": topic, "lang": lang},
    )
