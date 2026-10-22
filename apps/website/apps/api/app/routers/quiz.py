from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RoleEnum, User
from app.routers.auth import get_current_user, user_role_to_str
from app.services.question_bank import game_quiz
from app.services.materials import (
    generate_teacher_quiz,
    list_suggested_topics,
    list_teacher_chapters,
    topic_from_suggestion,
)

router = APIRouter(prefix="/quiz", tags=["quiz"])

MAX_TOPIC_CHARACTERS = 120


class QuizRequest(BaseModel):
    student_id: str
    message: str


class QuizScoreRequest(BaseModel):
    student_name: str
    quiz_title: str
    score: int
    total_questions: int


class JoinClassRequest(BaseModel):
    class_code: str


class StudentQuizRequest(BaseModel):
    topic: str = "general"
    question_count: int = 5
    chapter_id: str | None = None


@router.post("/join-class")
def join_class(
    payload: JoinClassRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if user_role_to_str(current_user.role) != "student":
        raise HTTPException(status_code=403, detail="Only student accounts can join a class")
    class_code = payload.class_code.strip().upper()
    if len(class_code) != 8:
        raise HTTPException(status_code=400, detail="Enter a valid 8-character class code")
    teacher = (
        db.query(User)
        .filter(User.class_code == class_code, User.role == RoleEnum.teacher)
        .first()
    )
    if teacher is None:
        raise HTTPException(status_code=404, detail="Class code not found")
    if current_user.teacher_user_id not in (None, teacher.id):
        raise HTTPException(status_code=409, detail="You are already enrolled in another class")
    current_user.teacher_user_id = teacher.id
    db.commit()
    return {"status": "joined"}


@router.post("/game/generate")
async def generate_student_quiz(
    payload: StudentQuizRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if user_role_to_str(current_user.role) != "student":
        raise HTTPException(status_code=403, detail="Only student accounts can request class quizzes")
    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required")
    if len(topic) > MAX_TOPIC_CHARACTERS:
        raise HTTPException(status_code=400, detail="Topic is too long")
    if not 1 <= payload.question_count <= 20:
        raise HTTPException(status_code=400, detail="Question count must be between 1 and 20")
    # Students in a class use their teacher's uploads; everyone else gets the model's own knowledge.
    if current_user.teacher_user_id is None:
        topic = topic_from_suggestion(payload.chapter_id) or topic
    else:
        return game_quiz(db, current_user.teacher_user_id, payload.chapter_id, payload.question_count)
    return await generate_teacher_quiz(
        db,
        teacher_user_id=current_user.teacher_user_id,
        topic=topic,
        question_count=payload.question_count,
        chapter_id=payload.chapter_id,
        language_practice=True,
        require_full_count=True,
    )


@router.get("/game/chapters")
def get_student_quiz_chapters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, str]]]:
    if user_role_to_str(current_user.role) != "student":
        raise HTTPException(status_code=403, detail="Only student accounts can request class quizzes")
    if current_user.teacher_user_id is None:
        return {"chapters": list_suggested_topics()}
    chapters = list_teacher_chapters(db, teacher_user_id=current_user.teacher_user_id)
    if not chapters:
        raise HTTPException(status_code=422, detail="No readable chapters found in your teacher's materials")
    return {"chapters": chapters}


@router.post("/chat")
def quiz_chat(payload: QuizRequest) -> dict:
    # Response shape is aligned with the Godot client's current quiz expectation.
    return {
        "quiz": {
            "quiz_title": f"Practice Quiz: {payload.message[:30]}",
            "questions": [
                {
                    "question": "Which option best matches the study topic?",
                    "options": ["A", "B", "C", "D"],
                    "answer": "A",
                }
            ],
        }
    }


@router.post("/score")
def submit_score(payload: QuizScoreRequest) -> dict[str, str]:
    # Placeholder endpoint to be replaced with DB persistence.
    _ = payload
    return {"status": "saved"}
