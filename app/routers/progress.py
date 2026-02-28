from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.progress_service import get_progress_summary
from app.templates_config import templates

router = APIRouter()


@router.get("/progress", response_class=HTMLResponse)
async def progress_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Progress dashboard — SRS counts and per-subject topic/quiz stats."""
    data = await get_progress_summary(db)
    due_count = data["srs"]["due"]
    return templates.TemplateResponse(
        request=request,
        name="progress.html",
        context={**data, "active_tab": "progress", "due_count": due_count},
    )
