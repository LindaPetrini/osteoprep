from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.routers import pages, fragments
from app.templates_config import templates

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are managed by Alembic — just verify connection
    # create_all only as fallback if alembic not run yet
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(pages.router)
app.include_router(fragments.router)

# Expose templates on app.state for access from other modules if needed
app.state.templates = templates
