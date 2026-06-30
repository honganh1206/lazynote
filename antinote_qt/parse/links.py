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
