import os
import time
import httpx
from dotenv import load_dotenv

# Ensure environment variables are loaded BEFORE imports that rely on os.getenv
load_dotenv(override=True)

from sqlalchemy.orm import Session

from src.analyzer import JournalAnalyzer, ChatCopilot
from src.core.crud import save_entry, get_chat_history, save_chat_message
from src.core.database import SessionLocal, init_db
from src.core.logging import get_logger

logger = get_logger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ALLOWED_CHAT_ID = os.getenv("TELEGRAM_ALLOWED_CHAT_ID")

API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_message(chat_id: int, text: str) -> None:
    """Send confirmation text message back to the user on Telegram."""
    try:
        with httpx.Client() as client:
            client.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})
    except Exception as exc:
        logger.error("Failed to send telegram confirmation: %s", exc)


def run_collector() -> None:
    """
    Stateless polling routine designed to run as a continuous long-polling daemon.
    Fetches pending messages, gates by authorized sender, extracts CBT metrics, 
    embeds vectors, persists to database, and acknowledges the queue.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing from environment variables")
        return
    if not TELEGRAM_ALLOWED_CHAT_ID:
        logger.error("TELEGRAM_ALLOWED_CHAT_ID is missing from environment variables")
        return

    logger.info("Starting Telegram Journal Ingestion Routine (continuous long-polling)...")

    # Pre-heat analyzer
    analyzer = JournalAnalyzer()
    
    offset = None

    while True:
        try:
            # Fetch pending updates from Telegram with long-polling
            params = {"timeout": 30}
            if offset is not None:
                params["offset"] = offset

            with httpx.Client(timeout=35) as client:
                resp = client.get(f"{API_URL}/getUpdates", params=params)
                resp.raise_for_status()
                updates = resp.json().get("result", [])
        except Exception as exc:
            logger.error("Failed to fetch updates from Telegram: %s", exc)
            time.sleep(5)
            continue

        if not updates:
            continue

        logger.info("Retrieved %d pending updates.", len(updates))
        db: Session = SessionLocal()
        
        try:
            for update in updates:
                update_id = update.get("update_id")
                offset = update_id + 1

                message = update.get("message")
                if not message:
                    continue

                chat_id = str(message.get("chat", {}).get("id"))
                text = message.get("text")

                # Ignore non-text interactions (e.g. commands like /start or photo sharing)
                if not text or text.startswith("/"):
                    continue

                # SECURITY GATE: Reject non-authorized senders
                if chat_id != TELEGRAM_ALLOWED_CHAT_ID:
                    logger.warning("Blocked unauthorized message attempt from Chat ID: %s", chat_id)
                    continue

                logger.info("Ingesting text entry (len=%d) from authorized user", len(text))

                try:
                    is_reply = bool(message.get("reply_to_message"))
                    
                    if is_reply:
                        logger.info("Routing reply to ChatCopilot")
                        history = get_chat_history(db, chat_id, limit=10)
                        copilot = ChatCopilot()
                        
                        response_text = copilot.chat(history, text)
                        
                        save_chat_message(db, chat_id, "user", text)
                        save_chat_message(db, chat_id, "assistant", response_text)
                        
                        send_message(int(chat_id), response_text)
                    else:
                        logger.info("Routing new entry to JournalAnalyzer")
                        # Query Groq Cloud for CBT/psychological structured extraction
                        analysis = analyzer.analyze(text)
                        analysis_dict = analysis.model_dump()
        
                        # Generate embeddings and write directly to Supabase
                        save_entry(db, text, analysis_dict)
                        
                        # Save the initial bot response to memory as well so copilot has context
                        save_chat_message(db, chat_id, "user", text)
        
                        # Report key analysis stats back to user instantly
                        summary = "✅ **Journal Saved**\n\n"
                        
                        guidance = analysis_dict.get("motivational_guidance")
                        if guidance:
                            summary += f"💡 {guidance}\n\n"
                        
                        reframing = analysis_dict.get("reframing")
                        if reframing:
                            summary += f"🌱 **Perspective Shift**: {reframing}"
                        
                        save_chat_message(db, chat_id, "assistant", summary)
                        send_message(int(chat_id), summary)

                except Exception as exc:
                    logger.error("Failed to analyze and save message ID %d: %s", update_id, exc)
                    send_message(
                        int(chat_id), 
                        f"⚠️ **Processing Error**: Could not ingest journal. Technical logs reported:\n`{str(exc)}`"
                    )
        finally:
            db.close()


if __name__ == "__main__":
    # Initialize schema dynamically (first run hook)
    init_db()
    run_collector()

