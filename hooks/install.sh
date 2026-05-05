#!/usr/bin/env bash
# Wire Brevix hooks + statusline into Claude Code's settings.json.
# Idempotent: safe to re-run.
set -euo pipefail

CLAUDE_DIR="${HOME}/.claude"
SETTINGS="${CLAUDE_DIR}/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${CLAUDE_DIR}"

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required to merge settings.json safely." >&2
  exit 1
fi

if [ ! -f "${SETTINGS}" ]; then
  echo "{}" > "${SETTINGS}"
fi

TMP="$(mktemp)"
jq --arg activate "${SCRIPT_DIR}/brevix-activate.js" \
   --arg tracker "${SCRIPT_DIR}/brevix-mode-tracker.js" \
   --arg mutex "${SCRIPT_DIR}/brevix-mutex.js" \
   --arg statusline "${SCRIPT_DIR}/brevix-statusline.sh" '
  .hooks //= {}
  | .hooks.SessionStart //= []
  | .hooks.SessionStart |= (map(select(.matcher != "brevix" and .matcher != "brevix-mutex")) + [
      { "matcher": "brevix",
        "hooks": [{"type": "command", "command": ("node " + $activate)}] },
      { "matcher": "brevix-mutex",
        "hooks": [{"type": "command", "command": ("node " + $mutex)}] }
    ])
  | .hooks.UserPromptSubmit //= []
  | .hooks.UserPromptSubmit |= (map(select(.matcher != "brevix")) + [
      { "matcher": "brevix",
        "hooks": [{"type": "command", "command": ("node " + $tracker)}] }
    ])
  | .statusLine = { "type": "command", "command": ("bash " + $statusline) }
' "${SETTINGS}" > "${TMP}"
mv "${TMP}" "${SETTINGS}"

chmod +x "${SCRIPT_DIR}/brevix-statusline.sh" 2>/dev/null || true

echo ">> Brevix hooks installed in ${SETTINGS}"
echo ">> Disable statusline: export BREVIX_STATUSLINE=0"
