import asyncio
import json
import logging
from types import SimpleNamespace

import pytest
import torch

from aimo_agents import models, runner
from aimo_agents.agents.teacher import graph, nodes
from aimo_agents.server import QuizRequest, quiz_generate

SOURCE = "Green plants use sunlight to make food. Roots take in water from the soil."


def item(question, options, answer):
    return {"question": question, "options": options, "answer": answer}


SUNLIGHT = item("What do green plants need to make their food?", ["Sunlight", "Sand", "Plastic", "Gravel"], "A")
SOIL = item("Where do roots take in water from?", ["The soil", "The sky", "A cloud", "The moon"], "A")
PLANET = item("Which planet is closest to the sun?", ["Mercury", "Venus", "Mars", "Earth"], "A")


def reply(*items):
    return json.dumps({"questions": list(items)})


class FakeQuizWriter:
    def __init__(self):
        self.saved = []

    def invoke(self, payload):
        self.saved.append(payload)
        return "SUCCESS"


@pytest.fixture
def writer(monkeypatch):
    fake = FakeQuizWriter()
    monkeypatch.setattr(nodes, "create_quiz_tool", fake)
    return fake


def script_model(monkeypatch, *outputs):
    """Make each model call return the next scripted output and record the prompts."""
    prompts = []
    remaining = iter(outputs)

    def fake_run_chat(_model, _tokenizer, messages, max_new_tokens, temperature):
        prompts.append(messages[-1]["content"])
        return next(remaining)

    monkeypatch.setattr(nodes, "_run_chat", fake_run_chat)
    return prompts


def generate(state):
    return nodes.teacher_llm_call(state, None, None, 128, 0.0)


def answer_text(question):
    return question["options"][ord(question["answer"]) - ord("A")].split(": ", 1)[1]


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
        "use_model_knowledge": False,
    }


def test_quiz_endpoint_forwards_the_model_knowledge_flag(monkeypatch):
    captured = {}

    def fake_run_once(*_args, **kwargs):
        captured.update(kwargs)
        return {"quiz": {"quiz_title": "Colours", "questions": []}}

    monkeypatch.setattr(runner, "run_once", fake_run_once)

    asyncio.run(quiz_generate(QuizRequest(topic="colours", use_model_knowledge=True)))

    assert captured["use_model_knowledge"] is True
    assert captured["learning_material"] == ""


def test_teacher_graph_loads_the_shared_model_once(monkeypatch):
    calls = []
    monkeypatch.setattr(graph, "load_causal_lm", lambda model_id, device_map: calls.append((model_id, device_map)) or ("tok", "model"))
    settings = SimpleNamespace(teacher_model_id="chat-model", device_map="auto", max_new_tokens=128, temperature=0.0)

    graph.build_teacher_graph(settings)

    assert calls == [("chat-model", "auto")]


def test_quiz_comes_from_the_supplied_material(monkeypatch, writer):
    prompts = script_model(monkeypatch, reply(SUNLIGHT, SOIL))

    result = generate({"learning_material": SOURCE, "topic": "plants", "question_count": 2})

    questions = result["quiz"]["questions"]
    assert {answer_text(q) for q in questions} == {"Sunlight", "The soil"}
    assert result["quiz"]["quiz_title"] == "English Quiz: plants"
    assert "shortfall" not in result["quiz"]
    assert "ONLY the source text" in prompts[0]
    assert SOURCE in prompts[0]
    assert writer.saved[0]["questions"] == questions


def test_answers_not_found_in_the_source_are_rejected(monkeypatch, writer):
    script_model(monkeypatch, reply(PLANET, SUNLIGHT), reply(PLANET), reply(PLANET))

    result = generate({"learning_material": SOURCE, "topic": "plants", "question_count": 2})

    assert [answer_text(q) for q in result["quiz"]["questions"]] == ["Sunlight"]
    assert result["quiz"]["shortfall"] == 1


