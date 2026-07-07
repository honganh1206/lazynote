"""Tests for the pure per-line render helper used by the bespoke editor (Option B).

These exercise editormodel.line_render_spans, which delegates classification to
highlight.compute_ranges and turns the document into per-line, per-character spans
(color/italic/strike/hidden/link) plus a checkbox descriptor. Pure logic only.
"""

from __future__ import annotations

from lazynote.editormodel import LineRender, line_render_spans
from lazynote.theme import PALETTES


def _render(doc: str, line: int, cursor: int) -> LineRender:
    return line_render_spans(doc, line, cursor)


def test_light_palette_changes_heading_color():
    r = line_render_spans("# Big", 0, -1, palette=PALETTES["light"])
    assert r.spans[0].color.lower() == "#b9701f"  # light amber


def test_default_palette_is_dark():
    r = line_render_spans("# Big", 0, -1)
    assert r.spans[0].color.lower() == "#e6a86b"  # dark amber


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
    # url carries the full URL even when not shortening
    assert all(s.url == "https://example.com" for s in r.spans if s.link)


def test_link_span_url_carries_full_url_when_not_link():
    r = _render("plain text", 0, -1)
    assert all(s.url is None for s in r.spans)


def test_shorten_replaces_visible_text_keeps_url():
    doc = "see https://github.com/owner/repo/issues/123 now"
    r = line_render_spans(doc, 0, -1, shorten=True)
    link = next(s for s in r.spans if s.link)
    assert link.text == "github.com/…/123"
    assert link.url == "https://github.com/owner/repo/issues/123"


def test_shorten_off_keeps_full_url_visible():
    doc = "see https://github.com/owner/repo/issues/123 now"
    r = line_render_spans(doc, 0, -1, shorten=False)
    link = next(s for s in r.spans if s.link)
    assert link.text == "https://github.com/owner/repo/issues/123"
    assert link.url == "https://github.com/owner/repo/issues/123"


def test_expand_set_keeps_full_url_visible():
    url = "https://github.com/owner/repo/issues/123"
    doc = f"see {url} now"
    r = line_render_spans(doc, 0, -1, shorten=True, expand_set={url})
    link = next(s for s in r.spans if s.link)
    assert link.text == url
    assert link.url == url


def test_occurrence_map_suffixes_duplicates():
    url = "https://example.com/a/b/c"
    doc = f"{url}\n{url}\n{url}"
    # line 2 starts after "url\nurl\n" = len(url)+1 + len(url)+1
    line2_start = (len(url) + 1) + (len(url) + 1)
    occ = {0: 1, len(url) + 1: 2, line2_start: 3}
    r = line_render_spans(doc, 2, -1, shorten=True, occurrence_by_offset=occ)
    link = next(s for s in r.spans if s.link)
    assert link.text == "example.com/…/c[3]"
    assert link.url == url


def test_occurrence_first_has_no_suffix():
    url = "https://example.com/a/b/c"
    doc = f"{url}\n{url}"
    occ = {0: 1, len(url) + 1: 2}
    r0 = line_render_spans(doc, 0, -1, shorten=True, occurrence_by_offset=occ)
    r1 = line_render_spans(doc, 1, -1, shorten=True, occurrence_by_offset=occ)
    assert next(s for s in r0.spans if s.link).text == "example.com/…/c"
    assert next(s for s in r1.spans if s.link).text == "example.com/…/c[2]"


def test_hyperlink_features_disabled_emits_no_link_spans():
    doc = "see https://github.com/owner/repo/issues/123 now"
    r = line_render_spans(doc, 0, -1, shorten=True, hyperlink_features=False)
    assert not any(s.link for s in r.spans)
    assert not any(s.url for s in r.spans)


def test_empty_line_renders_empty():
    r = _render("a\n\nb", 1, -1)
    assert r.spans == []
    assert r.checkbox is None
