"""Global hotkey Alt+A via an X11 key grab (python-xlib).

Degrades gracefully: on Wayland-without-X11, or if python-xlib / the X display is
unavailable, start() returns False and the app relies on the tray instead. The
Wayland-native path is the GlobalShortcuts portal (best provided under Flatpak);
not implemented here yet.

The grab runs on a background thread and emits `activated` (a Qt signal), which
Qt delivers to the GUI thread via a queued connection.
"""

from __future__ import annotations

import threading
import time

from PySide6.QtCore import QObject, Signal


class GlobalShortcut(QObject):
    activated = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._stop = False
        self._thread: threading.Thread | None = None
        self._dpy = None
        self._keycode = None

    def start(self) -> bool:
        try:
            from Xlib import X, XK, display

            dpy = display.Display()  # raises if there's no usable X display
        except Exception:
            return False

        root = dpy.screen().root
        keycode = dpy.keysym_to_keycode(XK.string_to_keysym("a"))
        alt = X.Mod1Mask
        # Grab Alt+A under the common lock-mask combinations (NumLock / CapsLock).
        for extra in (0, X.LockMask, X.Mod2Mask, X.LockMask | X.Mod2Mask):
            root.grab_key(keycode, alt | extra, True, X.GrabModeAsync, X.GrabModeAsync)
        root.change_attributes(event_mask=X.KeyPressMask)
        dpy.sync()

        self._dpy = dpy
        self._keycode = keycode
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def _run(self) -> None:
        from Xlib import X

        dpy = self._dpy
        while not self._stop:
            if dpy.pending_events():
                ev = dpy.next_event()
                if ev.type == X.KeyPress and ev.detail == self._keycode:
                    self.activated.emit()
            else:
                time.sleep(0.02)

    def stop(self) -> None:
        self._stop = True
