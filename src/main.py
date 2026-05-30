import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv(override=True)


from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy.orm import Session

from src.core.crud import clear_entries, get_entries, get_entry_by_id
from src.core.database import get_db, init_db
from src.core.logging import get_logger
from src.core.models import JournalEntry
from src.services.journal_service import JournalService

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Initializing database tables")
    init_db()
    logger.info("Application ready")
    yield


app = FastAPI(title="PraxisIQ API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

journal_service = JournalService()


class JournalRequest(BaseModel):
    text: str


class JournalEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    analysis: dict
    created_at: str


def _entry_to_response(entry: JournalEntry) -> JournalEntryResponse:
    """Convert an ORM JournalEntry to a JournalEntryResponse."""
    return JournalEntryResponse(
        id=entry.id,
        text=entry.text,
        analysis=entry.analysis,
        created_at=entry.created_at.isoformat(),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/journal", response_model=JournalEntryResponse)
async def analyze_journal(
    request: JournalRequest,
    db: Session = Depends(get_db),
) -> JournalEntryResponse:
    try:
        entry = await journal_service.process_journal_entry(db, request.text)
        return _entry_to_response(entry)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(status_code=502, detail="LLM returned invalid response") from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503, detail="Analysis service temporarily unavailable"
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error during analysis: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.get("/journal/history", response_model=list[JournalEntryResponse])
def journal_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[JournalEntryResponse]:
    entries = get_entries(db, skip=skip, limit=limit)
    return [_entry_to_response(e) for e in entries]


@app.delete("/journal/all")
def journal_clear_all(db: Session = Depends(get_db)) -> dict[str, int]:
    """Delete all journal entries. Returns the count of deleted rows."""
    deleted = clear_entries(db)
    logger.info("Cleared all journal entries (%d rows)", deleted)
    return {"deleted": deleted}


@app.get("/journal/search", response_model=list[JournalEntryResponse])
async def journal_search(
    q: str = Query(..., min_length=2, description="Search conceptually similar entries"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> list[JournalEntryResponse]:
    """Semantic search over past journal entries."""
    entries = await journal_service.search_similar(db, query_text=q, limit=limit)
    return [_entry_to_response(e) for e in entries]


@app.get("/journal/{entry_id}", response_model=JournalEntryResponse)
def journal_detail(
    entry_id: int,
    db: Session = Depends(get_db),
) -> JournalEntryResponse:
    entry = get_entry_by_id(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return _entry_to_response(entry)
