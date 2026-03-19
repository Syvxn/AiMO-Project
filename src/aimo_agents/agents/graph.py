"""LangGraph assembly scaffold."""
from __future__ import annotations

from ..config import Settings
from .orchestrator.state import OrchestratorState
from .teacher.state import TeacherState


def build_graph(settings: Settings):
    """Build and return the parent graph.

    The parent graph wires the orchestrator and teacher subgraphs together.
    Each subgraph operates on its own state (OrchestratorState / TeacherState);
    the parent maps fields across the subgraph boundaries.
    """
    pass
