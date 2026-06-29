import { app } from 'electron'
import { join } from 'node:path'
import { homedir } from 'node:os'
import { existsSync, copyFileSync, mkdirSync } from 'node:fs'
import { openDb, NotesRepo, SettingsRepo } from './db'

let notes: NotesRepo
let settings: SettingsRepo

// IMPORTANT: initStore() must run AFTER any app.setName(...) call (done in
// app/main/index.ts) and AFTER app.whenReady(), because app.getPath('userData')
// is derived from the app name and is only reliable once the app is ready.
export function initStore(): void {
  const dir = app.getPath('userData')
  mkdirSync(dir, { recursive: true })
  const dbPath = join(dir, 'notes.db')
  // Preserve notes from the old Tauri build: copy its DB on first launch only.
  const oldPath = join(homedir(), '.config', 'com.honganh.antinote-linux', 'notes.db')
  if (!existsSync(dbPath) && existsSync(oldPath)) copyFileSync(oldPath, dbPath)
  const db = openDb(dbPath)
  notes = new NotesRepo(db)
  settings = new SettingsRepo(db)
}

export function getNotes(): NotesRepo {
  if (!notes) throw new Error('Store not initialized — call initStore() first')
  return notes
}

export function getSettings(): SettingsRepo {
  if (!settings) throw new Error('Store not initialized — call initStore() first')
  return settings
}
