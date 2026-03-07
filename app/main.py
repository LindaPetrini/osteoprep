import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database import engine, Base
from app.routers import pages, fragments, review, quiz, exam, progress, chat, section_quiz
from app.templates_config import templates

logger = logging.getLogger(__name__)


async def _ensure_sqlite_compat_columns() -> None:
    """Backfill critical columns when DB migrations were skipped."""
    async with engine.begin() as conn:
        if conn.dialect.name != "sqlite":
            return

        topic_cols = {
            row[1]
            for row in (await conn.execute(text("PRAGMA table_info(topics)"))).fetchall()
        }
        if "content_linda_it" not in topic_cols:
            await conn.execute(text("ALTER TABLE topics ADD COLUMN content_linda_it TEXT"))
            logger.warning("Added missing column topics.content_linda_it at startup")
        if "content_linda_en" not in topic_cols:
            await conn.execute(text("ALTER TABLE topics ADD COLUMN content_linda_en TEXT"))
            logger.warning("Added missing column topics.content_linda_en at startup")

        section_cols = {
            row[1]
            for row in (await conn.execute(text("PRAGMA table_info(section_questions)"))).fetchall()
        }
        if "questions_json" not in section_cols:
            await conn.execute(text("ALTER TABLE section_questions ADD COLUMN questions_json TEXT"))
            logger.warning("Added missing column section_questions.questions_json at startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are managed by Alembic — just verify connection
    # create_all only as fallback if alembic not run yet
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _ensure_sqlite_compat_columns()
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(pages.router)
app.include_router(fragments.router)
app.include_router(review.router)
app.include_router(quiz.router)
app.include_router(exam.router)
app.include_router(progress.router)
app.include_router(chat.router)
app.include_router(section_quiz.router)

# Service worker must be served from root scope
@app.get("/sw.js")
async def service_worker():
    return FileResponse("static/sw.js", media_type="application/javascript",
                        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"})


@app.get("/manifest.json")
async def manifest():
    return FileResponse("static/manifest.json", media_type="application/manifest+json")


@app.get("/.well-known/assetlinks.json")
async def assetlinks():
    return FileResponse("static/assetlinks.json", media_type="application/json",
                        headers={"Access-Control-Allow-Origin": "*"})


# Expose templates on app.state for access from other modules if needed
app.state.templates = templates
