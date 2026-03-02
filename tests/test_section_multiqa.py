"""
Tests for Section Multi-Questions feature.
2-3 questions per collapsible section.
"""
import json
import time
import pytest
import pytest_asyncio
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.exc import IntegrityError

from app.models import SectionQuestion, Topic


# ---- Test 1: Model has questions_json field ----

@pytest.mark.asyncio
async def test_section_question_has_questions_json(db):
    """SectionQuestion model must have a questions_json column."""
    async with db.bind.connect() as conn:
        def _get_cols(sync_conn):
            inspector = sa_inspect(sync_conn)
            return [c["name"] for c in inspector.get_columns("section_questions")]
        cols = await conn.run_sync(_get_cols)
    assert "questions_json" in cols, (
        "SectionQuestion table is missing questions_json column. "
        "Run the migration to add it."
    )


# ---- Test 2: Model can store multiple questions ----

@pytest.mark.asyncio
async def test_section_question_model_stores_multiple_questions(db):
    """Can insert a SectionQuestion with questions_json containing 2-3 question dicts."""
    # Create a topic first (FK constraint)
    topic = Topic(
        slug="test-topic-multiqa",
        title_it="Argomento di test",
        title_en="Test Topic",
        subject="biology",
        order_in_subject=999,
        content_it="## Definizione\n\nTesto di prova.",
    )
    db.add(topic)
    await db.flush()

    questions = [
        {
            "question_it": "Quale e' la prima domanda?",
            "choices": ["Risposta A", "Risposta B", "Risposta C", "Risposta D"],
            "correct_index": 0,
        },
        {
            "question_it": "Quale e' la seconda domanda?",
            "choices": ["Opzione 1", "Opzione 2", "Opzione 3", "Opzione 4"],
            "correct_index": 2,
        },
        {
            "question_it": "Quale e' la terza domanda?",
            "choices": ["Scelta A", "Scelta B", "Scelta C", "Scelta D"],
            "correct_index": 1,
        },
    ]

    sq = SectionQuestion(
        topic_slug="test-topic-multiqa",
        section_slug="definizione",
        # legacy fields (question 1)
        question_it=questions[0]["question_it"],
        choices_json=json.dumps(questions[0]["choices"], ensure_ascii=False),
        correct_index=questions[0]["correct_index"],
        # new multi-question field
        questions_json=json.dumps(questions, ensure_ascii=False),
    )
    db.add(sq)
    await db.flush()

    # Re-read from DB
    await db.refresh(sq)

    assert sq.questions_json is not None
    loaded = json.loads(sq.questions_json)
    assert len(loaded) == 3
    assert loaded[0]["question_it"] == "Quale e' la prima domanda?"
    assert loaded[1]["correct_index"] == 2
    assert loaded[2]["choices"][1] == "Scelta B"


# ---- Helpers to create test data ----

@pytest_asyncio.fixture
async def topic_and_sq(db):
    """Create a topic + SectionQuestion with 2 questions in questions_json.

    Uses a unique slug per test invocation to avoid UNIQUE constraint failures
    when the test DB persists across runs.
    """
    unique_slug = f"test-multiqa-endpoint-{int(time.time() * 1000)}"

    topic = Topic(
        slug=unique_slug,
        title_it="Argomento endpoint test",
        title_en="Endpoint Test Topic",
        subject="biology",
        order_in_subject=998,
        content_it="## Definizione\n\nTesto di prova endpoint.",
    )
    db.add(topic)
    await db.flush()

    questions = [
        {
            "question_it": "Prima domanda per l'endpoint?",
            "choices": ["Corretta", "Sbagliata 1", "Sbagliata 2", "Sbagliata 3"],
            "correct_index": 0,
        },
        {
            "question_it": "Seconda domanda per l'endpoint?",
            "choices": ["Sbagliata 1", "Corretta", "Sbagliata 2", "Sbagliata 3"],
            "correct_index": 1,
        },
    ]

    sq = SectionQuestion(
        topic_slug=unique_slug,
        section_slug="definizione",
        question_it=questions[0]["question_it"],
        choices_json=json.dumps(questions[0]["choices"], ensure_ascii=False),
        correct_index=questions[0]["correct_index"],
        questions_json=json.dumps(questions, ensure_ascii=False),
    )
    db.add(sq)
    await db.commit()
    await db.refresh(sq)
    return topic, sq


# ---- Test 3: POST with correct answer, q_index=0 ----

@pytest.mark.asyncio
async def test_section_check_multi_q_correct(client, topic_and_sq):
    """POST /topic/{slug}/section-check/{sq_id}?q_index=0 with correct answer returns success."""
    topic, sq = topic_and_sq
    response = await client.post(
        f"/topic/{topic.slug}/section-check/{sq.id}?q_index=0",
        data={"answer": "0"},
    )
    assert response.status_code == 200
    body = response.text
    assert "Corretto" in body


# ---- Test 4: POST with incorrect answer, q_index=0 ----

@pytest.mark.asyncio
async def test_section_check_multi_q_incorrect(client, topic_and_sq):
    """POST /topic/{slug}/section-check/{sq_id}?q_index=0 with wrong answer returns error."""
    topic, sq = topic_and_sq
    response = await client.post(
        f"/topic/{topic.slug}/section-check/{sq.id}?q_index=0",
        data={"answer": "2"},  # wrong: correct_index is 0
    )
    assert response.status_code == 200
    body = response.text
    assert "Sbagliato" in body


# ---- Test 5: POST with q_index=1 (second question) ----

@pytest.mark.asyncio
async def test_section_check_multi_q_second_question(client, topic_and_sq):
    """POST /topic/{slug}/section-check/{sq_id}?q_index=1 works for second question."""
    topic, sq = topic_and_sq
    # correct answer for q_index=1 is index 1
    response = await client.post(
        f"/topic/{topic.slug}/section-check/{sq.id}?q_index=1",
        data={"answer": "1"},
    )
    assert response.status_code == 200
    body = response.text
    assert "Corretto" in body
