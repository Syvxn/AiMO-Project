from types import SimpleNamespace

import pytest
import torch

from aimo_agents import models
from aimo_agents.agents.teacher import graph


def test_nf4_loading_uses_gpu_compute_dtype(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "is_bf16_supported", lambda: True)
    monkeypatch.setattr(models, "BitsAndBytesConfig", lambda **kw: SimpleNamespace(**kw))

    options = models._load_options("auto", "4bit")

    assert options["device_map"] == "auto"
    assert options["quantization_config"].load_in_4bit is True
    assert options["quantization_config"].bnb_4bit_quant_type == "nf4"
    assert options["quantization_config"].bnb_4bit_compute_dtype == torch.bfloat16


@pytest.mark.parametrize("device", ["cpu", "auto"])
def test_nf4_does_not_silently_fall_back_to_cpu(monkeypatch, device):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(RuntimeError, match="requires a CUDA GPU"):
        models._load_options(device, "4bit")


def test_quantized_and_plain_models_have_separate_cache_entries(monkeypatch):
    loads = []
    monkeypatch.setattr(models, "_cache", {})
    monkeypatch.setattr(models, "AutoTokenizer", SimpleNamespace(from_pretrained=lambda _: "tokenizer"))
    monkeypatch.setattr(models, "AutoModelForCausalLM", SimpleNamespace(
        from_pretrained=lambda name, **kw: loads.append((name, kw)) or SimpleNamespace(device="cuda:0")))
    monkeypatch.setattr(models, "_load_options", lambda device, mode: {"device_map": device, "mode": mode})

    plain = models.load_causal_lm("model", "auto")
    quantized = models.load_causal_lm("model", "auto", "4bit")

    assert plain is not quantized
    assert models.load_causal_lm("model", "auto", "4bit") is quantized
    assert len(loads) == 2


def test_teacher_graph_requests_quantization_only_when_configured(monkeypatch):
    calls = []
    monkeypatch.setattr(graph, "load_causal_lm", lambda *a, **kw: calls.append((a, kw)) or ("tokenizer", "model"))
    settings = SimpleNamespace(teacher_model_id="pilot", device_map="auto", teacher_quantization="4bit",
                               max_new_tokens=512, temperature=0.2)

    graph.build_teacher_graph(settings)

    assert calls == [(("pilot", "auto"), {"quantization": "4bit"})]
