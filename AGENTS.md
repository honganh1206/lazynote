# Antinote for Linux — Agent Context

## Project Overview

Antinote for Linux is a lightweight, always-accessible scratchpad for temporary notes. Built with **Electron + Svelte 5 + TypeScript + CodeMirror 6**. Single-window desktop app, no routing or SSR.

The app is being rebuilt off Tauri/Rust onto Electron; the active implementation plan
lives at `docs/plans/2026-06-29-electron-rebuild.md`. New code lives under `app/`.

- **App identifier:** `com.antinote.app`
- **Product name:** Antinote
- **Package manager:** npm (NOT yarn or pnpm)
- **Frontend framework:** Plain Svelte 5 (NOT SvelteKit)

## Tech Stack

- **Shell:** Electron (electron-vite build, electron-builder packaging)
- **Main process:** Node + TypeScript (window, tray, global shortcut, DB)
- **Renderer:** Svelte 5 + CodeMirror 6 (`@codemirror/{state,view,commands}`)
- **IPC:** `preload` exposes a typed `window.api` via `contextBridge`; the renderer never touches Node
- **Database:** SQLite via `better-sqlite3` (native module, rebuilt for Electron's ABI)
- **Tests:** vitest (pure logic — parsers, db)

## Architecture

Standard secure Electron 3-layer split:

- `app/main/` — Node-side privileged work; all DB/window/shortcut/tray logic. Exposes operations over `ipcMain.handle`.
- `app/preload/` — `contextBridge` bridge mapping IPC channels to a typed `window.api`.
- `app/renderer/` — Svelte 5 UI + CodeMirror 6 editor. No direct Node access.

## Key Conventions

### Svelte 5 Runes

- Files using `$state`, `$derived`, or other Svelte 5 runes **must** use the `.svelte.ts` extension (e.g., `noteState.svelte.ts`)
- Regular `.ts` files **cannot** use runes

### Main Process Module Organization

- Feature-per-module pattern: each feature gets its own module file (e.g., `shortcuts.ts`, `tray.ts`, `db.ts`)
- `main/index.ts` is a thin orchestrator that wires up window creation, IPC handlers, and each module on `app.whenReady()`

### Frontend State Management

- Shared reactive state lives in `.svelte.ts` files under `app/renderer/src/`
- `noteState.svelte.ts` manages notes array, current index, content, save timer
- State is exposed via getter/setter functions, not exported `$state` variables directly

### CSS in Svelte

- **Never import CSS files** into Svelte components (e.g., `import './styles.css'`)
- Always modify CSS directly within `<style>` blocks in Svelte files
- Importing external CSS files causes rendering bugs (app gets squished on launch)

### Database

- DB access lives in the **main process** (`app/main/db.ts`); the renderer reaches it via `window.api`
- `openDb(path)` is a **singleton** — cache the `Database` instance; do NOT open it in multiple places
- `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=3000` set on first connection
- SQLite DB lives under Electron's `app.getPath('userData')`
- Migrations are idempotent (`CREATE TABLE IF NOT EXISTS`). Schema (carried over from the
  old app, must match): `notes(id, content, sort_index UNIQUE, created_at, updated_at)`
  and `app_settings(key, value)`, seeding `auto_create_note_on_launch=true` and
  `always_on_top=true`
- `getSetting(key)` / `setSetting(key, value)` for the `app_settings` table

## Window Configuration

- Size: 360×360, frameless (no system titlebar), resizable
- Always-on-top: enabled by default, persisted in DB
- Global hotkey: Alt+A to toggle show/hide

## Linux-Specific Notes

- Target: Pop!_OS 22.04 (X11)
- Do NOT rely on tray click events on Linux — use tray menu only
- Global hotkey may not work on Wayland — app degrades gracefully

## Project Structure

```
app/                    # Electron app source
  main/
    index.ts            # Main process orchestrator
  preload/
    index.ts            # contextBridge → typed window.api
  renderer/
    index.html          # Renderer entry
    src/                # Svelte 5 + CodeMirror 6 UI
electron.vite.config.ts # electron-vite config (main/preload/renderer inputs)
electron-builder.yml    # Packaging config
tsconfig*.json          # TypeScript project references
tasks/                  # PRD, roadmap, test strategy
docs/plans/             # Implementation plan(s)
```

> Note: the legacy Tauri code (`src/`, `src-tauri/`) is kept temporarily as a port/reference
> source for the rebuild and is removed in the final cleanup phase.

## Build & Run

```bash
# Development
npm install
npm run rebuild      # rebuild better-sqlite3 for Electron's ABI
npm run dev          # electron-vite dev server + Electron window

# Build & package
npm run build        # build main/preload/renderer bundles
npm run package      # build + electron-builder (.deb, .AppImage)

# Tests / typecheck
npm test             # vitest
npm run check        # svelte-check
```

## CI/CD

- `release.sh` bumps the version in `package.json`
- A `v*` tag push is intended to trigger a GitHub Actions release workflow (to be added
  for the Electron build; the old Tauri workflow has been removed)
