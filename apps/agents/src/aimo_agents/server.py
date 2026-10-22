"""FastAPI server exposing agents as HTTP endpoints for the API service."""
from __future__ import annotations

import asyncio
import json
import logging
import queue
import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from transformers import StoppingCriteria, StoppingCriteriaList, TextIteratorStreamer

from .config.settings import load_settings
from .models import load_causal_lm

# Longest wait for the next token before the stream is abandoned.
TOKEN_TIMEOUT_SECONDS = 60.0
MAX_HISTORY_TURNS = 6


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Preload the model in a worker thread so the event loop stays responsive.
    await asyncio.get_running_loop().run_in_executor(None, get_conv_model)
    yield


app = FastAPI(title="AiMO Agents Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_conv_model():
    settings = load_settings()
    return load_causal_lm(settings.orchestrator_model_id, settings.device_map)


class ConversationRequest(BaseModel):
    npc_id: str
    player_id: str
    persona: str
    history: list[dict[str, str]] = []
    user_text: str
    max_new_tokens: int = Field(default=160, ge=1, le=256)


class QuizRequest(BaseModel):
    topic: str = Field(max_length=200)
    question_count: int = Field(default=3, ge=1, le=20)
    learning_material: str = ""
    # Without learning material, a quiz is only written when this is explicitly allowed.
    use_model_knowledge: bool = False
    teaching_guidance: str = ""
    language_practice: bool = False
    require_full_count: bool = False


@app.get("/health")
def health():
    return {"status": "ok"}


class _CancelCriteria(StoppingCriteria):
    """Stops generation once the client has gone away."""

    def __init__(self, cancelled: threading.Event) -> None:
        self._cancelled = cancelled

    def __call__(self, input_ids, scores, **kwargs):
        return torch.full(
            (input_ids.shape[0],), self._cancelled.is_set(), dtype=torch.bool, device=input_ids.device
        )


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


async def _token_generator(
    tokenizer, model, prompt: str, max_new_tokens: int
) -> AsyncGenerator[str, None]:
    streamer = TextIteratorStreamer(
        tokenizer, skip_prompt=True, skip_special_tokens=True, timeout=TOKEN_TIMEOUT_SECONDS
    )
    cancelled = threading.Event()
    failure: list[BaseException] = []

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    generation_kwargs = dict(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        repetition_penalty=1.1,
        streamer=streamer,
        stopping_criteria=StoppingCriteriaList([_CancelCriteria(cancelled)]),
    )

    def generate() -> None:
        try:
            model.generate(**generation_kwargs)
        except BaseException as exc:  # noqa: BLE001 - must always unblock the reader
            failure.append(exc)
            streamer.end()

    thread = threading.Thread(target=generate, daemon=True)
    thread.start()

    loop = asyncio.get_running_loop()
    iterator = iter(streamer)
    finished = object()
    try:
        while True:
            # Queue reads block, so they run off the event loop.
            token = await loop.run_in_executor(None, next, iterator, finished)
            if token is finished:
                break
            yield _sse({"type": "token", "text": token})
    except queue.Empty:
        failure.append(TimeoutError("Timed out waiting for the model."))
    finally:
        cancelled.set()

    if failure:
        print(f"Conversation generation failed: {failure[0]!r}")
        yield _sse({"type": "error", "message": "The assistant could not finish its reply."})
        return
    yield _sse({"type": "done"})


def _build_prompt(persona: str, history: list[dict], user_text: str, tokenizer) -> str:
    recent = [
        {
            "role": "assistant" if turn.get("role") == "assistant" else "user",
            "text": turn.get("text", ""),
        }
        for turn in history[-MAX_HISTORY_TURNS:]
    ]
    messages = [{"role": "system", "content": persona}]
    messages.extend({"role": turn["role"], "content": turn["text"]} for turn in recent)
    messages.append({"role": "user", "content": user_text})

    if hasattr(tokenizer, "apply_chat_template"):
        try:
            return tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        except Exception:
            pass

    # Fallback: plain text prompt
    prompt = f"System: {persona}\n"
    for turn in recent:
        prompt += f"{turn['role'].capitalize()}: {turn['text']}\n"
    prompt += f"User: {user_text}\nAssistant:"
    return prompt


@app.post("/converse/stream")
async def converse_stream(req: ConversationRequest):
    tokenizer, model = get_conv_model()
    prompt = _build_prompt(req.persona, req.history, req.user_text, tokenizer)

    return StreamingResponse(
        _token_generator(tokenizer, model, prompt, req.max_new_tokens),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/quiz/generate")
async def quiz_generate(req: QuizRequest):
    """Run the teacher quiz pipeline and return a structured quiz payload."""
    from .runner import run_once

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        lambda: run_once(
            "",
            learning_material=req.learning_material,
            topic=req.topic,
            question_count=req.question_count,
            use_model_knowledge=req.use_model_knowledge,
            **({"teaching_guidance": req.teaching_guidance} if req.teaching_guidance else {}),
            **({"language_practice": True} if req.language_practice else {}),
            **({"require_full_count": True} if req.require_full_count else {}),
        ),
    )

    quiz = result.get("quiz")
    logging.getLogger("uvicorn.error").info(
        "Quiz generation: model_calls=%s questions=%s failed=%s",
        result.get("llm_calls", 0),
        len(quiz.get("questions", [])) if isinstance(quiz, dict) else 0,
        bool(result.get("error")),
    )

    if result.get("error"):
        return {"error": result["error"]}

    quiz_data = result.get("quiz")
    if not quiz_data:
        return {"error": "No quiz produced."}

    # Parse quiz JSON if returned as string
    if isinstance(quiz_data, str):
        try:
            quiz_data = json.loads(quiz_data)
        except json.JSONDecodeError:
            return {"error": "Quiz output could not be parsed."}

    return {"quiz": quiz_data}
