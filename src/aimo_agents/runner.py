"""Programmatic and CLI entry points."""
from __future__ import annotations

from .agents import build_graph
from .config import load_settings


def run_once(
    user_input: str,
    learning_material: str = "",
    topic: str = "general",
    question_count: int | None = None,
) -> dict:
    """Run the graph once and return the final state."""
    pass


def run_cli() -> None:
    """Run the CLI entrypoint."""
    pass


if __name__ == "__main__":
    run_cli()