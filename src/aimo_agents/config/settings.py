"""Configuration scaffolding for the project."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Immutable configuration object passed to the graph and all agents."""

    # Hugging Face model IDs — one per agent role.
    # Any model that supports text-generation on HF Hub can be used here.
    orchestrator_model_id: str
    teacher_model_id: str

    # Controls how many new tokens the model is allowed to generate per call.
    # Increase this if quizzes are being cut off mid-output.
    max_new_tokens: int

    # Sampling temperature. 0.0 = deterministic (greedy). Higher = more creative.
    # Keep low for structured outputs like quizzes.
    temperature: float

    # Passed directly to the Hugging Face pipeline.
    # "auto"  — uses GPU if available, otherwise falls back to CPU.
    # "cpu"   — forces CPU inference (slow but universally compatible).
    device_map: str

    # Default quiz size used by the CLI and run_once().
    default_question_count: int


def load_settings() -> Settings:
    """Load runtime settings."""
    pass
