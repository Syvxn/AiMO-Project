from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/quiz", tags=["quiz"])


class QuizRequest(BaseModel):
    student_id: str
    message: str


class QuizScoreRequest(BaseModel):
    student_name: str
    quiz_title: str
    score: int
    total_questions: int


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
