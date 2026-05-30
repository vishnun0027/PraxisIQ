from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_get_embedding():
    """Mock get_embedding globally during testing to return a dummy vector."""
    dummy_vector = [0.1] * 384
    with (
        patch("src.core.embeddings.get_embedding", return_value=dummy_vector),
        patch("src.services.journal_service.get_embedding", return_value=dummy_vector),
    ):
        yield
