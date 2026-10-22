"""Teacher node: write multiple-choice quizzes with an instruction-tuned model."""
from __future__ import annotations

import json
import logging
import random
import re
import unicodedata

import torch
from transformers import PreTrainedModel, PreTrainedTokenizerBase

from ...tools.create_quiz import create_quiz as create_quiz_tool
from .state import TeacherState

_LETTERS = ["A", "B", "C", "D"]
_MATERIAL_WORD_LIMIT = 1200
_MAX_ATTEMPTS = 3
_TOKENS_PER_QUESTION = 110
_MAX_TOPIC_CHARACTERS = 120
# Jaccard overlap at or above this value means two questions test the same fact.
_OVERLAP_THRESHOLD = 0.25
# At least this share of the correct answer's words must appear in the source text.
_ANSWER_SUPPORT_RATIO = 0.5

# Words so short they add no signal to overlap comparisons.
_STOP_WORDS: frozenset[str] = frozenset(
    "a an the is are was were be been of in on at to for and or but not"
    " it its this that these those with from by what which who how".split()
)
# Words in a topic that say nothing about which part of the material is relevant.
_GENERIC_TOPIC_WORDS: frozenset[str] = frozenset(
    "question questions practice example examples chapter material topic lesson"
    " which what where when who why how general knowledge class unit english".split()
)
# Options that depend on their position break once the options are shuffled.
_POSITIONAL_OPTION = re.compile(r"\b(?:all|none|both)\s+of\s+the\s+above\b|\bboth\s+[a-d]\s+and\s+[a-d]\b", re.I)
_PASSAGE_SEPARATOR = "\n\n---\n\n"
# This adult course contains examples unsuitable for elementary school pupils.
# Screen source selection and generated text, in addition to the model review.
_ADULT_CONTENT = re.compile(r"\b(?:sexy|porn\w*|erotic\w*|prostitut\w*|sexual\w*)\b", re.I)
logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a careful teacher who writes multiple-choice quiz questions for school students "
    "in elementary school. Use simple, clear language. Reply with JSON only."
)
_FORMAT_PROMPT = (
    'Return JSON only, in exactly this shape: {"questions": [{"question": "...", '
    '"options": ["...", "...", "...", "..."], "answer": "B"}]} where "answer" is the letter '
    "(A, B, C or D) of the one correct option."
)


def teacher_llm_call(
    state: TeacherState,
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    max_new_tokens: int,
    temperature: float,
) -> dict:
    """Generate a quiz from the supplied material, or from the model's own knowledge."""
    llm_calls = state.get("llm_calls", 0)
    topic = _clean_topic(state.get("topic", ""))
    n = max(1, int(state.get("question_count", 5)))
    material = state.get("learning_material", "").strip()
    practice = state.get("language_practice", False)
    guidance = state.get("teaching_guidance", "").strip()

    if material:
        sentences = _practice_sentences(material) if practice else []
        source = "\n".join(sentences) if sentences else _select_material_excerpt(material, topic, _MATERIAL_WORD_LIMIT)
    elif state.get("use_model_knowledge"):
        source = ""
    else:
        return {"llm_calls": llm_calls, "error": "No study material available for this topic."}

    guidance = _select_material_excerpt(guidance, topic, 400) if guidance else ""
    questions: list[dict] = []
    rejected: list[str] = []
    for attempt in range(_MAX_ATTEMPTS):
        missing = n - len(questions)
        if missing <= 0:
            break
        messages = _build_messages(
            topic, source, missing, [q["question"] for q in questions] + rejected,
            language_practice=practice, teaching_guidance=guidance,
            required_skills=(
                [skill for skill in ("grammar", "vocabulary", "reading")
                 if not any(q.get("skill") == skill for q in questions)]
                if practice and n >= 3 else None
            ),
        )
        raw = _run_chat(
            model,
            tokenizer,
            messages,
            max_new_tokens=max(max_new_tokens, (220 if practice else _TOKENS_PER_QUESTION) * missing + 100),
            temperature=temperature,
        )
        llm_calls += 1
        logger.debug("Quiz attempt %s output: %s", attempt + 1, raw)
        pending: list[dict] = []
        candidates = _parse_questions(raw)
        for candidate in candidates:
            if len(questions) + len(pending) >= n:
                break
            item = _build_item(candidate, source, questions + pending, language_practice=practice)
            if item is not None:
                pending.append(item)
            elif isinstance(candidate.get("question"), str):
                rejected.append(candidate["question"])
        if practice and pending:
            review = _run_chat(
                model, tokenizer, _review_messages(pending),
                max_new_tokens=100 + 100 * len(pending), temperature=0.0,
            )
            llm_calls += 1
            valid = _reviewed_ids(review, pending)
            logger.debug("Quiz review output: %s", review)
            for index, item in enumerate(pending):
                if index in valid:
                    questions.append(item)
                else:
                    rejected.append(item["question"])
        else:
            questions.extend(pending)
        logger.info(
            "Quiz attempt %s: parsed=%s, structurally_valid=%s, accepted_total=%s/%s",
            attempt + 1, len(candidates), len(pending), len(questions), n,
        )

    if not questions:
        return {
            "llm_calls": llm_calls,
            "error": "Could not build a valid multiple-choice quiz from the study material."
            if source
            else "Could not build a valid multiple-choice quiz on this topic.",
        }

    if state.get("require_full_count") and len(questions) < n:
        return {
            "llm_calls": llm_calls,
            "error": f"Only {len(questions)} of {n} questions passed the learning checks. Please try again or choose another unit.",
        }

    quiz_title = f"English Quiz: {topic}"
    quiz_data = {"quiz_title": quiz_title, "questions": questions}
    if len(questions) < n:
        quiz_data["shortfall"] = n - len(questions)

    save_result = create_quiz_tool.invoke({"quiz_title": quiz_title, "questions": questions})
    if isinstance(save_result, str) and save_result.startswith("ERROR:"):
        return {"llm_calls": llm_calls, "error": save_result}

    return {"quiz": quiz_data, "llm_calls": llm_calls}


