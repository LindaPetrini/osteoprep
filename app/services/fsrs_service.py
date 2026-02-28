"""
FSRS spaced repetition service.

Module-level singleton scheduler with maximum_interval=7 (product requirement:
no card scheduled beyond exam window).
"""
from datetime import datetime, timezone

from fsrs import Card, Rating, Scheduler
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SRSState

_scheduler = Scheduler(
    desired_retention=0.9,
    maximum_interval=7,        # PRODUCT REQUIREMENT: keep reviews within exam window
    enable_fuzzing=False,      # Deterministic for small queue
)


def review_card(card_json: str, rating: Rating) -> tuple[str, datetime]:
    """Apply rating to card. Returns (updated_card_json, due_date_utc)."""
    card = Card.from_json(card_json)
    card, _ = _scheduler.review_card(card, rating)
    return card.to_json(), card.due   # card.due is timezone-aware UTC


def new_card_json() -> str:
    """Create fresh card JSON for a new flashcard."""
    return Card().to_json()


async def get_due_count(db: AsyncSession) -> int:
    """Count flashcards due now (for badge on Review tab)."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(func.count()).select_from(SRSState).where(SRSState.due_at <= now)
    )
    return result.scalar_one()
