from pathlib import Path
import os
import re
from typing import Iterable

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import StudyMaterial
from app.services.textbooks import parse_think_english


MATERIAL_UPLOAD_DIR = Path("uploaded_materials")
MAX_MATERIAL_CHARACTERS = 60_000
CHAPTER_HEADER = re.compile(
    r"^\s*((?:chapter|unit|lesson)\s+\d+(?:\s*[:.-]\s*.*)?)\s*$",
    re.IGNORECASE,
)
CONTENTS_HEADER = re.compile(r"^\s*(table of )?contents\s*$", re.IGNORECASE)


def extract_material_chapters(materials: Iterable[StudyMaterial]) -> list[dict[str, str]]:
    """Split uploaded books on visible chapter/unit headings."""
    chapters: list[dict[str, str]] = []

    for material in materials:
        path = MATERIAL_UPLOAD_DIR / material.storage_filename
        if not path.is_file():
            continue

        if path.suffix.lower() in {".txt", ".md"}:
            pages = [path.read_text(encoding="utf-8", errors="replace")]
            # A text file is one "page", so only its contents block may be skipped.
            skip_contents_pages = False
        elif path.suffix.lower() == ".pdf":
            from pypdf import PdfReader

            pages = [page.extract_text() or "" for page in PdfReader(path).pages]
            skip_contents_pages = True
        else:
            continue

        textbook_units = parse_think_english(pages) if skip_contents_pages else None
        if textbook_units is not None:
            material_id = str(getattr(material, "id", material.storage_filename))
            chapters.extend(
                {
                    "chapter_id": f"{material_id}:{unit['key']}",
                    "title": unit["title"],
                    "material_title": material.original_filename,
                    "content": unit["content"],
                    "teaching_guidance": unit["teaching_guidance"],
                }
                for unit in textbook_units
            )
            continue

        book_chapters: list[dict[str, str]] = []
        current: dict[str, str] | None = None
        for page in pages:
            lines = page.splitlines()
            if skip_contents_pages and any(CONTENTS_HEADER.match(line) for line in lines):
                continue

            in_contents_block = False
            for line in lines:
                if not skip_contents_pages:
                    if CONTENTS_HEADER.match(line):
                        in_contents_block = True
                        continue
                    if in_contents_block:
                        in_contents_block = bool(line.strip())
                        continue
                match = CHAPTER_HEADER.match(line)
                if match:
                    title = re.sub(r"\s+", " ", match.group(1)).strip()
                    current = next((item for item in book_chapters if item["title"].casefold() == title.casefold()), None)
                    if current is None:
                        current = {"title": title, "content": ""}
                        book_chapters.append(current)
                    continue
                if current is not None and line.strip():
                    current["content"] += line.strip() + "\n"

        if not book_chapters:
            content = "\n\n".join(pages).strip()
            if content:
                book_chapters.append({"title": "Whole document", "content": content})

        material_id = str(getattr(material, "id", material.storage_filename))
        for chapter in book_chapters:
            content = chapter["content"].strip()
            if not content:
                continue
            slug = re.sub(r"[^a-z0-9]+", "-", chapter["title"].lower()).strip("-")
            chapters.append(
                {
                    "chapter_id": f"{material_id}:{slug}",
                    "title": chapter["title"],
                    "material_title": material.original_filename,
                    "content": content,
                }
            )

    return chapters


def list_teacher_chapters(db: Session, teacher_user_id: int) -> list[dict[str, str]]:
    materials = (
        db.query(StudyMaterial)
        .filter(StudyMaterial.uploaded_by_user_id == teacher_user_id)
        .order_by(StudyMaterial.created_at.desc())
        .all()
    )
    return [
        {key: chapter[key] for key in ("chapter_id", "title", "material_title")}
        for chapter in extract_material_chapters(materials)
    ]


def read_uploaded_materials(materials: Iterable[StudyMaterial]) -> str:
    """Read teacher-owned text and PDF files into bounded quiz context."""
    sections: list[str] = []
    remaining = MAX_MATERIAL_CHARACTERS

    for material in materials:
        path = MATERIAL_UPLOAD_DIR / material.storage_filename
        if not path.is_file():
            continue

        if path.suffix.lower() in {".txt", ".md"}:
            content = path.read_text(encoding="utf-8", errors="replace")
        elif path.suffix.lower() == ".pdf":
            from pypdf import PdfReader

            content = "\n\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        else:
            continue

        content = content.strip()
        if not content:
            continue

        section = f"Source: {material.original_filename}\n{content}"
        section = section[:remaining]
        sections.append(section)
        remaining -= len(section)
        if remaining <= 0:
            break

    return "\n\n".join(sections)


