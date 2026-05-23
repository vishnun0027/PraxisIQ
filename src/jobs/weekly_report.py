import os
from dotenv import load_dotenv

# Load env before imports
load_dotenv(override=True)

from langchain_core.messages import SystemMessage, HumanMessage
from src.core.database import SessionLocal, init_db
from src.core.crud import get_recent_entries
from src.core.logging import get_logger
from src.bot.collector import send_message
from src.analyzer import get_llm

logger = get_logger(__name__)

def run_weekly_report() -> None:
    chat_id = os.getenv("TELEGRAM_ALLOWED_CHAT_ID")
    if not chat_id:
        logger.error("TELEGRAM_ALLOWED_CHAT_ID not found.")
        return

    db = SessionLocal()
    try:
        entries = get_recent_entries(db, days=7)
        if not entries:
            logger.info("No entries this week.")
            send_message(
                int(chat_id),
                "📅 **Weekly Check-in**\n\nYou haven't journaled any entries this week. Take a few minutes today to check in with yourself!"
            )
            return

        logger.info("Found %d entries for the weekly report.", len(entries))

        # Format entries for the LLM
        formatted_entries = ""
        for entry in entries:
            formatted_entries += f"--- Entry (Intensity: {entry.analysis.get('emotional_intensity')}/10) ---\n"
            formatted_entries += f"Text: {entry.text}\n"
            formatted_entries += f"Emotions: {', '.join(entry.analysis.get('detected_emotions', []))}\n"
            formatted_entries += f"Distortions: {', '.join(entry.analysis.get('cognitive_distortions', []))}\n\n"

        # Initialize LLM using shared logic
        llm = get_llm()

        messages = [
            SystemMessage(content=(
                "You are the PraxisIQ assistant, a compassionate CBT-trained therapist. "
                "You are providing a weekly digest of the user's journal entries. "
                "Analyze the provided journal entries from the past 7 days. "
                "Highlight emotional trends, recurring cognitive distortions, and offer "
                "a supportive, overarching cognitive reframing for the week. "
                "Format using markdown. Keep it concise, insightful, and highly supportive."
            )),
            HumanMessage(content=formatted_entries)
        ]

        logger.info("Generating report via Groq...")
        response = llm.invoke(messages)
        report = response.content

        # Add a nice header
        final_message = f"📅 **Your PraxisIQ Weekly Digest**\n\n{report}"

        send_message(int(chat_id), final_message)
        logger.info("Weekly report sent successfully.")

    except Exception as exc:
        logger.error("Failed to generate or send weekly report: %s", exc)
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    run_weekly_report()
