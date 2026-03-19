"""teacher/agent.py — Teacher agent nodes (ReAct loop)

The teacher agent uses a ReAct (Reason + Act) loop to generate a quiz:
  1. teacher_llm_call    : The LLM reasons and decides whether to call a tool
                           or produce the final quiz output.
  2. teacher_tool_node   : Executes whichever tools the LLM requested and
                           appends the results to the message history.
  3. teacher_should_continue : Conditional edge — routes back to teacher_llm_call
                               if the LLM made tool calls, or to END if it is done.

Flow
----
  teacher_llm_call
    └─► teacher_should_continue ──(tool calls)──► teacher_tool_node ──► teacher_llm_call
                                ──(no tool calls)──────────────────────────────────► END

Prompt location : agents/teacher/prompts.py
Tools location  : agents/teacher/tools.py
"""
from __future__ import annotations

from langchain_core.runnables import Runnable
from langgraph.graph import END

from ...core.state import AgentState
from .tools import tools_by_name


def teacher_llm_call(state: AgentState, llm: Runnable) -> AgentState:
    """Node: LLM reasoning step.

    The model receives the current message history and decides to either:
    - Call one or more tools (e.g. retrieve_material, create_quiz), or
    - Produce the final quiz and stop.

    Increments llm_calls so callers can track model usage.
    """
    pass


def teacher_tool_node(state: AgentState) -> AgentState:
    """Node: Tool execution step.

    Iterates over all tool calls in the last LLM message, dispatches each
    to the matching function in tools_by_name, and appends a ToolMessage
    containing the result so the LLM can see it on the next turn.
    """
    pass


def teacher_should_continue(state: AgentState) -> str:
    """Conditional edge: decide whether to loop or stop.

    Inspects the last message in state["messages"].
    Returns:
        "teacher_tool"  — if the LLM produced tool calls (loop continues)
        END             — if the LLM produced a plain response (loop ends)
    """
    pass
