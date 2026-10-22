from datetime import datetime
from typing import Literal
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import QuestionBankItem, User
from app.routers.auth import require_teacher_or_admin
from app.services.materials import generate_teacher_quiz, list_teacher_chapters
from app.services.question_bank import owned_chapter, supported_quote

router = APIRouter(prefix="/teacher/question-bank", tags=["teacher"])


class DraftRequest(BaseModel):
    chapter_id: str = Field(min_length=1, max_length=200)
    question_count: int = Field(default=3, ge=1, le=10)


class QuestionInput(BaseModel):
    question: str = Field(min_length=4, max_length=500)
    options: list[str] = Field(min_length=4, max_length=4)
    answer: Literal["A", "B", "C", "D"]
    skill: Literal["grammar", "vocabulary", "reading"]
    source_quote: str = Field(min_length=3, max_length=1000)
    status: Literal["draft", "approved"] = "draft"

    @field_validator("question", "source_quote")
    @classmethod
    def clean_text(cls, value):
        return " ".join(value.split())

    @field_validator("options")
    @classmethod
    def clean_options(cls, values):
        options = [re.sub(r"^[A-D][.:]\s+", "", value.strip()) for value in values]
        if any(not option or len(option) > 200 for option in options) or len({o.casefold() for o in options}) != 4:
            raise ValueError("Enter four different, non-empty options (up to 200 characters each)")
        if any(re.search(r"\b(?:all|none|both) of the above\b|\bboth [A-D] and [A-D]\b", o, re.I) for o in options):
            raise ValueError("Options must work when shuffled; avoid references to other option letters")
        return options


class CreateQuestion(QuestionInput):
    chapter_id: str = Field(min_length=1, max_length=200)


class JsonQuestion(QuestionInput):
    model_config = ConfigDict(extra="forbid")
    id: int | None = Field(default=None, gt=0, strict=True)
    chapter_id: str | None = Field(default=None, min_length=1, max_length=200)
    reviewed_at: datetime | None = None


class BankJsonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chapter_id: str = Field(min_length=1, max_length=200)
    questions: list[JsonQuestion] = Field(max_length=500)
    approve_all: bool = False


CONTENT_FIELDS = ("question", "options", "answer", "skill", "source_quote")


def serialise(item):
    return {key: getattr(item, key) for key in (
        "id", "chapter_id", "question", "options", "answer", "skill", "source_quote", "status", "reviewed_at",
    )}


def get_item(db, teacher_id, item_id):
    item = db.query(QuestionBankItem).filter(QuestionBankItem.id == item_id, QuestionBankItem.teacher_user_id == teacher_id).first()
    if item is None:
        raise HTTPException(404, "Question not found")
    return item


def validate_evidence(payload, chapter):
    if not payload.question.strip() or not supported_quote(payload.source_quote, chapter["content"]):
        raise HTTPException(422, "Use an exact source quotation from the student lesson text, not teacher guidance.")


@router.get("/chapters")
def chapters(user: User = Depends(require_teacher_or_admin), db: Session = Depends(get_db)):
    return {"chapters": list_teacher_chapters(db, user.id)}


@router.get("")
def list_questions(chapter_id: str, user: User = Depends(require_teacher_or_admin), db: Session = Depends(get_db)):
    chapter = owned_chapter(db, user.id, chapter_id)
    items = db.query(QuestionBankItem).filter(QuestionBankItem.teacher_user_id == user.id, QuestionBankItem.chapter_id == chapter_id).order_by(QuestionBankItem.id).all()
    return {"questions": [serialise(item) for item in items], "student_text": chapter["content"],
            "teaching_guidance": chapter.get("teaching_guidance", "")}


