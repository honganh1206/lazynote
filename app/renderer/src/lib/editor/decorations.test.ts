import { describe, it, expect } from 'vitest'
import { computeRanges } from './decorations'

describe('computeRanges', () => {
  it('hides /x token when cursor not on that line', () => {
    const r = computeRanges('todo:\ndone /x', 0)
    expect(r).toContainEqual(expect.objectContaining({ kind: 'hide-x' }))
    expect(r).toContainEqual(expect.objectContaining({ kind: 'checkbox-checked' }))
  })

  it('reveals /x and shows unchecked when cursor on that line', () => {
    const r = computeRanges('todo:\ndone /x', 1)
    expect(r.some(x => x.kind === 'hide-x')).toBe(false)
    expect(r).toContainEqual(expect.objectContaining({ kind: 'checkbox-unchecked' }))
  })

  it('hide-x covers exactly the trailing /x', () => {
    const doc = 'todo:\ndone /x'
    const r = computeRanges(doc, 0)
    const hide = r.find(x => x.kind === 'hide-x')!
    expect(doc.slice(hide.from, hide.to)).toBe('/x')
  })

  it('marks line 1 as keyword in todo mode', () => {
    const r = computeRanges('todo:\nx', 99)
    expect(r.some(x => x.kind === 'keyword' && x.from === 0)).toBe(true)
  })

  it('marks heading in plain mode line 0', () => {
    const r = computeRanges('# Title', 99)
    expect(r).toContainEqual(expect.objectContaining({ kind: 'heading1', from: 0 }))
  })

  it('classifies heading levels 2 and 3', () => {
    const r2 = computeRanges('## Sub', 99)
    expect(r2).toContainEqual(expect.objectContaining({ kind: 'heading2', from: 0 }))
    const r3 = computeRanges('### Subsub', 99)
    expect(r3).toContainEqual(expect.objectContaining({ kind: 'heading3', from: 0 }))
  })

  it('classifies comment and unchecked in todo mode', () => {
    const r = computeRanges('todo:\n// note\nbuy milk', 99)
    expect(r.some(x => x.kind === 'comment')).toBe(true)
    expect(r.some(x => x.kind === 'checkbox-unchecked')).toBe(true)
  })

  it('emits link ranges with correct offsets', () => {
    const doc = 'see https://example.com'
    const r = computeRanges(doc, 99)
    const link = r.find(x => x.kind === 'link')!
    expect(doc.slice(link.from, link.to)).toBe('https://example.com')
  })

  it('emits link ranges on non-first lines with correct absolute offsets', () => {
    const doc = 'todo:\nvisit https://example.com/page'
    const r = computeRanges(doc, 99)
    const link = r.find(x => x.kind === 'link')!
    expect(doc.slice(link.from, link.to)).toBe('https://example.com/page')
  })

  it('does not parse links on the todo keyword line', () => {
    const r = computeRanges('todo: https://x.com\nitem', 99)
    expect(r.some(x => x.kind === 'link' && x.from < 6)).toBe(false)
  })

  it('plain-mode non-heading line has NO checkbox kind', () => {
    const r = computeRanges('just some text', 99)
    expect(r.some(x => x.kind === 'checkbox-unchecked')).toBe(false)
    expect(r.some(x => x.kind === 'checkbox-checked')).toBe(false)
  })

  it('emits nothing line-classified for blank todo lines', () => {
    const r = computeRanges('todo:\n\nitem', 99)
    // line 1 is blank: no checkbox/heading/comment emitted for it (offset 6)
    expect(r.some(x => x.from === 6 && x.kind !== 'link')).toBe(false)
  })

  it('checkbox kinds span the whole line', () => {
    const doc = 'todo:\nbuy milk'
    const r = computeRanges(doc, 99)
    const cb = r.find(x => x.kind === 'checkbox-unchecked')!
    expect(cb.from).toBe(6)
    expect(cb.to).toBe(doc.length)
  })
})
