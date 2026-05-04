"""Tests for multi-platform installer."""

from pathlib import Path

import pytest

from brevix.install import (
    TARGETS,
    MARKER_START,
    MARKER_END,
    install,
)


def test_list_targets_covers_major_tools():
    expected = {
        "claude-code", "cursor", "windsurf", "codex", "antigravity", "copilot",
        "aider", "continue", "cline", "roo", "zed", "agents-md",
        "gemini", "augment", "kilo", "openhands", "tabnine", "warp", "replit",
        "sourcegraph-amp",
    }
    assert expected.issubset(set(TARGETS))


def test_codex_writes_hooks_json(tmp_path):
    files = install("codex", tmp_path)
    rels = {str(f.relative_to(tmp_path)) for f in files}
    assert ".codex/hooks.json" in rels
    body = (tmp_path / ".codex" / "hooks.json").read_text(encoding="utf-8")
    assert "$brevix" in body


def test_gemini_writes_extension_and_md(tmp_path):
    files = install("gemini", tmp_path)
    rels = {str(f.relative_to(tmp_path)) for f in files}
    assert "gemini-extension.json" in rels
    assert "GEMINI.md" in rels


@pytest.mark.parametrize("target", list(TARGETS))
def test_each_target_writes_at_least_one_file(tmp_path: Path, target: str) -> None:
    files = install(target, tmp_path)
    assert files, f"{target} produced no files"
    for f in files:
        assert f.exists()
        assert f.read_text(encoding="utf-8")


def test_cursor_emits_mdc_with_frontmatter(tmp_path: Path) -> None:
    files = install("cursor", tmp_path)
    body = files[0].read_text(encoding="utf-8")
    assert files[0].suffix == ".mdc"
    assert body.startswith("---")
    assert "alwaysApply: true" in body
    assert "Brevix Compression Mode" in body


def test_codex_writes_agents_md_with_markers(tmp_path: Path) -> None:
    files = install("codex", tmp_path)
    body = files[0].read_text(encoding="utf-8")
    assert files[0].name == "AGENTS.md"
    assert MARKER_START in body
    assert MARKER_END in body


def test_agents_md_idempotent(tmp_path: Path) -> None:
    install("agents-md", tmp_path)
    install("agents-md", tmp_path)
    body = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert body.count(MARKER_START) == 1
    assert body.count(MARKER_END) == 1


def test_agents_md_preserves_user_content(tmp_path: Path) -> None:
    p = tmp_path / "AGENTS.md"
    p.write_text("# My existing instructions\n\nDo not delete this.\n", encoding="utf-8")
    install("agents-md", tmp_path)
    body = p.read_text(encoding="utf-8")
    assert "Do not delete this." in body
    assert MARKER_START in body


def test_aider_writes_conventions_and_config(tmp_path: Path) -> None:
    files = install("aider", tmp_path)
    paths = {f.name for f in files}
    assert "CONVENTIONS.md" in paths
    assert ".aider.conf.yml" in paths
    config = (tmp_path / ".aider.conf.yml").read_text(encoding="utf-8")
    assert "CONVENTIONS.md" in config


def test_install_all_runs_all_targets(tmp_path: Path) -> None:
    files = install("all", tmp_path)
    assert len(files) >= len(TARGETS)


def test_unknown_target_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        install("nonexistent-tool", tmp_path)


def test_claude_code_full_layout(tmp_path: Path) -> None:
    files = install("claude-code", tmp_path)
    rels = {str(f.relative_to(tmp_path)) for f in files}
    assert ".claude-plugin/plugin.json" in rels
    assert ".claude-plugin/marketplace.json" in rels
    assert any(r.endswith("brevix/SKILL.md") for r in rels)
    assert any(r.endswith("brevix.md") and "commands" in r for r in rels)
