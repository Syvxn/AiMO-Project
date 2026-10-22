import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
import httpx
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, RoleEnum, StudyMaterial, User
from app.routers import quiz
from app.routers import teacher
from app.services import materials


@pytest.mark.parametrize("failure,status", [(httpx.ReadTimeout("slow generation"), 504),
                                          (httpx.ConnectError("service stopped"), 503)])
def test_generation_timeout_is_distinct_from_service_unavailability(monkeypatch, failure, status):
    class Client:
        def __init__(self, **_kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *_args):
            pass
        async def post(self, *_args, **_kwargs):
            raise failure
    monkeypatch.setattr(materials.httpx, "AsyncClient", Client)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(materials.request_agent_quiz({"topic": "test"}))
    assert exc.value.status_code == status
    assert ("took too long" in exc.value.detail) == (status == 504)


def test_drafting_timeout_reaches_http_client_without_changing_model_payload(monkeypatch):
    captured = {}
    class Client:
        def __init__(self, **options):
            captured["timeout"] = options["timeout"]
        async def __aenter__(self):
            return self
        async def __aexit__(self, *_args):
            pass
        async def post(self, _url, json):
            captured["payload"] = json
            return SimpleNamespace(status_code=200, json=lambda: {"quiz": {"questions": []}})
    monkeypatch.setattr(materials.httpx, "AsyncClient", Client)
    asyncio.run(materials.generate_teacher_quiz(object(), None, "Greetings", 8, request_timeout=600))
    assert captured["timeout"].read == 600
    assert captured["timeout"].connect == 5
    assert captured["payload"] == {"topic": "Greetings", "question_count": 8, "use_model_knowledge": True}


class FakeQuery:
    def __init__(self, items, teacher_user_id):
        self.items = items
        self.teacher_user_id = teacher_user_id

    def filter(self, criterion):
        assert criterion.right.value == self.teacher_user_id
        return self

    def order_by(self, _ordering):
        return self

    def all(self):
        return self.items


class FakeDatabase:
    def __init__(self, items, teacher_user_id):
        self.items = items
        self.teacher_user_id = teacher_user_id

    def query(self, model):
        assert model is StudyMaterial
        return FakeQuery(self.items, self.teacher_user_id)


def test_generate_teacher_quiz_uses_only_selected_teacher_material(monkeypatch, tmp_path):
    material_file = tmp_path / "science.txt"
    material_file.write_text("Plants use sunlight to make food.", encoding="utf-8")
    teacher_material = SimpleNamespace(
        storage_filename="science.txt",
        original_filename="science.txt",
    )
    request_data = {}

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"quiz": {"quiz_title": "Plants", "questions": []}}

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            pass

        async def post(self, _url, json):
            request_data.update(json)
            return FakeResponse()

    monkeypatch.setattr(materials, "MATERIAL_UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(materials.httpx, "AsyncClient", FakeClient)
    db = FakeDatabase([teacher_material], teacher_user_id=42)

    result = asyncio.run(
        materials.generate_teacher_quiz(
            db,
            teacher_user_id=42,
            topic="plants",
            question_count=3,
        )
    )

    assert result["quiz"]["quiz_title"] == "Plants"
    assert request_data == {
        "topic": "plants",
        "question_count": 3,
        "learning_material": "Source: science.txt\nPlants use sunlight to make food.",
    }


def test_extract_material_chapters_skips_contents_and_splits_units(monkeypatch, tmp_path):
    material_file = tmp_path / "textbook.txt"
    material_file.write_text(
        "Contents\nUnit 1: Contents-only title\n\n"
        "Unit 1: Gardens\nPlants need sunlight and water.\n\n"
        "Unit 2: Rivers\nRivers carry fresh water.",
        encoding="utf-8",
    )
    material = SimpleNamespace(
        id=5,
        storage_filename="textbook.txt",
        original_filename="textbook.pdf",
    )
    monkeypatch.setattr(materials, "MATERIAL_UPLOAD_DIR", tmp_path)

    chapters = materials.extract_material_chapters([material])

    assert [chapter["title"] for chapter in chapters] == ["Unit 1: Gardens", "Unit 2: Rivers"]
    assert "Plants need sunlight" in chapters[0]["content"]
    assert "Rivers carry fresh water" in chapters[1]["content"]


def test_generate_teacher_quiz_sends_only_selected_chapter(monkeypatch, tmp_path):
    material_file = tmp_path / "textbook.txt"
    material_file.write_text(
        "Unit 1: Gardens\nPlants need sunlight.\n"
        "Unit 2: Rivers\nRivers carry fresh water.",
        encoding="utf-8",
    )
    teacher_material = SimpleNamespace(
        id=5,
        storage_filename="textbook.txt",
        original_filename="textbook.pdf",
    )
    request_data = {}

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"quiz": {"quiz_title": "Unit 2: Rivers", "questions": []}}

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            pass

        async def post(self, _url, json):
            request_data.update(json)
            return FakeResponse()

    monkeypatch.setattr(materials, "MATERIAL_UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(materials.httpx, "AsyncClient", FakeClient)

    result = asyncio.run(
        materials.generate_teacher_quiz(
            FakeDatabase([teacher_material], teacher_user_id=42),
            teacher_user_id=42,
            topic="class material",
            question_count=3,
            chapter_id="5:unit-2-rivers",
        )
    )

    assert result["quiz"]["quiz_title"] == "Unit 2: Rivers"
    assert request_data["topic"] == "Unit 2: Rivers"
    assert request_data["learning_material"] == (
        "Source: textbook.pdf\nChapter: Unit 2: Rivers\nRivers carry fresh water."
    )


def test_generate_student_quiz_without_a_class_uses_model_knowledge(monkeypatch):
    student = SimpleNamespace(role=RoleEnum.student, teacher_user_id=None)
    captured = {}

    async def fake_generate_teacher_quiz(db, teacher_user_id, topic, question_count, chapter_id, **options):
        captured.update(teacher_user_id=teacher_user_id, topic=topic, chapter_id=chapter_id, **options)
        return {"quiz": {"quiz_title": "Colours", "questions": []}}

    monkeypatch.setattr(quiz, "generate_teacher_quiz", fake_generate_teacher_quiz)
    payload = quiz.StudentQuizRequest(
        topic="General knowledge \u2014 Colours", chapter_id="topic:Colours", question_count=3
    )

    asyncio.run(quiz.generate_student_quiz(payload, student, object()))

    assert captured == {"teacher_user_id": None, "topic": "Colours", "chapter_id": "topic:Colours",
                        "language_practice": True, "require_full_count": True}


def test_generate_student_quiz_rejects_overlong_topics():
    student = SimpleNamespace(role=RoleEnum.student, teacher_user_id=None)
    payload = quiz.StudentQuizRequest(topic="x" * 500)

    with pytest.raises(HTTPException) as error:
        asyncio.run(quiz.generate_student_quiz(payload, student, object()))

    assert error.value.status_code == 400


def test_students_without_a_class_get_suggested_topics_instead_of_chapters():
    student = SimpleNamespace(role=RoleEnum.student, teacher_user_id=None)

    chapters = quiz.get_student_quiz_chapters(student, object())["chapters"]

    assert chapters
    assert all(chapter["chapter_id"].startswith("topic:") for chapter in chapters)
    assert materials.topic_from_suggestion(chapters[0]["chapter_id"]) == chapters[0]["title"]
    assert materials.topic_from_suggestion("topic:Anything else") is None


def test_generate_quiz_without_a_teacher_sends_no_material(monkeypatch):
    request_data = {}

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"quiz": {"quiz_title": "Colours", "questions": []}}

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            pass

        async def post(self, _url, json):
            request_data.update(json)
            return FakeResponse()

    monkeypatch.setattr(materials.httpx, "AsyncClient", FakeClient)

    asyncio.run(
        materials.generate_teacher_quiz(object(), teacher_user_id=None, topic="Colours", question_count=3)
    )

    assert request_data == {"topic": "Colours", "question_count": 3, "use_model_knowledge": True}


