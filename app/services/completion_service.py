"""
Completion service — 3-signal topic completion tracking.

No new DB tables. Derives completion state from:
  - Topic.content_it (explainer generated = read)
  - QuizAttempt best score/max_score >= 0.60
  - SRSState rows vs Flashcard rows for the topic

CompletionStatus levels:
  0 = not started (no signal)
  1 = in progress (at least one signal)
  2 = mastered (quiz_passed AND cards_learned)
"""
from typing import TypedDict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Flashcard, QuizAttempt, SRSState, Topic


class CompletionStatus(TypedDict):
    level: int            # 0=not_started, 1=in_progress, 2=mastered
    explainer_read: bool  # Topic.content_it is not None
    quiz_passed: bool     # best attempt score/max_score >= 0.60
    cards_learned: bool   # all flashcards for topic have SRSState rows
    learned_count: int    # number of SRSState rows for topic
    total_cards: int      # total Flashcard rows for topic


def _make_status(
    explainer_read: bool,
    quiz_passed: bool,
    cards_learned: bool,
    learned_count: int,
    total_cards: int,
) -> CompletionStatus:
    if quiz_passed and cards_learned:
        level = 2
    elif explainer_read or quiz_passed or learned_count > 0:
        level = 1
    else:
        level = 0
    return CompletionStatus(
        level=level,
        explainer_read=explainer_read,
        quiz_passed=quiz_passed,
        cards_learned=cards_learned,
        learned_count=learned_count,
        total_cards=total_cards,
    )


async def get_topic_completion(db: AsyncSession, topic_slug: str) -> CompletionStatus:
    """Compute completion status for a single topic."""
    topic = await db.scalar(select(Topic).where(Topic.slug == topic_slug))
    if topic is None:
        return _make_status(False, False, False, 0, 0)

    explainer_read = topic.content_it is not None

    # Best quiz score for this topic
    best_pct = await db.scalar(
        select(func.max(QuizAttempt.score * 1.0 / QuizAttempt.max_score))
        .where(QuizAttempt.topic_slug == topic_slug)
    )
    quiz_passed = (best_pct is not None and best_pct >= 0.6)

    # Card counts
    total_cards = await db.scalar(
        select(func.count()).select_from(Flashcard).where(Flashcard.topic_slug == topic_slug)
    ) or 0

    learned_count = await db.scalar(
        select(func.count())
        .select_from(SRSState)
        .join(Flashcard, SRSState.flashcard_id == Flashcard.id)
        .where(Flashcard.topic_slug == topic_slug)
    ) or 0

    cards_learned = (total_cards > 0 and learned_count >= total_cards)

    return _make_status(explainer_read, quiz_passed, cards_learned, learned_count, total_cards)


async def get_batch_completions(
    db: AsyncSession, topic_slugs: list[str]
) -> dict[str, CompletionStatus]:
    """
    Compute completion for multiple topics efficiently.
    Uses one query per signal type — no N+1.
    """
    if not topic_slugs:
        return {}

    # Signal 1: explainer_read — fetch topic rows (need content_it)
    topics_result = await db.execute(
        select(Topic.slug, Topic.content_it).where(Topic.slug.in_(topic_slugs))
    )
    explainer_map: dict[str, bool] = {
        row.slug: (row.content_it is not None) for row in topics_result
    }

    # Signal 2: quiz_passed — best score per topic
    quiz_result = await db.execute(
        select(
            QuizAttempt.topic_slug,
            func.max(QuizAttempt.score * 1.0 / QuizAttempt.max_score).label("best_pct"),
        )
        .where(QuizAttempt.topic_slug.in_(topic_slugs))
        .group_by(QuizAttempt.topic_slug)
    )
    quiz_map: dict[str, bool] = {
        row.topic_slug: (row.best_pct >= 0.6) for row in quiz_result
    }

    # Signal 3: card counts — total flashcards per topic
    total_result = await db.execute(
        select(Flashcard.topic_slug, func.count(Flashcard.id).label("cnt"))
        .where(Flashcard.topic_slug.in_(topic_slugs))
        .group_by(Flashcard.topic_slug)
    )
    total_map: dict[str, int] = {row.topic_slug: row.cnt for row in total_result}

    # Learned (SRSState) counts per topic via join
    learned_result = await db.execute(
        select(Flashcard.topic_slug, func.count(SRSState.id).label("cnt"))
        .join(SRSState, SRSState.flashcard_id == Flashcard.id)
        .where(Flashcard.topic_slug.in_(topic_slugs))
        .group_by(Flashcard.topic_slug)
    )
    learned_map: dict[str, int] = {row.topic_slug: row.cnt for row in learned_result}

    result: dict[str, CompletionStatus] = {}
    for slug in topic_slugs:
        explainer_read = explainer_map.get(slug, False)
        quiz_passed = quiz_map.get(slug, False)
        total_cards = total_map.get(slug, 0)
        learned_count = learned_map.get(slug, 0)
        cards_learned = (total_cards > 0 and learned_count >= total_cards)
        result[slug] = _make_status(
            explainer_read, quiz_passed, cards_learned, learned_count, total_cards
        )

    return result


async def get_subject_completion_summary(db: AsyncSession, subject: str) -> dict:
    """
    Return {total, mastered, in_progress} for a subject.
    Mastered = quiz_passed AND cards_learned.
    In progress = at least one signal but not mastered.
    """
    # Get all topic slugs for this subject
    slugs_result = await db.execute(
        select(Topic.slug).where(Topic.subject == subject)
    )
    slugs = [row.slug for row in slugs_result]
    total = len(slugs)

    if not slugs:
        return {"total": 0, "mastered": 0, "in_progress": 0}

    completions = await get_batch_completions(db, slugs)

    mastered = sum(1 for c in completions.values() if c["level"] == 2)
    in_progress = sum(1 for c in completions.values() if c["level"] == 1)

    return {"total": total, "mastered": mastered, "in_progress": in_progress}
