"""Page-aware textbook parsing, independent of the database and model service."""
from __future__ import annotations

import re


_UNIT = re.compile(r"\bUNIT\s+(\d+)\b", re.I)
_RUNNING_HEADER = re.compile(
    r"^.*THINK\s+ENGLISH.*(?:BOOK|BOOK\s+UNIT).*?$", re.I
)


def parse_think_english(pages: list[str]) -> list[dict[str, str]] | None:
    """Read the interleaved student/teacher edition; None means another book.

    Unit numbers come from running headers, not every mention of a unit in the
    contents, course map, revision, or resources. No PDF page ranges are hardcoded.
    """
    if not pages or "THINKENGLISH" not in _compact(" ".join(pages[:2])):
        return None

    units: dict[int, dict] = {}
    for page_number, text in enumerate(pages, 1):
        # Running headers identify both the edition and unit on each lesson page.
        header = next(
            (line for line in text.splitlines()
             if "THINKENGLISH" in _compact(line) and "BOOK" in _compact(line)
             and _UNIT.search(line)),
            None,
        )
        if header is None:
            continue
        number = int(_UNIT.search(header).group(1))
        compact = _compact(header)
        if "STUDENTSBOOK" in compact:
            role = "content"
        elif "TEACHERSBOOK" in compact:
            role = "teaching_guidance"
        else:
            continue

        unit = units.setdefault(number, {"title": f"Unit {number}", "content": [], "teaching_guidance": []})
        # The full unit title appears after the standalone UNIT N on opening pages.
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for index, line in enumerate(lines[:-1]):
            if re.fullmatch(rf"UNIT\s+{number}", line, re.I):
                title = lines[index + 1]
                if (title.isupper() or (unit["title"] == f"Unit {number}" and index < 8)) and re.fullmatch(r"[A-Za-z][A-Za-z &'-]{2,80}", title):
                    unit["title"] = f"Unit {number}: {title.title()}"
                    break

        body = "\n".join(
            line for line in text.splitlines()
            if not _RUNNING_HEADER.match(line)
            and not re.fullmatch(r"\s*[BW]\.\s*[LR]\s*", line)
        ).strip()
        if body:
            unit[role].append(f"[PDF page {page_number}]\n{body}")

    return [
        {
            "key": f"unit-{number}",
            "title": unit["title"],
            "content": "\n\n---\n\n".join(unit["content"]),
            "teaching_guidance": "\n\n---\n\n".join(unit["teaching_guidance"]),
        }
        for number, unit in sorted(units.items()) if unit["content"]
    ]


def _compact(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", text.upper())
