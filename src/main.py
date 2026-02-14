from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.analyzer import JournalAnalyzer, JournalAnalysis
from src.core.logging import get_logger

logger = get_logger(__name__)


app = FastAPI(title="AI Mental Clarity Journal API")

analyzer = JournalAnalyzer()


class JournalRequest(BaseModel):
    text: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/journal", response_model=JournalAnalysis)
def analyze_journal(request: JournalRequest) -> JournalAnalysis:
    try:
        return analyzer.analyze(request.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
