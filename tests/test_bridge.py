def test_backend_load_edit_flush(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from lazynote import store
    from lazynote.bridge import Backend

    monkeypatch.setattr(store, "_LEGACY_DB_PATHS", [])
    QApplication.instance() or QApplication([])
    store.init_store()

    b = Backend()
    b.load()
    b.edit("hello world")
    b.flush()

    assert store.get_notes().list()[-1].content == "hello world"
    assert b.property("count") == 1
    assert b.property("mode") == ""


def test_backend_slash_and_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from lazynote import store
    from lazynote.bridge import Backend

    monkeypatch.setattr(store, "_LEGACY_DB_PATHS", [])
    QApplication.instance() or QApplication([])
    store.init_store()

    b = Backend()
    b.load()
    b.edit("/")
    b.slash_select("todo")
    assert b.property("content") == "todo"
    assert b.property("mode") == "todo"
