#!/usr/bin/env python3
"""
Generate exam-style MCQ questions for all topics using Claude AI.
Models real professioni sanitarie / TOLC-B exam questions.

Usage:
  python generate_exam_questions.py                          # all topics with < 5 exam questions
  python generate_exam_questions.py --subject biology        # one subject
  python generate_exam_questions.py --topic mitosi-meiosi fotosintesi
  python generate_exam_questions.py --count 10              # questions per topic (default: 10)
  python generate_exam_questions.py --dry-run               # preview, no API calls
  python generate_exam_questions.py --list                  # show counts per topic
  python generate_exam_questions.py --all                   # include topics already with questions
"""
import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

from anthropic import Anthropic

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "osteoprep.db")

SUBJECT_MAP = {
    "biology": "biologia",
    "chemistry": "chimica",
    "physics": "fisica e matematica",
}

SYSTEM_PROMPT = """You are an Italian university entrance exam question writer for professioni sanitarie (health professions).

Write multiple-choice questions that match the exact style of real Italian professioni sanitarie and TOLC-B exams.

Style rules:
- Questions in Italian, concise and unambiguous
- One clearly correct answer, three plausible but wrong distractors
- Distractors must be specific (not vague "nessuna delle precedenti" type)
- Questions test application of knowledge, not just definitions
- Difficulty matches real professioni sanitarie exam (undergraduate entry level)
- No two questions test the exact same fact

Output format — use these XML tags exactly, one <Q> block per question:
<QUESTIONS>
<Q>
<STEM>...</STEM>
<A>...</A>
<B>...</B>
<C>...</C>
<D>...</D>
<CORRECT>0</CORRECT>
</Q>
</QUESTIONS>

CORRECT is 0-based index: 0=A, 1=B, 2=C, 3=D"""


def parse_questions(raw: str) -> list[dict]:
    questions = []
    for block in re.finditer(r"<Q>(.*?)</Q>", raw, re.DOTALL):
        b = block.group(1)

        def extract(tag):
            m = re.search(rf"<{tag}>(.*?)</{tag}>", b, re.DOTALL)
            return m.group(1).strip() if m else ""

        stem = extract("STEM")
        choices = [extract("A"), extract("B"), extract("C"), extract("D")]
        correct_raw = extract("CORRECT").strip()
        try:
            correct = int(correct_raw)
        except ValueError:
            continue
        if not stem or not all(choices) or correct not in range(4):
            continue
        questions.append({
            "question_it": stem,
            "choices": choices,
            "correct_index": correct,
        })
    return questions


def generate_for_topic(client: Anthropic, slug: str, title_it: str, subject: str, count: int) -> list[dict]:
    subject_it = SUBJECT_MAP.get(subject, subject)
    print(f"  [{subject_it}] {slug} ({title_it})...", end=" ", flush=True)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Write {count} exam questions for topic: '{title_it}' (slug: {slug}, subject: {subject_it}).\n"
                f"Target: Italian professioni sanitarie entrance exam.\n"
                f"Vary question types: mechanisms, comparisons, clinical relevance, numerical values, definitions."
            ),
        }],
    )
    raw = response.content[0].text
    questions = parse_questions(raw)
    print(f"{len(questions)} questions")
    return questions


def insert_questions(conn: sqlite3.Connection, slug: str, subject: str, questions: list[dict]) -> tuple[int, int]:
    inserted = 0
    skipped = 0
    for q in questions:
        existing = conn.execute(
            "SELECT id FROM exam_questions WHERE topic_slug=? AND question_it=?",
            (slug, q["question_it"]),
        ).fetchone()
        if existing:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO exam_questions (subject, topic_slug, question_it, choices_json, correct_index) VALUES (?,?,?,?,?)",
            (subject, slug, q["question_it"], json.dumps(q["choices"], ensure_ascii=False), q["correct_index"]),
        )
        inserted += 1
    conn.commit()
    return inserted, skipped


