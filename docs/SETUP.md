# Brevix — Development Machine Setup (A to Z)

Complete guide for setting up a fresh laptop to develop, test, and release Brevix.
Follow top to bottom on a new machine.

---

## 1. Prerequisites

Install these first:

| Tool | Version | Install (macOS) |
|------|---------|-----------------|
| Git | any recent | `xcode-select --install` or `brew install git` |
| Python | **3.9+** (3.11/3.12 recommended) | `brew install python@3.12` |
| Node.js | **>= 18** (needed for hooks + MCP server) | `brew install node` |
| GitHub CLI | latest | `brew install gh` |
| Claude Code | latest | `npm install -g @anthropic-ai/claude-code` |

Verify:

```bash
git --version
python3 --version   # >= 3.9
node --version      # >= 18
gh --version
```

## 2. Git identity & GitHub auth

```bash
git config --global user.name  "Yash Koladiya"
git config --global user.email "yashkoladiya123@gmail.com"

gh auth login       # choose GitHub.com → HTTPS → login via browser
```

> **Important:** if you use a Personal Access Token instead of `gh auth login`,
> it must have the **`workflow` scope** — pushing any edit to
> `.github/workflows/*` is rejected with a `repo`-only PAT. Plain code pushes
> don't need it.

## 3. Clone the repo

```bash
mkdir -p ~/Documents/Claude
cd ~/Documents/Claude
git clone https://github.com/Yash-Koladiya30/brevix.git Brevix
cd Brevix
```

## 4. Python dev environment

Editable install with all extras (guard model, tiktoken, pytest, ruff):

```bash
python3 -m venv .venv          # optional but recommended
source .venv/bin/activate
pip install -e '.[dev,all]'
```

Extras reference:

- `guard` — `sentence-transformers` (Accuracy Guard semantic check)
- `tokens` — `tiktoken` (token counting)
- `dev` — `pytest`, `pytest-cov`, `ruff`
- `all` — guard + tokens

Sanity check:

```bash
brevix --help
pytest              # full suite must pass
ruff check .
```

## 5. Node side (MCP server + hooks)

The npm package `brevix-shrink` lives in `mcp-servers/brevix-shrink/`.
It has no runtime dependencies; just verify it runs:

```bash
node mcp-servers/brevix-shrink/index.js --help 2>/dev/null || true
```

Hooks under `hooks/` are plain Node scripts invoked by Claude Code — no
`npm install` step required.

## 6. Install Brevix itself (end-user setup)

Use the bundled installer to wire up hooks, statusline, and the MCP proxy:

```bash
./install.sh --all        # CLI + hooks + MCP shrink + per-repo init
# or pick pieces:
./install.sh --list       # show available targets
./install.sh --minimal    # CLI only
./install.sh --dry-run    # preview without changes
```

Local state (stats, mode) lives in `~/.brevix/` — copy that folder from the
old laptop if you want to keep compression stats history
(`~/.brevix/stats.json`).

## 7. Claude Code plugin

The plugin manifest is `.claude-plugin/plugin.json` (SessionStart auto-activate,
Brevix/Caveman mutex, mode tracker). Install via the Claude Code marketplace,
or for local development point Claude Code at this repo's plugin directory.

Optional: copy from the old laptop to preserve Claude Code state:

- `~/.claude/settings.json` — global settings, statusline, permissions
- `~/.claude/plugins/` — installed plugins
- `~/.claude/projects/` — per-project memory

## 8. Release credentials (only needed for publishing)

Publishing runs in CI on tag push — you don't publish from the laptop — but
the GitHub repo needs valid secrets:

| Secret | Where | Notes |
|--------|-------|-------|
| `NPM_TOKEN` | repo secrets | npm **Automation** (or Read-Write) token for `brevix-shrink`. `E404 on PUT` during publish = bad/expired token, not a missing package. |
| PyPI | trusted publisher / token per `pypi.yml` | publishes `brevix` |

GitHub environment settings (not in repo, set in repo → Settings → Environments):

- `npm` and `pypi` environments have **required reviewers** (Yash) — runs
  pause until manually approved.
- Deployment branch/tag policy must allow `main` (branch) and `v*` (tags).

## 9. Release process

Version lives in **4 files that must stay in sync**:

1. `pyproject.toml`
2. `src/brevix/__init__.py`
3. `.claude-plugin/plugin.json`
4. `mcp-servers/brevix-shrink/package.json`

Steps:

```bash
# 1. bump all 4 files to the same X.Y.Z
# 2. commit
git commit -am "chore: bump to X.Y.Z"
git push origin main
# 3. tag push triggers npm.yml + pypi.yml
git tag vX.Y.Z
git push origin vX.Y.Z
# 4. approve the paused npm/pypi environment runs in the Actions tab
```

`npm.yml` is idempotent — it skips publish when the version already exists on
the registry, so re-runs go green.

## 10. Project layout refresher

```
src/brevix/         Python library (compressor, guard, stats, install, …)
hooks/              Claude Code hooks (Node.js) + statusline scripts
agents/             Subagent skill files (investigator/builder/reviewer)
mcp-servers/        Node.js MCP middleware (brevix-shrink)
skills/             Claude Code skills
commands/           Claude Code slash commands
.claude-plugin/     Plugin + marketplace manifests
extensions/browser/ Browser extension
evals/              Three-arm A/B harness
tests/              pytest suite
docs/               CONTRIBUTING.md, how-it-works.md, this file
```

## 11. Final checklist

- [ ] `pytest` passes
- [ ] `ruff check .` clean
- [ ] `brevix --help` works
- [ ] `./install.sh --dry-run` shows expected targets
- [ ] Claude Code session shows Brevix activation on start
- [ ] `gh auth status` logged in (with `workflow` scope if editing CI)
- [ ] `~/.brevix/` migrated (optional, keeps stats)
- [ ] `~/.claude/` settings migrated (optional)
