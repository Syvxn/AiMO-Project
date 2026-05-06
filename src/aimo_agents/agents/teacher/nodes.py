"""Teacher node implementations."""
from __future__ import annotations

import random
import re

import torch
from transformers import PreTrainedModel, PreTrainedTokenizerBase

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
_OVERLAP_THRESHOLD = 0.25
_LOW_QUALITY_PATTERNS = [
    "what is the name of the person",
    "what is the name of the",
    "what is the name of",
    "what is the person",
]
_FALLBACK_QUESTION_STEMS = [
    "Complete the sentence from the {topic} material: {cloze}",
    "Choose the best word to fill the blank: {cloze}",
    "From the {topic} lesson text, which word fits the blank: {cloze}",
]
_FALLBACK_EXCLUDED_TERMS = {
    "question",
    "questions",
    "practice",
    "example",
    "examples",
    "chapter",
    "material",
    "topic",
    "lesson",
    "which",
    "what",
    "where",
    "when",
    "who",
    "why",
    "how",
}

def teacher_tool_node(state: TeacherState) -> dict:
    """Retrieve learning material via RAG for the requested topic."""
    topic = state.get("topic", "general")
    # Use "chapter <topic>" as the chapter arg so the query is more specific
    # and avoids drifting into unrelated chapters that mention the word incidentally.
    material = retrieve_material_tool.invoke({"chapter": f"chapter {topic}", "topic": topic})
    return {"learning_material": material}


