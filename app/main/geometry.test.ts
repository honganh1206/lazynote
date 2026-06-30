import { describe, it, expect } from 'vitest'
import { isOnScreen, parseGeometry, MIN_WIDTH, MIN_HEIGHT } from './geometry'

const mon = { x: 0, y: 0, width: 1920, height: 1080 }

describe('isOnScreen', () => {
  it('accepts a window fully on screen', () => {
    expect(isOnScreen({ x: 100, y: 100, width: 360, height: 360 }, mon)).toBe(true)
  })
  it('rejects a window off screen', () => {
    expect(isOnScreen({ x: 5000, y: 5000, width: 360, height: 360 }, mon)).toBe(false)
  })
  it('rejects a window overlapping by less than 50px', () => {
    // only 40px of the window pokes onto the monitor from the left edge
    expect(isOnScreen({ x: -320, y: 100, width: 360, height: 360 }, mon)).toBe(false)
  })
  it('accepts a window overlapping by at least 50px', () => {
    expect(isOnScreen({ x: -310, y: 100, width: 360, height: 360 }, mon)).toBe(true)
  })
})

describe('parseGeometry', () => {
  it('returns null for null/empty', () => {
    expect(parseGeometry(null)).toBeNull()
    expect(parseGeometry('')).toBeNull()
  })
  it('returns null for malformed json', () => {
    expect(parseGeometry('{not json')).toBeNull()
  })
  it('returns null when a field is missing or wrong type', () => {
    expect(parseGeometry('{"x":1,"y":2,"width":300}')).toBeNull()
    expect(parseGeometry('{"x":"1","y":2,"width":300,"height":300}')).toBeNull()
  })
  it('parses valid geometry and clamps to minimums', () => {
    const g = parseGeometry('{"x":10,"y":20,"width":100,"height":100}')
    expect(g).toEqual({ x: 10, y: 20, width: MIN_WIDTH, height: MIN_HEIGHT })
  })
  it('keeps sizes above the minimum', () => {
    const g = parseGeometry('{"x":10,"y":20,"width":800,"height":600}')
    expect(g).toEqual({ x: 10, y: 20, width: 800, height: 600 })
  })
})
