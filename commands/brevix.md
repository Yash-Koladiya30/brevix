---
description: Toggle Brevix compression mode (lite | full | ultra | off). Default full.
argument-hint: "[lite|full|ultra|off]"
allowed-tools: Read
---

Activate Brevix compression for this conversation.

**Argument:** `$ARGUMENTS` — one of `lite`, `full`, `ultra`, `off`. Default: `full`.

If argument is `off`, stop applying Brevix compression rules and resume normal output. Otherwise:

1. Set active level to the argument (or `full` if empty).
2. Read [skills/brevix/SKILL.md](../skills/brevix/SKILL.md) for the rule set.
3. Apply compression rules to every response until user says `/brevix off`, "stop brevix", or "normal mode".
4. Acknowledge with one short line: `Brevix: <level> active.`

**Boundaries:** code blocks, commit messages, security warnings, and irreversible-action confirmations are written normally.
