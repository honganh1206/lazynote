# Antinote — Electron rebuild design

**Date:** 2026-06-29
**Status:** Approved (brainstorming)

## Goal

Rebuild the app off Rust/Tauri onto a less flamboyant, widely-used, TS-friendly
Linux desktop stack with mature libraries. Full feature parity.

## Decisions

- **Stack:** Electron + TypeScript (the ubiquitous Linux desktop stack: VS Code,
  Slack, Obsidian, Discord).
- **UI:** Fresh rewrite in **Svelte 5** (same framework, new code).
- **Editor:** **CodeMirror 6** replaces the transparent-textarea overlay trick.
- **DB:** SQLite via **better-sqlite3** (most-used Node SQLite). Schema unchanged.
- **Tooling:** **electron-vite** (scaffold/build), **electron-builder** (package).

## Why Electron

All current UI/logic is already web tech. Rust was only a thin ~190-line shell
(window config, global hotkey, tray, SQLite migrations, an X11 `XInitThreads`
crash workaround). Every feature maps to a mature, built-in Electron API:

| Need | Tauri now | Electron equiv |
|------|-----------|----------------|
| Window (frameless/transparent/always-on-top) | tauri.conf | `BrowserWindow` opts |
| Global hotkey | plugin-global-shortcut | `globalShortcut` (built-in) |
| Tray | tray-icon crate | `Tray` (built-in) |
| SQLite | plugin-sql | `better-sqlite3` |
| Open URL | plugin-opener | `shell.openExternal` |
| X11 thread crash | `XInitThreads` hack | not needed — removed |

Trade-off: ~80–100MB binary, higher RAM. Irrelevant for a desktop scratchpad. In
return: no Rust, no gtk/webkit dev-deps, consistent Chromium rendering, trivial
to review.

## Process architecture

Standard secure Electron 3-layer split.

```
src/
  main/                  # Node/Electron main process (replaces Rust shell)
    main.ts              # create BrowserWindow (frameless, transparent, alwaysOnTop, 360x360)
    window.ts            # window lifecycle + geometry persist (on-screen guard)
    tray.ts              # Tray + Menu; click -> act or send IPC
    shortcuts.ts         # globalShortcut Alt+A toggle show/hide
    db.ts                # better-sqlite3: open, migrate, CRUD
    settings.ts          # app_settings get/set
    ipc.ts               # ipcMain.handle registrations
  preload/
    preload.ts           # contextBridge -> window.api (typed)
  renderer/              # Svelte 5 UI
    App.svelte
    Editor.svelte        # CodeMirror 6 wrapper
    SlashPicker.svelte
    lib/
      noteState.svelte.ts
      api.ts             # thin wrapper over window.api
      editor/            # CM6 extensions (decorations, links, theme, keymap)
      parse/             # PURE: todo.ts, links.ts  (unit-tested)
      types.ts
```

Security: `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`.

## IPC bridge (`window.api`)

```
notes:    list() · create(content?) · update(id, content) · delete(id)
settings: get(key) · set(key, value)
shell:    openExternal(url)
window:   setAlwaysOnTop(b) · hide() · show()
events:   onTray(cb)   // 'new-note' | 'toggle-aot' | 'toggle-auto-hide' | 'quit'
```

All DB/shell work via `ipcMain.handle` (async). Renderer never touches Node.

## Editor — CodeMirror 6

Single `EditorView`. **Text protocol unchanged**: `todo:` first line, `/x`
checked suffix, `#` headings, `//` comments, `/` slash trigger. Only rendering
changes.

A `ViewPlugin` recomputes decorations on each update, branching on mode (first
line -> `todo` vs plain):

- **Headings** `#/##/###` -> line mark class `h1/h2/h3`
- **Comments** `//...` (todo) -> line class `comment`
- **Checked** lines ending `/x` -> strikethrough + `☑` widget; `/x` token hidden
  via replace decoration **unless cursor on that line** (CM6 reveal-markup-at-cursor
  pattern). Matches current cursor-line behavior.
- **Checkboxes** -> `☐` widget at line start (todo mode)
- **Keyword line** (todo) -> greyed
- **Links** -> clickable mark; `EditorView.domEventHandlers.mousedown` ->
  `window.api.shell.openExternal`. Link parsing stays a pure module.
- **Theme**: reproduce current look (`#faf8f5` bg, colors, hanging-indent
  checkbox, 15px / 1.7 line-height).
- **Autosave**: `updateListener` on `docChanged` -> 500ms debounce ->
  `window.api.notes.update`.
- **Keymap**: Ctrl+H/L/N/D via high-precedence CM keymap.
- **Slash picker**: when doc first line is exactly `/`, show `SlashPicker.svelte`;
  selection dispatches a CM transaction inserting the keyword.

## Feature parity

All current features survive: multi-note nav + counter, debounced autosave,
Alt+A toggle, tray menu (show/hide, new note, toggle always-on-top, toggle
auto-hide, quit), geometry persist, auto-hide-on-blur, auto-create-on-launch,
always-on-top persist, todo/plain/slash modes, clickable links.

## Data flow

Renderer `noteState.svelte.ts` holds notes array + index + content (`$state`),
calls `window.api`, routed by `ipcMain.handle` to `db.ts` (better-sqlite3,
synchronous — off the UI thread). Tray/shortcut events: main -> preload ->
`onTray` callback -> state actions.

## DB migration

Same schema. Path = `app.getPath('userData')/notes.db`. On first launch, if the
old Tauri DB exists at `~/.config/com.honganh.antinote-linux/notes.db`, copy it
to preserve existing notes.

## Packaging / CI

electron-builder -> `.AppImage` + `.deb` (same artifacts as current CI). Rewrite
`.github/workflows/release.yml`. `better-sqlite3` native module rebuilt via
`@electron/rebuild` in postinstall + CI.

## Testing

- **vitest** unit tests for pure parsers (`parse/todo.ts`, `parse/links.ts`) —
  the high-value reviewable core.
- Small integration tests for `db.ts` against a temp SQLite file.
- CM6 view layer kept thin (delegates to pure parsers).

## Trade-offs accepted

- Binary ~80–100MB, higher RAM — fine for a scratchpad.
- Global shortcut on Wayland: same limit as today; degrade gracefully (tray works).
- `better-sqlite3` native rebuild step in CI.
