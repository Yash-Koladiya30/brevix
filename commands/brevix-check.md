---
description: Run Accuracy Guard — check semantic similarity between original and compressed text.
argument-hint: "<original> | <compressed>"
allowed-tools: Bash
---

Verify a compression preserves meaning.

Parse `$ARGUMENTS` as `<original> | <compressed>` (split on first ` | `).

Run:
```bash
brevix check "<original>" "<compressed>"
```

Report similarity score, threshold, and pass/fail. If sentence-transformers is not installed, the check uses content-word containment fallback (still meaningful for compression — drops stopwords without penalty).
