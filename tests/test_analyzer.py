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
