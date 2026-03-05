import datetime

from sqlalchemy import Integer, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    analysis: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.UTC),
        nullable=False,
    )
