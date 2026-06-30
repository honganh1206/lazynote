// Pure geometry helpers for window persistence. No Electron imports here so this
// module is unit-testable under plain Node (vitest).

export interface Geometry {
  x: number
  y: number
  width: number
  height: number
}

export interface Bounds {
  x: number
  y: number
  width: number
  height: number
}

export const MIN_WIDTH = 360
export const MIN_HEIGHT = 360

// A window counts as on-screen if it overlaps the monitor by at least 50px on
// both axes — enough to be grabbable. Mirrors the old Tauri windowState logic.
export function isOnScreen(g: Geometry, m: Bounds): boolean {
  const gRight = g.x + g.width
  const gBottom = g.y + g.height
  const mRight = m.x + m.width
  const mBottom = m.y + m.height

  const overlapX = Math.max(0, Math.min(gRight, mRight) - Math.max(g.x, m.x))
  const overlapY = Math.max(0, Math.min(gBottom, mBottom) - Math.max(g.y, m.y))

  return overlapX >= 50 && overlapY >= 50
}

// Parse persisted geometry JSON; returns null if missing/malformed. Clamps the
// size up to the window minimums.
export function parseGeometry(raw: string | null): Geometry | null {
  if (!raw) return null
  let g: unknown
  try {
    g = JSON.parse(raw)
  } catch {
    return null
  }
  if (typeof g !== 'object' || g === null) return null
  const rec = g as Record<string, unknown>
  if (
    typeof rec.x !== 'number' ||
    typeof rec.y !== 'number' ||
    typeof rec.width !== 'number' ||
    typeof rec.height !== 'number'
  ) {
    return null
  }
  return {
    x: rec.x,
    y: rec.y,
    width: Math.max(rec.width, MIN_WIDTH),
    height: Math.max(rec.height, MIN_HEIGHT)
  }
}