def test_generate_student_quiz_uses_authenticated_teacher(monkeypatch):
    student = SimpleNamespace(role=RoleEnum.student, teacher_user_id=42)
    captured = {}

    def fake_game_quiz(db, teacher_id, chapter_id, count):
        captured.update(
            db=db,
            teacher_id=teacher_id,
            count=count,
            chapter_id=chapter_id,
        )
        return {"quiz": {"quiz_title": "Class quiz", "questions": []}}

    monkeypatch.setattr(quiz, "game_quiz", fake_game_quiz)
    db = object()
    payload = quiz.StudentQuizRequest(topic="plants", question_count=4, chapter_id="42:unit-1-plants")

    result = asyncio.run(quiz.generate_student_quiz(payload, student, db))

    assert result["quiz"]["quiz_title"] == "Class quiz"
    assert captured == {
        "db": db,
        "teacher_id": 42,
        "count": 4,
        "chapter_id": "42:unit-1-plants",
    }


def test_get_student_quiz_chapters_uses_enrolled_teacher(monkeypatch):
    student = SimpleNamespace(role=RoleEnum.student, teacher_user_id=42)
    db = object()
    captured = {}

    def fake_list_teacher_chapters(database, teacher_user_id):
        captured.update(database=database, teacher_user_id=teacher_user_id)
        return [{"chapter_id": "42:unit-1-plants", "title": "Unit 1: Plants", "material_title": "book.pdf"}]

    monkeypatch.setattr(quiz, "list_teacher_chapters", fake_list_teacher_chapters)

    result = quiz.get_student_quiz_chapters(student, db)

    assert result["chapters"][0]["title"] == "Unit 1: Plants"
    assert captured == {"database": db, "teacher_user_id": 42}


def test_teacher_class_code_enrolls_student():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        teacher_user = User(
            email="teacher@example.test",
            hashed_password="unused",
            role=RoleEnum.teacher,
        )
        student = User(
            email="student@example.test",
            hashed_password="unused",
            role=RoleEnum.student,
        )
        db.add_all([teacher_user, student])
        db.commit()

        class_info = teacher.get_teacher_class_code(teacher_user, db)
        assert len(class_info.class_code) == 8

        result = quiz.join_class(
            quiz.JoinClassRequest(class_code=class_info.class_code.lower()),
            student,
            db,
        )

        db.refresh(student)
        assert result["status"] == "joined"
        assert student.teacher_user_id == teacher_user.id
        assert teacher.get_teacher_class_code(teacher_user, db).joined_students == 1
