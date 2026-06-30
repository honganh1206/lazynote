"""Theme palettes and color-scheme resolution.

Pure module (no PySide6) so it can be unit tested. The Backend passes the live
OS scheme in; this module owns the palette values and the system/override logic.
"""

from __future__ import annotations

PALETTES: dict[str, dict[str, str]] = {
    "dark": {
        "text": "#d6d3cc",
        "muted": "#6f6b64",
        "amber": "#e6a86b",
        "green": "#84c08a",
        "blue": "#79b8e0",
        "bg": "#1f2023",
        "selection": "#34363b",
    },
    "light": {
        "text": "#2b2a27",
        "muted": "#9a948b",
        "amber": "#b9701f",
        "green": "#3f8f47",
        "blue": "#2f7bb0",
        "bg": "#f4f2ec",
        "selection": "#d8d3c7",
    },
}


def resolve_scheme(mode: str, os_scheme: str = "dark") -> str:
    """Map a theme mode to a concrete scheme ("light"|"dark").

    `mode` is "system" | "light" | "dark" (anything else == "system").
    `os_scheme` is the OS-reported scheme, used only when following the system.
    """
    if mode in ("light", "dark"):
        return mode
    return "light" if os_scheme == "light" else "dark"


def palette_for(mode: str, os_scheme: str = "dark") -> dict[str, str]:
    return PALETTES[resolve_scheme(mode, os_scheme)]
