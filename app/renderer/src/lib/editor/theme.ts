import { EditorView } from '@codemirror/view'

/**
 * Antinote-style dark theme (first pass). Warm charcoal panel, off-white text,
 * muted warm accents. Colors are an interpretation of Antinote's dark look, not
 * sampled pixel-exact — tune to taste. Checklist lines use a hanging indent so
 * the ☐/☑ widget (rendered by decorations.ts as `.cm-checkbox`) sits in a
 * gutter-like space to the left of the wrapped text.
 *
 * Palette (single source of truth — change here):
 *   panel    #1f2023   bg
 *   text     #d6d3cc   default foreground
 *   muted    #6f6b64   comments / keyword line / checked
 *   sel      #34363b   selection
 *   amber    #e6a86b   h1
 *   green    #84c08a   h2
 *   blue     #79b8e0   h3 / links
 */
const PANEL = '#1f2023'
const TEXT = '#d6d3cc'
const MUTED = '#6f6b64'
const SEL = '#34363b'

export const antinoteTheme = EditorView.theme(
  {
    '&': {
      backgroundColor: PANEL,
      color: TEXT,
      fontFamily: 'system-ui, -apple-system, sans-serif',
      fontSize: '15px',
      height: '100%',
    },
    '.cm-editor': {
      height: '100%',
    },
    '.cm-scroller': {
      overflow: 'auto',
      lineHeight: '1.7',
      fontFamily: 'system-ui, -apple-system, sans-serif',
    },
    '.cm-content': {
      padding: '0.75rem 1.25rem',
      caretColor: TEXT,
    },
    // Hanging indent: wrapped text and checklist glyphs align with a left gutter.
    '.cm-line': {
      paddingLeft: '1.4em',
      textIndent: '-1.4em',
    },
    '.cm-cursor, .cm-dropCursor': {
      borderLeftColor: TEXT,
    },
    '&.cm-focused': {
      outline: 'none',
    },
    '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection': {
      backgroundColor: SEL,
    },
    // Heading colors (warm amber / green / blue).
    '.cm-h1': { color: '#e6a86b' },
    '.cm-h2': { color: '#84c08a' },
    '.cm-h3': { color: '#79b8e0' },
    // Muted syntax.
    '.cm-comment': { color: MUTED, fontStyle: 'italic' },
    '.cm-keyword': { color: MUTED },
    '.cm-checked': { color: MUTED, textDecoration: 'line-through' },
    // Links.
    '.cm-link': { color: '#79b8e0', cursor: 'pointer' },
    '.cm-link:hover': { textDecoration: 'underline' },
    // Checkbox widgets (☑/☐) rendered with class `cm-checkbox` by decorations.ts.
    '.cm-checkbox': {
      color: MUTED,
      // Reserve space matching the hanging indent so the glyph sits in the gutter.
      display: 'inline-block',
      width: '1.4em',
      textIndent: '0',
    },
  },
  { dark: true },
)
