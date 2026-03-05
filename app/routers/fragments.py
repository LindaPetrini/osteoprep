import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SectionQuestion, Topic
from app.services.completion_service import get_batch_completions
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

    slugs = [t.slug for t in topics]
    completions = await get_batch_completions(db, slugs)

    return templates.TemplateResponse(
        request=request,
        name="fragments/topic_list.html",
        context={"topics": topics, "subject": subject, "completions": completions},
    )


@router.get("/search", response_class=HTMLResponse)
async def search_topics(request: Request, q: str = "", db: AsyncSession = Depends(get_db)):
    """HTMX fragment: topic search results. Returns empty response for blank query."""
    if not q.strip():
        return HTMLResponse("")

    q_lower = q.lower().strip()
    result = await db.execute(
        select(Topic).where(
            or_(
                func.lower(Topic.title_it).contains(q_lower),
                func.lower(Topic.title_en).contains(q_lower),
                func.lower(Topic.subject).contains(q_lower),
            )
        ).order_by(Topic.subject, Topic.order_in_subject)
    )
    topics = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="fragments/search_results.html",
        context={"topics": topics, "q": q},
    )


@router.get("/topic/{slug}/content", response_class=HTMLResponse)
async def topic_content_fragment(
    request: Request,
    slug: str,
    lang: str = "it",
    style: str = "linda",
    db: AsyncSession = Depends(get_db),
):
    """
    HTMX fragment: explainer content body.
    - If content is ready: returns rendered markdown.
    - If still generating: returns a polling skeleton (HTMX retries every 2s).
    Language/style toggle also uses this endpoint.
    """
    topic = await db.scalar(select(Topic).where(Topic.slug == slug))
    if topic is None:
        raise HTTPException(status_code=404)

    if lang not in ("it", "en"):
        lang = "it"
    if style not in ("linda", "libro"):
        style = "linda"

    sq_result = await db.execute(
        select(SectionQuestion).where(SectionQuestion.topic_slug == slug)
    )
    section_questions = {
        sq.section_slug: {
            "id": sq.id,
            "question_it": sq.question_it,
            "choices": json.loads(sq.choices_json),
            "choices_json": sq.choices_json,
            "correct_index": sq.correct_index,
            "topic_slug": sq.topic_slug,
            "questions_json": sq.questions_json,
        }
        for sq in sq_result.scalars().all()
    }

    # Fetch section images matched to section headings
    from app.routers.pages import _get_section_images
    from app.templates_config import split_sections
    try:
        active_content = (
            (topic.content_linda_it if lang == "it" else topic.content_linda_en)
            if style == "linda"
            else (topic.content_it if lang == "it" else topic.content_en)
        )
        headings = [s["heading"] for s in split_sections(active_content or "")]
        section_images = await _get_section_images(topic.title_en, headings)
    except Exception:
        section_images = {}

    return templates.TemplateResponse(
        request=request,
        name="fragments/explainer_content.html",
        context={"topic": topic, "lang": lang, "style": style, "section_questions": section_questions, "section_images": section_images},
    )
