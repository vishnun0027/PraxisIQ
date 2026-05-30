import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.core.base import Base
from src.core.database import get_db
from src.main import app, verify_api_key

VALID_ANALYSIS_JSON = json.dumps(
    {
        "emotion_summary": "User shows signs of stress",
        "detected_emotions": ["stress"],
        "emotional_intensity": 5,
        "cognitive_distortions": ["catastrophizing"],
        "root_cause_analysis": "Work-related pressure",
        "action_steps": ["Take a break"],
        "reframing": "This is temporary",
        "motivational_guidance": "You are capable",
        "crisis_detected": False,
    }
)


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_verify_api_key():
        return "ci-dummy-api-key"

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key] = override_verify_api_key
    with patch("src.main.init_db"), TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestJournalEndpoint:
    @patch("src.main.journal_service.analyzer")
    def test_post_journal_success(self, mock_analyzer: MagicMock, client: TestClient) -> None:
        from src.analyzer import JournalAnalysis

        analysis = JournalAnalysis.model_validate_json(VALID_ANALYSIS_JSON)
        mock_analyzer.analyze = AsyncMock(return_value=analysis)

        response = client.post("/journal", json={"text": "I feel stressed"})
        assert response.status_code == 200

        data = response.json()
        assert data["text"] == "I feel stressed"
        assert data["analysis"]["detected_emotions"] == ["stress"]
        assert "id" in data
        assert "created_at" in data

    @patch("src.main.journal_service.analyzer")
    def test_post_journal_empty_text(self, mock_analyzer: MagicMock, client: TestClient) -> None:
        mock_analyzer.analyze = AsyncMock(side_effect=ValueError("Journal entry must not be empty"))

        response = client.post("/journal", json={"text": ""})
        assert response.status_code == 422

    @patch("src.main.journal_service.analyzer")
    def test_post_journal_llm_failure(self, mock_analyzer: MagicMock, client: TestClient) -> None:
        mock_analyzer.analyze = AsyncMock(side_effect=RuntimeError("Failed to generate"))

        response = client.post("/journal", json={"text": "test"})
        assert response.status_code == 503


class TestHistoryEndpoint:
    def test_get_history_empty(self, client: TestClient) -> None:
        response = client.get("/journal/history")
        assert response.status_code == 200
        assert response.json() == []

    @patch("src.main.journal_service.analyzer")
    def test_get_history_after_post(self, mock_analyzer: MagicMock, client: TestClient) -> None:
        from src.analyzer import JournalAnalysis

        analysis = JournalAnalysis.model_validate_json(VALID_ANALYSIS_JSON)
        mock_analyzer.analyze = AsyncMock(return_value=analysis)

        client.post("/journal", json={"text": "Entry 1"})
        client.post("/journal", json={"text": "Entry 2"})

        response = client.get("/journal/history")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2


class TestDetailEndpoint:
    def test_get_entry_not_found(self, client: TestClient) -> None:
        response = client.get("/journal/999")
        assert response.status_code == 404

    @patch("src.main.journal_service.analyzer")
    def test_get_entry_by_id(self, mock_analyzer: MagicMock, client: TestClient) -> None:
        from src.analyzer import JournalAnalysis

        analysis = JournalAnalysis.model_validate_json(VALID_ANALYSIS_JSON)
        mock_analyzer.analyze = AsyncMock(return_value=analysis)

        post_response = client.post("/journal", json={"text": "My entry"})
        entry_id = post_response.json()["id"]

        response = client.get(f"/journal/{entry_id}")
        assert response.status_code == 200
        assert response.json()["text"] == "My entry"


class TestClearEndpoint:
    @patch("src.main.clear_entries")
    def test_clear_all_entries(self, mock_clear_entries: MagicMock, client: TestClient) -> None:
        mock_clear_entries.return_value = 5

        response = client.delete("/journal/all")

        assert response.status_code == 200
        assert response.json() == {"deleted": 5}
        mock_clear_entries.assert_called_once()
