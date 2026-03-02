import asyncio
import json
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime, timezone

from app.main import app
from app.database import Base, get_db
from app.models import Topic, SectionQuestion, QuizQuestion, ExamQuestion, PracticeTestAttempt, PracticeTestAnswer

TEST_DB_URL = "sqlite+aiosqlite:///./tests/test.db"
test_engine = create_async_engine(TEST_DB_URL)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

@pytest_asyncio.fixture
async def db():
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def client(db):
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def sample_topic(db):
    from sqlalchemy import select as sa_select
    existing = await db.scalar(sa_select(Topic).where(Topic.slug == "test-topic"))
    if existing:
        return existing
    topic = Topic(slug="test-topic", title_it="Argomento Test", title_en="Test Topic", subject="biology")
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return topic

@pytest_asyncio.fixture
async def sample_quiz_questions(db, sample_topic):
    from sqlalchemy import select as sa_select
    result = await db.execute(
        sa_select(QuizQuestion).where(QuizQuestion.topic_slug == "test-topic")
    )
    existing = result.scalars().all()
    if existing:
        return list(existing)

    questions = []
    choices = json.dumps(["Risposta A", "Risposta B", "Risposta C", "Risposta D"])
    explanation = json.dumps({"correct": "Corretta perché...", "wrong_0": "Sbagliata perché...", "wrong_1": "Sbagliata perché...", "wrong_2": "Sbagliata perché..."})
    for i in range(5):
        q = QuizQuestion(
            topic_slug="test-topic",
            question_it=f"Domanda di test {i+1}?",
            choices_json=choices,
            correct_index=0,
            explanation_json=explanation,
        )
        db.add(q)
        questions.append(q)
    await db.commit()
    for q in questions:
        await db.refresh(q)
    return questions
