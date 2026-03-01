#!/usr/bin/env python3
"""
Generate flashcards for topics using Claude AI.

Usage:
  python generate_flashcards.py                          # all topics with 0 cards
  python generate_flashcards.py --subject biology        # one subject
  python generate_flashcards.py --topic mitosi-meiosi fotosintesi
  python generate_flashcards.py --count 5               # cards per topic (default: 3)
  python generate_flashcards.py --dry-run               # show topics, don't generate
  python generate_flashcards.py --list                  # show card counts per topic
"""
import argparse
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

from anthropic import Anthropic
from fsrs import Card

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "osteoprep.db")

SYSTEM_PROMPT = """You are a study assistant for Italian professioni sanitarie and osteopathy entry exams.
Generate flashcards as front/back pairs. Each card tests one specific, examinable fact.

Rules:
- Front: short question or term (Italian) — under 15 words
- Back: concise but complete answer (Italian) — 1-3 sentences with key details, numbers, names
- Also provide English translations for both front and back
- Cards must be self-contained: the back fully answers the front without needing context
- Vary card types: definitions, mechanisms, numbers, comparisons, clinical connections
- No overlap between cards in the same batch

Output format — use these XML tags exactly, one <CARD> block per flashcard:
<CARDS>
<CARD>
<FRONT_IT>...</FRONT_IT>
<BACK_IT>...</BACK_IT>
<FRONT_EN>...</FRONT_EN>
<BACK_EN>...</BACK_EN>
</CARD>
</CARDS>"""


def parse_cards(raw: str) -> list[dict]:
    cards = []
    for block in re.finditer(r"<CARD>(.*?)</CARD>", raw, re.DOTALL):
        b = block.group(1)
        def extract(tag):
            m = re.search(rf"<{tag}>(.*?)</{tag}>", b, re.DOTALL)
            return m.group(1).strip() if m else ""
        front_it = extract("FRONT_IT")
        back_it = extract("BACK_IT")
        front_en = extract("FRONT_EN")
        back_en = extract("BACK_EN")
        if front_it and back_it:
            cards.append({
                "front_it": front_it,
                "back_it": back_it,
                "front_en": front_en or None,
                "back_en": back_en or None,
            })
    return cards


def generate_for_topic(client: Anthropic, slug: str, title_it: str, count: int) -> list[dict]:
    print(f"  Generating {count} cards for {slug} ({title_it})...", end=" ", flush=True)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Generate {count} flashcards for the exam topic: '{title_it}' (slug: {slug}).\n"
                f"Target audience: Italian university entrance exam for health professions.\n"
                f"Focus on the most important, testable concepts for this specific topic."
            ),
        }],
    )
    raw = response.content[0].text
    cards = parse_cards(raw)
    print(f"{len(cards)} cards parsed")
    return cards


def insert_cards(conn: sqlite3.Connection, slug: str, cards: list[dict]) -> tuple[int, int]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    new_card_json = Card().to_json()
    inserted = 0
    skipped = 0
    for card in cards:
        existing = conn.execute(
            "SELECT id FROM flashcards WHERE topic_slug=? AND front_it=?",
            (slug, card["front_it"]),
        ).fetchone()
        if existing:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO flashcards (topic_slug, front_it, back_it, front_en, back_en) VALUES (?,?,?,?,?)",
            (slug, card["front_it"], card["back_it"], card["front_en"], card["back_en"]),
        )
        fid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO srs_states (flashcard_id, card_json, due_at, updated_at) VALUES (?,?,?,?)",
            (fid, new_card_json, now, now),
        )
        inserted += 1
    conn.commit()
    return inserted, skipped


def get_topics(conn: sqlite3.Connection, subject_filter=None, slug_filter=None):
    if slug_filter:
        placeholders = ",".join("?" * len(slug_filter))
        rows = conn.execute(
            f"SELECT slug, title_it, subject FROM topics WHERE slug IN ({placeholders}) ORDER BY subject, order_in_subject",
            slug_filter,
        ).fetchall()
    elif subject_filter:
        rows = conn.execute(
            "SELECT slug, title_it, subject FROM topics WHERE subject=? ORDER BY order_in_subject",
            (subject_filter,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT slug, title_it, subject FROM topics ORDER BY subject, order_in_subject"
        ).fetchall()
    return rows


def card_counts(conn: sqlite3.Connection):
    rows = conn.execute(
        "SELECT t.slug, t.title_it, t.subject, COUNT(f.id) as cnt "
        "FROM topics t LEFT JOIN flashcards f ON f.topic_slug=t.slug "
        "GROUP BY t.slug ORDER BY t.subject, t.order_in_subject"
    ).fetchall()
    return rows


def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    load_env()

    parser = argparse.ArgumentParser(description="Generate AI flashcards for OsteoPrep topics")
    parser.add_argument("--topic", nargs="+", metavar="SLUG", help="specific topic slug(s)")
    parser.add_argument("--subject", choices=["biology", "chemistry", "physics"], help="generate for whole subject")
    parser.add_argument("--count", type=int, default=3, help="flashcards per topic (default: 3)")
    parser.add_argument("--all", action="store_true", help="generate for ALL topics (including those with existing cards)")
    parser.add_argument("--dry-run", action="store_true", help="show which topics would be generated, don't call API")
    parser.add_argument("--list", action="store_true", help="show flashcard counts per topic and exit")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if args.list:
        rows = card_counts(conn)
        print(f"\n{'Subject':<12} {'Cards':>5}  Slug")
        print("-" * 50)
        for r in rows:
            marker = "" if r["cnt"] > 0 else "  (none)"
            print(f"{r['subject']:<12} {r['cnt']:>5}  {r['slug']}{marker}")
        total = sum(r["cnt"] for r in rows)
        print(f"\nTotal: {total} flashcards across {len(rows)} topics")
        conn.close()
        return

    topics = get_topics(conn, subject_filter=args.subject, slug_filter=args.topic)

    if not topics:
        print("No topics found for the given filter.")
        conn.close()
        return

    # Unless --all, skip topics that already have cards (when no specific filter)
    if not args.all and not args.topic:
        topics = [t for t in topics if conn.execute(
            "SELECT COUNT(*) FROM flashcards WHERE topic_slug=?", (t["slug"],)
        ).fetchone()[0] == 0]

    if not topics:
        print("All selected topics already have flashcards. Use --all to regenerate.")
        conn.close()
        return

    print(f"\n{'DRY RUN — ' if args.dry_run else ''}Generating {args.count} cards each for {len(topics)} topic(s):\n")
    for t in topics:
        existing = conn.execute(
            "SELECT COUNT(*) FROM flashcards WHERE topic_slug=?", (t["slug"],)
        ).fetchone()[0]
        print(f"  [{t['subject']}] {t['slug']}  (existing: {existing})")

    if args.dry_run:
        conn.close()
        return

    print()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set. Add it to .env or export it.")
        conn.close()
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    total_inserted = 0
    total_skipped = 0

    for t in topics:
        try:
            cards = generate_for_topic(client, t["slug"], t["title_it"], args.count)
            if cards:
                ins, skip = insert_cards(conn, t["slug"], cards)
                total_inserted += ins
                total_skipped += skip
                if skip:
                    print(f"    → {ins} inserted, {skip} skipped (duplicate front_it)")
        except Exception as e:
            print(f"\n  ERROR on {t['slug']}: {e}")
            continue

    conn.close()
    print(f"\nDone. {total_inserted} new flashcards inserted, {total_skipped} skipped.")


if __name__ == "__main__":
    main()
