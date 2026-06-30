# Antinote GTK4 + Python Port — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a native Linux Antinote in Python + GTK4 with full feature parity to the Electron app, reusing the existing pure logic as a tested spec.

**Architecture:** Single-process Gtk.Application. A `GtkTextView` + `GtkTextTag` table renders the syntax modes by applying tags computed from a Python port of `computeRanges`. SQLite via stdlib `sqlite3`. Tray via AyatanaAppIndicator3, global hotkey via the GlobalShortcuts portal, both degrading gracefully. See the design doc `2026-06-30-gtk4-python-port-design.md`.

**Tech Stack:** Python 3.12, PyGObject (gi), GTK 4, sqlite3 (stdlib), pytest. Optional: gtk4-layer-shell, libadwaita. Packaging: Flatpak (primary) + .deb.

**Porting oracle:** The Electron app's pure tests are the behavioral spec. For each pure module, translate the existing TS test cases into pytest 1:1, then implement until green. Reference files in the Electron repo:
- `app/renderer/src/lib/parse/{links,todo,mode}.ts` (+ `.test.ts`)
- `app/renderer/src/lib/editor/decorations.ts` (`computeRanges`) (+ `.test.ts`)
- `app/main/geometry.ts` (+ `geometry.test.ts`)
- `app/main/db.ts` (schema) and `app/main/store.ts` (old-DB copy)

---

## Conventions

- New project lives in a separate location (separate repo, or `native-gtk/` subdir — confirm placement before Task 0.1). Paths below are relative to the project root.
- TDD for every pure module (`parse/*`, `highlight.py`, `geometry.py`, `db.py`). UI/IO glue (window, editor widget, tray, shortcut) is verified by running the app — manual smoke steps included.
- `ruff` for lint/format, `pytest` for tests, `mypy` (optional) for types.
- Commit after each task. Conventional Commits.
- GTK/PyGObject docs: prefer the official PyGObject + GTK4 API reference; verify widget APIs against the installed version rather than memory.

## Text protocol (unchanged — the spec)

First line decides the mode: `todo`/`todo: <title>` → todo mode; lone `/` → slash picker; else plain. Todo lines: `#/##/### ` heading, `//` comment, trailing `/x` checked (hidden + struck unless the cursor is on that line), else unchecked checklist item. Plain: headings + text. URLs clickable in both. (Identical to the Electron app.)

---

## Phase 0 — Project scaffold

### Task 0.1: Python project + GTK4 hello window

**Files:** `pyproject.toml`, `antinote_gtk/__main__.py`, `antinote_gtk/app.py`, `tests/`

