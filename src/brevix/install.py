"""Multi-platform installer — generate Brevix rule files for any LLM coding tool.

Brevix rules live in a single source: templates/brevix_rules.md. This module
adapts that source to each tool's plugin/rule format and writes it into the
target project (or merges into a shared file like AGENTS.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Callable


# Marker pair so Brevix sections in shared files (AGENTS.md, CONVENTIONS.md,
# copilot-instructions.md) can be updated/removed without nuking surrounding
# content the user added themselves.
MARKER_START = "<!-- BREVIX:BEGIN -->"
MARKER_END = "<!-- BREVIX:END -->"


@dataclass
class Target:
    name: str
    description: str
    write: Callable[[Path, str], list[Path]]


def _load_rules() -> str:
    return resources.files("brevix.templates").joinpath("brevix_rules.md").read_text(encoding="utf-8")


def _wrap_with_markers(body: str) -> str:
    return f"{MARKER_START}\n\n{body}\n\n{MARKER_END}\n"


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _merge_section(path: Path, body: str, header: str = "## Brevix Compression Mode") -> Path:
    """Insert/update a Brevix section in a shared markdown file."""
    section = _wrap_with_markers(f"{header}\n\n{body}")
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if MARKER_START in existing and MARKER_END in existing:
            before, _, rest = existing.partition(MARKER_START)
            _, _, after = rest.partition(MARKER_END)
            new = before.rstrip() + "\n\n" + section + after.lstrip()
        else:
            new = existing.rstrip() + "\n\n" + section
    else:
        new = section
    return _write(path, new)


# --- Per-platform installers ---

def install_claude_code(root: Path, rules: str) -> list[Path]:
    written = []
    written.append(_write(root / ".claude-plugin" / "plugin.json", _claude_plugin_json()))
    written.append(_write(root / ".claude-plugin" / "marketplace.json", _claude_marketplace_json()))
    written.append(_write(root / "skills" / "brevix" / "SKILL.md", _claude_skill_brevix(rules)))
    written.append(_write(root / "commands" / "brevix.md", _claude_command_brevix()))
    return written


def install_cursor(root: Path, rules: str) -> list[Path]:
    body = (
        "---\n"
        "description: Brevix output compression mode\n"
        "globs: [\"**/*\"]\n"
        "alwaysApply: true\n"
        "---\n\n"
        + rules
    )
    return [_write(root / ".cursor" / "rules" / "brevix.mdc", body)]


def install_windsurf(root: Path, rules: str) -> list[Path]:
    return [_write(root / ".windsurf" / "rules" / "brevix.md", rules)]


def install_codex(root: Path, rules: str) -> list[Path]:
    """OpenAI Codex CLI: AGENTS.md + .codex/hooks.json for auto-activation.

    Codex doesn't support slash commands, so users invoke via `$brevix` prefix.
    """
    written = [_merge_section(root / "AGENTS.md", rules)]
    hooks_json = (
        '{\n'
        '  "version": 1,\n'
        '  "hooks": {\n'
        '    "session_start": [\n'
        '      { "type": "context", "content": '
        '"Brevix mode active. Compress prose 40-75%. Drop articles/filler/pleasantries/hedges. '
        'Code/commits/security stay normal. Switch with $brevix lite|full|ultra|auto. '
        'Stop with $brevix off." }\n'
        '    ]\n'
        '  }\n'
        '}\n'
    )
    written.append(_write(root / ".codex" / "hooks.json", hooks_json))
    return written


def install_antigravity(root: Path, rules: str) -> list[Path]:
    # Google Antigravity reads AGENTS.md.
    return [_merge_section(root / "AGENTS.md", rules)]


def install_copilot(root: Path, rules: str) -> list[Path]:
    return [_merge_section(root / ".github" / "copilot-instructions.md", rules)]


def install_aider(root: Path, rules: str) -> list[Path]:
    written = [_merge_section(root / "CONVENTIONS.md", rules)]
    aider_conf = root / ".aider.conf.yml"
    line = "read: CONVENTIONS.md\n"
    if aider_conf.exists():
        existing = aider_conf.read_text(encoding="utf-8")
        if "CONVENTIONS.md" not in existing:
            aider_conf.write_text(existing.rstrip() + "\n" + line, encoding="utf-8")
    else:
        aider_conf.write_text(line, encoding="utf-8")
    written.append(aider_conf)
    return written


def install_continue(root: Path, rules: str) -> list[Path]:
    return [_write(root / ".continue" / "rules" / "brevix.md", rules)]


def install_cline(root: Path, rules: str) -> list[Path]:
    return [_write(root / ".clinerules", rules)]


def install_roo(root: Path, rules: str) -> list[Path]:
    return [_write(root / ".roo" / "rules" / "brevix.md", rules)]


def install_zed(root: Path, rules: str) -> list[Path]:
    return [_merge_section(root / ".rules", rules)]


def install_agents_md(root: Path, rules: str) -> list[Path]:
    """Universal AGENTS.md target — read by Codex, Antigravity, Cursor (newer),
    Continue, Cline, Roo, and others adopting the convention."""
    return [_merge_section(root / "AGENTS.md", rules)]


def install_gemini(root: Path, rules: str) -> list[Path]:
    """Google Gemini CLI extension: gemini-extension.json + GEMINI.md."""
    import json as _json
    ext = {
        "name": "brevix",
        "version": "0.4.0",
        "description": "Brevix output compression for Gemini CLI.",
        "files": ["GEMINI.md"],
    }
    written = [
        _write(root / "gemini-extension.json", _json.dumps(ext, indent=2) + "\n"),
        _write(root / "GEMINI.md", rules),
    ]
    return written


def install_augment(root: Path, rules: str) -> list[Path]:
    return [_write(root / ".augment" / "rules" / "brevix.md", rules)]


def install_kilo(root: Path, rules: str) -> list[Path]:
    return [_write(root / ".kilocode" / "rules" / "brevix.md", rules)]


def install_openhands(root: Path, rules: str) -> list[Path]:
    return [_merge_section(root / ".openhands" / "microagents" / "brevix.md", rules)]


def install_tabnine(root: Path, rules: str) -> list[Path]:
    return [_write(root / ".tabnine" / "rules" / "brevix.md", rules)]


def install_warp(root: Path, rules: str) -> list[Path]:
    return [_merge_section(root / ".warp" / "RULES.md", rules)]


def install_replit(root: Path, rules: str) -> list[Path]:
    return [_merge_section(root / ".replit" / "ai-rules.md", rules)]


def install_sourcegraph_amp(root: Path, rules: str) -> list[Path]:
    return [_write(root / ".amp" / "rules" / "brevix.md", rules)]


# --- Registry ---

TARGETS: dict[str, Target] = {
    "claude-code": Target("claude-code", "Claude Code plugin (.claude-plugin/, skills/, commands/)", install_claude_code),
    "cursor": Target("cursor", "Cursor IDE rules (.cursor/rules/brevix.mdc)", install_cursor),
    "windsurf": Target("windsurf", "Windsurf rules (.windsurf/rules/brevix.md)", install_windsurf),
    "codex": Target("codex", "OpenAI Codex CLI (AGENTS.md + .codex/hooks.json)", install_codex),
    "antigravity": Target("antigravity", "Google Antigravity (AGENTS.md)", install_antigravity),
    "copilot": Target("copilot", "GitHub Copilot Chat (.github/copilot-instructions.md)", install_copilot),
    "aider": Target("aider", "Aider (CONVENTIONS.md + .aider.conf.yml)", install_aider),
    "continue": Target("continue", "Continue.dev (.continue/rules/brevix.md)", install_continue),
    "cline": Target("cline", "Cline (.clinerules)", install_cline),
    "roo": Target("roo", "Roo Code (.roo/rules/brevix.md)", install_roo),
    "zed": Target("zed", "Zed AI (.rules)", install_zed),
    "gemini": Target("gemini", "Google Gemini CLI (gemini-extension.json + GEMINI.md)", install_gemini),
    "augment": Target("augment", "Augment Code (.augment/rules/brevix.md)", install_augment),
    "kilo": Target("kilo", "Kilo Code (.kilocode/rules/brevix.md)", install_kilo),
    "openhands": Target("openhands", "OpenHands (.openhands/microagents/brevix.md)", install_openhands),
    "tabnine": Target("tabnine", "Tabnine (.tabnine/rules/brevix.md)", install_tabnine),
    "warp": Target("warp", "Warp Terminal (.warp/RULES.md)", install_warp),
    "replit": Target("replit", "Replit AI (.replit/ai-rules.md)", install_replit),
    "sourcegraph-amp": Target("sourcegraph-amp", "Sourcegraph Amp (.amp/rules/brevix.md)", install_sourcegraph_amp),
    "agents-md": Target("agents-md", "Universal AGENTS.md (cross-tool standard)", install_agents_md),
}


def install(target: str, root: Path | str = ".") -> list[Path]:
    root_path = Path(root).resolve()
    rules = _load_rules()
    if target == "all":
        all_files: list[Path] = []
        for t in TARGETS.values():
            all_files.extend(t.write(root_path, rules))
        return all_files
    if target not in TARGETS:
        raise ValueError(f"Unknown target: {target}. Run `brevix install --list` to see options.")
    return TARGETS[target].write(root_path, rules)


def list_targets() -> str:
    rows = ["Available install targets:", ""]
    width = max(len(name) for name in TARGETS)
    for t in TARGETS.values():
        rows.append(f"  {t.name:<{width}}  {t.description}")
    rows.append(f"  {'all':<{width}}  All targets above")
    return "\n".join(rows)


# --- Claude Code static content ---

def _claude_plugin_json() -> str:
    import json
    payload = {
        "name": "brevix",
        "version": "0.3.0",
        "description": "Compress LLM output safely. Save tokens without breaking your code.",
        "author": {"name": "Yash Koladiya", "email": "yashkoladiya123@gmail.com"},
        "license": "MIT",
        "homepage": "https://github.com/Yash-Koladiya30/brevix",
        "repository": "https://github.com/Yash-Koladiya30/brevix",
        "keywords": ["compression", "tokens", "cost-optimization", "accuracy-guard", "semantic-verification", "adaptive-mode", "rule-engine"],
    }
    return json.dumps(payload, indent=2) + "\n"


def _claude_marketplace_json() -> str:
    import json
    payload = {
        "name": "brevix",
        "owner": {"name": "Yash-Koladiya30", "email": "yashkoladiya123@gmail.com"},
        "metadata": {"description": "Brevix marketplace.", "version": "0.3.0"},
        "plugins": [
            {
                "name": "brevix",
                "source": "./",
                "description": "Compress Claude responses 40-75% with semantic Accuracy Guard.",
                "version": "0.3.0",
                "category": "productivity",
                "tags": ["compression", "tokens", "cost-optimization", "accuracy-guard", "semantic-verification", "adaptive-mode"],
                "license": "MIT",
                "homepage": "https://github.com/Yash-Koladiya30/brevix",
            }
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


def _claude_skill_brevix(rules: str) -> str:
    frontmatter = (
        "---\n"
        "name: brevix\n"
        "description: Toggle Brevix compression mode (lite/full/ultra/auto). "
        "Compresses Claude's responses to save tokens while preserving meaning.\n"
        "---\n\n"
    )
    return frontmatter + rules


def _claude_command_brevix() -> str:
    return (
        "---\n"
        "description: Toggle Brevix compression mode (lite | full | ultra | auto | off).\n"
        "argument-hint: \"[lite|full|ultra|auto|off]\"\n"
        "---\n\n"
        "Activate Brevix compression for this conversation. Argument `$ARGUMENTS` "
        "selects level (default `full`). `off` disables. See "
        "[skills/brevix/SKILL.md](../skills/brevix/SKILL.md) for rules.\n"
    )
