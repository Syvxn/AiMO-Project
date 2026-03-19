"""Tool registry exposed as one import surface."""

from .create_quiz import create_quiz
from .retrieve_material import retrieve_material
from .send_analytics import send_analytics

tools = [retrieve_material, create_quiz, send_analytics]
tools_by_name = {tool.name: tool for tool in tools}

__all__ = ["create_quiz", "retrieve_material", "send_analytics", "tools", "tools_by_name"]