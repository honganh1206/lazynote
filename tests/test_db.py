from antinote_qt.db import NotesRepo, SettingsRepo, open_db


def fresh(tmp_path):
    return open_db(str(tmp_path / "notes.db"))


def test_creates_and_lists_ordered_by_sort_index(tmp_path):
    notes = NotesRepo(fresh(tmp_path))
    a = notes.create("first")
    b = notes.create("second")
    assert [n.id for n in notes.list()] == [a.id, b.id]
    assert b.sort_index > a.sort_index


def test_updates_content(tmp_path):
    notes = NotesRepo(fresh(tmp_path))
    n = notes.create("x")
    notes.update(n.id, "y")
    assert notes.list()[0].content == "y"


def test_deletes_a_note(tmp_path):
    notes = NotesRepo(fresh(tmp_path))
    n = notes.create("x")
    notes.delete(n.id)
    assert notes.list() == []


def test_settings_seed_defaults_and_round_trip(tmp_path):
    s = SettingsRepo(fresh(tmp_path))
    assert s.get("always_on_top") == "true"
    s.set("always_on_top", "false")
    assert s.get("always_on_top") == "false"


def test_settings_get_missing_returns_none(tmp_path):
    s = SettingsRepo(fresh(tmp_path))
    assert s.get("nope") is None
