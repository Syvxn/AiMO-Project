"""Analytics reporting tool scaffold."""
from __future__ import annotations

from langchain_core.tools import tool


@tool
def send_analytics(event: str, payload: dict) -> str:
    """Send an analytics event with an associated payload."""
    pass
