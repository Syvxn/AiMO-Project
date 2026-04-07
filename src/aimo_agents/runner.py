"""Programmatic and CLI entry points."""
from __future__ import annotations

import argparse

from .agents import build_graph
from .config import load_settings


def run_once(
    user_input: str,
    learning_material: str = "",
    topic: str = "general",
    question_count: int | None = None,
) -> dict:
    """Run the teacher graph once and return the final state."""
    settings = load_settings()
    graph = build_graph(settings)
    initial_state: dict = {
        "topic": topic,
        "question_count": question_count or settings.default_question_count,
        "llm_calls": 0,
    }
    if learning_material:
        initial_state["learning_material"] = learning_material
    return graph.invoke(initial_state)


def run_cli() -> None:
    """Run the CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate an English quiz using AiMO agents."
    )
    parser.add_argument(
        "--topic",
        default="colours",
        help="Topic / chapter to quiz on (default: colours)",
    )
    parser.add_argument(
        "--questions",
        type=int,
        default=None,
        help="Number of quiz questions (default from settings)",
    )
    args = parser.parse_args()

    print(f"Generating quiz — topic: {args.topic}")
    result = run_once("", topic=args.topic, question_count=args.questions)

    if result.get("error"):
        print(f"\nError: {result['error']}")
    elif result.get("quiz"):
        print(f"\n{result['quiz']}")
    else:
        print("\nNo quiz output produced.")


if __name__ == "__main__":
    run_cli()