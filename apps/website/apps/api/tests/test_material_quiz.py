import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, RoleEnum, StudyMaterial, User
from app.routers import quiz
from app.routers import teacher
from app.services import materials


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


def test_generate_student_quiz_rejects_unenrolled_students():
    student = SimpleNamespace(role=RoleEnum.student, teacher_user_id=None)

    with pytest.raises(HTTPException) as error:
        asyncio.run(quiz.generate_student_quiz(quiz.StudentQuizRequest(), student, object()))

    assert error.value.status_code == 409


def test_generate_student_quiz_uses_authenticated_teacher(monkeypatch):
    student = SimpleNamespace(role=RoleEnum.student, teacher_user_id=42)
    captured = {}

    async def fake_generate_teacher_quiz(db, teacher_user_id, topic, question_count):
        captured.update(
            db=db,
            teacher_user_id=teacher_user_id,
            topic=topic,
            question_count=question_count,
        )
        return {"quiz": {"quiz_title": "Class quiz", "questions": []}}

    monkeypatch.setattr(quiz, "generate_teacher_quiz", fake_generate_teacher_quiz)
    db = object()
    payload = quiz.StudentQuizRequest(topic="plants", question_count=4)

    result = asyncio.run(quiz.generate_student_quiz(payload, student, db))

    assert result["quiz"]["quiz_title"] == "Class quiz"
    assert captured == {
        "db": db,
        "teacher_user_id": 42,
        "topic": "plants",
        "question_count": 4,
    }


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
