"""Material retrieval tool — backed by the lightweight TXT RAG module."""
from __future__ import annotations

from langchain_core.tools import tool

from ..config import Settings, load_settings
from ..rag import TxtRetriever

# Module-level singletons — initialised lazily on first tool call.
_settings: Settings | None = None
_retriever: TxtRetriever | None = None


def _get_retriever() -> TxtRetriever:
    global _settings, _retriever
    if _retriever is None:
        _settings = load_settings()
        _retriever = TxtRetriever(
            model_id=_settings.rag_model_id,
            chunk_size=_settings.rag_chunk_size,
            overlap=_settings.rag_chunk_overlap,
        )
        try:
            _retriever.load_dir(_settings.material_dir)
        except FileNotFoundError:
            pass  # No material directory yet; queries will return empty results.
    return _retriever


@tool
def retrieve_material(chapter: str, topic: str) -> str:
    """Retrieve the most relevant learning material passages for a chapter and topic.

    Performs a semantic search over all .txt files in the configured material
    directory and returns the top matching passages joined by separators.

    Always call this tool before create_quiz so the quiz is grounded in real
    study material.
    """
    retriever = _get_retriever()
    assert _settings is not None  # set by _get_retriever()

    query = f"{chapter} {topic}"
    chunks = retriever.query(query, top_k=_settings.rag_top_k)

    if not chunks:
        return (
            f"No material found for chapter '{chapter}' on topic '{topic}'. "
            "Make sure .txt files are present in the material directory."
        )

    return "\n\n---\n\n".join(chunks)
