from lazynote.highlight import compute_ranges


def _kinds(ranges):
    return [r.kind for r in ranges]


def test_hides_x_token_when_cursor_not_on_that_line():
    r = compute_ranges("todo:\ndone /x", 0)
    assert any(x.kind == "hide_x" for x in r)
    assert any(x.kind == "checkbox_checked" for x in r)


def test_reveals_x_and_unchecked_when_cursor_on_that_line():
    r = compute_ranges("todo:\ndone /x", 1)
    assert not any(x.kind == "hide_x" for x in r)
    assert any(x.kind == "checkbox_unchecked" for x in r)


def test_hide_x_covers_exactly_the_token():
    doc = "todo:\ndone /x"
    r = compute_ranges(doc, 0)
    hide = next(x for x in r if x.kind == "hide_x")
    assert doc[hide.from_ : hide.to] == "/x"


def test_keyword_line_in_todo_mode():
    r = compute_ranges("todo:\nx", 99)
    assert any(x.kind == "keyword" and x.from_ == 0 for x in r)


def test_heading_in_plain_mode_line0():
    r = compute_ranges("# Title", 99)
    assert any(x.kind == "heading1" and x.from_ == 0 for x in r)


def test_heading_levels_2_and_3():
    assert any(x.kind == "heading2" for x in compute_ranges("## H", 99))
    assert any(x.kind == "heading3" for x in compute_ranges("### H", 99))


def test_comment_and_unchecked_in_todo_mode():
    r = compute_ranges("todo:\n// note\nbuy milk", 99)
    assert any(x.kind == "comment" for x in r)
    assert any(x.kind == "checkbox_unchecked" for x in r)


def test_plain_mode_has_no_checkbox():
    r = compute_ranges("buy milk\nmore", 99)
    assert not any(x.kind.startswith("checkbox") for x in r)
    assert not any(x.kind == "keyword" for x in r)


def test_emits_link_with_correct_absolute_offsets():
    doc = "see https://example.com"
    r = compute_ranges(doc, 99)
    link = next(x for x in r if x.kind == "link")
    assert doc[link.from_ : link.to] == "https://example.com"


def test_no_links_on_todo_keyword_line():
    doc = "todo: https://a.com\nsee https://b.com"
    r = compute_ranges(doc, 99)
    links = [x for x in r if x.kind == "link"]
    assert len(links) == 1
    assert doc[links[0].from_ : links[0].to] == "https://b.com"


def test_hyperlink_features_disabled_emits_no_links():
    doc = "see https://example.com and https://other.com/x/y/z"
    r = compute_ranges(doc, 99, hyperlink_features=False)
    assert not any(x.kind == "link" for x in r)


def test_hyperlink_features_disabled_keeps_headings_and_checkboxes():
    doc = "todo:\n# Heading\nbuy milk\n// comment\nsee https://x.com"
    r = compute_ranges(doc, 0, hyperlink_features=False)
    kinds = {x.kind for x in r}
    assert "heading1" in kinds
    assert "checkbox_unchecked" in kinds
    assert "comment" in kinds
    assert "link" not in kinds
