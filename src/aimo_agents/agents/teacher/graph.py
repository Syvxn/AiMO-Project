"""Teacher subgraph — retrieve → generate → END."""
from __future__ import annotations

from functools import partial

from langgraph.graph import END, StateGraph
from langchain_huggingface import HuggingFacePipeline
from transformers import pipeline as hf_pipeline

from ...config import Settings
from .nodes import teacher_llm_call, teacher_tool_node
from .state import TeacherState


def build_teacher_graph(settings: Settings):
    """Build and return the compiled teacher subgraph."""
    pipeline_kwargs: dict = {
        "model": settings.teacher_model_id,
        "max_new_tokens": settings.max_new_tokens,
        "return_full_text": False,
        "device_map": settings.device_map,
    }
    if settings.temperature > 0:
        pipeline_kwargs["do_sample"] = True
        pipeline_kwargs["temperature"] = settings.temperature
    else:
        pipeline_kwargs["do_sample"] = False

    pipe = hf_pipeline("text-generation", **pipeline_kwargs)
    llm = HuggingFacePipeline(pipeline=pipe)

    graph = StateGraph(TeacherState)
    graph.add_node("retrieve", teacher_tool_node)
    graph.add_node("generate", partial(teacher_llm_call, llm=llm))
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()