"""In-memory TXT retriever — the core of the lightweight RAG system."""
from __future__ import annotations

import os

import numpy as np

from .chunker import chunk_text
from .embedder import Embedder


class TxtRetriever:
    """Index .txt files and retrieve the most relevant chunks for a query.

    Usage::

        retriever = TxtRetriever()
        retriever.load_dir("/path/to/materials")
        chunks = retriever.query("explain photosynthesis", top_k=3)
    """

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

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def load_dir(self, path: str) -> int:
        """Load every ``*.txt`` file found directly inside *path*.

        Returns:
            Number of chunks indexed.

        Raises:
            FileNotFoundError: If *path* does not exist.
        """
        if not os.path.isdir(path):
            raise FileNotFoundError(f"Material directory not found: {path}")

        texts: list[str] = []
        for fname in sorted(os.listdir(path)):
            if fname.lower().endswith(".txt"):
                fpath = os.path.join(path, fname)
                with open(fpath, "r", encoding="utf-8") as fh:
                    texts.append(fh.read())

        return self._index(texts)

    def load_file(self, path: str) -> int:
        """Load a single ``*.txt`` file.

        Returns:
            Number of chunks indexed.
        """
        with open(path, "r", encoding="utf-8") as fh:
            return self._index([fh.read()])

    def _index(self, texts: list[str]) -> int:
        chunks: list[str] = []
        for text in texts:
            chunks.extend(chunk_text(text, self._chunk_size, self._overlap))
        self._chunks = chunks
        if chunks:
            self._embeddings = self._embedder.embed(chunks)
        return len(chunks)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def query(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: float = 0.0,
    ) -> list[str]:
        """Return the *top_k* most relevant text chunks for *query*.

        Args:
            query: Search query string.
            top_k: Maximum number of chunks to return.
            score_threshold: Minimum cosine similarity (0–1) a chunk must reach
                to be included. Chunks below this value are discarded even if
                they rank in the top-k. Set to 0.0 to disable filtering.

        Returns:
            List of matching chunks ordered by descending similarity.
            Empty when the index is empty or no chunk clears the threshold.
        """
        if not self._chunks or self._embeddings is None:
            return []

        q_emb = self._embedder.embed([query])           # (1, D)
        scores = (self._embeddings @ q_emb.T).squeeze() # (N,) cosine similarities

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
