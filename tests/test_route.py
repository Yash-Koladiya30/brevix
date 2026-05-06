"""Tests for brevix.route — Phase 1 (static rules + budget)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from brevix.route import (
    BudgetExceededError,
    BudgetTracker,
    DEFAULT_RULES,
    RouteConfig,
    Router,
    classify,
    load_config,
    price,
    write_default_config,
)


# ---------- classifier ----------

def test_classify_known_tasks():
    assert classify("Classify this support ticket") == "classify"
    assert classify("Parse the JSON response from the API") == "parse_json"
    assert classify("Review my Flutter code for null safety") == "code_review"
    assert classify("Architect a multi-agent system") == "architecture"
    assert classify("Refactor this messy module") == "refactor"
    assert classify("Translate this paragraph to Spanish") == "translate"
    assert classify("Summarize the meeting notes") == "summarize"


def test_classify_general_fallback():
    assert classify("Write a haiku about kittens") == "general"
    assert classify("") == "general"


# ---------- pricing ----------

def test_pricing_known_model():
    cost = price("claude-haiku-4-5", 1_000_000, 1_000_000)
    assert cost == pytest.approx(6.00)


def test_pricing_unknown_model_returns_zero():
    assert price("totally-fake-model", 10_000, 10_000) == 0.0


def test_pricing_zero_tokens():
    assert price("claude-opus-4-7", 0, 0) == 0.0


# ---------- rules / config ----------

def test_load_config_returns_defaults_when_missing(tmp_path: Path):
    cfg = load_config(tmp_path / "missing.json")
    assert cfg.rules["classify"] == DEFAULT_RULES["rules"]["classify"]
    assert cfg.rules["architecture"] == DEFAULT_RULES["rules"]["architecture"]


def test_load_config_merges_user_overrides(tmp_path: Path):
    cfg_path = tmp_path / "route.json"
    cfg_path.write_text(json.dumps({
        "rules": {"classify": "gpt-4o-mini"}
    }))
    cfg = load_config(cfg_path)
    # override applied
    assert cfg.rules["classify"] == "gpt-4o-mini"
    # defaults still present
    assert cfg.rules["architecture"] == "claude-opus-4-7"


def test_load_config_handles_corrupt_json(tmp_path: Path):
    cfg_path = tmp_path / "broken.json"
    cfg_path.write_text("{not valid json")
    cfg = load_config(cfg_path)
    assert cfg.rules["classify"] == DEFAULT_RULES["rules"]["classify"]


def test_write_default_config(tmp_path: Path):
    p = write_default_config(tmp_path / "route.json")
    assert p.exists()
    cfg = load_config(p)
    assert cfg.rules == DEFAULT_RULES["rules"]


def test_route_config_model_for_unknown_task():
    cfg = RouteConfig.from_dict(DEFAULT_RULES)
    # unknown task falls back to general
    assert cfg.model_for("invented_task") == cfg.rules["general"]


# ---------- budget ----------

def test_budget_blocks_when_token_limit_exceeded(tmp_path: Path):
    b = BudgetTracker(limit_tokens=100, path=tmp_path / "budget.json")
    with pytest.raises(BudgetExceededError):
        b.check(est_input_tokens=200, est_output_tokens=0, est_cost=0)


def test_budget_blocks_when_cost_limit_exceeded(tmp_path: Path):
    b = BudgetTracker(limit_cost_usd=0.001, path=tmp_path / "budget.json")
    with pytest.raises(BudgetExceededError):
        b.check(est_cost=0.10)


def test_budget_unlimited_passes(tmp_path: Path):
    b = BudgetTracker(path=tmp_path / "budget.json")
    b.check(est_input_tokens=10_000_000, est_output_tokens=10_000_000, est_cost=999.99)


def test_budget_record_accumulates(tmp_path: Path):
    p = tmp_path / "budget.json"
    b = BudgetTracker(limit_tokens=1000, path=p)
    b.record(input_tokens=10, output_tokens=20, cost_usd=0.001)
    b.record(input_tokens=5, output_tokens=15, cost_usd=0.0005)
    assert b.state.tokens_used == 50
    assert b.state.cost_used_usd == pytest.approx(0.0015)
    assert b.state.calls == 2

    # Reload from disk; state persists.
    b2 = BudgetTracker(path=p)
    assert b2.state.tokens_used == 50
    assert b2.state.calls == 2


def test_budget_reset_preserves_limits(tmp_path: Path):
    b = BudgetTracker(limit_tokens=1000, limit_cost_usd=5.0, path=tmp_path / "budget.json")
    b.record(input_tokens=100, output_tokens=200, cost_usd=0.5)
    b.reset()
    assert b.state.tokens_used == 0
    assert b.state.cost_used_usd == 0.0
    assert b.state.limit_tokens == 1000
    assert b.state.limit_cost_usd == 5.0


def test_budget_summary_renders(tmp_path: Path):
    b = BudgetTracker(limit_tokens=10_000, limit_cost_usd=1.00, path=tmp_path / "budget.json")
    b.record(input_tokens=100, output_tokens=200, cost_usd=0.05)
    s = b.summary()
    assert "Tokens used" in s
    assert "Cost used" in s
    assert "Calls" in s


# ---------- router ----------

def _router_with_tmp_budget(tmp_path: Path) -> Router:
    cfg = RouteConfig.from_dict(DEFAULT_RULES)
    budget = BudgetTracker(path=tmp_path / "budget.json")
    return Router(config=cfg, budget=budget)


def test_router_picks_model_per_task(tmp_path: Path):
    r = _router_with_tmp_budget(tmp_path)
    d = r.route("Classify this incoming bug report")
    assert d.task == "classify"
    assert "haiku" in d.model.lower()


def test_router_architecture_picks_opus(tmp_path: Path):
    r = _router_with_tmp_budget(tmp_path)
    d = r.route("Architect a distributed payment system")
    assert d.task == "architecture"
    assert "opus" in d.model.lower()


def test_router_override_model(tmp_path: Path):
    r = _router_with_tmp_budget(tmp_path)
    d = r.route("anything goes", override_model="gpt-4o-mini")
    assert d.task == "override"
    assert d.model == "gpt-4o-mini"


def test_router_blocks_on_budget(tmp_path: Path):
    cfg = RouteConfig.from_dict(DEFAULT_RULES)
    budget = BudgetTracker(limit_cost_usd=0.0000001, path=tmp_path / "budget.json")
    r = Router(config=cfg, budget=budget)
    with pytest.raises(BudgetExceededError):
        r.route("Architect a distributed payment system" * 100)


def test_router_record_updates_budget(tmp_path: Path):
    r = _router_with_tmp_budget(tmp_path)
    r.record("claude-haiku-4-5", input_tokens=1000, output_tokens=500)
    assert r.budget.state.tokens_used == 1500
    assert r.budget.state.calls == 1


def test_router_next_tier(tmp_path: Path):
    r = _router_with_tmp_budget(tmp_path)
    assert r.next_tier("claude-haiku-4-5") == "claude-sonnet-4-6"
    assert r.next_tier("claude-sonnet-4-6") == "claude-opus-4-7"
    assert r.next_tier("claude-opus-4-7") is None
    # Unknown model jumps to top tier as a safe fallback.
    assert r.next_tier("unknown-model") == "claude-opus-4-7"


def test_routing_decision_estimates_cost(tmp_path: Path):
    r = _router_with_tmp_budget(tmp_path)
    d = r.route("Classify this", est_input_tokens=1000, est_output_tokens=1000)
    expected = price(d.model, 1000, 1000)
    assert d.estimated_cost_usd == pytest.approx(expected)
