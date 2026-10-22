"""Teacher subgraph — generate → END."""
from __future__ import annotations

from functools import partial

from langgraph.graph import END, StateGraph

from ...config import Settings
from ...models import load_causal_lm
from .nodes import teacher_llm_call
from .state import TeacherState


def build_teacher_graph(settings: Settings):
    """Build and return the compiled teacher subgraph."""
    quantization = getattr(settings, "teacher_quantization", "none")
    options = {"quantization": quantization} if quantization != "none" else {}
    tokenizer, model = load_causal_lm(settings.teacher_model_id, settings.device_map, **options)

    graph = StateGraph(TeacherState)
    graph.add_node(
        "generate",
        partial(
            teacher_llm_call,
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=settings.max_new_tokens,
            temperature=settings.temperature,
        ),
    )
    graph.set_entry_point("generate")
    graph.add_edge("generate", END)
    return graph.compile()
