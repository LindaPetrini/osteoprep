import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.database import AsyncSessionLocal, engine, Base
from app.models import Topic
from app.routers import pages, fragments, review, quiz, exam
from app.services.claude import generate_explainer
from app.templates_config import templates

logger = logging.getLogger(__name__)


async def _bulk_generate() -> None:
    """On startup: generate explainers for all topics that don't have content yet."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Topic).where(Topic.content_it.is_(None)))
        missing = result.scalars().all()

    if not missing:
        logger.info("Bulk generate: all topics already have content.")
        return

    logger.info(f"Bulk generate: {len(missing)} topics need content, starting parallel generation...")
    sem = asyncio.Semaphore(5)  # max 5 concurrent Claude calls

    async def _one(topic: Topic) -> None:
        async with sem:
            try:
                content_it, content_en = await generate_explainer(topic.title_it, topic.title_en)
                async with AsyncSessionLocal() as db:
                    t = await db.scalar(select(Topic).where(Topic.slug == topic.slug))
                    if t and t.content_it is None:
                        t.content_it = content_it
                        t.content_en = content_en
                        t.generated_at = datetime.utcnow()
                        await db.commit()
                        logger.info(f"Bulk generate: saved {topic.slug}")
            except Exception as e:
                logger.error(f"Bulk generate failed for '{topic.slug}': {e}")

    await asyncio.gather(*[_one(t) for t in missing])
    logger.info("Bulk generate: complete.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are managed by Alembic — just verify connection
    # create_all only as fallback if alembic not run yet
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Pre-generate all missing topic content in the background
    asyncio.create_task(_bulk_generate())
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(pages.router)
app.include_router(fragments.router)
app.include_router(review.router)
app.include_router(quiz.router)
app.include_router(exam.router)

# Expose templates on app.state for access from other modules if needed
app.state.templates = templates
