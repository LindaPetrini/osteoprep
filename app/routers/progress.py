from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.completion_service import get_subject_completion_summary
from app.services.progress_service import get_progress_summary
from app.templates_config import templates

router = APIRouter()


@router.get("/progress", response_class=HTMLResponse)
async def progress_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Progress dashboard — SRS counts and per-subject topic/quiz stats."""
    data = await get_progress_summary(db)
    due_count = data["srs"]["due"]

    # Build completion summary for each subject
    subjects_list = [row.subject for row in data["topics_by_subject"]]
    completion_summary = {
        subject: await get_subject_completion_summary(db, subject)
        for subject in subjects_list
    }

    return templates.TemplateResponse(
        request=request,
        name="progress.html",
        context={
            **data,
            "active_tab": "progress",
            "due_count": due_count,
            "completion_summary": completion_summary,
        },
    )
