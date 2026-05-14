from datetime import datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import StudyMaterial, User
from app.routers.auth import require_teacher_or_admin, user_role_to_str

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


def ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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
    if suffix not in {".txt", ".pdf"}:
        raise HTTPException(status_code=400, detail="Only .txt and .pdf files are allowed")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if suffix == ".pdf":
        try:
            reader = PdfReader(BytesIO(raw))
            text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except Exception:
            raise HTTPException(status_code=400, detail="Could not read PDF — file may be corrupted or scanned-only")
        if not text:
            raise HTTPException(status_code=400, detail="No extractable text found in PDF (scanned-only PDFs are not supported)")
        content = text.encode("utf-8")
    else:
        content = raw

    ensure_upload_dir()
    storage_filename = f"{uuid4().hex}.txt"
    destination = UPLOAD_DIR / storage_filename
    destination.write_bytes(content)

    material = StudyMaterial(
        original_filename=file.filename,
        description=description.strip(),
        storage_filename=storage_filename,
        content_type="text/plain",
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
    material = db.query(StudyMaterial).filter(StudyMaterial.id == material_id).first()
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")

    user_role = user_role_to_str(current_user.role)
    if user_role == "teacher" and material.uploaded_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own materials")

    file_path = UPLOAD_DIR / material.storage_filename
    if file_path.exists():
        file_path.unlink()

    db.delete(material)
    db.commit()
    return {"status": "deleted", "message": f"Deleted {material.original_filename}"}