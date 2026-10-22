import os
import json
import uuid
from datetime import datetime, timezone
from langchain_core.tools import tool

# Here is the main structure, modify this to our needs 
@tool
def create_quiz(quiz_title: str, questions: list) -> str:
    """ Create a quiz based on the material "retrieve_notes" tool retrieved. 
    Always call retrieve_notes first and pass its output here

    REQUIREMENT: The input MUST be a raw JSON string with this structure:
    {
        "quiz_title": "Title",
        "questions": [
            {"question": "...", "options": ["a", "b", "c"], "answer": "a"}
        ]
    }

    For example: 
    {
        "English multiple choice quiz": "Vocabulary",
        "questions": [
            {"question": "What does bizarre mean", "options":["a:To show something that was hidden","b:The pleasant smell of rain",
            "c. Very strange or unusual"], "answer": "c"}
            
        ]
    }

    There should be 5 questions
    """
    print("---CREATING JSON QUIZ ---")
    
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    # tools/ → aimo_agents/ → src/ → AiMO-Agents/
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(tools_dir)))
    quiz_dir = os.path.join(project_root, "generated_quizzes")
    # A unique name per quiz keeps concurrent requests from overwriting each other.
    file_path = os.path.join(
        quiz_dir, f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:8]}.json"
    )
    
    quiz_data = {
        "quiz_title": quiz_title,
        "questions": questions
    }
    try:
        os.makedirs(quiz_dir, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(quiz_data, f, indent=4)
        return f"SUCCESS: The quiz has been saved at {file_path}."
    except Exception as e:
        return f"ERROR: {str(e)}"
