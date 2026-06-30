# Antinote for Linux — Agent Context

## Project Overview

Antinote for Linux is a lightweight, always-accessible scratchpad for temporary
notes. Built with **Electron + Svelte 5 + TypeScript + CodeMirror 6**. Single
frameless window, no routing or SSR.

- **App identifier:** `com.honganh.antinote-linux`
- **Product name:** Antinote
- **Package manager:** npm (NOT yarn or pnpm)
- **Frontend framework:** Plain Svelte 5 (NOT SvelteKit)
- **Editor:** CodeMirror 6
- **Build tool:** electron-vite; packaging via electron-builder

## Tech Stack

- **Main process:** Electron (Node) — window, tray, global shortcut, SQLite
- **Renderer:** Svelte 5 + CodeMirror 6
- **Database:** SQLite via `better-sqlite3` (synchronous, in the main process)
- **IPC:** `ipcMain.handle` + a typed `contextBridge` preload (`window.api`)

## Architecture

Standard secure Electron 3-layer split:

```
app/
  main/                 # Node — privileged code (replaces the old Rust shell)
    index.ts            # app lifecycle, BrowserWindow creation, wiring
    window.ts           # geometry persistence + on-screen guard + auto-hide-on-blur
    geometry.ts         # PURE geometry helpers (unit-tested)
    tray.ts             # system tray + menu
    shortcuts.ts        # global hotkey Alt+A
    db.ts               # better-sqlite3 repos + migrations (unit-tested)
    store.ts            # DB singleton + migrate old Tauri DB on first launch
    ipc.ts              # ipcMain.handle registrations
  preload/
    index.ts            # contextBridge → window.api (typed)
  renderer/
    index.html          # Vite entry (-> src/main.ts)
    src/
      App.svelte        # shell: editor + slash picker + indicator + tray events
      Editor.svelte     # CodeMirror 6 wrapper (owns the EditorView)
      SlashPicker.svelte
      lib/
        api.ts          # single import point for window.api
        noteState.svelte.ts   # reactive note state (runes)
        parse/          # PURE parsers: links.ts, todo.ts, mode.ts (unit-tested)
        editor/         # CM6: decorations.ts (tested), extensions.ts, theme.ts
```

Security: `contextIsolation: true`, `nodeIntegration: false`. (`sandbox: false`
is required for the electron-vite ESM preload; the bridge surface stays narrow.)
The renderer never touches Node directly — all DB/shell/window work goes over
`window.api` → `ipcMain.handle`.

## Key Conventions

### Svelte 5 Runes
- Files using `$state`/`$derived`/etc. **must** use the `.svelte.ts` extension
  (e.g., `noteState.svelte.ts`). Regular `.ts` files cannot use runes.
- Shared reactive state lives in `.svelte.ts` under `app/renderer/src/lib/`,
  exposed via getter/setter functions (not exported `$state` variables directly).

### CSS in Svelte
- **Never import CSS files** into Svelte components — it causes rendering bugs.
  Use `<style>` blocks. The only global stylesheet is `app/renderer/src/assets/main.css`
  (a minimal reset), imported once in `main.ts`.

### Pure parsers + tested core
- `lib/parse/*` and `lib/editor/decorations.ts` (`computeRanges`) and
  `main/geometry.ts` (`isOnScreen`/`parseGeometry`) and `main/db.ts` are PURE
  and unit-tested with vitest. View/Electron glue is kept thin and verified by
  running the app. Keep new logic testable.

### Database
- `db.ts` exposes `openDb(path)`, `NotesRepo`, `SettingsRepo`. Schema matches the
  old Tauri app (`notes`, `app_settings`) so existing data migrates.
- `store.ts` opens the DB at `app.getPath('userData')/notes.db` (`~/.config/Antinote`)
  and, on first launch, copies the old Tauri DB from
  `~/.config/com.honganh.antinote-linux/notes.db` if present.
- `app.setName('Antinote')` MUST run before `initStore()` (it determines userData).

### better-sqlite3 ABI (IMPORTANT)
- Native module built for **Electron** via `npm run rebuild`. **vitest runs under
  Node**, so DB tests need: `npm rebuild better-sqlite3` → `npm test` →
  `npm run rebuild` (restore Electron build). Always restore at the end.

## Text Protocol (editor)
First line decides the mode:
- `todo` / `todo: <title>` → todo mode. Lines: `#`/`##`/`### ` heading; `//` comment;
  trailing `/x` = checked (hidden + struck unless the cursor is on that line); else
  an unchecked checklist item.
- a lone `/` on line 1 → slash picker (insert a keyword).
- otherwise → plain mode: `#`/`##`/`### ` headings, plain text.
URLs are clickable in both modes (open in the default browser).

## Window
- 400×400 default, 360×360 minimum, frameless, transparent, resizable.
- Always-on-top: enabled by default, persisted in DB, applied by the renderer on launch.
- Geometry (position+size) persisted with an on-screen guard.
- Global hotkey Alt+A toggles show/hide (may not register on Wayland — degrades
  gracefully; the tray still works).

## Build & Run
```bash
npm install && npm run rebuild   # install + build better-sqlite3 for Electron
npm run dev                       # electron-vite dev + Electron window
npm run check                     # svelte-check (renderer) + tsc (main)
npm test                          # vitest (see better-sqlite3 ABI note)
npm run build                     # build bundles to out/
npm run package                   # .deb + .AppImage to dist/
```

## CI/CD
- `.github/workflows/release.yml` triggers on `v*` tag push, builds on
  `ubuntu-22.04`, and publishes a draft GitHub release with `.deb` + `.AppImage`.
- `release.sh` bumps the version in `package.json` (the single source of truth).
