# Antinote Qt Quick / PySide6 Port — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a native, sleek, animated Antinote in Python + PySide6 + QML with full feature parity to the Electron app, reusing the existing pure logic as a tested spec.

**Architecture:** Single-process `QApplication` + `QQmlApplicationEngine`. UI in QML (Qt Quick + Controls); a Python `bridge` QObject exposes notes/settings/url to QML. Syntax rendering driven by a Python port of `computeRanges` — first via a `QSyntaxHighlighter` on a `TextArea` (Option A milestone), then a custom QML editor (line model + styled delegates + overlay input) for real ☐/☑ + animation (Option B). SQLite via stdlib `sqlite3`. Tray via `Qt.labs.platform`, global hotkey via portal/X11 with graceful degrade. See `2026-06-30-qtquick-pyside6-port-design.md`.

**Tech Stack:** Python 3.12, PySide6 (Qt 6), QML, sqlite3 (stdlib), pytest. Packaging: Flatpak (KDE runtime) primary + .deb.

**Porting oracle:** the Electron app's pure tests are the spec. For each pure module, translate the TS test cases into pytest 1:1, then implement until green. Reference files in this repo:
- `app/renderer/src/lib/parse/{links,todo,mode}.ts` (+ `.test.ts`)
- `app/renderer/src/lib/editor/decorations.ts` (`computeRanges`) (+ `.test.ts`)
- `app/main/geometry.ts` (+ `geometry.test.ts`); `app/main/db.ts`, `store.ts`
- Design tokens: `app/renderer/src/lib/editor/theme.ts` (dark palette)

---

## Conventions
- New project lives separately (separate repo, or `native-qt/` subdir — confirm before Task 0.1). Paths below are project-root relative.
- TDD for pure modules (`parse/*`, `highlight.py`, `geometry.py`, `db.py`). QML/editor/tray/shortcut glue verified by running the app (manual smoke steps included).
- `ruff` lint/format, `pytest` tests, `mypy` optional.
- Commit per task (Conventional Commits).
- Verify PySide6/QML APIs against the installed Qt6 version, not memory.

## Text protocol (unchanged spec)
First line: `todo`/`todo:<title>` → todo mode; lone `/` → slash picker; else plain. Todo lines: `#/##/### ` heading, `//` comment, trailing `/x` checked (hidden + struck unless cursor on that line), else unchecked item. Plain: headings + text. URLs clickable both modes.

---

## Phase 0 — Scaffold

### Task 0.1: PySide6 + QML hello window
**Files:** `pyproject.toml`, `antinote_qt/__main__.py`, `antinote_qt/app.py`, `antinote_qt/qml/Main.qml`
1. Confirm repo placement.
2. `pyproject.toml`: deps `PySide6`; dev `pytest`, `ruff`. Document that small footprint wants system/Flatpak Qt, not bundled wheels.
3. venv + `pip install -e .[dev]`.
4. `app.py`: `QApplication` (Widgets-capable, needed for tray) + `QQmlApplicationEngine` loading `Main.qml` — a 400×400 window with a label.
5. `python -m antinote_qt` → window appears. Headless CI: a smoke that imports `app` and constructs the engine under `QT_QPA_PLATFORM=offscreen` without error.
6. **Commit:** `chore: scaffold pyside6 + qml app`

### Task 0.2: pytest + ruff config
**Files:** `pyproject.toml`, `tests/test_sanity.py`. Configure pytest/ruff; trivial passing test; `pytest` green. **Commit:** `chore: add pytest + ruff config`

---

## Phase 1 — Pure logic ports (TDD, TS tests as oracle)

(Identical algorithms to the Electron app; pure Python, no Qt imports — fully unit-tested.)

### Task 1.1: `parse/links.py` + tests
Translate `links.test.ts`; port `parseLinks` (regex `r'https?://[^\s()]+(?:\([^\s()]*\)[^\s()]*)*|https?://[^\s]+'`) → `LinkSegment` dataclasses. TDD. **Commit:** `feat: port link parser with tests`

### Task 1.2: `parse/todo.py` + tests
Translate `todo.test.ts`; port `parse_todo_lines`/`parse_plain_lines` + classifiers (heading `^(#{1,3}) `, `//` comment, trailing `/x` checked w/ `/x` stripped, else item, blank empty). TDD. **Commit:** `feat: port todo classifier with tests`

### Task 1.3: `parse/mode.py` + tests
Translate `mode.test.ts`; `REGISTERED_KEYWORDS=['todo']`, `detect_mode` (`^(\w+)(?::\s*(.*))?$`, lowercase, allowlist), `is_keyword_registered`. TDD. **Commit:** `feat: port mode detection with tests`

