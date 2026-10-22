import asyncio
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models import Base, QuestionBankItem, RoleEnum, StudyMaterial, User
from app.routers import question_bank as routes
from app.services import materials
from app.services.question_bank import game_quiz


@pytest.fixture
def bank(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(materials, "MATERIAL_UPLOAD_DIR", tmp_path)
    with Session(engine) as db:
        teacher = User(email="owner@test", hashed_password="x", role=RoleEnum.teacher)
        other = User(email="other@test", hashed_password="x", role=RoleEnum.teacher)
        db.add_all([teacher, other]); db.flush()
        (tmp_path / "lesson.txt").write_text("Unit 1: Names\nShe is from Australia.\nUnit 2: Jobs\nShe is a nurse.")
        material = StudyMaterial(original_filename="lesson.txt", storage_filename="lesson.txt", content_type="text/plain",
                                 size_bytes=100, uploaded_by_user_id=teacher.id)
        db.add(material); db.commit()
        yield db, teacher, other, material


def payload(material, **changes):
    return routes.CreateQuestion(chapter_id=f"{material.id}:unit-1-names", question="Complete: She ___ from Australia.",
        options=["is", "am", "are", "be"], answer="A", skill="grammar", source_quote="She is from Australia.", **changes)


def test_drafts_unavailable_until_teacher_approval_and_can_be_withdrawn(bank):
    db, teacher, _, material = bank
    item = routes.create_question(payload(material), teacher, db)
    with pytest.raises(HTTPException) as exc:
        game_quiz(db, teacher.id, item["chapter_id"], 1)
    assert exc.value.status_code == 422
    approved = routes.update_question(item["id"], routes.QuestionInput(**{**item, "status": "approved"}), teacher, db)
    assert approved["reviewed_at"]
    for _ in range(10):
        question = game_quiz(db, teacher.id, item["chapter_id"], 1)["quiz"]["questions"][0]
        assert question["options"]["ABCD".index(question["answer"])] == f'{question["answer"]}: is'
        assert "source_quote" not in question
    routes.update_question(item["id"], routes.QuestionInput(**{**item, "status": "draft"}), teacher, db)
    assert db.get(QuestionBankItem, item["id"]).reviewed_at is None
    with pytest.raises(HTTPException):
        game_quiz(db, teacher.id, item["chapter_id"], 1)


def test_bank_requires_full_count_and_keeps_teacher_and_unit_boundaries(bank):
    db, teacher, other, material = bank
    item = routes.create_question(payload(material, status="approved"), teacher, db)
    for teacher_id, chapter_id, count in ((teacher.id, item["chapter_id"], 3), (other.id, item["chapter_id"], 1),
                                          (teacher.id, f"{material.id}:unit-2-jobs", 1)):
        with pytest.raises(HTTPException) as exc:
            game_quiz(db, teacher_id, chapter_id, count)
        assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        routes.list_questions(item["chapter_id"], other, db)
    assert exc.value.status_code == 404
    with pytest.raises(HTTPException):
        routes.update_question(item["id"], routes.QuestionInput(**item), other, db)
    with pytest.raises(HTTPException):
        routes.delete_question(item["id"], other, db)


def test_source_quote_cannot_come_from_other_units_or_teacher_notes(bank):
    db, teacher, _, material = bank
    data = payload(material).model_dump()
    data["source_quote"] = "She is a nurse."
    with pytest.raises(HTTPException) as exc:
        routes.create_question(routes.CreateQuestion(**data), teacher, db)
    assert exc.value.status_code == 422
    data["source_quote"] = "Play audio and tell students the answer."
    with pytest.raises(HTTPException):
        routes.create_question(routes.CreateQuestion(**data), teacher, db)


def test_ai_cannot_approve_its_own_drafts(bank, monkeypatch):
    db, teacher, _, material = bank
    question = payload(material, status="approved").model_dump()
    async def generate(*args, **kwargs):
        return {"quiz": {"questions": [question]}}
    monkeypatch.setattr(routes, "generate_teacher_quiz", generate)
    result = asyncio.run(routes.generate_drafts(routes.DraftRequest(chapter_id=question["chapter_id"]), teacher, db))
    assert result["questions"][0]["status"] == "draft"
    assert result["questions"][0]["reviewed_at"] is None


def test_requested_draft_count_and_chapter_reach_generator(bank, monkeypatch):
    db, teacher, _, material = bank
    chapter_id = f"{material.id}:unit-2-jobs"
    captured = {}

    async def generate(database, teacher_id, topic, question_count, selected_chapter, **options):
        captured.update(teacher_id=teacher_id, topic=topic, count=question_count, chapter=selected_chapter)
        assert options["request_timeout"] == 600.0
        return {"quiz": {"questions": [{
            "question": "Complete: She is a ___ .", "options": ["nurse", "teacher", "farmer", "driver"],
            "answer": "A", "skill": "vocabulary", "source_quote": "She is a nurse.",
        }]}}

    monkeypatch.setattr(routes, "generate_teacher_quiz", generate)
    result = asyncio.run(routes.generate_drafts(routes.DraftRequest(chapter_id=chapter_id, question_count=7), teacher, db))
    assert captured == {"teacher_id": teacher.id, "topic": "Unit 2: Jobs", "count": 7, "chapter": chapter_id}
    assert result["questions"][0]["chapter_id"] == chapter_id
    assert result["questions"][0]["status"] == "draft"


def test_invalid_candidates_do_not_discard_valid_drafts(bank, monkeypatch):
    db, teacher, _, material = bank
    valid = payload(material).model_dump()
    async def generate(*_args, **_kwargs):
        return {"quiz": {"questions": [valid, {**valid, "source_quote": "Not in the selected student unit."},
                                        {**valid, "options": ["is", "is", "are", "be"]}]}}
    monkeypatch.setattr(routes, "generate_teacher_quiz", generate)
    result = asyncio.run(routes.generate_drafts(routes.DraftRequest(chapter_id=valid["chapter_id"]), teacher, db))
    assert len(result["questions"]) == 1
    assert result["skipped_count"] == 2
    assert result["questions"][0]["status"] == "draft"
    assert db.query(QuestionBankItem).count() == 1


def test_all_invalid_candidates_leave_bank_unchanged(bank, monkeypatch):
    db, teacher, _, material = bank
    invalid = {**payload(material).model_dump(), "source_quote": "Not in the student text."}
    async def generate(*_args, **_kwargs):
        return {"quiz": {"questions": [invalid]}}
    monkeypatch.setattr(routes, "generate_teacher_quiz", generate)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(routes.generate_drafts(routes.DraftRequest(chapter_id=invalid["chapter_id"]), teacher, db))
    assert exc.value.status_code == 422
    assert db.query(QuestionBankItem).count() == 0


def test_material_deletion_removes_approved_questions(bank):
    db, teacher, _, material = bank
    item = routes.create_question(payload(material, status="approved"), teacher, db)
    db.delete(material); db.commit()
    assert db.query(QuestionBankItem).count() == 0
    with pytest.raises(HTTPException):
        game_quiz(db, teacher.id, item["chapter_id"], 1)


def test_json_edits_reset_approval_but_keep_unchanged_and_omitted_questions(bank):
    db, teacher, _, material = bank
    first = routes.create_question(payload(material, status="approved"), teacher, db)
    second = routes.create_question(payload(material, status="approved"), teacher, db)
    omitted = routes.create_question(payload(material), teacher, db)
    changed = {**first, "question": "Choose the present tense: She ___ from Australia."}
    request = routes.BankJsonRequest(chapter_id=first["chapter_id"], questions=[changed, second])
    result = routes.save_bank_json(request, teacher, db)
    assert result["updated"] == 1 and result["unchanged"] == 1
    assert len(result["questions"]) == 3
    db.refresh(db.get(QuestionBankItem, first["id"]))
    assert db.get(QuestionBankItem, first["id"]).status == "draft"
    assert db.get(QuestionBankItem, first["id"]).reviewed_at is None
    assert db.get(QuestionBankItem, second["id"]).status == "approved"
    assert db.get(QuestionBankItem, second["id"]).reviewed_at == second["reviewed_at"]
    assert db.get(QuestionBankItem, omitted["id"]).status == "draft"


def test_json_status_metadata_cannot_approve_without_explicit_action(bank):
    db, teacher, _, material = bank
    original = routes.create_question(payload(material), teacher, db)
    forged = {**original, "status": "approved", "reviewed_at": "2026-01-01T00:00:00"}
    new = {**payload(material).model_dump(), "status": "approved"}
    result = routes.save_bank_json(routes.BankJsonRequest(chapter_id=original["chapter_id"], questions=[forged, new]), teacher, db)
    assert result["created"] == 1
    assert all(item["status"] == "draft" and item["reviewed_at"] is None for item in result["questions"])


def test_explicit_json_approve_all_saves_edits_and_approves_submitted_only(bank):
    db, teacher, _, material = bank
    first = routes.create_question(payload(material), teacher, db)
    omitted = routes.create_question(payload(material), teacher, db)
    changed = {**first, "question": "Choose the present tense: She ___ from Australia."}
    new = payload(material).model_dump()
    result = routes.save_bank_json(routes.BankJsonRequest(chapter_id=first["chapter_id"], questions=[changed, new], approve_all=True), teacher, db)
    assert result["approved"] == 2 and result["created"] == 1 and result["updated"] == 1
    assert db.get(QuestionBankItem, omitted["id"]).status == "draft"
    assert len(game_quiz(db, teacher.id, first["chapter_id"], 2)["quiz"]["questions"]) == 2


@pytest.mark.parametrize("failure", ["duplicate_id", "foreign_id", "different_unit", "invalid_source"])
def test_invalid_json_batch_does_not_partially_edit_or_approve(bank, failure):
    db, teacher, _, material = bank
    first = routes.create_question(payload(material), teacher, db)
    changed = {**first, "question": "Choose the present tense: She ___ from Australia."}
    bad = {**payload(material).model_dump()}
    if failure == "duplicate_id": bad["id"] = first["id"]
    elif failure == "foreign_id": bad["id"] = 99999
    elif failure == "different_unit": bad["chapter_id"] = f"{material.id}:unit-2-jobs"
    else: bad["source_quote"] = "She is a nurse."
    request = routes.BankJsonRequest(chapter_id=first["chapter_id"], questions=[changed, bad], approve_all=True)
    with pytest.raises(HTTPException): routes.save_bank_json(request, teacher, db)
    item = db.get(QuestionBankItem, first["id"])
    assert item.question == first["question"] and item.status == "draft" and item.reviewed_at is None
    assert db.query(QuestionBankItem).count() == 1


def test_json_cannot_access_another_teachers_bank(bank):
    db, teacher, other, material = bank
    first = routes.create_question(payload(material), teacher, db)
    with pytest.raises(HTTPException) as exc:
        routes.save_bank_json(routes.BankJsonRequest(chapter_id=first["chapter_id"], questions=[first], approve_all=True), other, db)
    assert exc.value.status_code == 404
    assert db.get(QuestionBankItem, first["id"]).status == "draft"


def test_json_endpoint_accepts_downloaded_shape_and_keeps_ids(bank):
    from app.main import app
    from app.database import get_db
    from app.routers.auth import get_current_user
    db, teacher, _, material = bank
    first = routes.create_question(payload(material), teacher, db)
    app.dependency_overrides[get_current_user] = lambda: teacher
    app.dependency_overrides[get_db] = lambda: db
    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.put("/teacher/question-bank/json", json={"chapter_id": first["chapter_id"], "questions": [first], "approve_all": True})
    try:
        response = asyncio.run(check())
        assert response.status_code == 200, response.text
        assert response.json()["questions"][0]["id"] == first["id"]
        assert response.json()["questions"][0]["status"] == "approved"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.parametrize("options", [["is", "is", "are", "be"], ["is", "am", "are", ""],
    ["is", "am", "are", "all of the above"], ["is", "am", "are"]])
def test_invalid_options_cannot_be_approved(options):
    with pytest.raises(ValidationError):
        routes.QuestionInput(question="Complete: She ___ a student.", options=options, answer="A", skill="grammar",
                             source_quote="She is a student.", status="approved")


def test_student_cannot_access_teacher_bank_editor():
    from app.main import app
    from app.routers.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(role=RoleEnum.student)
    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.get("/teacher/question-bank/chapters")
    try:
        assert asyncio.run(check()).status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
