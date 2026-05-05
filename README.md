<div align="center">

<img src="assets/brevix-banner.png" alt="Brevix — Compress AI responses. Save tokens. Keep meaning." width="100%" />

<br />

# Brevix

### Compress LLM output safely. Save tokens without breaking your code.

<p>
  <a href="https://github.com/Yash-Koladiya30/brevix/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Yash-Koladiya30/brevix/ci.yml?branch=main&style=for-the-badge&label=CI&labelColor=0D1117&color=00D4FF" alt="CI" /></a>
  <a href="https://github.com/Yash-Koladiya30/brevix/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/tests-78_passing-00D4FF?style=for-the-badge&labelColor=0D1117" alt="Tests" /></a>
  <a href="https://pypi.org/project/brevix/"><img src="https://img.shields.io/pypi/v/brevix.svg?style=for-the-badge&label=PyPI&labelColor=0D1117&color=8B5CF6" alt="PyPI" /></a>
  <a href="https://www.npmjs.com/package/brevix-shrink"><img src="https://img.shields.io/npm/v/brevix-shrink.svg?style=for-the-badge&label=npm&labelColor=0D1117&color=FF3CAC" alt="npm" /></a>
  <a href="https://skills.sh/Yash-Koladiya30/brevix"><img src="https://img.shields.io/badge/skills.sh-brevix-0EA5E9?style=for-the-badge&labelColor=0D1117" alt="skills.sh" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-FFD93D?style=for-the-badge&labelColor=0D1117" alt="License: MIT" /></a>
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/python-3.9+-3776AB?style=for-the-badge&labelColor=0D1117&logo=python&logoColor=FFD43B" alt="Python" /></a>
  <a href="https://github.com/Yash-Koladiya30/brevix"><img src="https://img.shields.io/badge/Claude_Code-Plugin-8B5CF6?style=for-the-badge&labelColor=0D1117" alt="Claude Code Plugin" /></a>
</p>

<p>
  <b>
    <a href="#-install">Install</a> &nbsp;·&nbsp;
    <a href="#-usage">Usage</a> &nbsp;·&nbsp;
    <a href="#-how-accuracy-guard-works">Accuracy Guard</a> &nbsp;·&nbsp;
    <a href="#-benchmarks">Benchmarks</a> &nbsp;·&nbsp;
    <a href="#-roadmap">Roadmap</a> &nbsp;·&nbsp;
    <a href="docs/CONTRIBUTING.md">Contributing</a>
  </b>
</p>

<p>
  <i>Cuts response tokens <b>40–75%</b> with a deterministic rule engine. Verifies meaning is preserved before emit. Works across <b>20+ AI coding tools</b>.</i>
</p>

<p>
  <img src="https://img.shields.io/badge/-40--75%25_token_savings-00D4FF?style=for-the-badge&labelColor=0D1117" alt="40-75% savings" />
  <img src="https://img.shields.io/badge/-Accuracy_Guard-8B5CF6?style=for-the-badge&labelColor=0D1117" alt="Accuracy Guard" />
  <img src="https://img.shields.io/badge/-20+_Platforms-FF3CAC?style=for-the-badge&labelColor=0D1117" alt="20+ Platforms" />
  <img src="https://img.shields.io/badge/-100%25_Local-10B981?style=for-the-badge&labelColor=0D1117" alt="100% Local" />
</p>

</div>

---

<div align="center">
  <img src="https://img.shields.io/badge/-WHY_BREVIX-00D4FF?style=for-the-badge&labelColor=0D1117" alt="Why Brevix" />
</div>

## Why Brevix

**Brevix** is a universal output-compression layer for LLM coding tools. Every compressed response is scored against the original locally — if similarity drops below your threshold, you get warned, or in strict mode the original is emitted instead. **No silent meaning loss on dense technical prose.**

Works with **Claude Code · Cursor · Windsurf · OpenAI Codex CLI · Google Antigravity · Gemini CLI · GitHub Copilot Chat · Aider · Continue.dev · Cline · Roo Code · Zed AI · Augment · Kilo · OpenHands · Tabnine · Warp · Replit · Sourcegraph Amp** — plus any tool reading `AGENTS.md`.

---

<div align="center">
  <img src="https://img.shields.io/badge/-FEATURES-8B5CF6?style=for-the-badge&labelColor=0D1117" alt="Features" />
</div>

## Features

<table>
<tr>
<td width="50%" valign="top">

