"""Interactive analytics chat loop for the teacher interface.

Run with:
    python -m aimo_agents.analytics_runner

The teacher can ask questions in plain English. The router maps the
intent to the appropriate report tool based on keywords in the message.
"""
from __future__ import annotations

from .tools.generate_report import class_overview, quiz_stats, student_report

# Known student names loaded from scores.jsonl at startup.
def _known_students() -> list[str]:
    import json, os
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, "scores.jsonl")
    if not os.path.exists(path):
        return []
    names = set()
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                names.add(json.loads(line)["student"].lower())
    return list(names)


# Known quiz titles loaded from scores.jsonl at startup.
def _known_quizzes() -> list[str]:
    import json, os
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, "scores.jsonl")
    if not os.path.exists(path):
        return []
    titles: dict[str, str] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                title = json.loads(line)["quiz"]
                titles[title.lower()] = title
    return list(titles.values())


def _route(message: str, students: list[str], quizzes: list[str]) -> str:
    """Map a teacher message to a tool call and return its output."""
    msg = message.lower()

    # Check if message mentions a specific student name.
    for name in students:
        if name in msg:
            return student_report.invoke({"student_name": name})

    # Check if message mentions a specific quiz title.
    for title in quizzes:
        if title.lower() in msg:
            return quiz_stats.invoke({"quiz_title": title})

    # Class-level keywords.
    class_keywords = ["class", "everyone", "all students", "overview", "help", "struggling", "summary"]
    if any(kw in msg for kw in class_keywords):
        return class_overview.invoke({})

    return (
        "I didn't quite understand that. You can ask me things like:\n"
        "  - 'How is alice doing?'\n"
        "  - 'Show me the class overview'\n"
        "  - 'Who is struggling?'\n"
        "  - 'Stats for English Quiz: colours'"
    )


def run_analytics_chat() -> None:
    print("=== AiMO Teacher Analytics ===")
    print("Ask me about your students. Type 'exit' to quit.\n")

    students = _known_students()
    quizzes = _known_quizzes()

    while True:
        try:
            message = input("Teacher: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not message:
            continue
        if message.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break

        response = _route(message, students, quizzes)
        print(f"\nAgent:\n{response}\n")


if __name__ == "__main__":
    run_analytics_chat()
