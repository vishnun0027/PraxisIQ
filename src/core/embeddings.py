import os

import httpx

from src.core.logging import get_logger

logger = get_logger(__name__)

EMBEDDING_SERVER_URL = os.getenv("EMBEDDING_SERVER_URL", "http://127.0.0.1:8080/embed")


def get_embedding(text: str) -> list[float]:
    """
    Generate a 384-dimensional semantic embedding via the shared embedding microservice.
    """
    if not text or not text.strip():
        raise ValueError("Text must not be empty")

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(EMBEDDING_SERVER_URL, json={"text": text})
            resp.raise_for_status()
            return resp.json()["embedding"]
    except Exception as exc:
        logger.error("Failed to generate embedding via server: %s", exc)
        raise RuntimeError("Embedding service unavailable") from exc
