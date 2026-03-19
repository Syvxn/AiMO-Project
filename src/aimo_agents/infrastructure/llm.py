"""llm.py — Hugging Face pipeline builder

This module is the only place in the codebase that talks directly to Hugging Face.
All agents receive a LangChain-compatible Runnable from build_pipeline() and never
import transformers themselves — this keeps agent logic model-agnostic.

To swap the inference backend (e.g. vLLM, llama.cpp) in the future, only this
file needs to change. Agent and graph code stays the same.
"""
from __future__ import annotations

from transformers import pipeline as hf_pipeline
from langchain_huggingface import HuggingFacePipeline

from ..config import Settings


def build_pipeline(model_id: str, settings: Settings) -> HuggingFacePipeline:
    """Load a Hugging Face text-generation model and wrap it as a LangChain Runnable.

    Args:
        model_id: A Hugging Face model repo ID (e.g. "Qwen/Qwen2.5-7B-Instruct").
        settings: The shared Settings object loaded from the environment.

    Returns:
        A HuggingFacePipeline that any agent node can call with .invoke(prompt).
    """
    pipe = hf_pipeline(
        task="text-generation",
        model=model_id,
        tokenizer=model_id,
        max_new_tokens=settings.max_new_tokens,
        temperature=settings.temperature,
        # do_sample must be True for temperature > 0 to have any effect.
        do_sample=settings.temperature > 0,
        # "auto" places layers on GPU if available, CPU otherwise.
        device_map=settings.device_map,
    )
    return HuggingFacePipeline(pipeline=pipe)
