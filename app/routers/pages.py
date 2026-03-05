import json
import logging
from datetime import datetime, timezone

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
from app.api_key import get_user_api_key
from app.templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter()

# Tracks slugs currently being generated to avoid duplicate API calls
_generating: set[str] = set()
_generating_sq: set[str] = set()
_generating_linda: set[str] = set()


async def _generate_and_cache(slug: str, api_key: str | None = None) -> None:
    """Background task: generate explainer with its own DB session."""
    if not api_key:
        _generating.discard(slug)
        return
    async with AsyncSessionLocal() as db:
        try:
            topic = await db.scalar(select(Topic).where(Topic.slug == slug))
            if topic is None or topic.content_it is not None:
                return
            content_it, content_en = await generate_explainer(topic.title_it, topic.title_en, api_key=api_key)
            topic.content_it = content_it
            topic.content_en = content_en
            topic.generated_at = datetime.now(timezone.utc)
            await db.commit()
            logger.info(f"Background generation complete: {slug}")
        except Exception as e:
            logger.error(f"Background generation failed for '{slug}': {e}")
        finally:
            _generating.discard(slug)


async def _generate_linda_and_cache(slug: str, api_key: str | None = None) -> None:
    """Background task: generate Linda-style explainer with its own DB session."""
    if not api_key:
        _generating_linda.discard(slug)
        return
    async with AsyncSessionLocal() as db:
        try:
            topic = await db.scalar(select(Topic).where(Topic.slug == slug))
            if topic is None or topic.content_linda_it is not None:
                return
            content_it, content_en = await generate_linda_explainer(topic.title_it, topic.title_en, api_key=api_key)
            topic.content_linda_it = content_it
            topic.content_linda_en = content_en
            await db.commit()
            logger.info(f"Linda-style generation complete: {slug}")
        except Exception as e:
            logger.error(f"Linda-style generation failed for '{slug}': {e}")
        finally:
            _generating_linda.discard(slug)


async def _generate_section_questions(slug: str, api_key: str | None = None) -> None:
    """Background task: generate section questions for a topic."""
    if not api_key:
        _generating_sq.discard(slug)
        return
    async with AsyncSessionLocal() as db:
        try:
            topic = await db.scalar(select(Topic).where(Topic.slug == slug))
            if topic is None or topic.content_it is None:
                return
            sq_data = await generate_section_questions(slug, topic.title_it, topic.content_it, api_key=api_key)
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
                    thumb = _re.sub(r"/\d+px-", "/560px-", thumb)
                return {
                    "image": thumb,
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
                    "title": data.get("title", title_en),
                }
    except Exception:
        pass
    return None


def _extract_search_keyword(heading: str) -> str | None:
    """Extract a searchable biology keyword from an Italian section heading.

    Strips Italian articles, takes the part before ':' (the concept, not the
    metaphor), and filters out meta-section headings.
    """
    import re as _re

    _skip_patterns = {
        "dati da ricordare", "focus esame", "connessioni con altri argomenti",
        "come funziona tutto insieme", "riepilogo", "riassunto",
        "cosa succede senza", "come funziona", "perch",
    }

    lower = heading.lower().strip()
    for skip in _skip_patterns:
        if lower.startswith(skip):
            return None

    # Take part before colon (the concept, not the metaphor)
    key = heading.split(":")[0].strip()
    # Strip Italian articles: Il, La, Le, I, Lo, Gli, L', L + space
    key = _re.sub(r"^(Il|La|Le|I|Lo|Gli|L['\u2019 ])\s*", "", key, flags=_re.IGNORECASE).strip()
    # Strip leading "Perche/Perché (la/il/...)"
    key = _re.sub(r"^Perch[eé]\s+", "", key, flags=_re.IGNORECASE).strip()
    key = _re.sub(r"^(il|la|le|i|lo|gli|l['\u2019 ])\s*", "", key, flags=_re.IGNORECASE).strip()

    # Skip if too short or too generic
    if len(key) < 4:
        return None
    return key


