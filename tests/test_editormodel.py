"""Tests for the pure per-line render helper used by the bespoke editor (Option B).

These exercise editormodel.line_render_spans, which delegates classification to
highlight.compute_ranges and turns the document into per-line, per-character spans
(color/italic/strike/hidden/link) plus a checkbox descriptor. Pure logic only.
"""

from __future__ import annotations

from antinote_qt.editormodel import LineRender, line_render_spans


def _render(doc: str, line: int, cursor: int) -> LineRender:
    return line_render_spans(doc, line, cursor)


def test_plain_line_single_text_span():
    r = _render("hello world", 0, -1)
    assert r.checkbox is None
    assert "".join(s.text for s in r.spans) == "hello world"
    # default text colour, nothing italic/strike/hidden
    assert all(not s.hidden and not s.strike and not s.italic for s in r.spans)


def test_heading_levels_get_colors():
    r1 = _render("# Big", 0, -1)
    assert r1.spans[0].color.lower() == "#e6a86b"
    r2 = _render("## Mid", 0, -1)
    assert r2.spans[0].color.lower() == "#84c08a"
    r3 = _render("### Small", 0, -1)
    assert r3.spans[0].color.lower() == "#79b8e0"


def test_todo_unchecked_item_has_unchecked_checkbox():
    doc = "todo\nbuy milk"
    r = _render(doc, 1, -1)
    assert r.checkbox == "unchecked"
    assert "".join(s.text for s in r.spans) == "buy milk"


def test_todo_checked_item_hides_x_and_strikes_off_cursor():
    doc = "todo\nbuy milk/x"
    r = _render(doc, 1, 0)  # cursor on line 0, not on the item
    assert r.checkbox == "checked"
    visible = "".join(s.text for s in r.spans if not s.hidden)
    assert visible == "buy milk"
    hidden = "".join(s.text for s in r.spans if s.hidden)
    assert hidden == "/x"
    # the visible body is struck through
    assert any(s.strike for s in r.spans if not s.hidden)


def test_todo_checked_item_revealed_on_cursor_line():
    doc = "todo\nbuy milk/x"
    r = _render(doc, 1, 1)  # cursor on the item line -> raw/editable
    assert r.checkbox == "unchecked"
    visible = "".join(s.text for s in r.spans if not s.hidden)
    assert visible == "buy milk/x"
    assert all(not s.strike for s in r.spans)


def test_comment_line_is_muted_italic():
    doc = "todo\n// a note"
    r = _render(doc, 1, -1)
    assert r.checkbox is None
    assert all(s.italic for s in r.spans)
    assert r.spans[0].color.lower() == "#6f6b64"


def test_keyword_line_is_muted_no_checkbox():
    doc = "todo\nbuy milk"
    r = _render(doc, 0, -1)
    assert r.checkbox is None
    assert r.spans[0].color.lower() == "#6f6b64"


def test_links_are_flagged():
    doc = "see https://example.com now"
    r = _render(doc, 0, -1)
    link_text = "".join(s.text for s in r.spans if s.link)
    assert link_text == "https://example.com"
    assert all(s.color.lower() == "#79b8e0" for s in r.spans if s.link)


def test_empty_line_renders_empty():
    r = _render("a\n\nb", 1, -1)
    assert r.spans == []
    assert r.checkbox is None
