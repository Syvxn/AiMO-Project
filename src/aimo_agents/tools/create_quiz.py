"""Quiz generation tool scaffold."""
from __future__ import annotations

from langchain_core.tools import tool


@tool
def create_quiz(material: str, topic: str = "general", question_count: int = 5) -> str:
    """Create a quiz from the provided material."""
    pass