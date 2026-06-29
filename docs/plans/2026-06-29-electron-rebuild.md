# Antinote Electron Rebuild — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild Antinote off Tauri/Rust onto Electron + TypeScript with a fresh Svelte 5 UI and a CodeMirror 6 editor, preserving 100% feature parity.

**Architecture:** Standard secure Electron 3-layer split — `main/` (Node: window, tray, global shortcut, better-sqlite3 DB), `preload/` (contextBridge → typed `window.api`), `renderer/` (Svelte 5 + CodeMirror 6). All privileged work goes over `ipcMain.handle`; the renderer never touches Node. Syntax modes (todo/plain/links) render via CM6 decorations driven by pure, unit-tested parsers.

**Tech Stack:** Electron, TypeScript, electron-vite (`@quick-start/electron` svelte-ts template), Svelte 5, CodeMirror 6 (`@codemirror/{state,view,commands}`), better-sqlite3, vitest, electron-builder.

**Working location:** branch `electron-rebuild` (already created; design doc committed there).

---

## Conventions

- The new app is built **alongside** the old code, then the old `src-tauri/` + Tauri `src/` are deleted at the end (Phase 9). This keeps the repo buildable/comparable during the rebuild.
- New code lives under `app/` (`app/main`, `app/preload`, `app/renderer`) so it never collides with the old `src/` until cleanup.
- TDD where logic is pure (parsers, db). Electron/CM6 glue is verified by running the app (manual smoke steps included).
- Commit after every task. Conventional Commit messages.
- Reference @superpowers:test-driven-development for the red→green→commit loop.

## Text protocol (unchanged from current app — do not alter)

- First line decides mode: `todo` or `todo: <title>` → **todo mode**; a lone `/` on line 1 → **slash picker**; otherwise **plain mode**.
- Todo mode lines: `#`/`##`/`### ` → heading; `//…` → comment; line ending `/x` → checked item (strikethrough); else unchecked checklist item.
- Plain mode lines: `#`/`##`/`### ` → heading; everything else literal.
- URLs (`https?://…`) are clickable in both modes.
- Checked `/x` token is hidden in rendering **except on the line containing the cursor**.

---

## Phase 0 — Scaffold Electron + Svelte + tooling

### Task 0.1: Scaffold electron-vite svelte-ts app into a temp dir, relocate to `app/`

**Files:**
- Create: `app/`, `electron.vite.config.ts`, `package.json` (merge), `tsconfig*.json`

**Step 1:** Scaffold in scratch, then copy the pieces we want.
```bash
cd /home/honganh/projects/antinote-linux
npm create @quick-start/electron@latest .ev-tmp -- --template svelte-ts --skip
```
Expected: creates `.ev-tmp/` with `src/main`, `src/preload`, `src/renderer`, `electron.vite.config.ts`, `electron-builder.yml`.

**Step 2:** Move scaffold layout into `app/` and root config.
```bash
mkdir -p app
cp -r .ev-tmp/src/main app/main
cp -r .ev-tmp/src/preload app/preload
cp -r .ev-tmp/src/renderer app/renderer
cp .ev-tmp/electron.vite.config.ts .
cp .ev-tmp/electron-builder.yml .
cp .ev-tmp/tsconfig.node.json .ev-tmp/tsconfig.web.json .ev-tmp/tsconfig.json .
```
Adjust `electron.vite.config.ts` input paths to point at `app/main/index.ts`, `app/preload/index.ts`, `app/renderer/index.html` (per electron-vite custom-structure config).

**Step 3:** Merge dependencies into the existing root `package.json`. Replace `@tauri-apps/*` deps. Final `dependencies`/`devDependencies` should include:
```jsonc
// dependencies
"better-sqlite3": "^11",
"@codemirror/state": "^6",
"@codemirror/view": "^6",
"@codemirror/commands": "^6"
// devDependencies
"electron": "^33",
"electron-vite": "^2",
"electron-builder": "^25",
"@electron/rebuild": "^3",
"@sveltejs/vite-plugin-svelte": "^5",
"svelte": "^5",
"svelte-check": "^4",
"typescript": "^5",
"vitest": "^2",
"@types/better-sqlite3": "^7"
```
Set scripts:
```jsonc
"scripts": {
  "dev": "electron-vite dev",
  "build": "electron-vite build",
  "start": "electron-vite preview",
  "test": "vitest run",
  "rebuild": "electron-rebuild -f -w better-sqlite3",
  "package": "electron-vite build && electron-builder",
  "check": "svelte-check --tsconfig ./tsconfig.web.json"
}
```

