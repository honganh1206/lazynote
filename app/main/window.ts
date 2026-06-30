import { BrowserWindow, screen } from 'electron'
import { getSettings } from './store'
import { isOnScreen, parseGeometry } from './geometry'

const SETTING_KEY = 'window_geometry'
const DEBOUNCE_MS = 500

// Restore a previously persisted window position/size, but only if it still
// lands on a connected display (guards against a monitor being unplugged).
export function restoreGeometry(win: BrowserWindow): void {
  const g = parseGeometry(getSettings().get(SETTING_KEY))
  if (!g) return
  const display = screen.getDisplayMatching({
    x: g.x,
    y: g.y,
    width: g.width,
    height: g.height
  })
  if (!isOnScreen(g, display.workArea)) return
  win.setBounds(g)
}

// Persist the window geometry on move/resize, debounced.
export function trackGeometry(win: BrowserWindow): void {
  let timer: ReturnType<typeof setTimeout> | null = null
  const save = (): void => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      const b = win.getBounds()
      getSettings().set(
        SETTING_KEY,
        JSON.stringify({ x: b.x, y: b.y, width: b.width, height: b.height })
      )
    }, DEBOUNCE_MS)
  }
  win.on('move', save)
  win.on('resize', save)
  win.on('closed', () => {
    if (timer) clearTimeout(timer)
  })
}
