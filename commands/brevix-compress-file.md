---
description: Compress a memory file (CLAUDE.md, AGENTS.md, project notes) in place with backup.
argument-hint: "<path> [--mode lite|full|ultra] [--dry-run] [--force]"
allowed-tools: Bash
---

Run Brevix file compression on the target file. Brevix:

1. Reads the file.
2. Applies compression rules (default: full mode).
3. Saves an untouched copy as `<file>.original.<ext>`.
4. Writes the compressed text back to the original path.
5. Runs Accuracy Guard. If similarity < 0.85, the operation is skipped unless `--force`.

Run:
```bash
brevix compress-file $ARGUMENTS
```

Report the savings and the backup path.