def _clean_topic(topic: str) -> str:
    return re.sub(r"\s+", " ", topic).strip()[:_MAX_TOPIC_CHARACTERS] or "general"


def _build_messages(
    topic: str, source: str, count: int, avoid: list[str],
    language_practice: bool = False, teaching_guidance: str = "",
    required_skills: list[str] | None = None,
) -> list[dict]:
    if language_practice:
        sentences = _practice_sentences(source)
        examples = _practice_examples(sentences, 1, avoid) if not required_skills or "grammar" in required_skills else []
        student_text = "\n".join(sentences) or source
        notes = (
            "Teacher context, for choosing teaching methods only (never quote this as student evidence):\n"
            + _limit_material_words(teaching_guidance, 80) + "\n\n"
        ) if teaching_guidance else ""
        prompt = notes + (
            f"Write {count} different English practice questions for children. Topic: {topic}.\n"
            "Use the STUDENT EXAMPLES below. Include a mix of grammar, vocabulary meaning, and short reading comprehension when the examples support it. "
            "For a grammar question, copy a complete example sentence and replace one word with ___. "
            "State the tense when necessary. For vocabulary, ask what a word means in its sentence. "
            "Give three clearly incorrect alternatives. "
            "Each question has exactly FOUR options and one correct answer letter A, B, C, or D. "
            "For source_quote, copy exactly ONE complete student example (at most 22 words), not a paragraph. "
            "Keep the question under 40 words and each option under 12 words. "
            "Do not ask about teachers, pictures, recordings, or memorising the characters' names. "
            "A reading question must contain its short passage.\n"
            'Return a JSON object with a questions array. Each question has question, options, answer, skill, and source_quote. '
            'The skill must be exactly "grammar", "vocabulary", or "reading".\n'
            f"STUDENT EXAMPLES:\n{student_text}\n"
        )
        if examples:
            prompt += (
                "This is one complete grammar example showing the JSON format. "
                "Create the requested number of exercises, including other skills when suitable:\n"
                + json.dumps({"questions": examples}, ensure_ascii=False) + "\n"
            )
        if not source:
            prompt += "No source was supplied. Use basic English grammar and vocabulary; omit source_quote.\n"
        if avoid:
            prompt += "\nDo not repeat these questions:\n" + "\n".join(avoid[-10:])
        prompt += "\nReturn only the questions JSON. Use the student examples above for every source_quote."
        if count >= 3:
            prompt += " Include at least one grammar question, one vocabulary-meaning question, and one reading question."
        if required_skills:
            prompt += " The skills still needed are: " + ", ".join(required_skills) + ". Focus on these skills."
        return [{"role": "system", "content": _SYSTEM_PROMPT}, {"role": "user", "content": prompt}]

    rules = [
        "Give exactly 4 options. Exactly one is correct and the other three are plausible but clearly wrong.",
        "Do not write the letters A-D inside the question or the options.",
        "Never reveal one question's answer inside another question.",
    ]
    if source:
        task = f'Write {count} multiple-choice questions about "{topic}" using ONLY the source text below.'
        rules.insert(0, "Every question must be answerable from the source text alone; never use outside facts.")
        rules.append("Ignore headings, page numbers and exercise instructions in the source text.")
    else:
        task = f'Write {count} multiple-choice questions about "{topic}" from your own knowledge.'
        rules.insert(0, "Only ask about widely taught facts that you are certain are correct.")
    if avoid:
        rules.append("Do not repeat or rephrase these existing questions: " + " | ".join(avoid))

    prompt = "\n".join([task, "Rules:", *(f"- {rule}" for rule in rules), _FORMAT_PROMPT])
    if source:
        prompt += f'\n\nSource text:\n"""\n{source}\n"""'
    if teaching_guidance:
        prompt += f'\n\nTEACHER GUIDANCE (pedagogy only, not student source):\n"""\n{teaching_guidance}\n"""'
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]