def teacher_llm_call(
    state: TeacherState,
    qa_model: PreTrainedModel,
    qa_tokenizer: PreTrainedTokenizerBase,
    distractor_model: PreTrainedModel,
    distractor_tokenizer: PreTrainedTokenizerBase,
    max_new_tokens: int,
    temperature: float,
) -> dict:
    """Generate quiz questions from retrieved material and save them."""
    material = state.get("learning_material", "")
    topic = state.get("topic", "English")
    n = state.get("question_count", 5)
    llm_calls = state.get("llm_calls", 0)

    if not material.strip() or material.startswith("No material found for chapter"):
        return {
            "llm_calls": llm_calls,
            "error": "No study material available for this topic.",
        }

    # Limit to ~1 200 words for model context constraints.
    excerpt = " ".join(material.split()[:1200])

    passages = _split_passages(excerpt)
    if not passages:
        passages = [excerpt]

    drafted_questions: list[dict] = []
    attempts = 0
    max_attempts = max(n * 8, 40)
    while len(drafted_questions) < n and attempts < max_attempts:
        context = passages[attempts % len(passages)]
        qa_text = _generate_qa(
            context=context,
            model=qa_model,
            tokenizer=qa_tokenizer,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )
        llm_calls += 1
        parsed_qa = _parse_qa(qa_text, qa_tokenizer)
        attempts += 1
        if parsed_qa is None:
            continue

        question_text, answer_text = parsed_qa
        distractor_text = _generate_distractors(
            question=question_text,
            answer=answer_text,
            context=context,
            model=distractor_model,
            tokenizer=distractor_tokenizer,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )
        llm_calls += 1
        distractors = _parse_distractors(distractor_text, distractor_tokenizer)
        distractors = [d for d in distractors if d.strip().lower() != answer_text.strip().lower()]
        distractors = _unique_texts(distractors)
        if len(distractors) < 3:
            continue

        # Skip if we already have a question with the same correct answer
        answer_lower = answer_text.strip().lower()
        if any(
            q["options"][_LETTERS.index(q["answer"])].split(":", 1)[-1].strip().lower()
            == answer_lower
            for q in drafted_questions
        ):
            continue

        options = [answer_text] + distractors[:3]
        drafted_questions.append(
            {
                "question": question_text,
                "options": [f"{_LETTERS[i]}: {options[i]}" for i in range(4)],
                "answer": "A",
            }
        )

    questions = _postprocess(drafted_questions)
    # If strict quality filtering under-produces, keep unique drafted questions
    # as a fallback so quiz size is closer to the requested count.
    if len(questions) < n:
        questions = _fill_with_unique_drafts(questions, drafted_questions, target=n)

    if len(questions) < n:
        questions.extend(
            _build_material_based_questions(
                material=excerpt,
                topic=topic,
                target=n - len(questions),
                existing=questions,
            )
        )

    if len(questions) > n:
        questions = questions[:n]

    if not questions:
        return {
            "llm_calls": llm_calls,
            "error": "Could not build a valid multiple-choice quiz from the retrieved material.",
        }

    quiz_title = f"English Quiz: {topic}"

    save_result = create_quiz_tool.invoke(
        {"quiz_title": quiz_title, "questions": questions}
    )

    return {
        "quiz": save_result,
        "llm_calls": llm_calls,
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
        if not _is_acceptable_question_text(text):
            continue
        if not _is_acceptable_options(opts):
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
    # Pick a new random position for the correct answer
    new_correct_idx = random.randrange(len(_LETTERS))
    # Rotate by swapping
    texts[correct_idx], texts[new_correct_idx] = texts[new_correct_idx], texts[correct_idx]

    new_opts = [f"{_LETTERS[i]}: {texts[i]}" for i in range(len(_LETTERS))]
    new_answer = _LETTERS[new_correct_idx]

    return {**q, "options": new_opts, "answer": new_answer}


def _split_passages(text: str) -> list[str]:
    """Split retrieved material into passage candidates for QA generation."""
    parts = [p.strip() for p in text.split("\n\n---\n\n") if p.strip()]
    if parts:
        return parts
    sentences = _extract_sentences(text)
    if not sentences:
        return [text] if text.strip() else []

    chunks: list[str] = []
    step = 3
    size = 5
    for i in range(0, len(sentences), step):
        chunk = " ".join(sentences[i : i + size]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks or ([text] if text.strip() else [])


def _generate_qa(
    context: str,
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    max_new_tokens: int,
    temperature: float,
) -> str:
    """Generate one question+answer pair from a context passage."""
    return _run_seq2seq(
        input_text=context,
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
    )


def _generate_distractors(
    question: str,
    answer: str,
    context: str,
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    max_new_tokens: int,
    temperature: float,
) -> str:
    """Generate distractors in 'question <sep> answer <sep> context' format."""
    sep = tokenizer.sep_token or "<sep>"
    input_text = f"{question} {sep} {answer} {sep} {context}"
    return _run_seq2seq(
        input_text=input_text,
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
    )


def _run_seq2seq(
    input_text: str,
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    max_new_tokens: int,
    temperature: float,
) -> str:
    """Execute a seq2seq generation call and return raw decoded text."""
    inputs = tokenizer(
        input_text,
        return_tensors="pt",
        truncation=True,
    )

    try:
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
    except (StopIteration, RuntimeError):
        pass

    generate_kwargs: dict = {"max_new_tokens": max_new_tokens}
    # Always sample so repeated calls on the same passage produce different outputs.
    if temperature > 0:
        generate_kwargs["do_sample"] = True
        generate_kwargs["temperature"] = temperature
    else:
        # Fall back to greedy but add a small temperature to encourage variation.
        generate_kwargs["do_sample"] = True
        generate_kwargs["temperature"] = 0.7

    with torch.no_grad():
        outputs = model.generate(**inputs, **generate_kwargs)

    decoded = tokenizer.decode(outputs[0], skip_special_tokens=False)
    if tokenizer.pad_token:
        decoded = decoded.replace(tokenizer.pad_token, "")
    if tokenizer.eos_token:
        decoded = decoded.replace(tokenizer.eos_token, "")
    return decoded.strip()


def _parse_qa(text: str, tokenizer: PreTrainedTokenizerBase) -> tuple[str, str] | None:
    """Parse 'question <sep> answer' output from the QA model."""
    sep = tokenizer.sep_token
    if sep and sep in text:
        question, answer = text.split(sep, 1)
        question = question.strip()
        answer = answer.strip()
        if question and answer:
            return question, answer

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) >= 2:
        return lines[0], lines[1]

    q_pos = text.find("?")
    if q_pos != -1 and q_pos + 1 < len(text):
        question = text[: q_pos + 1].strip()
        answer = text[q_pos + 1 :].strip()
        if question and answer:
            return question, answer

    return None


def _parse_distractors(text: str, tokenizer: PreTrainedTokenizerBase) -> list[str]:
    """Parse distractor output into a list of answer strings."""
    sep = tokenizer.sep_token
    if sep and sep in text:
        return [chunk.strip() for chunk in text.split(sep) if chunk.strip()]

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) >= 3:
        return lines
    return [part.strip() for part in re.split(r"\s*;\s*", text) if part.strip()]


