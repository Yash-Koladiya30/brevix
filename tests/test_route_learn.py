"""Tests for brevix.route.learn — Phase 5 (suggest rule overrides)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from brevix.route import (
    DEFAULT_RULES,
    RouteConfig,
    Suggestion,
    analyze,
    apply_suggestions,
    log_call,
    render_suggestions,
    suggest_overrides,
)


# ---------- analyze ----------

def _seed_classify_log(p: Path, *, n_haiku: int, n_escalated_to_sonnet: int) -> None:
    """Write n_haiku entries that landed on Haiku (no escalation),
    plus n_escalated_to_sonnet entries that escalated and landed on Sonnet."""
    for _ in range(n_haiku):
        log_call(
            task="classify", model="claude-haiku-4-5",
            input_tokens=50, output_tokens=20, cost_usd=0.0001,
            confidence=0.9, escalations=0, attempts=1, path=p,
        )
    for _ in range(n_escalated_to_sonnet):
        log_call(
            task="classify", model="claude-sonnet-4-6",
            input_tokens=50, output_tokens=50, cost_usd=0.0008,
            confidence=0.85, escalations=1, attempts=2, path=p,
        )


def test_analyze_aggregates_per_task(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    _seed_classify_log(p, n_haiku=5, n_escalated_to_sonnet=15)
    log_call(
        task="architecture", model="claude-opus-4-7",
        input_tokens=500, output_tokens=300, cost_usd=0.030,
        confidence=0.95, escalations=0, attempts=1, path=p,
    )
    stats = analyze(p)
    assert stats["classify"].total_calls == 20
    assert stats["classify"].escalation_count == 15
    assert stats["classify"].escalation_rate == pytest.approx(0.75)
    assert stats["classify"].dominant_final_model() == "claude-sonnet-4-6"
    assert stats["architecture"].total_calls == 1
    assert stats["architecture"].escalation_count == 0


def test_analyze_empty_log(tmp_path: Path):
    stats = analyze(tmp_path / "missing.jsonl")
    assert stats == {}


# ---------- suggest_overrides ----------

def test_suggests_when_escalation_rate_high(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    # 25 calls, 20 escalated to Sonnet -> 80% escalation rate.
    _seed_classify_log(p, n_haiku=5, n_escalated_to_sonnet=20)
    cfg = RouteConfig.from_dict(DEFAULT_RULES)
    sugs = suggest_overrides(config=cfg, log_path=p, min_samples=20)
    assert len(sugs) == 1
    s = sugs[0]
    assert s.task == "classify"
    assert s.current_model == "claude-haiku-4-5"
    assert s.suggested_model == "claude-sonnet-4-6"
    assert s.samples == 25
    assert s.escalation_rate == pytest.approx(0.80)


def test_no_suggestion_below_min_samples(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    _seed_classify_log(p, n_haiku=1, n_escalated_to_sonnet=4)  # 5 total
    sugs = suggest_overrides(log_path=p, min_samples=20)
    assert sugs == []


def test_no_suggestion_below_threshold(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    _seed_classify_log(p, n_haiku=18, n_escalated_to_sonnet=2)  # 10% escalation
    sugs = suggest_overrides(log_path=p, min_samples=20, escalation_threshold=0.5)
    assert sugs == []


def test_no_suggestion_when_already_at_dominant_tier(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    # Even if escalation rate is high, if dominant final model == current rule, skip.
    for _ in range(25):
        log_call(
            task="classify", model="claude-haiku-4-5",
            input_tokens=10, output_tokens=10, cost_usd=0.0001,
            confidence=0.9, escalations=1, attempts=2, path=p,
        )
    sugs = suggest_overrides(log_path=p, min_samples=20)
    # Current is haiku, dominant is haiku -> nothing to do.
    assert sugs == []


def test_threshold_gates_suggestion(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    # 8 haiku-success + 14 escalated-to-sonnet -> 22 calls, ~64% rate, sonnet dominant.
    _seed_classify_log(p, n_haiku=8, n_escalated_to_sonnet=14)
    # High threshold blocks.
    assert suggest_overrides(log_path=p, min_samples=20, escalation_threshold=0.7) == []
    # Lower threshold surfaces it.
    sugs = suggest_overrides(log_path=p, min_samples=20, escalation_threshold=0.5)
    assert len(sugs) == 1
    assert sugs[0].suggested_model == "claude-sonnet-4-6"


# ---------- apply_suggestions ----------

def test_apply_suggestions_writes_config(tmp_path: Path):
    cfg_path = tmp_path / "route.json"
    sugs = [
        Suggestion(
            task="classify",
            current_model="claude-haiku-4-5",
            suggested_model="claude-sonnet-4-6",
            samples=25, escalation_rate=0.8,
            reason="seed",
        ),
    ]
    apply_suggestions(sugs, config_path=cfg_path)
    assert cfg_path.exists()
    with cfg_path.open() as f:
        data = json.load(f)
    assert data["rules"]["classify"] == "claude-sonnet-4-6"
    # Other defaults preserved.
    assert "architecture" in data["rules"]


def test_apply_suggestions_merges_into_existing_config(tmp_path: Path):
    cfg_path = tmp_path / "route.json"
    cfg_path.write_text(json.dumps({
        "rules": {"classify": "claude-haiku-4-5", "custom_task": "gpt-4o-mini"},
        "budget": {"tokens": 1000},
    }))
    sugs = [Suggestion("classify", "claude-haiku-4-5", "claude-sonnet-4-6", 30, 0.9, "x")]
    apply_suggestions(sugs, config_path=cfg_path)
    with cfg_path.open() as f:
        data = json.load(f)
    assert data["rules"]["classify"] == "claude-sonnet-4-6"
    # User customizations preserved.
    assert data["rules"]["custom_task"] == "gpt-4o-mini"
    assert data["budget"]["tokens"] == 1000


def test_apply_handles_corrupt_config(tmp_path: Path):
    cfg_path = tmp_path / "broken.json"
    cfg_path.write_text("{broken")
    sugs = [Suggestion("classify", "claude-haiku-4-5", "claude-sonnet-4-6", 30, 0.9, "x")]
    apply_suggestions(sugs, config_path=cfg_path)
    with cfg_path.open() as f:
        data = json.load(f)
    # Falls back to defaults + applies suggestion.
    assert data["rules"]["classify"] == "claude-sonnet-4-6"


# ---------- render ----------

def test_render_no_suggestions():
    out = render_suggestions([])
    assert "No suggestions" in out


def test_render_suggestions_smoke():
    sugs = [Suggestion("classify", "claude-haiku-4-5", "claude-sonnet-4-6",
                       25, 0.8, "seed reason")]
    out = render_suggestions(sugs)
    assert "classify" in out
    assert "claude-haiku-4-5 -> claude-sonnet-4-6" in out
    assert "samples=25" in out
    assert "80.0%" in out
