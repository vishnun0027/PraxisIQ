import json
import time
from typing import List, Literal
from pydantic import BaseModel, Field, ValidationError
from langchain_ollama import ChatOllama


class JournalAnalysis(BaseModel):
    """
    Structured analysis of a journal entry with CBT-style insights. 
    All fields are required and must adhere to specified formats and constraints.
    """

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

llm = ChatOllama(model="gpt-oss:120b-cloud", temperature=0.0)
model_with_structure = llm.with_structured_output(JournalAnalysis)
response = model_with_structure.invoke(
    "I feel completely overwhelmed at work. My manager keeps pointing out mistakes. I feel likeI will fail and everything will collapse."
)


class JournalAnalyzer:
    def __init__(self, model_name: str, temperature: float = 0.0) -> None:
        self._llm = ChatOllama(model=model_name, temperature=temperature)

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
{entry}
"""

    def _parse_response(self, content: str) -> JournalAnalysis:
        parsed = json.loads(content)
        return JournalAnalysis(**parsed)

    def analyze(self, entry: str, max_retries: int = 3) -> JournalAnalysis:
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
    analyzer = JournalAnalyzer(model_name="gpt-oss:120b-cloud")

    journal_entry = """
    I feel completely overwhelmed at work.
    My manager keeps pointing out mistakes.
    I feel like I will fail and everything will collapse.
    """

    analysis = analyzer.analyze(journal_entry)
    print(analysis.model_dump_json(indent=2))
