import Database from 'better-sqlite3'

export type DB = Database.Database

export interface Note {
  id: number
  content: string
  sort_index: number
  created_at: number
  updated_at: number
}

export function openDb(path: string): DB {
  const db = new Database(path)
  db.pragma('journal_mode = WAL')
  db.pragma('busy_timeout = 3000')

  db.exec(`
    CREATE TABLE IF NOT EXISTS notes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      content TEXT NOT NULL DEFAULT '',
      sort_index INTEGER NOT NULL UNIQUE,
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS app_settings (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL
    );
  `)

  const seed = db.prepare(
    `INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)`
  )
  seed.run('auto_create_note_on_launch', 'true')
  seed.run('always_on_top', 'true')

  return db
}

export class NotesRepo {
  private listStmt
  private maxIndexStmt
  private insertStmt
  private getStmt
  private updateStmt
  private deleteStmt

  constructor(db: DB) {
    this.listStmt = db.prepare(`SELECT * FROM notes ORDER BY sort_index ASC`)
    this.maxIndexStmt = db.prepare(`SELECT MAX(sort_index) AS max FROM notes`)
    this.insertStmt = db.prepare(
      `INSERT INTO notes (content, sort_index, created_at, updated_at) VALUES (?, ?, ?, ?)`
    )
    this.getStmt = db.prepare(`SELECT * FROM notes WHERE id = ?`)
    this.updateStmt = db.prepare(
      `UPDATE notes SET content = ?, updated_at = ? WHERE id = ?`
    )
    this.deleteStmt = db.prepare(`DELETE FROM notes WHERE id = ?`)
  }

  list(): Note[] {
    return this.listStmt.all() as Note[]
  }

  create(content = ''): Note {
    const row = this.maxIndexStmt.get() as { max: number | null }
    const nextIndex = (row.max ?? 0) + 1
    const now = Date.now()
    const info = this.insertStmt.run(content, nextIndex, now, now)
    return this.getStmt.get(Number(info.lastInsertRowid)) as Note
  }

  update(id: number, content: string): void {
    this.updateStmt.run(content, Date.now(), id)
  }

  delete(id: number): void {
    this.deleteStmt.run(id)
  }
}

export class SettingsRepo {
  private getStmt
  private setStmt

  constructor(db: DB) {
    this.getStmt = db.prepare(`SELECT value FROM app_settings WHERE key = ?`)
    this.setStmt = db.prepare(
      `INSERT INTO app_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value`
    )
  }

  get(key: string): string | null {
    const row = this.getStmt.get(key) as { value: string } | undefined
    return row ? row.value : null
  }

  set(key: string, value: string): void {
    this.setStmt.run(key, value)
  }
}
