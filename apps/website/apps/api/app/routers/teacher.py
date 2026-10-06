from datetime import datetime
from pathlib import Path
import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import StudyMaterial, User
from app.routers.auth import require_teacher_or_admin, user_role_to_str
from app.services.materials import generate_teacher_quiz as generate_quiz_from_teacher_materials

router = APIRouter(prefix="/teacher", tags=["teacher"])

UPLOAD_DIR = Path("uploaded_materials")


class TeacherChatRequest(BaseModel):
    message: str


class TeacherChatResponse(BaseModel):
    reply: str
    status: str


class TeacherMaterialResponse(BaseModel):
    id: int
    original_filename: str
    description: str
    content_type: str
    size_bytes: int
    uploaded_by_user_id: int
    created_at: datetime


class TeacherMaterialPreviewResponse(BaseModel):
    id: int
    original_filename: str
    content: str


class TeacherQuizRequest(BaseModel):
    topic: str
    question_count: int = 5


class TeacherClassCodeResponse(BaseModel):
    class_code: str
    joined_students: int


def ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/class-code", response_model=TeacherClassCodeResponse)
def get_teacher_class_code(
    current_user: User = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db),
) -> TeacherClassCodeResponse:
    if user_role_to_str(current_user.role) != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can manage a class")

    if not current_user.class_code:
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        for _ in range(10):
            class_code = "".join(secrets.choice(alphabet) for _ in range(8))
            if not db.query(User).filter(User.class_code == class_code).first():
                current_user.class_code = class_code
                db.commit()
                db.refresh(current_user)
                break
        else:
            raise HTTPException(status_code=503, detail="Could not create a class code")

    joined_students = (
        db.query(User)
        .filter(User.teacher_user_id == current_user.id)
        .count()
    )
    return TeacherClassCodeResponse(
        class_code=current_user.class_code,
        joined_students=joined_students,
    )


def get_material_for_user(material_id: int, current_user: User, db: Session) -> StudyMaterial:
    material = db.query(StudyMaterial).filter(StudyMaterial.id == material_id).first()
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")

    if (
        user_role_to_str(current_user.role) == "teacher"
        and material.uploaded_by_user_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="You can only access your own materials")
    return material


@router.post("/chat", response_model=TeacherChatResponse)
def teacher_chat(
    payload: TeacherChatRequest,
    current_user: User = Depends(require_teacher_or_admin),
) -> TeacherChatResponse:
    _ = current_user
    _ = payload
    reply = (
        "Analytics assistant stub: this chat will summarize student progress, quiz outcomes, "
        "engagement patterns, and teacher-facing insights once the analytics agent is implemented."
    )
    return TeacherChatResponse(reply=reply, status="stub")


@router.post("/materials/upload", response_model=TeacherMaterialResponse)
async def upload_study_material(
    file: UploadFile = File(...),
    description: str = Form(default=""),
    current_user: User = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db),
) -> TeacherMaterialResponse:
    _ = description

    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".txt", ".md", ".pdf"}:
        raise HTTPException(
            status_code=400,
            detail="Only .txt, .md, and .pdf files are allowed",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    ensure_upload_dir()
    storage_filename = f"{uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / storage_filename
    destination.write_bytes(content)

    material = StudyMaterial(
        original_filename=file.filename,
        description=description.strip(),
        storage_filename=storage_filename,
        content_type=file.content_type or "text/plain",
        size_bytes=len(content),
        uploaded_by_user_id=current_user.id,
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    return TeacherMaterialResponse(
        id=material.id,
        original_filename=material.original_filename,
        description=material.description,
        content_type=material.content_type,
        size_bytes=material.size_bytes,
        uploaded_by_user_id=material.uploaded_by_user_id,
        created_at=material.created_at,
    )


@router.get("/materials/{material_id}/preview", response_model=TeacherMaterialPreviewResponse)
def preview_study_material(
    material_id: int,
    current_user: User = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db),
) -> TeacherMaterialPreviewResponse:
    material = get_material_for_user(material_id, current_user, db)
    file_path = UPLOAD_DIR / material.storage_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored material file not found")

    if file_path.suffix.lower() in {".txt", ".md"}:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    else:
        from pypdf import PdfReader

        content = "\n\n".join(
            page.extract_text() or "" for page in PdfReader(str(file_path)).pages
        )

    return TeacherMaterialPreviewResponse(
        id=material.id,
        original_filename=material.original_filename,
        content=content[:20000],
    )


@router.get("/materials/{material_id}/file")
def open_study_material(
    material_id: int,
    current_user: User = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Serve the original material inline for browser-native previewing."""
    material = get_material_for_user(material_id, current_user, db)
    file_path = UPLOAD_DIR / material.storage_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored material file not found")

    return FileResponse(
        path=file_path,
        media_type=material.content_type,
        filename=material.original_filename,
        content_disposition_type="inline",
    )


@router.post("/quiz/generate")
async def generate_teacher_quiz(
    payload: TeacherQuizRequest,
    current_user: User = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db),
) -> dict:
    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required")
    if not 1 <= payload.question_count <= 20:
        raise HTTPException(status_code=400, detail="Question count must be between 1 and 20")
    return await generate_quiz_from_teacher_materials(
        db,
        teacher_user_id=current_user.id,
        topic=topic,
        question_count=payload.question_count,
    )


@router.get("/materials", response_model=list[TeacherMaterialResponse])
def list_study_materials(
    current_user: User = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db),
) -> list[TeacherMaterialResponse]:
    query = db.query(StudyMaterial)
    if user_role_to_str(current_user.role) == "teacher":
        query = query.filter(StudyMaterial.uploaded_by_user_id == current_user.id)

    materials = query.order_by(StudyMaterial.created_at.desc()).all()
    return [
        TeacherMaterialResponse(
            id=item.id,
            original_filename=item.original_filename,
            description=item.description,
            content_type=item.content_type,
            size_bytes=item.size_bytes,
            uploaded_by_user_id=item.uploaded_by_user_id,
            created_at=item.created_at,
        )
        for item in materials
    ]


@router.delete("/materials/{material_id}")
def delete_study_material(
    material_id: int,
    current_user: User = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    material = get_material_for_user(material_id, current_user, db)

    file_path = UPLOAD_DIR / material.storage_filename
    if file_path.exists():
        file_path.unlink()

    db.delete(material)
    db.commit()
    return {"status": "deleted", "message": f"Deleted {material.original_filename}"}