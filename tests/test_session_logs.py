"""Tests for Claude Code JSONL session log parser."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from brevix.session_logs import (
    SessionStats,
    _parse_since,
    estimate_savings_from_baseline,
    parse_logs,
)


def _ts(minutes_ago: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()


def _write_session(dir: Path, name: str, records: list[dict]) -> Path:
    p = dir / f"{name}.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return p


def test_parse_since_units():
    now = datetime.now(timezone.utc)
    assert _parse_since("all") is None
    assert (now - _parse_since("7d")).days in (6, 7)
    assert (now - _parse_since("24h")).total_seconds() // 3600 in (23, 24)
    assert (now - _parse_since("30m")).total_seconds() // 60 in (29, 30)


def test_parse_since_invalid():
    with pytest.raises(ValueError):
        _parse_since("garbage")


def test_parse_logs_aggregates_usage(tmp_path: Path) -> None:
    proj = tmp_path / "projects" / "myrepo"
    proj.mkdir(parents=True)
    _write_session(proj, "session-1", [
        {"timestamp": _ts(60), "message": {"model": "claude-sonnet-4-6",
                                            "usage": {"input_tokens": 100, "output_tokens": 50}}},
        {"timestamp": _ts(30), "message": {"model": "claude-sonnet-4-6",
                                            "usage": {"input_tokens": 200, "output_tokens": 80}}},
    ])
    _write_session(proj, "session-2", [
        {"timestamp": _ts(10), "message": {"model": "claude-haiku-4-5",
                                            "usage": {"input_tokens": 50, "output_tokens": 25}}},
    ])

    s = parse_logs(since="all", root=tmp_path / "projects")
    assert s.sessions == 2
    assert s.assistant_turns == 3
    assert s.input_tokens == 350
    assert s.output_tokens == 155
    assert s.by_model["claude-sonnet-4-6"] == 130
    assert s.by_model["claude-haiku-4-5"] == 25


def test_parse_logs_since_filter(tmp_path: Path) -> None:
    proj = tmp_path / "projects" / "myrepo"
    proj.mkdir(parents=True)
    _write_session(proj, "old", [
        {"timestamp": _ts(60 * 24 * 30), "message": {"usage": {"output_tokens": 1000}}},
    ])
    _write_session(proj, "new", [
        {"timestamp": _ts(10), "message": {"usage": {"output_tokens": 50}}},
    ])
    s = parse_logs(since="1h", root=tmp_path / "projects")
    assert s.output_tokens == 50


def test_parse_logs_handles_missing_dir(tmp_path: Path) -> None:
    s = parse_logs(since="all", root=tmp_path / "nonexistent")
    assert s.assistant_turns == 0
    assert s.output_tokens == 0


def test_parse_logs_skips_records_without_usage(tmp_path: Path) -> None:
    proj = tmp_path / "projects" / "x"
    proj.mkdir(parents=True)
    _write_session(proj, "s", [
        {"timestamp": _ts(1), "message": {"role": "user"}},  # no usage
        {"timestamp": _ts(1), "garbage": True},
        {"timestamp": _ts(1), "message": {"usage": {"output_tokens": 7}}},
    ])
    s = parse_logs(since="all", root=tmp_path / "projects")
    assert s.assistant_turns == 1
    assert s.output_tokens == 7


def test_estimate_savings_baseline():
    s = SessionStats(output_tokens=1000)
    est = estimate_savings_from_baseline(s, baseline_factor=2.5)
    assert est["estimated_baseline_tokens"] == 2500
    assert est["estimated_tokens_saved"] == 1500
    assert est["estimated_pct_saved"] == 60.0
