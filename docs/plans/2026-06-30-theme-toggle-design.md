# Light/Dark Theme Toggle — Design

Date: 2026-06-30

## Goal

Let the user switch between light and dark appearance. Follow the OS theme by
default, with a manual override available from the system tray.

## Theme model — 3-state setting

A single setting `theme` with values `system` (default) | `light` | `dark`:

- `system` — follow the OS color scheme.
- `light` / `dark` — pin an explicit override.

The *effective scheme* (always concretely `light` or `dark`) is what paints the
UI. When `theme == "system"` it is derived from the OS; otherwise it equals the
override.

Exposed in the tray as a **Theme submenu** with three radio items: System,
Light, Dark.

## Single source of truth — `theme.py`

Colors are currently scattered across `editormodel.py` (palette constants),
`Editor.qml`, and `Main.qml`. Centralize into a new pure module `theme.py`:

```python
PALETTES = {
    "dark":  {text, muted, amber, green, blue, bg, selection},
    "light": {text, muted, amber, green, blue, bg, selection},
}

def resolve_scheme(mode: str) -> str:  # "light" | "dark"
    # mode in {"system","light","dark"}; reads OS when "system".

def palette_for(mode: str) -> dict:
    return PALETTES[resolve_scheme(mode)]
```

OS detection uses `QGuiApplication.styleHints().colorScheme()` (PySide6 6.5+;
project ships 6.11). `Qt.ColorScheme.Dark` → `dark`, else `light`.

### Palette keys

| key       | dark      | light (proposed) |
|-----------|-----------|------------------|
| text      | `#d6d3cc` | `#2b2a27`        |
| muted     | `#6f6b64` | `#9a948b`        |
| amber     | `#e6a86b` | `#b9701f`        |
| green     | `#84c08a` | `#3f8f47`        |
| blue      | `#79b8e0` | `#2f7bb0`        |
| bg        | `#1f2023` | `#f4f2ec`        |
| selection | `#34363b` | `#d8d3c7`        |

Light values are a first pass — dark text on warm near-white, same hue families
darkened for contrast. Tunable later.

## editormodel changes

`_KIND_STYLE` switches from hardcoded color strings to palette *keys*
(`"amber"`, `"green"`, ...). `line_render_spans` gains a `palette: dict`
parameter and resolves keys → hex against it. Stays pure (no PySide6), so unit
tests cover both palettes.

## Backend wiring (`bridge.py`)

`Backend` gains:

- `themeChanged = Signal()`
- `colors` — `Property("QVariantMap", notify=themeChanged)` returning the
  effective palette dict; QML binds to `backend.colors.text` etc.
- `theme` — `Property(str, notify=themeChanged)` returning the mode string (for
  radio checkmarks).
- `set_theme(mode)` slot — persist via `store.get_settings().set("theme", mode)`,
  then emit `themeChanged` and `contentChanged` (so static line spans re-render
  in the new palette).
- In `__init__`, connect `QGuiApplication.styleHints().colorSchemeChanged` →
  emit `themeChanged` **only when** the stored mode is `system`.

`line_render` reads the effective palette and passes it to `line_render_spans`.

## QML changes

- `Editor.qml`: `colText`, `colMuted`, and the `TextInput` `selectionColor`
  bind to `backend.colors.*` instead of literals.
- `Main.qml`: panel `Rectangle.color` and the status `Text.color` bind to
  `backend.colors.*`. Add the Theme submenu to the tray menu; each item calls
  `backend.set_theme(...)` and shows `checked: backend.theme === "..."`.

## Data flow

```
tray radio -> backend.set_theme(mode) -> settings persist
                                       -> themeChanged -> QML colors rebind
                                       -> contentChanged -> spans re-render
OS scheme change -> colorSchemeChanged -> (if mode==system) themeChanged -> rebind
```

## Testing

`theme.py` and `editormodel` projection are pure:

- `resolve_scheme`: explicit `light`/`dark` returned as-is; `system` maps OS
  scheme correctly (monkeypatch the OS query).
- `palette_for` returns the expected dict per mode.
- `line_render_spans` yields different colors under light vs dark for the same
  input; default (no setting) resolves to system.

QML binding is verified manually by running the app and toggling the tray menu.
