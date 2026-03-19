"""config/settings.py — Settings loader

All runtime configuration is read from environment variables or a .env file.
Copy .env.example to .env and edit the values before running the system.

To add a setting for a new agent:
  1. Add a new field to the Settings dataclass below.
  2. Read it in load_settings() using os.getenv().
    3. Reference it in core/graph.py when building that agent's pipeline.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


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


def load_settings() -> Settings:
    """Read configuration from environment variables or a .env file."""
    load_dotenv()
    return Settings(
        orchestrator_model_id=os.getenv("ORCHESTRATOR_MODEL_ID", "Qwen/Qwen2.5-7B-Instruct"),
        teacher_model_id=os.getenv("TEACHER_MODEL_ID", "Qwen/Qwen2.5-7B-Instruct"),
        max_new_tokens=int(os.getenv("MAX_NEW_TOKENS", "1024")),
        temperature=float(os.getenv("TEMPERATURE", "0.0")),
        device_map=os.getenv("DEVICE_MAP", "auto"),
    )
