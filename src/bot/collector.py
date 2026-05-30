import asyncio
import os

import httpx
from dotenv import load_dotenv

# Ensure environment variables are loaded BEFORE imports that rely on os.getenv
load_dotenv(override=True)

from sqlalchemy.orm import Session

from src.core.database import SessionLocal, init_db
from src.core.logging import get_logger
from src.services.chat_service import ChatService
from src.services.journal_service import JournalService

logger = get_logger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ALLOWED_CHAT_ID = os.getenv("TELEGRAM_ALLOWED_CHAT_ID")

API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


async def send_message(chat_id: int, text: str) -> None:
    """Send confirmation text message back to the user on Telegram."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})
    except Exception as exc:
        logger.error("Failed to send telegram confirmation: %s", exc)


async def process_update(
    db: Session, update: dict, journal_service: JournalService, chat_service: ChatService
) -> None:
    message = update.get("message")
    if not message:
        return

    chat_id = str(message.get("chat", {}).get("id"))
    text = message.get("text")

    # Ignore non-text interactions (e.g. commands like /start or photo sharing)
    if not text or text.startswith("/"):
        return

    # SECURITY GATE: Reject non-authorized senders
    if chat_id != TELEGRAM_ALLOWED_CHAT_ID:
        logger.warning("Blocked unauthorized message attempt from Chat ID: %s", chat_id)
        return

    logger.info("Ingesting text entry (len=%d) from authorized user", len(text))

    try:
        is_reply = bool(message.get("reply_to_message"))

        if is_reply:
            logger.info("Routing reply to ChatService")
            response_text = await chat_service.get_response(db, chat_id, text)
            await send_message(int(chat_id), response_text)
        else:
            logger.info("Routing new entry to JournalService")
            entry = await journal_service.process_journal_entry(db, text)

            # Save the initial bot response to memory as well so copilot has context
            await chat_service.save_system_message(db, chat_id, "user", text)

            # Report key analysis stats back to user instantly
            summary = "✅ **Journal Saved**\n\n"

            guidance = entry.analysis.get("motivational_guidance")
            if guidance:
                summary += f"💡 {guidance}\n\n"

            reframing = entry.analysis.get("reframing")
            if reframing:
                summary += f"🌱 **Perspective Shift**: {reframing}"

            await chat_service.save_system_message(db, chat_id, "assistant", summary)
            await send_message(int(chat_id), summary)

    except Exception as exc:
        logger.error("Failed to analyze and save message: %s", exc, exc_info=True)
        await send_message(
            int(chat_id),
            "⚠️ **Processing Error**: Could not ingest journal. The system encountered an unexpected error. Please try again later.",
        )


async def run_collector() -> None:
    """
    Stateless polling routine designed to run as a continuous long-polling daemon.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing from environment variables")
        return
    if not TELEGRAM_ALLOWED_CHAT_ID:
        logger.error("TELEGRAM_ALLOWED_CHAT_ID is missing from environment variables")
        return

    logger.info("Starting Telegram Journal Ingestion Routine (continuous long-polling)...")

    # Initialize services
    journal_service = JournalService()
    chat_service = ChatService()

    offset = None

    async with httpx.AsyncClient(timeout=35) as client:
        while True:
            try:
                # Fetch pending updates from Telegram with long-polling
                params = {"timeout": 30}
                if offset is not None:
                    params["offset"] = offset

                resp = await client.get(f"{API_URL}/getUpdates", params=params)
                resp.raise_for_status()
                updates = resp.json().get("result", [])
            except Exception as exc:
                logger.error("Failed to fetch updates from Telegram: %s", exc)
                await asyncio.sleep(5)
                continue

            if not updates:
                continue

            logger.info("Retrieved %d pending updates.", len(updates))

            # Process updates. We use a single session for the batch or one per update?
            # One per update is safer for async.
            for update in updates:
                update_id = update.get("update_id")
                offset = update_id + 1

                # We'll process updates sequentially for now to keep it simple with DB sessions,
                # but we use await so it doesn't block the loop.
                db: Session = SessionLocal()
                try:
                    await process_update(db, update, journal_service, chat_service)
                finally:
                    db.close()


if __name__ == "__main__":
    # Initialize schema dynamically (first run hook)
    init_db()
    asyncio.run(run_collector())
