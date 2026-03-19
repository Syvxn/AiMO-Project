"""Orchestrator node scaffolding."""
from __future__ import annotations

from langchain_core.runnables import Runnable

from .state import OrchestratorState


def orchestrator_llm_call(state: OrchestratorState, llm: Runnable) -> OrchestratorState:
    """Run the orchestrator LLM step."""
    pass


def orchestrator_tool_node(state: OrchestratorState) -> OrchestratorState:
    """Run any orchestrator tool step."""
    pass