"""Tests for the pure URL shortening oracle (parse/shorten.py).

Antinote's exact "smart endings" heuristic is not public, so these tests define
our spec: keep the host and a meaningful tail, drop the middle of long paths and
drop query/fragment. Short URLs are returned unchanged.
"""

from __future__ import annotations

from lazynote.parse.shorten import display_for_url, shorten_url


# ---- shorten_url: always transform (drop scheme + query/fragment + middle) ----


def test_no_path_returns_host() -> None:
    assert shorten_url("https://example.com") == "example.com"


def test_one_segment_kept() -> None:
    assert shorten_url("https://example.com/a") == "example.com/a"


def test_two_segments_kept() -> None:
    assert shorten_url("https://example.com/a/b") == "example.com/a/b"


def test_three_path_segments_drop_middle() -> None:
    assert shorten_url("https://example.com/a/b/c") == "example.com/…/c"


def test_github_issues() -> None:
    assert shorten_url("https://github.com/owner/repo/issues/123") == "github.com/…/123"


def test_drops_query_and_fragment() -> None:
    assert shorten_url("https://example.com/a/b/c?ref=1#frag") == "example.com/…/c"
    # query on a 1-segment URL: path kept, query dropped
    assert shorten_url("https://example.com/path?utm_source=x&id=42") == "example.com/path"


def test_scheme_always_dropped() -> None:
    assert shorten_url("https://example.com/a/b/c/d") == "example.com/…/d"


def test_extremely_long_last_segment_tail_truncated() -> None:
    long_seg = "x" * 200
    out = shorten_url(f"https://example.com/a/b/{long_seg}")
    assert out.startswith("example.com/…/…")
    # tail preserved, total within max_len
    assert len(out) <= 40
    assert out.endswith(long_seg[-(40 - len("example.com/…/…")):])


def test_host_truncated_when_alone_too_long() -> None:
    host = "x" * 200
    out = shorten_url(f"https://{host}.com/a/b/c")
    assert out.endswith("…")
    assert len(out) <= 40


def test_custom_max_len_bounds_output() -> None:
    out = shorten_url("https://example.com/a/verylongsegmentname", max_len=20)
    assert len(out) <= 20
    assert out.startswith("example.com/")


def test_unparseable_falls_back_to_truncated_original() -> None:
    # urlsplit is lenient, so feed something that still gets returned sensibly but
    # is degenerate. The contract: never throw, never return empty, length bounded.
    out = shorten_url("not a url at all " * 10)
    assert out
    assert len(out) <= 40


def test_empty_returns_empty() -> None:
    assert shorten_url("") == ""


# ---- display_for_url: occurrence suffix ----


def test_display_first_occurrence_no_suffix() -> None:
    assert display_for_url("https://example.com/a/b/c", 1) == "example.com/…/c"


def test_display_second_occurrence_suffix() -> None:
    assert display_for_url("https://example.com/a/b/c", 2) == "example.com/…/c[2]"


def test_display_short_url_unchanged_with_suffix() -> None:
    assert display_for_url("https://example.com", 3) == "example.com[3]"


def test_display_occurrence_zero_treated_as_first() -> None:
    assert display_for_url("https://example.com/a/b/c", 0) == "example.com/…/c"
