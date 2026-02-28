from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct
from datetime import datetime
from app.database import get_db
from app.models import Topic
from app.templates_config import templates
from app.services.claude import generate_explainer
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    """Home page: shows subject list as accordions."""
    subjects_result = await db.execute(
        select(distinct(Topic.subject)).order_by(Topic.subject)
    )
    subjects = subjects_result.scalars().all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"subjects": subjects},
    )


@router.get("/topic/{slug}", response_class=HTMLResponse)
async def topic_page(
    request: Request,
    slug: str,
    lang: str = "it",
    db: AsyncSession = Depends(get_db),
):
    """
    Topic page. Generates explainer on first access, serves from cache on all subsequent visits.
    Generate-once-cache: check DB FIRST, call Claude only when content IS NULL.
    """
    topic = await db.scalar(select(Topic).where(Topic.slug == slug))
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Generate BOTH languages at once on first access (single API call)
    if topic.content_it is None:
        try:
            content_it, content_en = await generate_explainer(topic.title_it, topic.title_en)
            topic.content_it = content_it
            topic.content_en = content_en
            topic.generated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(topic)
            logger.info(f"Generated and cached explainer for: {slug}")
        except Exception as e:
            logger.error(f"Explainer generation failed for '{slug}': {e}")
            # Show error state — do not crash the page
            error_msg = f"Errore nella generazione. Ricarica la pagina per riprovare. ({e})"
            return templates.TemplateResponse(
                request=request,
                name="topic.html",
                context={"topic": topic, "lang": lang, "generation_error": error_msg},
            )

    # Validate lang param
    if lang not in ("it", "en"):
        lang = "it"

    return templates.TemplateResponse(
        request=request,
        name="topic.html",
        context={"topic": topic, "lang": lang},
    )
