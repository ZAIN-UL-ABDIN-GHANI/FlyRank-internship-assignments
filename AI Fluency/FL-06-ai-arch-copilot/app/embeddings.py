from typing import List, Protocol

import numpy as np


class Embedder(Protocol):
    def encode(self, texts: List[str]) -> np.ndarray: ...


class SentenceTransformerEmbedder:
    """Production embedder backed by a local sentence-transformers model."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def encode(self, texts: List[str]) -> np.ndarray:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return np.array(vectors, dtype="float32")


_embedder: Embedder = None


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        from app.config import settings

        _embedder = SentenceTransformerEmbedder(settings.embedding_model)
    return _embedder


def set_embedder(embedder: Embedder) -> None:
    """Override the active embedder. Used in tests to avoid network calls."""
    global _embedder
    _embedder = embedder