**Step 4:** Install + native rebuild.
```bash
rm -rf .ev-tmp node_modules package-lock.json
npm install
npm run rebuild
```
Expected: installs cleanly; `electron-rebuild` reports `better-sqlite3` rebuilt for the Electron ABI.

**Step 5:** Smoke-run the untouched scaffold.
```bash
npm run dev
```
Expected: a default electron-vite Svelte window opens. Close it.

**Step 6: Commit**
```bash
git add -A
git commit -m "chore: scaffold electron-vite + svelte-ts app shell"
```

### Task 0.2: Set up vitest

**Files:**
- Create: `vitest.config.ts`

**Step 1:** Create config:
```ts
import { defineConfig } from 'vitest/config'
export default defineConfig({ test: { environment: 'node', include: ['app/**/*.test.ts'] } })
```
**Step 2:** Add a trivial `app/sanity.test.ts` asserting `expect(1).toBe(1)`. Run `npm test`. Expected: 1 passing. Delete the sanity file.
**Step 3: Commit** `git add -A && git commit -m "chore: add vitest config"`

---

## Phase 1 — Pure parsers (TDD, ported verbatim in behavior)

These are framework-free and fully testable. Port logic from old `src/lib/links.ts` and `src/lib/keywords/todo.ts`, add the test suite they never had.

### Task 1.1: `links.ts` parser + tests

**Files:**
- Create: `app/renderer/lib/parse/links.ts`, `app/renderer/lib/parse/links.test.ts`

**Step 1: Write failing tests** (`links.test.ts`):
```ts
import { describe, it, expect } from 'vitest'
import { parseLinks } from './links'

describe('parseLinks', () => {
  it('returns single text segment for plain text', () => {
    expect(parseLinks('hello world')).toEqual([
      { type: 'text', value: 'hello world', displayValue: 'hello world' },
    ])
  })
  it('extracts a url segment', () => {
    const segs = parseLinks('see https://example.com now')
    expect(segs.map(s => s.type)).toEqual(['text', 'link', 'text'])
    expect(segs[1]).toMatchObject({ type: 'link', fullUrl: 'https://example.com' })
  })
  it('keeps url inside parens balanced', () => {
    const segs = parseLinks('(https://en.wikipedia.org/wiki/A_(b))')
    const link = segs.find(s => s.type === 'link')!
    expect(link.fullUrl).toBe('https://en.wikipedia.org/wiki/A_(b)')
  })
  it('returns empty array for empty string', () => {
    expect(parseLinks('')).toEqual([])
  })
})
```
**Step 2:** Run `npx vitest run app/renderer/lib/parse/links.test.ts` → FAIL (module missing).
**Step 3:** Port implementation from old `src/lib/links.ts` (copy `LinkSegment`, `URL_REGEX`, `parseLinks` verbatim; drop unused `MAX_DISPLAY_LENGTH`).
**Step 4:** Run tests → PASS.
**Step 5: Commit** `git commit -am "feat: port link parser with tests"`

### Task 1.2: `todo.ts` line classifier + tests

**Files:**
- Create: `app/renderer/lib/parse/todo.ts`, `app/renderer/lib/parse/todo.test.ts`

**Step 1: Write failing tests** covering each `LineType`:
```ts
import { describe, it, expect } from 'vitest'
import { parseTodoLines, parsePlainLines } from './todo'

describe('parseTodoLines', () => {
  it('skips the keyword line and classifies the rest', () => {
    const out = parseTodoLines('todo:\nbuy milk\ndone /x\n// note\n## H')
    expect(out.map(l => l.type)).toEqual([
      'checklist-item', 'checklist-item-checked', 'comment', 'heading',
    ])
  })
  it('strips the /x token from checked text', () => {
    const [line] = parseTodoLines('todo:\ntask /x')
    expect(line).toMatchObject({ type: 'checklist-item-checked', text: 'task ' })
  })
})
describe('parsePlainLines', () => {
  it('classifies headings and text', () => {
    const out = parsePlainLines('# Title\nbody')
    expect(out[0]).toMatchObject({ type: 'heading', headingLevel: 1 })
    expect(out[1]).toMatchObject({ type: 'checklist-item', text: 'body' })
  })
})
```
**Step 2:** Run → FAIL.
**Step 3:** Port `src/lib/keywords/todo.ts` verbatim (types + `parseTodoLines`, `parsePlainLines`, `classifyLine`, `classifyPlainLine`).
**Step 4:** Run → PASS.
**Step 5: Commit** `git commit -am "feat: port todo line classifier with tests"`

