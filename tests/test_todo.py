from lazynote.parse.todo import parse_plain_lines, parse_todo_lines


def test_skips_keyword_line_and_classifies_rest():
    out = parse_todo_lines("todo:\nbuy milk\ndone /x\n// note\n## H")
    assert [line.type for line in out] == [
        "checklist-item",
        "checklist-item-checked",
        "comment",
        "heading",
    ]


def test_strips_x_token_from_checked_text():
    (line,) = parse_todo_lines("todo:\ntask /x")
    assert line.type == "checklist-item-checked"
    assert line.text == "task "


def test_plain_lines_classify_headings_and_text():
    out = parse_plain_lines("# Title\nbody")
    assert out[0].type == "heading"
    assert out[0].heading_level == 1
    assert out[1].type == "checklist-item"
    assert out[1].text == "body"