async def _get_section_images(
    title_en: str, section_headings: list[str] | None = None
) -> dict[int, dict]:
    """Fetch Wikimedia Commons images matched to specific section headings.

    Extracts the biology keyword from each Italian heading, searches Commons
    in parallel, and returns a dict mapping section index → {"src", "alt"}.
    """
    import asyncio

    if not section_headings:
        return {}

    async def _fetch_one(client: httpx.AsyncClient, keyword: str) -> dict | None:
        """Find the best image for a biology keyword via Italian Wikipedia."""
        import re as _re

        # Words that indicate a biology/science article
        _bio_hints = {
            "cell", "cellu", "organi", "biolog", "chimic", "molecol",
            "protein", "enzim", "membran", "nucle", "cromoso", "gene",
            "mitocond", "ribosom", "citoplas", "metabol", "osmosi",
            "fotosintet", "respira", "aminoacid", "lipid", "DNA", "RNA",
            "divisione", "replicaz", "sintesi", "tessut", "anatomia",
        }

        def _is_biology(data: dict) -> bool:
            """Check if article description/extract suggests biology content."""
            text = (data.get("description", "") + " " + data.get("extract", "")).lower()
            return any(hint in text for hint in _bio_hints)

        async def _try_rest(term: str, require_bio: bool = False) -> dict | None:
            """Direct article lookup — fast, returns curated main image."""
            slug = term.replace(" ", "_")
            r = await client.get(
                f"https://it.wikipedia.org/api/rest_v1/page/summary/{slug}",
                headers={"User-Agent": "OsteoPrep/1.0"},
            )
            if r.status_code != 200:
                return None
            data = r.json()
            thumb = data.get("thumbnail", {}).get("source")
            if not thumb or ".tif" in thumb.lower():
                return None
            if require_bio and not _is_biology(data):
                return None
            thumb = _re.sub(r"/\d+px-", "/400px-", thumb)
            return {"src": thumb, "alt": data.get("title", "")}

        def _singular_variants(kw: str) -> list[str]:
            """Generate Italian singular forms for common biology plurals."""
            variants = []
            # Handle "X e Y" compounds — try each part as singular
            if " e " in kw:
                parts = [p.strip() for p in kw.split(" e ", 1)]
                for p in parts:
                    for s in _singular_variants(p):
                        variants.append(s)
                return variants
            # Common Italian plural→singular rules for biology
            if kw.endswith("i"):
                variants.append(kw[:-1] + "o")   # mitocondri → mitocondrio
                variants.append(kw[:-1] + "a")   # lisosomi → lisosoma
                variants.append(kw[:-1] + "e")   # gradienti → gradiente
            return variants

        try:
            # Try disambiguated forms first (always biology), then plain keyword with bio check
            for term in [f"{keyword} (biologia)", f"{keyword} cellulare"]:
                result = await _try_rest(term)
                if result:
                    return result
            # Try plain keyword + singular variants, but require biology content
            for term in [keyword, *_singular_variants(keyword)]:
                result = await _try_rest(term, require_bio=True)
                if result:
                    return result
            return None
        except Exception:
            return None

    result: dict[int, dict] = {}
    async with httpx.AsyncClient(timeout=4.0) as client:
        tasks = []
        indices = []
        for i, heading in enumerate(section_headings):
            if not heading:  # intro section
                continue
            keyword = _extract_search_keyword(heading)
            if not keyword:
                continue
            tasks.append(_fetch_one(client, keyword))
            indices.append(i)

        images = await asyncio.gather(*tasks, return_exceptions=True)
        seen_srcs: set[str] = set()
        for idx, img in zip(indices, images):
            if isinstance(img, dict) and img.get("src") and img["src"] not in seen_srcs:
                seen_srcs.add(img["src"])
                result[idx] = img

    return result


@router.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse(request=request, name="privacy.html")


@router.get("/settings", response_class=HTMLResponse)
async def settings(request: Request, db: AsyncSession = Depends(get_db)):
    due_count = await fsrs_service.get_due_count(db)
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={"active_tab": "settings", "due_count": due_count},
    )


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

    user_api_key = get_user_api_key(request)

    # Non-blocking: start generation in background if content missing
    if topic.content_it is None and slug not in _generating:
        _generating.add(slug)
        background_tasks.add_task(_generate_and_cache, slug, api_key=user_api_key)

    # Non-blocking: generate Linda-style content if missing
    if topic.content_it is not None and topic.content_linda_it is None and slug not in _generating_linda:
        _generating_linda.add(slug)
        background_tasks.add_task(_generate_linda_and_cache, slug, api_key=user_api_key)

    # Non-blocking: generate section questions once content exists
    if topic.content_it is not None and slug not in _generating_sq:
        sq_count = await db.scalar(
            select(func.count(SectionQuestion.id)).where(SectionQuestion.topic_slug == slug)
        )
        if sq_count == 0:
            _generating_sq.add(slug)
            background_tasks.add_task(_generate_section_questions, slug, api_key=user_api_key)

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
    wiki, section_images = await _get_wikipedia_info(topic.title_en), {}
    try:
        # Extract section headings from the active content for targeted image search
        from app.templates_config import split_sections
        active_content = (
            (topic.content_linda_it if lang == "it" else topic.content_linda_en)
            if style == "linda"
            else (topic.content_it if lang == "it" else topic.content_en)
        )
        headings = [s["heading"] for s in split_sections(active_content or "")]
        section_images = await _get_section_images(topic.title_en, headings)
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
