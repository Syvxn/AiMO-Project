from pathlib import Path
from types import SimpleNamespace
import asyncio
import os

import pytest

from app.services import materials
from app.services.textbooks import parse_think_english


def test_interleaved_edition_uses_running_headers_and_excludes_back_matter():
    pages = [
        "Think English Teacher's Book",
        "Unit 1: Wrong contents title\nUnit 2: Wrong contents title\nContents",
        "COURSE MAP\nUnit 1: Names\nUnit 2: Family",
        "UNIT 1\nNAMES AND COUNTRIES\nShe is from Australia.\n1 THINK ENGLISH ELEMENT ARY STUDENT’S BOOK UNIT 1",
        "Play audio and drill the questions.\nTHINK ENGLISH ELEMENTARY TEA CHER’S BOOK UNIT 1 1",
        "UNIT 2\nFAMILY AND JOBS\nMy mother is a teacher.\nTHINK ENGLISH ELEMENTARY STUDENT’S BOOK UNIT 2 18",
        "REVISION\nUNIT 1\nBack matter must not become another unit.\nTHINK ENGLISH ELEMENTARY STUDENT’S BOOK REVISION",
    ]

    units = parse_think_english(pages)

    assert [unit["key"] for unit in units] == ["unit-1", "unit-2"]
    assert units[0]["title"] == "Unit 1: Names And Countries"
    assert "She is from Australia" in units[0]["content"]
    assert "Play audio" not in units[0]["content"]
    assert "Play audio" in units[0]["teaching_guidance"]
    assert "Back matter" not in units[1]["content"]
    assert "[PDF page 4]" in units[0]["content"]
    assert parse_think_english(["Another textbook\nUnit 1: Gardens"]) is None


def test_chapter_listing_does_not_expose_teacher_notes(monkeypatch):
    monkeypatch.setattr(materials, "extract_material_chapters", lambda _: [{
        "chapter_id": "1:unit-1", "title": "Unit 1", "material_title": "book.pdf",
        "content": "Student text", "teaching_guidance": "Private answer key",
    }])
    query = SimpleNamespace(filter=lambda _: query, order_by=lambda _: query, all=lambda: [])
    db = SimpleNamespace(query=lambda _: query)

    assert materials.list_teacher_chapters(db, 1) == [{
        "chapter_id": "1:unit-1", "title": "Unit 1", "material_title": "book.pdf",
    }]


def test_uploaded_think_english_has_six_unique_student_units(monkeypatch):
    book = next((parent / "docs" / "think-english-curriculumproject-692.pdf"
                 for parent in Path(__file__).resolve().parents
                 if (parent / "docs" / "think-english-curriculumproject-692.pdf").is_file()), None)
    if os.getenv("AIMO_TEXTBOOK_PATH"):
        book = Path(os.environ["AIMO_TEXTBOOK_PATH"])
    if book is None or not book.is_file():
        pytest.skip("Optional real textbook fixture is not available in this checkout")
    monkeypatch.setattr(materials, "MATERIAL_UPLOAD_DIR", book.parent)
    upload = SimpleNamespace(id=9, storage_filename=book.name, original_filename=book.name)

    chapters = materials.extract_material_chapters([upload])

    assert [chapter["chapter_id"] for chapter in chapters] == [f"9:unit-{i}" for i in range(1, 7)]
    assert all(len(chapter["content"]) > 5000 for chapter in chapters)
    assert all(chapter["teaching_guidance"] for chapter in chapters)
    assert "Play audio (004). Students listen" not in chapters[0]["content"]
    assert "Play audio (004). Students listen" in chapters[0]["teaching_guidance"]
    assert "[PDF page 28]" in chapters[0]["content"]
    assert "[PDF page 27]" not in chapters[0]["content"]


def test_minigame_forwards_selected_student_text_and_separate_guidance(monkeypatch):
    captured = {}
    monkeypatch.setattr(materials, "extract_material_chapters", lambda _: [{
        "chapter_id": "1:unit-1", "title": "Unit 1", "material_title": "book.pdf",
        "content": "She is from Australia.", "teaching_guidance": "Drill personal pronouns.",
    }])
    query = SimpleNamespace(filter=lambda _: query, order_by=lambda _: query, all=lambda: [])

    async def request(payload):
        captured.update(payload)
        return {"quiz": {}}

    monkeypatch.setattr(materials, "request_agent_quiz", request)
    asyncio.run(materials.generate_teacher_quiz(
        SimpleNamespace(query=lambda _: query), 1, "Unit 1", 3, "1:unit-1",
        language_practice=True, require_full_count=True,
    ))
    assert "She is from Australia" in captured["learning_material"]
    assert "Drill" not in captured["learning_material"]
    assert captured["teaching_guidance"] == "Drill personal pronouns."
    assert captured["language_practice"] is True
    assert captured["require_full_count"] is True
