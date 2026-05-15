import os
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
    Stateless polling routine designed to be run intermittently/via crontab.
    Fetches pending messages, gates by authorized sender, extracts CBT metrics, 
    embeds vectors, persists to database, and acknowledges the queue.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing from environment variables")
        return
    if not TELEGRAM_ALLOWED_CHAT_ID:
        logger.error("TELEGRAM_ALLOWED_CHAT_ID is missing from environment variables")
        return

    logger.info("Starting Telegram Journal Ingestion Routine...")

    # 1. Fetch pending updates from Telegram
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{API_URL}/getUpdates")
            resp.raise_for_status()
            updates = resp.json().get("result", [])
    except Exception as exc:
        logger.error("Failed to fetch updates from Telegram: %s", exc)
        return

    if not updates:
        logger.info("No new messages in the Telegram queue.")
        return

    logger.info("Retrieved %d pending updates.", len(updates))

    # Pre-heat analyzer and database resources
    analyzer = JournalAnalyzer()
    db: Session = SessionLocal()
    
    last_update_id = -1
    processed_count = 0

    try:
        for update in updates:
            update_id = update.get("update_id")
            last_update_id = max(last_update_id, update_id)

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
                    processed_count += 1
                else:
                    logger.info("Routing new entry to JournalAnalyzer")
                    # 2. Query Groq Cloud for CBT/psychological structured extraction
                    analysis = analyzer.analyze(text)
                    analysis_dict = analysis.model_dump()
    
                    # 3. Generate embeddings and write directly to Supabase
                    save_entry(db, text, analysis_dict)
                    
                    # Save the initial bot response to memory as well so copilot has context
                    save_chat_message(db, chat_id, "user", text)
    
                    # 4. Report key analysis stats back to user instantly
                    summary = "✅ **Journal Saved**\n\n"
                    
                    guidance = analysis_dict.get("motivational_guidance")
                    if guidance:
                        summary += f"💡 {guidance}\n\n"
                    
                    reframing = analysis_dict.get("reframing")
                    if reframing:
                        summary += f"🌱 **Perspective Shift**: {reframing}"
                    
                    save_chat_message(db, chat_id, "assistant", summary)
                    send_message(int(chat_id), summary)
                    processed_count += 1

            except Exception as exc:
                logger.error("Failed to analyze and save message ID %d: %s", update_id, exc)
                send_message(
                    int(chat_id), 
                    f"⚠️ **Processing Error**: Could not ingest journal. Technical logs reported:\n`{str(exc)}`"
                )

    finally:
        db.close()

    # 5. Flush processed messages by shifting the offset + 1
    if last_update_id != -1:
        logger.info("Acknowledging read state to Telegram up to Offset: %d", last_update_id)
        try:
            with httpx.Client() as client:
                client.get(f"{API_URL}/getUpdates", params={"offset": last_update_id + 1})
        except Exception as exc:
            logger.error("Acknowledge request failed: %s", exc)

    logger.info("Ingestion completed. Saved %d entries safely to Supabase.", processed_count)


if __name__ == "__main__":
    # Initialize schema dynamically (first run hook)
    init_db()
    run_collector()
