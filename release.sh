#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: ./release.sh <version>"
  echo "Example: ./release.sh 0.2.0"
  exit 1
fi

VERSION="$1"

# Validate semver format
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Error: Version must be in semver format (e.g., 0.2.0)"
  exit 1
fi

echo "Bumping version to $VERSION..."

# Update package.json
sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" package.json

# Update src-tauri/tauri.conf.json
sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" src-tauri/tauri.conf.json

# Update src-tauri/Cargo.toml (only the package version, not dependency versions)
sed -i "0,/^version = \".*\"/s//version = \"$VERSION\"/" src-tauri/Cargo.toml

echo "Updated:"
echo "  package.json         → $VERSION"
echo "  tauri.conf.json      → $VERSION"
echo "  Cargo.toml           → $VERSION"
echo ""
echo "Next steps:"
echo "  git add package.json src-tauri/tauri.conf.json src-tauri/Cargo.toml"
echo "  git commit -m \"chore: bump version to $VERSION\""
echo "  git tag v$VERSION"
echo "  git push origin main --tags"
