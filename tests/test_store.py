def test_init_store_creates_db_and_seeds(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from antinote_qt import store

    monkeypatch.setattr(store, "_LEGACY_DB_PATHS", [])
    store.init_store()
    assert (tmp_path / "antinote-qt" / "notes.db").exists()
    assert store.get_settings().get("always_on_top") == "true"
    note = store.get_notes().create("hi")
    assert note.content == "hi"
    assert store.config_dir() == tmp_path / "antinote-qt"


def test_imports_legacy_db_on_first_launch(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from antinote_qt import store
    from antinote_qt.db import NotesRepo, open_db

    # Build a fake legacy DB with one note, then close it so WAL is checkpointed
    # into the main file before we copy it.
    legacy = tmp_path / "legacy.db"
    legacy_conn = open_db(str(legacy))
    NotesRepo(legacy_conn).create("from old app")
    legacy_conn.close()
    monkeypatch.setattr(store, "_LEGACY_DB_PATHS", [legacy])

    store.init_store()
    contents = [n.content for n in store.get_notes().list()]
    assert "from old app" in contents
