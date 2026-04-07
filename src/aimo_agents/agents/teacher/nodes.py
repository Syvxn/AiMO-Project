"""Teacher node implementations."""
from __future__ import annotations

import json
import random
import re

from langchain_core.runnables import Runnable

from ...tools.create_quiz import create_quiz as create_quiz_tool
from ...tools.retrieve_material import retrieve_material as retrieve_material_tool
from .state import TeacherState

_LETTERS = ["A", "B", "C", "D"]

_FEW_SHOT_EXAMPLE = """\
Example of a good question:
{
  "question": "What colour is the sky described as in the text?",
  "options": ["A: Red", "B: Blue", "C: Green", "D: Yellow"],
  "answer": "B"
}
Example of a good question with a different style:
{
  "question": "Complete the sentence: 'Purple is a mix of red and ___.'",
  "options": ["A: yellow", "B: green", "C: blue", "D: orange"],
  "answer": "C"
}"""


def teacher_tool_node(state: TeacherState) -> dict:
    """Retrieve learning material via RAG for the requested topic."""
    topic = state.get("topic", "general")
    # Use "chapter <topic>" as the chapter arg so the query is more specific
    # and avoids drifting into unrelated chapters that mention the word incidentally.
    material = retrieve_material_tool.invoke({"chapter": f"chapter {topic}", "topic": topic})
    return {"learning_material": material}


def teacher_llm_call(state: TeacherState, llm: Runnable) -> dict:
    """Generate quiz questions from retrieved material and save them."""
    material = state.get("learning_material", "")
    topic = state.get("topic", "English")
    n = state.get("question_count", 5)
    llm_calls = state.get("llm_calls", 0)

    # Limit to ~1 200 words to stay within the model's context window.
    excerpt = " ".join(material.split()[:1200])

    prompt = (
        "<|im_start|>system\n"
        "You are an English teacher creating a multiple-choice quiz. "
        "Output ONLY a single valid JSON object — no prose, no markdown, no code fences.\n"
        "<|im_end|>\n"
        "<|im_start|>user\n"
        f"Create exactly {n} multiple-choice questions for Finnish 5th graders about \"{topic}\".\n\n"
        "RULES:\n"
        f"1. Base every question on a specific fact found in the study material below.\n"
        "2. Use a DIFFERENT question style for each question. Vary among:\n"
        "   - 'What is [property] of [thing]?' — fact recall\n"
        "   - 'Which of these is [descriptor]?' — identification\n"
        "   - Complete the sentence: '...' — fill-in-the-blank\n"
        "   - 'Which sentence uses [word] correctly?' — usage\n"
        "   - 'How do you say [concept] in English?' — vocabulary\n"
        "3. Distractors must be clearly wrong but plausible (e.g. other colours, related words).\n"
        "4. The correct answer position (A/B/C/D) must differ across questions.\n\n"
        f"{_FEW_SHOT_EXAMPLE}\n\n"
        f"Study material:\n{excerpt}\n\n"
        "Output ONLY this JSON, no other text:\n"
        '{"quiz_title": "English Quiz: ' + topic + '", '
        '"questions": [{"question": "...", "options": ["A: ...", "B: ...", "C: ...", "D: ..."], "answer": "B"}]}\n'
        "<|im_end|>\n"
        "<|im_start|>assistant\n"
    )

    raw = llm.invoke(prompt)
    if isinstance(raw, dict):
        raw = raw.get("text", str(raw))

    quiz_data = _extract_json(raw)
    if quiz_data is None:
        return {
            "llm_calls": llm_calls + 1,
            "error": f"LLM did not return valid JSON. Raw output: {raw[:400]}",
        }

    quiz_title = quiz_data.get("quiz_title", f"English Quiz: {topic}")
    questions = _postprocess(quiz_data.get("questions", []))

    save_result = create_quiz_tool.invoke(
        {"quiz_title": quiz_title, "questions": questions}
    )

    return {
        "quiz": save_result,
        "llm_calls": llm_calls + 1,
    }


# ---------------------------------------------------------------------------
# Post-processing helpers
# ---------------------------------------------------------------------------

def _postprocess(questions: list[dict]) -> list[dict]:
    """Validate, deduplicate, and shuffle answer positions."""
    valid: list[dict] = []
    seen_questions: set[str] = set()
    seen_option_sets: list[frozenset] = []

    for q in questions:
        # Basic structure check
        opts = q.get("options", [])
        ans = q.get("answer", "")
        text = q.get("question", "").strip()
        if not text or len(opts) != 4 or ans not in _LETTERS:
            continue

        # Deduplicate by question text
        key = text.lower()
        if key in seen_questions:
            continue
        seen_questions.add(key)

        # Deduplicate by option set (catches questions with identical choices)
        opt_values = frozenset(o.split(":", 1)[-1].strip().lower() for o in opts)
        if opt_values in seen_option_sets:
            continue
        seen_option_sets.append(opt_values)

        valid.append(_shuffle_answer(q))

    return valid


def _shuffle_answer(q: dict) -> dict:
    """Rotate the correct answer to a random letter position."""
    opts = q["options"]
    current_letter = q["answer"]

    # Strip letter prefixes to get bare option texts
    texts = [o.split(":", 1)[-1].strip() for o in opts]
    correct_idx = _LETTERS.index(current_letter)
    correct_text = texts[correct_idx]

    # Pick a new random position for the correct answer
    new_correct_idx = random.randrange(len(_LETTERS))
    # Rotate by swapping
    texts[correct_idx], texts[new_correct_idx] = texts[new_correct_idx], texts[correct_idx]

    new_opts = [f"{_LETTERS[i]}: {texts[i]}" for i in range(len(_LETTERS))]
    new_answer = _LETTERS[new_correct_idx]

    return {**q, "options": new_opts, "answer": new_answer}


def _extract_json(text: str) -> dict | None:
    """Extract the first valid JSON object containing 'questions' from raw text."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{[\s\S]*?"questions"[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None