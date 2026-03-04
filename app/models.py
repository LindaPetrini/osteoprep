from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class Topic(Base):
    __tablename__ = "topics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    title_it: Mapped[str] = mapped_column(String(200), nullable=False)
    title_en: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    order_in_subject: Mapped[int] = mapped_column(Integer, default=0)
    content_it: Mapped[str | None] = mapped_column(Text, nullable=True)   # NULL = not yet generated
    content_en: Mapped[str | None] = mapped_column(Text, nullable=True)   # NULL = not yet generated
    content_linda_it: Mapped[str | None] = mapped_column(Text, nullable=True)  # Linda-style explainer
    content_linda_en: Mapped[str | None] = mapped_column(Text, nullable=True)  # Linda-style explainer
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Flashcard(Base):
    __tablename__ = "flashcards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_slug: Mapped[str] = mapped_column(String(100), ForeignKey("topics.slug"), nullable=False, index=True)
    front_it: Mapped[str] = mapped_column(Text, nullable=False)
    back_it: Mapped[str] = mapped_column(Text, nullable=False)
    front_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    back_en: Mapped[str | None] = mapped_column(Text, nullable=True)


class SRSState(Base):
    __tablename__ = "srs_states"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    flashcard_id: Mapped[int] = mapped_column(Integer, ForeignKey("flashcards.id"), nullable=False, index=True, unique=True)
    card_json: Mapped[str] = mapped_column(Text, nullable=False)   # Card.to_json() blob
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)  # UTC, denormalized for query
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_slug: Mapped[str] = mapped_column(String(100), ForeignKey("topics.slug"), nullable=False, index=True)
    question_it: Mapped[str] = mapped_column(Text, nullable=False)
    choices_json: Mapped[str] = mapped_column(Text, nullable=False)   # JSON list of 4 strings
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-3
    explanation_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # NULL = not generated yet
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_slug: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    subject: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ExamQuestion(Base):
    __tablename__ = "exam_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    topic_slug: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    source_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    question_it: Mapped[str] = mapped_column(Text, nullable=False)
    choices_json: Mapped[str] = mapped_column(Text, nullable=False)
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PracticeTestAttempt(Base):
    __tablename__ = "practice_test_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    time_expired: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)


class PracticeTestAnswer(Base):
    __tablename__ = "practice_test_answers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(Integer, ForeignKey("practice_test_attempts.id"), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("exam_questions.id"), nullable=False)
    chosen_index: Mapped[int | None] = mapped_column(Integer, nullable=True)  # NULL = skipped/timed out
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class SectionQuestion(Base):
    """2-3 inline MCQs per topic section — generate-once-cache, no answer tracking."""
    __tablename__ = "section_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_slug: Mapped[str] = mapped_column(String(100), ForeignKey("topics.slug"), nullable=False, index=True)
    section_slug: Mapped[str] = mapped_column(String(100), nullable=False)
    question_it: Mapped[str] = mapped_column(Text, nullable=False)          # legacy: question 1
    choices_json: Mapped[str] = mapped_column(Text, nullable=False)          # legacy: choices for question 1
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)       # legacy: correct for question 1
    questions_json: Mapped[str | None] = mapped_column(Text, nullable=True)   # NEW: JSON array of {question_it, choices, correct_index}
    __table_args__ = (UniqueConstraint("topic_slug", "section_slug", name="uq_section_question"),)
