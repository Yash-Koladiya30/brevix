#!/usr/bin/env bash
#
# Pack the Brevix browser extension for Chrome Web Store / Firefox AMO
# submission. Run from anywhere:
#
#   bash extensions/browser/build.sh
#
# Writes: extensions/browser/dist/brevix-<version>.zip
#
# Excludes: build script, dist folder, .DS_Store, .map files, anything that
# isn't needed at runtime.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION=$(grep '"version"' manifest.json | head -1 | awk -F\" '{print $4}')
if [ -z "$VERSION" ]; then
  echo "Could not read version from manifest.json"
  exit 1
fi

DIST="dist"
OUT="$DIST/brevix-$VERSION.zip"

mkdir -p "$DIST"
rm -f "$OUT"

# Sanity: required files must exist before packing.
required=(
  manifest.json
  background/service_worker.js
  content/inject.js
  content/page_inject.js
  content/claude_ai.js
  content/chatgpt_com.js
  content/toolbar.css
  lib/rules.js
  lib/stats.js
  popup/popup.html
  popup/popup.js
  popup/popup.css
  options/options.html
  options/options.js
  icons/icon-16.png
  icons/icon-48.png
  icons/icon-128.png
)
for f in "${required[@]}"; do
  if [ ! -f "$f" ]; then
    echo "Missing required file: $f"
    exit 1
  fi
done

# Pack with only the runtime files. Excludes: build artifacts, OS junk,
# documentation, source maps.
zip -r "$OUT" \
  manifest.json \
  background/ \
  content/ \
  lib/ \
  popup/ \
  options/ \
  icons/ \
  -x "*.DS_Store" \
  -x "*.map" \
  -x "dist/*" \
  -x "build.sh" \
  -x "README.md"

SIZE=$(du -k "$OUT" | cut -f1)
echo ""
echo "Packed: $OUT  (${SIZE} KB)"
echo "Upload at: https://chrome.google.com/webstore/devconsole"
