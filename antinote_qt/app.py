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

from antinote_qt import store
from antinote_qt.bridge import Backend

QML_DIR = Path(__file__).parent / "qml"


def create_engine(app: QGuiApplication) -> QQmlApplicationEngine:
    """Open the store, build the QML engine, expose the backend, load the window.

    Separated from main() so a headless smoke test can construct it under
    QT_QPA_PLATFORM=offscreen without entering the event loop.
    """
    store.init_store()
    engine = QQmlApplicationEngine()
    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(str(QML_DIR / "Main.qml"))
    if not engine.rootObjects():
        raise RuntimeError("Failed to load Main.qml")
    # Keep references so they aren't garbage-collected.
    engine._backend = backend  # type: ignore[attr-defined]
    return engine


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Antinote")
    app.setOrganizationName("antinote-qt")
    engine = create_engine(app)
    app._engine = engine  # type: ignore[attr-defined]
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
