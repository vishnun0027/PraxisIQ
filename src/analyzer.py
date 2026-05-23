from pathlib import Path

import yaml
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field
from src.core.logging import get_logger

logger = get_logger(__name__)

_llm_instance: ChatGroq | None = None


def _initialize_model() -> ChatGroq:
    config_path = Path("config/llm_model.yaml")

    if not config_path.exists():
        raise FileNotFoundError("llm_model.yaml not found")

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return ChatGroq(
        model=config["model_name"],
        temperature=config.get("temperature", 0.0),
        timeout=config.get("timeout"),
        max_retries=config.get("max_retries", 3),
    )


def get_llm() -> ChatGroq:
    """Lazily initialize the LLM singleton on first call."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = _initialize_model()
    return _llm_instance


class JournalAnalysis(BaseModel):
    emotion_summary: str = Field(
        description="Brief summary of the user's emotional state"
    )

    detected_emotions: list[str] = Field(
        description="List of detected emotions (e.g. joy, sadness, anxiety, relief, pride, etc.)"
    )

    emotional_intensity: int = Field(
        ge=1,
        le=10,
        description="Overall emotional intensity score from 1 (low) to 10 (very high)",
    )

    cognitive_distortions: list[str] = Field(
        description="Detected cognitive distortions (e.g. catastrophizing, all_or_nothing, etc.)"
    )

    root_cause_analysis: str = Field(
        description="Likely psychological root cause of emotional state"
    )

    action_steps: list[str] = Field(
        min_length=1, description="Practical, actionable improvement steps"
    )

    reframing: str = Field(description="CBT-style cognitive reframing")

    motivational_guidance: str = Field(
        description="Encouraging motivational support message"
    )

    crisis_detected: bool = Field(
        description="True if crisis or self-harm language is detected"
    )


class JournalAnalyzer:
    def __init__(self) -> None:
        self._structured_llm = None

    @property
    def _llm(self):
        if self._structured_llm is None:
            self._structured_llm = get_llm().with_structured_output(JournalAnalysis)
        return self._structured_llm

    @_llm.setter
    def _llm(self, value):
        self._structured_llm = value

    def _build_prompt(self, entry: str) -> str:
        return f"""
You are the PraxisIQ assistant, specialized in CBT-style structured analysis.

Analyze the following journal entry and structure the feedback according to the required schema.
Accurately detect emotional labels, assign a severity rating (1-10), catch common cognitive distortions,
outline root causes, offer practical actionable steps, frame the experience under a cognitive reframing lens, and note potential self-harm crises.

Journal Entry:
\"\"\"
{entry.strip()}
\"\"\"
"""

    async def analyze(self, entry: str) -> JournalAnalysis:
        if not entry or not entry.strip():
            raise ValueError("Journal entry must not be empty")

        # ainvoke() returns a validated JournalAnalysis model directly
        try:
            return await self._llm.ainvoke(self._build_prompt(entry))
        except Exception as exc:
            logger.error("Failed to analyze journal entry: %s", exc)
            raise RuntimeError("Failed to generate structured analysis via Groq") from exc

class ChatCopilot:
    def __init__(self) -> None:
        self._llm = get_llm()
        
    async def chat(self, chat_history: list, new_message: str) -> str:
        messages = [
            SystemMessage(content=(
                "You are the PraxisIQ assistant, a compassionate CBT-trained therapist. "
                "You are following up with the user on their journal entries. "
                "Provide therapeutic, helpful, and supportive responses. Keep responses concise and natural. "
                "Do not be overly clinical."
            ))
        ]
        
        for msg in chat_history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
                
        messages.append(HumanMessage(content=new_message))
        
        try:
            response = await self._llm.ainvoke(messages)
            return response.content
        except Exception as exc:
            logger.error("Failed to generate chat response: %s", exc)
            raise RuntimeError("Failed to generate response via Groq") from exc
