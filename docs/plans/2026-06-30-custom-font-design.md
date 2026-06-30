# Custom Font Selection — Design

Date: 2026-06-30

## Goal

Let the user choose the editor font (family + size) instead of the hardcoded
default. Global (applies to all notes), monospace-only, picked from an in-app
settings popup. Mirrors the existing theme system's persistence + bridge wiring.

## Decisions

- **Scope**: global — one font for the whole app, like `theme`.
- **Adjustable**: family + size (size currently hardcoded at 15px).
- **Picker UI**: in-app settings popup with a font dropdown + size stepper.
- **Restriction**: monospace (fixed-pitch) families only.
- **Bridge shape**: a `font` QVariantMap property (pattern A — mirrors `colors`).

## Data model & persistence

Two new keys in the existing `SettingsRepo` (same store as `theme`):

- `font_family` (str) — empty means "use default".
- `font_size` (str, parsed as int) — empty means default `15`.

Defaults are resolved in the bridge (not written to the store until the user
picks):

- Default family = `QFontDatabase.systemFont(QFontDatabase.FixedFont).family()`
  (the system monospace font).
- Default size = `15`.
- Size clamped to `[8, 32]`.

## Pure helper (testable, no Qt)

Extract defaulting/clamping into a pure module `src/lazynote/fonts.py`, mirroring
how `theme.py` stays free of PySide6 so it can be unit-tested:

```
resolve_font(family: str, size, available: list[str], default_family: str)
    -> dict   # {"family": str, "size": int}
```

Rules:
- size: parse to int, fall back to 15 on bad input, clamp to [8, 32].
- family: if empty OR not in `available`, use `default_family`.

## Backend API (`bridge.py`)

Mirror the theme members:

- `fontChanged = Signal()`
- `font = Property("QVariantMap", _font, notify=fontChanged)` — getter calls
  `fonts.resolve_font(...)` using the stored keys + `mono_families()` +
  the system fixed font, returns `{"family", "size"}`.
- `@Slot(str, int) set_font(family, size)` — clamp size, persist both keys,
  emit `fontChanged`.
- `@Slot(result="QStringList") mono_families()` — families from
  `QFontDatabase.families()` where `QFontDatabase.isFixedPitch(f)`, sorted.
  If none are fixed-pitch, fall back to the full family list (never empty).

## QML font application

On the `Editor` root, expose a convenience binding:

```qml
readonly property var fnt: backend ? backend.font : ({family: "", size: 15})
```

Apply at the three text sites in `Editor.qml`, replacing `font.pixelSize: 15`:

- `:183` checkbox glyph (☐/☑) — `font.family: root.fnt.family; font.pixelSize: root.fnt.size`
- `:210` static styled line (`rowText`) — same
- `:257` editable raw line (`TextInput`) — same

Live-reactive through `fontChanged`. Render spans set only color/italic/strike
(no font in the HTML), so family + size apply cleanly with no heading conflict.

Chrome stays fixed: status counter (`Main.qml:139`) and `SlashPicker` labels.

## Settings popup + trigger

New `src/lazynote/qml/SettingsPopup.qml` — a `Popup` styled like `SlashPicker`
(bg/text from `backend.colors`):

- `ComboBox` — model = `backend.mono_families()`, current = `backend.font.family`.
- Size control — SpinBox or +/− steppers, range 8–32.
- Live apply on change → `backend.set_font(family, size)`.

Triggers (both):
- Tray menu item `"Settings…"` added near the theme items in `Main.qml`.
- `Shortcut { sequence: "Ctrl+," }` opens the popup.

## Error handling / fallback

- `set_font`: clamp size to `[8, 32]`; ignore empty family (keep current).
- Stored family no longer installed → `font` getter falls back to the default
  monospace (handled in `resolve_font` via the `available` check).
- `mono_families()` empty → fall back to full family list so the combo is never
  empty.

## Testing

- `tests/test_fonts.py` against the pure helper: size clamp bounds (low/high/bad
  input), empty family → default, uninstalled family → default, valid passthrough.
- Bridge slots are thin Qt wrappers — untested, consistent with the rest of
  `bridge.py`.

## Out of scope (YAGNI)

- Per-note fonts.
- Proportional (non-monospace) fonts.
- Native FontDialog.
- Font weight/style selection beyond family + size.
