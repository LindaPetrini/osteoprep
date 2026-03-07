#!/usr/bin/env python3
"""
Bulk-generate harder quiz questions across topics.

Default behavior is safe: append new questions.
Use --replace-existing to replace each topic's current bank after successful generation.
"""
import argparse
import asyncio
import json
import os
from datetime import datetime, timezone

from sqlalchemy import delete, select

from app.database import AsyncSessionLocal
from app.models import QuizQuestion, Topic
from app.services.claude import generate_new_quiz_questions


def _parse_csv(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {part.strip() for part in value.split(",") if part.strip()}


async def _run(args: argparse.Namespace) -> None:
    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing API key. Pass --api-key or set ANTHROPIC_API_KEY."
        )

    subjects = _parse_csv(args.subjects)
    slugs = _parse_csv(args.topic_slugs)

    async with AsyncSessionLocal() as db:
        stmt = select(Topic).order_by(Topic.subject, Topic.order_in_subject, Topic.id)
        if subjects:
            stmt = stmt.where(Topic.subject.in_(subjects))
        if slugs:
            stmt = stmt.where(Topic.slug.in_(slugs))

        topics = (await db.execute(stmt)).scalars().all()
        if args.max_topics:
            topics = topics[: args.max_topics]

        if not topics:
            print("No topics matched filters.")
            return

        print(
            f"Processing {len(topics)} topics | per-topic={args.per_topic} | "
            f"replace_existing={args.replace_existing}"
        )

        generated_total = 0
        replaced_topics = 0
        skipped_topics = 0

        for idx, topic in enumerate(topics, start=1):
            existing_rows = (
                await db.execute(
                    select(QuizQuestion.question_it).where(QuizQuestion.topic_slug == topic.slug)
                )
            ).all()
            existing_questions = [row[0] for row in existing_rows]

            print(
                f"[{idx}/{len(topics)}] {topic.subject}/{topic.slug}: "
                f"{len(existing_questions)} existing -> generating {args.per_topic}"
            )

            try:
                new_questions = await generate_new_quiz_questions(
                    topic_slug=topic.slug,
                    title_it=topic.title_it,
                    count=args.per_topic,
                    existing_questions=existing_questions,
                    api_key=api_key,
                )
            except Exception as exc:
                skipped_topics += 1
                print(f"  ! generation failed: {exc}")
                continue

            if not new_questions:
                skipped_topics += 1
                print("  ! no questions returned")
                continue

            now = datetime.now(timezone.utc)

            if args.replace_existing:
                await db.execute(
                    delete(QuizQuestion).where(QuizQuestion.topic_slug == topic.slug)
                )
                replaced_topics += 1

            for q_data in new_questions:
                db.add(
                    QuizQuestion(
                        topic_slug=topic.slug,
                        question_it=q_data["question_it"],
                        choices_json=json.dumps(q_data["choices"], ensure_ascii=False),
                        correct_index=q_data["correct_index"],
                        generated_at=now,
                    )
                )

            await db.commit()
            generated_total += len(new_questions)
            print(f"  + saved {len(new_questions)}")

            if args.pause_ms > 0:
                await asyncio.sleep(args.pause_ms / 1000)

        print(
            "Done. "
            f"generated_total={generated_total}, replaced_topics={replaced_topics}, skipped_topics={skipped_topics}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upgrade quiz bank with harder official-style questions."
    )
    parser.add_argument(
        "--per-topic",
        type=int,
        default=5,
        help="How many new questions to generate per topic (default: 5).",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace each topic's existing question bank after successful generation.",
    )
    parser.add_argument(
        "--subjects",
        type=str,
        default=None,
        help="Comma-separated subjects (biology,chemistry,physics,logic).",
    )
    parser.add_argument(
        "--topic-slugs",
        type=str,
        default=None,
        help="Comma-separated topic slugs to target.",
    )
    parser.add_argument(
        "--max-topics",
        type=int,
        default=0,
        help="Limit number of topics processed (0 = no limit).",
    )
    parser.add_argument(
        "--pause-ms",
        type=int,
        default=250,
        help="Pause between topics to avoid burst API calls (default: 250).",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Anthropic API key (falls back to ANTHROPIC_API_KEY env var).",
    )
    args = parser.parse_args()

    if args.per_topic < 1:
        raise SystemExit("--per-topic must be >= 1")
    if args.max_topics < 0:
        raise SystemExit("--max-topics must be >= 0")
    if args.pause_ms < 0:
        raise SystemExit("--pause-ms must be >= 0")

    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
