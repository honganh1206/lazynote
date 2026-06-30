# Custom Font Selection Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Let the user choose the editor font family + size (global, monospace-only) from an in-app settings popup, persisted like the theme setting.

**Architecture:** A pure `fonts.py` helper owns defaulting/clamping (unit-tested, no Qt), mirroring `theme.py`. `Backend` exposes a reactive `font` QVariantMap property + `set_font` / `mono_families` slots (pattern A, mirrors `colors`). QML binds the three editor text sites to `backend.font`. A new `SettingsPopup.qml` (font dropdown + size stepper) is opened from a tray item and `Ctrl+,`.

**Tech Stack:** Python 3, PySide6 (QtQuick/QML, QFontDatabase), pytest.

Design doc: `docs/plans/2026-06-30-custom-font-design.md`.

---

### Task 1: Pure font helper (`fonts.py`)

**Files:**
- Create: `src/lazynote/fonts.py`
- Test: `tests/test_fonts.py`

**Step 1: Write the failing tests**

```python
# tests/test_fonts.py
from __future__ import annotations

import lazynote.fonts as fonts

AVAIL = ["DejaVu Sans Mono", "Hack", "Noto Sans Mono"]
DEFAULT = "DejaVu Sans Mono"


def test_valid_family_and_size_pass_through():
    assert fonts.resolve_font("Hack", 18, AVAIL, DEFAULT) == {
        "family": "Hack",
        "size": 18,
    }


def test_empty_family_uses_default():
    assert fonts.resolve_font("", 15, AVAIL, DEFAULT)["family"] == DEFAULT


def test_uninstalled_family_uses_default():
    assert fonts.resolve_font("Comic Mono", 15, AVAIL, DEFAULT)["family"] == DEFAULT


def test_size_clamped_low():
    assert fonts.resolve_font("Hack", 2, AVAIL, DEFAULT)["size"] == fonts.MIN_SIZE


def test_size_clamped_high():
    assert fonts.resolve_font("Hack", 999, AVAIL, DEFAULT)["size"] == fonts.MAX_SIZE


def test_bad_size_falls_back_to_default():
    assert fonts.resolve_font("Hack", "", AVAIL, DEFAULT)["size"] == fonts.DEFAULT_SIZE
    assert fonts.resolve_font("Hack", "abc", AVAIL, DEFAULT)["size"] == fonts.DEFAULT_SIZE
    assert fonts.resolve_font("Hack", None, AVAIL, DEFAULT)["size"] == fonts.DEFAULT_SIZE
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_fonts.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'lazynote.fonts'`

**Step 3: Write minimal implementation**

```python
# src/lazynote/fonts.py
"""Font defaulting + clamping.

Pure module (no PySide6) so it can be unit tested. The Backend passes the live
list of available families + the system default monospace in; this module owns
the fallback and clamp logic.
"""

from __future__ import annotations

MIN_SIZE = 8
MAX_SIZE = 32
DEFAULT_SIZE = 15


def _clamp_size(size) -> int:
    try:
        n = int(size)
    except (TypeError, ValueError):
        return DEFAULT_SIZE
    return max(MIN_SIZE, min(MAX_SIZE, n))


def resolve_font(
    family: str, size, available: list[str], default_family: str
) -> dict:
    """Return an effective {"family", "size"}.

    `family` falls back to `default_family` when empty or not in `available`.
    `size` is parsed to int (DEFAULT_SIZE on bad input) and clamped to range.
    """
    fam = family if family and family in available else default_family
    return {"family": fam, "size": _clamp_size(size)}
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_fonts.py -v`
Expected: PASS (6 passed)

**Step 5: Commit**

```bash
git add src/lazynote/fonts.py tests/test_fonts.py
git commit -m "feat: add pure font defaulting/clamping helper"
```

---

### Task 2: Backend font property + slots (`bridge.py`)

**Files:**
- Modify: `src/lazynote/bridge.py` — add `import`, signal (line ~28), font block after the theme block (after line 75)

**Step 1: Add the import**

In `src/lazynote/bridge.py`, update the imports:

- Line 14: `from lazynote import store, theme` → `from lazynote import fonts, store, theme`
- Line 12: add `QFontDatabase` to the `PySide6.QtGui` import:
  `from PySide6.QtGui import QDesktopServices, QFontDatabase, QGuiApplication`

**Step 2: Add the signal**

After line 28 (`themeChanged = Signal()`), add:

```python
    fontChanged = Signal()
```

**Step 3: Add the font block**

After the theme block (after `set_theme`, line 75), insert:

```python
    # ---- font ----
    def _default_family(self) -> str:
        return QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family()

    @Slot(result="QStringList")
    def mono_families(self) -> list[str]:
        mono = sorted(f for f in QFontDatabase.families() if QFontDatabase.isFixedPitch(f))
        return mono if mono else sorted(QFontDatabase.families())

    def _font(self) -> dict:
        s = store.get_settings()
        return fonts.resolve_font(
            s.get("font_family") or "",
            s.get("font_size"),
            self.mono_families(),
            self._default_family(),
        )

    font = Property("QVariantMap", _font, notify=fontChanged)

    @Slot(str, int)
    def set_font(self, family: str, size: int) -> None:
        s = store.get_settings()
        if family:
            s.set("font_family", family)
        s.set("font_size", str(fonts._clamp_size(size)))
        self.fontChanged.emit()
```

**Step 4: Verify nothing broke**