@router.put("/json")
def save_bank_json(payload: BankJsonRequest, user: User = Depends(require_teacher_or_admin), db: Session = Depends(get_db)):
    chapter = owned_chapter(db, user.id, payload.chapter_id)
    existing = db.query(QuestionBankItem).filter(
        QuestionBankItem.teacher_user_id == user.id, QuestionBankItem.chapter_id == payload.chapter_id,
    ).with_for_update().all()
    by_id = {item.id: item for item in existing}
    seen_ids = set()
    plan = []
    # Validate the complete batch before changing any row, including approvals.
    for index, question in enumerate(payload.questions, 1):
        label = f"Question {index}"
        if question.chapter_id is not None and question.chapter_id != payload.chapter_id:
            raise HTTPException(422, f"{label}: chapter_id must match the selected unit.")
        if question.id is not None:
            if question.id in seen_ids:
                raise HTTPException(422, f"{label}: question ID {question.id} appears more than once.")
            seen_ids.add(question.id)
            if question.id not in by_id:
                raise HTTPException(404, f"{label}: question ID {question.id} was not found in the selected unit.")
        try:
            validate_evidence(question, chapter)
        except HTTPException as exc:
            raise HTTPException(exc.status_code, f"{label}: {exc.detail}") from exc
        data = question.model_dump(include=set(CONTENT_FIELDS))
        item = by_id.get(question.id)
        changed = item is None or any(getattr(item, key) != value for key, value in data.items())
        plan.append((item, data, changed))

    created = updated = unchanged = approved = 0
    now = datetime.utcnow()
    for item, data, changed in plan:
        if item is None:
            item = QuestionBankItem(teacher_user_id=user.id, material_id=int(payload.chapter_id.split(":", 1)[0]),
                                    chapter_id=payload.chapter_id, **data, status="draft")
            db.add(item)
            created += 1
        elif changed:
            for key, value in data.items():
                setattr(item, key, value)
            updated += 1
        else:
            unchanged += 1
        if payload.approve_all:
            item.status = "approved"
            item.reviewed_at = now
            approved += 1
        elif changed:
            item.status = "draft"
            item.reviewed_at = None
        # Embedded status/reviewed_at values never grant approval.
    db.commit()
    items = db.query(QuestionBankItem).filter(
        QuestionBankItem.teacher_user_id == user.id, QuestionBankItem.chapter_id == payload.chapter_id,
    ).order_by(QuestionBankItem.id).all()
    return {"questions": [serialise(item) for item in items], "created": created, "updated": updated,
            "unchanged": unchanged, "approved": approved}


@router.post("/drafts")
async def generate_drafts(payload: DraftRequest, user: User = Depends(require_teacher_or_admin), db: Session = Depends(get_db)):
    chapter = owned_chapter(db, user.id, payload.chapter_id)
    result = await generate_teacher_quiz(db, user.id, chapter["title"], payload.question_count,
                                         payload.chapter_id, language_practice=True, request_timeout=600.0)
    created = []
    skipped = 0
    for question in result.get("quiz", {}).get("questions", []):
        try:
            if not isinstance(question, dict):
                skipped += 1
                continue
            data = QuestionInput.model_validate({**question, "status": "draft"})
            validate_evidence(data, chapter)
        except (ValidationError, HTTPException):
            # A bad candidate must not discard the rest of a slow model batch.
            skipped += 1
            continue
        item = QuestionBankItem(teacher_user_id=user.id, material_id=int(payload.chapter_id.split(":", 1)[0]),
                                chapter_id=payload.chapter_id, **data.model_dump())
        db.add(item)
        created.append(item)
    if not created:
        raise HTTPException(422, "No drafts passed the question and source checks. Try fewer questions or add a question manually.")
    db.commit()
    return {"questions": [serialise(item) for item in created], "skipped_count": skipped}


@router.post("")
def create_question(payload: CreateQuestion, user: User = Depends(require_teacher_or_admin), db: Session = Depends(get_db)):
    chapter = owned_chapter(db, user.id, payload.chapter_id)
    validate_evidence(payload, chapter)
    data = payload.model_dump()
    item = QuestionBankItem(teacher_user_id=user.id, material_id=int(payload.chapter_id.split(":", 1)[0]),
                            reviewed_at=datetime.utcnow() if payload.status == "approved" else None, **data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialise(item)


@router.put("/{item_id}")
def update_question(item_id: int, payload: QuestionInput, user: User = Depends(require_teacher_or_admin), db: Session = Depends(get_db)):
    item = get_item(db, user.id, item_id)
    chapter = owned_chapter(db, user.id, item.chapter_id)
    validate_evidence(payload, chapter)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    item.reviewed_at = datetime.utcnow() if payload.status == "approved" else None
    db.commit()
    db.refresh(item)
    return serialise(item)


@router.delete("/{item_id}")
def delete_question(item_id: int, user: User = Depends(require_teacher_or_admin), db: Session = Depends(get_db)):
    item = get_item(db, user.id, item_id)
    db.delete(item)
    db.commit()
    return {"status": "deleted"}