async def generate_teacher_quiz(
    db: Session,
    teacher_user_id: int | None,
    topic: str,
    question_count: int,
    chapter_id: str | None = None,
    language_practice: bool = False,
    require_full_count: bool = False,
    request_timeout: float = 180.0,
) -> dict:
    """Quiz from a teacher's uploads, or from the model's own knowledge when there is no teacher."""
    options = {}
    request_options = {"timeout_seconds": request_timeout} if request_timeout != 180.0 else {}
    if language_practice:
        options["language_practice"] = True
    if require_full_count:
        options["require_full_count"] = True
    if teacher_user_id is None:
        return await request_agent_quiz(
            {"topic": topic, "question_count": question_count, "use_model_knowledge": True, **options},
            **request_options,
        )

    materials = (
        db.query(StudyMaterial)
        .filter(StudyMaterial.uploaded_by_user_id == teacher_user_id)
        .order_by(StudyMaterial.created_at.desc())
        .all()
    )
    teaching_guidance = ""
    if chapter_id:
        chapter = next(
            (item for item in extract_material_chapters(materials) if item["chapter_id"] == chapter_id),
            None,
        )
        if chapter is None:
            raise HTTPException(status_code=404, detail="Selected chapter was not found")
        topic = chapter["title"]
        learning_material = (
            f"Source: {chapter['material_title']}\n"
            f"Chapter: {chapter['title']}\n{chapter['content']}"
        )
        teaching_guidance = chapter.get("teaching_guidance", "")
    else:
        chapters = extract_material_chapters(materials)
        if any("teaching_guidance" in chapter for chapter in chapters):
            # Share the context budget across units, so later units are represented.
            budget = MAX_MATERIAL_CHARACTERS // max(1, len(chapters))
            learning_material = "\n\n---\n\n".join(
                f"Source: {chapter['material_title']}\nChapter: {chapter['title']}\n"
                + chapter["content"][:budget] for chapter in chapters
            )
            teaching_guidance = "\n\n---\n\n".join(
                chapter.get("teaching_guidance", "")[:budget] for chapter in chapters
            )
        else:
            learning_material = read_uploaded_materials(materials)
    if not learning_material:
        raise HTTPException(
            status_code=422,
            detail="Your teacher has not uploaded readable study material yet.",
        )

    return await request_agent_quiz(
        {
            "topic": topic,
            "question_count": question_count,
            "learning_material": learning_material,
            **({"teaching_guidance": teaching_guidance} if teaching_guidance else {}),
            **options,
        },
        **request_options,
    )


async def request_agent_quiz(payload: dict, timeout_seconds: float = 180.0) -> dict:
    agents_url = os.getenv("AGENTS_SERVICE_URL", "http://agents:8001")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_seconds, connect=5.0)) as client:
            response = await client.post(f"{agents_url}/quiz/generate", json=payload)
    except httpx.ReadTimeout as exc:
        raise HTTPException(
            status_code=504,
            detail="Quiz generation took too long. Try a smaller question count. Your saved bank questions are unchanged.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Quiz agent is unavailable") from exc

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Quiz agent failed to generate a quiz")
    result = response.json()
    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])
    return result


# Offered to students without a class, who have no teacher chapters to pick from.
SUGGESTED_TOPICS = [
    "Greetings and introductions",
    "Numbers and counting",
    "Colours",
    "Days of the week and months",
    "School and classroom vocabulary",
    "Family members",
    "Food and drinks",
    "Animals",
    "Weather and seasons",
    "Present simple tense",
    "Present continuous tense",
    "Common adjectives and opposites",
]
TOPIC_ID_PREFIX = "topic:"


def list_suggested_topics() -> list[dict[str, str]]:
    return [
        {
            "chapter_id": f"{TOPIC_ID_PREFIX}{topic}",
            "title": topic,
            "material_title": "General knowledge",
        }
        for topic in SUGGESTED_TOPICS
    ]


def topic_from_suggestion(chapter_id: str | None) -> str | None:
    """Return the topic of a suggested-topic id, or None for anything else."""
    if chapter_id and chapter_id.startswith(TOPIC_ID_PREFIX):
        topic = chapter_id[len(TOPIC_ID_PREFIX):]
        if topic in SUGGESTED_TOPICS:
            return topic
    return None
