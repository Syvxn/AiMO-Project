"""Material retrieval tool."""
from __future__ import annotations

from langchain_core.tools import tool


@tool
def retrieve_material(chapter: str, topic: str) -> str:
    """Retrieve learning material for a chapter and topic."""
    pass