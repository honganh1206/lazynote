# Antinote — Qt Quick / QML + PySide6 native port design

**Date:** 2026-06-30
**Status:** Design (not yet approved for implementation)
**Supersedes:** the GTK4/Python port design (removed) — chosen route is Qt Quick
for the most bespoke, animated, sleek result.

## Goal

A native Linux Antinote that matches the original's **sleek, animated** feel, with
a small footprint (relative to Electron) and no Chromium. Same features, same text
protocol, same on-disk data. From-scratch parallel app.

## Why Qt Quick / QML (PySide6)

Qt Quick is the most capable native toolkit for a *bespoke, animated* UI:
GPU-accelerated scene graph, trivial transitions/`Behavior`/states, easy
translucency, full visual control. Python via **PySide6** (official Qt for Python,
mature, not-Rust). This is the deliberate trade vs GTK4/libadwaita, which looks
sleek-but-GNOME-conventional; QML lets us paint Antinote's exact look and animate
checks, window show/hide, caret, etc.

**Footprint caveat (important):** PySide6/Qt is heavy if bundled via pip wheels
(~hundreds of MB). "Small" here means **relying on system Qt** (distro
`python3-pyside6`) or a **Flatpak KDE runtime** (shared Qt). Do NOT bundle Qt with
PyInstaller if size matters. Still far smaller/lighter than Electron, just not as
featherweight as GTK.

## Stack

- **Python 3.12 + PySide6 (Qt 6)**, UI in **QML (Qt Quick + Qt Quick Controls)**.
- **Qt.labs.platform** for a QML-native `SystemTrayIcon` + `Menu`.
- **sqlite3** (stdlib — testable, no native build).
- **pytest** for pure logic.
- Optional **Kirigami** (KDE) for adaptive shell pieces; not required for a single window.

## The editor — the crux

Antinote is essentially a custom-styled editor. Qt offers two routes:

### Option A — `TextArea` + `QSyntaxHighlighter` (pragmatic)
A QML `TextArea` exposes `textDocument` (`QQuickTextDocument` → `QTextDocument`).
Attach a PySide6 `QSyntaxHighlighter` that colors runs from our `compute_ranges`
port. Real text editing (caret/selection/IME/undo) for free.
**Limits:** a highlighter can only *restyle* existing characters — it cannot
inject `☐/☑` glyphs, and it cannot truly hide the `/x` token (best it can do is a
transparent format, leaving trailing space). Good enough for a fast first
milestone; not the full Antinote look.

### Option B — custom QML editor (recommended for the sleek goal)
A bespoke editor: a line **model** (`QAbstractListModel`) whose delegates render
each line as styled `Text` (colors, strikethrough, real `☐/☑` items, `/x` simply
not drawn off the cursor line), with a `TextEdit`/`TextInput` capturing input — the
same "transparent input over styled display" overlay technique the Electron app
used, but in QML. This unlocks: real checkboxes (tap-to-toggle with a check
**animation**), per-line reveal of `/x`, and full control over typography/motion.
More work (must coordinate caret/selection between input and display), but it's the
route that actually looks and feels like Antinote.

**Recommendation:** build **A first as a running milestone**, then evolve the
display layer to **B** for the bespoke look + animated checkboxes. The pure
`compute_ranges` port feeds both.

## Architecture / module mapping

```
antinote_qt/
  __main__.py            # entry
  app.py                 # QApplication (needed for tray) + QQmlApplicationEngine
  qml/
    Main.qml             # frameless rounded translucent window, always-on-top, drag
    Editor.qml           # editor (Option A then B)
    SlashPicker.qml      # keyword popup with animation
    theme.js / Theme.qml # design tokens (dark palette, fonts, radii, durations)
  highlighter.py         # QSyntaxHighlighter using compute_ranges (Option A)
  editormodel.py         # QAbstractListModel for the custom editor (Option B)
  bridge.py              # QObject exposed to QML: notes API, settings, open-url
  highlight.py           # PORT of computeRanges (PURE, tested)
  parse/                 # PORT of links.py, todo.py, mode.py (PURE, tested)
  notestate.py           # notes list/index/content + debounced autosave
  db.py                  # sqlite3 repos + migrations + legacy import (tested)
  tray.py / via QML      # Qt.labs.platform SystemTrayIcon + Menu
  shortcuts.py           # global hotkey via portal / X11 (degrade)
  geometry.py            # PORT of isOnScreen/parseGeometry (PURE, tested)
tests/                   # pytest mirrors of the existing TS suites
data/                    # .desktop, icons, flatpak manifest
pyproject.toml
```

