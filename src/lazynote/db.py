"""SQLite storage (stdlib sqlite3). Schema matches the original app so data migrates."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass


@dataclass
class Note:
    id: int
    content: str
    sort_index: int
    created_at: int
    updated_at: int


def _now_ms() -> int:
    return int(time.time() * 1000)


def open_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 3000")
    conn.executescript(
        """
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
        """
    )
    conn.executemany(
        "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
        [
            ("auto_create_note_on_launch", "true"),
            ("always_on_top", "true"),
            ("link_shortening", "true"),
            ("hyperlink_features", "true"),
        ],
    )
    conn.commit()
    return conn


class NotesRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list(self) -> list[Note]:
        rows = self._conn.execute("SELECT * FROM notes ORDER BY sort_index ASC").fetchall()
        return [Note(**dict(r)) for r in rows]

    def create(self, content: str = "") -> Note:
        row = self._conn.execute("SELECT MAX(sort_index) AS m FROM notes").fetchone()
        next_index = (row["m"] or 0) + 1
        now = _now_ms()
        cur = self._conn.execute(
            "INSERT INTO notes (content, sort_index, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (content, next_index, now, now),
        )
        self._conn.commit()
        return Note(int(cur.lastrowid), content, next_index, now, now)

    def update(self, note_id: int, content: str) -> None:
        self._conn.execute(
            "UPDATE notes SET content = ?, updated_at = ? WHERE id = ?",
            (content, _now_ms(), note_id),
        )
        self._conn.commit()

    def delete(self, note_id: int) -> None:
        self._conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self._conn.commit()


class SettingsRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get(self, key: str) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def set(self, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT INTO app_settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self._conn.commit()
