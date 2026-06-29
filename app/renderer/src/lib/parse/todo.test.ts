import { describe, it, expect } from 'vitest'
import { parseTodoLines, parsePlainLines } from './todo'

describe('parseTodoLines', () => {
  it('skips the keyword line and classifies the rest', () => {
    const out = parseTodoLines('todo:\nbuy milk\ndone /x\n// note\n## H')
    expect(out.map(l => l.type)).toEqual([
      'checklist-item', 'checklist-item-checked', 'comment', 'heading',
    ])
  })
  it('strips the /x token from checked text', () => {
    const [line] = parseTodoLines('todo:\ntask /x')
    expect(line).toMatchObject({ type: 'checklist-item-checked', text: 'task ' })
  })
})
describe('parsePlainLines', () => {
  it('classifies headings and text', () => {
    const out = parsePlainLines('# Title\nbody')
    expect(out[0]).toMatchObject({ type: 'heading', headingLevel: 1 })
    expect(out[1]).toMatchObject({ type: 'checklist-item', text: 'body' })
  })
})
