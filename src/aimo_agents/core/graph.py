"""graph.py — LangGraph graph assembly

This file is the single source of truth for how agents are connected.
If you want to understand the flow of a request, start here.

Current flow
------------
  START
    └─► orchestrator
          ├─(route="teacher")─► teacher_llm_call
          │                       ├─(tool calls)─► teacher_tool ─► teacher_llm_call (loop)
          │                       └─(done)───────────────────────────────────────── ► END
          └─(route="end")────────────────────────────────────────────────────────── ► END

How to add a new agent
----------------------
  1. Build its pipeline:  <name>_llm = build_pipeline(settings.<name>_model_id, settings)
  2. Register its nodes:  graph.add_node(...)
    3. Add routing:         update orchestrator conditional_edges + core/state.py Route
  4. Add exit edge:       graph.add_edge("<name>", END)
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from ..agents.orchestrator.agent import orchestrator_node
from ..agents.teacher.agent import (
    teacher_llm_call,
    teacher_should_continue,
    teacher_tool_node,
)
from ..config import Settings
from ..infrastructure.llm import build_pipeline
from .state import AgentState


def build_graph(settings: Settings):
    """Instantiate all agent pipelines and compile the LangGraph StateGraph.

    Each agent receives its own pipeline so models and settings can differ
    per role without affecting other agents.
    """
    # --- Build one LLM pipeline per agent ---
    orchestrator_llm = build_pipeline(settings.orchestrator_model_id, settings)
    teacher_llm = build_pipeline(settings.teacher_model_id, settings)

    graph = StateGraph(AgentState)

    # --- Register nodes ---
    # Each node is a function: AgentState -> partial AgentState.
    # LangGraph merges the returned dict back into the shared state automatically.
    graph.add_node("orchestrator",    lambda s: orchestrator_node(s, orchestrator_llm))
    graph.add_node("teacher_llm_call", lambda s: teacher_llm_call(s, teacher_llm))
    graph.add_node("teacher_tool",     teacher_tool_node)

    # --- Edges ---
    # Every request starts at the orchestrator.
    graph.add_edge(START, "orchestrator")

    # Orchestrator routes to the entry node of the appropriate agent.
    graph.add_conditional_edges(
        "orchestrator",
        lambda s: s.get("route", "end"),
        {
            "teacher": "teacher_llm_call",  # entry point of the teacher ReAct loop
            "end": END,
        },
    )

    # Teacher ReAct loop:
    # After each LLM call, check whether to run tools or stop.
    graph.add_conditional_edges(
        "teacher_llm_call",
        teacher_should_continue,
        {
            "teacher_tool": "teacher_tool",
            END: END,
        },
    )

    # After tools run, loop back to the LLM for the next reasoning step.
    graph.add_edge("teacher_tool", "teacher_llm_call")

    return graph.compile()
