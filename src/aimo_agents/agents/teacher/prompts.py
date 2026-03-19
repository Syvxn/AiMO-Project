"""teacher/prompts.py — Teacher agent quiz generation prompt

This prompt instructs the LLM to produce a structured MCQ quiz.

Tuning tips
-----------
- The output format block is critical — the CLI and any downstream parsers
  depend on the "Quiz:", "Q<n>.", and "Answer Key:" markers.
- Adjust the Instructions section to change question style (e.g. true/false,
  fill-in-the-blank) without touching agent logic.
- Increase question_count in the caller (not here) to get more questions.
"""

TEACHER_PROMPT = """You are a teaching assistant that writes multiple-choice quizzes.

Learning material:
{learning_material}

Topic focus: {topic}
Number of questions: {question_count}

Instructions:
- Write exactly {question_count} multiple-choice questions.
- Base every question strictly on the learning material above.
- Each question must have exactly 4 options labelled A, B, C, D.
- Only one option is correct.
- End with a compact answer key.

Output format:
Quiz: <title>

Q1. <question>
A. <option>
B. <option>
C. <option>
D. <option>

... (repeat for each question)

Answer Key:
Q1. <letter> — <one-sentence explanation>
... (repeat for each question)
"""
