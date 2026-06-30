<script lang="ts">
  import { onMount } from 'svelte'
  import Editor from './Editor.svelte'
  import SlashPicker from './SlashPicker.svelte'
  import { api } from './lib/api'
  import {
    loadNotes,
    getContent,
    setContent,
    scheduleSave,
    flushSave,
    addNote,
    getCurrentIndex,
    noteCount,
  } from './lib/noteState.svelte'
  import { detectMode } from './lib/parse/mode'

  let editor: Editor

  let alwaysOnTop = $state(true)

  // Reads of the noteState getters are tracked across modules, so these derived
  // values update whenever the editor mutates content via setContent().
  const content = $derived(getContent())
  const mode = $derived(detectMode(content)?.keyword ?? null)
  const showSlashPicker = $derived(content.split('\n')[0] === '/')

  function handleSlashSelect(keyword: string): void {
    const c = getContent()
    const nl = c.indexOf('\n')
    const rest = nl !== -1 ? c.slice(nl) : ''
    setContent(keyword + rest)
    editor.setDoc(getContent())
    editor.focus()
    scheduleSave()
  }

  function handleSlashDismiss(): void {
    editor.focus()
  }

  async function handleTray(action: string): Promise<void> {
    if (action === 'new-note') {
      await addNote()
      editor.setDoc(getContent())
      editor.focus()
    } else if (action === 'toggle-aot') {
      alwaysOnTop = !alwaysOnTop
      api.window.setAlwaysOnTop(alwaysOnTop)
      api.settings.set('always_on_top', alwaysOnTop ? 'true' : 'false')
    } else if (action === 'toggle-auto-hide') {
      const current = (await api.settings.get('auto_hide_on_blur')) !== 'false'
      const next = !current
      api.settings.set('auto_hide_on_blur', next ? 'true' : 'false')
    } else if (action === 'quit') {
      await flushSave()
    }
  }

  onMount(() => {
    let off: (() => void) | undefined

    void (async () => {
      await loadNotes()
      editor.setDoc(getContent())
      editor.focus()

      const aot = (await api.settings.get('always_on_top')) !== 'false'
      alwaysOnTop = aot
      api.window.setAlwaysOnTop(aot)

      off = api.onTray(handleTray)
    })()

    return () => {
      off?.()
      void flushSave()
    }
  })
</script>

<main>
  <div class="drag-region"></div>
  <div class="editor-wrap">
    <Editor bind:this={editor} />
  </div>
  {#if showSlashPicker}
    <SlashPicker onselect={handleSlashSelect} ondismiss={handleSlashDismiss} />
  {/if}
  <div class="position">
    {#if mode}{mode} · {/if}{getCurrentIndex() + 1}/{noteCount()}
  </div>
</main>

<style>
  main {
    position: relative;
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #faf8f5;
    border-radius: 10px;
    overflow: hidden;
  }
  .drag-region {
    flex: 0 0 16px;
    height: 16px;
    width: 100%;
    -webkit-app-region: drag;
  }
  .editor-wrap {
    flex: 1 1 auto;
    min-height: 0;
    -webkit-app-region: no-drag;
  }
  .position {
    position: absolute;
    bottom: 8px;
    right: 12px;
    font-size: 11px;
    color: #b0a99f;
    user-select: none;
    pointer-events: none;
  }
</style>
