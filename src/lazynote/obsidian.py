"""Obsidian export helpers (pure, no Qt).

Builds an `obsidian://new` URI that creates a new note in the user's
last-focused vault (we omit the `vault` parameter on purpose). See
https://help.obsidian.md/Extending+Obsidian/Obsidian+URI for the scheme.
"""

from __future__ import annotations

import re
from urllib.parse import quote

# Characters Obsidian forbids in file names (Windows + cross-platform rules).
_FORBIDDEN = re.compile(r'[\\/:*?"<>|]+')


def derive_note_name(content: str, *, fallback: str = "Untitled", max_len: int = 80) -> str:
    """Pick a readable file name for an exported note.

    Scans lines top-down, skips blank lines and `//` comments, strips leading
    `#` heading markers and the `todo`/`todo:` keyword, trims, and removes
    characters that Obsidian file names cannot contain. Falls back to
    `fallback` when there is nothing usable.
    """
    for raw in content.split("\n"):
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        # Drop leading heading hashes ("#", "##", "### ...").
        if line.startswith("#"):
            line = line.lstrip("#").strip()
        # Drop a leading "todo" / "todo:" keyword (todo-mode title line).
        m = re.match(r"^todo\b\s*:?\s*", line, re.IGNORECASE)
        if m:
            line = line[m.end():]
        line = re.sub(r"\s+", " ", _FORBIDDEN.sub(" ", line)).strip()
        if line:
            if len(line) > max_len:
                line = line[:max_len].rstrip()
            return line
    return fallback


def build_new_note_url(name: str, content: str) -> str:
    """Build `obsidian://new?file=...&content=...` with both values URL-encoded.

    We use `file` (not `name`) so the note lands at the **vault root** regardless
    of the user's "Default location for new notes" setting — `name` would honour
    that preference (often a subfolder), whereas `file` with no path prefix
    targets the vault root directly. `content` becomes the note body. We use
    `quote(..., safe="")` so forward slashes and spaces are encoded too.
    """
    return "obsidian://new?file=" + quote(name, safe="") + "&content=" + quote(content, safe="")
