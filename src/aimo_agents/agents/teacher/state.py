"""State contract for the teacher agent."""
from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage


class TeacherState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], operator.add]  # Full conversation history
    llm_calls: int          # Number of LLM calls made this run
    learning_material: str  # Source text to base the quiz on
    topic: str              # Topic focus for the quiz
    question_count: int     # Number of MCQ questions to generate
    quiz: str               # Final quiz output
    agent_response: str     # Free-text response when no quiz is produced
    error: str              # Set when the agent cannot proceed
