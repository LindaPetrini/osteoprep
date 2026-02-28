import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.claude import stream_chat_generator, build_chat_system_prompt

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/chat/stream")
async def chat_stream(
    request: Request,
    q: str = "",
    topic_slug: str = "",
    db: AsyncSession = Depends(get_db),
):
    """
    SSE endpoint for streaming chat responses.
    q: user question (URL-encoded)
    topic_slug: optional topic for context injection (CHAT-03)
    """
    if not q.strip():
        async def empty():
            yield "data: [DONE]\n\n"
        return StreamingResponse(empty(), media_type="text/event-stream")

    system = await build_chat_system_prompt(topic_slug, db)
    return StreamingResponse(
        stream_chat_generator(q, system),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering if ever added
        },
    )
