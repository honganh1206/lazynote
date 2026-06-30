# Lazynote for Linux

<p align="center">
  <img src="docs/icon.png" alt="Lazynote icon" width="128">
</p>

<p align="center">
  A lightweight, always-accessible <b>native</b> scratchpad for Linux, inspired by
  <a href="https://antinote.io/">Antinote</a>.<br>
  Built with <a href="https://doc.qt.io/qtforpython/">PySide6</a> + Qt Quick (QML).
</p>

## Status

All features below are implemented and the app runs. The editor has two
implementations: **Option A** (`Editor.qml`, a `TextArea` + `QSyntaxHighlighter`)
and the bespoke **Option B** (`EditorB.qml`, per-line styled delegates with real
☐/☑ checkboxes and animation), which is the default. See
`docs/plans/2026-06-30-qtquick-pyside6-port.md` (plan) and `…-design.md`
(architecture).

## Features

- Frameless, translucent, always-on-top scratchpad window
- Multiple notes with quick navigation and a position counter
- Auto-save to a local SQLite database
- Global hotkey **Alt+A** to toggle show/hide
- System tray menu (show/hide, new note, toggle always-on-top, toggle auto-hide, quit)
- Window position/size remembered across restarts
- `todo:` mode with checklist items (`/x` to check), `#` headings, `//` comments
- Plain mode with markdown-style headings and clickable links

## Prerequisites

- **Python 3.12+**
- A Qt 6 platform (PySide6 ships its own Qt for development)

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]

# Run (needs a display)
lazynote           # or: python -m lazynote

# Headless smoke (no UI shown)
QT_QPA_PLATFORM=offscreen python -m lazynote

# Tests + lint
QT_QPA_PLATFORM=offscreen pytest -q
ruff check .
```

## Packaging

**Flatpak (primary)** — the KDE 6 runtime supplies Qt; the app stays small and gets
portal access for the global shortcut:

```bash
flatpak install flathub org.kde.Platform//6.7 org.kde.Sdk//6.7
flatpak-builder --user --install --force-clean build-dir data/com.honganh.lazynote.yml
flatpak run com.honganh.lazynote
```

**.deb** — depends on system `python3-pyside6.*` packages; install the package and
`lazynote` is on `PATH`. (The Flatpak manifest is the maintained path; the deb
recipe is a thin wrapper over `pip install --prefix`.)

Notes migrate automatically on first launch from an older Electron
(`~/.config/Antinote`) or Tauri (`~/.config/com.honganh.antinote-linux`) install.

## Project Structure

```
src/lazynote/        # application package (Python + QML)
  app.py             # entry: QApplication + QML engine
  bridge.py          # QObject exposed to QML
  qml/               # QML UI (Main, Editor, EditorB, SlashPicker)
  parse/             # pure parsers (links, todo, mode)
  highlight.py       # pure: syntax range computation
  geometry.py        # pure: on-screen / geometry helpers
  db.py              # sqlite storage
  store.py           # config dir + legacy import
tests/               # pytest
data/                # .desktop, AppStream metainfo, Flatpak manifest
docs/plans/          # design + implementation plan
pyproject.toml
```

## License

MIT
