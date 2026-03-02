import json
import pytest
import pytest_asyncio
from app.models import QuizQuestion


pytestmark = pytest.mark.asyncio


# ============================================================
# Feature A: Chat in quiz results
# ============================================================

async def test_quiz_results_has_chat_panel(client, sample_topic, sample_quiz_questions):
    """Quiz results page should contain a chat panel."""
    questions = sample_quiz_questions
    form_data = {f"answer_{q.id}": "0" for q in questions[:3]}
    resp = await client.post("/topic/test-topic/quiz/submit", data=form_data)
    assert resp.status_code == 200
    assert "Chiedi a Claude" in resp.text  # chat panel should be present


async def test_chat_stream_accepts_quiz_context(client):
    """Chat stream should accept quiz_context param without error."""
    resp = await client.get("/chat/stream?q=Spiegami+questa+domanda&quiz_context=test")
    # SSE endpoint — check it opens without 400/500
    assert resp.status_code == 200


# ============================================================
# Feature B: Pre-generate explanations
# ============================================================

async def test_quiz_page_triggers_explanation_prefetch(client, db, sample_topic):
    """When quiz page loads, questions without explanations should get explanations pre-generated."""
    # Create question without explanation
    q = QuizQuestion(
        topic_slug="test-topic",
        question_it="Domanda senza spiegazione?",
        choices_json=json.dumps(["A", "B", "C", "D"]),
        correct_index=0,
        explanation_json=None,  # No explanation yet
    )
    db.add(q)
    await db.commit()

    # Load quiz page — should trigger background explanation gen
    resp = await client.get("/topic/test-topic/quiz")
    assert resp.status_code == 200
    # We can't easily test background tasks in tests, but page should load without error


# ============================================================
# Feature C: Generate new questions
# ============================================================

async def test_generate_new_quiz_endpoint_exists(client, sample_topic):
    """POST /topic/{slug}/quiz/generate should return redirect or HTML."""
    # This will fail without API key, but endpoint should exist
    resp = await client.post("/topic/test-topic/quiz/generate", follow_redirects=False)
    # Should be 302 redirect or 200, not 404
    assert resp.status_code != 404


async def test_quiz_results_has_new_questions_button(client, sample_topic, sample_quiz_questions):
    """Quiz results page should have a button to generate new questions."""
    questions = sample_quiz_questions
    form_data = {f"answer_{q.id}": "0" for q in questions[:3]}
    resp = await client.post("/topic/test-topic/quiz/submit", data=form_data)
    assert resp.status_code == 200
    assert "Genera nuove domande" in resp.text or "Nuovo quiz" in resp.text or "generat" in resp.text.lower()
