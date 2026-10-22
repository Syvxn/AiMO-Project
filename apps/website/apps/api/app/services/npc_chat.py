from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field

import httpx
from fastapi import HTTPException

from app.core.security import decode_token
from app.database import SessionLocal
from app.models import User
from app.services.materials import generate_teacher_quiz


DEFAULT_NPC_ID = "quiz_llehc"
AGENTS_SERVICE_URL = os.getenv("AGENTS_SERVICE_URL", "http://agents:8001")
MAX_QUIZ_TOPIC_CHARACTERS = 120


@dataclass
class QuizAccount:
    """Who is asking for a quiz, reduced to which source material applies."""

    # Teacher whose uploads are used; None means the model's own knowledge.
    teacher_user_id: int | None


def resolve_quiz_account(token: str) -> QuizAccount | None:
    """Map a login token to the quiz source for that account, or None if it is not valid."""
    token_data = decode_token(token) if token else None
    if token_data is None:
        return None
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == token_data.email).first()
        if user is None:
            return None
        role = str(getattr(user.role, "value", user.role))
        if role == "student":
            return QuizAccount(teacher_user_id=user.teacher_user_id)
        if role == "teacher":
            return QuizAccount(teacher_user_id=user.id)
        return QuizAccount(teacher_user_id=None)
    finally:
        db.close()


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
        npc_id="quiz_Rook",
        npc_type="game_guide",
        display_name="Rook",
        capabilities={"quiz_generation"},
        persona=(
            "You are Rook, a friendly AI game guide for AiMO, an educational multiplayer "
            "game. Help players explore and understand the game. Reply in at most three "
            "short sentences. Verified controls: WASD "
            "moves, right-click moves to a destination, E interacts with nearby NPCs, I "
            "opens character customization, and Escape opens the room menu or closes the "
            "current menu. Players can join rooms, talk with NPCs, and play quiz activities. "
            "This is a prototype, so some rooms and features may be unfinished. Give clear, "
            "concise, practical help. Do not claim you can see the player's screen or operate "
            "the game for them. Do not invent controls or unsupported features; ask what the "
            "player sees when details are unclear. Answer game questions directly, and offer "
            "a quiz only when the player asks for one."
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


def extract_quiz_topic(user_text: str) -> str | None:
    lowered = user_text.lower()
    for splitter in (" about ", " on ", " for "):
        if splitter in lowered:
            idx = lowered.index(splitter) + len(splitter)
            candidate = user_text[idx:].strip(" .!?")
            if candidate:
                return candidate
    return None


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
        "max_new_tokens": 160,
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
                    elif event.get("type") == "error":
                        yield {
                            "type": "typing_token",
                            "text": event.get("message") or "[Agent error]",
                        }
                        break
                    elif event.get("type") == "done":
                        break

    except httpx.ConnectError:
        # Agents service not available — fall back to template reply
        async for event in _fallback_conversation(profile, user_text):
            yield event
        return
    except httpx.HTTPError:
        yield {"type": "typing_token", "text": "[Agent timed out. Please try again.]"}
        yield {"type": "assistant_message_done"}
        return

    yield {"type": "assistant_message_done"}


async def _fallback_conversation(profile: NpcProfile, user_text: str):
    lowered = user_text.lower().strip("! .?")
    greetings = ("hi", "hello", "hey", "sup", "yo", "howdy")
    if lowered in greetings:
        reply = (
            f"Hi, I'm {profile.display_name}, your AI game guide. "
            "Use WASD or right-click to move, E to interact, I to customize your character, "
            "and Escape for the room menu. What are you trying to do?"
        )
    else:
        reply = (
            f"I'm {profile.display_name}, your AI game guide. Tell me what you're trying "
            "to do and where you are, and I'll help with movement, rooms, customization, "
            "or talking to NPCs."
        )
    for word in reply.split(" "):
        yield {"type": "typing_token", "text": word + " "}
        await asyncio.sleep(0.07)
    yield {"type": "assistant_message_done"}


async def stream_task_events(profile: NpcProfile, user_text: str, account: QuizAccount | None):
    topic = extract_quiz_topic(user_text)
    if topic is None:
        yield {
            "type": "task_progress",
            "message": "What should the quiz be about? For example: make a quiz about colours.",
        }
        return
    if account is None:
        yield {
            "type": "task_progress",
            "message": "Sign in on the website and reopen the game so I can make quizzes for you.",
        }
        return
    topic = topic[:MAX_QUIZ_TOPIC_CHARACTERS]
    yield {
        "type": "task_started",
        "task": "quiz_generation",
        "message": f"{profile.display_name} is preparing a quiz on {topic}...",
    }

    db = SessionLocal()
    try:
        result = await generate_teacher_quiz(
            db, teacher_user_id=account.teacher_user_id, topic=topic, question_count=3
        )
    except HTTPException as exc:
        yield {"type": "task_progress", "message": f"Quiz error: {exc.detail}"}
        return
    finally:
        db.close()

    yield {"type": "quiz_ready", "quiz": result["quiz"]}

def trim_memory(memory: list[dict[str, str]], limit: int = 20) -> list[dict[str, str]]:
    if len(memory) <= limit:
        return memory
    return memory[-limit:]
