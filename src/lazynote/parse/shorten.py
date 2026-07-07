"""Pure URL shortening oracle.

Antinote shortens URLs visually while keeping the full URL as the stored truth.
The exact "smart endings" heuristic is not public, so this module defines our
own: always drop the scheme and the query/fragment, keep the host, and keep a
meaningful tail — the last path segment — collapsing the middle of long paths
into an ellipsis. The result is then hard-truncated to `max_len` if still too
long.

Rules:
- 0 path segments -> `host`
- 1 segment      -> `host/seg`
- 2 segments     -> `host/seg1/seg2`
- >2 segments    -> `host/…/<last>`
- If the result exceeds `max_len`, the last segment is truncated from the left
  with a leading `…`; if even the host is too long, the host is truncated from
  the right with a trailing `…`.
- Unparseable input never throws; it falls back to a length-truncated copy.

Pure (no PySide6) so it can be unit-tested under plain pytest.
"""

from __future__ import annotations

import urllib.parse

ELLIPSIS = "…"

DEFAULT_MAX_LEN = 40


def shorten_url(url: str, max_len: int = DEFAULT_MAX_LEN) -> str:
    """Return a compact display form of `url`, bounded to `max_len` chars.

    Never throws and never returns empty for non-empty input. On any parse
    failure, falls back to a length-truncated copy of the original.
    """
    if not url:
        return ""

    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return _truncate(url, max_len)

    host = parts.hostname or ""
    if parts.port:
        host = f"{host}:{parts.port}"

    if not host:
        # Not a parseable authority-bearing URL; truncate the raw string.
        return _truncate(url, max_len)

    segments = [s for s in parts.path.split("/") if s != ""]
    body = _build_body(host, segments)
    if len(body) <= max_len:
        return body
    return _truncate_body(body, max_len)


def _build_body(host: str, segments: list[str]) -> str:
    if not segments:
        return host
    if len(segments) <= 2:
        return f"{host}/{'/'.join(segments)}"
    return f"{host}/{ELLIPSIS}/{segments[-1]}"


def _truncate_body(body: str, max_len: int) -> str:
    # Try to truncate the last segment (text after the final '/') from the left.
    slash = body.rfind("/")
    if slash < 0:
        # No slash: it's just the host — truncate from the right.
        return _truncate(body, max_len)
    prefix = body[: slash + 1]
    last = body[slash + 1:]
    if len(prefix) >= max_len:
        return _truncate(prefix.rstrip("/"), max_len)
    budget = max_len - len(prefix)
    if budget <= 0:
        return _truncate(prefix, max_len)
    if len(last) <= budget:
        return prefix + last
    # Truncate the last segment from the left, prefixed with an ellipsis.
    if budget == 1:
        return prefix + last[-1:]
    tail = last[-(budget - 1):]
    return prefix + ELLIPSIS + tail


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    if max_len <= 0:
        return ""
    return s[: max_len - 1] + ELLIPSIS


def display_for_url(url: str, occurrence: int, max_len: int = DEFAULT_MAX_LEN) -> str:
    """Shortened form with a `[#]` disambiguator appended for repeat URLs.

    First occurrence (or occurrence <= 1) gets no suffix; 2nd gets `[2]`, etc.
    The suffix is appended to the already-shortened form.
    """
    short = shorten_url(url, max_len)
    if occurrence and occurrence > 1:
        short = f"{short}[{occurrence}]"
    return short
