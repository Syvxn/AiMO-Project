import asyncio
import importlib
import json
import os
import queue
from pathlib import Path

import numpy as np

from aimo_agents import server
from aimo_agents.agents.teacher import nodes
from aimo_agents.config import load_settings
from aimo_agents.rag import retriever as retriever_module


class FakeInputs(dict):
    def to(self, _device):
        return self


class FakeTokenizer:
    def __call__(self, _prompt, return_tensors=None):
        return FakeInputs()


class FakeStreamer:
    def __init__(self, *_args, **_kwargs):
        self.tokens: queue.Queue = queue.Queue()

    def put_token(self, text):
        self.tokens.put(text)

    def end(self):
        self.tokens.put(None)

    def __iter__(self):
        return self

    def __next__(self):
        item = self.tokens.get(timeout=0.05)
        if item is None:
            raise StopIteration
        return item


def _collect_events(model):
    async def run():
        return [
            json.loads(chunk[len("data: "):])
            async for chunk in server._token_generator(FakeTokenizer(), model, "hi", 8)
        ]

    return asyncio.run(run())


def test_stream_reports_generation_failure_instead_of_hanging(monkeypatch):
    class FailingModel:
        device = "cpu"

        def generate(self, **_kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(server, "TextIteratorStreamer", FakeStreamer)

    events = _collect_events(FailingModel())

    assert [event["type"] for event in events] == ["error"]


def test_stream_times_out_when_the_model_never_answers(monkeypatch):
    class SilentModel:
        device = "cpu"

        def generate(self, **_kwargs):
            pass

    monkeypatch.setattr(server, "TextIteratorStreamer", FakeStreamer)

    events = _collect_events(SilentModel())

    assert [event["type"] for event in events] == ["error"]


def test_stream_yields_tokens_then_done(monkeypatch):
    class WorkingModel:
        device = "cpu"

        def generate(self, streamer, **_kwargs):
            streamer.put_token("Hello")
            streamer.put_token(" there")
            streamer.end()

    monkeypatch.setattr(server, "TextIteratorStreamer", FakeStreamer)

    events = _collect_events(WorkingModel())

    assert [event["type"] for event in events] == ["token", "token", "done"]
    assert "".join(event.get("text", "") for event in events) == "Hello there"


def test_excerpt_keeps_topic_blocks_from_long_material():
    paragraphs = [f"para{i}x " + "filler " * 28 for i in range(60)]
    paragraphs[57] = "Colours such as red and blue describe the colour of things. " + "more " * 20
    material = "\n\n".join(paragraphs)

    excerpt = nodes._select_material_excerpt(material, "colours", 100)

    assert "Colours such as red" in excerpt
    assert len(excerpt.split()) <= 100


def test_excerpt_samples_across_material_when_topic_does_not_match():
    material = "\n\n".join(f"para{i}x " + "filler " * 28 for i in range(60))

    excerpt = nodes._select_material_excerpt(material, "general", 200)

    assert any(f"para{i}x" in excerpt for i in range(30, 60))


def test_short_material_is_left_intact():
    material = "Plants use sunlight.\nThey make food."

    assert nodes._select_material_excerpt(material, "plants", 1200) == material


def test_retriever_never_indexes_uploads(monkeypatch, tmp_path):
    class FakeEmbedder:
        def __init__(self, *_args):
            pass

        def embed(self, texts):
            return np.zeros((len(texts), 2), dtype=np.float32)

    monkeypatch.setattr(retriever_module, "Embedder", FakeEmbedder)
    (tmp_path / "uploads").mkdir()
    (tmp_path / "chapter.txt").write_text("Shared chapter text.", encoding="utf-8")
    (tmp_path / "uploads" / "private.txt").write_text("Private class text.", encoding="utf-8")

    retriever = retriever_module.TxtRetriever()

    assert retriever.load_dir(str(tmp_path)) == 1
    assert retriever._chunks == ["Shared chapter text."]


def test_relative_material_dir_resolves_against_project_root(monkeypatch):
    monkeypatch.setenv("MATERIAL_DIR", os.path.join("data", "custom"))

    material_dir = Path(load_settings().material_dir)

    assert material_dir.is_absolute()
    assert material_dir.parts[-2:] == ("data", "custom")
    assert (material_dir.parents[1] / "pyproject.toml").exists()


def test_each_saved_quiz_gets_its_own_file(monkeypatch, tmp_path):
    create_quiz_module = importlib.import_module("aimo_agents.tools.create_quiz")
    # The tool derives the project root three directories above its own folder.
    monkeypatch.setattr(
        create_quiz_module.os.path,
        "abspath",
        lambda _path: str(tmp_path / "a" / "b" / "c" / "create_quiz.py"),
    )

    for _ in range(2):
        result = create_quiz_module.create_quiz.invoke({"quiz_title": "Quiz", "questions": []})
        assert result.startswith("SUCCESS")

    assert len(list((tmp_path / "generated_quizzes").glob("*.json"))) == 2
