# Antinote for Linux

<p align="center">
  <img src="docs/icon.png" alt="Antinote icon" width="128">
</p>

<p align="center">
  A lightweight, always-accessible scratchpad for Linux, inspired by <a href="https://antinote.io/">Antinote</a>.<br>
  Built with <a href="https://tauri.app/">Tauri 2</a> + <a href="https://svelte.dev/">Svelte 5</a>.
</p>

## Demo

<p align="center">
  <img src="docs/demo.gif" alt="Antinote demo" width="600">
</p>

## Prerequisites

### System dependencies

**Ubuntu / Pop!_OS 22.04+:**

```bash
sudo apt update
sudo apt install -y \
  libwebkit2gtk-4.1-dev \
  libsoup-3.0-dev \
  libgtk-3-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev \
  build-essential \
  patchelf
```

**Fedora:**

```bash
sudo dnf install -y \
  webkit2gtk4.1-devel \
  libsoup3-devel \
  gtk3-devel \
  libappindicator-gtk3-devel \
  librsvg2-devel \
  patchelf
```

**Arch Linux:**

```bash
sudo pacman -S --needed \
  webkit2gtk-4.1 \
  libsoup3 \
  gtk3 \
  libappindicator-gtk3 \
  librsvg \
  patchelf
```

### Rust

Install via [rustup](https://rustup.rs/):

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Node.js

Install Node.js 18+ via [nvm](https://github.com/nvm-sh/nvm) or your package manager:

```bash
nvm install 22
nvm use 22
```

## Local Development

```bash
# Install npm dependencies
npm install

# Run in development mode (starts Vite dev server + Tauri window)
npm run tauri dev
```

## Build

```bash
# Production build (outputs to src-tauri/target/release/bundle/)
npm run tauri build
```

## Project Structure

```
antinote-linux/
├── src/                  # Svelte frontend
│   ├── App.svelte        # Main app component
│   └── main.js           # Svelte entry point
├── src-tauri/            # Tauri/Rust backend
│   ├── src/
│   │   ├── lib.rs        # App setup and Tauri commands
│   │   └── main.rs       # Entry point
│   ├── capabilities/     # Tauri permission definitions
│   ├── icons/            # App icons
│   ├── Cargo.toml        # Rust dependencies
│   └── tauri.conf.json   # Tauri configuration
├── tasks/                # PRD and roadmap docs
├── index.html            # HTML entry point
├── package.json          # Node dependencies
└── vite.config.js        # Vite configuration
```

## Releasing

### Version bump

Use the release script to update version numbers across all config files:

```bash
./release.sh 0.2.0
```

This updates `package.json`, `src-tauri/tauri.conf.json`, and `src-tauri/Cargo.toml`.

### Creating a release

After bumping the version:

```bash
git add package.json src-tauri/tauri.conf.json src-tauri/Cargo.toml
git commit -m "chore: bump version to 0.2.0"
git tag v0.2.0
git push origin main --tags
```

Pushing a `v*` tag triggers the GitHub Actions workflow, which:
1. Builds the Tauri app on `ubuntu-22.04`
2. Creates a **draft** GitHub release with `.deb` and `.AppImage` artifacts

Go to the GitHub Releases page to review and publish the draft.

## License

MIT
