import os


def test_init_store_creates_db_and_seeds(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    # Import after env is set so QStandardPaths resolves the temp config dir.
    from antinote_qt import store

    store.init_store()
    assert (tmp_path / "antinote-qt" / "notes.db").exists()
    assert store.get_settings().get("always_on_top") == "true"
    note = store.get_notes().create("hi")
    assert note.content == "hi"
    assert store.config_dir() == tmp_path / "antinote-qt"
