import json
import time
from pathlib import Path
from typing import List, Literal

import yaml
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field, ValidationError


class JournalAnalysis(BaseModel):
    emotion_summary: str = Field(
        description="Brief summary of the user's emotional state"
    )

    detected_emotions: List[
        Literal["stress", "anxiety", "frustration", "burnout", "sadness", "positive"]
    ] = Field(description="List of detected core emotions using only allowed values")

    emotional_intensity: int = Field(
        ge=1,
        le=10,
        description="Overall emotional intensity score from 1 (low) to 10 (very high)",
    )

    cognitive_distortions: List[
        Literal[
            "catastrophizing",
            "all_or_nothing",
            "overgeneralization",
            "mind_reading",
            "negative_filtering",
        ]
    ] = Field(description="Detected cognitive distortions using only allowed values")

    root_cause_analysis: str = Field(
        description="Likely psychological root cause of emotional state"
    )

    action_steps: List[str] = Field(
        min_length=1, description="Practical, actionable improvement steps"
    )

    reframing: str = Field(description="CBT-style cognitive reframing")

    motivational_guidance: str = Field(
        description="Encouraging motivational support message"
    )

    crisis_detected: bool = Field(
        description="True if crisis or self-harm language is detected"
    )

    analysis_confidence: float = Field(
        ge=0.0, le=1.0, description="Model confidence score between 0 and 1"
    )


def _initialize_model() -> ChatOllama:
    config_path = Path("config.yaml")

    if not config_path.exists():
        raise FileNotFoundError("config.yaml not found")

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return ChatOllama(
        model=config["model_name"],
        temperature=config.get("temperature", 0.0),
        format=config.get("format", "json"),
        timeout=config.get("timeout"),
        num_predict=config.get("num_predict"),
        top_p=config.get("top_p"),
        repeat_penalty=config.get("repeat_penalty"),
    )


_llm = _initialize_model()


class JournalAnalyzer:
    def __init__(self) -> None:
        self._llm = _llm

    def _build_prompt(self, entry: str) -> str:
        return f"""
You are a mental clarity assistant specialized in CBT-style structured analysis.

Return ONLY strict JSON.
No markdown.
No commentary.
No additional keys.
No trailing text.

Allowed detected_emotions:
["stress","anxiety","frustration","burnout","sadness","positive"]

Allowed cognitive_distortions:
["catastrophizing","all_or_nothing","overgeneralization","mind_reading","negative_filtering"]

Constraints:
- emotional_intensity: integer 1-10
- analysis_confidence: float 0-1
- crisis_detected: true or false
- Use only allowed literal values
- Ensure valid JSON format

Required structure:

{{
  "emotion_summary": string,
  "detected_emotions": [string],
  "emotional_intensity": integer,
  "cognitive_distortions": [string],
  "root_cause_analysis": string,
  "action_steps": [string],
  "reframing": string,
  "motivational_guidance": string,
  "crisis_detected": boolean,
  "analysis_confidence": float
}}

Journal Entry:
{entry.strip()}
"""

    def _parse_response(self, content: str) -> JournalAnalysis:
        parsed = json.loads(content)
        return JournalAnalysis.model_validate(parsed)

    def analyze(self, entry: str, max_retries: int = 3) -> JournalAnalysis:
        if not entry or not entry.strip():
            raise ValueError("Journal entry must not be empty")

        last_error: Exception | None = None

        for _ in range(max_retries):
            response = self._llm.invoke(self._build_prompt(entry))

            try:
                return self._parse_response(response.content)
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                time.sleep(0.5)

        raise RuntimeError("Failed to generate valid structured output") from last_error


if __name__ == "__main__":
    analyzer = JournalAnalyzer()

    journal_entry = """
    I feel completely overwhelmed at work.
    My manager keeps pointing out mistakes.
    I feel like I will fail and everything will collapse.
    """

    analysis = analyzer.analyze(journal_entry)
    print(analysis.model_dump_json(indent=2))
