"""Editor mode detection from the first line. Ported from keywords.svelte.ts."""

from __future__ import annotations

import re

REGISTERED_KEYWORDS: list[str] = ["todo"]

_FIRST_LINE_RE = re.compile(r"^(\w+)(?::\s*(.*))?$")


def detect_mode(content: str) -> dict | None:
    """Return {"keyword", "title"} if the first line names a registered keyword, else None."""
    first = content.split("\n")[0].strip()
    if not first:
        return None
    m = _FIRST_LINE_RE.match(first)
    if not m:
        return None
    keyword = m.group(1).lower()
    if keyword not in REGISTERED_KEYWORDS:
        return None
    title = (m.group(2) or "").strip()
    return {"keyword": keyword, "title": title}


def is_keyword_registered(keyword: str) -> bool:
    return keyword.lower() in REGISTERED_KEYWORDS
