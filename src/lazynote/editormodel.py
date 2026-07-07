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
from lazynote.parse.shorten import display_for_url
from lazynote.theme import PALETTES

# Legacy module-level constants (dark) kept for back-compat with existing imports.
TEXT = PALETTES["dark"]["text"]
MUTED = PALETTES["dark"]["muted"]
AMBER = PALETTES["dark"]["amber"]
GREEN = PALETTES["dark"]["green"]
BLUE = PALETTES["dark"]["blue"]

# Per-kind base style: (palette_key, italic, strike). Hiding and links are
# handled separately because they are character-level, not line-level.
_KIND_STYLE: dict[str, tuple[str, bool, bool]] = {
    "heading1": ("amber", False, False),
    "heading2": ("green", False, False),
    "heading3": ("blue", False, False),
    "comment": ("muted", True, False),
    "keyword": ("muted", False, False),
    "checkbox_checked": ("muted", False, True),
    "checkbox_unchecked": ("text", False, False),
}


@dataclass
class Span:
    text: str
    color: str = TEXT
    italic: bool = False
    strike: bool = False
    hidden: bool = False
    link: bool = False
    # Full URL when `link` is True (the stored truth); None otherwise. The visible
    # `text` may be a shortened display form, but `url` always carries the
    # original URL so click/copy use the full value.
    url: str | None = None


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


def line_render_spans(
    doc: str,
    line_index: int,
    cursor_line: int,
    palette: dict | None = None,
    shorten: bool = False,
    expand_set: set[str] | None = None,
    occurrence_by_offset: dict[int, int] | None = None,
    hyperlink_features: bool = True,
) -> LineRender:
    """Project compute_ranges onto a single line as styled character spans.

    `cursor_line` is forwarded to compute_ranges so the checked-item reveal on the
    caret's line matches the spec exactly. `palette` maps style keys to hex colors
    (defaults to the dark palette for back-compat).

    Link shortening: when `shorten` is True and a link's full URL is not in
    `expand_set`, the visible span text is replaced with the compact
    `display_for_url` form; the occurrence index is looked up in
    `occurrence_by_offset` (keyed by the link's document start offset) so duplicate
    URLs get `[#]` per-occurrence. `Span.url` always carries the original full URL.
    `hyperlink_features=False` suppresses link emission entirely.
    """
    if palette is None:
        palette = PALETTES["dark"]
    bounds = _line_bounds(doc, line_index)
    if bounds is None:
        return LineRender()
    start, end = bounds
    line_text = doc[start:end]
    if line_text == "":
        return LineRender()

    n = len(line_text)
    ranges = [
        r
        for r in compute_ranges(doc, cursor_line, hyperlink_features=hyperlink_features)
        if r.from_ < end and r.to > start
    ]

    # Per-character attribute arrays, seeded with defaults.
    colors = [palette["text"]] * n
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
                colors[i] = palette["blue"]
            continue

        style = _KIND_STYLE.get(r.kind)
        if style is None:
            continue
        key, italic, strike = style
        color = palette[key]
        for i in range(lo, hi):
            colors[i] = color
            italics[i] = italic
            strikes[i] = strike

    # Coalesce adjacent characters with identical attributes into spans. Track the
    # document start offset of each span so link spans can look up their occurrence.
    spans: list[Span] = []
    span_doc_start: list[int] = []
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
        span_doc_start.append(start + i)

    # Substitute the shortened display form into link spans (text only; url keeps
    # the full URL). Done after coalescing so each link is exactly one span.
    if shorten and any(s.link for s in spans):
        occ = occurrence_by_offset or {}
        expanded = expand_set or set()
        for idx, s in enumerate(spans):
            if not s.link:
                continue
            full = s.text
            s.url = full
            if full not in expanded:
                occurrence = occ.get(span_doc_start[idx], 1)
                s.text = display_for_url(full, occurrence)
    else:
        for s in spans:
            if s.link:
                s.url = s.text

    return LineRender(spans=spans, checkbox=checkbox)