### Task 1.4: `highlight.py` (compute_ranges) + tests
Translate `decorations.test.ts` (`computeRanges`) incl. cursor-reveal both directions + absolute link offsets. Port `compute_ranges(doc, sel_head_line) -> list[Range]`, `Range(from_, to, kind)`, kinds `heading1/2/3, comment, keyword, checkbox_checked, checkbox_unchecked, link, hide_x`. Reuse `detect_mode`+`parse_links`; same offset math/precedence/keyword-line exclusion/cursor reveal. TDD. **Commit:** `feat: port highlight range computation with tests`

### Task 1.5: `geometry.py` + tests
Translate `geometry.test.ts`; `is_on_screen`, `parse_geometry` (clamp 360), mins. TDD. **Commit:** `feat: port geometry helpers with tests`

---

## Phase 2 — Database

### Task 2.1: `db.py` repos + migrations + tests
Mirror `db.test.ts` (temp-file DB). stdlib `sqlite3`: `open_db` (WAL, busy_timeout, `CREATE TABLE IF NOT EXISTS` exact schema, `INSERT OR IGNORE` seeds), `NotesRepo` (list/create(sort_index=MAX+1, ms timestamps, return row)/update/delete), `SettingsRepo` (get/set upsert), `Note` dataclass. Parameterized queries. TDD. **Commit:** `feat: sqlite db + settings repos with tests`

### Task 2.2: store init + legacy import
`init_store()`: dir from `QStandardPaths.writableLocation(AppConfigLocation)` → `~/.config/antinote-qt/`; mkdir; if new DB absent, copy from first existing legacy DB (Electron `~/.config/Antinote/notes.db`, then Tauri path); open + expose repos. **Commit:** `feat: store init + legacy db import`

---

## Phase 3 — Python↔QML bridge + state

### Task 3.1: `bridge.py` QObject
A `QObject` with slots/signals/properties exposing: `notes_list()`, `note_create`, `note_update`, `note_delete`, `setting_get/set`, `open_url(url)` (`QDesktopServices.openUrl`), and a `contentChanged`/`notesChanged` signal. Registered into the QML context (`engine.rootContext().setContextProperty('backend', bridge)` or `@QmlElement`). Wires to `notestate.py` + `db.py`. No unit test (Qt glue); construct under offscreen platform to confirm import. **Commit:** `feat: qml bridge object`

### Task 3.2: `notestate.py`
Port `noteState` (list/index/content, load-on-launch incl. `auto_create_note_on_launch`, navigate/add/remove) over `db.py`. Autosave: `QTimer` 500ms debounce; flush on quit/blur/navigation. Exposed through `bridge`. **Commit:** `feat: note state + debounced autosave`

---

## Phase 4 — Editor (Option A milestone)

### Task 4.1: `highlighter.py` + `Editor.qml` (TextArea)
1. `Editor.qml`: a `Flickable`+`TextArea` (wrapMode Wrap), dark palette, bundled font.
2. `highlighter.py`: `QSyntaxHighlighter` subclass attached to `TextArea.textDocument.textDocument`. Implement highlighting from `compute_ranges`: detect mode from the first block, track the cursor line (from TextArea `cursorPosition`), and on `highlightBlock` apply char formats for the ranges intersecting that block (offset by block position). For `hide_x`, apply a transparent foreground format (Option A limitation — full hide comes in Option B). For checked, strikethrough+dim; headings/comments/keyword/link colored.
3. On cursor move, `rehighlight()` (or affected blocks) so `/x` reveal updates.
4. Wire typing → `bridge` autosave; Ctrl+H/L/N/D shortcuts (`Shortcut` in QML) → bridge nav/new/delete; undo via TextArea.
5. Smoke: todo mode styling, headings, comments, `/x` dims off cursor line. **Commit:** `feat: editor via TextArea + syntax highlighter (option A)`

### Task 4.2: Clickable links (Option A)
Hit-test the `link` format/range at the click position (map cursor pos → range from `compute_ranges`) → `bridge.open_url`. Pointer cursor over links. Smoke: click URL → browser. **Commit:** `feat: clickable links in editor`

---

## Phase 5 — Window shell + slash picker

### Task 5.1: Frameless rounded translucent always-on-top window
`Main.qml` `Window` `flags: Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint`, `color:"transparent"`, 400×400, min 360. Root rounded `Rectangle` `#1f2023` with `MultiEffect` shadow. Top drag strip → `DragHandler`/`startSystemMove()`. Bottom-right `{mode} · n/m` indicator. Apply persisted `always_on_top`. **Commit:** `feat: frameless rounded always-on-top window`

### Task 5.2: `SlashPicker.qml` (animated)
When the first line is exactly `/`, show an animated `Popup` listing `REGISTERED_KEYWORDS` (↑/↓/Enter/Esc/number); on select, replace the first line with the keyword (preserve rest), refocus editor. Entry/exit `Transition`s. Smoke: `/` → picker; Enter inserts `todo`. **Commit:** `feat: animated slash picker`

