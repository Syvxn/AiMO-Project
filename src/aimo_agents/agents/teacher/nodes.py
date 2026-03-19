"""Teacher node scaffolding."""
from __future__ import annotations

from langchain_core.runnables import Runnable

from .state import TeacherState


def teacher_llm_call(state: TeacherState, llm: Runnable) -> TeacherState:
    """Run the teacher LLM step."""
    pass


def teacher_tool_node(state: TeacherState) -> TeacherState:
    """Run the teacher tool step."""
    pass