import {
  Decoration,
  EditorView,
  WidgetType,
  type DecorationSet,
} from '@codemirror/view'
import { detectMode } from '../parse/mode'
import { parseLinks } from '../parse/links'

export type RangeKind =
  | 'heading1'
  | 'heading2'
  | 'heading3'
  | 'comment'
  | 'keyword'
  | 'checkbox-checked'
  | 'checkbox-unchecked'
  | 'link'
  | 'hide-x'

export interface Range {
  from: number
  to: number
  kind: RangeKind
}

const HEADING_RE = /^(#{1,3}) /

function headingKind(level: number): RangeKind {
  return level === 1 ? 'heading1' : level === 2 ? 'heading2' : 'heading3'
}

/**
 * Emit `link` ranges for every URL in `lineText`, converted to absolute
 * document offsets relative to `lineStart`. `parseLinks` returns contiguous
 * segments, so we track a running offset within the line to locate each URL.
 */
function emitLinks(lineText: string, lineStart: number, out: Range[]): void {
  let local = 0
  for (const seg of parseLinks(lineText)) {
    if (seg.type === 'link') {
      out.push({
        from: lineStart + local,
        to: lineStart + local + seg.value.length,
        kind: 'link',
      })
    }
    local += seg.value.length
  }
}

/**
 * PURE: compute decoration ranges for `doc` given the (0-indexed) line the
 * selection head is on. Encodes the text protocol and cursor-reveal rule.
 */
export function computeRanges(doc: string, selHeadLine: number): Range[] {
  const ranges: Range[] = []
  const lines = doc.split('\n')
  const isTodo = detectMode(doc)?.keyword === 'todo'

  let offset = 0
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const lineStart = offset
    const lineEnd = lineStart + line.length
    // advance offset for the next iteration (account for the '\n' separator)
    offset = lineEnd + 1

    // ── todo keyword line ──────────────────────────────────────────────
    if (isTodo && i === 0) {
      ranges.push({ from: lineStart, to: lineEnd, kind: 'keyword' })
      // No link parsing on the keyword line.
      continue
    }

    // blank line: nothing line-classified, no links possible.
    if (line.trim() === '') {
      continue
    }

    // ── headings (both modes) ──────────────────────────────────────────
    const heading = line.match(HEADING_RE)
    if (heading) {
      ranges.push({
        from: lineStart,
        to: lineEnd,
        kind: headingKind(heading[1].length),
      })
      emitLinks(line, lineStart, ranges)
      continue
    }

    if (isTodo) {
      // ── comment ──────────────────────────────────────────────────────
      if (line.startsWith('//')) {
        ranges.push({ from: lineStart, to: lineEnd, kind: 'comment' })
        emitLinks(line, lineStart, ranges)
        continue
      }

      // ── checked item (cursor-reveal rule) ────────────────────────────
      if (line.endsWith('/x')) {
        if (selHeadLine === i) {
          // cursor on the line → render raw/editing: unchecked, keep `/x`.
          ranges.push({ from: lineStart, to: lineEnd, kind: 'checkbox-unchecked' })
        } else {
          // cursor elsewhere → render checked + hide the trailing `/x`.
          ranges.push({ from: lineStart, to: lineEnd, kind: 'checkbox-checked' })
          ranges.push({ from: lineEnd - 2, to: lineEnd, kind: 'hide-x' })
        }
        emitLinks(line, lineStart, ranges)
        continue
      }

      // ── unchecked item ───────────────────────────────────────────────
      ranges.push({ from: lineStart, to: lineEnd, kind: 'checkbox-unchecked' })
      emitLinks(line, lineStart, ranges)
      continue
    }

    // ── plain mode, non-heading: plain text (no checkbox), links only ──
    emitLinks(line, lineStart, ranges)
  }

  return ranges
}

// ── Translator (thin; not unit-tested) ────────────────────────────────

class CheckboxWidget extends WidgetType {
  constructor(readonly checked: boolean) {
    super()
  }

  eq(other: CheckboxWidget): boolean {
    return other.checked === this.checked
  }

  toDOM(): HTMLElement {
    const box = document.createElement('span')
    box.className = this.checked
      ? 'cm-checkbox cm-checkbox-checked'
      : 'cm-checkbox cm-checkbox-unchecked'
    box.setAttribute('aria-hidden', 'true')
    box.textContent = this.checked ? '☑' : '☐'
    return box
  }

  ignoreEvent(): boolean {
    return false
  }
}

const checkedBox = Decoration.widget({
  widget: new CheckboxWidget(true),
  side: -1,
})
const uncheckedBox = Decoration.widget({
  widget: new CheckboxWidget(false),
  side: -1,
})

const lineDeco: Record<string, Decoration> = {
  heading1: Decoration.line({ class: 'cm-h1' }),
  heading2: Decoration.line({ class: 'cm-h2' }),
  heading3: Decoration.line({ class: 'cm-h3' }),
  comment: Decoration.line({ class: 'cm-comment' }),
  keyword: Decoration.line({ class: 'cm-keyword' }),
  'checkbox-checked': Decoration.line({ class: 'cm-checked' }),
}

const hideX = Decoration.replace({})

/**
 * Translate `computeRanges` output into a CodeMirror DecorationSet for the
 * given view. Decorations are collected into an array and handed to
 * `Decoration.set(_, true)` which sorts by `from`/startSide, sidestepping the
 * strict-ordering requirements of `RangeSetBuilder`.
 */
export function buildDecorations(view: EditorView): DecorationSet {
  const doc = view.state.doc.toString()
  const selHeadLine =
    view.state.doc.lineAt(view.state.selection.main.head).number - 1
  const ranges = computeRanges(doc, selHeadLine)

  const decos: Array<ReturnType<Decoration['range']>> = []

  for (const r of ranges) {
    switch (r.kind) {
      case 'heading1':
      case 'heading2':
      case 'heading3':
      case 'comment':
      case 'keyword':
        decos.push(lineDeco[r.kind].range(r.from))
        break
      case 'checkbox-checked':
        decos.push(lineDeco[r.kind].range(r.from))
        decos.push(checkedBox.range(r.from))
        break
      case 'checkbox-unchecked':
        decos.push(uncheckedBox.range(r.from))
        break
      case 'link':
        decos.push(
          Decoration.mark({
            class: 'cm-link',
            attributes: { 'data-url': doc.slice(r.from, r.to) },
          }).range(r.from, r.to),
        )
        break
      case 'hide-x':
        decos.push(hideX.range(r.from, r.to))
        break
    }
  }

  return Decoration.set(decos, true)
}
