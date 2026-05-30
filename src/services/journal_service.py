import asyncio

from sqlalchemy.orm import Session

from src.analyzer import JournalAnalyzer
from src.core import crud
from src.core.embeddings import get_embedding
from src.core.models import JournalEntry


class JournalService:
    def __init__(self):
        self.analyzer = JournalAnalyzer()

    async def process_journal_entry(self, db: Session, text: str) -> JournalEntry:
        """Analyze, embed, and save a journal entry."""
        # LLM analysis is now async
        analysis = await self.analyzer.analyze(text)
        analysis_dict = analysis.model_dump()

        # Embedding is CPU-bound, run in thread
        embedding = await asyncio.to_thread(get_embedding, text)

        # CRUD is synchronous, run in thread
        return await asyncio.to_thread(crud.save_entry, db, text, analysis_dict, embedding)

    async def search_similar(
        self, db: Session, query_text: str, limit: int = 5
    ) -> list[JournalEntry]:
        """Search for similar entries using embeddings."""
        query_vector = await asyncio.to_thread(get_embedding, query_text)
        return await asyncio.to_thread(crud.search_similar_entries, db, query_vector, limit)