### Task 1.3: Mode detection (extract from old `keywords.svelte.ts`)

**Files:**
- Create: `app/renderer/lib/parse/mode.ts`, `app/renderer/lib/parse/mode.test.ts`

**Step 1: Failing tests:**
```ts
import { describe, it, expect } from 'vitest'
import { detectMode, REGISTERED_KEYWORDS } from './mode'

describe('detectMode', () => {
  it('detects todo with title', () => {
    expect(detectMode('todo: groceries\n...')).toEqual({ keyword: 'todo', title: 'groceries' })
  })
  it('detects bare todo', () => {
    expect(detectMode('todo')).toEqual({ keyword: 'todo', title: '' })
  })
  it('returns null for plain text', () => {
    expect(detectMode('just a note')).toBeNull()
  })
  it('exposes registered keywords', () => {
    expect(REGISTERED_KEYWORDS).toContain('todo')
  })
})
```
**Step 2:** Run → FAIL.
**Step 3:** Implement pure `detectMode(content): { keyword, title } | null` and `REGISTERED_KEYWORDS = ['todo']`, porting the regex (`/^(\w+)(?::\s*(.*))?$/`) and keyword-allowlist logic from old `keywords.svelte.ts` — but as a pure function (no `$derived`, takes content arg).
**Step 4:** Run → PASS.
**Step 5: Commit** `git commit -am "feat: pure mode detection with tests"`

---

## Phase 2 — Main process: DB + settings + IPC

### Task 2.1: better-sqlite3 DB module with migrations + tests

**Files:**
- Create: `app/main/db.ts`, `app/main/db.test.ts`

