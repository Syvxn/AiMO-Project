import os
import json
from datetime import date
from langchain_core.tools import tool


@tool
def record_score(student_name: str, quiz_title: str, score: int, total_questions: int) -> str:
    """Record a student's quiz result to the scores log.

    Call this automatically when a student submits a quiz.
    Each result is appended as a new line to scores.jsonl at the project root.

    Args:
        student_name: Name or ID of the student.
        quiz_title: Title of the quiz that was taken.
        score: Number of correct answers.
        total_questions: Total number of questions in the quiz.
    """
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(tools_dir)))
    file_path = os.path.join(project_root, "scores.jsonl")

    record = {
        "student": student_name,
        "quiz": quiz_title,
        "score": score,
        "total": total_questions,
        "date": date.today().isoformat(),
    }

    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return f"SUCCESS: Score recorded for '{student_name}' in '{file_path}'."
    except Exception as e:
        return f"ERROR: {str(e)}"
