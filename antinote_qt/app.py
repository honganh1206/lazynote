"""Application entry point.

Uses QApplication (not QGuiApplication) because the system tray
(Qt.labs.platform SystemTrayIcon) needs the Widgets module available.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

QML_DIR = Path(__file__).parent / "qml"


def create_engine(app: QGuiApplication) -> QQmlApplicationEngine:
    """Build the QML engine and load the root window. Returns the engine.

    Separated from main() so a headless smoke test can construct it under
    QT_QPA_PLATFORM=offscreen without entering the event loop.
    """
    engine = QQmlApplicationEngine()
    engine.load(str(QML_DIR / "Main.qml"))
    if not engine.rootObjects():
        raise RuntimeError("Failed to load Main.qml")
    return engine


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Antinote")
    app.setOrganizationName("antinote-qt")
    engine = create_engine(app)
    # Keep a reference so it isn't garbage-collected.
    app._engine = engine  # type: ignore[attr-defined]
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