#### Compression Engine
- **Three modes** — Lite · Full · Ultra
- **Adaptive Auto mode** — picks safest aggressive level per response
- **Protected regions** — code blocks, URLs, error quotes never touched
- **File compression** — `CLAUDE.md`, `AGENTS.md`, project notes with `.original` backup

</td>
<td width="50%" valign="top">

#### Safety & Verification
- **Accuracy Guard** — semantic similarity check before emit
- **Strict mode** — auto-fallback to original when meaning would be lost
- **Local-first** — no telemetry, no API calls in the engine
- **Reproducible benchmarks** — three-arm A/B eval harness with `tiktoken o200k_base`

</td>
</tr>
<tr>
<td width="50%" valign="top">

#### Integrations
- **MCP middleware** (`brevix-shrink`) — compresses tool/prompt/resource descriptions
- **20 platform install targets** — idempotent `BREVIX:BEGIN/END` markers
- **Statusline badge** — `[BREVIX] ⛏ X.Xk saved`
- **Subagents** — investigator · builder · reviewer with terse output

</td>
<td width="50%" valign="top">

#### Insights
- **Real session-log token counts** — `stats --real --since 7d`
- **Shareable savings** — `stats --share` produces tweet-ready output
- **Per-mode breakdown** — see exactly what each level saves
- **Free + MIT licensed**

</td>
</tr>
</table>

---

<div align="center">
  <img src="https://img.shields.io/badge/-INSTALL-FF3CAC?style=for-the-badge&labelColor=0D1117" alt="Install" />
</div>

## 🚀 Install

#### One-liner — macOS / Linux / WSL

```bash
curl -fsSL https://raw.githubusercontent.com/Yash-Koladiya30/brevix/main/install.sh | bash -s -- --all
```

#### Windows — PowerShell

```powershell
irm https://raw.githubusercontent.com/Yash-Koladiya30/brevix/main/install.ps1 | iex
```

#### `skills` CLI — one command, 9 tools at once

Auto-installs Brevix skills into Antigravity, Claude Code, Cline, Codex, Cursor, Gemini CLI, GitHub Copilot, Kiro CLI, and Qoder simultaneously.

```bash
npx skills add https://github.com/Yash-Koladiya30/brevix
```

Pick a specific skill:

```bash
npx skills add https://github.com/Yash-Koladiya30/brevix --skill brevix
npx skills add https://github.com/Yash-Koladiya30/brevix --skill brevix-commit
npx skills add https://github.com/Yash-Koladiya30/brevix --skill brevix-stats
```

