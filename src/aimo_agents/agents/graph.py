"""LangGraph assembly — wires the teacher subgraph."""
from __future__ import annotations

from ..config import Settings
from .teacher.graph import build_teacher_graph


def build_graph(settings: Settings):
    """Build and return the parent graph.

    Currently routes all traffic directly to the teacher agent.
    The orchestrator routing layer will be wired in a future iteration.
    """
    return build_teacher_graph(settings)
