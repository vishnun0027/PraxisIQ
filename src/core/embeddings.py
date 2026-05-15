from sentence_transformers import SentenceTransformer

# Lazy initialization singleton
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # all-MiniLM-L6-v2 is an excellent balance of speed and semantic quality
        # It produces 384-dimensional vectors
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def get_embedding(text: str) -> list[float]:
    """
    Generate a 384-dimensional semantic embedding via all-MiniLM-L6-v2.
    """
    model = _get_model()
    # model.encode returns a numpy array, we convert to a standard python list
    # for compatibility with database drivers
    embedding = model.encode(text)
    return embedding.tolist()
