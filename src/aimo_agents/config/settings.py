"""Configuration scaffolding for the project."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


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

    # RAG settings
    material_dir: str       # Directory containing .txt study material files.
    rag_model_id: str       # Sentence-transformers model used for embeddings.
    rag_chunk_size: int     # Chunk size in words.
    rag_chunk_overlap: int  # Overlap between consecutive chunks, in words.
    rag_top_k: int          # Number of chunks returned per retrieval query.


def load_settings() -> Settings:
    """Load runtime settings from environment variables (with .env support)."""
    from dotenv import load_dotenv
    load_dotenv()

    _root = Path(__file__).resolve().parents[3]  # AiMO-Agents/

    return Settings(
        orchestrator_model_id=os.getenv(
            "ORCHESTRATOR_MODEL_ID", "HuggingFaceTB/SmolLM2-360M-Instruct"
        ),
        teacher_model_id=os.getenv(
            "TEACHER_MODEL_ID", "HuggingFaceTB/SmolLM2-360M-Instruct"
        ),
        max_new_tokens=int(os.getenv("MAX_NEW_TOKENS", "512")),
        temperature=float(os.getenv("TEMPERATURE", "0.2")),
        device_map=os.getenv("DEVICE_MAP", "auto"),
        default_question_count=int(os.getenv("DEFAULT_QUESTION_COUNT", "5")),
        material_dir=os.getenv("MATERIAL_DIR", str(_root / "data" / "materials")),
        rag_model_id=os.getenv(
            "RAG_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        rag_chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "200")),
        rag_chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "40")),
        rag_top_k=int(os.getenv("RAG_TOP_K", "3")),
    )