def test_missing_questions_are_requested_again_without_repeats(monkeypatch, writer):
    prompts = script_model(monkeypatch, reply(SUNLIGHT), reply(SOIL))

    result = generate({"learning_material": SOURCE, "topic": "plants", "question_count": 2})

    assert len(result["quiz"]["questions"]) == 2
    assert result["llm_calls"] == 2
    assert "Write 1 multiple-choice" in prompts[1]
    assert SUNLIGHT["question"] in prompts[1]


def test_model_attempts_are_bounded(monkeypatch, writer):
    prompts = script_model(monkeypatch, "no json", "still nothing", "nope", "never reached")

    result = generate({"learning_material": SOURCE, "topic": "plants", "question_count": 3})

    assert len(prompts) == 3
    assert result["error"]
    assert writer.saved == []


def test_a_question_that_reveals_another_answer_is_dropped(monkeypatch, writer):
    leaky = item("Why do plants need sunlight to make food?", ["For energy", "For noise", "For cold", "For sand"], "A")
    script_model(monkeypatch, reply(SUNLIGHT, leaky), reply(leaky), reply(leaky))

    result = generate({"learning_material": SOURCE, "topic": "plants", "question_count": 2})

    assert [answer_text(q) for q in result["quiz"]["questions"]] == ["Sunlight"]


def test_no_material_without_permission_does_not_call_the_model(monkeypatch, writer):
    prompts = script_model(monkeypatch)

    result = generate({"topic": "colours", "question_count": 2})

    assert result["error"]
    assert prompts == []


def test_model_knowledge_quiz_when_allowed(monkeypatch, writer):
    capital = item("What is the capital city of France?", ["Paris", "Rome", "Madrid", "Berlin"], "A")
    prompts = script_model(monkeypatch, reply(capital))

    result = generate({"topic": "France", "question_count": 1, "use_model_knowledge": True})

    assert answer_text(result["quiz"]["questions"][0]) == "Paris"
    assert "own knowledge" in prompts[0]
    assert "source text" not in prompts[0]


def test_correct_answer_position_is_shuffled(monkeypatch, writer):
    positions = set()
    for _ in range(40):
        script_model(monkeypatch, reply(SUNLIGHT))
        result = generate({"learning_material": SOURCE, "topic": "plants", "question_count": 1})
        positions.add(result["quiz"]["questions"][0]["answer"])

    assert len(positions) > 1


def test_parse_questions_handles_prose_fences_and_truncation():
    wrapped = "Sure!\n```json\n" + reply(SUNLIGHT) + "\n```"
    truncated = reply(SUNLIGHT, SOIL)[:-30]

    assert [q["question"] for q in nodes._parse_questions(wrapped)] == [SUNLIGHT["question"]]
    assert [q["question"] for q in nodes._parse_questions(truncated)] == [SUNLIGHT["question"]]
    assert nodes._parse_questions("no json here") == []


@pytest.mark.parametrize(
    ("answer", "expected"),
    [("B", 1), ("b", 1), ("(C)", 2), ("D.", 3), ("Venus", 1), ("venus", 1), (2, None), ("E", None), ("Pluto", None)],
)
def test_correct_index_accepts_letters_or_option_text(answer, expected):
    assert nodes._correct_index(answer, ["Mercury", "Venus", "Mars", "Earth"]) == expected


def test_options_that_depend_on_position_are_rejected():
    assert not nodes._is_acceptable_options(["Red", "Blue", "Green", "All of the above"])
    assert not nodes._is_acceptable_options(["Red", "Blue", "red", "Green"])
    assert nodes._is_acceptable_options(["Red", "Blue", "Green", "Yellow"])


