# Antinote — GTK4 + Python native port design

**Date:** 2026-06-30
**Status:** Design (not yet approved for implementation)

## Goal

A second, **native Linux** implementation of Antinote with a small footprint and
no Chromium/Electron. Same features, same text protocol, same on-disk data. This
is a **from-scratch parallel app**, not a refactor of the Electron build.

## Motivation & trade-offs

| | Electron (current) | GTK4 + Python (this) |
|---|---|---|
| Binary / install | ~120 MB AppImage, ~100 MB RAM idle | a few MB of code; shares system GTK or a Flatpak runtime; ~30–60 MB RSS |
| Language | TypeScript | **Python (leaves TS)** |
| Editor | CodeMirror 6 | GtkTextView + tag table |
| Native feel | Chromium webview | real GTK widgets, system theme |
| Global hotkey (Wayland) | broken without portal | broken without portal (**same limit**) |
| Effort | done | **full rewrite** |

Accept this only if small/native is a hard requirement. The valuable, language-
agnostic parts (parse rules, decoration logic, geometry math, DB schema, text
protocol) carry over as **specs with existing tests as the porting oracle**.

## Stack

- **Python 3.12**, **PyGObject (gi)**, **GTK 4**.
- **GtkTextView + GtkTextBuffer + GtkTextTag** for the editor (NOT GtkSourceView —
  our highlighting is dynamic: mode depends on the first line and the checked-token
  reveal depends on the cursor line, which maps cleanly to applying our own tags).
- **sqlite3** (Python stdlib — no native build, no ABI dance).
- **pytest** for the pure logic.
- Optional **libadwaita** for styling niceties (kept optional to stay desktop-agnostic).
- **gtk4-layer-shell** (via gi) for always-on-top/overlay on Wayland (optional dep).

## Why GtkTextView tags map perfectly

The Electron app fakes highlighting with CodeMirror decorations. GTK gives the
real thing for free:

- **`GtkTextTag.invisible = True`** hides the trailing `/x` token — exactly the
  "hide unless cursor on line" behavior, toggled by re-tagging on cursor move.
- Tags carry `foreground`, `style=italic`, `strikethrough` → headings, comments,
  checked items, keyword line, links — one tag per `RangeKind`.
- **Checkbox glyphs** `☐`/`☑`: render as leading text via a tag, or as a child
  widget at a `GtkTextChildAnchor`. First pass: text glyph + tag (simplest).
- **Links**: a `link` tag + a `button-press` handler that hit-tests the tag at the
  click iter and opens via `Gio.AppInfo.launch_default_for_uri`.

So `computeRanges(doc, cursorLine)` ports almost verbatim; only the *translator*
changes (CM `Decoration` → `buffer.apply_tag`).

## Architecture / module mapping

```
antinote_gtk/
  __main__.py            # Gtk.Application entry
  app.py                 # Application + window lifecycle
  window.py              # frameless rounded window, always-on-top, drag, indicator
  editor.py              # GtkTextView wrapper: tag table + re-tag on change/cursor
  highlight.py           # PORT of computeRanges -> tag ranges (PURE, tested)
  slashpicker.py         # popover keyword picker
  notestate.py           # notes list/index/content + debounced autosave
  db.py                  # sqlite3 repos + migrations + old-DB copy (tested)
  parse/                 # PORT of links.py, todo.py, mode.py (PURE, tested)
  tray.py                # AppIndicator (ayatana) + menu
  shortcuts.py           # GlobalShortcuts portal (Alt+A) + graceful degrade
  geometry.py            # PORT of isOnScreen/parseGeometry (PURE, tested)
  style.css              # GTK CSS: panel bg, rounded corners, accents
tests/                   # pytest mirrors of the existing TS test suites
data/
  *.desktop, icons, flatpak manifest
pyproject.toml
```

Single process — **no IPC, no preload, no contextBridge** (those whole layers
vanish).

### Electron → GTK mapping

