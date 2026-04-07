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

# Words so short they add no signal to overlap comparisons.
_STOP_WORDS: frozenset[str] = frozenset(
    "a an the is are was were be been of in on at to for and or but not"
    " it its this that these those with from by what which who how".split()
)
# Jaccard overlap above this value -> questions are considered too similar.
_OVERLAP_THRESHOLD = 0.40

_FEW_SHOT_EXAMPLE = """\
Here are two examples of GOOD questions for the topic "colours":
{
  "question": "What colour is the sky described as in the text?",
  "options": ["A: Red", "B: Blue", "C: Green", "D: Yellow"],
  "answer": "B"
}
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
        f"Create exactly {n} multiple-choice questions STRICTLY about the topic \"{topic}\". "
        f"Every question must test knowledge that appears in the study material below. "
        f"Do NOT write questions about any other topic.\n\n"
        "RULES:\n"
        f"1. Every question MUST be answerable using only the study material — quote or paraphrase a fact from it.\n"
        f"2. ALL {n} questions must be about \"{topic}\" — reject any question that is off-topic.\n"
        "3. Use a DIFFERENT question style for each question. Rotate among:\n"
        "   - Fact recall: 'What is [property] of [thing from text]?'\n"
        "   - Identification: 'Which of these is described as [descriptor from text]?'\n"
        "   - Fill-in-the-blank: 'Complete the sentence: \"[sentence from text with blank]\"'\n"
        "   - Usage: 'Which sentence uses [word from text] correctly?'\n"
        "   - Vocabulary: 'What does [specific adjective/descriptor from text] mean?'\n"
        "4. Every distractor must be UNAMBIGUOUSLY WRONG. If a distractor could also be\n"
        "   defended as correct, pick a different distractor or rewrite the question.\n"
        "   BAD EXAMPLE: Q='What does orange mean?' with options 'a fruit' and 'a colour'\n"
        "   — both are correct. Instead ask: 'What colour is described as both a fruit and a colour?'\n"
        "5. Each question must test a UNIQUE fact. After writing all questions, check:\n"
        "   does answering one reveal the answer to another? If yes, replace the duplicate.\n"
        "   BAD EXAMPLE: Q2='Which is a mix of red and blue?' (A: purple) and\n"
        "   Q3='Purple is a mix of ___' — Q2 gives away Q3. Remove one.\n"
        "6. Spread correct answers across A, B, C, D — do not cluster on one letter.\n\n"
        f"{_FEW_SHOT_EXAMPLE}\n\n"
        f"Study material (topic: {topic}):\n{excerpt}\n\n"
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
    """Validate, deduplicate, check for cross-leakage, and shuffle answer positions."""
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

        # Deduplicate by exact question text
        key = text.lower()
        if key in seen_questions:
            continue
        seen_questions.add(key)

        # Deduplicate by identical option set
        opt_values = frozenset(o.split(":", 1)[-1].strip().lower() for o in opts)
        if opt_values in seen_option_sets:
            continue
        seen_option_sets.append(opt_values)

        # Cross-question quality checks against already-accepted questions
        if _leaks_answer(q, valid) or _too_similar_to_any(q, valid):
            continue

        valid.append(_shuffle_answer(q))

    return valid


def _content_words(text: str) -> frozenset[str]:
    """Return lowercase content words, stripping stop words and punctuation."""
    tokens = re.sub(r"[^\w\s]", " ", text.lower()).split()
    return frozenset(t for t in tokens if t not in _STOP_WORDS and len(t) > 1)


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _leaks_answer(candidate: dict, accepted: list[dict]) -> bool:
    """Return True if this question's correct answer text appears in another
    question's body (or vice-versa), meaning one reveals the answer to the other.
    """
    ans_idx = _LETTERS.index(candidate["answer"])
    cand_answer = candidate["options"][ans_idx].split(":", 1)[-1].strip().lower()
    cand_q_lower = candidate["question"].lower()

    for acc in accepted:
        acc_ans_idx = _LETTERS.index(acc["answer"])
        acc_answer = acc["options"][acc_ans_idx].split(":", 1)[-1].strip().lower()
        acc_q_lower = acc["question"].lower()

        # Accepted answer appears in candidate question text
        if acc_answer and len(acc_answer) > 2 and acc_answer in cand_q_lower:
            return True
        # Candidate answer appears in accepted question text
        if cand_answer and len(cand_answer) > 2 and cand_answer in acc_q_lower:
            return True
    return False


def _too_similar_to_any(candidate: dict, accepted: list[dict]) -> bool:
    """Return True if the candidate overlaps too much with any accepted question
    (same underlying fact tested in different phrasing).
    """
    ans_idx = _LETTERS.index(candidate["answer"])
    cand_answer = candidate["options"][ans_idx].split(":", 1)[-1].strip()
    cand_words = _content_words(candidate["question"] + " " + cand_answer)

    for acc in accepted:
        acc_ans_idx = _LETTERS.index(acc["answer"])
        acc_answer = acc["options"][acc_ans_idx].split(":", 1)[-1].strip()
        acc_words = _content_words(acc["question"] + " " + acc_answer)
        if _jaccard(cand_words, acc_words) >= _OVERLAP_THRESHOLD:
            return True
    return False


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