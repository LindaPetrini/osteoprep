from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.database import get_db
from app.models import Topic
from app.templates_config import templates
from app.services.claude import generate_explainer
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/subjects/{subject}/topics", response_class=HTMLResponse)
async def subject_topics_fragment(
    request: Request,
    subject: str,
    db: AsyncSession = Depends(get_db),
):
    """HTMX fragment: list of topics for a subject (lazy-loaded when accordion opens)."""
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
    HTMX fragment: returns only the explainer content body for language toggle.
    Same generate-if-missing logic as the full page route.
    """
    topic = await db.scalar(select(Topic).where(Topic.slug == slug))
    if topic is None:
        raise HTTPException(status_code=404)

    # Generate if missing (may happen if user hits content fragment directly)
    if topic.content_it is None:
        try:
            content_it, content_en = await generate_explainer(topic.title_it, topic.title_en)
            topic.content_it = content_it
            topic.content_en = content_en
            topic.generated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(topic)
        except Exception as e:
            logger.error(f"Fragment generation failed for '{slug}': {e}")

    if lang not in ("it", "en"):
        lang = "it"

    return templates.TemplateResponse(
        request=request,
        name="fragments/explainer_content.html",
        context={"topic": topic, "lang": lang},
    )
