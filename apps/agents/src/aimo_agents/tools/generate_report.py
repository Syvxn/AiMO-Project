"""Analytics and reporting tools that read from scores.jsonl."""
from __future__ import annotations

import json
import os
from collections import defaultdict

from langchain_core.tools import tool


def _load_scores() -> list[dict]:
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(tools_dir)))
    file_path = os.path.join(project_root, "scores.jsonl")

    if not os.path.exists(file_path):
        return []

    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _trend(scores: list[float]) -> str:
    if len(scores) < 4:
        return "not enough data"
    mid = len(scores) // 2
    first_half = sum(scores[:mid]) / mid
    second_half = sum(scores[mid:]) / (len(scores) - mid)
    diff = second_half - first_half
    if diff > 0.1:
        return "improving"
    if diff < -0.1:
        return "declining"
    return "stable"


# Example triggers: "How is alice doing?", "Show me bob's progress", "Is charlie improving?"
@tool
def student_report(student_name: str) -> str:
    """Generate a performance report for a single student.

    Shows all quiz attempts, average score, and whether the student
    is improving, declining, or staying stable over time.
    """
    records = [r for r in _load_scores() if r["student"].lower() == student_name.lower()]

    if not records:
        return f"No records found for student '{student_name}'."

    records.sort(key=lambda r: r["date"])

    lines = [f"Report for {student_name} ({len(records)} attempts):\n"]
    percentages = []
    for r in records:
        pct = round(r["score"] / r["total"] * 100)
        percentages.append(pct / 100)
        lines.append(f"  {r['date']}  {r['quiz']}: {r['score']}/{r['total']} ({pct}%)")

    avg = round(sum(percentages) / len(percentages) * 100)
    trend = _trend(percentages)
    lines.append(f"\nAverage score: {avg}%")
    lines.append(f"Trend: {trend}")

    return "\n".join(lines)


# Example triggers: "How is the class doing?", "Who needs help?", "Give me a class overview"
@tool
def class_overview() -> str:
    """Show how every student is performing across all quizzes.

    Lists each student's overall average score and trend,
    sorted from highest to lowest average. Use this for a general
    class health check or when the teacher asks how the class is doing.
    """
    records = _load_scores()

    if not records:
        return "No score records found."

    by_student: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_student[r["student"]].append(r)

    rows = []
    for student, attempts in by_student.items():
        sorted_attempts = sorted(attempts, key=lambda r: r["date"])
        percentages = [r["score"] / r["total"] for r in sorted_attempts]
        avg = round(sum(percentages) / len(percentages) * 100)
        trend = _trend(percentages)
        rows.append((student, avg, trend, len(attempts)))

    rows.sort(key=lambda x: x[1], reverse=True)

    lines = ["Class overview:\n"]
    for student, avg, trend, count in rows:
        lines.append(f"  {student}: {avg}% avg ({count} attempts) — {trend}")

    struggling = [s for s, avg, _, _ in rows if avg < 50]
    if struggling:
        lines.append(f"\nStudents who may need help: {', '.join(struggling)}")

    return "\n".join(lines)


# Example triggers: "How did the colours quiz go?", "What's the pass rate for the colours quiz?"
@tool
def quiz_stats(quiz_title: str) -> str:
    """Show aggregate statistics for a specific quiz across all students.

    Includes overall average, highest and lowest scores, pass rate (>= 50%),
    and a per-student breakdown. Use this when the teacher asks about a
    specific quiz rather than a specific student.
    """
    records = [r for r in _load_scores() if r["quiz"].lower() == quiz_title.lower()]

    if not records:
        return f"No records found for quiz '{quiz_title}'."

    percentages = [round(r["score"] / r["total"] * 100) for r in records]
    avg = round(sum(percentages) / len(percentages))
    pass_rate = round(sum(1 for p in percentages if p >= 50) / len(percentages) * 100)

    lines = [
        f"Stats for '{quiz_title}' ({len(records)} total attempts):\n",
        f"  Average score: {avg}%",
        f"  Highest score: {max(percentages)}%",
        f"  Lowest score:  {min(percentages)}%",
        f"  Pass rate:     {pass_rate}%",
    ]

    by_student: dict[str, list[int]] = defaultdict(list)
    for r, pct in zip(records, percentages):
        by_student[r["student"]].append(pct)

    lines.append("\nPer-student averages:")
    per_student = [(s, round(sum(p) / len(p))) for s, p in by_student.items()]
    per_student.sort(key=lambda x: x[1], reverse=True)
    for student, avg_pct in per_student:
        lines.append(f"  {student}: {avg_pct}%")

    return "\n".join(lines)
