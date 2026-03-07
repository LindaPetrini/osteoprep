#!/usr/bin/env python3
"""Audit local content coverage for healthcare entry-test preparation."""

import os
import sqlite3
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "osteoprep.db")

REQUIRED_SUBJECTS = ["biology", "chemistry", "physics", "logic"]
MIN_QUIZ_PER_TOPIC = 4
MIN_EXAM_PER_TOPIC = 6


def fetch_all(conn: sqlite3.Connection, sql: str):
    return conn.execute(sql).fetchall()


def main() -> None:
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        topics_by_subject = dict(fetch_all(conn, "select subject, count(*) from topics group by subject"))
        quiz_by_subject = dict(fetch_all(conn, """
            select t.subject, count(*)
            from quiz_questions q join topics t on t.slug=q.topic_slug
            group by t.subject
        """))
        exam_by_subject = dict(fetch_all(conn, "select subject, count(*) from exam_questions group by subject"))

        quiz_per_topic = fetch_all(conn, """
            select t.subject, t.slug, count(q.id) as c
            from topics t
            left join quiz_questions q on q.topic_slug=t.slug
            group by t.slug
            order by t.subject, t.order_in_subject
        """)
        exam_per_topic = fetch_all(conn, """
            select t.subject, t.slug, count(e.id) as c
            from topics t
            left join exam_questions e on e.topic_slug=t.slug
            group by t.slug
            order by t.subject, t.order_in_subject
        """)

        quiz_gaps = [(s, slug, c) for s, slug, c in quiz_per_topic if c < MIN_QUIZ_PER_TOPIC]
        exam_gaps = [(s, slug, c) for s, slug, c in exam_per_topic if c < MIN_EXAM_PER_TOPIC]

        print("=== ENTRY COVERAGE AUDIT ===")
        print("\nSubject coverage:")
        for subject in REQUIRED_SUBJECTS:
            t = topics_by_subject.get(subject, 0)
            q = quiz_by_subject.get(subject, 0)
            e = exam_by_subject.get(subject, 0)
            status = "OK" if t > 0 and q > 0 and e > 0 else "GAP"
            print(f"- {subject:9} topics={t:3} quiz={q:4} exam={e:4} [{status}]")

        missing_subjects = [s for s in REQUIRED_SUBJECTS if topics_by_subject.get(s, 0) == 0]
        if missing_subjects:
            print("\nMissing subjects:")
            for s in missing_subjects:
                print(f"- {s}")

        print(f"\nTopics below quiz threshold (<{MIN_QUIZ_PER_TOPIC}): {len(quiz_gaps)}")
        for s, slug, c in quiz_gaps[:20]:
            print(f"- {s}/{slug}: {c}")

        print(f"\nTopics below exam threshold (<{MIN_EXAM_PER_TOPIC}): {len(exam_gaps)}")
        for s, slug, c in exam_gaps[:20]:
            print(f"- {s}/{slug}: {c}")

        null_topic_exam = fetch_all(conn, "select count(*) from exam_questions where topic_slug is null")[0][0]
        print(f"\nExam questions without topic mapping: {null_topic_exam}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
