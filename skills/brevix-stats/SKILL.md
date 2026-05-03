---
name: brevix-stats
description: Show local Brevix compression stats — total tokens saved, characters saved, estimated cost savings, and breakdown by mode. Reads from ~/.brevix/stats.json.
---

# Brevix Stats

Display the user's compression savings.

## Workflow

1. Run `brevix stats` in the shell
2. Pass through the output as-is — it is already terse
3. If `brevix` CLI is not installed, instruct the user to install it:
   ```
   pip install brevix
   ```
   or via the install script:
   ```
   curl -fsSL https://raw.githubusercontent.com/Yash-Koladiya30/brevix/main/install.sh | bash
   ```

## Reset

If the user asks to reset stats:
```
brevix stats --reset
```

## Notes

- Stats are local-only (`~/.brevix/stats.json`). No telemetry, no cloud.
- `$$` saved is an estimate based on average Claude/GPT pricing (~$3 per million output tokens).