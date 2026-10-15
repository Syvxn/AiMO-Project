import asyncio
from types import SimpleNamespace

import torch

from aimo_agents import runner
from aimo_agents.agents.teacher import graph
from aimo_agents.agents.teacher import nodes
from aimo_agents.server import QuizRequest, quiz_generate


def test_teacher_node_uses_supplied_material(monkeypatch):
    class UnexpectedRetriever:
        def invoke(self, _query):
            raise AssertionError("Supplied material should bypass global retrieval")

    monkeypatch.setattr(nodes, "retrieve_material_tool", UnexpectedRetriever())
    material = "The water cycle includes evaporation and condensation."

    result = nodes.teacher_tool_node({"topic": "water cycle", "learning_material": material})

    assert result["learning_material"] == material


def test_quiz_endpoint_passes_material_to_runner(monkeypatch):
    captured = {}

    def fake_run_once(*args, **kwargs):
        captured.update(args=args, kwargs=kwargs)
        return {"quiz": {"quiz_title": "Water Cycle", "questions": []}}

    monkeypatch.setattr(runner, "run_once", fake_run_once)
    request = QuizRequest(
        topic="water cycle",
        question_count=4,
        learning_material="Evaporation changes liquid water into vapor.",
    )

    response = asyncio.run(quiz_generate(request))

    assert response["quiz"]["quiz_title"] == "Water Cycle"
    assert captured["kwargs"] == {
        "learning_material": request.learning_material,
        "topic": "water cycle",
        "question_count": 4,
    }


def test_teacher_models_use_fp16_when_cuda_is_available(monkeypatch):
    calls = []

    class FakeTokenizerLoader:
        @staticmethod
        def from_pretrained(model_id):
            return model_id

    class FakeModelLoader:
        @staticmethod
        def from_pretrained(model_id, **options):
            calls.append((model_id, options))
            return object()

    monkeypatch.setattr(graph, "AutoTokenizer", FakeTokenizerLoader)
    monkeypatch.setattr(graph, "AutoModelForSeq2SeqLM", FakeModelLoader)
    monkeypatch.setattr(graph.torch.cuda, "is_available", lambda: True)
    settings = SimpleNamespace(
        teacher_model_id="teacher-model",
        teacher_distractor_model_id="distractor-model",
        device_map="auto",
        max_new_tokens=128,
        temperature=0.0,
    )

    graph.build_teacher_graph(settings)

    assert calls == [
        ("teacher-model", {"device_map": "auto", "torch_dtype": torch.float16}),
        ("distractor-model", {"device_map": "auto", "torch_dtype": torch.float16}),
    ]


def test_teacher_models_do_not_force_fp16_on_cpu(monkeypatch):
    calls = []

    class FakeTokenizerLoader:
        @staticmethod
        def from_pretrained(model_id):
            return model_id

    class FakeModelLoader:
        @staticmethod
        def from_pretrained(model_id, **options):
            calls.append((model_id, options))
            return object()

    monkeypatch.setattr(graph, "AutoTokenizer", FakeTokenizerLoader)
    monkeypatch.setattr(graph, "AutoModelForSeq2SeqLM", FakeModelLoader)
    monkeypatch.setattr(graph.torch.cuda, "is_available", lambda: False)
    settings = SimpleNamespace(
        teacher_model_id="teacher-model",
        teacher_distractor_model_id="distractor-model",
        device_map="cpu",
        max_new_tokens=128,
        temperature=0.0,
    )

    graph.build_teacher_graph(settings)

    assert calls == [
        ("teacher-model", {"device_map": "cpu"}),
        ("distractor-model", {"device_map": "cpu"}),
    ]


def test_quiz_generation_bounds_model_attempts(monkeypatch):
    calls = []
    monkeypatch.setattr(
        nodes,
        "_generate_qa",
        lambda **_kwargs: calls.append("qa") or "unparseable",
    )
    monkeypatch.setattr(nodes, "_parse_qa", lambda *_args: None)
    monkeypatch.setattr(nodes, "_build_material_based_questions", lambda **_kwargs: [])

    result = nodes.teacher_llm_call(
        {"learning_material": "A short lesson gives students useful facts.", "topic": "lesson", "question_count": 3},
        None,
        None,
        None,
        None,
        128,
        0.0,
    )

    assert len(calls) == 3
    assert result["error"]


