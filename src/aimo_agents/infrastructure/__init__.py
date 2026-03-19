"""Infrastructure adapters (LLM providers, external clients)."""

from .llm import build_pipeline

__all__ = ["build_pipeline"]
