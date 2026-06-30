# Antinote for Linux

<p align="center">
  <img src="docs/icon.png" alt="Antinote icon" width="128">
</p>

<p align="center">
  A lightweight, always-accessible scratchpad for Linux, inspired by <a href="https://antinote.io/">Antinote</a>.<br>
  Built with <a href="https://www.electronjs.org/">Electron</a> + <a href="https://svelte.dev/">Svelte 5</a> + <a href="https://codemirror.net/">CodeMirror 6</a>.
</p>

## Demo

<p align="center">
  <img src="docs/demo.gif" alt="Antinote demo" width="600">
</p>

## Features

- Frameless, transparent, always-on-top scratchpad window
- Multiple notes with quick navigation and a position counter
- Auto-save to a local SQLite database
- Global hotkey **Alt+A** to toggle show/hide
- System tray menu (show/hide, new note, toggle always-on-top, toggle auto-hide, quit)
- Window position/size remembered across restarts
- `todo:` mode with checklist items (`/x` to check), `#` headings, `//` comments
- Plain mode with markdown-style headings and clickable links

## Prerequisites

Only **Node.js 18+** and **npm** are required — no Rust, no system WebKit/GTK
development packages.

Install Node.js via [nvm](https://github.com/nvm-sh/nvm) or your package manager:

```bash
nvm install 22
nvm use 22
```

Running the produced **AppImage** additionally needs `libfuse2`:

```bash
# Debian / Ubuntu / Pop!_OS
sudo apt install -y libfuse2
```

## Local Development

```bash
# Install dependencies, then rebuild the better-sqlite3 native module for Electron
npm install
npm run rebuild

# Run in development mode (electron-vite dev server + Electron window)
npm run dev
```

> **Note:** `better-sqlite3` is a native module compiled against Electron's ABI.
> `npm run rebuild` builds it for Electron. To run the unit tests (which execute
> under plain Node), run `npm rebuild better-sqlite3` first, then `npm test`, then
> `npm run rebuild` again to restore the Electron build.

## Build & Package

```bash
# Type-check and run tests
npm run check
npm test

# Build the app bundles (outputs to out/)
npm run build

# Produce distributable .deb and .AppImage (outputs to dist/)
npm run package
```

## Project Structure

```
antinote-linux/
├── app/
│   ├── main/             # Electron main process (window, tray, shortcuts, SQLite)
│   ├── preload/          # contextBridge → typed window.api
│   └── renderer/         # Svelte 5 + CodeMirror 6 UI
│       └── src/
│           ├── App.svelte
│           ├── Editor.svelte        # CodeMirror 6 wrapper
│           ├── SlashPicker.svelte
│           └── lib/                 # state, api bridge, parsers, editor extensions
├── electron.vite.config.ts
├── electron-builder.yml
└── docs/                 # PRD, roadmap, design docs
```

## Releasing

### Version bump

```bash
./release.sh 0.2.0
```

This updates the version in `package.json` (electron-builder reads it from there).

### Creating a release

```bash
git add package.json
git commit -m "chore: bump version to 0.2.0"
git tag v0.2.0
git push origin main --tags
```

Pushing a `v*` tag triggers the GitHub Actions workflow, which builds the app on
`ubuntu-22.04` and creates a **draft** GitHub release with `.deb` and `.AppImage`
artifacts. Review and publish it from the GitHub Releases page.

## License

MIT
