import json
import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import distinct, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.models import SectionQuestion, Topic
from app.services.claude import generate_explainer, generate_section_questions
from app.services import fsrs_service
from app.templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter()

# Tracks slugs currently being generated to avoid duplicate API calls
_generating: set[str] = set()
_generating_sq: set[str] = set()


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


async def _generate_section_questions(slug: str) -> None:
    """Background task: generate section questions for a topic."""
    async with AsyncSessionLocal() as db:
        try:
            topic = await db.scalar(select(Topic).where(Topic.slug == slug))
            if topic is None or topic.content_it is None:
                return
            sq_data = await generate_section_questions(slug, topic.title_it, topic.content_it)
            for section_slug, data in sq_data.items():
                sq = SectionQuestion(
                    topic_slug=slug,
                    section_slug=section_slug,
                    question_it=data["question_it"],
                    choices_json=json.dumps(data["choices"], ensure_ascii=False),
                    correct_index=data["correct_index"],
                )
                db.add(sq)
            try:
                await db.commit()
                logger.info(f"Section questions saved for {slug}: {list(sq_data.keys())}")
            except IntegrityError:
                logger.warning(f"Section question race condition for {slug}, rolling back")
                await db.rollback()
        except Exception as e:
            logger.error(f"Section question generation failed for '{slug}': {e}")
        finally:
            _generating_sq.discard(slug)


async def _get_wikipedia_info(title_en: str) -> dict | None:
    """Fetch Wikipedia thumbnail + article URL. Returns None on any failure."""
    import re as _re
    search_title = title_en.replace(" ", "_")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{search_title}",
                headers={"User-Agent": "OsteoPrep/1.0"},
            )
            if r.status_code == 200:
                data = r.json()
                thumb = data.get("thumbnail", {}).get("source")
                if thumb:
                    # Upscale thumbnail to 400px for hero display
                    thumb = _re.sub(r"/\d+px-", "/400px-", thumb)
                return {
                    "image": thumb,
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
    due_count = await fsrs_service.get_due_count(db)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"subjects": subjects, "active_tab": "topics", "due_count": due_count},
    )


@router.get("/topic/{slug}", response_class=HTMLResponse)
async def topic_page(
    request: Request,
    slug: str,
    background_tasks: BackgroundTasks,
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
        background_tasks.add_task(_generate_and_cache, slug)

    # Non-blocking: generate section questions once content exists
    if topic.content_it is not None and slug not in _generating_sq:
        sq_count = await db.scalar(
            select(func.count(SectionQuestion.id)).where(SectionQuestion.topic_slug == slug)
        )
        if sq_count == 0:
            _generating_sq.add(slug)
            background_tasks.add_task(_generate_section_questions, slug)

    # Query existing section questions for inline display
    sq_result = await db.execute(
        select(SectionQuestion).where(SectionQuestion.topic_slug == slug)
    )
    section_questions = {
        sq.section_slug: {
            "id": sq.id,
            "question_it": sq.question_it,
            "choices": json.loads(sq.choices_json),
            "correct_index": sq.correct_index,
            "topic_slug": sq.topic_slug,
        }
        for sq in sq_result.scalars().all()
    }

    # Wikipedia image (3s timeout — optional, never blocks the page)
    wiki = await _get_wikipedia_info(topic.title_en)

    due_count = await fsrs_service.get_due_count(db)
    return templates.TemplateResponse(
        request=request,
        name="topic.html",
        context={
            "topic": topic,
            "lang": lang,
            "wiki": wiki,
            "active_tab": "topics",
            "due_count": due_count,
            "section_questions": section_questions,
        },
    )
