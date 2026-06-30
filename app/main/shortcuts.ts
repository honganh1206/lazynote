import { app, globalShortcut, BrowserWindow } from 'electron'

// Global hotkey Alt+A toggles the window's visibility. Registration can fail on
// Wayland (no global-shortcut portal) — degrade gracefully, the tray still works.
export function registerShortcuts(win: BrowserWindow): void {
  const ok = globalShortcut.register('Alt+A', () => {
    if (win.isVisible()) {
      win.hide()
    } else {
      win.show()
      win.focus()
    }
  })
  if (!ok) {
    console.warn('[shortcuts] failed to register Alt+A (may be unavailable on Wayland)')
  }
  app.on('will-quit', () => {
    globalShortcut.unregisterAll()
  })
}
