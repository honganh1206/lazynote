#!/usr/bin/env bash
# Wrap the PyInstaller onedir bundle (dist/lazynote/) into a .deb.
#
# Usage (from repo root, after pyinstaller has produced dist/lazynote/):
#   bash packaging/build-deb.sh <version>
#
# Output: dist/lazynote_<version>_amd64.deb
set -euo pipefail

VERSION="${1:?usage: build-deb.sh <version>}"
ARCH="amd64"
APP_ID="com.honganh.lazynote"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUNDLE="$ROOT/dist/lazynote"
[ -d "$BUNDLE" ] || { echo "missing $BUNDLE — run pyinstaller first" >&2; exit 1; }

PKG="$ROOT/dist/deb/lazynote_${VERSION}_${ARCH}"
rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN" \
         "$PKG/usr/lib/lazynote" \
         "$PKG/usr/bin" \
         "$PKG/usr/share/applications" \
         "$PKG/usr/share/metainfo" \
         "$PKG/usr/share/icons/hicolor/512x512/apps"

# App bundle -> /usr/lib/lazynote, launcher on PATH via /usr/bin symlink.
cp -a "$BUNDLE/." "$PKG/usr/lib/lazynote/"
ln -sf /usr/lib/lazynote/lazynote "$PKG/usr/bin/lazynote"

# Desktop integration.
cp "$ROOT/data/$APP_ID.desktop"      "$PKG/usr/share/applications/$APP_ID.desktop"
cp "$ROOT/data/$APP_ID.metainfo.xml" "$PKG/usr/share/metainfo/$APP_ID.metainfo.xml"
cp "$ROOT/src/lazynote/icon.png"     "$PKG/usr/share/icons/hicolor/512x512/apps/$APP_ID.png"

INSTALLED_KB="$(du -sk "$PKG/usr" | cut -f1)"

cat > "$PKG/DEBIAN/control" <<EOF
Package: lazynote
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: Hong Anh Pham <phamhonganh12062000@gmail.com>
Installed-Size: ${INSTALLED_KB}
Depends: libegl1, libgl1, libxkbcommon0, libdbus-1-3, libfontconfig1, libfreetype6, libxcb-cursor0
Recommends: tesseract-ocr
Description: A lightweight native scratchpad
 Always-accessible scratchpad for temporary notes, inspired by Antinote.
 Frameless, translucent, always-on-top window with todo mode, clickable
 links, multiple notes, autosave to SQLite, a tray menu and an Alt+A
 global toggle. Self-contained (Qt 6 / PySide6 bundled).
EOF

dpkg-deb --root-owner-group --build "$PKG" "$ROOT/dist/lazynote_${VERSION}_${ARCH}.deb"
echo "built dist/lazynote_${VERSION}_${ARCH}.deb"