def _unique_texts(items: list[str]) -> list[str]:
    """Deduplicate strings while preserving order (case-insensitive)."""
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item.strip())
    return out


def _fill_with_unique_drafts(
    accepted: list[dict],
    drafts: list[dict],
    target: int,
) -> list[dict]:
    """Backfill quiz items from unique drafts when strict checks are too aggressive."""
    out = list(accepted)
    seen_questions = {q.get("question", "").strip().lower() for q in out}

    for q in drafts:
        if len(out) >= target:
            break
        question_text = q.get("question", "").strip().lower()
        opts = q.get("options", [])
        ans = q.get("answer", "")
        if not question_text or question_text in seen_questions:
            continue
        if len(opts) != 4 or ans not in _LETTERS:
            continue
        if not _is_acceptable_question_text(q.get("question", "")):
            continue
        if not _is_acceptable_options(opts):
            continue
        seen_questions.add(question_text)
        out.append(_shuffle_answer(q))

    return out


def _extract_sentences(material: str) -> list[str]:
    """Extract sentence-like facts from retrieved material."""
    clean_lines: list[str] = []
    for line in material.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.fullmatch(r"=+", stripped):
            continue
        if stripped.upper().startswith("CHAPTER "):
            continue
        clean_lines.append(stripped)

    normalized = re.sub(r"\s+", " ", " ".join(clean_lines))
    normalized = re.sub(r"\bCHAPTER\s+\d+\s*:\s*[A-Z\s]+", "", normalized, flags=re.IGNORECASE)
    pieces = re.split(r"(?<=[.!?])\s+", normalized)
    out: list[str] = []
    seen: set[str] = set()
    for piece in pieces:
        sentence = piece.strip().strip('"').strip("'")
        sentence = re.sub(r"[^A-Za-z0-9,;:'()/\-\s.?]", "", sentence)
        sentence = re.sub(r"\s+", " ", sentence).strip()
        words = sentence.split()
        if len(words) < 5 or len(words) > 22:
            continue
        if sentence.count(":") > 1:
            continue
        key = sentence.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(sentence)
    return out


