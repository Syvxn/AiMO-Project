"""Teacher-owned drafts and approved exercises; game requests never call a model."""
import random
import re
import unicodedata

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import QuestionBankItem, StudyMaterial
from app.services.materials import extract_material_chapters

LETTERS = "ABCD"


def owned_chapter(db: Session, teacher_id: int, chapter_id: str) -> dict:
    # Filter ownership before reading any uploaded file.
    materials = db.query(StudyMaterial).filter(StudyMaterial.uploaded_by_user_id == teacher_id).all()
    chapter = next((c for c in extract_material_chapters(materials) if c["chapter_id"] == chapter_id), None)
    if chapter is None:
        raise HTTPException(404, "Selected chapter was not found")
    return chapter


def supported_quote(quote: str, source: str) -> bool:
    def normalise(text):
        return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).replace("’", "'").replace("‘", "'")).strip().casefold()
    quote = normalise(quote)
    return bool(quote) and re.search(r"(?<!\w)" + re.escape(quote) + r"(?!\w)", normalise(source)) is not None


def game_quiz(db: Session, teacher_id: int, chapter_id: str | None, count: int) -> dict:
    # Joining the material prevents deleted or transferred uploads being served.
    query = db.query(QuestionBankItem).join(StudyMaterial, StudyMaterial.id == QuestionBankItem.material_id).filter(
        QuestionBankItem.teacher_user_id == teacher_id,
        StudyMaterial.uploaded_by_user_id == teacher_id,
        QuestionBankItem.status == "approved",
        QuestionBankItem.reviewed_at.isnot(None),
    )
    if chapter_id:
        query = query.filter(QuestionBankItem.chapter_id == chapter_id)
    items = query.all()
    if len(items) < count:
        raise HTTPException(422, f"This unit has {len(items)} approved questions and needs {count}. Ask your teacher to approve more questions in the question bank.")
    random.shuffle(items)
    selected = []
    if count >= 3:
        for skill in ("grammar", "vocabulary", "reading"):
            match = next((item for item in items if item.skill == skill), None)
            if match:
                selected.append(match)
    selected.extend(item for item in items if item not in selected)
    questions = []
    for item in selected[:count]:
        order = random.sample(range(4), 4)
        questions.append({
            "question": item.question,
            "options": [f"{LETTERS[i]}: {item.options[j]}" for i, j in enumerate(order)],
            "answer": LETTERS[order.index(LETTERS.index(item.answer))],
            "skill": item.skill,
        })
    random.shuffle(questions)
    return {"quiz": {"quiz_title": "Textbook practice", "questions": questions}}
