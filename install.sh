#!/usr/bin/env bash
# Brevix installer — installs the Python CLI, optionally hooks/MCP shrink,
# and points users at the Claude Code marketplace.
set -euo pipefail

REPO="${BREVIX_REPO:-Yash-Koladiya30/brevix}"
BRANCH="${BREVIX_BRANCH:-main}"

DRY_RUN=0
FORCE=0
MINIMAL=0
ALL=0
WITH_HOOKS=0
WITH_MCP_SHRINK=0
WITH_INIT=0
NO_COLOR=0
ONLY=""
LIST_ONLY=0

usage() {
  cat <<EOF
Brevix installer

Usage: $0 [options]

  --minimal           CLI only (no hooks, no MCP, no per-repo init)
  --all               CLI + hooks + MCP shrink + per-repo init
  --with-hooks        Install Claude Code hooks + statusline
  --with-mcp-shrink   Register brevix-shrink MCP proxy globally
  --with-init         Drop AGENTS.md / .cursor/rules etc. into cwd
  --only <target>     Only this target (claude-code, cursor, codex, …)
  --dry-run           Print what would happen, don't change anything
  --force             Reinstall even if already present
  --no-color          Disable ANSI colors
  --list              Show available install targets and exit
  -h, --help          This message
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --force) FORCE=1 ;;
    --minimal) MINIMAL=1 ;;
    --all) ALL=1 ;;
    --with-hooks) WITH_HOOKS=1 ;;
    --with-mcp-shrink) WITH_MCP_SHRINK=1 ;;
    --with-init) WITH_INIT=1 ;;
    --only) ONLY="$2"; shift ;;
    --no-color) NO_COLOR=1 ;;
    --list) LIST_ONLY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown flag: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

if [ $ALL -eq 1 ]; then
  WITH_HOOKS=1
  WITH_MCP_SHRINK=1
  WITH_INIT=1
fi
if [ $MINIMAL -eq 1 ]; then
  WITH_HOOKS=0
  WITH_MCP_SHRINK=0
  WITH_INIT=0
fi

if [ $NO_COLOR -eq 1 ] || [ ! -t 1 ]; then
  C_RESET=""; C_CYAN=""; C_YEL=""
else
  C_RESET=$'\033[0m'; C_CYAN=$'\033[36m'; C_YEL=$'\033[33m'
fi
step() { printf "%s>> %s%s\n" "$C_CYAN" "$1" "$C_RESET"; }
warn() { printf "%sWARN: %s%s\n" "$C_YEL" "$1" "$C_RESET" >&2; }

run() {
  if [ $DRY_RUN -eq 1 ]; then
    echo "[dry-run] $*"
  else
    eval "$*"
  fi
}

if [ $LIST_ONLY -eq 1 ]; then
  echo "Available targets:"
  echo "  claude-code, cursor, windsurf, codex, antigravity, copilot,"
  echo "  aider, continue, cline, roo, zed, gemini, augment, kilo,"
  echo "  openhands, tabnine, warp, replit, sourcegraph-amp, agents-md, all"
  exit 0
fi

step "Brevix installer"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 required." >&2
  exit 1
fi

# 1. Install Python CLI
if command -v pipx >/dev/null 2>&1; then
  step "Installing brevix via pipx"
  FLAGS=""
  [ $FORCE -eq 1 ] && FLAGS="--force"
  run "pipx install $FLAGS 'git+https://github.com/${REPO}.git@${BRANCH}'"
elif command -v pip3 >/dev/null 2>&1; then
  step "Installing brevix via pip"
  run "pip3 install --user --upgrade 'git+https://github.com/${REPO}.git@${BRANCH}'"
else
  echo "ERROR: pip3 or pipx required." >&2
  exit 1
fi

# 2. Hooks
if [ $WITH_HOOKS -eq 1 ]; then
  step "Installing Claude Code hooks (SessionStart, UserPromptSubmit, statusline)"
  TMP_HOOKS="$(mktemp -d)"
  run "curl -fsSL https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz | tar -xz -C '${TMP_HOOKS}' --strip-components=1"
  run "bash '${TMP_HOOKS}/hooks/install.sh'"
fi

# 3. MCP shrink
if [ $WITH_MCP_SHRINK -eq 1 ]; then
  if command -v npm >/dev/null 2>&1; then
    step "Installing brevix-shrink MCP proxy globally"
    run "npm install -g brevix-shrink"
  else
    warn "npm not found; skipping brevix-shrink. Install Node.js then run 'npm install -g brevix-shrink'."
  fi
fi

# 4. Per-repo init
if [ $WITH_INIT -eq 1 ]; then
  TARGET="${ONLY:-all}"
  step "Dropping rule files into $(pwd) for target=${TARGET}"
  run "brevix install ${TARGET} --path ."
elif [ -n "$ONLY" ]; then
  step "Per-repo init for ${ONLY}"
  run "brevix install ${ONLY} --path ."
fi

# 5. Verify
if command -v brevix >/dev/null 2>&1; then
  brevix --version
  echo ""
  step "Brevix CLI installed."
  echo "  brevix compress 'verbose text' --mode auto"
  echo "  brevix stats --real --since 7d"
  echo "  brevix install --list"
else
  warn "'brevix' not on PATH. Add ~/.local/bin to PATH and re-open shell."
fi

cat <<EOF

Claude Code plugin (marketplace):
  /plugin marketplace add ${REPO}
  /plugin install brevix@brevix

Optional extras:
  pip install 'brevix[guard]'   # semantic Accuracy Guard
  pip install 'brevix[tokens]'  # accurate tiktoken counts
  pip install 'brevix[all]'     # everything

EOF
