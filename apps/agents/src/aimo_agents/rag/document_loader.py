"""Load supported study-material files into plain text."""
from __future__ import annotations

from pathlib import Path

SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf"}


def load_document(path: str | Path) -> str:
    """Return the readable text from a TXT, Markdown, or PDF document."""
    document_path = Path(path)
    suffix = document_path.suffix.lower()

    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported material type: {suffix or '<none>'}")

    if suffix in {".txt", ".md"}:
        return document_path.read_text(encoding="utf-8")

    from pypdf import PdfReader

    pages = PdfReader(str(document_path)).pages
    return "\n\n".join(page.extract_text() or "" for page in pages).strip()
