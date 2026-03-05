import json
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from src.analyzer import JournalAnalyzer, JournalAnalysis
from src.core.crud import save_entry, get_entries, get_entry_by_id
from src.core.database import get_db, init_db
from src.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Initializing database tables")
    init_db()
    logger.info("Database ready")
    yield


app = FastAPI(title="AI Mental Clarity Journal API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = JournalAnalyzer()


class JournalRequest(BaseModel):
    text: str


class JournalEntryResponse(BaseModel):
    id: int
    text: str
    analysis: JournalAnalysis
    created_at: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/journal", response_model=JournalEntryResponse)
def analyze_journal(
    request: JournalRequest,
    db: Session = Depends(get_db),
) -> JournalEntryResponse:
    try:
        analysis = analyzer.analyze(request.text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(
            status_code=502, detail="LLM returned invalid response"
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503, detail="Analysis service temporarily unavailable"
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error during analysis: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc

    entry = save_entry(db, request.text, analysis.model_dump())

    return JournalEntryResponse(
        id=entry.id,
        text=entry.text,
        analysis=analysis,
        created_at=entry.created_at.isoformat(),
    )


@app.get("/journal/history", response_model=list[JournalEntryResponse])
def journal_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[JournalEntryResponse]:
    entries = get_entries(db, skip=skip, limit=limit)
    return [
        JournalEntryResponse(
            id=e.id,
            text=e.text,
            analysis=JournalAnalysis.model_validate(e.analysis),
            created_at=e.created_at.isoformat(),
        )
        for e in entries
    ]


@app.get("/journal/{entry_id}", response_model=JournalEntryResponse)
def journal_detail(
    entry_id: int,
    db: Session = Depends(get_db),
) -> JournalEntryResponse:
    entry = get_entry_by_id(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    return JournalEntryResponse(
        id=entry.id,
        text=entry.text,
        analysis=JournalAnalysis.model_validate(entry.analysis),
        created_at=entry.created_at.isoformat(),
    )
