from lazynote.parse.links import LinkSegment, parse_links


def test_plain_text_single_segment():
    assert parse_links("hello world") == [LinkSegment("text", "hello world", "hello world")]


def test_extracts_url_segment():
    segs = parse_links("see https://example.com now")
    assert [s.type for s in segs] == ["text", "link", "text"]
    assert segs[1].type == "link"
    assert segs[1].full_url == "https://example.com"


def test_keeps_url_inside_balanced_parens():
    segs = parse_links("(https://en.wikipedia.org/wiki/A_(b))")
    link = next(s for s in segs if s.type == "link")
    assert link.full_url == "https://en.wikipedia.org/wiki/A_(b)"


def test_empty_string_returns_empty():
    assert parse_links("") == []
