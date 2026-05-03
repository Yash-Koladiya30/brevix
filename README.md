# Brevix

> Compress LLM output safely. Save tokens without breaking your code.

**Brevix** is a universal output-compression layer for LLM coding tools. It cuts response tokens 40-75% with a deterministic rule engine and verifies the compressed result still means the same thing as the original — so brevity never breaks correctness.

Works with **Claude Code, Cursor, Windsurf, OpenAI Codex CLI, Google Antigravity, GitHub Copilot Chat, Aider, Continue.dev, Cline, Roo Code, Zed AI**, and any tool that reads `AGENTS.md`.

Inspired by [Caveman](https://github.com/JuliusBrussee/caveman). Built for production.

---

## Why Brevix?

| Feature | Caveman | **Brevix** |
|---------|---------|------------|
| Lite / Full / Ultra modes | ✅ | ✅ |
| Adaptive (auto) mode | ❌ | ✅ |
| Slash commands | ✅ | ✅ |
| **Accuracy Guard** (semantic check) | ❌ | ✅ |
| **Auto-warn on meaning loss** | ❌ | ✅ |
| **Local stats counter** | basic | ✅ |
| **Multi-platform installer** (Cursor, Codex, Aider, …) | ❌ | ✅ |
| Protected regions (code/URL/errors) | partial | ✅ |
| Free + MIT | ✅ | ✅ |

**Killer differentiator:** Brevix verifies compressed output preserves meaning before showing it. Caveman compresses blindly.

---

## Install (30 sec)

### Python CLI

```bash
pip install brevix                  # core
pip install 'brevix[guard]'         # + semantic Accuracy Guard
pip install 'brevix[tokens]'        # + accurate tiktoken counts
pip install 'brevix[all]'           # everything
```

Or one-liner:

```bash
curl -fsSL https://raw.githubusercontent.com/Yash-Koladiya30/brevix/main/install.sh | bash
```

### Plug into your LLM coding tool

Pick your tool (one command per project):

```bash
brevix install claude-code     # Claude Code plugin layout
brevix install cursor          # .cursor/rules/brevix.mdc
brevix install windsurf        # .windsurf/rules/brevix.md
brevix install codex           # AGENTS.md (OpenAI Codex CLI)
brevix install antigravity     # AGENTS.md (Google Antigravity)
brevix install copilot         # .github/copilot-instructions.md
brevix install aider           # CONVENTIONS.md + .aider.conf.yml
brevix install continue        # .continue/rules/brevix.md
brevix install cline           # .clinerules
brevix install roo             # .roo/rules/brevix.md
brevix install zed             # .rules
brevix install agents-md       # universal AGENTS.md (cross-tool standard)
brevix install all             # everything above
brevix install --list          # show all targets
```

Files written are deterministic and idempotent — re-running updates the Brevix block, leaves your other content alone.

### Claude Code marketplace (one-line)

```
/plugin marketplace add Yash-Koladiya30/brevix
/plugin install brevix@brevix
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

### CLI

```bash
brevix compress "Your verbose text here" --mode full
brevix compress -                 # stdin
brevix compress . --mode auto -v  # adaptive mode picks best
brevix compress . --guard --strict --threshold 0.85
brevix check "original" "compressed"
brevix count "how many tokens?"
brevix stats                      # cumulative savings
brevix stats --reset
brevix install cursor             # generate platform rules
```

---

## How Accuracy Guard works

1. Brevix compresses output using the rule engine.
2. Embeds both compressed and original locally (`sentence-transformers`, no API cost).
3. Computes cosine similarity.
4. If similarity < threshold (default 0.85): warn or, in `--strict` mode, fall back to original.
5. Without `sentence-transformers` installed, falls back to a content-word containment metric (drops stopwords without penalty — fair to compression).

Result: compression you can trust on production code, specs, contracts.

---

## Compression example

**Before:**
> The reason your React component is re-rendering on every parent update is that you are passing an inline object as a prop. In JavaScript, every render creates a new object reference, even if the contents are identical. To fix this, wrap the object in `useMemo` so the reference stays stable across renders.

**After (full mode):**
> Inline object prop = new ref each render = re-render. Wrap in `useMemo`.

**Tokens saved:** ~75%. **Meaning preserved:** ✅ (similarity 0.91)

---

## Roadmap

- [x] Core compression engine
- [x] Claude Code plugin
- [x] Accuracy Guard (semantic + content-word fallback)
- [x] Local stats counter
- [x] Adaptive (auto) mode
- [x] Multi-platform installer (Cursor, Windsurf, Codex, Antigravity, Copilot, Aider, Continue, Cline, Roo, Zed, AGENTS.md)
- [ ] VSCode extension UI
- [ ] One-click expand to full
- [ ] Two-way compression (input + output)
- [ ] Web dashboard (team tier, paid)

---

## License

MIT — free for personal and commercial use.

---

## Contributing

Issues and PRs welcome. See [docs/](./docs/).
