"""QSyntaxHighlighter that colors a QTextDocument from compute_ranges (Option A).

A highlighter can only restyle existing characters — it cannot inject ☐/☑ glyphs
and cannot truly hide the `/x` token (it dims it to transparent). The bespoke
editor (Option B) lifts those limits.

Re-highlighting is always *deferred* to the next event-loop tick (and coalesced),
never called synchronously — a synchronous rehighlight() during the edit that
triggered it re-enters highlightBlock and recurses.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat

from antinote_qt.highlight import compute_ranges

# Dark palette (matches the Antinote first-pass theme).
TEXT = "#d6d3cc"
MUTED = "#6f6b64"
AMBER = "#e6a86b"
GREEN = "#84c08a"
BLUE = "#79b8e0"


def _fmt(color: str | None = None, *, italic=False, strike=False, underline=False) -> QTextCharFormat:
    f = QTextCharFormat()
    if color is not None:
        f.setForeground(QColor(color))
    if italic:
        f.setFontItalic(True)
    if strike:
        f.setFontStrikeOut(True)
    if underline:
        f.setFontUnderline(True)
    return f


_FORMATS = {
    "heading1": _fmt(AMBER),
    "heading2": _fmt(GREEN),
    "heading3": _fmt(BLUE),
    "comment": _fmt(MUTED, italic=True),
    "keyword": _fmt(MUTED),
    "checkbox_checked": _fmt(MUTED, strike=True),
    "checkbox_unchecked": _fmt(TEXT),
    "link": _fmt(BLUE, underline=True),
    "hide_x": _fmt("#00000000"),  # transparent — Option A's stand-in for hiding
}


class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document) -> None:
        super().__init__(document)
        self._cursor_line = -1
        self._pending = False

    def set_cursor_line(self, line: int) -> None:
        if line != self._cursor_line:
            self._cursor_line = line
            # Cursor moved between lines -> the /x reveal changes; full re-pass.
            self.schedule_rehighlight()

    def schedule_rehighlight(self) -> None:
        """Re-highlight the whole document on the next tick (coalesced)."""
        if self._pending:
            return
        self._pending = True
        QTimer.singleShot(0, self._run)

    def _run(self) -> None:
        self._pending = False
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:  # noqa: N802 (Qt override)
        doc_text = self.document().toPlainText()
        ranges = compute_ranges(doc_text, self._cursor_line)
        block_start = self.currentBlock().position()
        block_end = block_start + len(text)
        for r in ranges:
            s = max(r.from_, block_start)
            e = min(r.to, block_end)
            if s < e:
                self.setFormat(s - block_start, e - s, _FORMATS[r.kind])
