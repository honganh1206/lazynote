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
- **Clipboard OCR:** take a screenshot with your desktop tool, press **Ctrl+V** in
  Lazynote, and the recognized text is inserted at the cursor (multi-line
  preserved). Requires Tesseract (see Prerequisites).

## Prerequisites

- **Python 3.12+**
- A Qt 6 platform (PySide6 ships its own Qt for development)
- **Tesseract OCR** — for the screenshot-to-text paste feature:

  ```bash
  sudo apt update
  sudo apt install tesseract-ocr tesseract-ocr-eng
  ```

  The `.deb` package recommends `tesseract-ocr`, so apt installs it by default
  when you `apt install ./lazynote_*.deb`. If it's missing, Ctrl+V on a
  screenshot shows an install hint toast.

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

**.deb** — a self-contained package (Python + Qt 6 bundled via PyInstaller, no
runtime `python3`/`pyside6` deps). Build locally:

```bash
pip install pyinstaller .
pyinstaller --noconfirm packaging/lazynote.spec   # -> dist/lazynote/
bash packaging/build-deb.sh 0.1.6                  # -> dist/lazynote_0.1.6_amd64.deb
```

Install with `sudo apt install ./lazynote_*.deb` (or `sudo dpkg -i`); `lazynote`
lands on `PATH`. After CI passes on a push to `main`, it invokes the reusable
`.github/workflows/cd.yml` workflow to build the `.deb` and publish a GitHub
Release automatically. Tags use the CI run number and tested commit, for example
`v0.1.40+gc72cf1b`.

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
data/                # .desktop, AppStream metainfo
packaging/           # PyInstaller spec + build-deb.sh
docs/plans/          # design + implementation plan
pyproject.toml
```

## License

MIT
