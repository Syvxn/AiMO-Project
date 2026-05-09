from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Any

import httpx


DEFAULT_NPC_ID = "quiz_llehc"
AGENTS_SERVICE_URL = os.getenv("AGENTS_SERVICE_URL", "http://agents:8001")


@dataclass
class NpcProfile:
    npc_id: str
    npc_type: str
    display_name: str
    capabilities: set[str]
    persona: str


@dataclass
class ChatSession:
    session_id: str
    npc_id: str
    mode: str = "conversation"
    memory: list[dict[str, str]] = field(default_factory=list)


NPC_PROFILES: dict[str, NpcProfile] = {
    "quiz_llehc": NpcProfile(
        npc_id="quiz_llehc",
        npc_type="quiz_npc",
        display_name="Llehc",
        capabilities={"quiz_generation"},
        persona=(
            "You are Llehc, a friendly and encouraging quiz guide in an educational game. "
            "Keep your responses short, warm, and helpful. You can create quizzes on any "
            "topic a student is studying. When asked to make a quiz, confirm the topic and "
            "let them know you are generating it. Otherwise, chat naturally and helpfully."
        ),
    )
}


def resolve_profile(npc_id: str) -> NpcProfile:
    return NPC_PROFILES.get(npc_id, NPC_PROFILES[DEFAULT_NPC_ID])


def route_turn(profile: NpcProfile, user_text: str) -> str:
    lowered = user_text.lower()
    quiz_markers = ("create quiz", "make quiz", "generate quiz", "practice quiz")
    broad_markers = ("quiz", "questions", "test", "practice")
    if "quiz_generation" in profile.capabilities:
        if any(marker in lowered for marker in quiz_markers):
            return "task_quiz"
        if any(marker in lowered for marker in broad_markers) and any(
            marker in lowered for marker in ("make", "create", "generate", "give")
        ):
            return "task_quiz"
    return "conversation"


def extract_quiz_topic(user_text: str) -> str:
    lowered = user_text.lower()
    for splitter in (" about ", " on ", " for "):
        if splitter in lowered:
            idx = lowered.index(splitter) + len(splitter)
            candidate = user_text[idx:].strip(" .!?")
            if candidate:
                return candidate
    return "general knowledge"


async def stream_conversation_events(
    profile: NpcProfile, user_text: str, memory: list[dict[str, str]]
):
    """Call agents service SSE endpoint and re-yield token events."""
    payload = {
        "npc_id": profile.npc_id,
        "player_id": "player",
        "persona": profile.persona,
        "history": memory,
        "user_text": user_text,
        "max_new_tokens": 64,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", f"{AGENTS_SERVICE_URL}/converse/stream", json=payload
            ) as response:
                if response.status_code != 200:
                    yield {"type": "typing_token", "text": f"[Agent error: {response.status_code}]"}
                    yield {"type": "assistant_message_done"}
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line[len("data: "):]
                    try:
                        event = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    if event.get("type") == "token":
                        text = event.get("text", "")
                        if text:
                            yield {"type": "typing_token", "text": text}
                    elif event.get("type") == "done":
                        break

    except httpx.ConnectError:
        # Agents service not available — fall back to template reply
        async for event in _fallback_conversation(profile, user_text):
            yield event
        return

    yield {"type": "assistant_message_done"}


async def _fallback_conversation(profile: NpcProfile, user_text: str):
    lowered = user_text.lower().strip("! .?")
    greetings = ("hi", "hello", "hey", "sup", "yo", "howdy")
    if lowered in greetings:
        reply = (
            f"Hey! I'm {profile.display_name}, your quiz guide. "
            "Ask me to create a quiz on any topic and I'll get one ready!"
        )
    else:
        reply = (
            f"I'm {profile.display_name}! I can create quizzes on any topic. "
            "Just say 'create a quiz on fractions' and I'll get started."
        )
    for word in reply.split(" "):
        yield {"type": "typing_token", "text": word + " "}
        await asyncio.sleep(0.07)
    yield {"type": "assistant_message_done"}


async def stream_task_events(profile: NpcProfile, user_text: str):
    topic = extract_quiz_topic(user_text)
    yield {
        "type": "task_started",
        "task": "quiz_generation",
        "message": f"{profile.display_name} is preparing a quiz on {topic}...",
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{AGENTS_SERVICE_URL}/quiz/generate",
                json={"topic": topic, "question_count": 3},
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("error"):
                    yield {"type": "task_progress", "message": f"Quiz error: {data['error']}"}
                else:
                    yield {"type": "quiz_ready", "quiz": data["quiz"]}
                    return
            else:
                yield {"type": "task_progress", "message": "Quiz generation failed. Try again."}
    except httpx.ConnectError:
        # Fall back to placeholder quiz
        yield {"type": "task_progress", "message": "Generating question set..."}
        await asyncio.sleep(0.2)
        yield {"type": "quiz_ready", "quiz": _placeholder_quiz(topic)}

    yield {
        "type": "task_progress",
        "message": "Quiz is ready! Submit your answers when done.",
    }


def _placeholder_quiz(topic: str) -> dict[str, Any]:
    return {
        "quiz_title": f"Practice Quiz: {topic.title()}",
        "questions": [
            {
                "question": f"[{topic}] Question {i + 1}: choose the best answer.",
                "options": ["A", "B", "C", "D"],
                "answer": "A",
            }
            for i in range(3)
        ],
    }


def trim_memory(memory: list[dict[str, str]], limit: int = 20) -> list[dict[str, str]]:
    if len(memory) <= limit:
        return memory
    return memory[-limit:]
