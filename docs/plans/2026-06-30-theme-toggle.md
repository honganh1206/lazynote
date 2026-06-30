# Light/Dark Theme Toggle Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Let the user switch app appearance between light and dark, following the OS theme by default with a manual tray-menu override.

**Architecture:** Centralize all colors in a new pure `theme.py` module (palettes + OS-scheme resolution). `editormodel` resolves palette *keys* against a passed-in palette. `Backend` exposes the effective palette and theme mode to QML and persists the choice; QML binds colors to `backend.colors.*` and drives a tray Theme submenu.

**Tech Stack:** Python 3.12, PySide6 6.11 (Qt Quick / QML), pytest. OS detection via `QGuiApplication.styleHints().colorScheme()` / `colorSchemeChanged`.

---

## Design reference

See `docs/plans/2026-06-30-theme-toggle-design.md` for palette table and data flow.

Palette keys: `text, muted, amber, green, blue, bg, selection`.

| key       | dark      | light     |
|-----------|-----------|-----------|
| text      | `#d6d3cc` | `#2b2a27` |
| muted     | `#6f6b64` | `#9a948b` |
| amber     | `#e6a86b` | `#b9701f` |
| green     | `#84c08a` | `#3f8f47` |
| blue      | `#79b8e0` | `#2f7bb0` |
| bg        | `#1f2023` | `#f4f2ec` |
| selection | `#34363b` | `#d8d3c7` |

---

## Task 1: Pure theme module — palettes + scheme resolution

**Files:**
- Create: `src/lazynote/theme.py`
- Test: `tests/test_theme.py`

**Step 1: Write the failing test**

```python
# tests/test_theme.py
from __future__ import annotations

import lazynote.theme as theme

KEYS = {"text", "muted", "amber", "green", "blue", "bg", "selection"}


def test_palettes_have_same_keys():
    assert set(theme.PALETTES["dark"]) == KEYS
    assert set(theme.PALETTES["light"]) == KEYS


def test_dark_palette_matches_legacy_colors():
    d = theme.PALETTES["dark"]
    assert d["text"] == "#d6d3cc"
    assert d["muted"] == "#6f6b64"
    assert d["amber"] == "#e6a86b"
    assert d["green"] == "#84c08a"
    assert d["blue"] == "#79b8e0"


def test_resolve_scheme_explicit_modes_pass_through():
    assert theme.resolve_scheme("light", os_scheme="dark") == "light"
    assert theme.resolve_scheme("dark", os_scheme="light") == "dark"


def test_resolve_scheme_system_follows_os():
    assert theme.resolve_scheme("system", os_scheme="light") == "light"
    assert theme.resolve_scheme("system", os_scheme="dark") == "dark"


def test_resolve_scheme_unknown_mode_defaults_to_system():
    assert theme.resolve_scheme("", os_scheme="dark") == "dark"


def test_palette_for_returns_effective_dict():
    assert theme.palette_for("dark", os_scheme="light") == theme.PALETTES["dark"]
    assert theme.palette_for("system", os_scheme="light") == theme.PALETTES["light"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_theme.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'lazynote.theme'`

**Step 3: Write minimal implementation**

```python
# src/lazynote/theme.py
"""Theme palettes and color-scheme resolution.

Pure module (no PySide6) so it can be unit tested. The Backend passes the live
OS scheme in; this module owns the palette values and the system/override logic.
"""

from __future__ import annotations

PALETTES: dict[str, dict[str, str]] = {
    "dark": {
        "text": "#d6d3cc",
        "muted": "#6f6b64",
        "amber": "#e6a86b",
        "green": "#84c08a",
        "blue": "#79b8e0",
        "bg": "#1f2023",
        "selection": "#34363b",
    },
    "light": {
        "text": "#2b2a27",
        "muted": "#9a948b",
        "amber": "#b9701f",
        "green": "#3f8f47",
        "blue": "#2f7bb0",
        "bg": "#f4f2ec",
        "selection": "#d8d3c7",
    },
}


def resolve_scheme(mode: str, os_scheme: str = "dark") -> str:
    """Map a theme mode to a concrete scheme ("light"|"dark").

    `mode` is "system" | "light" | "dark" (anything else == "system").
    `os_scheme` is the OS-reported scheme, used only when following the system.
    """
    if mode in ("light", "dark"):
        return mode
    return "light" if os_scheme == "light" else "dark"


def palette_for(mode: str, os_scheme: str = "dark") -> dict[str, str]:
    return PALETTES[resolve_scheme(mode, os_scheme)]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_theme.py -v`
Expected: PASS (6 passed)

**Step 5: Commit**

