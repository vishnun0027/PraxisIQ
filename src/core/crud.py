from sqlalchemy.orm import Session

from src.core.models import JournalEntry


def save_entry(db: Session, text: str, analysis: dict) -> JournalEntry:
    entry = JournalEntry(text=text, analysis=analysis)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_entries(db: Session, skip: int = 0, limit: int = 20) -> list[JournalEntry]:
    return (
        db.query(JournalEntry)
        .order_by(JournalEntry.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_entry_by_id(db: Session, entry_id: int) -> JournalEntry | None:
    return db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
