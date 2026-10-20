from pathlib import Path
import os
import re
from typing import Iterable

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import StudyMaterial


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

        book_chapters: list[dict[str, str]] = []
        current: dict[str, str] | None = None
        for page in pages:
            lines = page.splitlines()
            if skip_contents_pages and any(CONTENTS_HEADER.match(line) for line in lines[:12]):
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
                    current = next((item for item in book_chapters if item["title"] == title), None)
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
        {key: value for key, value in chapter.items() if key != "content"}
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
    teacher_user_id: int,
    topic: str,
    question_count: int,
    chapter_id: str | None = None,
) -> dict:
    materials = (
        db.query(StudyMaterial)
        .filter(StudyMaterial.uploaded_by_user_id == teacher_user_id)
        .order_by(StudyMaterial.created_at.desc())
        .all()
    )
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
    else:
        learning_material = read_uploaded_materials(materials)
    if not learning_material:
        raise HTTPException(
            status_code=422,
            detail="Your teacher has not uploaded readable study material yet.",
        )

    agents_url = os.getenv("AGENTS_SERVICE_URL", "http://agents:8001")
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{agents_url}/quiz/generate",
                json={
                    "topic": topic,
                    "question_count": question_count,
                    "learning_material": learning_material,
                },
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Quiz agent is unavailable") from exc

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Quiz agent failed to generate a quiz")
    result = response.json()
    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])
    return result