```bash
git add src/lazynote/theme.py tests/test_theme.py
git commit -m "feat: add pure theme module with palettes and scheme resolution"
```

---

## Task 2: Make editormodel palette-aware

`_KIND_STYLE` currently bakes in color strings. Switch it to palette *keys* and
resolve against a palette passed into `line_render_spans` (default dark, so the
existing tests and call sites keep working).

**Files:**
- Modify: `src/lazynote/editormodel.py:21-38` (palette constants + `_KIND_STYLE`)
- Modify: `src/lazynote/editormodel.py:68-118` (`line_render_spans` signature + body)
- Test: `tests/test_editormodel.py` (add new test; existing must still pass)

**Step 1: Write the failing test**

Add to `tests/test_editormodel.py`:

```python
from lazynote.theme import PALETTES


def test_light_palette_changes_heading_color():
    r = line_render_spans("# Big", 0, -1, palette=PALETTES["light"])
    assert r.spans[0].color.lower() == "#b9701f"  # light amber


def test_default_palette_is_dark():
    r = line_render_spans("# Big", 0, -1)
    assert r.spans[0].color.lower() == "#e6a86b"  # dark amber
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_editormodel.py::test_light_palette_changes_heading_color -v`
Expected: FAIL — `TypeError: line_render_spans() got an unexpected keyword argument 'palette'`

**Step 3: Write minimal implementation**

In `src/lazynote/editormodel.py`, replace the palette block (lines 21-38). Keep
the module-level constants (other code/tests import them) but redefine
`_KIND_STYLE` in terms of keys:

```python
from lazynote.theme import PALETTES

# Legacy module-level constants (dark) kept for back-compat with existing imports.
TEXT = PALETTES["dark"]["text"]
MUTED = PALETTES["dark"]["muted"]
AMBER = PALETTES["dark"]["amber"]
GREEN = PALETTES["dark"]["green"]
BLUE = PALETTES["dark"]["blue"]

# Per-kind base style: (palette_key, italic, strike).
_KIND_STYLE: dict[str, tuple[str, bool, bool]] = {
    "heading1": ("amber", False, False),
    "heading2": ("green", False, False),
    "heading3": ("blue", False, False),
    "comment": ("muted", True, False),
    "keyword": ("muted", False, False),
    "checkbox_checked": ("muted", False, True),
    "checkbox_unchecked": ("text", False, False),
}
```

Update `line_render_spans` (line 68) signature and the two color resolutions:

```python
def line_render_spans(
    doc: str, line_index: int, cursor_line: int, palette: dict | None = None
) -> LineRender:
    if palette is None:
        palette = PALETTES["dark"]
    ...
    # seed defaults (was: colors = [TEXT] * n)
    colors = [palette["text"]] * n
    ...
    # link branch (was: colors[i] = BLUE)
    colors[i] = palette["blue"]
    ...
    # kind branch (was: color, italic, strike = style)
    key, italic, strike = style
    color = palette[key]
    for i in range(lo, hi):
        colors[i] = color
        italics[i] = italic
        strikes[i] = strike
```

**Step 4: Run tests to verify all pass**

Run: `pytest tests/test_editormodel.py -v`
Expected: PASS (existing dark-color assertions still hold + 2 new tests pass)

**Step 5: Commit**

```bash
git add src/lazynote/editormodel.py tests/test_editormodel.py
git commit -m "feat: make line_render_spans palette-aware (defaults to dark)"
```

---

## Task 3: Backend theme API + persistence

Expose effective palette + mode to QML, persist the choice, react to OS changes.

**Files:**
- Modify: `src/lazynote/bridge.py` (imports, signals, `__init__`, properties, slot, `line_render`)
- Test: `tests/test_bridge.py`

**Step 1: Write the failing test**

Inspect `tests/test_bridge.py` for the existing Backend fixture/QApplication
setup and reuse it. Add:

```python
def test_default_theme_is_system(backend):
    assert backend.theme == "system"


def test_set_theme_persists_and_updates(backend):
    backend.set_theme("light")
    assert backend.theme == "light"
    assert backend.colors["bg"] == "#f4f2ec"      # light bg
    assert backend.colors["text"] == "#2b2a27"


def test_set_theme_dark(backend):
    backend.set_theme("dark")
    assert backend.colors["bg"] == "#1f2023"
```

(If `test_bridge.py` has no shared `backend` fixture, add one mirroring the
existing setup — construct `Backend()` after a `QGuiApplication` exists.)

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_bridge.py -k theme -v`
Expected: FAIL — `AttributeError: 'Backend' object has no attribute 'theme'`

**Step 3: Write minimal implementation**

In `src/lazynote/bridge.py`:

Imports:
```python
from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication
from lazynote import store, theme
from lazynote.editormodel import line_render_spans
```

Add signal near the other signals:
```python
    themeChanged = Signal()
