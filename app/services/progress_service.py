"""
Progress service — aggregate statistics for the /progress dashboard.

Returns:
  - topics_by_subject: list of Row(subject, total, generated)
  - quiz_by_subject:   dict[subject -> Row(subject, attempts, avg_accuracy)]
  - srs:               dict with due/learned/new/total counts
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Flashcard, QuizAttempt, SRSState, Topic
from app.services import fsrs_service


async def get_progress_summary(db: AsyncSession) -> dict:
    """Return aggregated progress data for the dashboard."""

    # Query 1: topics by subject — total count and generated count
    topics_result = await db.execute(
        select(
            Topic.subject,
            func.count(Topic.id).label("total"),
            func.count(Topic.content_it).label("generated"),
        )
        .group_by(Topic.subject)
        .order_by(Topic.subject)
    )
    topics_by_subject = topics_result.all()

    # Query 2: quiz accuracy per subject (join QuizAttempt -> Topic to get subject)
    quiz_result = await db.execute(
        select(
            Topic.subject,
            func.count(QuizAttempt.id).label("attempts"),
            func.avg(QuizAttempt.score * 1.0 / QuizAttempt.max_score).label("avg_accuracy"),
        )
        .join(Topic, QuizAttempt.topic_slug == Topic.slug)
        .group_by(Topic.subject)
    )
    quiz_by_subject = {row.subject: row for row in quiz_result.all()}

    # Query 3: SRS counts (do NOT parse card_json)
    total_cards = await db.scalar(
        select(func.count()).select_from(Flashcard)
    ) or 0
    reviewed_cards = await db.scalar(
        select(func.count()).select_from(SRSState)
    ) or 0
    new_cards = total_cards - reviewed_cards  # never reviewed = no SRSState row
    due_count = await fsrs_service.get_due_count(db)
    learned_cards = reviewed_cards - due_count  # reviewed but not currently due

    return {
        "topics_by_subject": topics_by_subject,
        "quiz_by_subject": quiz_by_subject,
        "srs": {
            "due": due_count,
            "learned": max(0, learned_cards),
            "new": max(0, new_cards),
            "total": total_cards,
        },
    }
