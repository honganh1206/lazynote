import { describe, it, expect } from 'vitest'
import { parseLinks } from './links'

describe('parseLinks', () => {
  it('returns single text segment for plain text', () => {
    expect(parseLinks('hello world')).toEqual([
      { type: 'text', value: 'hello world', displayValue: 'hello world' },
    ])
  })
  it('extracts a url segment', () => {
    const segs = parseLinks('see https://example.com now')
    expect(segs.map(s => s.type)).toEqual(['text', 'link', 'text'])
    expect(segs[1]).toMatchObject({ type: 'link', fullUrl: 'https://example.com' })
  })
  it('keeps url inside parens balanced', () => {
    const segs = parseLinks('(https://en.wikipedia.org/wiki/A_(b))')
    const link = segs.find(s => s.type === 'link')!
    expect(link.fullUrl).toBe('https://en.wikipedia.org/wiki/A_(b)')
  })
  it('returns empty array for empty string', () => {
    expect(parseLinks('')).toEqual([])
  })
})
