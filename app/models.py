from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Integer
from datetime import datetime
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
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
