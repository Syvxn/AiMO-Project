import asyncio
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.models import Base, RoleEnum, User
from app.services import npc_chat


class FakeResponse:
    def __init__(self, status_code=200, lines=()):
        self.status_code = status_code
        self._lines = lines

    async def aiter_lines(self):
        for line in self._lines:
            yield line


class FakeStream:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, *_exc):
        return False


def fake_client(response=None, error=None):
    class FakeClient:
        def __init__(self, *_args, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_exc):
            return False

        def stream(self, *_args, **_kwargs):
            if error:
                raise error
            return FakeStream(response)

    return FakeClient


def collect(async_generator):
    async def run():
        return [event async for event in async_generator]

    return asyncio.run(run())


def profile():
    return npc_chat.resolve_profile(npc_chat.DEFAULT_NPC_ID)


@pytest.fixture
def fake_db(monkeypatch):
    monkeypatch.setattr(npc_chat, "SessionLocal", lambda: SimpleNamespace(close=lambda: None))


def stub_quiz_generation(monkeypatch, result=None, error=None):
    calls = []

    async def fake_generate(db, teacher_user_id, topic, question_count):
        calls.append({"teacher_user_id": teacher_user_id, "topic": topic, "question_count": question_count})
        if error:
            raise error
        return result

    monkeypatch.setattr(npc_chat, "generate_teacher_quiz", fake_generate)
    return calls


def test_quiz_topic_is_none_when_the_player_names_no_topic():
    assert npc_chat.extract_quiz_topic("make a quiz") is None
    assert npc_chat.extract_quiz_topic("Make a quiz about colours.") == "colours"


def test_missing_topic_asks_instead_of_generating(monkeypatch, fake_db):
    calls = stub_quiz_generation(monkeypatch)

    events = collect(npc_chat.stream_task_events(profile(), "make a quiz", npc_chat.QuizAccount(None)))

    assert [event["type"] for event in events] == ["task_progress"]
    assert calls == []


def test_quiz_requires_a_signed_in_account(monkeypatch, fake_db):
    calls = stub_quiz_generation(monkeypatch)

    events = collect(npc_chat.stream_task_events(profile(), "make a quiz about colours", None))

    assert [event["type"] for event in events] == ["task_progress"]
    assert "Sign in" in events[0]["message"]
    assert calls == []


@pytest.mark.parametrize("teacher_user_id", [42, None])
def test_quiz_uses_the_accounts_teacher_or_model_knowledge(monkeypatch, fake_db, teacher_user_id):
    quiz = {"quiz_title": "Colours", "questions": []}
    calls = stub_quiz_generation(monkeypatch, result={"quiz": quiz})

    events = collect(
        npc_chat.stream_task_events(
            profile(), "make a quiz about colours", npc_chat.QuizAccount(teacher_user_id)
        )
    )

    assert calls == [{"teacher_user_id": teacher_user_id, "topic": "colours", "question_count": 3}]
    assert events[-1] == {"type": "quiz_ready", "quiz": quiz}


def test_failed_quiz_is_reported_and_not_called_ready(monkeypatch, fake_db):
    stub_quiz_generation(monkeypatch, error=HTTPException(status_code=422, detail="No material"))

    events = collect(
        npc_chat.stream_task_events(
            profile(), "make a quiz about colours", npc_chat.QuizAccount(42)
        )
    )

    assert events[-1] == {"type": "task_progress", "message": "Quiz error: No material"}
    assert not any(event["type"] == "quiz_ready" for event in events)


def test_overlong_topics_are_truncated(monkeypatch, fake_db):
    calls = stub_quiz_generation(monkeypatch, result={"quiz": {}})

    collect(
        npc_chat.stream_task_events(
            profile(), "make a quiz about " + "x" * 500, npc_chat.QuizAccount(None)
        )
    )

    assert len(calls[0]["topic"]) == npc_chat.MAX_QUIZ_TOPIC_CHARACTERS


def test_quiz_account_follows_the_account_class(monkeypatch):
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(npc_chat, "SessionLocal", session_factory)

    with session_factory() as db:
        teacher = User(email="t@example.test", hashed_password="x", role=RoleEnum.teacher)
        db.add(teacher)
        db.commit()
        db.add_all(
            [
                User(email="in@example.test", hashed_password="x", role=RoleEnum.student, teacher_user_id=teacher.id),
                User(email="out@example.test", hashed_password="x", role=RoleEnum.student),
                User(email="boss@example.test", hashed_password="x", role=RoleEnum.admin),
            ]
        )
        db.commit()
        teacher_id = teacher.id

    def account(email):
        return npc_chat.resolve_quiz_account(create_access_token(email, "student"))

    assert account("in@example.test").teacher_user_id == teacher_id
    assert account("out@example.test").teacher_user_id is None
    assert account("t@example.test").teacher_user_id == teacher_id
    assert account("boss@example.test").teacher_user_id is None
    assert account("nobody@example.test") is None
    assert npc_chat.resolve_quiz_account("not-a-token") is None
    assert npc_chat.resolve_quiz_account("") is None


def test_agent_timeout_ends_the_conversation_cleanly(monkeypatch):
    monkeypatch.setattr(npc_chat.httpx, "AsyncClient", fake_client(error=httpx.ReadTimeout("slow")))

    events = collect(npc_chat.stream_conversation_events(profile(), "hello", []))

    assert events[-1]["type"] == "assistant_message_done"
    assert "timed out" in events[0]["text"]


def test_agent_stream_error_is_shown_to_the_player(monkeypatch):
    lines = ['data: {"type": "token", "text": "Hi"}', 'data: {"type": "error", "message": "Failed"}']
    monkeypatch.setattr(npc_chat.httpx, "AsyncClient", fake_client(FakeResponse(lines=lines)))

    events = collect(npc_chat.stream_conversation_events(profile(), "hello", []))

    assert [event.get("text") for event in events if event["type"] == "typing_token"] == ["Hi", "Failed"]
    assert events[-1]["type"] == "assistant_message_done"