| Electron piece | GTK4 + Python |
|---|---|
| Renderer (Svelte+CM6+theme) | `editor.py` (GtkTextView+tags) + `style.css` |
| `decorations.ts` `computeRanges` | `highlight.py` (pure) |
| `lib/parse/*` | `parse/*` (pure) |
| `noteState.svelte.ts` | `notestate.py` |
| frameless/transparent/always-on-top window | `window.py`: `set_decorated(False)`, CSS `background: transparent` + rounded child, layer-shell/X11 keep-above |
| drag region | `GtkWindowHandle` wrapping a top strip |
| slash picker | `Gtk.Popover` / custom overlay |
| tray (Electron `Tray`) | `tray.py` via AyatanaAppIndicator3 (GI) |
| global shortcut | `org.freedesktop.portal.GlobalShortcuts` (works under Flatpak/Wayland) |
| better-sqlite3 + IPC | `sqlite3` stdlib, in-process |
| geometry/auto-hide/autosave timers | `GLib.timeout_add` |
| settings table | same `app_settings` table |

## Data compatibility

Same SQLite schema (`notes`, `app_settings`). DB at
`GLib.get_user_config_dir()/antinote/notes.db` (or keep `Antinote` to share with
the Electron build — **decision point**, see below). On first launch, copy the old
Tauri DB from `~/.config/com.honganh.antinote-linux/notes.db` if present, same as
the Electron app.

**Open question:** should the GTK app share the Electron app's DB
(`~/.config/Antinote/notes.db`) so users can run either against the same notes, or
use its own dir? Sharing is friendlier but risks two apps writing concurrently
(WAL handles it, but still). Recommend its **own dir** (`~/.config/antinote-gtk/`)
with a one-time import from whichever older DB exists.

## Hard parts (be honest)

1. **Global hotkey Alt+A**: only reliable via the GlobalShortcuts portal, which in
   practice means **running under Flatpak** (or a desktop that exposes the portal).
   Plain X11 grab works on X11 sessions; Wayland without the portal cannot. Degrade
   gracefully — the tray always works. This is *not worse* than Electron.
2. **System tray**: GTK4 has no built-in tray. Use AyatanaAppIndicator3 via GI
   (StatusNotifierItem). Works on most DEs; GNOME needs an extension (same caveat
   the Electron tray has on GNOME).
3. **Always-on-top + transparency on Wayland**: GTK4 dropped several X11-era window
   controls. Always-on-top needs `gtk4-layer-shell` (overlay layer) on Wayland; on
   X11 use `_NET_WM_STATE_ABOVE`. Transparency needs a compositor + CSS alpha.
4. **Frameless drag**: use `GtkWindowHandle` for the drag strip.

## Packaging

- **Primary: Flatpak** — the native-Linux answer. GNOME runtime supplies GTK4;
  your code is tiny; the runtime is shared across apps. Crucially, Flatpak gives
  **portal access** (global shortcut, file opening) and sandboxing. Manifest pulls
  python3 + PyGObject from the runtime.
- **Secondary: `.deb`** depending on `python3-gi`, `gir1.2-gtk-4.0`,
  `gir1.2-ayatanaappindicator3-0.1`, `gtk4-layer-shell` — tiny package, relies on
  system libs.
- PyInstaller is possible but bundles Python and balloons size — not recommended
  when Flatpak/deb can share system GTK.

## Testing

- `pytest`. Port the pure modules first and translate the **existing TS test
  cases 1:1** — they are the behavioral oracle (`computeRanges`, parsers, geometry,
  db). The GtkTextView/window/tray glue is verified by running the app.

## What carries over vs. rewritten

- **Carries over (as spec + tests):** `parse/*`, `computeRanges` logic, geometry
  math, DB schema, the text protocol, the design tokens (dark palette).
- **Rewritten:** every UI/IO surface — window, editor widget, tray, shortcut, DB
  access, state, packaging.

## Decisions to confirm before implementing

1. **Repo placement:** separate repo (cleanest) vs a `native-gtk/` subdir of this
   repo (easy comparison). Recommend separate repo; subdir is fine for now.
2. **DB dir:** own `~/.config/antinote-gtk/` (recommended) vs shared with Electron.
3. **Packaging target:** Flatpak primary (recommended) — confirm, or prioritize `.deb`.
4. **Dark-only** (matching the Antinote first pass) vs theme toggle.
