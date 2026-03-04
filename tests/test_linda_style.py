"""Tests for Linda-style explanations feature."""

import pytest
import pytest_asyncio
from sqlalchemy import select as sa_select

from app.models import Topic


@pytest.mark.asyncio
async def test_topic_model_has_linda_columns(db, sample_topic):
    """Topic model should have content_linda_it and content_linda_en columns."""
    topic = await db.scalar(sa_select(Topic).where(Topic.slug == "test-topic"))
    assert hasattr(topic, "content_linda_it")
    assert hasattr(topic, "content_linda_en")
    # Initially null
    assert topic.content_linda_it is None
    assert topic.content_linda_en is None


@pytest.mark.asyncio
async def test_topic_page_default_style_linda(client, sample_topic):
    """Topic page should default to linda style."""
    response = await client.get("/topic/test-topic")
    assert response.status_code == 200
    text = response.text
    # Style toggle buttons should be present
    assert "btn-style-linda" in text
    assert "btn-style-libro" in text


@pytest.mark.asyncio
async def test_topic_content_fragment_accepts_style(client, sample_topic, db):
    """Content fragment endpoint should accept style parameter."""
    # Set textbook content so we can test libro style
    topic = await db.scalar(sa_select(Topic).where(Topic.slug == "test-topic"))
    topic.content_it = "## Definizione\nTest content"
    topic.content_en = "## Definition\nTest content"
    await db.commit()

    response = await client.get("/topic/test-topic/content?lang=it&style=libro")
    assert response.status_code == 200
    assert "Test content" in response.text


@pytest.mark.asyncio
async def test_linda_style_renders_when_content_exists(client, db, sample_topic):
    """Linda style should render content when available."""
    topic = await db.scalar(sa_select(Topic).where(Topic.slug == "test-topic"))
    topic.content_linda_it = "## Perché importa\nSpiegazione Linda in italiano"
    topic.content_linda_en = "## Why it matters\nLinda explanation in English"
    await db.commit()

    response = await client.get("/topic/test-topic/content?lang=it&style=linda")
    assert response.status_code == 200
    assert "Spiegazione Linda in italiano" in response.text

    response = await client.get("/topic/test-topic/content?lang=en&style=linda")
    assert response.status_code == 200
    assert "Linda explanation in English" in response.text


@pytest.mark.asyncio
async def test_linda_style_shows_spinner_when_missing(client, db, sample_topic):
    """Linda style should show polling spinner when content not yet generated."""
    topic = await db.scalar(sa_select(Topic).where(Topic.slug == "test-topic"))
    topic.content_linda_it = None
    topic.content_linda_en = None
    await db.commit()

    response = await client.get("/topic/test-topic/content?lang=it&style=linda")
    assert response.status_code == 200
    assert "Generazione in corso" in response.text