def _practice_sentences(source: str) -> list[str]:
    """Find complete learner examples in PDF text, leaving out headings and tasks.

    This is a small text cleanup step, not a model-generated summary: every
    returned example remains a verbatim substring after whitespace normalisation.
    """
    text = re.sub(r"\s+", " ", source)
    start = re.compile(r"\b(?:I|You|He|She|It|We|They|This|That|There|My|Your|His|Her|Our|Their)\b")
    sentences: list[str] = []
    for fragment in re.findall(r"[^.!?]+\.", text):
        match = start.search(fragment)
        if not match:
            continue
        sentence = fragment[match.start():].strip()
        if not 3 <= len(sentence.split()) <= 22 or "_" in sentence or _ADULT_CONTENT.search(sentence):
            continue
        if re.search(r"\b(?:audio|picture|listen|repeat|partner|exercise|question|answer|complete|table)\b|\bpage\s+\d|\bThis unit\b|\bWe use\b", sentence, re.I):
            continue
        # PDF list numbers can become the final word of an otherwise good example.
        # Keep real times ("at 8.") but omit these fragments and broken decimals.
        if "/" in sentence or re.search(r"(?<!at)(?<!about)(?<!until)(?<!before)(?<!after) \d+\.$", sentence):
            continue
        if sentence not in sentences:
            sentences.append(sentence)
    return sentences[:24]


def _practice_examples(sentences: list[str], count: int = 3, avoid: list[str] | None = None) -> list[dict]:
    """Scaffold the small model with real, source-grounded grammar examples."""
    examples: list[dict] = []
    seen_verbs: set[str] = set()
    for quote in random.sample(sentences, len(sentences)):
        expanded = re.sub(r"\b(I)['’]m\b", r"\1 am", quote)
        expanded = re.sub(r"\b(He|She|It)['’]s\b", r"\1 is", expanded)
        expanded = re.sub(r"\b(You|We|They)['’]re\b", r"\1 are", expanded)
        match = re.search(r"\b(?:I am|You are|He is|She is|It is|We are|They are)\b", expanded)
        if not match:
            continue
        verb = match.group().split()[-1]
        start = match.end() - len(verb)
        blank = expanded[:start] + "___" + expanded[match.end():]
        item = {
            "question": f"Complete (present tense): {blank}",
            "options": ["am", "is", "are", "be"],
            "answer": _LETTERS[["am", "is", "are", "be"].index(verb)],
            "skill": "grammar", "source_quote": quote,
        }
        if any(_normalise(item["question"]) == _normalise(previous) for previous in avoid or []):
            continue
        if verb not in seen_verbs:
            examples.insert(0, item)
            seen_verbs.add(verb)
        else:
            examples.append(item)
    return examples[:count]


