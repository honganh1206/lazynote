"""Backend QObject exposed to QML.

Wraps NoteState + a debounced autosave QTimer, and exposes settings / open-url.
QML reads `content`/`index`/`count`/`mode` properties and calls the slots.
"""

from __future__ import annotations

import json

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtQuick import QQuickTextDocument

from antinote_qt import store
from antinote_qt.geometry import Geometry, is_on_screen, parse_geometry
from antinote_qt.highlight import compute_ranges
from antinote_qt.highlighter import SyntaxHighlighter
from antinote_qt.notestate import NoteState
from antinote_qt.parse.mode import REGISTERED_KEYWORDS, detect_mode

SAVE_DEBOUNCE_MS = 500


class Backend(QObject):
    contentChanged = Signal()
    statusChanged = Signal()
    autoHideChanged = Signal(bool)
    toggleWindowRequested = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._state = NoteState(store.get_notes(), store.get_settings())
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(SAVE_DEBOUNCE_MS)
        self._save_timer.timeout.connect(self._state.save_current)
        self._highlighter: SyntaxHighlighter | None = None

    # ---- properties ----
    def _content(self) -> str:
        return self._state.content

    content = Property(str, _content, notify=contentChanged)

    def _index(self) -> int:
        return self._state.index

    index = Property(int, _index, notify=statusChanged)

    def _count(self) -> int:
        return self._state.count()

    count = Property(int, _count, notify=statusChanged)

    def _mode(self) -> str:
        m = detect_mode(self._state.content)
        return m["keyword"] if m else ""

    mode = Property(str, _mode, notify=contentChanged)

    def _keywords(self) -> list:
        return list(REGISTERED_KEYWORDS)

    keywords = Property("QStringList", _keywords, constant=True)

    # ---- slots ----
    @Slot()
    def load(self) -> None:
        self._state.load()
        self.contentChanged.emit()
        self.statusChanged.emit()

    @Slot(str)
    def edit(self, text: str) -> None:
        self._state.set_content(text)
        self.contentChanged.emit()
        self._save_timer.start()

    @Slot()
    def flush(self) -> None:
        self._save_timer.stop()
        self._state.save_current()

    @Slot(int)
    def navigate(self, delta: int) -> None:
        if self._state.navigate(delta):
            self.contentChanged.emit()
            self.statusChanged.emit()

    @Slot()
    def new_note(self) -> None:
        self._state.add()
        self.contentChanged.emit()
        self.statusChanged.emit()

    @Slot()
    def delete_current(self) -> None:
        self._state.remove_current()
        self.contentChanged.emit()
        self.statusChanged.emit()

    @Slot(str)
    def slash_select(self, keyword: str) -> None:
        c = self._state.content
        nl = c.find("\n")
        rest = c[nl:] if nl != -1 else ""
        self._state.set_content(keyword + rest)
        self.contentChanged.emit()
        self._save_timer.start()

    @Slot(str, result=str)
    def setting_get(self, key: str) -> str:
        v = store.get_settings().get(key)
        return v if v is not None else ""

    @Slot(str, str)
    def setting_set(self, key: str, value: str) -> None:
        store.get_settings().set(key, value)

    @Slot(int, int, int, int)
    def save_geometry(self, x: int, y: int, w: int, h: int) -> None:
        store.get_settings().set(
            "window_geometry", json.dumps({"x": x, "y": y, "width": w, "height": h})
        )

    @Slot(result="QVariantList")
    def restore_geometry(self) -> list:
        """Return [x, y, w, h] if a saved geometry is still on a connected screen, else []."""
        g = parse_geometry(store.get_settings().get("window_geometry"))
        if g is None:
            return []
        for screen in QGuiApplication.screens():
            r = screen.availableGeometry()
            if is_on_screen(g, Geometry(r.x(), r.y(), r.width(), r.height())):
                return [g.x, g.y, g.width, g.height]
        return []

    @Slot(result=bool)
    def auto_hide_enabled(self) -> bool:
        return store.get_settings().get("auto_hide_on_blur") == "true"

    @Slot(result=bool)
    def toggle_auto_hide(self) -> bool:
        nxt = not self.auto_hide_enabled()
        store.get_settings().set("auto_hide_on_blur", "true" if nxt else "false")
        self.autoHideChanged.emit(nxt)
        return nxt

    @Slot(str)
    def open_url(self, url: str) -> None:
        QDesktopServices.openUrl(QUrl(url))

    @Slot()
    def request_toggle(self) -> None:
        # Called from the global-shortcut thread (queued onto the GUI thread).
        self.toggleWindowRequested.emit()

    # ---- editor highlighting (Option A) ----
    @Slot(QQuickTextDocument)
    def attach_highlighter(self, quick_text_document: QQuickTextDocument) -> None:
        td = quick_text_document.textDocument
        qdoc = td() if callable(td) else td
        self._highlighter = SyntaxHighlighter(qdoc)

    @Slot(int)
    def set_cursor_line(self, line: int) -> None:
        if self._highlighter is not None:
            self._highlighter.set_cursor_line(line)

    @Slot()
    def refresh_highlight(self) -> None:
        if self._highlighter is not None:
            self._highlighter.schedule_rehighlight()

    @Slot(int, result=str)
    def url_at(self, pos: int) -> str:
        for r in compute_ranges(self._state.content, -1):
            if r.kind == "link" and r.from_ <= pos < r.to:
                return self._state.content[r.from_ : r.to]
        return ""
