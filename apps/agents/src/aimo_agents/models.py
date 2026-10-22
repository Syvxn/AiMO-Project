"""Shared loader so the NPC chat and the quiz teacher reuse one in-memory model on the GPU."""
from __future__ import annotations

import logging
import threading

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

logger = logging.getLogger(__name__)

_cache: dict[tuple[str, str, str], tuple] = {}
_lock = threading.Lock()


def _load_options(device_map: str, quantization: str = "none") -> dict:
    """Prefer the GPU with a half-precision dtype; the CPU path stays full precision."""
    options: dict = {"device_map": device_map}
    if quantization not in {"none", "4bit"}:
        raise ValueError("Quantization must be 'none' or '4bit'.")
    if quantization == "4bit":
        if device_map == "cpu" or not torch.cuda.is_available():
            raise RuntimeError("4-bit teacher loading requires a CUDA GPU. Set TEACHER_QUANTIZATION=none for CPU use.")
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        try:
            options["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=dtype,
            )
        except ImportError as exc:
            raise RuntimeError("Install the quantization extra: pip install -e '.[quantization]'") from exc
        options["torch_dtype"] = dtype
        return options
    if device_map == "cpu":
        return options
    if torch.cuda.is_available():
        bf16 = torch.cuda.is_bf16_supported()
        options["torch_dtype"] = torch.bfloat16 if bf16 else torch.float16
    else:
        logger.warning(
            "CUDA is not available, so models will run on the CPU (slow). Install a CUDA "
            "build of PyTorch, e.g. pip install torch --index-url "
            "https://download.pytorch.org/whl/cu128"
        )
    return options


def load_causal_lm(model_id: str, device_map: str, quantization: str = "none"):
    """Return (tokenizer, model) for an instruction-tuned causal LM, loading it once."""
    key = (model_id, device_map, quantization)
    with _lock:
        if key in _cache:
            return _cache[key]

        try:
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForCausalLM.from_pretrained(model_id, **_load_options(device_map, quantization))
        except ValueError as exc:
            if "upgrade torch to at least v2.6" in str(exc):
                raise RuntimeError(
                    "Incompatible torch version detected while loading HuggingFace model. "
                    "Install torch>=2.6.0 in this environment and retry."
                ) from exc
            if "Unrecognized configuration class" in str(exc):
                raise RuntimeError(
                    f"'{model_id}' is not a causal language model. Set TEACHER_MODEL_ID and "
                    "ORCHESTRATOR_MODEL_ID to an instruction-tuned chat model such as "
                    "Qwen/Qwen2.5-1.5B-Instruct."
                ) from exc
            raise

        logger.info("Loaded %s on %s", model_id, getattr(model, "device", "unknown device"))
        _cache[key] = (tokenizer, model)
        return _cache[key]
