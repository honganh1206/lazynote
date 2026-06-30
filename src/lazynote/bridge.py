"""Backend QObject exposed to QML.

Wraps NoteState + a debounced autosave QTimer, and exposes settings / open-url.
QML reads `content`/`index`/`count`/`mode` properties and calls the slots.
"""

from __future__ import annotations

import json

from PySide6.QtCore import Property, Qt, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QFontDatabase, QGuiApplication

from lazynote import fonts, store, theme
from lazynote.editormodel import line_render_spans
from lazynote.geometry import Geometry, is_on_screen, parse_geometry
from lazynote.notestate import NoteState
from lazynote.parse.mode import REGISTERED_KEYWORDS, detect_mode

SAVE_DEBOUNCE_MS = 500


class Backend(QObject):
    contentChanged = Signal()
    statusChanged = Signal()
    autoHideChanged = Signal(bool)
    toggleWindowRequested = Signal()
    themeChanged = Signal()
    fontChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._state = NoteState(store.get_notes(), store.get_settings())
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(SAVE_DEBOUNCE_MS)
        self._save_timer.timeout.connect(self._state.save_current)

        hints = QGuiApplication.styleHints()
        if hints is not None:
            hints.colorSchemeChanged.connect(self._on_os_scheme_changed)

    # ---- theme ----
    def _os_scheme(self) -> str:
        hints = QGuiApplication.styleHints()
        if hints is None:
            return "dark"
        return "light" if hints.colorScheme() == Qt.ColorScheme.Light else "dark"

    def _theme_mode(self) -> str:
        m = store.get_settings().get("theme")
        return m if m in ("system", "light", "dark") else "system"

    def _on_os_scheme_changed(self, _scheme) -> None:
        # Only the system-following mode cares about live OS changes.
        if self._theme_mode() == "system":
            self.themeChanged.emit()
            self.contentChanged.emit()

    def _theme(self) -> str:
        return self._theme_mode()

    theme = Property(str, _theme, notify=themeChanged)

    def _colors(self) -> dict:
        return theme.palette_for(self._theme_mode(), self._os_scheme())

    colors = Property("QVariantMap", _colors, notify=themeChanged)

    @Slot(str)
    def set_theme(self, mode: str) -> None:
        if mode not in ("system", "light", "dark"):
            return
        store.get_settings().set("theme", mode)
        self.themeChanged.emit()
        self.contentChanged.emit()

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

    # ---- editor ----
    @Slot(int, int, result="QVariantMap")
    def line_render(self, line: int, cursor_line: int) -> dict:
        """Per-line render data for the bespoke editor: styled spans + checkbox.

        Returns {"text": raw line text, "checkbox": ""|"checked"|"unchecked",
                 "spans": [{text,color,italic,strike,hidden,link}, ...]}.
        """
        pal = theme.palette_for(self._theme_mode(), self._os_scheme())
        lr = line_render_spans(self._state.content, line, cursor_line, palette=pal)
        lines = self._state.content.split("\n")
        raw = lines[line] if 0 <= line < len(lines) else ""
        return {
            "text": raw,
            "checkbox": lr.checkbox or "",
            "spans": [
                {
                    "text": s.text,
                    "color": s.color,
                    "italic": s.italic,
                    "strike": s.strike,
                    "hidden": s.hidden,
                    "link": s.link,
                }
                for s in lr.spans
            ],
        }

    @Slot(int)
    def toggle_checkbox(self, line: int) -> None:
        """Toggle the trailing /x on a todo checklist line, then re-emit content."""
        lines = self._state.content.split("\n")
        if not (0 <= line < len(lines)):
            return
        text = lines[line]
        # Only meaningful for non-heading, non-comment, non-empty todo items.
        if text.strip() == "" or text.startswith("#") or text.startswith("//"):
            return
        lines[line] = text[:-2] if text.endswith("/x") else text + "/x"
        self.edit("\n".join(lines))
