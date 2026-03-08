from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from qdrant_client.http.models import PointStruct

from src.core.models import JournalEntry
from src.core.database import get_qdrant_client
from src.core.embeddings import get_embedding


def save_entry(db: Session, text: str, analysis: dict) -> JournalEntry:
    entry = JournalEntry(text=text, analysis=analysis)
    db.add(entry)
    db.commit()
    db.refresh(entry)

    try:
        qdrant = get_qdrant_client()
        vector = get_embedding(text)
        point = PointStruct(
            id=entry.id,
            vector=vector,
            payload={
                "text": text,
                "created_at": entry.created_at.isoformat(),
                "emotional_intensity": analysis.get("emotional_intensity"),
                "detected_emotions": analysis.get("detected_emotions", []),
            },
        )
        qdrant.upsert(collection_name="journal_entries", points=[point])
    except Exception as exc:
        # We don't want a vector DB failure to break the primary Postgres save
        # but in production we'd log this properly or queue for retry.
        print(f"Warning: Failed to sync entry {entry.id} to Qdrant: {exc}")

    return entry


def get_entries(db: Session, skip: int = 0, limit: int = 20) -> list[JournalEntry]:
    stmt = (
        select(JournalEntry)
        .order_by(JournalEntry.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.execute(stmt).scalars())


def get_entry_by_id(db: Session, entry_id: int) -> JournalEntry | None:
    return db.get(JournalEntry, entry_id)


def clear_entries(db: Session) -> int:
    """Delete all journal entries. Returns the number of deleted rows."""
    result = db.execute(delete(JournalEntry))
    db.commit()

    try:
        qdrant = get_qdrant_client()
        # The easiest way to clear Qdrant is to delete and recreate the collection.
        # But we can also use an empty filter payload to delete everything.
        from src.core.database import init_qdrant
        qdrant.delete_collection("journal_entries")
        init_qdrant("journal_entries")
    except Exception as exc:
        print(f"Warning: Failed to clear Qdrant: {exc}")

    return result.rowcount


def search_similar_entries(db: Session, query_text: str, limit: int = 5) -> list[JournalEntry]:
    """Search for semantically similar journal entries using Qdrant."""
    qdrant = get_qdrant_client()
    query_vector = get_embedding(query_text)

    search_result = qdrant.search(
        collection_name="journal_entries",
        query_vector=query_vector,
        limit=limit,
    )
    
    if not search_result:
        return []

    # Extract the Postgres IDs returned by Qdrant
    entry_ids = [point.id for point in search_result]

    # Fetch rows from Postgres
    stmt = select(JournalEntry).filter(JournalEntry.id.in_(entry_ids))
    db_items = list(db.execute(stmt).scalars())

    # Order the DB items to match the Qdrant similarity score ordering
    items_by_id = {item.id: item for item in db_items}
    ordered_items = [items_by_id[eid] for eid in entry_ids if eid in items_by_id]
    
    return ordered_items
