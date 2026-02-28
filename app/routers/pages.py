import asyncio
import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.models import Topic
from app.services.claude import generate_explainer
from app.templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter()

# Tracks slugs currently being generated to avoid duplicate API calls
_generating: set[str] = set()


async def _generate_and_cache(slug: str) -> None:
    """Background task: generate explainer with its own DB session."""
    async with AsyncSessionLocal() as db:
        try:
            topic = await db.scalar(select(Topic).where(Topic.slug == slug))
            if topic is None or topic.content_it is not None:
                return
            content_it, content_en = await generate_explainer(topic.title_it, topic.title_en)
            topic.content_it = content_it
            topic.content_en = content_en
            topic.generated_at = datetime.utcnow()
            await db.commit()
            logger.info(f"Background generation complete: {slug}")
        except Exception as e:
            logger.error(f"Background generation failed for '{slug}': {e}")
        finally:
            _generating.discard(slug)


async def _get_wikipedia_info(title_en: str) -> dict | None:
    """Fetch Wikipedia thumbnail + article URL. Returns None on any failure."""
    search_title = title_en.replace(" ", "_")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{search_title}",
                headers={"User-Agent": "OsteoPrep/1.0"},
            )
            if r.status_code == 200:
                data = r.json()
                return {
                    "image": data.get("thumbnail", {}).get("source"),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
                    "title": data.get("title", title_en),
                }
    except Exception:
        pass
    return None


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
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
    Returns the page immediately. If content is missing, kicks off background
    generation and shows a polling skeleton — HTMX polls /topic/{slug}/content
    every 2s until the content appears.
    """
    topic = await db.scalar(select(Topic).where(Topic.slug == slug))
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    if lang not in ("it", "en"):
        lang = "it"

    # Non-blocking: start generation in background if content missing
    if topic.content_it is None and slug not in _generating:
        _generating.add(slug)
        asyncio.create_task(_generate_and_cache(slug))

    # Wikipedia image (3s timeout — optional, never blocks the page)
    wiki = await _get_wikipedia_info(topic.title_en)

    return templates.TemplateResponse(
        request=request,
        name="topic.html",
        context={"topic": topic, "lang": lang, "wiki": wiki},
    )
