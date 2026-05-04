#!/usr/bin/env bash
# Brevix uninstaller — removes the Python CLI and Claude Code hooks.
set -euo pipefail

echo ">> Brevix uninstaller"

# 1. Remove CLI
if command -v pipx >/dev/null 2>&1 && pipx list 2>/dev/null | grep -q "package brevix"; then
  echo ">> Removing brevix via pipx"
  pipx uninstall brevix || true
elif command -v pip3 >/dev/null 2>&1; then
  echo ">> Removing brevix via pip"
  pip3 uninstall -y brevix || true
fi

# 2. Remove Claude Code hooks
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/hooks/uninstall.sh" ]; then
  bash "${SCRIPT_DIR}/hooks/uninstall.sh" || true
fi

# 3. Stats are kept by default. Remove with: rm -rf ~/.brevix
echo ">> Done. Stats kept at ~/.brevix (delete manually if not needed)."
