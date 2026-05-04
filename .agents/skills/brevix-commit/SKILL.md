---
name: brevix-commit
description: Generate compressed conventional commit messages. Subject ≤50 chars. Body only when "why" is non-obvious. Triggers on /brevix-commit, "write a commit", or staging changes.
---

# Brevix Commit Generator

Produce a Conventional Commit message that strips noise while preserving intent.

## Format

```
<type>(<scope>): <subject>

<body — only if non-obvious why>
```

## Rules

- **Subject**: ≤50 chars, lowercase, imperative mood, no trailing period
- **Type**: feat, fix, refactor, perf, docs, test, chore, build, ci, style
- **Scope**: optional — module or file area
- **Body**: 2–4 lines max. Only when *why* isn't obvious from the diff. Skip "what" — the diff shows that.
- **Footer**: only for breaking changes or issue refs

## Examples

```
feat(auth): add JWT refresh endpoint

Token rotation needed for mobile clients with offline windows.
Refresh expires after 30d to limit blast radius if leaked.
```

```
fix(parser): handle empty input
```

```
refactor(api): extract retry logic into helper
```

## Skip

- "Update X file" — useless
- "Various improvements" — vague
- Long prose — the PR description is the right place

## Workflow

1. Run `git diff --cached` to see staged changes
2. Identify the dominant change type
3. Pick scope from the affected file/module
4. Draft subject ≤50 chars
5. Add body only if a reviewer would ask "why?"