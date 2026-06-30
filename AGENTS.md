# Lazynote — Agent Context

## Project Overview

Lazynote is a lightweight, always-accessible **native Linux** scratchpad (inspired
by Antinote). Built with **Python + PySide6 (Qt 6) + QML (Qt Quick)**. Single
frameless window.

A previous Electron+TypeScript implementation existed and was **removed** in favor
of this native port (it remains in git history if a TS reference is needed —
`git log` / `git show <old-sha>:app/...`). Do NOT reintroduce Electron/Node code.

## Tech Stack

- **Python 3.12+**, **PySide6 (Qt 6)**, UI in **QML** (Qt Quick + Controls)
- **sqlite3** (stdlib) for storage — no native build
- **pytest** for the pure logic; **ruff** for lint/format
- Tray via `Qt.labs.platform`; packaging via Flatpak (KDE runtime) + .deb

## Layout (src layout)

```
src/lazynote/
  __main__.py        # python -m lazynote
  app.py             # QApplication + QQmlApplicationEngine (create_engine() for smoke tests)
  qml/               # Main.qml, Editor.qml (Option A), EditorB.qml (default), SlashPicker.qml
  bridge.py          # QObject exposed to QML (notes/settings/open-url/editor)
  highlight.py       # PURE: compute_ranges — TESTED
  editormodel.py     # PURE-ish: per-line render spans for the bespoke editor — TESTED
  parse/             # PURE: links.py, todo.py, mode.py — TESTED
  notestate.py       # notes list/index/content — TESTED
  db.py              # sqlite3 repos + migrations — TESTED
  store.py           # config dir (~/.config/lazynote) + legacy import
  geometry.py        # PURE: is_on_screen / parse_geometry — TESTED
  shortcuts.py       # Alt+A global hotkey (X11 grab, degrades)
tests/               # pytest
data/                # .desktop, AppStream metainfo, Flatpak manifest
docs/plans/          # design + implementation plan (the spec)
pyproject.toml
```

## How to run / test

```bash
pip install -e .[dev]
lazynote                                    # run (needs a display); or: python -m lazynote
QT_QPA_PLATFORM=offscreen python -m lazynote   # headless smoke (won't show UI)
QT_QPA_PLATFORM=offscreen pytest -q          # tests
ruff check .                                 # lint
```

For headless construction of QML/Qt objects in CI or smoke tests, set
`QT_QPA_PLATFORM=offscreen`. `app.create_engine()` builds the engine without
entering the event loop, for exactly this.

## Conventions

- **TDD for pure modules** (`parse/*`, `highlight.py`, `geometry.py`, `db.py`).
  The old TypeScript tests are the behavioral oracle — translate their cases 1:1
  into pytest, then implement. The exact rules/regexes are in
  `docs/plans/2026-06-30-qtquick-pyside6-port.md`.
- QML/editor/tray/shortcut glue is verified by running the app (offscreen smoke
  for headless).
- Pure modules must NOT import PySide6 (keeps them unit-testable under plain pytest).
- Commit per task; Conventional Commits. Don't `git add -A` blindly — stage the
  files you changed.
- Verify PySide6/QML APIs against the installed Qt 6 version, not memory.

## Text Protocol (the editor spec — unchanged from the original app)

First line decides the mode:
- `todo` / `todo: <title>` → todo mode. Lines: `#`/`##`/`### ` heading; `//` comment;
  trailing `/x` = checked (hidden + struck unless the cursor is on that line); else
  an unchecked checklist item.
- a lone `/` on line 1 → slash picker (insert a keyword).
- otherwise → plain mode: headings + plain text.
URLs are clickable in both modes.

## Data

SQLite, schema `notes` + `app_settings`. DB at `~/.config/lazynote/notes.db`.
On first launch, import from a legacy DB if present (`~/.config/Antinote/notes.db`
or `~/.config/com.honganh.antinote-linux/notes.db`).

## Window / features

400×400 default, 360 min, frameless, translucent, rounded, always-on-top
(persisted), resizable, geometry persisted with on-screen guard. Global hotkey
Alt+A (via desktop portal / X11; degrades on Wayland-without-portal). Tray menu:
show/hide, new note, toggle always-on-top, toggle auto-hide, quit. Auto-hide on
blur. Debounced 500ms autosave.
