"""Line classification for todo/plain modes. Ported from the original todo.ts."""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING_RE = re.compile(r"^(#{1,3}) ")

# LineType: "checklist-item" | "checklist-item-checked" | "heading" | "comment" | "empty"


@dataclass
class ParsedLine:
    type: str
    text: str
    heading_level: int | None = None


def parse_todo_lines(content: str) -> list[ParsedLine]:
    # Skip line 0 (the keyword line); classify the rest.
    lines = content.split("\n")
    return [_classify_line(line) for line in lines[1:]]


def parse_plain_lines(content: str) -> list[ParsedLine]:
    return [_classify_plain_line(line) for line in content.split("\n")]


def _classify_plain_line(line: str) -> ParsedLine:
    if line.strip() == "":
        return ParsedLine("empty", line)
    m = _HEADING_RE.match(line)
    if m:
        return ParsedLine("heading", line, len(m.group(1)))
    return ParsedLine("checklist-item", line)


def _classify_line(line: str) -> ParsedLine:
    if line.strip() == "":
        return ParsedLine("empty", line)
    m = _HEADING_RE.match(line)
    if m:
        return ParsedLine("heading", line, len(m.group(1)))
    if line.startswith("//"):
        return ParsedLine("comment", line)
    if line.endswith("/x"):
        return ParsedLine("checklist-item-checked", line[:-2])
    return ParsedLine("checklist-item", line)