def _build_material_based_questions(
    material: str,
    topic: str,
    target: int,
    existing: list[dict],
) -> list[dict]:
    """Generate deterministic fallback questions directly from material facts."""
    if target <= 0:
        return []

    sentences = sorted(_extract_sentences(material), key=lambda s: len(s.split()))
    if not sentences:
        return []

    word_pool: list[str] = []
    for sentence in sentences:
        for token in re.findall(r"[A-Za-z][A-Za-z\-']+", sentence):
            low = token.lower()
            if len(low) <= 3:
                continue
            if low in _STOP_WORDS or low in _FALLBACK_EXCLUDED_TERMS:
                continue
            if not low.replace("-", "").isalpha():
                continue
            word_pool.append(low)
    # Keep word pool diverse while preserving order.
    seen_words: set[str] = set()
    deduped_pool: list[str] = []
    for word in word_pool:
        if word in seen_words:
            continue
        seen_words.add(word)
        deduped_pool.append(word)
    replacement_pool = deduped_pool

    existing_q = {q.get("question", "").strip().lower() for q in existing}
    out: list[dict] = []

    for idx, sentence in enumerate(sentences):
        if len(out) >= target:
            break

        token = _pick_cloze_token(sentence)
        if token is None:
            continue
        answer = token
        cloze = re.sub(rf"\b{re.escape(token)}\b", "____", sentence, count=1)
        stem = _FALLBACK_QUESTION_STEMS[idx % len(_FALLBACK_QUESTION_STEMS)]
        question_text = stem.format(topic=topic, cloze=cloze).strip()
        if not question_text.endswith("?"):
            question_text = f"{question_text}?"
        variant_key = question_text.lower()
        if variant_key in existing_q:
            continue

        distractors = _pick_distractors(answer, replacement_pool, sentence)

        if len(distractors) < 3:
            continue

        options = [answer] + distractors
        draft = {
            "question": question_text,
            "options": [f"{_LETTERS[i]}: {options[i]}" for i in range(4)],
            "answer": "A",
        }
        shuffled = _shuffle_answer(draft)
        if _is_acceptable_options(shuffled["options"]):
            out.append(shuffled)
        existing_q.add(variant_key)

    return out


def _pick_cloze_token(sentence: str) -> str | None:
    """Select a meaningful token from a sentence for cloze-question fallback."""
    candidates = [
        t
        for t in re.findall(r"[A-Za-z][A-Za-z\-']+", sentence)
        if len(t) > 3 and t.lower() not in _STOP_WORDS and not t.isdigit()
    ]
    if not candidates:
        return None
    # Prefer content words from the middle of the sentence.
    start = max(0, len(candidates) // 3)
    end = max(start + 1, (2 * len(candidates)) // 3)
    middle = candidates[start:end]
    pool = middle or candidates
    return random.choice(pool)


def _pick_distractors(answer: str, pool: list[str], sentence: str) -> list[str]:
    """Pick plausible distractors with similar shape and topical vocabulary."""
    answer_lower = answer.lower()
    sentence_tokens = {
        t.lower()
        for t in re.findall(r"[A-Za-z][A-Za-z\-']+", sentence)
    }

    def _collect(max_len_delta: int, exclude_sentence_words: bool) -> list[str]:
        out: list[str] = []
        seen: set[str] = {answer_lower}
        for token in pool:
            low = token.lower()
            if low in seen:
                continue
            if low in _FALLBACK_EXCLUDED_TERMS:
                continue
            if exclude_sentence_words and low in sentence_tokens:
                continue
            if abs(len(token) - len(answer)) > max_len_delta:
                continue
            seen.add(low)
            out.append(token)
        return out

    candidates = _collect(max_len_delta=4, exclude_sentence_words=True)
    if len(candidates) < 3:
        candidates = _collect(max_len_delta=6, exclude_sentence_words=False)
    if len(candidates) < 3:
        return []

    random.shuffle(candidates)
    return candidates[:3]


def _is_acceptable_question_text(text: str) -> bool:
    """Reject obviously weak or malformed question text."""
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    if len(normalized.split()) < 5:
        return False
    if not normalized.endswith("?"):
        return False
    if any(pattern in normalized for pattern in _LOW_QUALITY_PATTERNS):
        return False
    return True


def _is_acceptable_options(options: list[str]) -> bool:
    """Ensure options are readable and meaningfully distinct."""
    if len(options) != 4:
        return False
    texts = [o.split(":", 1)[-1].strip() for o in options]
    lowered = [t.lower() for t in texts]
    if len(set(lowered)) != 4:
        return False
    for text in texts:
        words = text.split()
        if len(words) < 1 or len(words) > 20:
            return False
        if re.search(r"={3,}", text):
            return False
    return True