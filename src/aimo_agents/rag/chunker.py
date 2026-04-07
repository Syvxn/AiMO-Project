"""Text chunking utilities."""
from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 40) -> list[str]:
    """Split *text* into overlapping windows measured in words.

    Args:
        text: Raw input text.
        chunk_size: Maximum number of words per chunk.
        overlap: Number of words shared between consecutive chunks.

    Returns:
        List of non-empty string chunks.
    """
    words = text.split()
    if not words:
        return []

    step = max(1, chunk_size - overlap)
    chunks: list[str] = []
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks
