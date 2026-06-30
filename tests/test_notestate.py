from antinote_qt.db import NotesRepo, SettingsRepo, open_db
from antinote_qt.notestate import NoteState


def make(tmp_path):
    conn = open_db(str(tmp_path / "notes.db"))
    return NoteState(NotesRepo(conn), SettingsRepo(conn)), conn


def test_load_empty_db_creates_one_note(tmp_path):
    state, _ = make(tmp_path)
    state.load()
    assert state.count() == 1
    assert state.index == 0
    assert state.content == ""


def test_load_auto_creates_when_last_note_nonempty(tmp_path):
    state, conn = make(tmp_path)
    NotesRepo(conn).create("existing")
    state.load()
    assert state.count() == 2
    assert state.content == ""  # sits on the fresh empty note


def test_load_respects_auto_create_false(tmp_path):
    state, conn = make(tmp_path)
    NotesRepo(conn).create("existing")
    SettingsRepo(conn).set("auto_create_note_on_launch", "false")
    state.load()
    assert state.count() == 1
    assert state.content == "existing"


def test_set_content_and_save_persists(tmp_path):
    state, conn = make(tmp_path)
    state.load()
    state.set_content("hello")
    state.save_current()
    assert NotesRepo(conn).list()[0].content == "hello"


def test_navigation_bounds_and_switch(tmp_path):
    state, _ = make(tmp_path)
    state.load()
    state.add()  # now 2 notes, index 1
    assert state.index == 1
    assert state.navigate(-1) is True
    assert state.index == 0
    assert state.navigate(-1) is False  # already at start


def test_add_appends_empty(tmp_path):
    state, _ = make(tmp_path)
    state.load()
    state.set_content("first")
    state.add()
    assert state.count() == 2
    assert state.content == ""


def test_remove_last_leaves_fresh_note(tmp_path):
    state, _ = make(tmp_path)
    state.load()
    state.remove_current()
    assert state.count() == 1
    assert state.content == ""
