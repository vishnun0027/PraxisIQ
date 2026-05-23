import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from src.analyzer import JournalAnalyzer, JournalAnalysis


VALID_ANALYSIS_JSON = json.dumps(
    {
        "emotion_summary": "User shows signs of stress and overwhelm",
        "detected_emotions": ["stress", "anxiety"],
        "emotional_intensity": 7,
        "cognitive_distortions": ["catastrophizing"],
        "root_cause_analysis": "Work pressure and critical feedback from manager",
        "action_steps": [
            "Practice mindful breathing for 5 minutes",
            "Write down three things that went well today",
        ],
        "reframing": "Mistakes are learning opportunities, not proof of failure",
        "motivational_guidance": "You are doing your best, and that is enough",
        "crisis_detected": False,
    }
)


class TestJournalAnalysis:
    def test_valid_analysis_parses(self) -> None:
        analysis = JournalAnalysis.model_validate_json(VALID_ANALYSIS_JSON)
        assert analysis.emotion_summary == "User shows signs of stress and overwhelm"
        assert analysis.detected_emotions == ["stress", "anxiety"]
        assert analysis.emotional_intensity == 7
        assert analysis.crisis_detected is False

    def test_invalid_intensity_rejected(self) -> None:
        data = json.loads(VALID_ANALYSIS_JSON)
        data["emotional_intensity"] = 15
        with pytest.raises(Exception):
            JournalAnalysis.model_validate(data)




# --- Parametrized: every individual emotion must be accepted ---
ALL_VALID_EMOTIONS = [
    "joy", "gratitude", "calm", "hope", "love", "excitement", "pride",
    "sadness", "anxiety", "stress", "anger", "frustration", "fear",
    "disgust", "shame", "guilt", "loneliness", "jealousy", "burnout", "overwhelm",
]

ALL_VALID_DISTORTIONS = [
    "catastrophizing", "all_or_nothing", "overgeneralization", "mind_reading",
    "negative_filtering", "emotional_reasoning", "should_statements",
    "labeling", "personalization", "magnification",
]


class TestAllEmotionsAccepted:
    @pytest.mark.parametrize("emotion", ALL_VALID_EMOTIONS)
    def test_single_emotion_accepted(self, emotion: str) -> None:
        data = json.loads(VALID_ANALYSIS_JSON)
        data["detected_emotions"] = [emotion]
        analysis = JournalAnalysis.model_validate(data)
        assert analysis.detected_emotions == [emotion]

    def test_all_emotions_at_once(self) -> None:
        data = json.loads(VALID_ANALYSIS_JSON)
        data["detected_emotions"] = ALL_VALID_EMOTIONS
        analysis = JournalAnalysis.model_validate(data)
        assert set(analysis.detected_emotions) == set(ALL_VALID_EMOTIONS)




class TestAllDistortionsAccepted:
    @pytest.mark.parametrize("distortion", ALL_VALID_DISTORTIONS)
    def test_single_distortion_accepted(self, distortion: str) -> None:
        data = json.loads(VALID_ANALYSIS_JSON)
        data["cognitive_distortions"] = [distortion]
        analysis = JournalAnalysis.model_validate(data)
        assert analysis.cognitive_distortions == [distortion]

    def test_all_distortions_at_once(self) -> None:
        data = json.loads(VALID_ANALYSIS_JSON)
        data["cognitive_distortions"] = ALL_VALID_DISTORTIONS
        analysis = JournalAnalysis.model_validate(data)
        assert set(analysis.cognitive_distortions) == set(ALL_VALID_DISTORTIONS)




class TestJournalAnalyzer:
    @pytest.mark.anyio
    async def test_empty_entry_raises(self) -> None:
        analyzer = JournalAnalyzer()
        with pytest.raises(ValueError, match="must not be empty"):
            await analyzer.analyze("")

    @pytest.mark.anyio
    async def test_whitespace_entry_raises(self) -> None:
        analyzer = JournalAnalyzer()
        with pytest.raises(ValueError, match="must not be empty"):
            await analyzer.analyze("   ")

    def test_prompt_contains_entry(self) -> None:
        analyzer = JournalAnalyzer()
        prompt = analyzer._build_prompt("I feel stressed today")
        assert "I feel stressed today" in prompt

    @pytest.mark.anyio
    @patch("src.analyzer.get_llm")
    async def test_analyze_returns_valid_analysis(self, mock_get_llm: MagicMock) -> None:
        mock_response = JournalAnalysis.model_validate_json(VALID_ANALYSIS_JSON)
        
        mock_structured_llm = MagicMock()
        mock_structured_llm.ainvoke = AsyncMock(return_value=mock_response)
        
        analyzer = JournalAnalyzer()
        analyzer._llm = mock_structured_llm

        result = await analyzer.analyze("I feel stressed at work")

        assert isinstance(result, JournalAnalysis)
        assert result.detected_emotions == ["stress", "anxiety"]
        mock_structured_llm.ainvoke.assert_called_once()
