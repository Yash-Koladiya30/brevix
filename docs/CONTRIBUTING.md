# Contributing to Brevix

Thanks for considering a contribution. Brevix aims to be small, deterministic, and trustworthy — keep that in mind for any change.

## Quick start

```bash
git clone https://github.com/Yash-Koladiya30/brevix.git
cd brevix
pip install -e '.[dev,all]'
pytest
```

## Project layout

```
src/brevix/         Python library (compressor, guard, stats, install, …)
hooks/              Claude Code hooks (Node.js) + statusline scripts
agents/             Subagent skill files (investigator/builder/reviewer)
mcp-servers/        Node.js MCP middleware (brevix-shrink)
skills/             Claude Code skills
commands/           Claude Code slash commands
.claude-plugin/     Plugin + marketplace manifests
evals/              Three-arm A/B harness
tests/              pytest suite
```

## What changes are welcome

- New verbose-to-terse phrase mappings (with a test).
- New install targets for LLM coding tools (with a test).
- Bug fixes and edge cases in protected-region handling.
- Real benchmark contributions in `evals/snapshots/`.

## What is out of scope

- Anything that mutates code blocks, URLs, error messages, or technical identifiers.
- LLM-based rewriting (Brevix is rule-based on purpose — predictable, no API cost).
- Network calls in the core engine.

## Style

- 100-char lines.
- Type hints required on public APIs.
- Tests required for new rules and install targets.
- No comments unless the *why* is non-obvious.

## Submitting a PR

1. Fork + branch.
2. Add tests, run `pytest`.
3. Run `ruff check .` if available.
4. Open a PR against `main`. Conventional Commit titles preferred.

## License

By contributing, you agree your work is licensed under MIT.