```

In `__init__`, after the save-timer setup, wire OS-scheme changes:
```python
        hints = QGuiApplication.styleHints()
        if hints is not None:
            hints.colorSchemeChanged.connect(self._on_os_scheme_changed)

    def _os_scheme(self) -> str:
        from PySide6.QtCore import Qt
        hints = QGuiApplication.styleHints()
        if hints is None:
            return "dark"
        return "light" if hints.colorScheme() == Qt.ColorScheme.Light else "dark"

    def _theme_mode(self) -> str:
        m = store.get_settings().get("theme")
        return m if m in ("system", "light", "dark") else "system"

    def _on_os_scheme_changed(self, _scheme) -> None:
        if self._theme_mode() == "system":
            self.themeChanged.emit()
            self.contentChanged.emit()
```

Properties + slot:
```python
    def _theme(self) -> str:
        return self._theme_mode()

    theme = Property(str, _theme, notify=themeChanged)

    def _colors(self) -> dict:
        return theme.palette_for(self._theme_mode(), self._os_scheme())

    colors = Property("QVariantMap", _colors, notify=themeChanged)

    @Slot(str)
    def set_theme(self, mode: str) -> None:
        if mode not in ("system", "light", "dark"):
            return
        store.get_settings().set("theme", mode)
        self.themeChanged.emit()
        self.contentChanged.emit()
```

Update `line_render` (line 164) to pass the effective palette:
```python
        pal = theme.palette_for(self._theme_mode(), self._os_scheme())
        lr = line_render_spans(self._state.content, line, cursor_line, palette=pal)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_bridge.py -v`
Expected: PASS (existing + 3 new)

**Step 5: Commit**

```bash
git add src/lazynote/bridge.py tests/test_bridge.py
git commit -m "feat: expose theme mode + effective palette from Backend"
```

---

## Task 4: QML binds colors + tray Theme submenu

No unit tests (QML); verify by running the app.

**Files:**
- Modify: `src/lazynote/qml/Editor.qml:20-21` (palette properties), `:248` (selectionColor)
- Modify: `src/lazynote/qml/Main.qml:91` (panel bg), `:120` (status muted), tray menu `:66-80`

**Step 1: Editor.qml — bind palette to backend**

Replace lines 20-21:
```qml
    readonly property color colText: backend.colors.text
    readonly property color colMuted: backend.colors.muted
```
Replace the `TextInput` `selectionColor` (line 248):
```qml
                    selectionColor: backend.colors.selection
```

**Step 2: Main.qml — bind panel + status colors**

Line 91 (panel `Rectangle.color`):
```qml
        color: backend.colors.bg
```
Line 120 (status `Text.color`):
```qml
            color: backend.colors.muted
```

**Step 3: Main.qml — tray Theme submenu**

Inside the tray `Platform.Menu` (after the Auto-hide item, before the final
separator/Quit), add:
```qml
            Platform.MenuSeparator {}
            Platform.Menu {
                title: "Theme"
                Platform.MenuItem {
                    text: "System"; checkable: true
                    checked: backend.theme === "system"
                    onTriggered: backend.set_theme("system")
                }
                Platform.MenuItem {
                    text: "Light"; checkable: true
                    checked: backend.theme === "light"
                    onTriggered: backend.set_theme("light")
                }
                Platform.MenuItem {
                    text: "Dark"; checkable: true
                    checked: backend.theme === "dark"
                    onTriggered: backend.set_theme("dark")
                }
            }
```

**Step 4: Run the app and verify**

Run: `python -m lazynote`
Verify:
- App launches in current OS appearance (System default).
- Tray → Theme → Light: bg goes near-white, text dark, headings recolor.
- Tray → Theme → Dark: returns to dark palette.
- Restart app: last choice persisted (Light stays light).
- Tray → Theme → System: matches OS; changing OS theme live updates the app.

**Step 5: Commit**

```bash
git add src/lazynote/qml/Editor.qml src/lazynote/qml/Main.qml
git commit -m "feat: bind QML colors to backend palette + add tray Theme submenu"
```

---

## Task 5: Full suite + final check

**Step 1: Run everything**

Run: `pytest -q`
Expected: all pass.

**Step 2: Manual smoke** — launch `python -m lazynote`, toggle all three theme modes once more, confirm no console errors.

**Step 3: Commit (if any cleanup)** — otherwise branch is ready for PR.