**Step 1: Failing tests** (inject a temp path so tests don't touch userData):
```ts
import { describe, it, expect, beforeEach } from 'vitest'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { openDb, NotesRepo, SettingsRepo } from './db'

function freshDb() {
  const dir = mkdtempSync(join(tmpdir(), 'antinote-'))
  return openDb(join(dir, 'notes.db'))
}

describe('NotesRepo', () => {
  it('creates and lists notes ordered by sort_index', () => {
    const db = freshDb(); const notes = new NotesRepo(db)
    const a = notes.create('first'); const b = notes.create('second')
    expect(notes.list().map(n => n.id)).toEqual([a.id, b.id])
    expect(b.sort_index).toBeGreaterThan(a.sort_index)
  })
  it('updates content and bumps updated_at', () => {
    const db = freshDb(); const notes = new NotesRepo(db)
    const n = notes.create('x'); notes.update(n.id, 'y')
    expect(notes.list()[0].content).toBe('y')
  })
  it('deletes a note', () => {
    const db = freshDb(); const notes = new NotesRepo(db)
    const n = notes.create('x'); notes.delete(n.id)
    expect(notes.list()).toHaveLength(0)
  })
})

describe('SettingsRepo', () => {
  it('seeds defaults and round-trips', () => {
    const db = freshDb(); const s = new SettingsRepo(db)
    expect(s.get('always_on_top')).toBe('true')
    s.set('always_on_top', 'false')
    expect(s.get('always_on_top')).toBe('false')
  })
})
```
**Step 2:** Run → FAIL.
**Step 3:** Implement `app/main/db.ts`:
- `openDb(path)`: `new Database(path)`, `pragma('journal_mode = WAL')`, `pragma('busy_timeout = 3000')`, then run migrations (idempotent `CREATE TABLE IF NOT EXISTS` for `notes` and `app_settings`, matching the old schema in `src-tauri/src/migrations.rs`; seed `auto_create_note_on_launch=true`, `always_on_top=true` via `INSERT OR IGNORE`). Return the `Database`.
- `NotesRepo` with `list()/create(content='')/update(id,content)/delete(id)` using prepared statements; `create` computes `sort_index = MAX(sort_index)+1` and returns the row (use `lastInsertRowid`).
- `SettingsRepo` with `get(key)/set(key,value)` (`INSERT … ON CONFLICT(key) DO UPDATE`).
- Export a `Note` interface identical to old `types.ts`.
**Step 4:** Run → PASS.
**Step 5: Commit** `git commit -am "feat: better-sqlite3 db + settings repos with tests"`

### Task 2.2: App DB singleton with old-DB migration on first launch

**Files:**
- Create: `app/main/store.ts`

**Step 1:** Implement (no unit test — depends on Electron `app`):
```ts
import { app } from 'electron'
import { join } from 'node:path'
import { homedir } from 'node:os'
import { existsSync, copyFileSync, mkdirSync } from 'node:fs'
import { openDb, NotesRepo, SettingsRepo } from './db'

let notes: NotesRepo, settings: SettingsRepo
export function initStore() {
  const dir = app.getPath('userData')
  mkdirSync(dir, { recursive: true })
  const dbPath = join(dir, 'notes.db')
  const oldPath = join(homedir(), '.config', 'com.honganh.antinote-linux', 'notes.db')
  if (!existsSync(dbPath) && existsSync(oldPath)) copyFileSync(oldPath, dbPath) // preserve Tauri notes
  const db = openDb(dbPath)
  notes = new NotesRepo(db); settings = new SettingsRepo(db)
}
export const getNotes = () => notes
export const getSettings = () => settings
```
**Step 2:** Set `app.setName('Antinote')` early in `main/index.ts` so `userData` = `~/.config/Antinote`. (Document this in code comment.)
**Step 3: Commit** `git commit -am "feat: db store singleton + migrate old tauri db"`

### Task 2.3: IPC handlers

**Files:**
- Create: `app/main/ipc.ts`
- Modify: `app/main/index.ts`

**Step 1:** Implement `registerIpc()` wiring `ipcMain.handle` channels to repos + shell:
```ts
import { ipcMain, shell, BrowserWindow } from 'electron'
import { getNotes, getSettings } from './store'
export function registerIpc() {
  ipcMain.handle('notes:list', () => getNotes().list())
  ipcMain.handle('notes:create', (_e, content?: string) => getNotes().create(content ?? ''))
  ipcMain.handle('notes:update', (_e, id: number, content: string) => getNotes().update(id, content))
  ipcMain.handle('notes:delete', (_e, id: number) => getNotes().delete(id))
  ipcMain.handle('settings:get', (_e, key: string) => getSettings().get(key))
  ipcMain.handle('settings:set', (_e, key: string, value: string) => getSettings().set(key, value))
  ipcMain.handle('shell:openExternal', (_e, url: string) => shell.openExternal(url))
  ipcMain.handle('win:setAlwaysOnTop', (e, b: boolean) =>
    BrowserWindow.fromWebContents(e.sender)?.setAlwaysOnTop(b))
  ipcMain.handle('win:hide', (e) => BrowserWindow.fromWebContents(e.sender)?.hide())
  ipcMain.handle('win:show', (e) => { const w = BrowserWindow.fromWebContents(e.sender); w?.show(); w?.focus() })
}
```
**Step 2:** Call `initStore()` then `registerIpc()` inside `app.whenReady()` in `main/index.ts`.
**Step 3: Commit** `git commit -am "feat: ipc handlers for notes/settings/shell/window"`

---

## Phase 3 — Preload bridge + shared types

### Task 3.1: Typed `window.api` preload

**Files:**
- Modify: `app/preload/index.ts`
- Create: `app/preload/api.d.ts`

**Step 1:** Implement preload with `contextBridge.exposeInMainWorld('api', …)`:
```ts
import { contextBridge, ipcRenderer } from 'electron'
import type { Note } from '../main/db'

const api = {
  notes: {
    list: (): Promise<Note[]> => ipcRenderer.invoke('notes:list'),
    create: (content?: string): Promise<Note> => ipcRenderer.invoke('notes:create', content),
    update: (id: number, content: string) => ipcRenderer.invoke('notes:update', id, content),
    delete: (id: number) => ipcRenderer.invoke('notes:delete', id),
  },
  settings: {
    get: (key: string): Promise<string | null> => ipcRenderer.invoke('settings:get', key),
    set: (key: string, value: string) => ipcRenderer.invoke('settings:set', key, value),
  },
  shell: { openExternal: (url: string) => ipcRenderer.invoke('shell:openExternal', url) },
  window: {
    setAlwaysOnTop: (b: boolean) => ipcRenderer.invoke('win:setAlwaysOnTop', b),
    hide: () => ipcRenderer.invoke('win:hide'),
    show: () => ipcRenderer.invoke('win:show'),
  },
  onTray: (cb: (action: TrayAction) => void) => {
    const h = (_: unknown, a: TrayAction) => cb(a)
    ipcRenderer.on('tray', h)
    return () => ipcRenderer.removeListener('tray', h)
  },
}
export type TrayAction = 'new-note' | 'toggle-aot' | 'toggle-auto-hide' | 'quit'
contextBridge.exposeInMainWorld('api', api)
export type Api = typeof api
```
**Step 2:** Create `app/preload/api.d.ts` declaring `interface Window { api: Api }` (global). Ensure `tsconfig.web.json` includes it.
**Step 3:** Confirm `webPreferences` in `main/index.ts`: `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`, `preload` path set.
**Step 4: Commit** `git commit -am "feat: typed contextBridge preload api"`

---

## Phase 4 — Renderer state

### Task 4.1: `api.ts` thin wrapper + `noteState.svelte.ts`

**Files:**
- Create: `app/renderer/lib/api.ts` (re-exports `window.api` with types for ergonomic import)
- Create: `app/renderer/lib/noteState.svelte.ts`

**Step 1:** Port old `src/lib/noteState.svelte.ts` nearly verbatim, swapping `./db` calls for `window.api.notes` / `window.api.settings`. Keep: `notes`/`currentIndex`/`content` `$state`, `loadNotes` (incl. `auto_create_note_on_launch` logic), `scheduleSave`/`flushSave` (500ms debounce), `navigateTo/Prev/Next`, `addNote`, `removeCurrentNote`, getters/setters.
**Step 2:** No unit test (depends on `window.api`); verified live in Phase 6 smoke. Type-check: `npm run check`.
**Step 3: Commit** `git commit -am "feat: renderer note state over window.api"`

---

## Phase 5 — CodeMirror 6 editor

CM6 reference confirmed: `ViewPlugin.fromClass(class { decorations; update() }, { decorations, eventHandlers })`; `Decoration.mark/line/widget/replace`; theme via `EditorView.theme`.

### Task 5.1: Decoration builder (pure-ish) + tests

**Files:**
- Create: `app/renderer/lib/editor/decorations.ts`, `app/renderer/lib/editor/decorations.test.ts`

Build a function `buildDecorations(view): DecorationSet` that iterates visible lines and, using `detectMode` + the parsers, emits:
- line decoration class `cm-h1/2/3` for headings,
- line class `cm-comment` for `//` (todo mode),
- line class `cm-keyword` for line 1 in todo mode,
- mark decoration `cm-link` over each URL range (from `parseLinks` offsets),
- todo unchecked: `Decoration.widget` `☐` at line start (`side: -1`); checked: `☑` widget + `cm-checked` line class (strikethrough via CSS),
- checked `/x` token: `Decoration.replace({})` over the trailing `/x` range **unless** the main selection head is on that line (reveal-at-cursor).

**Step 1: Failing tests** — test the *range computation* by exporting a pure helper `computeRanges(doc: string, selHeadLine: number)` returning a serializable list `{ from, to, kind }[]` (kind ∈ heading1/2/3/comment/keyword/link/checkbox-unchecked/checkbox-checked/hide-x). Example:
```ts
import { describe, it, expect } from 'vitest'
import { computeRanges } from './decorations'
it('hides /x token when cursor not on that line', () => {
  const r = computeRanges('todo:\ndone /x', /*selHeadLine*/ 0)
  expect(r).toContainEqual(expect.objectContaining({ kind: 'hide-x' }))
})
it('reveals /x token when cursor on that line', () => {
  const r = computeRanges('todo:\ndone /x', /*selHeadLine*/ 1)
  expect(r.some(x => x.kind === 'hide-x')).toBe(false)
})
it('marks heading line 1 in plain mode', () => {
  const r = computeRanges('# Title', 99)
  expect(r).toContainEqual(expect.objectContaining({ kind: 'heading1' }))
})
```
**Step 2:** Run → FAIL.
**Step 3:** Implement `computeRanges` (pure string→ranges) and a thin `buildDecorations(view)` that maps `computeRanges` output to actual `Decoration` objects via a `RangeSetBuilder` (sorted by `from`). Keep all logic decisions in `computeRanges` so they're testable; `buildDecorations` only translates.
**Step 4:** Run → PASS. `npm run check`.
**Step 5: Commit** `git commit -am "feat: CM6 decoration range computation with tests"`

### Task 5.2: Editor extension assembly (plugin + theme + links + keymap + autosave)

**Files:**
- Create: `app/renderer/lib/editor/theme.ts` (reproduce look: `#faf8f5` bg, `#2c2c2c` text, h1 `#d45d00` / h2 `#2e8b57` / h3 `#5a7ec2`, `.cm-link` blue underline-on-hover, `.cm-comment` grey italic, `.cm-keyword` grey, `.cm-checked` line-through, hanging-indent padding for checkbox, 15px / line-height 1.7, transparent gutter, no line numbers).
- Create: `app/renderer/lib/editor/extensions.ts`

**Step 1:** `extensions.ts` exports `createEditorExtensions({ onChange, onNavigate, onNewNote, onDelete })`:
- the decoration `ViewPlugin` (rebuild on `docChanged || selectionSet || viewportChanged`),
- `eventHandlers.mousedown`: if target has `cm-link` class, `window.api.shell.openExternal(url)` and return true,
- `EditorView.updateListener.of` → on `docChanged` call `onChange(view.state.doc.toString())`,
- `Prec.high(keymap.of([...]))` mapping `Ctrl-h`→onNavigate(-1), `Ctrl-l`→onNavigate(+1), `Ctrl-n`→onNewNote, `Ctrl-d`→onDelete (each `preventDefault` by returning true),
- the theme, `EditorView.lineWrapping`, and `EditorState.transactionFilter` is NOT needed.
**Step 2:** `npm run check`.
**Step 3: Commit** `git commit -am "feat: CM6 extensions theme links keymap autosave"`

### Task 5.3: `Editor.svelte` wrapper

**Files:**
- Create: `app/renderer/Editor.svelte`

**Step 1:** Svelte 5 component that:
- on mount, creates `EditorView` with `doc = getContent()` + `createEditorExtensions(...)`, parented to a `<div bind:this>`,
- `onChange` → `setContent(s)` + `scheduleSave()`,
- exposes a way to replace doc when the active note changes (e.g. an exported `setDoc(text)` that dispatches `view.dispatch({ changes: { from:0, to: docLength, insert: text } })`); App calls it after navigation/new/delete,
- focuses the view on mount and when window regains focus,
- destroys the view on unmount.
**Step 2:** `npm run check`.
**Step 3: Commit** `git commit -am "feat: Editor.svelte CM6 wrapper"`

---

## Phase 6 — App shell, slash picker, first runnable UI

### Task 6.1: `SlashPicker.svelte`

**Files:**
- Create: `app/renderer/SlashPicker.svelte`

**Step 1:** Port old `SlashPicker.svelte` (keyboard nav ↑/↓/Enter/Esc/number-select, `getRegisteredKeywords()` → `REGISTERED_KEYWORDS`). Styling reproduced.
**Step 2: Commit** `git commit -am "feat: port slash picker"`

### Task 6.2: `App.svelte` wiring

**Files:**
- Create/replace: `app/renderer/App.svelte`, `app/renderer/main.ts`, `app/renderer/index.html`

**Step 1:** Compose: drag region (`-webkit-app-region: drag` on a top strip; CM area `no-drag`), `<Editor>`, conditional `<SlashPicker>` when first line is lone `/`, and the `n/m` + mode counter. Wire:
- `onMount`: `loadNotes()` then focus; restore window geometry handled in main (Phase 7) so nothing here,
- slash select → set content to `keyword + rest`, dispatch to editor, save,
- navigation/new/delete handlers call noteState then `editor.setDoc(getContent())`,
- `window.api.onTray(action => …)` mapping `new-note`/`toggle-aot`/`toggle-auto-hide`/`quit(flushSave)`,
- always-on-top + auto-hide settings load (`window.api.settings.get`).
**Step 2:** Frameless transparent rounded look via CSS (`main` bg `#faf8f5`, `border-radius:10px`, body transparent).
**Step 3: Smoke run** `npm run dev`:
- type text → reload app → text persists (DB works),
- type `todo:` then lines, `/x` toggles strike, cursor-on-line reveals `/x`,
- `#`/`##`/`###` color, `//` greys, URLs clickable (opens browser),
- `/` shows picker, Enter inserts `todo`,
- Ctrl+H/L/N/D behave; counter updates.
**Step 4: Commit** `git commit -am "feat: app shell wiring + first runnable UI"`

---

## Phase 7 — Window: frameless/transparent/always-on-top + geometry persist

### Task 7.1: BrowserWindow config

**Files:**
- Modify: `app/main/index.ts`; Create: `app/main/window.ts`

**Step 1:** `createWindow()` with `{ width:360, height:360, minWidth:360, minHeight:360, frame:false, transparent:true, resizable:true, alwaysOnTop:true, backgroundColor:'#00000000', webPreferences:{...} }`. Load renderer (dev: `process.env.ELECTRON_RENDERER_URL`; prod: `loadFile` of built index). Set app icon.
**Step 2:** Apply persisted `always_on_top` setting on create.
**Step 3: Smoke:** window is frameless, transparent corners, on top.
**Step 4: Commit** `git commit -am "feat: frameless transparent always-on-top window"`

### Task 7.2: Geometry persistence (main side) + on-screen guard + tests

**Files:**
- Create: `app/main/window.ts` (geometry), `app/main/geometry.test.ts`

**Step 1: Failing test** for the pure on-screen guard (port `isOnScreen` math from old `windowState.ts`):
```ts
import { describe, it, expect } from 'vitest'
import { isOnScreen } from './window'
const mon = { x: 0, y: 0, width: 1920, height: 1080 }
it('accepts a window fully on screen', () => {
  expect(isOnScreen({ x: 100, y: 100, width: 360, height: 360 }, mon)).toBe(true)
})
it('rejects a window off screen', () => {
  expect(isOnScreen({ x: 5000, y: 5000, width: 360, height: 360 }, mon)).toBe(false)
})
```
**Step 2:** Run → FAIL.
**Step 3:** Implement `isOnScreen(geom, monitor)` (≥50px overlap on both axes, from old logic). Then wire window `'move'`/`'resize'` (or `'moved'`/`'resized'`) → debounce 500ms → `settings.set('window_geometry', JSON.stringify(...))`. On create, read `window_geometry`, clamp to mins, and apply only if `isOnScreen` against the matched `screen.getDisplayMatching`/nearest display.
**Step 4:** Run → PASS. Smoke: move/resize, restart, geometry restored; place off-screen value manually → ignored.
**Step 5: Commit** `git commit -am "feat: window geometry persistence with on-screen guard"`

---

## Phase 8 — Tray + global shortcut

### Task 8.1: Global shortcut Alt+A

**Files:**
- Create: `app/main/shortcuts.ts`; Modify: `app/main/index.ts`

**Step 1:** `registerShortcuts(win)`: `globalShortcut.register('Alt+A', () => win.isVisible() ? win.hide() : (win.show(), win.focus()))`. Guard registration failure with a console warning (Wayland degrade). Unregister on `will-quit`.
**Step 2: Smoke:** Alt+A toggles show/hide.
**Step 3: Commit** `git commit -am "feat: global shortcut Alt+A toggle"`

### Task 8.2: Tray menu

**Files:**
- Create: `app/main/tray.ts`; Modify: `app/main/index.ts`

**Step 1:** `createTray(win)` with `Menu` items matching old `tray.rs`:
- Show/Hide → toggle visibility (act in main),
- New Note → `win.show(); win.focus(); win.webContents.send('tray','new-note')`,
- separator,
- Toggle Always on Top → `send('tray','toggle-aot')`,
- Toggle Auto-hide → `send('tray','toggle-auto-hide')`,
- separator,
- Quit → `send('tray','quit')` then `app.quit()` (give renderer a tick to flush, or flush is synchronous via DB — acceptable to quit immediately since saves are debounced; to be safe, `setTimeout(()=>app.quit(), 50)`).
Set tray icon + tooltip "Antinote".
**Step 2: Smoke:** every menu item works; toggles persist across restart.
**Step 3: Commit** `git commit -am "feat: system tray menu"`

### Task 8.3: Auto-hide-on-blur

**Files:**
- Modify: `app/renderer/App.svelte` (or move to main `win.on('blur')`)

**Step 1:** Implement in main for reliability: when `auto_hide_on_blur === 'true'`, on `win.on('blur')` start 300ms timer → `win.hide()`; cancel on `focus`. Read/track the setting; update live on `toggle-auto-hide`. (Renderer toggles call `settings.set`; main reads current value on each blur, or main owns the setting cache.) On `blur`, also tell renderer to flush via existing debounced save — saves already fire on change, so a final flush isn't strictly required; document this.
**Step 2: Smoke:** enable auto-hide via tray, click away → hides after 300ms; disable → stays.
**Step 3: Commit** `git commit -am "feat: auto-hide on blur"`

---

## Phase 9 — Packaging, CI, cleanup

### Task 9.1: electron-builder config (.deb + .AppImage)

**Files:**
- Modify: `electron-builder.yml`

**Step 1:** Set `productName: Antinote`, `appId: com.honganh.antinote-linux`, `linux: { target: ['AppImage','deb'], category: 'Utility' }`, icon, and ensure `better-sqlite3` is unpacked (`asarUnpack: ['**/node_modules/better-sqlite3/**']`). Add `afterPack`/`npmRebuild: true` so the native module matches Electron.
**Step 2:** Build: `npm run package`. Expected: `.AppImage` and `.deb` in `dist/`.
**Step 3: Smoke:** run the produced `.AppImage` on a clean-ish env; notes persist, tray works.
**Step 4: Commit** `git commit -am "build: electron-builder linux deb+appimage"`

### Task 9.2: Rewrite GitHub Actions release workflow

**Files:**
- Modify: `.github/workflows/release.yml`

**Step 1:** Replace Tauri build with: checkout → setup-node 22 → `npm ci` → `npm run package` (electron-builder rebuilds native deps) → upload `.deb`/`.AppImage` to a draft release on `v*` tag. Drop the Rust/webkit system-dep install steps; add `libfuse2` for AppImage if needed.
**Step 2: Commit** `git commit -am "ci: build electron artifacts on tag"`

### Task 9.3: Remove Tauri, relocate `app/` → final layout, update docs

**Files:**
- Delete: `src-tauri/`, old `src/`, `vite.config.js`, `tsconfig.json` (Tauri one), `index.html` (root)
- Move: `app/*` to repo root layout matching `electron.vite.config.ts` (or keep `app/` and point config there — pick one; recommend keeping `app/` to minimize churn)
- Modify: `README.md`, `AGENTS.md`, `release.sh`

**Step 1:** Delete `src-tauri/` and the old Svelte/Tauri `src/`. Remove `@tauri-apps/*` from `package-lock` via `npm install`.
**Step 2:** Rewrite `README.md` (prereqs now just Node + npm; no Rust/webkit/gtk; `npm install && npm run dev`; build `npm run package`). Rewrite `AGENTS.md` to describe the Electron architecture (main/preload/renderer, IPC bridge, better-sqlite3, CM6, no runes-extension rule needed but keep Svelte 5 `.svelte.ts` note).
**Step 3:** Update `release.sh` to bump version in `package.json` + `electron-builder.yml` (drop Cargo/tauri.conf).
**Step 4:** Full verification:
```bash
npm run check && npm test && npm run package
```
Expected: type-check clean, all parser/db/geometry tests pass, artifacts build.
**Step 5: Commit** `git commit -am "chore: remove tauri, finalize electron layout, update docs"`

---

## Done criteria

- `npm run dev` runs the app; all features from the parity list work.
- `npm test` green (links, todo, mode, db, geometry suites).
- `npm run package` emits `.deb` + `.AppImage`.
- No `src-tauri/`, no Rust, no `@tauri-apps/*` deps remain.
- Existing users' notes migrate from the old Tauri DB path on first launch.

## Feature parity checklist (verify before merge)

- [ ] Multi-note: nav Ctrl+H/L, new Ctrl+N, delete Ctrl+D (with confirm on non-empty), `n/m` counter
- [ ] Debounced 500ms autosave; reload persists
- [ ] Alt+A global toggle show/hide
- [ ] Tray: show/hide, new note, toggle always-on-top, toggle auto-hide, quit
- [ ] Window: frameless, transparent rounded, always-on-top (persisted), resizable, geometry persisted + on-screen guard
- [ ] auto_create_note_on_launch behavior
- [ ] auto_hide_on_blur behavior
- [ ] Todo mode: checkboxes, `/x` checked + strike, reveal `/x` on cursor line, `#`/`//` styling
- [ ] Plain mode: heading colors
- [ ] Clickable links (open in default browser) in both modes
- [ ] Slash picker on lone `/`
- [ ] Old Tauri notes.db migrated on first launch
```