def test_fallback_skips_source_questions_and_uses_neutral_stem(monkeypatch):
    monkeypatch.setattr(nodes, "_pick_cloze_token", lambda _sentence: "garden")
    monkeypatch.setattr(
        nodes,
        "_pick_distractors",
        lambda *_args: ["shelter", "river", "forest"],
    )

    questions = nodes._build_material_based_questions(
        "What problem did Jonah discover? Jonah found the map in the garden.",
        "class material",
        1,
        [],
    )

    assert len(questions) == 1
    question_text = questions[0]["question"]
    assert "What problem did Jonah discover" not in question_text
    assert "class material material" not in question_text
    assert question_text.endswith("?")


def test_fallback_ignores_textbook_headers_and_workshop_directions(monkeypatch):
    monkeypatch.setattr(nodes, "_pick_cloze_token", lambda _sentence: "map")
    monkeypatch.setattr(
        nodes,
        "_pick_distractors",
        lambda *_args: ["garden", "attic", "notebook"],
    )

    questions = nodes._build_material_based_questions(
        "Grade 5 English: Reading, Language, and Writing\n"
        "Page 3\n"
        "Reading Passage\n"
        "Maya discovered a folded map beneath a loose floorboard in her grandmother's attic.\n"
        "Writing Workshop\n"
        "Write five sentences describing a mysterious place.\n"
        "Unit 1 review: Explain the passage's main idea.",
        "Unit 1",
        1,
        [],
    )

    assert len(questions) == 1
    question_text = questions[0]["question"]
    assert "Maya discovered" in question_text
    assert "Grade 5" not in question_text
    assert "Writing Workshop" not in question_text
    assert "Write five" not in question_text


def test_quiz_context_preserves_lines_for_textbook_cleanup():
    material = (
        "Source: Grade 5 English textbook.pdf\n"
        "Chapter: Unit 1: The Secret Garden Map\n"
        "Grade 5 English: Reading, Language, and Writing\n"
        "Page 3\n"
        "Writing Workshop\n"
        "Write five sentences describing a mysterious place.\n"
        "Maya discovered a folded map beneath a loose floorboard in her grandmother's attic."
    )

    excerpt = nodes._limit_material_words(material, 100)
    passages = nodes._split_passages(excerpt)

    assert len(passages) == 1
    assert "Maya discovered" in passages[0]
    assert "Grade 5" not in passages[0]
    assert "Writing Workshop" not in passages[0]
    assert "Write five" not in passages[0]


def test_fallback_distractors_prefer_related_words_from_the_same_sentence():
    distractors = nodes._pick_distractors(
        "place",
        ["Maya", "garden", "person", "thing", "idea", "clearly"],
        "A precise noun names a person, place, thing, or idea clearly.",
    )

    assert distractors == ["person", "thing", "idea"]


def test_question_filter_rejects_unsupported_name_questions():
    assert not nodes._is_acceptable_question_text(
        "What was the name of the map Maya found in her grandmother's attic?"
    )


def test_teacher_node_returns_structured_quiz_after_saving(monkeypatch):
    saved_payloads = []

    class FakeQuizWriter:
        @staticmethod
        def invoke(payload):
            saved_payloads.append(payload)
            return "SUCCESS: The quiz has been saved."

    monkeypatch.setattr(nodes, "_generate_qa", lambda **_kwargs: "generated")
    monkeypatch.setattr(nodes, "_parse_qa", lambda *_args: ("What do plants use?", "Sunlight"))
    monkeypatch.setattr(nodes, "_generate_distractors", lambda **_kwargs: "generated")
    monkeypatch.setattr(nodes, "_parse_distractors", lambda *_args: ["Water", "Soil", "Air"])
    monkeypatch.setattr(nodes, "_postprocess", lambda questions: questions)
    monkeypatch.setattr(nodes, "create_quiz_tool", FakeQuizWriter())

    result = nodes.teacher_llm_call(
        {"learning_material": "Green plants use sunlight to make food.", "topic": "plants", "question_count": 1},
        None,
        None,
        None,
        None,
        128,
        0.0,
    )

    assert result["quiz"] == saved_payloads[0]
    assert result["quiz"]["quiz_title"] == "English Quiz: plants"
    assert len(result["quiz"]["questions"]) == 1