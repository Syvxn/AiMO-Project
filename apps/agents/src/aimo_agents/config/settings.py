"""Configuration scaffolding for the project."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"


@dataclass(frozen=True)
class Settings:
    """Immutable configuration object passed to the graph and all agents."""

    # Hugging Face instruction-tuned chat model IDs. Equal IDs share one loaded model.
    orchestrator_model_id: str
    teacher_model_id: str

    # Minimum new tokens per call; quiz generation raises this as needed per question.
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
    rag_chunk_size: int          # Chunk size in words.
    rag_chunk_overlap: int       # Overlap between consecutive chunks, in words.
    rag_top_k: int               # Number of chunks returned per retrieval query.
    rag_score_threshold: float   # Minimum cosine similarity to accept a chunk (0–1).
    teacher_quantization: str = "none"  # Optional CUDA NF4 loading for the teacher only.


def load_settings() -> Settings:
    """Load runtime settings from environment variables (with .env support)."""
    from dotenv import load_dotenv

    _root = Path(__file__).resolve().parents[3]  # AiMO-Agents/

    # Team-friendly loading order:
    # 1) .env provides shared defaults tracked in docs
    # 2) .env.local is optional, gitignored, and overrides per-developer machine
    load_dotenv(_root / ".env")
    load_dotenv(_root / ".env.local", override=True)

    return Settings(
        orchestrator_model_id=os.getenv("ORCHESTRATOR_MODEL_ID", DEFAULT_MODEL_ID),
        teacher_model_id=os.getenv("TEACHER_MODEL_ID", DEFAULT_MODEL_ID),
        max_new_tokens=int(os.getenv("MAX_NEW_TOKENS", "512")),
        temperature=float(os.getenv("TEMPERATURE", "0.2")),
        device_map=os.getenv("DEVICE_MAP", "auto"),
        default_question_count=int(os.getenv("DEFAULT_QUESTION_COUNT", "5")),
        material_dir=str(
            # Relative values resolve against the agents project root, not the current directory.
            _root / os.getenv("MATERIAL_DIR", str(Path("data") / "materials" / "chapters"))
        ),
        rag_model_id=os.getenv(
            "RAG_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        rag_chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "200")),
        rag_chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "40")),
        rag_top_k=int(os.getenv("RAG_TOP_K", "3")),
        rag_score_threshold=float(os.getenv("RAG_SCORE_THRESHOLD", "0.30")),
        teacher_quantization=os.getenv("TEACHER_QUANTIZATION", "none").lower(),
    )
