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

## Prerequisites

### Node.js

Install Node.js 22+ via [nvm](https://github.com/nvm-sh/nvm) or your package manager:

```bash
nvm install 22
nvm use 22
```

### Build tools

`better-sqlite3` is a native module compiled from source for Electron's ABI, so a
C/C++ toolchain must be available:

**Ubuntu / Pop!_OS:**

```bash
sudo apt update
sudo apt install -y build-essential python3
```

**Fedora:**

```bash
sudo dnf install -y gcc-c++ make python3
```

**Arch Linux:**

```bash
sudo pacman -S --needed base-devel python
```

## Local Development

```bash
# Install npm dependencies
npm install

# Rebuild native modules (better-sqlite3) against Electron's ABI
npm run rebuild

# Run in development mode (electron-vite dev server + Electron window)
npm run dev
```

## Build

```bash
# Build main/preload/renderer bundles
npm run build

# Build and package distributables (.deb, .AppImage) via electron-builder
npm run package
```

## Project Structure

```
antinote-linux/
├── app/                      # Electron application source
│   ├── main/                 # Main process (window, tray, shortcuts, DB)
│   ├── preload/              # contextBridge → typed window.api
│   └── renderer/             # Svelte 5 + CodeMirror 6 UI
├── electron.vite.config.ts   # electron-vite config
├── electron-builder.yml      # Packaging config
├── tsconfig*.json            # TypeScript project references
├── tasks/                    # PRD and roadmap docs
└── package.json              # Node dependencies and scripts
```

## Releasing

### Version bump

Use the release script to update the version in `package.json`:

```bash
./release.sh 0.2.0
```

### Creating a release

After bumping the version:

```bash
git add package.json
git commit -m "chore: bump version to 0.2.0"
git tag v0.2.0
git push origin main --tags
```

## License

MIT
