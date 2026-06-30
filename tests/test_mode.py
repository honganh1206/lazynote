from lazynote.parse.mode import REGISTERED_KEYWORDS, detect_mode


def test_detects_todo_with_title():
    assert detect_mode("todo: groceries\n...") == {"keyword": "todo", "title": "groceries"}


def test_detects_bare_todo():
    assert detect_mode("todo") == {"keyword": "todo", "title": ""}


def test_returns_none_for_plain_text():
    assert detect_mode("just a note") is None


def test_exposes_registered_keywords():
    assert "todo" in REGISTERED_KEYWORDS
