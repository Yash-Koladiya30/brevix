# Brevix

> Compress LLM output safely. Save tokens without breaking your code.

[![CI](https://github.com/Yash-Koladiya30/brevix/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Yash-Koladiya30/brevix/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-78%20passing-brightgreen)](https://github.com/Yash-Koladiya30/brevix/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-8A2BE2)](https://github.com/Yash-Koladiya30/brevix)

**Brevix** is a universal output-compression layer for LLM coding tools. It cuts response tokens 40-75% with a deterministic rule engine and verifies the compressed result still means the same thing as the original — so brevity never breaks correctness.

Works with **Claude Code, Cursor, Windsurf, OpenAI Codex CLI, Google Antigravity, Gemini CLI, GitHub Copilot Chat, Aider, Continue.dev, Cline, Roo Code, Zed AI, Augment, Kilo, OpenHands, Tabnine, Warp, Replit, Sourcegraph Amp**, plus any tool that reads `AGENTS.md`.

---

## What Brevix gives you

| Capability | Brevix |
|------------|:-:|
| Rule-based compression — Lite, Full, Ultra | ✅ |
| **Adaptive Auto mode** (picks safest aggressive level per response) | ✅ |
| **Accuracy Guard** — semantic similarity verification before emit | ✅ |
| **Strict mode** — auto-fall-back to original when meaning would be lost | ✅ |
| Protected regions — code, URLs, error quotes are never touched | ✅ |
| File-level compression with `.original` backup (CLAUDE.md, AGENTS.md, …) | ✅ |
| MCP middleware (`brevix-shrink`) — compresses tool/prompt/resource descriptions | ✅ |
| Real Claude Code session-log token counts (`stats --real --since 7d`) | ✅ |
| Statusline badge — `[BREVIX] ⛏ X.Xk saved` | ✅ |
| Subagents — investigator / builder / reviewer with terse output formats | ✅ |
| Three-arm A/B eval harness with `tiktoken o200k_base` | ✅ |
| 20 platform install targets, idempotent `BREVIX:BEGIN/END` markers | ✅ |
| 100% local — no telemetry, no API calls in the engine | ✅ |
| Free + MIT | ✅ |

**Brevix's edge:** every compressed output is scored against the original locally. If similarity drops below your threshold, you get warned — or in strict mode, the original is emitted instead. No silent meaning loss on dense technical prose.

---

## Install

### One-liner (macOS / Linux / WSL)

```bash
curl -fsSL https://raw.githubusercontent.com/Yash-Koladiya30/brevix/main/install.sh | bash -s -- --all
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/Yash-Koladiya30/brevix/main/install.ps1 | iex
```

### Manual

```bash
pip install brevix                  # core
pip install 'brevix[guard]'         # + semantic Accuracy Guard
pip install 'brevix[tokens]'        # + accurate tiktoken counts
pip install 'brevix[all]'           # everything
```

### Plug into your LLM coding tool

```bash
brevix install --list                # show all 20 targets
brevix install claude-code           # Claude Code plugin layout
brevix install cursor                # .cursor/rules/brevix.mdc
brevix install codex                 # AGENTS.md + .codex/hooks.json
brevix install gemini                # gemini-extension.json + GEMINI.md
brevix install all                   # write rule files for every tool
```

Idempotent — re-running updates the Brevix block, leaves your other content alone.

### Claude Code marketplace

```
/plugin marketplace add Yash-Koladiya30/brevix
/plugin install brevix@brevix
```

### MCP middleware (compress upstream MCP server descriptions)

```bash
npm install -g brevix-shrink
```

Then wrap any MCP server in your Claude config:

```json
{
  "mcpServers": {
    "fs-shrunk": {
      "command": "npx",
      "args": ["brevix-shrink", "npx", "-y",
               "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
  }
}
```

---

## Usage

### Slash commands (Claude Code, Cursor, etc.)

```
/brevix                # toggle on (full mode)
/brevix lite           # gentle compression
/brevix ultra          # max compression
/brevix auto           # pick best mode per response
/brevix off            # disable
/brevix-commit         # terse Conventional Commit message
/brevix-check          # run Accuracy Guard on a snippet
/brevix-stats          # show savings
```

For Codex CLI (no slash commands), use `$brevix lite|full|ultra|auto|off`.

### CLI

```bash
# Output compression
brevix compress "Your verbose text here" --mode full
brevix compress -                      # stdin
brevix compress . --mode auto -v       # adaptive picks best
brevix compress . --guard --strict --threshold 0.85

# File compression (memory files like CLAUDE.md, AGENTS.md, project notes)
brevix compress-file CLAUDE.md         # writes .original.md backup
brevix compress-file CLAUDE.md --dry-run

# Stats
brevix stats                           # estimated, in-process
brevix stats --real --since 7d         # parsed from Claude Code session logs
brevix stats --share                   # tweet-ready one-liner
brevix stats --reset

# Verification
brevix check "original" "compressed"
brevix count "how many tokens?"

# Install rules into a project
brevix install cursor
brevix install --list
```

### Subagents (Claude Code)

`agents/` ships three small, focused subagents that emit ~60% smaller tool results than vanilla agents:

- **brevix-investigator** — read-only code locator (`path:line — symbol — note`)
- **brevix-builder** — surgical 1-2 file edits with verification
- **brevix-reviewer** — bug-focused diff review (`path:line: 🔴 bug: …. fix.`)

---

## How Accuracy Guard works

1. Compress output via the rule engine.
2. Score the original vs compressed text with a **local sentence-transformer** (no API cost).
3. If similarity ≥ threshold (default 0.85) → emit compressed. Otherwise warn, or in `--strict` mode fall back to original.
4. Without `sentence-transformers` installed, falls back to **content-word containment** (drops stopwords without penalty — fair to compression).

Result: compression you can trust on production code, specs, contracts.

---

## Compression example

**Before:**
> The reason your React component is re-rendering on every parent update is that you are passing an inline object as a prop. In JavaScript, every render creates a new object reference, even if the contents are identical. To fix this, wrap the object in `useMemo` so the reference stays stable across renders.

**After (full mode):**
> Inline object prop = new ref each render = re-render. Wrap in `useMemo`.

**Tokens saved:** ~75%. **Meaning preserved:** ✅ (similarity 0.91)

---

## Benchmarks

Reproducible three-arm A/B harness in [`evals/`](./evals). Compares no-system-prompt vs "be terse" control vs Brevix on 10 developer prompts.

```
arm       n   median  mean   total  vs baseline  vs control
baseline  10  221     247.3  2473   —            —
control   10  178     191.6  1916   22.5%        —
brevix    10  119     128.4  1284   48.1%        33.0%
```

Run yourself:

```bash
pip install 'brevix[all]' anthropic
export ANTHROPIC_API_KEY=...
python evals/llm_run.py --model claude-sonnet-4-6
python evals/measure.py
```

The `vs control` column is the honest savings — what Brevix adds *beyond* "just be brief."

---

## Roadmap

- [x] Core compression engine (lite/full/ultra)
- [x] Adaptive (auto) mode
- [x] Accuracy Guard (semantic + content-word fallback)
- [x] Local stats counter
- [x] Multi-platform installer (20 targets)
- [x] File-level compression (`brevix compress-file`)
- [x] MCP middleware (`brevix-shrink`)
- [x] Statusline badge + Claude Code hooks
- [x] Subagents (investigator/builder/reviewer)
- [x] Three-arm eval harness
- [x] PowerShell installer + uninstaller
- [ ] VSCode extension UI
- [ ] Browser extension (claude.ai, chatgpt.com web)
- [ ] Two-way compression (compress prompts before send)
- [ ] Custom user-defined rule packs
- [ ] Web dashboard (team tier)

---

## License

MIT — free for personal and commercial use.

---

## Contributing

Issues and PRs welcome. See [docs/CONTRIBUTING.md](./docs/CONTRIBUTING.md).
