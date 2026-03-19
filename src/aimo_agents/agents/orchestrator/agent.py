"""orchestrator/agent.py — Orchestrator agent node

The orchestrator is the entry point of every request.
It reads the user's input, asks the LLM which agent should handle it,
and returns a routing decision that the LangGraph conditional edge reads.

Responsibilities
----------------
- Validate that input is not empty.
- Format the routing prompt and call the LLM.
- Parse the LLM's one-word response into a valid Route.
- Set active_agent so downstream code knows who is handling the request.

This node does NOT generate content — it only routes.
Keep it lightweight and fast; use a smaller model here if possible.

Prompt location: agents/orchestrator/prompts.py
"""
from __future__ import annotations

from langchain_core.runnables import Runnable

from .prompts import ORCHESTRATOR_PROMPT
from ...core.state import AgentState


def orchestrator_node(state: AgentState, llm: Runnable) -> AgentState:
    """Route the user's request to the appropriate agent.

    Returns a partial AgentState with only `route` (and optionally
    `active_agent` or `error`) — LangGraph merges this into the full state.
    """
    user_input = state.get("user_input", "").strip()

    if not user_input:
        return {"route": "end", "error": "No input received."}

    prompt = ORCHESTRATOR_PROMPT.format(user_input=user_input)

    # The LLM is expected to return exactly one word matching an agent name.
    decision = str(llm.invoke(prompt)).strip().lower()

    if "teacher" in decision:
        return {"route": "teacher", "active_agent": "teacher"}

    # No agent matched — surface an informative error rather than silently ending.
    return {"route": "end", "error": f"No agent matched the request: '{user_input}'."}
