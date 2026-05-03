---
description: Show local Brevix compression stats — tokens saved, $ saved, breakdown by mode.
argument-hint: "[--reset]"
allowed-tools: Bash
---

Display Brevix savings from `~/.brevix/stats.json`.

1. If `$ARGUMENTS` contains `--reset`, run `brevix stats --reset`.
2. Otherwise run `brevix stats` and pass through output as-is (already terse).
3. If `brevix` CLI is missing, instruct user:
   ```bash
   pip install brevix
   ```
