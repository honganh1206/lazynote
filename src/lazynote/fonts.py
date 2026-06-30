"""Font defaulting + clamping.

Pure module (no PySide6) so it can be unit tested. The Backend passes the live
list of available families + the system default monospace in; this module owns
the fallback and clamp logic.
"""

from __future__ import annotations

MIN_SIZE = 8
MAX_SIZE = 32
DEFAULT_SIZE = 15


def clamp_size(size: int | str | None) -> int:
    try:
        n = int(size)
    except (TypeError, ValueError):
        return DEFAULT_SIZE
    return max(MIN_SIZE, min(MAX_SIZE, n))


def resolve_font(
    family: str, size: int | str | None, available: list[str], default_family: str
) -> dict[str, object]:
    """Return an effective {"family", "size"}.

    `family` falls back to `default_family` when empty or not in `available`.
    `size` is parsed to int (DEFAULT_SIZE on bad input) and clamped to range.
    """
    fam = family if family and family in available else default_family
    return {"family": fam, "size": clamp_size(size)}
