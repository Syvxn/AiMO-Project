"use client";

import { useEffect, useState } from "react";
import {
  BankChapter,
  BankQuestion,
  deleteBankQuestion,
  draftBankQuestions,
  getBankChapters,
  getBankQuestions,
  saveBankQuestion,
  saveBankJson,
} from "@/lib/api";

const inputClass = "mt-1 w-full rounded-md border border-accent-orange/30 px-3 py-2";

function questionJson(item: BankQuestion): string {
  const { question, options, answer, skill, source_quote } = item;
  return JSON.stringify({ question, options, answer, skill, source_quote }, null, 2);
}

function readQuestionJson(text: string, original: BankQuestion): BankQuestion {
  let value;
  try {
    value = JSON.parse(text);
  } catch {
    throw new Error("The JSON is not valid. Check commas, brackets and quotation marks.");
  }
  if (
    !value ||
    typeof value !== "object" ||
    Array.isArray(value) ||
    typeof value.question !== "string" ||
    typeof value.source_quote !== "string" ||
    !Array.isArray(value.options) ||
    value.options.length !== 4 ||
    !value.options.every((option: unknown) => typeof option === "string") ||
    !["A", "B", "C", "D"].includes(value.answer) ||
    !["grammar", "vocabulary", "reading"].includes(value.skill)
  ) {
    throw new Error(
      "Include question, four text options, answer (A–D), skill (grammar, vocabulary or reading), and source_quote.",
    );
  }
  // Identity and approval always come from the selected card and its save action.
  return {
    ...original,
    question: value.question,
    options: value.options,
    answer: value.answer,
    skill: value.skill,
    source_quote: value.source_quote,
  };
}

