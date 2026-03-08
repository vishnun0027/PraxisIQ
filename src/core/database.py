import os
import time
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from src.core.logging import get_logger

logger = get_logger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/journal",
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # Detect and recycle stale connections automatically
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


# Global Qdrant client instance
_qdrant_client: QdrantClient | None = None

def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        _qdrant_client = QdrantClient(url=qdrant_url)
    return _qdrant_client


def init_qdrant(collection_name: str = "journal_entries") -> None:
    """Ensure the Qdrant collection exists before using it."""
    client = get_qdrant_client()
    try:
        collections = client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        if not exists:
            logger.info("Creating Qdrant collection: %s", collection_name)
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        else:
            logger.info("Qdrant collection %s already exists", collection_name)
    except Exception as exc:
        logger.error("Failed to initialize Qdrant: %s", exc)



def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(max_retries: int = 5, retry_delay: float = 2.0) -> None:
    from src.core.models import JournalEntry  # noqa: F401

    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            return
        except Exception as exc:
            if attempt == max_retries:
                raise
            logger.warning(
                "Database not ready (attempt %d/%d): %s — retrying in %.0fs",
                attempt, max_retries, exc, retry_delay,
            )
            time.sleep(retry_delay)
