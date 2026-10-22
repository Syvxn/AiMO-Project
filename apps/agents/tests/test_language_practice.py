import json

from aimo_agents.agents.teacher import nodes


SOURCE = "She is from Australia. He is from England. They are from India."


def exercise(sentence, quote, answer="A"):
    return {"question": f"Complete the sentence: {sentence}", "options": ["is", "am", "are", "be"],
            "answer": answer, "source_quote": quote, "skill": "grammar"}


def test_grammar_exercises_can_share_correct_words():
    first = nodes._build_item(exercise("She ___ from Australia.", "She is from Australia."), SOURCE, [], True)
    second = nodes._build_item(exercise("He ___ from England.", "He is from England."), SOURCE, [first], True)
    assert first and second
    assert nodes._answer_text(first) == nodes._answer_text(second) == "is"
    assert nodes._build_item(exercise("She ___ from Australia.", "She is from Australia."), SOURCE, [first], True) is None


def test_practice_requires_real_student_evidence():
    candidate = exercise("She ___ from France.", "She is from France.")
    assert nodes._build_item(candidate, SOURCE, [], True) is None
    candidate["source_quote"] = ""
    assert nodes._build_item(candidate, SOURCE, [], True) is None
    # Teacher notes cannot establish support when absent from student text.
    candidate["source_quote"] = "Play audio and drill the questions."
    assert nodes._build_item(candidate, SOURCE, [], True) is None


def test_cloze_answer_is_derived_from_the_source_not_the_model_letter():
    candidate = exercise("She ___ from Australia.", "She is from Australia.", answer="D")
    question = nodes._build_item(candidate, SOURCE, [], True)
    assert nodes._answer_text(question) == "is"
    candidate["question"] = "Complete: They ___ from Australia."
    assert nodes._build_item(candidate, SOURCE, [], True) is None


def test_cloze_contractions_match_the_actual_source():
    candidate = exercise("She ___ from Australia.", "She’s from Australia.")
    question = nodes._build_item(candidate, "She’s from Australia.", [], True)
    assert question is not None
    assert nodes._answer_text(question) == "is"


def test_quote_support_does_not_match_inside_a_different_word():
    assert not nodes._quote_supported("He is from Australia.", "She is from Australia.")
    assert not nodes._quote_supported("India", "Indian")
    assert nodes._quote_supported("She’s from Australia.", "[PDF page 25]\nShe's from\nAustralia. Hi.")


def test_reading_exercise_supplies_its_verified_passage():
    candidate = {"question": "Where is the speaker from?", "options": ["Australia", "India", "England", "France"],
                 "answer": "A", "skill": "reading", "source_quote": "I am from Australia."}
    result = nodes._build_item(candidate, "I am from Australia.", [], True)
    assert result["question"] == 'Read: "I am from Australia." Where is the speaker from?'
    assert nodes._answer_text(result) == "Australia"
    assert nodes._build_item(candidate, "I am from Australia.", [result], True) is None


def test_worked_examples_are_grounded_and_can_repeat_a_correct_word():
    sentences = ["She is from Australia.", "He is from England.", "She is a student."]
    examples = nodes._practice_examples(sentences, 3)
    assert len(examples) == 3
    assert all(item["source_quote"] in sentences for item in examples)
    assert all(nodes._build_item(item, " ".join(sentences), [], True) for item in examples)


def test_common_skill_labels_keep_their_meaning_and_reading_context():
    candidate = {"question": "Where is the speaker from?", "options": ["Australia", "India", "England", "France"],
                 "answer": "A", "skill": "reading comprehension", "source_quote": "I am from Australia."}
    result = nodes._build_item(candidate, "I am from Australia.", [], True)
    assert result["skill"] == "reading"
    assert result["question"].startswith('Read: "I am from Australia."')
    assert nodes._practice_skill("vocabulary meaning") == "vocabulary"
    assert nodes._practice_skill("teacher instructions") is None


def test_source_cleanup_omits_audio_tasks_and_preserves_complete_examples():
    source = "Listen to the audio.\nShe’s from\nAustralia.\nI am Paul Smith.\nHe is in the picture."
    assert nodes._practice_sentences(source) == ["She’s from Australia.", "I am Paul Smith."]