**Steps:**
1. Confirm repo placement (separate repo vs `native-gtk/` subdir).
2. Create `pyproject.toml` (project metadata; deps: `PyGObject`; dev: `pytest`, `ruff`, `mypy`). Note: PyGObject needs system GTK4 dev libs — document in README (`gir1.2-gtk-4.0`, `libgirepository1.0-dev`, `python3-gi`).
3. Create a venv, `pip install -e .[dev]`.
4. `app.py`: a minimal `Gtk.Application` (`application_id='com.honganh.antinote-gtk'`) that opens a `Gtk.ApplicationWindow` titled "Antinote" with a label.
5. `__main__.py`: `from .app import main; main()`.
6. Run `python -m antinote_gtk` → a window appears. (Headless CI can't show it; verify it constructs without error via a smoke that instantiates the app and calls `do_activate` under `Gtk.init()` or skips on no-display.)
7. **Commit:** `chore: scaffold gtk4 python app`

### Task 0.2: pytest + ruff config

**Files:** `pyproject.toml` (tool sections), `tests/test_sanity.py`

Configure `[tool.pytest.ini_options]` (`testpaths=tests`), `[tool.ruff]`. Add a trivial passing test. Run `pytest`. **Commit:** `chore: add pytest + ruff config`

---

## Phase 1 — Pure logic ports (TDD, TS tests as oracle)

### Task 1.1: `parse/links.py`

**Files:** `antinote_gtk/parse/links.py`, `tests/test_links.py`

1. Translate `links.test.ts` cases into pytest (plain text → one text segment; URL extraction; balanced parens `A_(b)`; empty → `[]`).
2. Run → fail.
3. Port `parseLinks`: same regex `r'https?://[^\s()]+(?:\([^\s()]*\)[^\s()]*)*|https?://[^\s]+'`, returning a list of dicts/dataclasses `LinkSegment(type, value, display_value, full_url)`.
4. Run → pass. **Commit:** `feat: port link parser with tests`

### Task 1.2: `parse/todo.py`

**Files:** `antinote_gtk/parse/todo.py`, `tests/test_todo.py`

Translate `todo.test.ts`. Port `parse_todo_lines` / `parse_plain_lines` + `classify_line` / `classify_plain_line` (heading `^(#{1,3}) `, `//` comment, trailing `/x` checked with the `/x` stripped from text, else item; blank → empty). Dataclass `ParsedLine(type, text, heading_level)`. TDD red→green. **Commit:** `feat: port todo classifier with tests`

### Task 1.3: `parse/mode.py`

**Files:** `antinote_gtk/parse/mode.py`, `tests/test_mode.py`

Translate `mode.test.ts`. `REGISTERED_KEYWORDS = ['todo']`; `detect_mode(content)` → `{'keyword','title'}` or `None` using `^(\w+)(?::\s*(.*))?$`, lowercase, allowlist. `is_keyword_registered`. TDD. **Commit:** `feat: port mode detection with tests`

### Task 1.4: `highlight.py` (port of computeRanges)

**Files:** `antinote_gtk/highlight.py`, `tests/test_highlight.py`

1. Translate `decorations.test.ts` (`computeRanges`) cases into pytest, including the cursor-reveal both-directions cases and absolute link offsets.
2. Port `compute_ranges(doc: str, sel_head_line: int) -> list[Range]` where `Range(from_, to, kind)` and `kind` ∈ `heading1/2/3, comment, keyword, checkbox_checked, checkbox_unchecked, link, hide_x`. Reuse `detect_mode` + `parse_links`. Same line-offset math (account for `\n`), same precedence (heading→comment→checked→unchecked), same keyword-line link exclusion, same cursor-reveal rule.
3. Run → pass. (Only the pure range computation is ported here; applying tags to a buffer is Task 3.x.) **Commit:** `feat: port highlight range computation with tests`

### Task 1.5: `geometry.py`

**Files:** `antinote_gtk/geometry.py`, `tests/test_geometry.py`

Translate `geometry.test.ts`. `is_on_screen(g, m)` (≥50px overlap both axes), `parse_geometry(raw)` (JSON, validate, clamp to 360 mins), `MIN_WIDTH/MIN_HEIGHT`. TDD. **Commit:** `feat: port geometry helpers with tests`

---

## Phase 2 — Database

### Task 2.1: `db.py` repos + migrations + tests

**Files:** `antinote_gtk/db.py`, `tests/test_db.py`

1. Tests (mirror `db.test.ts`) against a temp-file DB: create/list ordered by sort_index; update content; delete; settings seed defaults + round-trip.
2. Implement with stdlib `sqlite3`:
   - `open_db(path)`: connect, `PRAGMA journal_mode=WAL`, `PRAGMA busy_timeout=3000`, `CREATE TABLE IF NOT EXISTS` for `notes` and `app_settings` (exact schema from `migrations.rs`), `INSERT OR IGNORE` seeds (`auto_create_note_on_launch='true'`, `always_on_top='true'`). Return connection.
   - `NotesRepo(conn)`: `list()`, `create(content='')` (sort_index = MAX+1, `int(time.time()*1000)` timestamps, return row), `update(id, content)`, `delete(id)`.
   - `SettingsRepo(conn)`: `get(key)->str|None`, `set(key, value)` upsert.
   - `Note` dataclass matching the schema. Use parameterized queries only.
3. Run → pass. **Commit:** `feat: sqlite db + settings repos with tests`

### Task 2.2: store/init + old-DB migration

**Files:** `antinote_gtk/db.py` (or `store.py`)

`init_store()`: dir = `GLib.get_user_config_dir()/antinote-gtk`; `mkdir -p`; if new DB absent, copy from the first existing legacy DB (`~/.config/Antinote/notes.db` (Electron) or `~/.config/com.honganh.antinote-linux/notes.db` (Tauri)); open and expose repos. No unit test (filesystem/XDG). **Commit:** `feat: store init + legacy db import`

---

## Phase 3 — Editor widget (GtkTextView + tags)

### Task 3.1: Tag table + apply-tags renderer

**Files:** `antinote_gtk/editor.py`

1. Build a `Gtk.TextView` (wrap=WORD_CHAR) with a `Gtk.TextBuffer`. Create a `Gtk.TextTag` per kind in the buffer's tag table: `h1/h2/h3` (foreground), `comment` (foreground+style italic), `keyword` (foreground), `checked` (foreground+strikethrough), `link` (foreground+underline), `hidex` (`invisible=True`). Colors from the dark palette (design tokens).
2. `retag()`: clear all tags over the full buffer, compute `cursor_line` from the insert mark's line, call `compute_ranges(text, cursor_line)`, and for each range `apply_tag_by_name` over `get_iter_at_offset(from)`..`(to)`. For `checkbox_*` kinds, insert the `☐`/`☑` glyph — **first pass:** prepend the glyph as a non-editable visual via a leading tag/marker, OR use a `GtkTextChildAnchor` (decide during impl; text glyph is simplest). For `hide_x`, apply the `hidex` invisible tag over the `/x`.
3. Re-run `retag()` on buffer `changed` and on `notify::cursor-position` (cursor move drives the `/x` reveal). Debounce/coalesce if needed.
4. Smoke: type `todo:` then lines with `/x`, headings, comments → verify styling and that `/x` hides off the cursor line and shows on it. **Commit:** `feat: gtk text editor with tag-based highlighting`

### Task 3.2: Clickable links

**Files:** `antinote_gtk/editor.py`

Add a `Gtk.GestureClick`; on press, map widget coords → buffer iter (`get_iter_at_location`); if the iter has the `link` tag, expand to the tag's run, slice the URL text, and open via `Gio.AppInfo.launch_default_for_uri(url, None)`. Change cursor to pointer over links (optional). Smoke: click a URL → browser opens. **Commit:** `feat: clickable links in editor`

### Task 3.3: Editor keybindings

**Files:** `antinote_gtk/editor.py`

Add a `Gtk.ShortcutController` (or key event handler) for Ctrl+H/L/N/D → emit signals/callbacks (prev/next/new/delete), matching the Electron keymap. Ctrl+Z/Y already provided by GtkTextView undo (`buffer.set_enable_undo(True)`). **Commit:** `feat: editor navigation keybindings`

---

## Phase 4 — Window shell

### Task 4.1: Frameless rounded always-on-top window

**Files:** `antinote_gtk/window.py`, `antinote_gtk/style.css`

1. `Gtk.ApplicationWindow`, `set_decorated(False)`, default 400×400, min 360×360 (`set_size_request`). Load `style.css` via `Gtk.CssProvider`; style a root box with `background:#1f2023; border-radius:10px;` and the window background transparent.
2. Top drag strip wrapped in `Gtk.WindowHandle`. Editor fills the rest.
3. Always-on-top: on X11 set `_NET_WM_STATE_ABOVE`; on Wayland use `gtk4-layer-shell` (overlay, anchored) if available — else degrade (no always-on-top) and log. Apply persisted `always_on_top`.
4. Bottom-right position/mode indicator label (`{mode} · n/m`), updated from note state.
5. Smoke: frameless, rounded, on top, draggable. **Commit:** `feat: frameless rounded always-on-top window`

### Task 4.2: Slash picker popover

**Files:** `antinote_gtk/slashpicker.py`, `antinote_gtk/window.py`

When the first line is exactly `/`, show a `Gtk.Popover` (or overlay) listing `REGISTERED_KEYWORDS` with ↑/↓/Enter/Esc/number selection; on select, replace the first line with the keyword (preserve the rest) and refocus the editor. Hidden otherwise. Smoke: type `/` → picker; Enter inserts `todo`. **Commit:** `feat: slash picker popover`

---

## Phase 5 — State, autosave, navigation

### Task 5.1: Note state + autosave

**Files:** `antinote_gtk/notestate.py`

Port `noteState` logic (notes list, current index, content, load-on-launch incl. `auto_create_note_on_launch`, navigation, add, remove) over the `db.py` repos. Autosave: `GLib.timeout_add(500, …)` debounce on buffer change, flush on quit/blur/navigation. Wire to the editor + window. Smoke: type, restart, persists; nav/new/delete work; counter updates. **Commit:** `feat: note state + debounced autosave`

---

## Phase 6 — Tray

### Task 6.1: AppIndicator tray + menu

**Files:** `antinote_gtk/tray.py`

Use `gi.require_version('AyatanaAppIndicator3', '0.1')`. Create an indicator with a `Gtk.PopoverMenu`/`Gio.Menu` of: Show/Hide (toggle here), New Note, separator, Toggle Always-on-Top, Toggle Auto-hide, separator, Quit. Wire actions to the window/state (no IPC needed — direct calls). If the indicator lib is unavailable, log and continue (no tray). Smoke: each item works. **Commit:** `feat: system tray via ayatana appindicator`

---

## Phase 7 — Global shortcut

### Task 7.1: Alt+A via GlobalShortcuts portal (+ X11 fallback)

**Files:** `antinote_gtk/shortcuts.py`

Try the `org.freedesktop.portal.GlobalShortcuts` portal (DBus) to bind Alt+A → toggle window; on X11 session, optionally fall back to an X11 key grab. If neither is available (Wayland, no portal), log a warning and rely on the tray. Smoke (best-effort): Alt+A toggles where supported. **Commit:** `feat: global shortcut Alt+A with graceful degrade`

---

## Phase 8 — Geometry & auto-hide

### Task 8.1: Geometry persistence

**Files:** `antinote_gtk/window.py`

On move/resize (GTK4: track via `notify::default-width/height` and a saved position; note GTK4 limits direct window position on Wayland — persist size always, position where the platform allows), debounce 500ms → `settings.set('window_geometry', json)`. On startup, `parse_geometry` + `is_on_screen` against the monitor (`Gdk.Display.get_monitors`) before applying. Uses the tested `geometry.py`. Smoke: move/resize, restart, restored; off-screen ignored. **Commit:** `feat: window geometry persistence`

### Task 8.2: Auto-hide on blur

**Files:** `antinote_gtk/window.py`

On window `notify::is-active` → False, if `auto_hide_on_blur=='true'`, `GLib.timeout_add(300, hide)`; cancel on focus. Toggled via tray. Smoke: enable, click away → hides; disable → stays. **Commit:** `feat: auto-hide on blur`

---

## Phase 9 — Packaging & docs

### Task 9.1: Flatpak manifest + desktop file + icon

**Files:** `data/com.honganh.antinote-gtk.yml` (flatpak-builder manifest), `data/com.honganh.antinote-gtk.desktop`, `data/icons/…`, AppStream metainfo.

Manifest: GNOME runtime, build the Python module, finish-args for `--talk-name` portals (GlobalShortcuts), tray, and config dir access. `flatpak-builder` build → install → run. Smoke: notes persist, tray works, hotkey via portal. **Commit:** `build: flatpak packaging`

### Task 9.2: .deb packaging

**Files:** `debian/` or an `fpm`/`dpkg-deb` script.

Depends on `python3-gi`, `gir1.2-gtk-4.0`, `gir1.2-ayatanaappindicator3-0.1`, `gtk4-layer-shell`. Build a tiny .deb. Smoke install on a clean-ish box. **Commit:** `build: deb packaging`

### Task 9.3: CI + README

**Files:** `.github/workflows/*.yml`, `README.md`

CI: install GTK4 + PyGObject deps, run `ruff` + `pytest` on PRs; build Flatpak/.deb on `v*` tags → draft release. README: deps, run, build. **Commit:** `ci+docs: test on PR, package on tag`

---

## Done criteria

- `pytest` green (links, todo, mode, highlight, geometry, db — mirrors of the TS suites).
- App runs; all parity features work (editor modes, links, multi-note, autosave, tray, Alt+A where supported, frameless/always-on-top, geometry, auto-hide).
- Flatpak + .deb build; legacy notes import on first launch.
- Binary/install footprint a fraction of the Electron build.

## Feature parity checklist

- [ ] Multi-note nav (Ctrl+H/L), new (Ctrl+N), delete (Ctrl+D, confirm on non-empty), `n/m` counter
- [ ] Debounced 500ms autosave; restart persists
- [ ] Alt+A toggle (portal/X11; degrade on Wayland-no-portal)
- [ ] Tray: show/hide, new note, toggle always-on-top, toggle auto-hide, quit
- [ ] Frameless, rounded, transparent-ish, always-on-top, resizable, geometry persisted + on-screen guard
- [ ] auto_create_note_on_launch + auto_hide_on_blur
- [ ] Todo mode: ☐/☑, `/x` checked+struck, reveal `/x` on cursor line, `#`/`//` styling
- [ ] Plain mode headings; clickable links both modes
- [ ] Slash picker on lone `/`
- [ ] Legacy notes.db imported on first launch
- [ ] Dark theme matching the Antinote first pass
```
