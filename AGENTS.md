# Antinote for Linux — Agent Context

## Project Overview

Antinote for Linux is a lightweight, always-accessible scratchpad for temporary notes. Built with **Tauri 2 + Svelte 5 + TypeScript**. Single-window desktop app, no routing or SSR.

- **App identifier:** `com.honganh.antinote-linux`
- **Product name:** Antinote
- **Window title:** "Antinote (dev)" for dev builds
- **Package manager:** npm (NOT yarn or pnpm)
- **Frontend framework:** Plain Svelte 5 (NOT SvelteKit)
- **Frontend build output:** `../dist` (plain Vite output)

## Tech Stack

- **Frontend:** Svelte 5, TypeScript, Vite
- **Backend:** Tauri 2 (Rust)
- **Database:** SQLite via `@tauri-apps/plugin-sql`
- **Plugins:** `plugin-sql`, `plugin-global-shortcut`, built-in tray API

## Key Conventions

### Svelte 5 Runes

- Files using `$state`, `$derived`, or other Svelte 5 runes **must** use the `.svelte.ts` extension (e.g., `noteState.svelte.ts`)
- Regular `.ts` files **cannot** use runes

### Rust Module Organization

- Feature-per-module pattern: each feature gets its own module file (e.g., `shortcuts.rs`, `tray.rs`)
- Each module exposes `pub fn setup(app: &App)` (or `pub fn setup(app: &mut App)` if needed)
- `lib.rs` is a thin orchestrator that calls each module's `setup()` in the `.setup()` closure
- Modules are called under `#[cfg(desktop)]` guard

### Frontend State Management

- Shared reactive state lives in `.svelte.ts` files under `src/lib/`
- `noteState.svelte.ts` manages notes array, current index, content, save timer
- State is exposed via getter/setter functions, not exported `$state` variables directly

### CSS in Svelte

- **Never import CSS files** into Svelte components (e.g., `import './styles.css'`)
- Always modify CSS directly within `<style>` blocks in Svelte files
- Importing external CSS files causes rendering bugs (app gets squished on launch)

### Database

- `db.ts` is a **singleton** — `getDb()` caches the Database instance
- Do NOT call `Database.load()` in multiple places
- `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=3000` set on first connection
- SQLite DB is at Tauri's default AppConfig path (`~/.config/com.honganh.antinote-linux/notes.db`)
- Migrations are defined in `src-tauri/src/migrations.rs` and run by `tauri-plugin-sql`
- `getSetting(key)` / `setSetting(key, value)` for app_settings table

## Window Configuration

- Size: 360×360, not decorated (system titlebar), resizable
- Always-on-top: enabled by default, persisted in DB
- Global hotkey: Alt+A to toggle show/hide

## Linux-Specific Notes

- Target: Pop!_OS 22.04 (X11)
- System tray requires `libayatana-appindicator3-dev` (NOT `libappindicator3-dev`)
- Tray requires `tray-icon` feature in Cargo.toml
- Do NOT rely on tray click events on Linux — use tray menu only
- Global hotkey may not work on Wayland — app degrades gracefully

## Project Structure

```
src/                    # Frontend (Svelte 5 + TypeScript)
  lib/
    db.ts               # Singleton DB service
    noteState.svelte.ts # Reactive note state (runes)
    types.ts            # TypeScript types
  App.svelte            # Main app component
src-tauri/              # Backend (Rust + Tauri 2)
  src/
    lib.rs              # Thin orchestrator
    main.rs             # Entry point
    migrations.rs       # SQLite migrations
    shortcuts.rs        # Global hotkey (Alt+A)
  capabilities/
    default.json        # Tauri permissions
  tauri.conf.json       # Tauri configuration
tasks/                  # PRD, roadmap, test strategy
```

## Build & Run

```bash
# Development
npm run dev          # Vite dev server only (no Tauri plugins)
cargo tauri dev      # Full app with Tauri plugins (use this!)

# Build
cargo tauri build    # Production build (.deb, .AppImage)
```

## CI/CD

- GitHub Actions at `.github/workflows/release.yml`
- Triggers on `v*` tag push, builds .deb and .AppImage
- `release.sh` handles version bumping
