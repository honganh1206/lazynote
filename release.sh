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

# electron-builder reads the version from package.json, so that's the only file
# to bump.
sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" package.json

echo "Updated:"
echo "  package.json → $VERSION"
echo ""
echo "Next steps:"
echo "  git add package.json"
echo "  git commit -m \"chore: bump version to $VERSION\""
echo "  git tag v$VERSION"
echo "  git push origin main --tags"
