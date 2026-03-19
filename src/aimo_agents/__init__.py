"""aimo_agents — Multi-Agent Teaching Assistant

This package implements a minimal multi-agent system using LangGraph.
Two agents are wired together:
  - Orchestrator : reads the user request and routes it to the right agent.
  - Teacher      : generates a multiple-choice quiz from learning material.

Package layout
--------------
  config/              — settings schema and environment loading
  core/                — shared state contract + graph assembly
  infrastructure/      — external adapters (LLM providers)
  app/                 — programmatic and CLI entry points
  agents/              — one folder per agent package
  agents/orchestrator/ — orchestrator agent (agent.py, prompts.py)
  agents/teacher/      — teacher agent (agent.py, prompts.py, tools.py)

How to add a new agent
----------------------
  1. Create a folder:    agents/<name>/
  2. Add agent logic:    agents/<name>/agent.py   (node functions)
  3. Add the prompt:     agents/<name>/prompts.py (prompt templates)
  4. Add tools if any:   agents/<name>/tools.py   (@tool-decorated functions)
  5. Register the node and edge in core/graph.py
  6. Add the new route literal to core/state.py → Route
  7. Expose via __all__ here if needed

Public API
----------
  from aimo_agents import run_once, build_graph, AgentState
"""

from .app.runner import run_once
from .core.graph import build_graph
from .core.state import AgentState

__all__ = ["run_once", "build_graph", "AgentState"]
