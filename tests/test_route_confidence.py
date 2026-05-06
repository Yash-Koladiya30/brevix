"""Tests for brevix.route.confidence + escalation loop in RoutedClient (Phase 3)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

from brevix.route import (
    BudgetExceededError,
    BudgetTracker,
    DEFAULT_RULES,
    Provider,
    RouteConfig,
    RoutedClient,
    Router,
    ScorerWeights,
    hedge_score,
    length_score,
    score_response,
    validity_score,
)


# ---------- scorer unit tests ----------

def test_hedge_score_no_hedges():
    assert hedge_score("The answer is 42.") == pytest.approx(1.0)


def test_hedge_score_lots_of_hedges():
    text = "I think maybe perhaps I don't know it could be unclear"
    assert hedge_score(text) < 0.4


def test_hedge_score_empty_neutral():
    assert hedge_score("") == 0.5


def test_validity_parses_json():
    assert validity_score('{"x": 1}', "parse_json") == 1.0
    assert validity_score("```json\n{\"x\": 1}\n```", "parse_json") == 1.0


def test_validity_rejects_bad_json():
    assert validity_score("not even close", "parse_json") == 0.2


def test_validity_classify_short_answer():
    assert validity_score("positive", "classify") == 1.0


def test_validity_classify_long_answer_penalized():
    long_answer = " ".join(["word"] * 30)
    assert validity_score(long_answer, "classify") == 0.4


def test_validity_returns_none_for_unmapped_task():
    assert validity_score("anything", "general") is None


def test_length_score_empty_zero():
    assert length_score("", "general") == 0.0


def test_length_score_short_low():
    assert length_score("ok", "general") == 0.2


def test_length_score_medium_high():
    assert length_score("a" * 200, "general") == 1.0


# ---------- aggregator ----------

def test_score_response_all_signals():
    res = score_response(
        prompt="Classify this ticket",
        response_text="positive",
        task="classify",
    )
    assert 0.0 <= res.score <= 1.0
    assert len(res.breakdown) >= 2


def test_score_response_drops_inapplicable_validity():
    res = score_response(
        prompt="Explain async/await",
        response_text="Async/await schedules a coroutine on the event loop and resumes it on completion. " * 3,
        task="explain",
    )
    names = {b.name for b in res.breakdown}
    # validity is None for "explain", should not appear in breakdown
    assert "validity" not in names


def test_score_response_high_for_clean_answer():
    text = "The user count is 42. Confirmed via SQL: SELECT COUNT(*) FROM users."
    res = score_response("How many users?", text, task="explain")
    assert res.score > 0.7


def test_score_response_low_for_hedged_answer():
    text = "I'm not sure, maybe it could be 42 perhaps. I don't know really."
    res = score_response("How many users?", text, task="explain")
    assert res.score < 0.7


def test_score_response_neutral_when_no_weights():
    weights = ScorerWeights(hedge=0, validity=0, length=0)
    res = score_response("anything", "anything", task="explain", weights=weights)
    assert res.score == 0.5


# ---------- escalation loop ----------

class ScriptedProvider(Provider):
    """Returns a different response per model id, so we can test escalation."""

    def __init__(self, name: str = "anthropic", responses: Optional[Dict[str, str]] = None) -> None:
        self.name = name
        self.responses = responses or {}
        self.calls: List[Dict[str, Any]] = []

    def call(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Tuple[str, int, int, Any]:
        self.calls.append({"model": model, "messages": messages})
        text = self.responses.get(model, "ok")
        # Cheap fixed token counts so cost math is predictable.
        return text, 100, 100, {"fake": True, "model": model}


def _client_with_scripts(tmp_path: Path, responses: Dict[str, str]) -> Tuple[RoutedClient, ScriptedProvider]:
    cfg = RouteConfig.from_dict(DEFAULT_RULES)
    budget = BudgetTracker(path=tmp_path / "budget.json")
    router = Router(config=cfg, budget=budget)
    fake = ScriptedProvider(responses=responses)
    client = RoutedClient(router=router, providers={"anthropic": fake, "openai": fake})
    return client, fake


def test_no_escalation_when_confidence_check_disabled(tmp_path):
    # Even with bad first response, confidence_check=False should single-call.
    client, fake = _client_with_scripts(tmp_path, {
        "claude-haiku-4-5": "I don't know, maybe perhaps unclear",
    })
    result = client.call("Classify this ticket", confidence_check=False)
    assert result.escalations == 0
    assert len(fake.calls) == 1
    assert result.confidence == 1.0  # disabled => sentinel value


def test_escalates_on_low_confidence(tmp_path):
    # Haiku gives a hedge-laden answer -> low conf -> escalate to Sonnet -> clean answer.
    client, fake = _client_with_scripts(tmp_path, {
        "claude-haiku-4-5": "I don't know maybe perhaps I'm not sure unclear",
        "claude-sonnet-4-6": "positive",
    })
    result = client.call("Classify this ticket", confidence_check=True)
    assert result.escalations >= 1
    assert "sonnet" in result.model.lower() or "opus" in result.model.lower()
    # Both attempts should be recorded.
    assert len(result.attempts) >= 2


def test_no_escalation_when_first_call_confident(tmp_path):
    client, fake = _client_with_scripts(tmp_path, {
        "claude-haiku-4-5": "positive",
    })
    result = client.call("Classify this ticket", confidence_check=True)
    assert result.escalations == 0
    assert len(fake.calls) == 1
    assert result.model == "claude-haiku-4-5"


def test_max_escalations_respected(tmp_path):
    # All tiers return bad answers; escalation must cap at max_escalations.
    bad = "I don't know maybe perhaps unclear I'm not sure"
    cfg_dict = dict(DEFAULT_RULES)
    cfg = RouteConfig.from_dict({**cfg_dict, "confidence": {**cfg_dict["confidence"], "max_escalations": 1}})
    budget = BudgetTracker(path=tmp_path / "budget.json")
    router = Router(config=cfg, budget=budget)
    fake = ScriptedProvider(responses={
        "claude-haiku-4-5": bad,
        "claude-sonnet-4-6": bad,
        "claude-opus-4-7": bad,
    })
    client = RoutedClient(router=router, providers={"anthropic": fake, "openai": fake})
    result = client.call("Classify this", confidence_check=True)
    # max_escalations=1 -> 2 attempts total max.
    assert result.escalations <= 1
    assert len(result.attempts) <= 2


def test_escalation_records_each_attempt_to_budget(tmp_path):
    bad = "I don't know perhaps maybe unclear"
    client, fake = _client_with_scripts(tmp_path, {
        "claude-haiku-4-5": bad,
        "claude-sonnet-4-6": bad,
        "claude-opus-4-7": "fine answer",
    })
    result = client.call("Classify this ticket", confidence_check=True)
    # Each attempt charges the budget.
    assert client.router.budget.state.calls == len(result.attempts)
    # Tokens logged = sum of all attempts.
    expected_tokens = sum(a.input_tokens + a.output_tokens for a in result.attempts)
    assert client.router.budget.state.tokens_used == expected_tokens


def test_escalation_blocked_by_budget(tmp_path):
    # Prompt routes to Haiku (cheap). First attempt fits the budget;
    # escalation to Sonnet should bust it.
    cfg = RouteConfig.from_dict(DEFAULT_RULES)
    budget = BudgetTracker(limit_cost_usd=0.0008, path=tmp_path / "budget.json")
    router = Router(config=cfg, budget=budget)
    bad = "I don't know perhaps maybe unclear I'm not sure can't tell"
    fake = ScriptedProvider(responses={
        "claude-haiku-4-5": bad,
        "claude-sonnet-4-6": bad,
        "claude-opus-4-7": bad,
    })
    client = RoutedClient(router=router, providers={"anthropic": fake, "openai": fake})
    with pytest.raises(BudgetExceededError):
        client.call("Classify this ticket", confidence_check=True)
