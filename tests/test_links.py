from lazynote.parse.links import LinkSegment, link_occurrence_by_offset, parse_links


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


def test_occurrence_by_offset_single_url():
    doc = "see https://example.com now"
    assert link_occurrence_by_offset(doc) == {4: 1}


def test_occurrence_by_offset_duplicates_in_order():
    url = "https://example.com/a/b/c"
    doc = f"{url}\n{url}\n{url}"
    occ = link_occurrence_by_offset(doc)
    assert occ == {0: 1, len(url) + 1: 2, 2 * (len(url) + 1): 3}


def test_occurrence_by_offset_distinct_urls_each_first():
    doc = "https://a.com and https://b.com"
    assert link_occurrence_by_offset(doc) == {0: 1, 18: 1}
