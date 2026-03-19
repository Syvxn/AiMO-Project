"""app/runner.py — Entry points

Provides two ways to run the system:

  run_once()  — programmatic API; call this from tests, notebooks, or other code.
  run_cli()   — interactive CLI; launched via the `quiz-run` script in pyproject.toml.

For integration into a larger application, import and call run_once() directly.
The CLI is intended for local development and manual testing only.
"""
from __future__ import annotations

from ..config import load_settings
from ..core.graph import build_graph
from ..core.state import AgentState


def run_once(
    user_input: str,
    # Teacher agent fields — only read if the orchestrator routes to "teacher".
    # Pass defaults if you are not targeting the teacher agent.
    learning_material: str = "",
    topic: str = "general",
    learner_level: str = "beginner",
    question_count: int = 5,
) -> AgentState:
    """Run the multi-agent graph for one request and return the final state.

    Args:
        user_input:        The user's request text (required).
        learning_material: Source text for the teacher agent to base the quiz on.
        topic:             Optional topic hint to focus the quiz.
        learner_level:     Difficulty — "beginner", "intermediate", or "advanced".
        question_count:    Number of MCQ questions to generate.

    Returns:
        The final AgentState after all nodes have run. Check state["error"] first;
        if absent, the relevant output field (e.g. state["quiz"]) holds the result.
    """
    settings = load_settings()
    app = build_graph(settings)

    initial_state: AgentState = {
        "user_input": user_input,
        "learning_material": learning_material,
        "topic": topic,
        "learner_level": learner_level,
        "question_count": question_count,
    }

    return app.invoke(initial_state)


def run_cli() -> None:
    print("=== AiMO Multi-Agent System ===\n")

    user_input = input("Request:\n> ").strip()

    print("\n--- Teacher agent settings ---")
    learning_material = input("Learning material:\n> ").strip()
    topic = input("Topic focus [general]: ").strip() or "general"
    learner_level = (
        input("Learner level (beginner / intermediate / advanced) [beginner]: ").strip()
        or "beginner"
    )
    raw_count = input("Number of questions [5]: ").strip() or "5"
    try:
        question_count = max(1, int(raw_count))
    except ValueError:
        question_count = 5

    print("\nProcessing…\n")
    result = run_once(
        user_input=user_input,
        learning_material=learning_material,
        topic=topic,
        learner_level=learner_level,
        question_count=question_count,
    )

    if result.get("error"):
        print(f"[Error] {result['error']}")
    elif result.get("quiz"):
        print(f"=== {result.get('active_agent', 'agent').capitalize()} agent ===\n")
        print(result["quiz"])
    else:
        print(result.get("agent_response", "No response generated."))


if __name__ == "__main__":
    run_cli()
