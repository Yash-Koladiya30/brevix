"""Tests for brevix.route.route_stats + RoutedClient logging hook (Phase 4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

from brevix.route import (
    BudgetTracker,
    DEFAULT_RULES,
    Provider,
    RouteConfig,
    RoutedClient,
    Router,
    RoutingSummary,
    log_call,
    read_log,
    render_summary,
    reset_log,
    summarize,
)


# ---------- log_call + read_log ----------

def test_log_call_appends_jsonl(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    log_call(
        task="classify",
        model="claude-haiku-4-5",
        input_tokens=10,
        output_tokens=20,
        cost_usd=0.0001,
        confidence=0.9,
        escalations=0,
        attempts=1,
        path=p,
    )
    log_call(
        task="code_review",
        model="claude-sonnet-4-6",
        input_tokens=100,
        output_tokens=200,
        cost_usd=0.0033,
        confidence=0.8,
        escalations=0,
        attempts=1,
        path=p,
    )
    entries = list(read_log(p))
    assert len(entries) == 2
    assert entries[0]["task"] == "classify"
    assert entries[1]["model"] == "claude-sonnet-4-6"
    assert "ts" in entries[0]


def test_read_log_skips_corrupt_lines(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    p.write_text(
        json.dumps({"task": "x", "model": "claude-haiku-4-5", "input_tokens": 1,
                    "output_tokens": 1, "cost_usd": 0.0,
                    "confidence": 1.0, "escalations": 0, "attempts": 1}) + "\n"
        "{not valid json}\n"
        "\n"
        + json.dumps({"task": "y", "model": "claude-opus-4-7", "input_tokens": 1,
                      "output_tokens": 1, "cost_usd": 0.0,
                      "confidence": 1.0, "escalations": 0, "attempts": 1}) + "\n"
    )
    entries = list(read_log(p))
    assert len(entries) == 2
    assert entries[0]["task"] == "x"
    assert entries[1]["task"] == "y"


def test_read_log_missing_file_yields_nothing(tmp_path: Path):
    entries = list(read_log(tmp_path / "nope.jsonl"))
    assert entries == []


def test_reset_log_removes_file(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    log_call(task="x", model="claude-haiku-4-5", input_tokens=1, output_tokens=1,
             cost_usd=0.0, confidence=1.0, escalations=0, attempts=1, path=p)
    assert p.exists()
    reset_log(p)
    assert not p.exists()
    # idempotent
    reset_log(p)


# ---------- summarize ----------

def _seed_log(p: Path) -> None:
    log_call(task="classify", model="claude-haiku-4-5",
             input_tokens=100, output_tokens=50, cost_usd=0.000350,
             confidence=0.9, escalations=0, attempts=1, path=p)
    log_call(task="classify", model="claude-haiku-4-5",
             input_tokens=200, output_tokens=100, cost_usd=0.000700,
             confidence=0.85, escalations=0, attempts=1, path=p)
    log_call(task="code_review", model="claude-sonnet-4-6",
             input_tokens=500, output_tokens=300, cost_usd=0.006000,
             confidence=0.7, escalations=1, attempts=2, path=p)
    log_call(task="architecture", model="claude-opus-4-7",
             input_tokens=1000, output_tokens=500, cost_usd=0.052500,
             confidence=0.95, escalations=0, attempts=1, path=p)


def test_summarize_aggregates_correctly(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    _seed_log(p)
    s = summarize(since="all", path=p)
    assert s.total_calls == 4
    assert s.total_input_tokens == 1800
    assert s.total_output_tokens == 950
    assert s.total_cost_usd == pytest.approx(0.05955)
    assert s.escalation_count == 1
    assert s.escalation_rate == pytest.approx(25.0)
    # by_model
    assert s.by_model["claude-haiku-4-5"]["calls"] == 2
    assert s.by_model["claude-sonnet-4-6"]["calls"] == 1
    # by_task
    assert s.by_task["classify"]["calls"] == 2
    assert s.by_task["architecture"]["calls"] == 1


def test_summarize_baseline_is_opus_only(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    _seed_log(p)
    s = summarize(since="all", path=p)
    # Opus baseline: every call repriced as Opus.
    # tokens: 1800 in + 950 out
    # opus: 15 in/Mtok, 75 out/Mtok
    expected = (1800 / 1_000_000) * 15 + (950 / 1_000_000) * 75
    assert s.baseline_cost_usd == pytest.approx(expected)
    # Saved is non-negative.
    assert s.saved_usd >= 0


def test_summarize_empty_log_returns_zero_summary(tmp_path: Path):
    s = summarize(since="all", path=tmp_path / "missing.jsonl")
    assert s.total_calls == 0
    assert s.saved_pct == 0.0
    assert s.escalation_rate == 0.0


def test_summarize_invalid_since_raises(tmp_path: Path):
    with pytest.raises(ValueError):
        summarize(since="bad", path=tmp_path / "log.jsonl")


def test_summarize_since_filter_excludes_old(tmp_path: Path):
    """Stamp an entry with a synthetic old timestamp -> excluded by since=1h."""
    p = tmp_path / "log.jsonl"
    p.write_text(
        json.dumps({
            "ts": "2020-01-01T00:00:00+00:00",
            "task": "old",
            "model": "claude-haiku-4-5",
            "input_tokens": 1, "output_tokens": 1, "cost_usd": 0.0,
            "confidence": 1.0, "escalations": 0, "attempts": 1,
        }) + "\n"
    )
    log_call(task="new", model="claude-opus-4-7",
             input_tokens=10, output_tokens=10, cost_usd=0.001,
             confidence=1.0, escalations=0, attempts=1, path=p)
    s = summarize(since="1h", path=p)
    assert s.total_calls == 1
    assert "claude-opus-4-7" in s.by_model


def test_render_summary_smoke(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    _seed_log(p)
    out = render_summary(summarize(since="all", path=p), since="all")
    assert "Brevix Routing Stats" in out
    assert "Saved:" in out
    assert "Escalations:" in out
    assert "By model:" in out
    assert "By task:" in out


def test_render_summary_empty(tmp_path: Path):
    out = render_summary(RoutingSummary(), since="all")
    assert "no routing calls logged yet" in out


# ---------- RoutedClient logging hook ----------

class _FakeProvider(Provider):
    name = "anthropic"

    def __init__(self, text="ok", in_tok=10, out_tok=10):
        self._text = text
        self._in = in_tok
        self._out = out_tok

    def call(self, model: str, messages: List[Dict[str, str]],
             max_tokens: int = 2000, system: Optional[str] = None,
             **kwargs: Any) -> Tuple[str, int, int, Any]:
        return self._text, self._in, self._out, {"fake": True}


def _client(tmp_path: Path, log_enabled: bool) -> RoutedClient:
    cfg = RouteConfig.from_dict(DEFAULT_RULES)
    budget = BudgetTracker(path=tmp_path / "budget.json")
    router = Router(config=cfg, budget=budget)
    fake = _FakeProvider()
    return RoutedClient(
        router=router,
        providers={"anthropic": fake, "openai": fake},
        log_enabled=log_enabled,
        log_path=tmp_path / "log.jsonl",
    )


def test_routed_client_writes_log_when_enabled(tmp_path: Path):
    client = _client(tmp_path, log_enabled=True)
    client.call("Classify this ticket")
    entries = list(read_log(tmp_path / "log.jsonl"))
    assert len(entries) == 1
    e = entries[0]
    assert e["task"] == "classify"
    assert "haiku" in e["model"].lower()
    assert e["attempts"] == 1
    assert e["escalations"] == 0


def test_routed_client_does_not_log_by_default(tmp_path: Path):
    client = _client(tmp_path, log_enabled=False)
    client.call("Classify this ticket")
    assert not (tmp_path / "log.jsonl").exists()


def test_routed_client_log_records_each_route_decision(tmp_path: Path):
    client = _client(tmp_path, log_enabled=True)
    client.call("Classify this ticket")
    client.call("Architect a payment system")
    client.call("Review this Flutter null safety code")
    entries = list(read_log(tmp_path / "log.jsonl"))
    assert len(entries) == 3
    tasks = [e["task"] for e in entries]
    assert tasks == ["classify", "architecture", "code_review"]
