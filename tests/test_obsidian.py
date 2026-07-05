from lazynote.obsidian import build_new_note_url, derive_note_name


# ---- derive_note_name ----

def test_plain_first_line_becomes_name():
    assert derive_note_name("buy milk\nwalk dog") == "buy milk"


def test_strips_heading_hashes():
    assert derive_note_name("# Project Ideas\n- thing") == "Project Ideas"


def test_strips_todo_keyword_with_colon():
    assert derive_note_name("todo: Shopping list\nbuy milk") == "Shopping list"


def test_strips_todo_keyword_without_colon():
    assert derive_note_name("todo Shopping list\nbuy milk") == "Shopping list"


def test_todo_keyword_case_insensitive():
    assert derive_note_name("TODO: Weekly review\n- x") == "Weekly review"


def test_skips_blank_and_comment_lines():
    content = "// a comment\n\n# Real Title\nbody"
    assert derive_note_name(content) == "Real Title"


def test_falls_back_when_empty():
    assert derive_note_name("") == "Untitled"
    assert derive_note_name("\n\n  \n// only a comment") == "Untitled"


def test_bare_todo_keyword_falls_through_to_next_line():
    # A lone "todo" line is not a title; the next content line is used.
    assert derive_note_name("todo\n- buy milk") == "- buy milk"


def test_bare_todo_keyword_only_falls_back():
    assert derive_note_name("todo") == "Untitled"


def test_removes_forbidden_filename_chars():
    content = 'ideas: a/b? c*d'
    assert derive_note_name(content) == "ideas a b c d"


def test_truncates_long_names():
    name = derive_note_name("x" * 200)
    assert len(name) == 80
    assert name == "x" * 80


def test_custom_fallback():
    assert derive_note_name("", fallback="Note") == "Note"


# ---- build_new_note_url ----

def test_builds_url_with_encoded_name_and_content():
    url = build_new_note_url("My Note", "hello world")
    assert url == "obsidian://new?file=My%20Note&content=hello%20world"


def test_encodes_forward_slashes_and_reserved_chars():
    url = build_new_note_url("a/b", "line1\nline2")
    assert url == "obsidian://new?file=a%2Fb&content=line1%0Aline2"


def test_omits_vault_parameter_uses_last_focused_vault():
    url = build_new_note_url("Note", "body")
    assert "vault=" not in url


def test_uses_file_parameter_for_vault_root_placement():
    # `file=` (not `name=`) forces the vault root regardless of the user's
    # "Default location for new notes" setting.
    url = build_new_note_url("Note", "body")
    assert "file=Note" in url
    assert "name=" not in url


def test_empty_content_still_encoded():
    url = build_new_note_url("Note", "")
    assert url == "obsidian://new?file=Note&content="
