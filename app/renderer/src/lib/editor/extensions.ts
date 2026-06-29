import {
  EditorView,
  ViewPlugin,
  keymap,
  type ViewUpdate,
  type DecorationSet,
} from '@codemirror/view'
import { Prec } from '@codemirror/state'
import { history, historyKeymap } from '@codemirror/commands'
import { buildDecorations } from './decorations'
import { antinoteTheme } from './theme'
import { api } from '../api'

export interface EditorCallbacks {
  onChange: (doc: string) => void
  onNavigate: (delta: -1 | 1) => void
  onNewNote: () => void
  onDelete: () => void
}

export function createEditorExtensions(cb: EditorCallbacks) {
  // Decoration plugin: rebuild on doc/selection/viewport changes (selection
  // drives the /x cursor-reveal rule in decorations.ts).
  const decorationPlugin = ViewPlugin.fromClass(
    class {
      decorations: DecorationSet
      constructor(view: EditorView) {
        this.decorations = buildDecorations(view)
      }
      update(u: ViewUpdate) {
        if (u.docChanged || u.selectionSet || u.viewportChanged)
          this.decorations = buildDecorations(u.view)
      }
    },
    {
      decorations: (v) => v.decorations,
      eventHandlers: {
        mousedown(event: MouseEvent) {
          const target = event.target as HTMLElement
          const linkEl = target.closest('.cm-link') as HTMLElement | null
          if (linkEl) {
            const url = linkEl.getAttribute('data-url')
            if (url) {
              event.preventDefault()
              void api.shell.openExternal(url)
              return true
            }
          }
          return false
        },
      },
    },
  )

  const saveListener = EditorView.updateListener.of((u) => {
    if (u.docChanged) cb.onChange(u.state.doc.toString())
  })

  // High precedence so our app bindings win over CodeMirror defaults.
  const appKeymap = Prec.high(
    keymap.of([
      { key: 'Ctrl-h', run: () => { cb.onNavigate(-1); return true } },
      { key: 'Ctrl-l', run: () => { cb.onNavigate(1); return true } },
      { key: 'Ctrl-n', run: () => { cb.onNewNote(); return true } },
      { key: 'Ctrl-d', run: () => { cb.onDelete(); return true } },
    ]),
  )

  return [
    appKeymap,
    decorationPlugin,
    saveListener,
    history(),
    keymap.of(historyKeymap),
    EditorView.lineWrapping,
    antinoteTheme,
  ]
}