Run: `pytest -q`
Expected: PASS (existing suite still green; bridge import resolves).

Run: `python -c "import lazynote.bridge"`
Expected: no error.

**Step 5: Commit**

```bash
git add src/lazynote/bridge.py
git commit -m "feat: expose font property + set_font/mono_families on Backend"
```

---

### Task 3: Apply font in the editor (`Editor.qml`)

**Files:**
- Modify: `src/lazynote/qml/Editor.qml` — add `fnt` property (near line 20), update 3 text sites (`:183`, `:210`, `:257`)

**Step 1: Add the convenience binding**

After line 20 (`readonly property color colText: ...`), add:

```qml
    readonly property var fnt: backend ? backend.font : ({family: "", size: 15})
```

**Step 2: Update the checkbox glyph**

`Editor.qml:183` — replace `font.pixelSize: 15` with:

```qml
                font.family: root.fnt.family
                font.pixelSize: root.fnt.size
```

**Step 3: Update the static styled line**

`Editor.qml:210` (`rowText`) — replace `font.pixelSize: 15` with:

```qml
                font.family: root.fnt.family
                font.pixelSize: root.fnt.size
```

**Step 4: Update the editable raw line**

`Editor.qml:257` (`TextInput`) — replace `font.pixelSize: 15` with:

```qml
                    font.family: root.fnt.family
                    font.pixelSize: root.fnt.size
```

**Step 5: Verify**

Run: `python -m lazynote` (or the project run command)
Expected: app launches, text renders. Lines, checkbox glyph, and the editable
caret line all share one font/size. No visual regression with default settings.

**Step 6: Commit**

```bash
git add src/lazynote/qml/Editor.qml
git commit -m "feat: bind editor text to backend.font"
```

---

### Task 4: Settings popup (`SettingsPopup.qml`)

**Files:**
- Create: `src/lazynote/qml/SettingsPopup.qml`

Reference `src/lazynote/qml/SlashPicker.qml` for popup styling conventions
(colors pulled from `backend.colors`, radius, padding).

**Step 1: Create the popup**

```qml
// src/lazynote/qml/SettingsPopup.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: root
    modal: true
    focus: true
    padding: 14
    anchors.centerIn: Overlay.overlay

    background: Rectangle {
        color: backend ? backend.colors.bg : "#1f2023"
        border.color: backend ? backend.colors.selection : "#34363b"
        radius: 10
    }

    function apply() {
        backend.set_font(familyBox.currentText, sizeSpin.value)
    }

    ColumnLayout {
        spacing: 10

        Text {
            text: "Font"
            color: backend ? backend.colors.muted : "#6f6b64"
            font.pixelSize: 12
        }

        ComboBox {
            id: familyBox
            Layout.preferredWidth: 240
            model: backend ? backend.mono_families() : []
            Component.onCompleted: {
                var i = model.indexOf(backend.font.family)
                if (i >= 0) currentIndex = i
            }
            onActivated: root.apply()
        }

        RowLayout {
            spacing: 8
            Text {
                text: "Size"
                color: backend ? backend.colors.text : "#d6d3cc"
                font.pixelSize: 13
            }
            SpinBox {
                id: sizeSpin
                from: 8
                to: 32
                value: backend ? backend.font.size : 15
                onValueModified: root.apply()
            }
        }
    }
}
```

**Step 2: Verify it parses**

(Wired up + visually checked in Task 5 — no standalone test for QML here.)

**Step 3: Commit**

```bash
git add src/lazynote/qml/SettingsPopup.qml
git commit -m "feat: add settings popup with font family + size controls"
```

---

### Task 5: Wire popup into Main (`Main.qml`)

**Files:**
- Modify: `src/lazynote/qml/Main.qml` — tray item (near line 96), shortcut (near line 104), popup instance (near line 159)

**Step 1: Add the tray menu item**

In the tray `menu`, after the theme items (after line 95, before the
`MenuSeparator` at line 96), add:

```qml
            Platform.MenuSeparator {}
            Platform.MenuItem {
                text: "Settings…"
                onTriggered: { win.show(); win.raise(); win.requestActivate(); settings.open() }
            }
```

**Step 2: Add the shortcut**

After line 104 (`Shortcut { sequence: "Ctrl+D"; ... }`), add:

```qml
    Shortcut { sequence: "Ctrl+," ; onActivated: settings.open() }
```

**Step 3: Add the popup instance**

After the `SlashPicker { ... }` block (after line 168), add:

```qml
    SettingsPopup {
        id: settings
    }
```

**Step 4: Verify end-to-end**

Run: `python -m lazynote`
Expected:
- `Ctrl+,` (and tray "Settings…") opens the popup.
- Combo lists monospace families; size spinner 8–32.
- Changing family/size updates the editor text live.
- Reopen the app → choice persisted (`font_family` / `font_size` in settings).

**Step 5: Commit**

```bash
git add src/lazynote/qml/Main.qml
git commit -m "feat: open settings popup from tray and Ctrl+,"
```

---

### Task 6: Final verification

**Step 1: Full test suite**

Run: `pytest -q`
Expected: all green (includes new `tests/test_fonts.py`).

**Step 2: Manual smoke**

- Pick an installed font + size → restart → setting persists.
- Uninstalled/empty setting falls back to system monospace (no crash).

**Step 3: Commit (if any cleanup)**

```bash
git add -A
git commit -m "chore: custom font selection cleanup"
```
