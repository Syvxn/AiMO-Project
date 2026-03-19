"""state.py — Shared agent state

AgentState is the single data object that flows through every node in the graph.
LangGraph passes it into each agent node and merges the returned dict back into
the state automatically — agents only need to return the fields they changed.

Conventions
-----------
- Input fields are set once by the caller before the graph starts.
- Routing fields are set by the orchestrator and read by the graph's conditional edges.
- Agent-specific fields are only written by the agent that owns them.
- Shared output fields can be written by any agent.
- All fields are optional (total=False) because no single run will populate every field.

To add fields for a new agent, append a clearly labelled section at the bottom.
"""
from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AnyMessage


# All valid routing targets the orchestrator can emit.
# Add the new agent name here when adding a new agent to the graph.
Route = Literal["teacher", "end"]


class AgentState(TypedDict, total=False):
    # --- Input (set by the caller before invoking the graph) ---
    user_input: str          # The user's raw request text

    # --- Conversation history ---
    # operator.add means each node APPENDS to this list rather than replacing it.
    # This is how the full conversation is preserved across multiple LLM calls.
    messages: Annotated[list[AnyMessage], operator.add]

    # Tracks how many times the LLM has been called in this run.
    # Useful for debugging and enforcing call-count limits.
    llm_calls: int

    # --- Internal routing (managed by the orchestrator) ---
    route: Route             # Which agent should handle the request next
    active_agent: str        # Name of the agent currently handling the request

    # --- Teacher agent fields ---
    # These are provided by the caller when a quiz is expected.
    learning_material: str   # Source text the teacher uses to write quiz questions
    topic: str               # Optional topic focus (e.g. "photosynthesis")
    question_count: int      # How many MCQ questions to generate
    quiz: str                # The final MCQ quiz produced by the teacher agent

    # --- Shared output fields (written by any agent) ---
    agent_response: str      # Free-text response for agents that don't produce a quiz
    error: str               # Human-readable error message; set when a node cannot proceed
