from __future__ import annotations

import lazynote.fonts as fonts

AVAIL = ["DejaVu Sans Mono", "Hack", "Noto Sans Mono"]
DEFAULT = "DejaVu Sans Mono"


def test_valid_family_and_size_pass_through():
    assert fonts.resolve_font("Hack", 18, AVAIL, DEFAULT) == {
        "family": "Hack",
        "size": 18,
    }


def test_empty_family_uses_default():
    assert fonts.resolve_font("", 15, AVAIL, DEFAULT)["family"] == DEFAULT


def test_uninstalled_family_uses_default():
    assert fonts.resolve_font("Comic Mono", 15, AVAIL, DEFAULT)["family"] == DEFAULT


def test_size_clamped_low():
    assert fonts.resolve_font("Hack", 2, AVAIL, DEFAULT)["size"] == fonts.MIN_SIZE


def test_size_clamped_high():
    assert fonts.resolve_font("Hack", 999, AVAIL, DEFAULT)["size"] == fonts.MAX_SIZE


def test_string_numeric_size_parsed():
    assert fonts.resolve_font("Hack", "18", AVAIL, DEFAULT)["size"] == 18


def test_bad_size_falls_back_to_default():
    assert fonts.resolve_font("Hack", "", AVAIL, DEFAULT)["size"] == fonts.DEFAULT_SIZE
    assert fonts.resolve_font("Hack", "abc", AVAIL, DEFAULT)["size"] == fonts.DEFAULT_SIZE
    assert fonts.resolve_font("Hack", None, AVAIL, DEFAULT)["size"] == fonts.DEFAULT_SIZE
