import { EditorView } from '@codemirror/view'

/**
 * Light theme reproducing the original Antinote look. Colors and metrics are
 * eyeballed-to-parity, not pixel-exact. Checklist lines use a hanging indent so
 * the ☐/☑ widget (rendered by decorations.ts as `.cm-checkbox`) sits in a
 * gutter-like space to the left of the wrapped text.
 */
export const antinoteTheme = EditorView.theme(
  {
    '&': {
      backgroundColor: '#faf8f5',
      color: '#2c2c2c',
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
      caretColor: '#2c2c2c',
    },
    // Hanging indent: wrapped text and checklist glyphs align with a left gutter.
    '.cm-line': {
      paddingLeft: '1.4em',
      textIndent: '-1.4em',
    },
    '.cm-cursor, .cm-dropCursor': {
      borderLeftColor: '#2c2c2c',
    },
    '&.cm-focused': {
      outline: 'none',
    },
    '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection': {
      backgroundColor: '#e8e1d6',
    },
    // Heading colors.
    '.cm-h1': { color: '#d45d00' },
    '.cm-h2': { color: '#2e8b57' },
    '.cm-h3': { color: '#5a7ec2' },
    // Muted syntax.
    '.cm-comment': { color: '#b0a99f', fontStyle: 'italic' },
    '.cm-keyword': { color: '#b0a99f' },
    '.cm-checked': { color: '#b0a99f', textDecoration: 'line-through' },
    // Links.
    '.cm-link': { color: '#5a7ec2', cursor: 'pointer' },
    '.cm-link:hover': { textDecoration: 'underline' },
    // Checkbox widgets (☑/☐) rendered with class `cm-checkbox` by decorations.ts.
    '.cm-checkbox': {
      color: '#b0a99f',
      // Reserve space matching the hanging indent so the glyph sits in the gutter.
      display: 'inline-block',
      width: '1.4em',
      textIndent: '0',
    },
  },
  { dark: false },
)
