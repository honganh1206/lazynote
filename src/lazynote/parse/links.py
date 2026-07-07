"""URL extraction. Ported from the original app's links.ts (same regex)."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Match URLs but stop before a trailing ) when the URL is wrapped in parens,
# while still allowing balanced parens inside the path (e.g. Wikipedia URLs).
_URL_RE = re.compile(r"https?://[^\s()]+(?:\([^\s()]*\)[^\s()]*)*|https?://[^\s]+")


@dataclass
class LinkSegment:
    type: str  # "text" | "link"
    value: str
    display_value: str
    full_url: str | None = None


def parse_links(text: str) -> list[LinkSegment]:
    segments: list[LinkSegment] = []
    last = 0
    for m in _URL_RE.finditer(text):
        url = m.group(0)
        start = m.start()
        if start > last:
            v = text[last:start]
            segments.append(LinkSegment("text", v, v))
        segments.append(LinkSegment("link", url, url, url))
        last = start + len(url)
    if last < len(text):
        v = text[last:]
        segments.append(LinkSegment("text", v, v))
    if not segments and text:
        segments.append(LinkSegment("text", text, text))
    return segments


def link_occurrence_by_offset(doc: str) -> dict[int, int]:
    """Map each link's start offset to its 1-based occurrence index among equal URLs.

    First occurrence of a URL → 1, second → 2, etc. Used by the render path to
    append Antinote's `[#]` duplicate disambiguator on a per-occurrence basis
    (the same URL appearing three times shows `…`, `…[2]`, `…[3]`).
    """
    counts: dict[str, int] = {}
    out: dict[int, int] = {}
    for m in _URL_RE.finditer(doc):
        url = m.group(0)
        counts[url] = counts.get(url, 0) + 1
        out[m.start()] = counts[url]
    return out