---

## Phase 6 — Tray

### Task 6.1: `Qt.labs.platform` SystemTrayIcon + Menu
QML `SystemTrayIcon` with a `Menu`: Show/Hide, New Note, separator, Toggle Always-on-Top, Toggle Auto-hide, separator, Quit. Actions call `backend`. Requires `QApplication`. Degrade if unavailable. Smoke: each item works. **Commit:** `feat: system tray (Qt.labs.platform)`

---

## Phase 7 — Global shortcut

### Task 7.1: Alt+A via portal (+ X11 fallback)
`shortcuts.py`: bind Alt+A → toggle window via `org.freedesktop.portal.GlobalShortcuts` (DBus); on X11, optional X11 grab; else warn + rely on tray. Smoke (best-effort). **Commit:** `feat: global shortcut Alt+A with graceful degrade`

---

## Phase 8 — Geometry & auto-hide

### Task 8.1: Geometry persistence
Track window x/y/width/height; debounce 500ms → `setting_set('window_geometry', json)`. On startup `parse_geometry`+`is_on_screen` (against `QScreen` geometry) before applying. Uses tested `geometry.py`. Smoke: move/resize, restart, restored; off-screen ignored. **Commit:** `feat: window geometry persistence`

### Task 8.2: Auto-hide on blur
On window active→false, if `auto_hide_on_blur=='true'`, `QTimer.singleShot(300, hide)`; cancel on focus. Toggle via tray. Smoke. **Commit:** `feat: auto-hide on blur`

---

## Phase 9 — Editor Option B (bespoke, animated)

> The premium look: real ☐/☑, true `/x` hide, animated checks. Replaces Option A's display layer; keeps `compute_ranges`.

### Task 9.1: `editormodel.py` line model
`QAbstractListModel` exposing per-line role data (text, kind/colors, checked, isCursorLine, segments incl. links) computed from the document text + cursor line via `compute_ranges`. Unit-testable in part (the role computation). **Commit:** `feat: editor line model`

### Task 9.2: Custom editor delegate + overlay input
`Editor.qml` (B): a `ListView` of styled line delegates (colors, strikethrough, real `☐/☑` items, `/x` not drawn off cursor line, link spans) with a transparent `TextEdit` capturing input synced to the model; coordinate caret/selection/scroll. Tap a checkbox → toggle `/x` with a check **animation**. Smoke: full Antinote-like rendering + editing. **Commit:** `feat: bespoke animated editor (option B)`

### Task 9.3: Motion polish
Window show/hide fade+scale `Behavior`s, note-switch slide, caret/selection easing, slash-picker spring. Smoke. **Commit:** `feat: motion polish`

---

## Phase 10 — Packaging & docs

### Task 10.1: Flatpak (KDE runtime)
`data/com.honganh.antinote-qt.yml`, `.desktop`, icons, AppStream metainfo. KDE 6 runtime (Qt6/PySide6); finish-args for portals (GlobalShortcuts), tray, config dir. Build→install→run. **Commit:** `build: flatpak packaging`

### Task 10.2: .deb
Depends on `python3-pyside6.*`. Tiny package; smoke install. **Commit:** `build: deb packaging`

### Task 10.3: CI + README
CI: install Qt6/PySide6, run `ruff`+`pytest` on PRs (offscreen platform for any Qt construction); build Flatpak/.deb on `v*` tags → draft release. README: deps, run, build. **Commit:** `ci+docs: test on PR, package on tag`

---

## Done criteria
- `pytest` green (links, todo, mode, highlight, geometry, db — mirrors of the TS suites).
- App runs; parity features work; Option B editor renders ☐/☑ with animated checks and real `/x` hide.
- Flatpak + .deb build; legacy notes import on first launch.
- Footprint a fraction of Electron (with system/Flatpak Qt).

## Feature parity checklist
- [ ] Multi-note nav (Ctrl+H/L), new (Ctrl+N), delete (Ctrl+D, confirm non-empty), `n/m` counter
- [ ] Debounced 500ms autosave; restart persists
- [ ] Alt+A toggle (portal/X11; degrade on Wayland-no-portal)
- [ ] Tray: show/hide, new note, toggle always-on-top, toggle auto-hide, quit
- [ ] Frameless, rounded, translucent, always-on-top, resizable, geometry persisted + on-screen guard
- [ ] auto_create_note_on_launch + auto_hide_on_blur
- [ ] Todo mode: ☐/☑ (animated), `/x` checked+struck+hidden, reveal on cursor line, `#`/`//` styling
- [ ] Plain mode headings; clickable links both modes
- [ ] Slash picker on lone `/` (animated)
- [ ] Legacy notes.db imported on first launch
- [ ] Dark theme + motion matching the Antinote feel
