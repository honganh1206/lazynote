<script lang="ts">
  import { onMount } from 'svelte'
  import { EditorView } from '@codemirror/view'
  import { EditorState } from '@codemirror/state'
  import { createEditorExtensions, type EditorCallbacks } from './lib/editor/extensions'
  import {
    getContent,
    setContent,
    scheduleSave,
    navigatePrev,
    navigateNext,
    addNote,
    removeCurrentNote,
  } from './lib/noteState.svelte'

  let host: HTMLDivElement
  let view: EditorView | undefined

  // Set while we programmatically replace the whole doc. CodeMirror fires its
  // updateListener synchronously inside dispatch(), so this flag lets us skip
  // the autosave onChange for content we just loaded (avoids a redundant save).
  let suppressChange = false

  function replaceDoc(text: string): void {
    if (!view) return
    suppressChange = true
    view.dispatch({
      changes: { from: 0, to: view.state.doc.length, insert: text },
    })
    suppressChange = false
  }

  async function handleDelete(): Promise<void> {
    if (getContent().trim().length > 0) {
      if (!confirm('Delete this note?')) return
    }
    await removeCurrentNote()
    replaceDoc(getContent())
    view?.focus()
  }

  const callbacks: EditorCallbacks = {
    onChange(doc) {
      if (suppressChange) return
      setContent(doc)
      scheduleSave()
    },
    async onNavigate(delta) {
      await (delta < 0 ? navigatePrev() : navigateNext())
      replaceDoc(getContent())
    },
    async onNewNote() {
      await addNote()
      replaceDoc(getContent())
      view?.focus()
    },
    onDelete() {
      void handleDelete()
    },
  }

  // Instance methods exposed to the parent (App.svelte) via bind:this. Svelte 5
  // exposes top-level `export function`s as members of the component instance.
  export function setDoc(text: string): void {
    replaceDoc(text)
  }

  export function focus(): void {
    view?.focus()
  }

  onMount(() => {
    const state = EditorState.create({
      doc: getContent(),
      extensions: createEditorExtensions(callbacks),
    })
    view = new EditorView({ state, parent: host })
    view.focus()

    return () => {
      view?.destroy()
      view = undefined
    }
  })
</script>

<div class="editor-host" bind:this={host}></div>

<style>
  .editor-host {
    height: 100%;
  }
</style>
