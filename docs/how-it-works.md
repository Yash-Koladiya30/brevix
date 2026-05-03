# How Brevix works

Brevix is two pieces working together: a **rule-based compression engine** and an **Accuracy Guard** that verifies meaning is preserved.

## 1. Compression engine

Pure Python, zero LLM calls, runs locally. The engine applies layered transformations based on the active mode:

### Lite (gentle, ~20-30% savings)
- Strips pleasantries: "Sure!", "I'd be happy to help"
- Strips filler: just, really, basically, actually
- Strips hedges: "I think", "it seems", "in my opinion"
- Replaces verbose phrases: "in order to" → "to", "make use of" → "use"
- Keeps articles, full sentences, full grammar

### Full (default, ~40-60% savings)
- All Lite rules
- Drops articles (a / an / the)
- Allows sentence fragments
- Pattern: `[thing] [action] [reason]. [next step].`

### Ultra (~60-80% savings)
- All Full rules
- Replaces `because` / `leads to` / `results in` → `→`
- Replaces `which is` / definitions → `=`
- Drops most transitional words

## 2. Protected regions (never compressed)

Before applying rules, Brevix replaces these with placeholders so they pass through unchanged:

- Code fences (```` ```...``` ````)
- Inline code (`` `...` ``)
- URLs (http(s)://...)
- Quoted error messages and stack traces

After compression runs, the placeholders are restored.

## 3. Accuracy Guard

The killer feature. After compression, Brevix can verify the compressed text still means the same thing as the original.

**How:**
1. Encode both texts with a small local embedding model (`sentence-transformers/all-MiniLM-L6-v2`, ~80 MB)
2. Compute cosine similarity
3. If similarity ≥ threshold (default 0.85): pass
4. If below: warn the user, or in `--strict` mode fall back to the original

**Why this matters:** caveman-style compression can silently break meaning on dense technical text. Accuracy Guard catches it.

**Cost:** zero — runs locally, no API calls. First run downloads the model (~80 MB cache). Subsequent runs are <100 ms per check on CPU.

**Fallback:** if `sentence-transformers` is not installed, Brevix degrades to Jaccard token-overlap similarity. Less precise but no hard dependency.

## 4. Stats

`~/.brevix/stats.json` records cumulative savings:
- Total compressions
- Characters saved
- Estimated tokens saved (chars / 4)
- Estimated $$ saved (tokens × $3 per million)
- Breakdown by mode

`brevix stats` prints a summary. No telemetry leaves your machine.

## 5. Claude Code plugin

The plugin in `.claude/plugins/brevix/` ships skills (`brevix.md`, `brevix-commit.md`, `brevix-stats.md`) that Claude Code loads on demand. The compression rules are documented in the skill markdown so Claude itself follows them when generating responses — no runtime hook needed.

## Limits

- Rule-based, not ML — won't paraphrase creatively, only trims
- Optimized for English (other languages fall back to Lite-equivalent transforms)
- Quality drops on very dense math/code prose at Ultra mode (use Accuracy Guard)