function QuestionEditor({
  initial,
  token,
  onSaved,
  onDeleted,
  onDirtyChange,
  locked,
}: {
  initial: BankQuestion;
  token: string;
  onSaved: (item: BankQuestion) => void;
  onDeleted: (id: number) => void;
  onDirtyChange: (id: number, dirty: boolean) => void;
  locked: boolean;
}) {
  const [item, setItem] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [jsonMode, setJsonMode] = useState(false);
  const [jsonText, setJsonText] = useState(() => questionJson(initial));

  function changeEditor(useJson: boolean) {
    setError("");
    try {
      if (useJson) setJsonText(questionJson(item));
      else setItem(readQuestionJson(jsonText, item));
      setJsonMode(useJson);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not read JSON");
    }
  }

  async function save(status: BankQuestion["status"]) {
    setBusy(true);
    onDirtyChange(initial.id, true);
    setError("");
    setNotice("");
    try {
      const edited = jsonMode ? readQuestionJson(jsonText, item) : item;
      const saved = await saveBankQuestion(token, { ...edited, status });
      setItem(saved);
      setJsonText(questionJson(saved));
      setNotice(
        status === "approved"
          ? "Approved and available in the minigame."
          : "Saved as a draft; unavailable to students.",
      );
      onSaved(saved);
      onDirtyChange(initial.id, false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save question");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!window.confirm("Delete this question from the bank?")) return;
    setBusy(true);
    setError("");
    try {
      await deleteBankQuestion(token, item.id);
      onDeleted(item.id);
      onDirtyChange(initial.id, false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete question");
    } finally {
      setBusy(false);
    }
  }

  return (
    <details open={!initial.id} className="space-y-3 rounded-md border border-accent-teal/30 p-4">
      <summary className="cursor-pointer text-sm text-accent-yellow">
        {initial.id ? `Question ${initial.id}` : "New question"} ·{" "}
        {initial.status === "approved" ? "Approved" : "Draft — needs review"} · {item.skill}
        <span className="mt-1 block truncate text-text-beige">
          {item.question || "Write a question"}
        </span>
      </summary>
      <fieldset
        disabled={busy || locked}
        className="space-y-3"
        onChange={() => onDirtyChange(initial.id, true)}
      >
        <div className="flex gap-3" role="group" aria-label="Question editor format">
          <button
            type="button"
            className="rounded-md border border-accent-teal/40 px-3 py-1 text-sm text-text-beige"
            aria-pressed={!jsonMode}
            onClick={() => changeEditor(false)}
            disabled={!jsonMode}
          >
            Form
          </button>
          <button
            type="button"
            className="rounded-md border border-accent-teal/40 px-3 py-1 text-sm text-text-beige"
            aria-pressed={jsonMode}
            onClick={() => changeEditor(true)}
            disabled={jsonMode}
          >
            JSON
          </button>
        </div>
        {jsonMode ? (
          <label className="block text-sm text-text-beige">
            Question JSON
            <textarea
              className={`${inputClass} font-mono`}
              rows={16}
              spellCheck={false}
              value={jsonText}
              onChange={(e) => setJsonText(e.target.value)}
            />
          </label>
        ) : (
          <>
            <label className="block text-sm text-text-beige">
              Skill
              <select
                className={inputClass}
                value={item.skill}
                onChange={(e) =>
                  setItem({ ...item, skill: e.target.value as BankQuestion["skill"] })
                }
              >
                <option value="grammar">Grammar</option>
                <option value="vocabulary">Vocabulary</option>
                <option value="reading">Reading</option>
              </select>
            </label>
            <label className="block text-sm text-text-beige">
              Question (include any passage students need)
              <textarea
                className={inputClass}
                rows={3}
                maxLength={500}
                value={item.question}
                onChange={(e) => setItem({ ...item, question: e.target.value })}
              />
            </label>
            <p className="text-sm text-text-beige">Choose the one correct answer:</p>
            {item.options.map((option, index) => (
              <div key={index} className="flex items-center gap-3">
                <label className="flex items-center gap-2 text-sm text-text-beige">
                  <input
                    type="radio"
                    name={`answer-${initial.id}`}
                    checked={item.answer === "ABCD"[index]}
                    aria-label={`Option ${"ABCD"[index]} is correct`}
                    onChange={() =>
                      setItem({ ...item, answer: "ABCD"[index] as BankQuestion["answer"] })
                    }
                  />
                  {"ABCD"[index]}
                </label>
                <input
                  className={inputClass}
                  aria-label={`Option ${"ABCD"[index]}`}
                  value={option}
                  maxLength={200}
                  onChange={(e) =>
                    setItem({
                      ...item,
                      options: item.options.map((value, i) =>
                        i === index ? e.target.value : value,
                      ),
                    })
                  }
                />
              </div>
            ))}
            <label className="block text-sm text-text-beige">
              Exact quotation from the student lesson (for your review)
              <textarea
                className={inputClass}
                rows={2}
                maxLength={1000}
                value={item.source_quote}
                onChange={(e) => setItem({ ...item, source_quote: e.target.value })}
              />
            </label>
          </>
        )}
        <div className="flex flex-wrap gap-3">
          <button type="button" className="btn-primary" onClick={() => save("approved")}>
            {busy ? "Saving..." : "Save and approve"}
          </button>
          <button
            type="button"
            className="rounded-md border border-accent-teal/40 px-3 py-2 text-sm text-text-beige"
            onClick={() => save("draft")}
          >
            Save as draft
          </button>
          {!!initial.id && (
            <button type="button" className="px-3 py-2 text-sm text-accent-yellow" onClick={remove}>
              Delete
            </button>
          )}
        </div>
      </fieldset>
      {error && (
        <p role="alert" className="text-sm text-accent-yellow">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="text-sm text-accent-green">
          {notice}
        </p>
      )}
    </details>
  );
}

export function QuestionBank({
  token,
  materialsVersion,
}: {
  token: string;
  materialsVersion: string;
}) {
  const [chapters, setChapters] = useState<BankChapter[]>([]);
  const [chapterId, setChapterId] = useState("");
  const [questions, setQuestions] = useState<BankQuestion[]>([]);
  const [questionCount, setQuestionCount] = useState(3);
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);
  const [drafting, setDrafting] = useState(false);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");

  const [jsonEditing, setJsonEditing] = useState(false);
  const [bankJsonText, setBankJsonText] = useState("");
  const [jsonSaving, setJsonSaving] = useState(false);
  const [jsonError, setJsonError] = useState("");
  const [editorVersion, setEditorVersion] = useState(0);
  const [dirtyIds, setDirtyIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    let active = true;
    getBankChapters(token)
      .then((result) => {
        if (!active) return;
        setChapters(result.chapters);
        setChapterId((previous) =>
          result.chapters.some((c) => c.chapter_id === previous)
            ? previous
            : result.chapters[0]?.chapter_id || "",
        );
      })
      .catch((err) => {
        if (active) setError(err.message);
      });
    return () => {
      active = false;
    };
  }, [token, materialsVersion]);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError("");
      setAdding(false);
      setQuestions([]);
      setNotice("");
      setJsonEditing(false);
      setBankJsonText("");
      setJsonError("");
      setDirtyIds(new Set());
      try {
        if (!chapterId) return;
        const result = await getBankQuestions(token, chapterId);
        if (active) {
          setQuestions(result.questions);
        }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Could not load questions");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [token, chapterId, materialsVersion]);

  async function draft(event: React.FormEvent) {
    event.preventDefault();
    if (!Number.isInteger(questionCount) || questionCount < 1 || questionCount > 10) {
      setError("Choose a whole number from 1 to 10.");
      return;
    }
    setDrafting(true);
    setError("");
    setNotice("");
    try {
      const result = await draftBankQuestions(token, chapterId, questionCount);
      setQuestions((previous) => [...previous, ...result.questions]);
      setNotice(
        `Prepared ${result.questions.length} of ${questionCount} requested drafts.${result.questions.length < questionCount ? " Some questions did not pass the checks; you can prepare more or add questions manually." : ""}`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not prepare drafts");
    } finally {
      setDrafting(false);
    }
  }

  function saved(item: BankQuestion) {
    setQuestions((previous) =>
      previous.some((q) => q.id === item.id)
        ? previous.map((q) => (q.id === item.id ? item : q))
        : [...previous, item],
    );
    setAdding(false);
  }

  function dirtyChanged(id: number, dirty: boolean) {
    setDirtyIds((previous) => {
      const next = new Set(previous);
      if (dirty) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  function editBankJson() {
    setBankJsonText(bankJson);
    setJsonEditing(true);
    setJsonError("");
    setNotice("");
  }

  async function saveJson(approveAll: boolean, fromEditor: boolean) {
    setJsonSaving(true);
    setJsonError("");
    setNotice("");
    try {
      let data;
      try {
        data = JSON.parse(fromEditor ? bankJsonText : bankJson);
      } catch {
        throw new Error("The JSON is not valid. Check commas, brackets and quotation marks.");
      }
      if (
        !data ||
        typeof data !== "object" ||
        Array.isArray(data) ||
        data.chapter_id !== chapterId ||
        !Array.isArray(data.questions)
      ) {
        throw new Error("Use an object containing this unit's chapter_id and a questions array.");
      }
      const result = await saveBankJson(token, data, approveAll);
      setQuestions(result.questions);
      setEditorVersion((previous) => previous + 1);
      setDirtyIds(new Set());
      setAdding(false);
      setJsonEditing(false);
      setBankJsonText("");
      setNotice(
        approveAll
          ? `Saved ${result.updated} updated and ${result.created} new questions. Approved all ${result.approved} submitted questions.`
          : `Saved ${result.updated} updated and ${result.created} new questions. New and changed questions are drafts; unchanged approvals are kept.`,
      );
    } catch (err) {
      setJsonError(err instanceof Error ? err.message : "Could not save bank JSON");
    } finally {
      setJsonSaving(false);
    }
  }

  const approved = questions.filter((q) => q.status === "approved").length;
  const materialId = chapterId.split(":")[0];
  const textbooks = [
    ...new Map(
      chapters.map((chapter) => [chapter.chapter_id.split(":")[0], chapter.material_title]),
    ).entries(),
  ];
  const unitChapters = chapters.filter(
    (chapter) => chapter.chapter_id.split(":")[0] === materialId,
  );
  const bankJson = JSON.stringify({ chapter_id: chapterId, questions }, null, 2);

  function downloadJson() {
    const url = URL.createObjectURL(
      new Blob([jsonEditing ? bankJsonText : bankJson], { type: "application/json" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = `question-bank-${chapterId.replace(/[^a-zA-Z0-9-]/g, "_")}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }
  const newQuestion: BankQuestion = {
    id: 0,
    chapter_id: chapterId,
    question: "",
    options: ["", "", "", ""],
    answer: "A",
    skill: "grammar",
    source_quote: "",
    status: "draft",
    reviewed_at: null,
  };

  return (
    <section className="card space-y-4">
      <h2 className="font-display text-2xl text-text-natural">Minigame Question Bank</h2>
      <p className="text-sm text-text-beige">
        AI drafts need your review. Check the language, correct answer, other choices and
        suitability for children before approving. Students only receive your approved questions.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block text-sm text-text-beige">
          Textbook
          <select
            className={inputClass}
            value={materialId}
            disabled={drafting || loading || jsonEditing || jsonSaving}
            onChange={(e) =>
              setChapterId(
                chapters.find((chapter) => chapter.chapter_id.startsWith(`${e.target.value}:`))
                  ?.chapter_id || "",
              )
            }
          >
            {!textbooks.length && <option value="">Upload material to get started</option>}
            {textbooks.map(([id, title]) => (
              <option key={id} value={id}>
                {title}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm text-text-beige">
          Unit / chapter
          <select
            className={inputClass}
            value={chapterId}
            disabled={drafting || loading || jsonEditing || jsonSaving}
            onChange={(e) => setChapterId(e.target.value)}
          >
            {!chapters.length && <option value="">Upload material to get started</option>}
            {unitChapters.map((chapter) => (
              <option key={chapter.chapter_id} value={chapter.chapter_id}>
                {chapter.title}
              </option>
            ))}
          </select>
        </label>
      </div>
      {chapterId && !loading && (
        <>
          <p className="text-sm text-accent-green">
            {approved} approved questions ·{" "}
            {approved >= 3
              ? "Ready for a three-question minigame"
              : `${3 - approved} more approvals needed for the minigame`}
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              className="rounded-md border border-accent-teal/40 px-3 py-2 text-sm text-text-beige"
              disabled={
                !questions.length ||
                approved === questions.length ||
                drafting ||
                jsonEditing ||
                jsonSaving ||
                dirtyIds.size > 0
              }
              onClick={() => saveJson(true, false)}
            >
              {jsonSaving ? "Saving..." : `Approve all ${questions.length} questions`}
            </button>
            <p className="text-sm text-text-beige">
              Approves the saved questions in this unit after your review.
            </p>
          </div>
          {dirtyIds.size > 0 && (
            <p className="text-sm text-accent-yellow">
              Save your question-card edits before using bank JSON or Approve all.
            </p>
          )}
          <form className="flex flex-wrap items-end gap-3" onSubmit={draft}>
            <label className="text-sm text-text-beige">
              Number of questions (1–10)
              <input
                type="number"
                min={1}
                max={10}
                step={1}
                required
                value={Number.isNaN(questionCount) ? "" : questionCount}
                disabled={drafting || jsonEditing || jsonSaving}
                className={`${inputClass} w-28`}
                onChange={(e) => setQuestionCount(e.target.valueAsNumber)}
              />
            </label>
            <button
              type="submit"
              className="btn-primary"
              disabled={drafting || jsonEditing || jsonSaving}
            >
              {drafting ? "Preparing drafts — this may take a few minutes..." : "Prepare AI drafts"}
            </button>
            <button
              type="button"
              className="rounded-md border border-accent-teal/40 px-3 py-2 text-sm text-text-beige"
              disabled={drafting || jsonEditing || jsonSaving}
              onClick={() => setAdding(true)}
            >
              Add a question manually
            </button>
          </form>
          {notice && (
            <p role="status" className="text-sm text-accent-green">
              {notice}
            </p>
          )}
          <details className="rounded-md border border-accent-teal/20 p-3">
            <summary className="cursor-pointer text-sm text-text-beige">
              View or edit this unit’s bank as JSON ({questions.length} questions)
            </summary>
            <p className="my-2 text-sm text-text-beige">
              Export this JSON for LLM review, then paste the revised JSON here. Keep existing IDs
              to update questions; omit the ID or use null for new questions. Questions left out are
              kept in the bank.
            </p>
            <p className="my-2 text-sm text-text-beige">Keep source_quote copied exactly from the student material; do not paraphrase quotations.</p>
            <p className="my-2 text-sm text-text-beige">
              Save JSON edits returns new or changed questions to drafts. Save and approve all
              explicitly approves every question included in the JSON. Status and review dates
              inside the JSON do not approve questions.
            </p>
            <label className="block text-sm text-text-beige">
              Bank JSON
              <textarea
                className={`${inputClass} font-mono`}
                rows={14}
                readOnly={!jsonEditing || jsonSaving}
                spellCheck={false}
                value={jsonEditing ? bankJsonText : bankJson}
                onChange={(e) => setBankJsonText(e.target.value)}
              />
            </label>
            <div className="mt-2 flex flex-wrap gap-3">
              {!jsonEditing ? (
                <button
                  type="button"
                  className="btn-primary"
                  disabled={drafting || jsonSaving || dirtyIds.size > 0}
                  onClick={editBankJson}
                >
                  Edit bank JSON
                </button>
              ) : (
                <>
                  <button
                    type="button"
                    className="btn-primary"
                    disabled={jsonSaving}
                    onClick={() => saveJson(false, true)}
                  >
                    Save JSON edits
                  </button>
                  <button
                    type="button"
                    className="rounded-md border border-accent-teal/40 px-3 py-2 text-sm text-text-beige"
                    disabled={jsonSaving}
                    onClick={() => saveJson(true, true)}
                  >
                    Save JSON and approve all
                  </button>
                  <button
                    type="button"
                    className="px-3 py-2 text-sm text-text-beige"
                    disabled={jsonSaving}
                    onClick={() => {
                      setJsonEditing(false);
                      setBankJsonText("");
                      setJsonError("");
                    }}
                  >
                    Cancel JSON edits
                  </button>
                </>
              )}
              <button
                type="button"
                className="mt-2 rounded-md border border-accent-teal/40 px-3 py-2 text-sm text-text-beige"
                onClick={downloadJson}
              >
                Download JSON
              </button>
            </div>
          </details>
          {adding && (
            <QuestionEditor
              key={`new-${chapterId}`}
              initial={newQuestion}
              token={token}
              onSaved={saved}
              onDeleted={() => setAdding(false)}
              onDirtyChange={dirtyChanged}
              locked={jsonEditing || jsonSaving}
            />
          )}
          {!questions.length && !adding && (
            <p className="text-sm text-text-beige">
              No questions saved for this unit. Prepare drafts or add your own.
            </p>
          )}
          {questions.map((item) => (
            <QuestionEditor
              key={`${item.id}-${editorVersion}`}
              initial={item}
              token={token}
              onSaved={saved}
              onDeleted={(id) => setQuestions((previous) => previous.filter((q) => q.id !== id))}
              onDirtyChange={dirtyChanged}
              locked={jsonEditing || jsonSaving}
            />
          ))}
        </>
      )}
      {loading && (
        <p role="status" className="text-sm text-text-beige">
          Loading unit...
        </p>
      )}
      {error && (
        <p role="alert" className="text-sm text-accent-yellow">
          {error}
        </p>
      )}
      {jsonError && (
        <p role="alert" className="text-sm text-accent-yellow">
          {jsonError}
        </p>
      )}
    </section>
  );
}
