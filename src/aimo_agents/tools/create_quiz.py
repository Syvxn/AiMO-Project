import os
import json
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
    
    ### This needs to be updated based on our implementation ###
    toolsit_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(toolsit_dir)
    file_path = os.path.join(project_root, "study_quiz.json")
    
    quiz_data = {
        "quiz_title": quiz_title,
        "questions": questions
    }
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(quiz_data, f, indent=4)
        return f"SUCCESS: The quiz has been saved at {file_path}."
    except Exception as e:
        return f"ERROR: {str(e)}"
