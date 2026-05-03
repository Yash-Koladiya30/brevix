---
description: Generate a compressed Conventional Commit message from staged changes.
allowed-tools: Bash, Read
---

Produce a terse Conventional Commit message for the currently staged changes.

1. Run `git diff --cached` to inspect staged changes.
2. Identify dominant change type: feat, fix, refactor, perf, docs, test, chore, build, ci, style.
3. Pick scope from affected module/file.
4. Follow rules in [skills/brevix-commit/SKILL.md](../skills/brevix-commit/SKILL.md):
   - Subject ≤50 chars, lowercase, imperative, no trailing period.
   - Body 2-4 lines, only when "why" is non-obvious.
5. Output the commit message in a code block. Do NOT run `git commit` automatically — let user review and run.
