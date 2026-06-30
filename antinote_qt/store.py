"""DB singleton + first-launch import of a legacy notes database.

Config dir is ~/.config/antinote-qt/ (honours $XDG_CONFIG_HOME). On first launch,
if no DB exists yet, copy one from a legacy Electron/Tauri install if present.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from antinote_qt.db import NotesRepo, SettingsRepo, open_db

_notes: NotesRepo | None = None
_settings: SettingsRepo | None = None

_LEGACY_DB_PATHS = [
    Path.home() / ".config" / "Antinote" / "notes.db",  # Electron build
    Path.home() / ".config" / "com.honganh.antinote-linux" / "notes.db",  # Tauri build
]


def config_dir() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericConfigLocation)
    root = Path(base) if base else Path.home() / ".config"
    return root / "antinote-qt"


def init_store() -> None:
    global _notes, _settings
    d = config_dir()
    d.mkdir(parents=True, exist_ok=True)
    db_path = d / "notes.db"
    if not db_path.exists():
        for legacy in _LEGACY_DB_PATHS:
            if legacy.exists():
                shutil.copyfile(legacy, db_path)
                # Bring the WAL sidecars too, so notes not yet checkpointed into
                # the main file are preserved.
                for suffix in ("-wal", "-shm"):
                    side = legacy.with_name(legacy.name + suffix)
                    if side.exists():
                        shutil.copyfile(side, db_path.with_name(db_path.name + suffix))
                break
    conn = open_db(str(db_path))
    _notes = NotesRepo(conn)
    _settings = SettingsRepo(conn)


def get_notes() -> NotesRepo:
    if _notes is None:
        raise RuntimeError("Store not initialized — call init_store() first")
    return _notes


def get_settings() -> SettingsRepo:
    if _settings is None:
        raise RuntimeError("Store not initialized — call init_store() first")
    return _settings