def _run_chat(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    messages: list[dict],
    max_new_tokens: int,
    temperature: float,
) -> str:
    """Run one chat completion and return only the newly generated text."""
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    generate_kwargs: dict = {
        "max_new_tokens": max_new_tokens,
        "pad_token_id": tokenizer.pad_token_id
        if tokenizer.pad_token_id is not None
        else tokenizer.eos_token_id,
    }
    if temperature > 0:
        generate_kwargs.update(do_sample=True, temperature=temperature, top_p=0.9)
    else:
        generate_kwargs["do_sample"] = False

    with torch.no_grad():
        output = model.generate(**inputs, **generate_kwargs)
    new_tokens = output[0][inputs["input_ids"].shape[1] :]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def _parse_questions(text: str) -> list[dict]:
    """Pull question objects out of model output, tolerating fences and truncation."""
    decoder = json.JSONDecoder()
    found: list[dict] = []
    index = text.find("{")
    while index != -1:
        try:
            value, end = decoder.raw_decode(text, index)
        except json.JSONDecodeError:
            index = text.find("{", index + 1)
            continue
        if isinstance(value, dict) and isinstance(value.get("questions"), list):
            found.extend(q for q in value["questions"] if isinstance(q, dict))
        elif isinstance(value, dict) and "question" in value:
            found.append(value)
        index = text.find("{", end)
    return found


def _build_item(
    candidate: dict, source: str, accepted: list[dict], language_practice: bool = False,
) -> dict | None:
    """Validate one model question and return it with shuffled options, or None."""
    question = candidate.get("question")
    options = candidate.get("options")
    if not isinstance(question, str) or not isinstance(options, list) or len(options) != 4:
        return None

    if not all(isinstance(option, str) for option in options):
        return None
    texts = [_strip_option_label(option) for option in options]
    correct = _correct_index(candidate.get("answer"), texts)
    question = re.sub(r"\s+", " ", question).strip()
    if correct is None or not _is_acceptable_question_text(question):
        return None
    if not _is_acceptable_options(texts):
        return None
    if language_practice and _ADULT_CONTENT.search(" ".join([question, *texts, str(candidate.get("source_quote", ""))])):
        return None
    if language_practice and source:
        quote = candidate.get("source_quote")
        if not isinstance(quote, str) or not 3 <= len(quote.split()) <= 30:
            return None
        if not _quote_supported(quote, source):
            return None
        blank = re.search(r"_{2,}", question)
        if blank:
            if len(re.findall(r"_{2,}", question)) != 1 or ":" not in question:
                return None
            sentence = question.split(":", 1)[1].strip(" \"'“”")
            matching = [
                index for index, option in enumerate(texts)
                if _expanded_sentence(re.sub(r"_{2,}", lambda _: option, sentence))
                == _expanded_sentence(quote)
            ]
            if len(matching) != 1:
                return None
            # The completed source sentence establishes the answer independently
            # of an unreliable model-generated letter.
            correct = matching[0]
        elif question.casefold().startswith("complete"):
            return None
        if not blank and _practice_skill(candidate.get("skill")) in ("vocabulary", "reading") and not _quote_supported(quote, question):
            # Supply the verified reading context rather than requiring pupils
            # to remember an unseen textbook dialogue or picture.
            question = f'Read: "{quote}" {question}'
            if not _is_acceptable_question_text(question):
                return None
    elif source and not _answer_supported(texts[correct], source):
        return None

    answer_lower = texts[correct].lower()
    for existing in accepted:
        if _normalise(existing["question"]) == _normalise(question):
            return None
        if not language_practice and _answer_text(existing).lower() == answer_lower:
            return None

    order = list(range(4))
    random.shuffle(order)
    item = {
        "question": question,
        "options": [f"{_LETTERS[slot]}: {texts[original]}" for slot, original in enumerate(order)],
        "answer": _LETTERS[order.index(correct)],
    }
    if language_practice:
        item["skill"] = _practice_skill(candidate.get("skill", "grammar"))
        if item["skill"] is None:
            return None
        if source:
            item["source_quote"] = candidate["source_quote"].strip()
    elif _leaks_answer(item, accepted) or _too_similar_to_any(item, accepted):
        return None
    return item


