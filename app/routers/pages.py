from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct
from app.database import get_db
from app.models import Topic
from app.templates_config import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    subjects = (await db.execute(
        select(distinct(Topic.subject)).order_by(Topic.subject)
    )).scalars().all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"subjects": subjects},
    )
