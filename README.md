# Antinote for Linux

<p align="center">
  <img src="docs/icon.png" alt="Antinote icon" width="128">
</p>

<p align="center">
  A lightweight, always-accessible <b>native</b> scratchpad for Linux, inspired by
  <a href="https://antinote.io/">Antinote</a>.<br>
  Built with <a href="https://doc.qt.io/qtforpython/">PySide6</a> + Qt Quick (QML).
</p>

## Status

Native rewrite in progress. See `docs/plans/2026-06-30-qtquick-pyside6-port.md`
for the implementation plan and `…-design.md` for the architecture.

## Features (target parity)

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
python -m antinote_qt

# Headless smoke (no UI shown)
QT_QPA_PLATFORM=offscreen python -m antinote_qt

# Tests + lint
pytest -q
ruff check .
```

## Project Structure

```
antinote_qt/        # application package (Python + QML)
  app.py            # entry: QApplication + QML engine
  qml/              # QML UI
  parse/            # pure parsers (links, todo, mode)
  highlight.py      # pure: syntax range computation
  db.py             # sqlite storage
tests/              # pytest
docs/plans/         # design + implementation plan
pyproject.toml
```

## License

MIT