def _practice_skill(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return {
        "grammar": "grammar", "vocabulary": "vocabulary", "vocabulary meaning": "vocabulary",
        "vocabulary-meaning": "vocabulary", "reading": "reading", "reading comprehension": "reading",
    }.get(value.strip().casefold())


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text).strip().casefold()


def _quote_supported(quote: str, source: str) -> bool:
    quote = _normalise(quote)
    if not quote:
        return False
    start = r"(?<!\w)" if quote[0].isalnum() else ""
    end = r"(?!\w)" if quote[-1].isalnum() else ""
    return re.search(start + re.escape(quote) + end, _normalise(source)) is not None


def _expanded_sentence(text: str) -> str:
    text = _normalise(text)
    text = re.sub(r"\bi'm\b", "i am", text)
    text = re.sub(r"\b(he|she|it|there|name)'s\b", r"\1 is", text)
    text = re.sub(r"\b(you|we|they)'re\b", r"\1 are", text)
    return text.rstrip(".!? \"'")


def _review_messages(items: list[dict]) -> list[dict]:
    return [
        {"role": "system", "content": "You check English exercises for elementary school pupils. Reply with JSON only."},
        {"role": "user", "content": (
            "Check each exercise independently. valid is true ONLY if there is exactly one grammatically and "
            "semantically correct option, and the question practises English "
            "grammar, vocabulary or reading. For a source_quote, the exercise must be supported by that quote. "
            "A reading question must include its passage. Reject questions needing audio, an unseen picture, "
            "another exercise, or teacher instructions. Reject inappropriate topics for children. "
            "Solve it yourself. No proposed answer is supplied. Do not choose the closest option if all are wrong. "
            "If no option is correct, return valid false and answer null. "
            "Distinguish a word's meaning from facts that might happen to be true of a speaker. "
            "Give your independently determined correct answer letter in answer. "
            'Return {"checks":[{"id":0,"valid":true,"answer":"B"}]} with one check per exercise.\n'
            + json.dumps([{"id": i, **{key: value for key, value in item.items() if key != "answer"}}
                          for i, item in enumerate(items)], ensure_ascii=False)
        )},
    ]


def _reviewed_ids(raw: str, items: list[dict]) -> set[int]:
    """Fail closed on malformed, missing, conflicting, or mismatched reviews."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", raw):
        try:
            payload, _ = decoder.raw_decode(raw, match.start())
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("checks"), list):
            continue
        checks: dict[int, list[dict]] = {}
        for check in payload["checks"]:
            if isinstance(check, dict) and type(check.get("id")) is int:
                checks.setdefault(check["id"], []).append(check)
        return {
            index for index, reviews in checks.items()
            if 0 <= index < len(items) and len(reviews) == 1
            and reviews[0].get("valid") is True
            and reviews[0].get("answer") == items[index]["answer"]
        }
    return set()


def _strip_option_label(text: str) -> str:
    return re.sub(r"^\s*(?:\(?[A-Da-d]\)|[A-Da-d][.:])\s+", "", text).strip()


def _correct_index(answer: object, texts: list[str]) -> int | None:
    """Resolve the model's answer (a letter or the option text) to an option index."""
    if not isinstance(answer, str):
        return None
    cleaned = answer.strip()
    letter = re.fullmatch(r"\(?([A-Da-d])[).:]?", cleaned)
    if letter:
        return _LETTERS.index(letter.group(1).upper())
    matches = [i for i, text in enumerate(texts) if text.lower() == cleaned.lower()]
    return matches[0] if len(matches) == 1 else None


def _is_acceptable_question_text(text: str) -> bool:
    return 4 <= len(text.split()) <= 60


def _is_acceptable_options(texts: list[str]) -> bool:
    """Options must be present, short, distinct and independent of their position."""
    if len(texts) != 4 or len({t.lower() for t in texts}) != 4:
        return False
    for text in texts:
        if not 1 <= len(text.split()) <= 20 or re.search(r"={3,}", text):
            return False
        if _POSITIONAL_OPTION.search(text):
            return False
    return True


def _answer_text(item: dict) -> str:
    return item["options"][_LETTERS.index(item["answer"])].split(":", 1)[-1].strip()


