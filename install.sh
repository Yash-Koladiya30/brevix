#!/usr/bin/env bash
# Brevix installer — installs Python CLI and points users at the Claude Code marketplace.
set -euo pipefail

REPO="${BREVIX_REPO:-Yash-Koladiya30/brevix}"
BRANCH="${BREVIX_BRANCH:-main}"

echo ">> Brevix installer"

# --- 1. Install Python CLI ---
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required but not found." >&2
  exit 1
fi

if command -v pipx >/dev/null 2>&1; then
  echo ">> Installing brevix via pipx"
  pipx install --force "git+https://github.com/${REPO}.git@${BRANCH}"
elif command -v pip3 >/dev/null 2>&1; then
  echo ">> Installing brevix via pip"
  pip3 install --user --upgrade "git+https://github.com/${REPO}.git@${BRANCH}"
else
  echo "ERROR: pip3 or pipx is required." >&2
  exit 1
fi

# --- 2. Verify CLI ---
if command -v brevix >/dev/null 2>&1; then
  brevix --version
  echo ""
  echo ">> Brevix CLI installed."
  echo ">> Try: brevix compress \"Your verbose text goes here\" --mode full"
  echo ">> Stats:  brevix stats"
else
  echo "WARNING: 'brevix' command not on PATH. You may need to add ~/.local/bin to PATH."
fi

# --- 3. Claude Code plugin install instructions ---
cat <<EOF

>> Claude Code plugin
   Install via marketplace:
     /plugin marketplace add ${REPO}
     /plugin install brevix@brevix

   Optional accuracy guard (semantic check):
     pip install 'brevix[guard]'

   Optional accurate token counts:
     pip install 'brevix[tokens]'

EOF
