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


def _make_backend(tmp_path, monkeypatch):
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
    return b


def test_default_theme_is_system(tmp_path, monkeypatch):
    b = _make_backend(tmp_path, monkeypatch)
    assert b.property("theme") == "system"


def test_set_theme_persists_and_updates(tmp_path, monkeypatch):
    b = _make_backend(tmp_path, monkeypatch)
    b.set_theme("light")
    assert b.property("theme") == "light"
    colors = b.property("colors")
    assert colors["bg"] == "#f4f2ec"
    assert colors["text"] == "#2b2a27"


def test_set_theme_dark(tmp_path, monkeypatch):
    b = _make_backend(tmp_path, monkeypatch)
    b.set_theme("dark")
    assert b.property("colors")["bg"] == "#1f2023"


def test_effective_scheme_follows_explicit_mode(tmp_path, monkeypatch):
    b = _make_backend(tmp_path, monkeypatch)
    # Offscreen OS scheme resolves to "dark", so system → dark.
    assert b.property("effectiveScheme") == "dark"
    b.set_theme("light")
    assert b.property("effectiveScheme") == "light"
    b.set_theme("dark")
    assert b.property("effectiveScheme") == "dark"


def test_toggle_theme_from_system_picks_opposite_of_effective(tmp_path, monkeypatch):
    b = _make_backend(tmp_path, monkeypatch)
    # Default theme is "system"; offscreen OS scheme resolves to "dark",
    # so the first toggle flips to "light" (an explicit override).
    b.toggle_theme()
    assert b.property("theme") == "light"
    assert b.property("effectiveScheme") == "light"


def test_toggle_theme_flips_light_and_dark(tmp_path, monkeypatch):
    b = _make_backend(tmp_path, monkeypatch)
    b.set_theme("light")
    b.toggle_theme()
    assert b.property("theme") == "dark"
    b.toggle_theme()
    assert b.property("theme") == "light"


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
