from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fsrs import Rating
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Flashcard, SRSState
from app.services import fsrs_service
from app.templates_config import templates

router = APIRouter()


@router.get("/review", response_class=HTMLResponse)
async def review_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Start a review session: all due cards."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(SRSState).where(SRSState.due_at <= now).order_by(SRSState.due_at)
    )
    due_states = result.scalars().all()

    due_count = await fsrs_service.get_due_count(db)

    if not due_states:
        return templates.TemplateResponse("review.html", {
            "request": request,
            "due_states": [],
            "total": 0,
            "active_tab": "review",
            "due_count": 0,
        })

    # Load first card
    first_state = due_states[0]
    flashcard = await db.get(Flashcard, first_state.flashcard_id)
    session_ids = [s.id for s in due_states]   # all remaining IDs (incl. first)

    return templates.TemplateResponse("review.html", {
        "request": request,
        "flashcard": flashcard,
        "srs_state": first_state,
        "session_ids": session_ids[1:],    # remaining after first
        "current_index": 1,
        "total": len(due_states),
        "active_tab": "review",
        "due_count": due_count,
    })


@router.get("/review/cards/{srs_state_id}/back", response_class=HTMLResponse)
async def card_back(
    request: Request,
    srs_state_id: int,
    session_ids: str = "",
    current_index: int = 1,
    total: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Return card back fragment (definition + rating buttons)."""
    state = await db.get(SRSState, srs_state_id)
    flashcard = await db.get(Flashcard, state.flashcard_id)
    return templates.TemplateResponse("fragments/card_back.html", {
        "request": request,
        "flashcard": flashcard,
        "srs_state": state,
        "session_ids": session_ids,
        "current_index": current_index,
        "total": total,
    })


@router.post("/review/cards/{srs_state_id}/rate", response_class=HTMLResponse)
async def rate_card(
    request: Request,
    srs_state_id: int,
    rating: int = Form(...),                   # 1=Again, 2=Hard, 3=Good, 4=Easy
    session_ids: str = Form(default=""),       # comma-separated remaining IDs
    current_index: int = Form(...),
    total: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Apply rating, save updated state, return next card or results fragment."""
    # Apply FSRS rating
    rating_enum = Rating(rating)
    state = await db.get(SRSState, srs_state_id)
    updated_json, due_at = fsrs_service.review_card(state.card_json, rating_enum)

    # Persist updated state — CRITICAL: due_at must be UTC-aware
    state.card_json = updated_json
    state.due_at = due_at
    state.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # Advance to next card or show results
    remaining_ids = [int(x) for x in session_ids.split(",") if x.strip()]

    if not remaining_ids:
        # Session complete — return results fragment
        return templates.TemplateResponse("fragments/session_results.html", {
            "request": request,
            "cards_reviewed": total,
            "return_url": "/review",
        })

    # Load next card
    next_id = remaining_ids[0]
    next_state = await db.get(SRSState, next_id)
    next_flashcard = await db.get(Flashcard, next_state.flashcard_id)

    return templates.TemplateResponse("fragments/card_front.html", {
        "request": request,
        "flashcard": next_flashcard,
        "srs_state": next_state,
        "session_ids": remaining_ids[1:],
        "current_index": current_index + 1,
        "total": total,
    })
