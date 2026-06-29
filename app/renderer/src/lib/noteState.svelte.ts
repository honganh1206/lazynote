import { api, type Note } from './api'

let notes = $state<Note[]>([])
let currentIndex = $state(0)
let content = $state('')

let saveTimer: ReturnType<typeof setTimeout> | null = null
let pendingSave = false

function currentNote(): Note | undefined {
  return notes[currentIndex]
}

export function getNotes(): Note[] {
  return notes
}
export function getCurrentIndex(): number {
  return currentIndex
}
export function getContent(): string {
  return content
}
export function setContent(value: string) {
  content = value
}
export function noteCount(): number {
  return notes.length
}

export async function loadNotes() {
  notes = await api.notes.list()
  const autoCreate = (await api.settings.get('auto_create_note_on_launch')) !== 'false'
  if (notes.length === 0) {
    const note = await api.notes.create()
    notes = [note]
  } else if (autoCreate) {
    const latest = notes[notes.length - 1]
    if (latest.content.trim().length > 0) {
      const note = await api.notes.create()
      notes = [...notes, note]
    }
  }
  currentIndex = notes.length - 1
  content = notes[currentIndex].content
}

export function scheduleSave() {
  pendingSave = true
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => flushSave(), 500)
}

export async function flushSave() {
  if (saveTimer) {
    clearTimeout(saveTimer)
    saveTimer = null
  }
  const note = currentNote()
  if (!pendingSave || !note) return
  pendingSave = false
  await api.notes.update(note.id, content)
  note.content = content
  note.updated_at = Date.now()
}

export async function navigateTo(index: number) {
  if (index < 0 || index >= notes.length) return
  await flushSave()
  currentIndex = index
  content = notes[currentIndex].content
}

export async function navigatePrev() {
  if (currentIndex > 0) {
    await navigateTo(currentIndex - 1)
  }
}

export async function navigateNext() {
  if (currentIndex < notes.length - 1) {
    await navigateTo(currentIndex + 1)
  }
}

export async function addNote() {
  await flushSave()
  const note = await api.notes.create()
  notes = [...notes, note]
  currentIndex = notes.length - 1
  content = ''
}

export async function removeCurrentNote() {
  const note = currentNote()
  if (!note) return
  await api.notes.delete(note.id)
  notes = notes.filter((n) => n.id !== note.id)
  if (notes.length === 0) {
    const newNote = await api.notes.create()
    notes = [newNote]
    currentIndex = 0
    content = ''
  } else if (currentIndex >= notes.length) {
    currentIndex = notes.length - 1
    content = notes[currentIndex].content
  } else {
    content = notes[currentIndex].content
  }
}
