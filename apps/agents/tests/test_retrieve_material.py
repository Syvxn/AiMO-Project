"""Tests for the TxtRetriever RAG module."""
from __future__ import annotations

import os
import tempfile

import pytest

from aimo_agents.rag import TxtRetriever
from aimo_agents.rag.chunker import chunk_text


# ---------------------------------------------------------------------------
# chunker
# ---------------------------------------------------------------------------

def test_chunk_text_basic():
    text = " ".join(["word"] * 500)
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    # Every chunk must have at most chunk_size words
    for chunk in chunks:
        assert len(chunk.split()) <= 100


def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_smaller_than_chunk_size():
    text = "short text here"
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert chunks == ["short text here"]


def test_chunk_overlap():
    words = list(range(20))
    text = " ".join(str(w) for w in words)
    chunks = chunk_text(text, chunk_size=10, overlap=5)
    # Second chunk should start at word index 5 (step = 10 - 5 = 5)
    assert chunks[1].split()[0] == "5"


# ---------------------------------------------------------------------------
# TxtRetriever — helpers
# ---------------------------------------------------------------------------

def _write_txt(directory: str, name: str, content: str) -> str:
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


BIO_TEXT = (
    "Photosynthesis is the process by which plants use sunlight, water, and "
    "carbon dioxide to produce oxygen and energy in the form of glucose. "
) * 30

CS_TEXT = (
    "A binary search tree is a data structure where each node has at most two "
    "children, referred to as the left child and the right child. "
) * 30


@pytest.fixture(scope="module")
def retriever():
    """Shared retriever instance (model loaded once per test session)."""
    return TxtRetriever(chunk_size=50, overlap=10)


# ---------------------------------------------------------------------------
# TxtRetriever — indexing
# ---------------------------------------------------------------------------

def test_load_single_file(retriever):
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_txt(tmpdir, "bio.txt", BIO_TEXT)
        n = retriever.load_file(os.path.join(tmpdir, "bio.txt"))
        assert n > 0


def test_load_dir_indexes_all_txt_files(retriever):
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_txt(tmpdir, "bio.txt", BIO_TEXT)
        _write_txt(tmpdir, "cs.txt", CS_TEXT)
        n = retriever.load_dir(tmpdir)
        assert n > 0


def test_load_dir_ignores_non_txt_files(retriever):
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_txt(tmpdir, "notes.txt", BIO_TEXT)
        other = os.path.join(tmpdir, "image.png")
        with open(other, "wb") as fh:
            fh.write(b"\x89PNG\r\n")
        n = retriever.load_dir(tmpdir)
        assert n > 0  # only notes.txt should be indexed, no crash


def test_load_dir_missing_raises(retriever):
    with pytest.raises(FileNotFoundError):
        retriever.load_dir("/nonexistent/path/xyz_aimo_test")


# ---------------------------------------------------------------------------
# TxtRetriever — retrieval
# ---------------------------------------------------------------------------

def test_query_returns_relevant_chunk(retriever):
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_txt(tmpdir, "bio.txt", BIO_TEXT)
        _write_txt(tmpdir, "cs.txt", CS_TEXT)
        retriever.load_dir(tmpdir)

        results = retriever.query("How do plants produce energy from sunlight?", top_k=2)
        assert len(results) >= 1
        assert any(
            "photosynthesis" in r.lower() or "plant" in r.lower() for r in results
        )


def test_query_empty_index_returns_empty_list():
    r = TxtRetriever(chunk_size=50, overlap=10)
    assert r.query("anything") == []


def test_query_top_k_respected(retriever):
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_txt(tmpdir, "bio.txt", BIO_TEXT)
        retriever.load_file(os.path.join(tmpdir, "bio.txt"))
        results = retriever.query("photosynthesis", top_k=2)
        assert len(results) <= 2


def test_query_top_k_larger_than_chunks():
    r = TxtRetriever(chunk_size=50, overlap=10)
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_txt(tmpdir, "tiny.txt", "Only a few words here.")
        r.load_file(os.path.join(tmpdir, "tiny.txt"))
        results = r.query("words", top_k=100)
        # Should not crash; returns however many chunks exist
        assert len(results) >= 1
