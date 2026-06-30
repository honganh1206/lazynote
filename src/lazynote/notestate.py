"""Note collection + current-note state. Ported from noteState.svelte.ts.

Pure of Qt (operates on the db repos), so it's unit-testable. The debounced
autosave timer lives in the QML bridge; here `save_current()` is the flush.
"""

from __future__ import annotations

from lazynote.db import Note, NotesRepo, SettingsRepo


class NoteState:
    def __init__(self, notes_repo: NotesRepo, settings_repo: SettingsRepo) -> None:
        self._notes_repo = notes_repo
        self._settings = settings_repo
        self.notes: list[Note] = []
        self.index = 0
        self.content = ""

    def current(self) -> Note | None:
        if 0 <= self.index < len(self.notes):
            return self.notes[self.index]
        return None

    def count(self) -> int:
        return len(self.notes)

    def load(self) -> None:
        self.notes = self._notes_repo.list()
        auto_create = self._settings.get("auto_create_note_on_launch") != "false"
        if not self.notes:
            self.notes = [self._notes_repo.create()]
        elif auto_create:
            latest = self.notes[-1]
            if latest.content.strip():
                self.notes.append(self._notes_repo.create())
        self.index = len(self.notes) - 1
        self.content = self.notes[self.index].content

    def set_content(self, value: str) -> None:
        self.content = value

    def save_current(self) -> None:
        note = self.current()
        if note is None:
            return
        self._notes_repo.update(note.id, self.content)
        note.content = self.content

    def navigate_to(self, index: int) -> bool:
        if index < 0 or index >= len(self.notes):
            return False
        self.save_current()
        self.index = index
        self.content = self.notes[self.index].content
        return True

    def navigate(self, delta: int) -> bool:
        return self.navigate_to(self.index + delta)

    def add(self) -> None:
        self.save_current()
        note = self._notes_repo.create()
        self.notes.append(note)
        self.index = len(self.notes) - 1
        self.content = ""

    def remove_current(self) -> None:
        note = self.current()
        if note is None:
            return
        self._notes_repo.delete(note.id)
        self.notes = [n for n in self.notes if n.id != note.id]
        if not self.notes:
            self.notes = [self._notes_repo.create()]
            self.index = 0
            self.content = ""
        elif self.index >= len(self.notes):
            self.index = len(self.notes) - 1
            self.content = self.notes[self.index].content
        else:
            self.content = self.notes[self.index].content