def test_source_cleanup_omits_pdf_list_numbers_and_exercise_choices():
    source = "He’s a teacher 2. This unit 1. We use there is/are with singular nouns. I start work at 8."
    assert nodes._practice_sentences(source) == ["I start work at 8."]


def test_vocabulary_cloze_does_not_reveal_the_missing_word():
    candidate = {"question": "Complete: She works at a ___ .", "options": ["hospital", "school", "shop", "farm"],
                 "answer": "A", "skill": "vocabulary", "source_quote": "She works at a hospital ."}
    result = nodes._build_item(candidate, candidate["source_quote"], [], True)
    assert result["question"] == candidate["question"]
    assert "hospital" not in result["question"]


def test_review_fails_closed_for_wrong_answers_missing_checks_and_conflicts():
    items = [{"answer": "A"}, {"answer": "B"}]
    assert nodes._reviewed_ids('{"checks":[{"id":0,"valid":true,"answer":"C"}]}', items) == set()
    assert nodes._reviewed_ids("invalid JSON", items) == set()
    assert nodes._reviewed_ids('{"checks":[{"id":0,"valid":true,"answer":"A"}]}', items) == {0}
    assert nodes._reviewed_ids('{"checks":[{"id":0,"valid":true,"answer":"A"},{"id":0,"valid":false}]}', items) == set()


def test_adult_course_examples_are_excluded_from_child_practice():
    adult = "It is fast, sexy and black."
    assert nodes._practice_sentences(adult + " She is a student.") == ["She is a student."]
    assert nodes._build_item(exercise("It ___ fast, sexy and black.", adult), adult, [], True) is None
    candidate = exercise("She ___ a student.", "She is a student.")
    candidate["options"][3] = "sexy"
    assert nodes._build_item(candidate, "She is a student.", [], True) is None


def test_minigame_does_not_save_partial_quiz(monkeypatch):
    class Writer:
        def invoke(self, _payload):
            raise AssertionError("A partial minigame quiz must not be saved")

    monkeypatch.setattr(nodes, "create_quiz_tool", Writer())
    monkeypatch.setattr(nodes, "_run_chat", lambda *_a, **_kw: json.dumps({"questions": [
        {"question": "Where is she from in this passage?", "options": ["Australia", "France", "Italy", "Spain"], "answer": "A"}
    ]}))
    result = nodes.teacher_llm_call({"learning_material": SOURCE, "topic": "Countries", "question_count": 3,
                                   "require_full_count": True}, None, None, 128, 0)
    assert "Only 1 of 3" in result["error"]
    assert "quiz" not in result


def test_practice_generation_reviews_shuffled_answers_and_forwards_guidance(monkeypatch):
    prompts = []
    saved = []

    def chat(_model, _tokenizer, messages, **_kwargs):
        prompts.append(messages)
        if len(prompts) == 1:
            return json.dumps({"questions": [exercise("She ___ from Australia.", "She is from Australia.")]})
        reviewed_items = json.loads(messages[-1]["content"].split("\n", 1)[1])
        assert "answer" not in reviewed_items[0]
        answer = next(option[0] for option in reviewed_items[0]["options"] if option.endswith(": is"))
        return json.dumps({"checks": [{"id": 0, "valid": True, "answer": answer}]})

    class Writer:
        def invoke(self, payload):
            saved.append(payload)
            return "SUCCESS"

    monkeypatch.setattr(nodes, "_run_chat", chat)
    monkeypatch.setattr(nodes, "create_quiz_tool", Writer())
    result = nodes.teacher_llm_call({"learning_material": SOURCE, "teaching_guidance": "Practise personal pronouns.",
                                   "language_practice": True, "require_full_count": True,
                                   "topic": "Unit 1", "question_count": 1}, None, None, 128, 0)
    assert len(result["quiz"]["questions"]) == 1
    assert result["llm_calls"] == 2
    assert "Practise personal pronouns" in prompts[0][-1]["content"]
    assert saved