def get_topics(conn, subject_filter=None, slug_filter=None):
    if slug_filter:
        placeholders = ",".join("?" * len(slug_filter))
        return conn.execute(
            f"SELECT slug, title_it, subject FROM topics WHERE slug IN ({placeholders}) ORDER BY subject, order_in_subject",
            slug_filter,
        ).fetchall()
    if subject_filter:
        return conn.execute(
            "SELECT slug, title_it, subject FROM topics WHERE subject=? ORDER BY order_in_subject",
            (subject_filter,),
        ).fetchall()
    return conn.execute(
        "SELECT slug, title_it, subject FROM topics ORDER BY subject, order_in_subject"
    ).fetchall()


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
    parser = argparse.ArgumentParser(description="Generate exam questions for OsteoPrep")
    parser.add_argument("--topic", nargs="+", metavar="SLUG")
    parser.add_argument("--subject", choices=["biology", "chemistry", "physics"])
    parser.add_argument("--count", type=int, default=10, help="questions per topic (default: 10)")
    parser.add_argument("--all", action="store_true", help="include topics that already have questions")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if args.list:
        rows = conn.execute(
            "SELECT t.slug, t.subject, COUNT(eq.id) as cnt "
            "FROM topics t LEFT JOIN exam_questions eq ON eq.topic_slug=t.slug "
            "GROUP BY t.slug ORDER BY t.subject, t.order_in_subject"
        ).fetchall()
        total_unlinked = conn.execute(
            "SELECT COUNT(*) FROM exam_questions WHERE topic_slug IS NULL"
        ).fetchone()[0]
        print(f"\n{'Subject':<12} {'Exam Qs':>7}  Slug")
        print("-" * 52)
        for r in rows:
            marker = "  (none)" if r["cnt"] == 0 else ""
            print(f"{r['subject']:<12} {r['cnt']:>7}  {r['slug']}{marker}")
        total = conn.execute("SELECT COUNT(*) FROM exam_questions").fetchone()[0]
        print(f"\nTotal: {total} exam questions ({total_unlinked} unlinked to topic)")
        conn.close()
        return

    topics = get_topics(conn, subject_filter=args.subject, slug_filter=args.topic)
    if not topics:
        print("No topics found.")
        conn.close()
        return

    # Filter to topics with fewer than 5 exam questions unless --all or --topic specified
    if not args.all and not args.topic:
        topics = [t for t in topics if conn.execute(
            "SELECT COUNT(*) FROM exam_questions WHERE topic_slug=?", (t["slug"],)
        ).fetchone()[0] < 5]

    if not topics:
        print("All selected topics already have questions. Use --all to add more.")
        conn.close()
        return

    print(f"\n{'DRY RUN — ' if args.dry_run else ''}Generating {args.count} questions each for {len(topics)} topic(s):\n")
    for t in topics:
        existing = conn.execute(
            "SELECT COUNT(*) FROM exam_questions WHERE topic_slug=?", (t["slug"],)
        ).fetchone()[0]
        print(f"  [{t['subject']:<10}] {t['slug']}  (existing: {existing})")

    if args.dry_run:
        conn.close()
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nERROR: ANTHROPIC_API_KEY not set.")
        conn.close()
        sys.exit(1)

    client = Anthropic(api_key=api_key)
    total_inserted = 0
    total_skipped = 0

    print()
    for t in topics:
        try:
            questions = generate_for_topic(client, t["slug"], t["title_it"], t["subject"], args.count)
            if questions:
                ins, skip = insert_questions(conn, t["slug"], t["subject"], questions)
                total_inserted += ins
                total_skipped += skip
        except Exception as e:
            print(f"\n  ERROR on {t['slug']}: {e}")

    conn.close()
    print(f"\nDone. {total_inserted} new questions inserted, {total_skipped} skipped.")
    total = conn.execute("SELECT COUNT(*) FROM exam_questions") if False else None
    # Quick final count
    conn2 = sqlite3.connect(DB_PATH)
    grand_total = conn2.execute("SELECT COUNT(*) FROM exam_questions").fetchone()[0]
    conn2.close()
    print(f"Total exam questions in DB: {grand_total}")


if __name__ == "__main__":
    main()
