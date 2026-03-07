import json
import pytest
from unittest.mock import MagicMock, patch

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

    def test_invalid_emotion_rejected(self) -> None:
        data = json.loads(VALID_ANALYSIS_JSON)
        data["detected_emotions"] = ["invalid_emotion"]
        with pytest.raises(Exception):
            JournalAnalysis.model_validate(data)

    def test_invalid_distortion_rejected(self) -> None:
        data = json.loads(VALID_ANALYSIS_JSON)
        data["cognitive_distortions"] = ["made_up_distortion"]
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

    @pytest.mark.parametrize("bad_emotion", ["happy", "positive", "angry", "scared", "bored", "confused", ""])
    def test_invalid_emotion_values_rejected(self, bad_emotion: str) -> None:
        data = json.loads(VALID_ANALYSIS_JSON)
        data["detected_emotions"] = [bad_emotion]
        with pytest.raises(Exception):
            JournalAnalysis.model_validate(data)


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

    @pytest.mark.parametrize("bad_distortion", ["overthinking", "rumination", "projection", ""])
    def test_invalid_distortion_values_rejected(self, bad_distortion: str) -> None:
        data = json.loads(VALID_ANALYSIS_JSON)
        data["cognitive_distortions"] = [bad_distortion]
        with pytest.raises(Exception):
            JournalAnalysis.model_validate(data)


class TestJournalAnalyzer:
    def test_empty_entry_raises(self) -> None:
        analyzer = JournalAnalyzer()
        with pytest.raises(ValueError, match="must not be empty"):
            analyzer.analyze("")

    def test_whitespace_entry_raises(self) -> None:
        analyzer = JournalAnalyzer()
        with pytest.raises(ValueError, match="must not be empty"):
            analyzer.analyze("   ")

    def test_prompt_contains_entry(self) -> None:
        analyzer = JournalAnalyzer()
        prompt = analyzer._build_prompt("I feel stressed today")
        assert "I feel stressed today" in prompt
        assert "JSON" in prompt

    @patch("src.analyzer._llm")
    def test_analyze_returns_valid_analysis(self, mock_llm: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.content = VALID_ANALYSIS_JSON
        mock_llm.invoke.return_value = mock_response

        analyzer = JournalAnalyzer()
        analyzer._llm = mock_llm

        result = analyzer.analyze("I feel stressed at work")

        assert isinstance(result, JournalAnalysis)
        assert result.detected_emotions == ["stress", "anxiety"]
        mock_llm.invoke.assert_called_once()

    @patch("src.analyzer._llm")
    def test_analyze_retries_on_invalid_json(self, mock_llm: MagicMock) -> None:
        bad_response = MagicMock()
        bad_response.content = "not json at all"

        good_response = MagicMock()
        good_response.content = VALID_ANALYSIS_JSON

        mock_llm.invoke.side_effect = [bad_response, good_response]

        analyzer = JournalAnalyzer()
        analyzer._llm = mock_llm

        result = analyzer.analyze("test entry")
        assert isinstance(result, JournalAnalysis)
        assert mock_llm.invoke.call_count == 2

    @patch("src.analyzer._llm")
    def test_analyze_raises_after_max_retries(self, mock_llm: MagicMock) -> None:
        bad_response = MagicMock()
        bad_response.content = "bad json"
        mock_llm.invoke.return_value = bad_response

        analyzer = JournalAnalyzer()
        analyzer._llm = mock_llm

        with pytest.raises(RuntimeError, match="Failed to generate"):
            analyzer.analyze("test entry")
        assert mock_llm.invoke.call_count == 3
