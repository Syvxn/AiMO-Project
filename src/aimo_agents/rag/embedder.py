"""Sentence-embedding wrapper using sentence-transformers (FOSS, Apache-2.0)."""
from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    """Thin wrapper around a SentenceTransformer model.

    Embeddings are L2-normalised so that dot-product equals cosine similarity.
    """

    def __init__(self, model_id: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self._model = SentenceTransformer(model_id)

    def embed(self, texts: list[str]) -> np.ndarray:
        """Return a (N, D) float32 array of normalised embeddings."""
        return self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
