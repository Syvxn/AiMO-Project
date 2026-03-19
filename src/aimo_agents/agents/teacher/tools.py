"""teacher/tools.py — Tools available to the teacher agent

These tools are called by the teacher agent during its ReAct loop.
Each tool stub below has a docstring describing its intended behaviour —
fill in the implementation when you are ready.

Tool list
---------
  retrieve_material : fetch learning content from a source (e.g. DB, PDF, vector store)
  create_quiz       : generate a structured MCQ quiz from retrieved material

Usage in the graph
------------------
  1. Pass `tools` to model.bind_tools() in llm.py or the teacher's llm_call node.
  2. The `tools_by_name` dict is used in teacher_tool_node() to dispatch calls.
"""
from __future__ import annotations

from langchain.tools import tool


@tool
def retrieve_material(chapter: str, topic: str) -> str:
    """Retrieve learning material for a given chapter and topic.

    Args:
        chapter: The chapter to retrieve material from (e.g. 'chapter 3').
        topic:   The specific topic within that chapter (e.g. 'photosynthesis').

    Returns:
        The retrieved learning material as a string.
    """
    pass


@tool
def create_quiz(material: str) -> str:
    """Create a multiple-choice quiz based on the provided learning material.

    Always call retrieve_material first and pass its output here.

    Args:
        material: The learning material text to base the quiz on.

    Returns:
        A formatted MCQ quiz string.
    """
    pass


# All tools the teacher agent is allowed to call.
# Extend this list when adding new tools.
tools = [retrieve_material, create_quiz]

# Lookup dict used in teacher_tool_node() to dispatch tool calls by name.
tools_by_name = {t.name: t for t in tools}
