# Brevix

> Compress LLM output safely. Save tokens without breaking your code.

Brevix is a Claude Code plugin (and CLI) that reduces LLM output tokens by 40-75% using terse, fragment-style responses — **with built-in accuracy checking** so compression never silently breaks your work.

Inspired by [Caveman](https://github.com/JuliusBrussee/caveman). Built for production.

---

## Why Brevix?

| Feature | Caveman | **Brevix** |
|---------|---------|------------|
| Lite / Full / Ultra modes | ✅ | ✅ |
| Slash commands | ✅ | ✅ |
| Multi-agent support | ✅ | ✅ (Claude Code first, more coming) |
| **Accuracy Guard** (semantic check) | ❌ | ✅ |
| **Auto-warn on meaning loss** | ❌ | ✅ |
| **Local stats counter** | basic | ✅ |
| **One-click expand to full** | ❌ | ✅ (planned) |
| Free + MIT | ✅ | ✅ |

**Killer differentiator:** Brevix verifies compressed output preserves meaning before showing it to you. Caveman compresses blindly.

---

## Install (30 sec)

### Claude Code plugin

```
/plugin marketplace add Yash-Koladiya30/brevix
/plugin install brevix@brevix
```

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

---

## Usage

### In Claude Code

```
/brevix                # toggle on (full mode)
/brevix lite           # gentle compression
/brevix ultra          # max compression
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
```

---

## How Accuracy Guard works

1. Brevix compresses output using rule engine
2. Embeds both compressed and full versions locally (sentence-transformers, no API cost)
3. Computes cosine similarity
4. If similarity < threshold (default 0.85), warns you or auto-falls back to full
5. Result: compression you can trust on production code, specs, contracts

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
- [x] Accuracy Guard
- [x] Local stats
- [ ] VSCode extension
- [ ] Cursor / Codex / Gemini CLI support
- [ ] Adaptive compression (auto-pick mode per task)
- [ ] Two-way compression (input + output)
- [ ] Web dashboard (team tier, paid)

---

## License

MIT — free for personal and commercial use.

---

## Contributing

Issues and PRs welcome. See [CONTRIBUTING.md](./docs/CONTRIBUTING.md).
