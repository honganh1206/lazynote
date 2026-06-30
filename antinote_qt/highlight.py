"""Syntax range computation. Pure port of the original decorations.ts computeRanges.

Returns a flat list of Range(from_, to, kind) over the document. The editor layer
translates these into Qt text formats / styled line items. Kept free of PySide6 so
it can be unit-tested under plain pytest.

Kinds: heading1 | heading2 | heading3 | comment | keyword |
       checkbox_checked | checkbox_unchecked | link | hide_x
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from antinote_qt.parse.links import parse_links
from antinote_qt.parse.mode import detect_mode

_HEADING_RE = re.compile(r"^(#{1,3}) ")


@dataclass
class Range:
    from_: int
    to: int
    kind: str


def _emit_links(ranges: list[Range], line: str, line_start: int) -> None:
    local = 0
    for seg in parse_links(line):
        if seg.type == "link":
            ranges.append(Range(line_start + local, line_start + local + len(seg.value), "link"))
        local += len(seg.value)


def compute_ranges(doc: str, sel_head_line: int) -> list[Range]:
    mode = detect_mode(doc)
    is_todo = bool(mode and mode["keyword"] == "todo")

    ranges: list[Range] = []
    offset = 0
    for i, line in enumerate(doc.split("\n")):
        line_start = offset
        line_end = offset + len(line)
        offset = line_end + 1  # advance past the '\n'

        # Todo keyword line (line 0): greyed, no link parsing.
        if is_todo and i == 0:
            ranges.append(Range(line_start, line_end, "keyword"))
            continue

        if line.strip() == "":
            continue

        m = _HEADING_RE.match(line)
        if m:
            ranges.append(Range(line_start, line_end, f"heading{len(m.group(1))}"))
            _emit_links(ranges, line, line_start)
            continue

        if is_todo:
            if line.startswith("//"):
                ranges.append(Range(line_start, line_end, "comment"))
                _emit_links(ranges, line, line_start)
                continue
            if line.endswith("/x"):
                if sel_head_line == i:
                    # Cursor on the line: show it raw/editable (no strike, no hide).
                    ranges.append(Range(line_start, line_end, "checkbox_unchecked"))
                else:
                    ranges.append(Range(line_start, line_end, "checkbox_checked"))
                    ranges.append(Range(line_end - 2, line_end, "hide_x"))
                _emit_links(ranges, line, line_start)
                continue
            ranges.append(Range(line_start, line_end, "checkbox_unchecked"))
            _emit_links(ranges, line, line_start)
            continue

        # Plain mode, non-heading line.
        _emit_links(ranges, line, line_start)

    return ranges
