from pathlib import Path
import os
from typing import Iterable

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import StudyMaterial


MATERIAL_UPLOAD_DIR = Path("uploaded_materials")
MAX_MATERIAL_CHARACTERS = 60_000


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
) -> dict:
    materials = (
        db.query(StudyMaterial)
        .filter(StudyMaterial.uploaded_by_user_id == teacher_user_id)
        .order_by(StudyMaterial.created_at.desc())
        .all()
    )
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