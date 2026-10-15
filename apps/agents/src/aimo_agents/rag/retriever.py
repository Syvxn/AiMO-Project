"""In-memory study-material retriever."""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from .chunker import chunk_text
from .document_loader import SUPPORTED_SUFFIXES, load_document
from .embedder import Embedder


class TxtRetriever:
    """Index supported study documents and retrieve relevant chunks."""

    def __init__(
        self,
        model_id: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 200,
        overlap: int = 40,
    ) -> None:
        self._embedder = Embedder(model_id)
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._chunks: list[str] = []
        self._embeddings: np.ndarray | None = None

    def load_dir(self, path: str) -> int:
        """Load supported files found recursively inside *path*."""
        if not os.path.isdir(path):
            raise FileNotFoundError(f"Material directory not found: {path}")

        texts: list[str] = []
        for root, _, filenames in os.walk(path):
            for filename in sorted(filenames):
                if Path(filename).suffix.lower() in SUPPORTED_SUFFIXES:
                    texts.append(load_document(os.path.join(root, filename)))

        return self._index(texts)

    def load_file(self, path: str) -> int:
        """Load a single supported study-material file."""
        return self._index([load_document(path)])

    def _index(self, texts: list[str]) -> int:
        chunks: list[str] = []
        for text in texts:
            chunks.extend(chunk_text(text, self._chunk_size, self._overlap))
        self._chunks = chunks
        self._embeddings = self._embedder.embed(chunks) if chunks else None
        return len(chunks)

    def query(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: float = 0.0,
    ) -> list[str]:
        """Return the top relevant chunks for *query*."""
        if not self._chunks or self._embeddings is None:
            return []

        q_emb = self._embedder.embed([query])
        scores = (self._embeddings @ q_emb.T).squeeze()

        k = min(top_k, len(self._chunks))
        if scores.ndim == 0:
            top_indices: list[int] = [0]
        else:
            top_indices = np.argsort(scores)[::-1][:k].tolist()

        return [
            self._chunks[i]
            for i in top_indices
            if float(scores[i] if scores.ndim > 0 else scores) >= score_threshold
        ]