Listing → [skills.sh/Yash-Koladiya30/brevix](https://skills.sh/Yash-Koladiya30/brevix)

#### Manual install

```bash
pip install brevix                  # core
pip install 'brevix[guard]'         # + semantic Accuracy Guard
pip install 'brevix[tokens]'        # + accurate tiktoken counts
pip install 'brevix[all]'           # everything
```

#### Plug into your LLM coding tool

```bash
brevix install --list                # show all 20 targets
brevix install claude-code           # Claude Code plugin layout
brevix install cursor                # .cursor/rules/brevix.mdc
brevix install codex                 # AGENTS.md + .codex/hooks.json
brevix install gemini                # gemini-extension.json + GEMINI.md
brevix install all                   # write rule files for every tool
```

> Idempotent — re-running updates the Brevix block, leaves your other content alone.

#### Claude Code marketplace

```
/plugin marketplace add Yash-Koladiya30/brevix
/plugin install brevix@brevix
```

#### MCP middleware

Compress upstream MCP server descriptions:

```bash
npm install -g brevix-shrink
```

Wrap any MCP server in your Claude config:

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

<div align="center">
  <img src="https://img.shields.io/badge/-USAGE-00D4FF?style=for-the-badge&labelColor=0D1117" alt="Usage" />
</div>

## ⚡ Usage

#### Slash commands — Claude Code, Cursor, etc.

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

#### CLI

```bash
# Output compression
brevix compress "Your verbose text here" --mode full
brevix compress -                      # stdin
brevix compress . --mode auto -v       # adaptive picks best
brevix compress . --guard --strict --threshold 0.85

# File compression (CLAUDE.md, AGENTS.md, project notes)
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

#### Subagents — Claude Code

`agents/` ships three small, focused subagents that emit ~60% smaller tool results than vanilla agents:

| Agent | Purpose | Output format |
|-------|---------|---------------|
| **brevix-investigator** | Read-only code locator | `path:line — symbol — note` |
| **brevix-builder** | Surgical 1–2 file edits with verification | Diff + verify status |
| **brevix-reviewer** | Bug-focused diff review | `path:line: 🔴 bug: …. fix.` |

---

<div align="center">
  <img src="https://img.shields.io/badge/-ACCURACY_GUARD-10B981?style=for-the-badge&labelColor=0D1117" alt="Accuracy Guard" />
</div>

## 🛡 How Accuracy Guard works

1. Compress output via the rule engine.
2. Score the original vs compressed text with a **local sentence-transformer** (no API cost).
3. If similarity ≥ threshold (default `0.85`) → emit compressed. Otherwise warn, or in `--strict` mode fall back to original.
4. Without `sentence-transformers` installed → falls back to **content-word containment** (drops stopwords without penalty, fair to compression).

> Result: compression you can trust on production code, specs, and contracts.

---

<div align="center">
  <img src="https://img.shields.io/badge/-EXAMPLE-FFD93D?style=for-the-badge&labelColor=0D1117" alt="Example" />
</div>

## 💡 Compression example

**Before**

> The reason your React component is re-rendering on every parent update is that you are passing an inline object as a prop. In JavaScript, every render creates a new object reference, even if the contents are identical. To fix this, wrap the object in `useMemo` so the reference stays stable across renders.

**After** (full mode)

> Inline object prop = new ref each render = re-render. Wrap in `useMemo`.

**Tokens saved:** ~75% &nbsp;·&nbsp; **Meaning preserved:** ✅ similarity `0.91`

---

<div align="center">
  <img src="https://img.shields.io/badge/-BENCHMARKS-FF3CAC?style=for-the-badge&labelColor=0D1117" alt="Benchmarks" />
</div>

## 📊 Benchmarks

Reproducible three-arm A/B harness in [`evals/`](./evals). Compares no-system-prompt vs *"be terse"* control vs Brevix on 10 developer prompts.

| arm       | n  | median | mean  | total | vs baseline | vs control |
|-----------|----|--------|-------|-------|-------------|------------|
| baseline  | 10 | 221    | 247.3 | 2473  | —           | —          |
| control   | 10 | 178    | 191.6 | 1916  | 22.5%       | —          |
| **brevix**| 10 | **119**| **128.4** | **1284** | **48.1%** | **33.0%** |

Run yourself:

```bash
pip install 'brevix[all]' anthropic
export ANTHROPIC_API_KEY=...
python evals/llm_run.py --model claude-sonnet-4-6
python evals/measure.py
```

> The `vs control` column is the honest savings — what Brevix adds *beyond* "just be brief."

---

<div align="center">
  <img src="https://img.shields.io/badge/-ROADMAP-8B5CF6?style=for-the-badge&labelColor=0D1117" alt="Roadmap" />
</div>

## 🗺 Roadmap

- [x] Core compression engine (lite / full / ultra)
- [x] Adaptive (auto) mode
- [x] Accuracy Guard (semantic + content-word fallback)
- [x] Local stats counter
- [x] Multi-platform installer (20 targets)
- [x] File-level compression (`brevix compress-file`)
- [x] MCP middleware (`brevix-shrink`)
- [x] Statusline badge + Claude Code hooks
- [x] Subagents (investigator / builder / reviewer)
- [x] Three-arm eval harness
- [x] PowerShell installer + uninstaller
- [ ] VSCode extension UI
- [ ] Browser extension (claude.ai, chatgpt.com web)
- [ ] Two-way compression (compress prompts before send)
- [ ] Custom user-defined rule packs
- [ ] Web dashboard (team tier)

---

<div align="center">
  <img src="https://img.shields.io/badge/-LICENSE-FFD93D?style=for-the-badge&labelColor=0D1117" alt="License" />
  &nbsp;
  <img src="https://img.shields.io/badge/-CONTRIBUTING-10B981?style=for-the-badge&labelColor=0D1117" alt="Contributing" />
</div>

## 📜 License & Contributing

**MIT** — free for personal and commercial use. Issues and PRs welcome — see [docs/CONTRIBUTING.md](./docs/CONTRIBUTING.md).

<br />

<div align="center">
  <sub>Built with care by <a href="https://github.com/Yash-Koladiya30">Yash Koladiya</a> · If Brevix saves you tokens, ⭐ the repo</sub>
</div>
