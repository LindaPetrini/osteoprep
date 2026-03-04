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
from app.models import QuizAttempt, SectionQuestion, Topic
from app.services.claude import generate_explainer, generate_linda_explainer, generate_section_questions
from app.services import fsrs_service
from app.services.completion_service import get_topic_completion
from app.templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter()

# Tracks slugs currently being generated to avoid duplicate API calls
_generating: set[str] = set()
_generating_sq: set[str] = set()
_generating_linda: set[str] = set()


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


async def _generate_linda_and_cache(slug: str) -> None:
    """Background task: generate Linda-style explainer with its own DB session."""
    async with AsyncSessionLocal() as db:
        try:
            topic = await db.scalar(select(Topic).where(Topic.slug == slug))
            if topic is None or topic.content_linda_it is not None:
                return
            content_it, content_en = await generate_linda_explainer(topic.title_it, topic.title_en)
            topic.content_linda_it = content_it
            topic.content_linda_en = content_en
            await db.commit()
            logger.info(f"Linda-style generation complete: {slug}")
        except Exception as e:
            logger.error(f"Linda-style generation failed for '{slug}': {e}")
        finally:
            _generating_linda.discard(slug)


async def _generate_section_questions(slug: str) -> None:
    """Background task: generate section questions for a topic."""
    async with AsyncSessionLocal() as db:
        try:
            topic = await db.scalar(select(Topic).where(Topic.slug == slug))
            if topic is None or topic.content_it is None:
                return
            sq_data = await generate_section_questions(slug, topic.title_it, topic.content_it)
            for section_slug, q_data in sq_data.items():
                # q_data is a list of {question_it, choices, correct_index}
                first_q = q_data[0] if isinstance(q_data, list) else q_data
                sq = SectionQuestion(
                    topic_slug=slug,
                    section_slug=section_slug,
                    question_it=first_q["question_it"],
                    choices_json=json.dumps(first_q["choices"], ensure_ascii=False),
                    correct_index=first_q["correct_index"],
                    questions_json=json.dumps(q_data, ensure_ascii=False) if isinstance(q_data, list) else None,
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


async def _get_section_images(title_en: str, max_images: int = 6) -> list[dict]:
    """Fetch multiple Wikipedia images related to a topic via search API.

    Returns a list of {"src": url, "alt": title} dicts for inline section figures.
    """
    import re as _re
    images: list[dict] = []
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            r = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": title_en,
                    "gsrlimit": str(max_images + 4),
                    "prop": "pageimages|info",
                    "piprop": "thumbnail",
                    "pithumbsize": "320",
                    "format": "json",
                    "formatversion": "2",
                },
                headers={"User-Agent": "OsteoPrep/1.0"},
            )
            if r.status_code != 200:
                return []
            data = r.json()
            pages = data.get("query", {}).get("pages", [])
            for page in pages:
                thumb = page.get("thumbnail", {}).get("source")
                if thumb:
                    # Upscale to 320px width
                    thumb = _re.sub(r"/\d+px-", "/320px-", thumb)
                    images.append({
                        "src": thumb,
                        "alt": page.get("title", ""),
                    })
                if len(images) >= max_images:
                    break
    except Exception:
        pass
    return images


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    subjects_result = await db.execute(
        select(distinct(Topic.subject)).order_by(Topic.subject)
    )
    subjects = subjects_result.scalars().all()
    due_count = await fsrs_service.get_due_count(db)

    # Last 3 distinct topic slugs from quiz attempts (most recent first), skip nulls
    recent_slugs_result = await db.execute(
        select(QuizAttempt.topic_slug)
        .where(QuizAttempt.topic_slug.isnot(None))
        .order_by(QuizAttempt.attempted_at.desc())
    )
    seen: set[str] = set()
    recent_slugs: list[str] = []
    for (slug,) in recent_slugs_result:
        if slug not in seen:
            seen.add(slug)
            recent_slugs.append(slug)
        if len(recent_slugs) == 3:
            break

    recent_topics: list[Topic] = []
    for slug in recent_slugs:
        topic = await db.scalar(select(Topic).where(Topic.slug == slug))
        if topic is not None:
            recent_topics.append(topic)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "subjects": subjects,
            "active_tab": "topics",
            "due_count": due_count,
            "recent_topics": recent_topics,
        },
    )


@router.get("/topic/{slug}", response_class=HTMLResponse)
async def topic_page(
    request: Request,
    slug: str,
    background_tasks: BackgroundTasks,
    lang: str = "it",
    style: str = "linda",
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the page immediately. If content is missing, kicks off background
    generation and shows a polling skeleton — HTMX polls /topic/{slug}/content
    every 2s until the content appears.
    """
    if style not in ("linda", "libro"):
        style = "linda"
    topic = await db.scalar(select(Topic).where(Topic.slug == slug))
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    if lang not in ("it", "en"):
        lang = "it"

    # Non-blocking: start generation in background if content missing
    if topic.content_it is None and slug not in _generating:
        _generating.add(slug)
        background_tasks.add_task(_generate_and_cache, slug)

    # Non-blocking: generate Linda-style content if missing
    if topic.content_it is not None and topic.content_linda_it is None and slug not in _generating_linda:
        _generating_linda.add(slug)
        background_tasks.add_task(_generate_linda_and_cache, slug)

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
            "choices_json": sq.choices_json,
            "correct_index": sq.correct_index,
            "topic_slug": sq.topic_slug,
            "questions_json": sq.questions_json,
        }
        for sq in sq_result.scalars().all()
    }

    # Wikipedia image + section figures (optional, never blocks the page)
    wiki, section_images = await _get_wikipedia_info(topic.title_en), []
    try:
        section_images = await _get_section_images(topic.title_en)
    except Exception:
        pass

    completion = await get_topic_completion(db, slug)
    due_count = await fsrs_service.get_due_count(db)

    # Fetch previous and next topics in the same subject for navigation
    prev_topic = await db.scalar(
        select(Topic)
        .where(Topic.subject == topic.subject, Topic.order_in_subject < topic.order_in_subject)
        .order_by(Topic.order_in_subject.desc())
        .limit(1)
    )
    next_topic = await db.scalar(
        select(Topic)
        .where(Topic.subject == topic.subject, Topic.order_in_subject > topic.order_in_subject)
        .order_by(Topic.order_in_subject.asc())
        .limit(1)
    )

    return templates.TemplateResponse(
        request=request,
        name="topic.html",
        context={
            "topic": topic,
            "lang": lang,
            "wiki": wiki,
            "section_images": section_images,
            "active_tab": "topics",
            "due_count": due_count,
            "style": style,
            "section_questions": section_questions,
            "completion": completion,
            "prev_topic": prev_topic,
            "next_topic": next_topic,
        },
    )
