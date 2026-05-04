---
description: Show local Brevix compression stats — tokens saved, $ saved, breakdown by mode.
argument-hint: "[--real] [--since 7d] [--share] [--reset]"
allowed-tools: Bash
---

Display Brevix savings.

Parse `$ARGUMENTS` for flags:

- `--reset` → run `brevix stats --reset`
- `--real` → parse real Claude Code JSONL session logs (no estimates)
- `--since 7d` (or `24h`, `30m`, `all`) → time window
- `--share` → tweet-ready one-line output

Run the resolved command and pass output through as-is (already terse).

If `brevix` CLI is missing, instruct user:
```bash
pip install brevix
```
