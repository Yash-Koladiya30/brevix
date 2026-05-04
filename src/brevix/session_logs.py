"""Parse Claude Code JSONL session logs for real token usage.

Claude Code persists every message turn at:
  ~/.claude/projects/<sanitized-cwd>/<session-uuid>.jsonl

Each line is a JSON record. Assistant turns include a `usage` field with
input/output token counts. We aggregate these for honest savings stats —
not the chars/4 estimate the in-process Compressor has to use.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable


CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"


@dataclass
class SessionStats:
    sessions: int = 0
    assistant_turns: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    first_seen: str = ""
    last_seen: str = ""
    by_model: dict = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def estimated_cost_usd(self) -> float:
        # Rough blended rate. Claude Sonnet output ~$15/Mtok, input ~$3/Mtok.
        return (self.output_tokens / 1_000_000) * 15.0 + (self.input_tokens / 1_000_000) * 3.0


def _parse_since(since: str) -> datetime | None:
    """Convert '7d' / '24h' / '30m' / 'all' to a UTC cutoff datetime."""
    if not since or since == "all":
        return None
    m = re.fullmatch(r"(\d+)\s*([dhm])", since.strip().lower())
    if not m:
        raise ValueError(f"Invalid --since '{since}'. Expected formats: 7d, 24h, 30m, all.")
    n, unit = int(m.group(1)), m.group(2)
    delta = {"d": timedelta(days=n), "h": timedelta(hours=n), "m": timedelta(minutes=n)}[unit]
    return datetime.now(timezone.utc) - delta


def _iter_log_files(root: Path = CLAUDE_PROJECTS) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("*.jsonl"))


def _parse_timestamp(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_logs(since: str = "all", root: Path = CLAUDE_PROJECTS) -> SessionStats:
    """Walk Claude session logs and aggregate token usage."""
    cutoff = _parse_since(since)
    stats = SessionStats()
    seen_sessions: set[str] = set()

    for log_path in _iter_log_files(root):
        session_used = False
        for line in _read_lines(log_path):
            record = _safe_json(line)
            if not record:
                continue
            ts = _parse_timestamp(record.get("timestamp"))
            if cutoff and ts and ts < cutoff:
                continue

            usage = _extract_usage(record)
            if not usage:
                continue

            stats.assistant_turns += 1
            stats.input_tokens += int(usage.get("input_tokens", 0) or 0)
            stats.output_tokens += int(usage.get("output_tokens", 0) or 0)
            stats.cache_read_tokens += int(usage.get("cache_read_input_tokens", 0) or 0)
            stats.cache_creation_tokens += int(usage.get("cache_creation_input_tokens", 0) or 0)

            model = _extract_model(record)
            if model:
                stats.by_model[model] = stats.by_model.get(model, 0) + int(usage.get("output_tokens", 0) or 0)

            if ts:
                ts_iso = ts.isoformat(timespec="seconds")
                if not stats.first_seen or ts_iso < stats.first_seen:
                    stats.first_seen = ts_iso
                if not stats.last_seen or ts_iso > stats.last_seen:
                    stats.last_seen = ts_iso

            session_used = True

        if session_used:
            seen_sessions.add(log_path.stem)

    stats.sessions = len(seen_sessions)
    return stats


def _read_lines(path: Path) -> Iterable[str]:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield line
    except OSError:
        return


def _safe_json(line: str) -> dict | None:
    try:
        return json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return None


def _extract_usage(record: dict) -> dict | None:
    """Find the usage block. Schema has shifted across Claude Code versions."""
    msg = record.get("message")
    if isinstance(msg, dict):
        usage = msg.get("usage")
        if isinstance(usage, dict):
            return usage
    usage = record.get("usage")
    if isinstance(usage, dict):
        return usage
    return None


def _extract_model(record: dict) -> str | None:
    msg = record.get("message")
    if isinstance(msg, dict):
        m = msg.get("model")
        if isinstance(m, str):
            return m
    m = record.get("model")
    return m if isinstance(m, str) else None


def estimate_savings_from_baseline(stats: SessionStats, baseline_factor: float = 2.5) -> dict:
    """Estimate tokens that *would have* been used without Brevix.

    `baseline_factor` is the heuristic ratio of verbose-output tokens to
    Brevix-output tokens, derived from benchmark testing (~60-65% reduction
    means roughly 2.5x more tokens without compression). Conservative;
    users can override.
    """
    output = stats.output_tokens
    baseline = int(output * baseline_factor)
    saved = max(0, baseline - output)
    return {
        "actual_output_tokens": output,
        "estimated_baseline_tokens": baseline,
        "estimated_tokens_saved": saved,
        "estimated_pct_saved": round(100 * saved / baseline, 1) if baseline else 0.0,
        "estimated_usd_saved": round((saved / 1_000_000) * 15.0, 4),
    }
