"""FastAPI server exposing agents as HTTP endpoints for the API service."""
from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
import threading

from .config.settings import load_settings

app = FastAPI(title="AiMO Agents Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_settings = None
_conv_tokenizer = None
_conv_model = None


def get_conv_model():
    global _settings, _conv_tokenizer, _conv_model
    if _conv_model is None:
        _settings = load_settings()
        print(f"Loading conversational model: {_settings.orchestrator_model_id}")
        _conv_tokenizer = AutoTokenizer.from_pretrained(_settings.orchestrator_model_id)
        _conv_model = AutoModelForCausalLM.from_pretrained(
            _settings.orchestrator_model_id,
            device_map=_settings.device_map,
        )
        print("Conversational model loaded.")
    return _conv_tokenizer, _conv_model


class ConversationRequest(BaseModel):
    npc_id: str
    player_id: str
    persona: str
    history: list[dict[str, str]] = []
    user_text: str
    max_new_tokens: int = 64


class QuizRequest(BaseModel):
    topic: str
    question_count: int = 3


@app.on_event("startup")
async def startup():
    # Load model in background thread so the server starts fast.
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, get_conv_model)


@app.get("/health")
def health():
    return {"status": "ok"}


async def _token_generator(
    tokenizer, model, prompt: str, max_new_tokens: int
) -> AsyncGenerator[str, None]:
    streamer = TextIteratorStreamer(
        tokenizer, skip_prompt=True, skip_special_tokens=True
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    generation_kwargs = dict(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        streamer=streamer,
    )

    thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    for token in streamer:
        yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
        await asyncio.sleep(0)  # yield control to event loop between tokens

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
    thread.join()


def _build_prompt(persona: str, history: list[dict], user_text: str, tokenizer) -> str:
    messages = [{"role": "system", "content": persona}]
    for turn in history[-6:]:  # keep fewer turns for lower latency
        role = turn.get("role", "user")
        text = turn.get("text", "")
        messages.append({"role": role, "content": text})
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
    for turn in history[-6:]:
        role = turn.get("role", "user").capitalize()
        prompt += f"{role}: {turn.get('text', '')}\n"
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

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, lambda: run_once("", topic=req.topic, question_count=req.question_count)
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
