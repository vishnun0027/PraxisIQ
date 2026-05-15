import os
import time
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase

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
            # Enable pgvector extension in PostgreSQL/Supabase before tables are built
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                logger.info("pgvector extension verified/created successfully")

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
