"""Programmatic and CLI entry points."""
from __future__ import annotations

import argparse
import threading

from .agents import build_graph
from .config import load_settings


_graph = None
_graph_settings = None
_graph_lock = threading.Lock()


def _get_graph(settings):
    """Build the graph once per process and reuse its loaded models."""
    global _graph, _graph_settings
    if _graph is not None and _graph_settings == settings:
        return _graph

    with _graph_lock:
        if _graph is None or _graph_settings != settings:
            _graph = build_graph(settings)
            _graph_settings = settings
    return _graph


def run_once(
    user_input: str,
    learning_material: str = "",
    topic: str = "general",
    question_count: int | None = None,
    use_model_knowledge: bool = False,
    teaching_guidance: str = "",
    language_practice: bool = False,
    require_full_count: bool = False,
) -> dict:
    """Run the teacher graph once and return the final state."""
    settings = load_settings()
    graph = _get_graph(settings)
    initial_state: dict = {
        "topic": topic,
        "question_count": question_count or settings.default_question_count,
        "llm_calls": 0,
        "use_model_knowledge": use_model_knowledge,
    }
    if learning_material:
        initial_state["learning_material"] = learning_material
    if teaching_guidance:
        initial_state["teaching_guidance"] = teaching_guidance
    if language_practice:
        initial_state["language_practice"] = True
    if require_full_count:
        initial_state["require_full_count"] = True
    return graph.invoke(initial_state)


def run_cli() -> None:
    """Run the CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate an English quiz using AiMO agents."
    )
    parser.add_argument(
        "--topic",
        default="colours",
        help="Topic to quiz on (default: colours)",
    )
    parser.add_argument(
        "--material",
        default=None,
        help="TXT, Markdown or PDF file to base the quiz on (default: the model's own knowledge)",
    )
    parser.add_argument(
        "--questions",
        type=int,
        default=None,
        help="Number of quiz questions (default from settings)",
    )
    args = parser.parse_args()

    print(f"Generating quiz — topic: {args.topic}")
    material = ""
    if args.material:
        from .rag.document_loader import load_document

        material = load_document(args.material)
    result = run_once(
        "",
        learning_material=material,
        topic=args.topic,
        question_count=args.questions,
        use_model_knowledge=not material,
    )

    if result.get("error"):
        print(f"\nError: {result['error']}")
    elif result.get("quiz"):
        print(f"\n{result['quiz']}")
    else:
        print("\nNo quiz output produced.")


if __name__ == "__main__":
    run_cli()
