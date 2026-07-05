"""Application entry point.

Uses QApplication (not QGuiApplication) because the system tray
(Qt.labs.platform SystemTrayIcon) needs the Widgets module available.
"""

from __future__ import annotations

import signal
import sys
import os
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from lazynote import store
from lazynote.bridge import Backend
from lazynote.shortcuts import GlobalShortcut

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

    shortcut = GlobalShortcut()
    shortcut.activated.connect(backend.request_toggle)
    if not shortcut.start():
        print(
            "[shortcuts] global Alt+A unavailable (Wayland without portal, or no X11) "
            "- use the tray to show/hide",
            file=sys.stderr,
        )

    engine.load(str(QML_DIR / "Main.qml"))
    if not engine.rootObjects():
        raise RuntimeError("Failed to load Main.qml")
    # Keep references so they aren't garbage-collected.
    engine._backend = backend  # type: ignore[attr-defined]
    engine._shortcut = shortcut  # type: ignore[attr-defined]
    return engine


def main() -> int:
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    app = QApplication(sys.argv)
    app.setApplicationName("Lazynote")
    app.setOrganizationName("lazynote")
    engine = create_engine(app)
    app._engine = engine  # type: ignore[attr-defined]

    # Make Ctrl-C work. Qt's event loop is C++ and never returns to Python to run
    # signal handlers, so (1) handle SIGINT by quitting and (2) wake the interpreter
    # periodically with a no-op timer so the handler actually fires.
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    heartbeat = QTimer()
    heartbeat.start(200)
    heartbeat.timeout.connect(lambda: None)
    app._heartbeat = heartbeat  # type: ignore[attr-defined]

    # Flush pending save and release the global-shortcut grab on exit.
    app.aboutToQuit.connect(engine._backend.flush)  # type: ignore[attr-defined]
    app.aboutToQuit.connect(engine._shortcut.stop)  # type: ignore[attr-defined]

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