def _answer_supported(answer: str, source: str) -> bool:
    """True when most of the answer's content words occur in the source text."""
    words = {_stem(w) for w in _content_words(answer)}
    if not words:
        return answer.strip().lower() in source.lower()
    source_words = {_stem(w) for w in _content_words(source)}
    return len(words & source_words) / len(words) >= _ANSWER_SUPPORT_RATIO


def _content_words(text: str) -> frozenset[str]:
    """Return lowercase content words, stripping stop words and punctuation."""
    tokens = re.sub(r"[^\w\s]", " ", text.lower()).split()
    return frozenset(t for t in tokens if t not in _STOP_WORDS and len(t) > 1)


def _stem(word: str) -> str:
    """Fold simple plurals so 'colours' matches 'colour'."""
    return word[:-1] if len(word) > 3 and word.endswith("s") else word


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _leaks_answer(candidate: dict, accepted: list[dict]) -> bool:
    """True if either question's correct answer appears in the other question's text."""
    cand_answer = _answer_text(candidate).lower()
    cand_question = candidate["question"].lower()

    for existing in accepted:
        existing_answer = _answer_text(existing).lower()
        existing_question = existing["question"].lower()
        if len(existing_answer) > 2 and existing_answer in cand_question:
            return True
        if len(cand_answer) > 2 and cand_answer in existing_question:
            return True
    return False


def _too_similar_to_any(candidate: dict, accepted: list[dict]) -> bool:
    """True if the candidate tests the same fact as an accepted question."""
    cand_words = _content_words(candidate["question"] + " " + _answer_text(candidate))
    return any(
        _jaccard(cand_words, _content_words(existing["question"] + " " + _answer_text(existing)))
        >= _OVERLAP_THRESHOLD
        for existing in accepted
    )


def _limit_material_words(material: str, word_limit: int) -> str:
    """Bound model context while retaining line boundaries."""
    lines: list[str] = []
    remaining = word_limit
    for line in material.splitlines():
        words = line.split()
        if not words:
            lines.append("")
            continue
        lines.append(" ".join(words[:remaining]))
        remaining -= min(len(words), remaining)
        if remaining <= 0:
            break
    return "\n".join(lines).strip()


def _split_blocks(material: str, max_words: int = 120) -> list[str]:
    """Split text into blank-line separated blocks, cutting overlong ones on line breaks."""
    blocks: list[str] = []
    current: list[str] = []
    count = 0
    for line in material.splitlines():
        if not line.strip():
            if current:
                blocks.append("\n".join(current))
            current, count = [], 0
            continue
        current.append(line.strip())
        count += len(line.split())
        if count >= max_words:
            blocks.append("\n".join(current))
            current, count = [], 0
    if current:
        blocks.append("\n".join(current))
    return blocks


def _select_material_excerpt(material: str, topic: str, word_limit: int) -> str:
    """Fit material into the word budget, keeping blocks that match the topic.

    Without any topic match, blocks are sampled evenly so later content is not dropped.
    """
    if len(material.split()) <= word_limit:
        return _limit_material_words(material, word_limit)

    if _PASSAGE_SEPARATOR in material:
        blocks = [p.strip() for p in material.split(_PASSAGE_SEPARATOR) if p.strip()]
        joiner = _PASSAGE_SEPARATOR
    else:
        blocks = _split_blocks(material)
        joiner = "\n\n"

    topic_words = {_stem(w) for w in _content_words(topic) - _GENERIC_TOPIC_WORDS}
    scores = [len(topic_words & {_stem(w) for w in _content_words(block)}) for block in blocks]
    if any(scores):
        order = sorted(range(len(blocks)), key=lambda i: (-scores[i], i))
    else:
        average = max(1, len(material.split()) // len(blocks))
        wanted = max(1, word_limit // average)
        spread = list(dict.fromkeys(min(len(blocks) - 1, j * len(blocks) // wanted) for j in range(wanted)))
        order = spread + [i for i in range(len(blocks)) if i not in spread]

    chosen: list[int] = []
    remaining = word_limit
    for index in order:
        size = len(blocks[index].split())
        if chosen and size > remaining:
            continue
        chosen.append(index)
        remaining -= size
        if remaining <= 0:
            break

    excerpt = joiner.join(blocks[i] for i in sorted(chosen))
    return _limit_material_words(excerpt, word_limit)
