import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.core.models import ChatMessage, JournalEntry


def save_entry(db: Session, text: str, analysis: dict, embedding: list[float]) -> JournalEntry:
    """Save journal entry alongside its 384d embedding directly to Postgres."""
    entry = JournalEntry(
        text=text,
        analysis=analysis,
        embedding=embedding,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_entries(db: Session, skip: int = 0, limit: int = 20) -> list[JournalEntry]:
    stmt = select(JournalEntry).order_by(JournalEntry.created_at.desc()).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars())


def get_recent_entries(db: Session, days: int = 7) -> list[JournalEntry]:
    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.created_at >= cutoff)
        .order_by(JournalEntry.created_at.asc())
    )
    return list(db.execute(stmt).scalars())


def get_entry_by_id(db: Session, entry_id: int) -> JournalEntry | None:
    return db.get(JournalEntry, entry_id)


def clear_entries(db: Session) -> int:
    """Delete all journal entries. Returns the number of deleted rows."""
    result = db.execute(delete(JournalEntry))
    db.commit()
    return result.rowcount


def search_similar_entries(
    db: Session, query_vector: list[float], limit: int = 5
) -> list[JournalEntry]:
    """Search for semantically similar journal entries using pgvector cosine distance."""
    stmt = (
        select(JournalEntry)
        .order_by(JournalEntry.embedding.cosine_distance(query_vector))
        .limit(limit)
    )

    return list(db.execute(stmt).scalars())


def save_chat_message(db: Session, chat_id: str, role: str, content: str) -> ChatMessage:
    msg = ChatMessage(chat_id=chat_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_chat_history(db: Session, chat_id: str, limit: int = 20) -> list[ChatMessage]:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    messages = list(db.execute(stmt).scalars())
    return list(reversed(messages))
