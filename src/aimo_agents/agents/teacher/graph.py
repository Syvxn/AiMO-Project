"""Teacher subgraph — retrieve → generate → END."""
from __future__ import annotations

from functools import partial

from langgraph.graph import END, StateGraph
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from ...config import Settings
from .nodes import teacher_llm_call, teacher_tool_node
from .state import TeacherState


def build_teacher_graph(settings: Settings):
    """Build and return the compiled teacher subgraph."""
    try:
        qa_tokenizer = AutoTokenizer.from_pretrained(settings.teacher_model_id)
        qa_model = AutoModelForSeq2SeqLM.from_pretrained(
            settings.teacher_model_id,
            device_map=settings.device_map,
        )

        distractor_tokenizer = AutoTokenizer.from_pretrained(
            settings.teacher_distractor_model_id
        )
        distractor_model = AutoModelForSeq2SeqLM.from_pretrained(
            settings.teacher_distractor_model_id,
            device_map=settings.device_map,
        )
    except ValueError as exc:
        if "upgrade torch to at least v2.6" in str(exc):
            raise RuntimeError(
                "Incompatible torch version detected while loading HuggingFace model. "
                "Install torch>=2.6.0 in this environment and retry."
            ) from exc
        raise

    graph = StateGraph(TeacherState)
    graph.add_node("retrieve", teacher_tool_node)
    graph.add_node(
        "generate",
        partial(
            teacher_llm_call,
            qa_model=qa_model,
            qa_tokenizer=qa_tokenizer,
            distractor_model=distractor_model,
            distractor_tokenizer=distractor_tokenizer,
            max_new_tokens=settings.max_new_tokens,
            temperature=settings.temperature,
        ),
    )
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()