Single process; QML ↔ Python via a `bridge` `QObject` (signals/slots/properties).
No IPC/preload/contextBridge.

### Electron → Qt mapping

| Electron piece | Qt Quick / PySide6 |
|---|---|
| Renderer (Svelte+CM6+theme) | QML (`Main.qml`/`Editor.qml`) + `highlighter.py`/`editormodel.py` |
| `decorations.ts` `computeRanges` | `highlight.py` (pure) feeding the highlighter/model |
| `lib/parse/*` | `parse/*` (pure) |
| `noteState.svelte.ts` | `notestate.py` (+ exposed via `bridge`) |
| frameless/transparent/always-on-top | QML `Window` `flags: FramelessWindowHint|Tool|WindowStaysOnTopHint`, `color:"transparent"`, rounded `Rectangle` |
| drag region | `DragHandler` or `window.startSystemMove()` on the top strip |
| slash picker | `SlashPicker.qml` (`Popup`, animated) |
| tray | `Qt.labs.platform` `SystemTrayIcon` + `Menu` (needs `QApplication`) |
| global shortcut | GlobalShortcuts portal (DBus) / X11 grab; degrade on Wayland-no-portal |
| better-sqlite3 + IPC | `sqlite3` stdlib, in-process |
| autosave/geometry/auto-hide timers | `QTimer` |
| open url | `QDesktopServices.openUrl` |

## Sleek levers (the point of choosing Qt)
- **Motion:** `Behavior on opacity/scale`, `Transition`s, `NumberAnimation` — window
  fade/scale on show/hide, checkbox check animation, slash-picker pop, note-switch
  slide.
- **Translucency/blur:** translucent frameless window + compositor blur (KDE via
  `KWindowEffects`/platform; GNOME via extension). Document as compositor-dependent.
- **Typography:** bundle a refined font (Inter, or a mono like Commit Mono / iA
  Writer). Font + tight dark palette = most of the look.
- **Rounded, shadowed, layered** chrome via `Rectangle` + `DropShadow`/`MultiEffect`.

## Hard parts (honest)
1. **Custom editor (Option B)** is real work — coordinating a transparent input with
   a styled display (caret, selection, scrolling, IME). Option A de-risks the start.
2. **Hiding `/x`** is trivial in B (don't draw it), awkward in A (transparent format).
3. **Global hotkey Alt+A**: same portal/X11/Wayland story as everywhere — degrade to
   tray. Not worse than Electron.
4. **Tray** needs `QApplication` (Widgets module present) even for a QML app; on GNOME
   needs the AppIndicator extension (same caveat as Electron).
5. **Footprint** only stays small with system/Flatpak Qt, not bundled wheels.

## Data compatibility
Same SQLite schema. DB at a Qt config dir
(`QStandardPaths.AppConfigLocation`, e.g. `~/.config/antinote-qt/`). On first launch,
import from the first existing legacy DB (`~/.config/Antinote/notes.db` Electron, or
`~/.config/com.honganh.antinote-linux/notes.db` Tauri).

## Packaging
- **Primary: Flatpak** (KDE 6 runtime supplies Qt6/PySide6; portal access for the
  global shortcut + url open + sandbox). App stays small (runtime shared).
- **Secondary: `.deb`** depending on `python3-pyside6.*` system packages.
- Avoid PyInstaller-bundled Qt (huge).

## Testing
`pytest`, porting the existing TS test cases 1:1 as the oracle for `parse/*`,
`compute_ranges`, `geometry`, `db`. QML/editor/tray/shortcut glue verified by
running the app.

## Decisions to confirm before implementing
1. **Editor route:** A-then-B (recommended) vs straight to B vs A-only.
2. **Repo placement:** separate repo (recommended) vs `native-qt/` subdir here.
3. **DB dir:** own `~/.config/antinote-qt/` + one-time legacy import (recommended).
4. **Packaging:** Flatpak primary (recommended) vs `.deb`-first.
5. **Dark-only** vs theme toggle.
