---
description: Toggle Brevix compression mode (lite | full | ultra | auto | off). Default full.
argument-hint: "[lite|full|ultra|auto|off]"
allowed-tools: Read
---

Activate Brevix compression for this conversation.

**Argument:** `$ARGUMENTS` — one of `lite`, `full`, `ultra`, `auto`, `off`. Default: `full`.

**FIRST LINE OF YOUR REPLY MUST BE:** `Brevix: <level> active.` (or `Brevix: off.` if argument is `off`).

After acknowledging:

- If argument is `off`: stop applying Brevix compression rules and resume normal output for the rest of the session.
- Otherwise: read [skills/brevix/SKILL.md](../skills/brevix/SKILL.md) for the rule set and apply compression to every response until the user says `/brevix off`, `stop brevix`, or `normal mode`.

Levels:
- **lite** — gentle (~20-30% savings). Drop pleasantries, filler, hedges. Keep articles, full sentences.
- **full** (default) — drop articles, fragments OK, short synonyms (~40-60% savings).
- **ultra** — arrows for causation, `=` for equivalence, drop transitionals (~60-80% savings).
- **auto** — adapt mode per response, picking most aggressive that passes Accuracy Guard.
- **off** — disable Brevix.

**Boundaries:** code blocks, commit messages, security warnings, and irreversible-action confirmations are written normally regardless of level.
