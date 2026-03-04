#!/usr/bin/env python3
"""Bulk-generate Linda-style explanations for all topics.

Usage:
    cd /home/linda/projects/osteoprep
    .venv/bin/python scripts/generate_linda_explanations.py
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Topic
from app.services.claude import generate_linda_explainer


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Topic).order_by(Topic.subject, Topic.order_in_subject))
        topics = result.scalars().all()

    total = len(topics)
    skipped = 0
    generated = 0
    failed = 0

    print(f"Found {total} topics\n")

    for i, topic in enumerate(topics, 1):
        if topic.content_linda_it is not None:
            print(f"[{i}/{total}] SKIP {topic.slug} (already has Linda content)")
            skipped += 1
            continue

        print(f"[{i}/{total}] Generating: {topic.title_it} ...", end=" ", flush=True)
        try:
            content_it, content_en = await generate_linda_explainer(topic.title_it, topic.title_en)
            async with AsyncSessionLocal() as db:
                t = await db.scalar(select(Topic).where(Topic.slug == topic.slug))
                t.content_linda_it = content_it
                t.content_linda_en = content_en
                await db.commit()
            generated += 1
            print("OK")
        except Exception as e:
            failed += 1
            print(f"FAILED: {e}")

    print(f"\nDone: {generated} generated, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    asyncio.run(main())
