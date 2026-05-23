import asyncio
from sqlalchemy.orm import Session
from src.analyzer import ChatCopilot
from src.core import crud
from src.core.models import ChatMessage

class ChatService:
    def __init__(self):
        self.copilot = ChatCopilot()

    async def get_response(self, db: Session, chat_id: str, text: str) -> str:
        """Get a response from the copilot and save history."""
        history = await asyncio.to_thread(crud.get_chat_history, db, chat_id, limit=10)
        
        # LLM chat is now async
        response_text = await self.copilot.chat(history, text)
        
        await asyncio.to_thread(crud.save_chat_message, db, chat_id, "user", text)
        await asyncio.to_thread(crud.save_chat_message, db, chat_id, "assistant", response_text)
        
        return response_text

    async def save_system_message(self, db: Session, chat_id: str, role: str, content: str) -> ChatMessage:
        return await asyncio.to_thread(crud.save_chat_message, db, chat_id, role, content)
