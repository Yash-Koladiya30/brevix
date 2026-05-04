#!/usr/bin/env bash
# Brevix statusline badge for Claude Code.
# Wires into ~/.claude/settings.json:
#   "statusLine": { "type": "command",
#                   "command": "bash <path>/brevix-statusline.sh" }
# Disable: export BREVIX_STATUSLINE=0

set -eu

if [ "${BREVIX_STATUSLINE:-1}" = "0" ]; then
  exit 0
fi

# Read JSON from stdin (Claude Code passes session info this way).
INPUT="$(cat 2>/dev/null || true)"
_ignored="$INPUT"

# Pull tokens-saved figure from brevix CLI if available, else from stats.json.
SAVED=""
if command -v brevix >/dev/null 2>&1; then
  SAVED="$(brevix stats 2>/dev/null | awk -F'~' '/Tokens saved/ {gsub(/[^0-9]/,"",$2); print $2}')"
fi

if [ -z "$SAVED" ] && [ -f "$HOME/.brevix/stats.json" ]; then
  SAVED="$(python3 -c '
import json, sys
try:
    print(json.load(open("'"$HOME"'/.brevix/stats.json"))["total_tokens_estimated"])
except Exception:
    print("")
' 2>/dev/null || true)"
fi

if [ -z "$SAVED" ] || [ "$SAVED" = "0" ]; then
  printf "[BREVIX]"
  exit 0
fi

# Format as 1.2k / 1.4M for readability.
HUMAN="$(printf "%s" "$SAVED" | awk '{
  v=$1+0
  if (v>=1000000) printf "%.1fM", v/1000000
  else if (v>=1000) printf "%.1fk", v/1000
  else printf "%d", v
}')"

printf "[BREVIX] ⛏ %s saved" "$HUMAN"
