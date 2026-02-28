import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import QuizAttempt, Topic
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

    # Best quiz score per topic slug (single GROUP BY query — no N+1)
    slugs = [t.slug for t in topics]
    if slugs:
        scores_result = await db.execute(
            select(
                QuizAttempt.topic_slug,
                func.max(QuizAttempt.score * 1.0 / QuizAttempt.max_score).label("best_pct"),
            )
            .where(QuizAttempt.topic_slug.in_(slugs))
            .group_by(QuizAttempt.topic_slug)
        )
        best_scores = {row.topic_slug: row.best_pct for row in scores_result}
    else:
        best_scores = {}

    return templates.TemplateResponse(
        request=request,
        name="fragments/topic_list.html",
        context={"topics": topics, "subject": subject, "best_scores": best_scores},
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
