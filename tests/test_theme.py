from __future__ import annotations

import lazynote.theme as theme

KEYS = {"text", "muted", "amber", "green", "blue", "bg", "selection"}


def test_palettes_have_same_keys():
    assert set(theme.PALETTES["dark"]) == KEYS
    assert set(theme.PALETTES["light"]) == KEYS


def test_dark_palette_matches_legacy_colors():
    d = theme.PALETTES["dark"]
    assert d["text"] == "#d6d3cc"
    assert d["muted"] == "#6f6b64"
    assert d["amber"] == "#e6a86b"
    assert d["green"] == "#84c08a"
    assert d["blue"] == "#79b8e0"


def test_resolve_scheme_explicit_modes_pass_through():
    assert theme.resolve_scheme("light", os_scheme="dark") == "light"
    assert theme.resolve_scheme("dark", os_scheme="light") == "dark"


def test_resolve_scheme_system_follows_os():
    assert theme.resolve_scheme("system", os_scheme="light") == "light"
    assert theme.resolve_scheme("system", os_scheme="dark") == "dark"


def test_resolve_scheme_unknown_mode_defaults_to_system():
    assert theme.resolve_scheme("", os_scheme="dark") == "dark"


def test_palette_for_returns_effective_dict():
    assert theme.palette_for("dark", os_scheme="light") == theme.PALETTES["dark"]
    assert theme.palette_for("system", os_scheme="light") == theme.PALETTES["light"]
