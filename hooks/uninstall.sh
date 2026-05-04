#!/usr/bin/env bash
# Remove Brevix hooks + statusline from ~/.claude/settings.json.
set -euo pipefail

SETTINGS="${HOME}/.claude/settings.json"
[ -f "${SETTINGS}" ] || { echo "Nothing to uninstall."; exit 0; }

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq required." >&2
  exit 1
fi

TMP="$(mktemp)"
jq '
  .hooks.SessionStart //= [] | .hooks.SessionStart |= map(select(.matcher != "brevix"))
  | .hooks.UserPromptSubmit //= [] | .hooks.UserPromptSubmit |= map(select(.matcher != "brevix"))
  | if (.statusLine.command // "" | test("brevix-statusline")) then del(.statusLine) else . end
' "${SETTINGS}" > "${TMP}"
mv "${TMP}" "${SETTINGS}"
echo ">> Brevix hooks removed from ${SETTINGS}"