def test_run_chat_uses_the_model_device_and_returns_only_new_text():
    class Batch(dict):
        moved_to = None

        def to(self, device):
            self.moved_to = device
            return self

    class Tokenizer:
        pad_token_id = None
        eos_token_id = 7

        def __init__(self):
            self.batch = Batch(input_ids=torch.tensor([[1, 2, 3]]))
            self.decoded = None

        def apply_chat_template(self, _messages, tokenize, add_generation_prompt):
            return "prompt"

        def __call__(self, _prompt, return_tensors=None):
            return self.batch

        def decode(self, ids, skip_special_tokens=False):
            self.decoded = ids.tolist()
            return " text "

    class Model:
        device = "cuda:0"

        def __init__(self):
            self.kwargs = None

        def generate(self, **kwargs):
            self.kwargs = kwargs
            return torch.tensor([[1, 2, 3, 4, 5]])

    tokenizer, greedy, sampled = Tokenizer(), Model(), Model()

    assert nodes._run_chat(greedy, tokenizer, [], 32, 0.0) == "text"
    nodes._run_chat(sampled, tokenizer, [], 32, 0.3)

    assert tokenizer.batch.moved_to == "cuda:0"
    assert tokenizer.decoded == [4, 5]
    assert greedy.kwargs["do_sample"] is False and "temperature" not in greedy.kwargs
    assert greedy.kwargs["pad_token_id"] == 7
    assert sampled.kwargs["do_sample"] is True and sampled.kwargs["temperature"] == 0.3


@pytest.mark.parametrize(("bf16", "expected"), [(True, torch.bfloat16), (False, torch.float16)])
def test_gpu_load_uses_half_precision(monkeypatch, bf16, expected):
    monkeypatch.setattr(models.torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(models.torch.cuda, "is_bf16_supported", lambda: bf16)

    assert models._load_options("auto") == {"device_map": "auto", "torch_dtype": expected}


def test_cpu_device_map_never_requests_half_precision(monkeypatch):
    monkeypatch.setattr(models.torch.cuda, "is_available", lambda: True)

    assert models._load_options("cpu") == {"device_map": "cpu"}


def test_missing_cuda_is_reported_loudly(monkeypatch, caplog):
    monkeypatch.setattr(models.torch.cuda, "is_available", lambda: False)

    with caplog.at_level(logging.WARNING, logger=models.logger.name):
        assert models._load_options("auto") == {"device_map": "auto"}

    assert "CUDA is not available" in caplog.text


def test_loader_reuses_one_model_per_id(monkeypatch):
    loads = []

    class Tokenizers:
        @staticmethod
        def from_pretrained(model_id):
            return f"tokenizer:{model_id}"

    class Models:
        @staticmethod
        def from_pretrained(model_id, **options):
            loads.append((model_id, options))
            return SimpleNamespace(device="cuda:0")

    monkeypatch.setattr(models, "_cache", {})
    monkeypatch.setattr(models, "AutoTokenizer", Tokenizers)
    monkeypatch.setattr(models, "AutoModelForCausalLM", Models)
    monkeypatch.setattr(models.torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(models.torch.cuda, "is_bf16_supported", lambda: True)

    first = models.load_causal_lm("chat-model", "auto")
    second = models.load_causal_lm("chat-model", "auto")

    assert first is second
    assert loads == [("chat-model", {"device_map": "auto", "torch_dtype": torch.bfloat16})]


def test_loader_explains_a_model_that_is_not_causal(monkeypatch):
    class Tokenizers:
        @staticmethod
        def from_pretrained(_model_id):
            return object()

    class Models:
        @staticmethod
        def from_pretrained(_model_id, **_options):
            raise ValueError("Unrecognized configuration class T5Config for this kind of AutoModel")

    monkeypatch.setattr(models, "_cache", {})
    monkeypatch.setattr(models, "AutoTokenizer", Tokenizers)
    monkeypatch.setattr(models, "AutoModelForCausalLM", Models)

    with pytest.raises(RuntimeError, match="not a causal language model"):
        models.load_causal_lm("t5-model", "cpu")
