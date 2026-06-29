import { describe, it, expect } from 'vitest'
import { detectMode, REGISTERED_KEYWORDS } from './mode'

describe('detectMode', () => {
  it('detects todo with title', () => {
    expect(detectMode('todo: groceries\n...')).toEqual({ keyword: 'todo', title: 'groceries' })
  })
  it('detects bare todo', () => {
    expect(detectMode('todo')).toEqual({ keyword: 'todo', title: '' })
  })
  it('returns null for plain text', () => {
    expect(detectMode('just a note')).toBeNull()
  })
  it('exposes registered keywords', () => {
    expect(REGISTERED_KEYWORDS).toContain('todo')
  })
})
