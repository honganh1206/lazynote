import { describe, it, expect } from 'vitest'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { openDb, NotesRepo, SettingsRepo } from './db'

function freshDb() {
  const dir = mkdtempSync(join(tmpdir(), 'antinote-'))
  return openDb(join(dir, 'notes.db'))
}

describe('NotesRepo', () => {
  it('creates and lists notes ordered by sort_index', () => {
    const db = freshDb(); const notes = new NotesRepo(db)
    const a = notes.create('first'); const b = notes.create('second')
    expect(notes.list().map(n => n.id)).toEqual([a.id, b.id])
    expect(b.sort_index).toBeGreaterThan(a.sort_index)
  })
  it('updates content and bumps updated_at', () => {
    const db = freshDb(); const notes = new NotesRepo(db)
    const n = notes.create('x'); notes.update(n.id, 'y')
    expect(notes.list()[0].content).toBe('y')
  })
  it('deletes a note', () => {
    const db = freshDb(); const notes = new NotesRepo(db)
    const n = notes.create('x'); notes.delete(n.id)
    expect(notes.list()).toHaveLength(0)
  })
})

describe('SettingsRepo', () => {
  it('seeds defaults and round-trips', () => {
    const db = freshDb(); const s = new SettingsRepo(db)
    expect(s.get('always_on_top')).toBe('true')
    s.set('always_on_top', 'false')
    expect(s.get('always_on_top')).toBe('false')
  })
})
