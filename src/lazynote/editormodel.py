"""Per-line render model for the bespoke editor (Option B).

This is the bridge between the pure rendering oracle (`highlight.compute_ranges`)
and the QML delegates. It turns the whole document into per-line, per-character
*spans* carrying the visual attributes a delegate needs (color, italic, strike,
hidden, link) plus a checkbox descriptor for todo items.

All classification rules are delegated to `compute_ranges` — this module only
*projects* those document-offset ranges down onto a single line and fills the
gaps with the default text style. It is pure (no PySide6) so it can be unit
tested under plain pytest. A thin Qt model wrapper (`LineListModel`) lives at the
bottom and is the only part that imports PySide6.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lazynote.highlight import compute_ranges

# Dark palette — the editor theme.
TEXT = "#d6d3cc"
MUTED = "#6f6b64"
AMBER = "#e6a86b"
GREEN = "#84c08a"
BLUE = "#79b8e0"

# Per-kind base style: (color, italic, strike). Hiding and links are handled
# separately because they are character-level, not line-level.
_KIND_STYLE: dict[str, tuple[str, bool, bool]] = {
    "heading1": (AMBER, False, False),
    "heading2": (GREEN, False, False),
    "heading3": (BLUE, False, False),
    "comment": (MUTED, True, False),
    "keyword": (MUTED, False, False),
    "checkbox_checked": (MUTED, False, True),
    "checkbox_unchecked": (TEXT, False, False),
}


@dataclass
class Span:
    text: str
    color: str = TEXT
    italic: bool = False
    strike: bool = False
    hidden: bool = False
    link: bool = False


@dataclass
class LineRender:
    spans: list[Span] = field(default_factory=list)
    # None | "checked" | "unchecked"
    checkbox: str | None = None


def _line_bounds(doc: str, line_index: int) -> tuple[int, int] | None:
    """Return (start, end) document offsets for line_index, or None if OOB."""
    offset = 0
    for i, line in enumerate(doc.split("\n")):
        if i == line_index:
            return offset, offset + len(line)
        offset += len(line) + 1
    return None


def line_render_spans(doc: str, line_index: int, cursor_line: int) -> LineRender:
    """Project compute_ranges onto a single line as styled character spans.

    `cursor_line` is forwarded to compute_ranges so the checked-item reveal on the
    caret's line matches the spec exactly.
    """
    bounds = _line_bounds(doc, line_index)
    if bounds is None:
        return LineRender()
    start, end = bounds
    line_text = doc[start:end]
    if line_text == "":
        return LineRender()

    n = len(line_text)
    ranges = [r for r in compute_ranges(doc, cursor_line) if r.from_ < end and r.to > start]

    # Per-character attribute arrays, seeded with defaults.
    colors = [TEXT] * n
    italics = [False] * n
    strikes = [False] * n
    hidden = [False] * n
    links = [False] * n

    checkbox: str | None = None
    for r in ranges:
        lo = max(r.from_, start) - start
        hi = min(r.to, end) - start
        if r.kind == "checkbox_checked":
            checkbox = "checked"
        elif r.kind == "checkbox_unchecked":
            checkbox = "unchecked"

        if r.kind == "hide_x":
            for i in range(lo, hi):
                hidden[i] = True
            continue
        if r.kind == "link":
            for i in range(lo, hi):
                links[i] = True
                colors[i] = BLUE
            continue

        style = _KIND_STYLE.get(r.kind)
        if style is None:
            continue
        color, italic, strike = style
        for i in range(lo, hi):
            colors[i] = color
            italics[i] = italic
            strikes[i] = strike

    # Coalesce adjacent characters with identical attributes into spans.
    spans: list[Span] = []
    for i, ch in enumerate(line_text):
        attrs = (colors[i], italics[i], strikes[i], hidden[i], links[i])
        if spans:
            prev = spans[-1]
            if (prev.color, prev.italic, prev.strike, prev.hidden, prev.link) == attrs:
                prev.text += ch
                continue
        spans.append(
            Span(
                text=ch,
                color=colors[i],
                italic=italics[i],
                strike=strikes[i],
                hidden=hidden[i],
                link=links[i],
            )
        )
    return LineRender(spans=spans, checkbox=checkbox)
