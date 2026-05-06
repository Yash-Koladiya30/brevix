"""Tests for brevix.route.client — Phase 2 (SDK wrapper).

Uses a FakeProvider so tests run without anthropic/openai installed
and without network access.
"""

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
    detect_provider,
)


class FakeProvider(Provider):
    """Records calls and returns canned response. No network."""

    def __init__(self, name: str = "anthropic", text: str = "ok",
                 input_tokens: int = 100, output_tokens: int = 50) -> None:
        self.name = name
        self._text = text
        self._in = input_tokens
        self._out = output_tokens
        self.calls: List[Dict[str, Any]] = []

    def call(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Tuple[str, int, int, Any]:
        self.calls.append({
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "system": system,
            "kwargs": kwargs,
        })
        return self._text, self._in, self._out, {"fake": True}


def _client_with_fake(tmp_path: Path, text: str = "ok",
                       in_tok: int = 100, out_tok: int = 50) -> tuple[RoutedClient, FakeProvider]:
    cfg = RouteConfig.from_dict(DEFAULT_RULES)
    budget = BudgetTracker(path=tmp_path / "budget.json")
    router = Router(config=cfg, budget=budget)
    fake = FakeProvider(text=text, input_tokens=in_tok, output_tokens=out_tok)
    client = RoutedClient(router=router, providers={"anthropic": fake, "openai": fake})
    return client, fake


# ---------- detect_provider ----------

def test_detect_provider_anthropic():
    assert detect_provider("claude-haiku-4-5") == "anthropic"
    assert detect_provider("claude-opus-4-7") == "anthropic"


def test_detect_provider_openai():
    assert detect_provider("gpt-4o-mini") == "openai"
    assert detect_provider("gpt-4o") == "openai"
    assert detect_provider("o1-preview") == "openai"


def test_detect_provider_google():
    assert detect_provider("gemini-1.5-flash") == "google"


def test_detect_provider_unknown_falls_back_to_anthropic():
    assert detect_provider("totally-fake-model") == "anthropic"


# ---------- RoutedClient ----------

def test_routed_client_picks_model_and_calls(tmp_path):
    client, fake = _client_with_fake(tmp_path, text="hello world", in_tok=10, out_tok=5)
    result = client.call("Classify this support ticket")
    assert result.text == "hello world"
    assert "haiku" in result.model.lower()
    assert result.task == "classify"
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.cost_usd > 0
    assert len(fake.calls) == 1
    assert fake.calls[0]["model"] == result.model


def test_routed_client_records_to_budget(tmp_path):
    client, _ = _client_with_fake(tmp_path, in_tok=100, out_tok=200)
    client.call("Architect a multi-agent system")
    assert client.router.budget.state.tokens_used == 300
    assert client.router.budget.state.calls == 1
    assert client.router.budget.state.cost_used_usd > 0


def test_routed_client_override_model_selects_provider(tmp_path):
    client, fake = _client_with_fake(tmp_path)
    result = client.call("anything", override_model="gpt-4o-mini")
    assert result.model == "gpt-4o-mini"
    assert fake.calls[0]["model"] == "gpt-4o-mini"


def test_routed_client_passes_system_prompt(tmp_path):
    client, fake = _client_with_fake(tmp_path)
    client.call("hi", system="You are a strict reviewer")
    assert fake.calls[0]["system"] == "You are a strict reviewer"


def test_routed_client_blocks_on_pre_call_budget(tmp_path):
    cfg = RouteConfig.from_dict(DEFAULT_RULES)
    budget = BudgetTracker(limit_cost_usd=0.0000001, path=tmp_path / "budget.json")
    router = Router(config=cfg, budget=budget)
    fake = FakeProvider()
    client = RoutedClient(router=router, providers={"anthropic": fake, "openai": fake})
    with pytest.raises(BudgetExceededError):
        client.call("Architect a vast distributed system " * 50)
    # Provider never called when budget blocks.
    assert fake.calls == []


def test_routed_client_passes_max_tokens_kwarg(tmp_path):
    client, fake = _client_with_fake(tmp_path)
    client.call("hi", max_tokens=512)
    assert fake.calls[0]["max_tokens"] == 512


def test_routed_client_unknown_provider_raises(tmp_path):
    cfg = RouteConfig.from_dict(DEFAULT_RULES)
    budget = BudgetTracker(path=tmp_path / "budget.json")
    router = Router(config=cfg, budget=budget)
    client = RoutedClient(router=router, providers={})  # no providers seeded
    with pytest.raises(ValueError):
        client.call("hi", override_model="gemini-1.5-flash")


# ---------- lazy import discipline ----------

def test_module_import_does_not_pull_sdk_libs():
    """Cold-importing brevix.route.client must not transitively load anthropic/openai.

    These SDKs are heavy (hundreds of ms each). The lazy-import contract is
    that the wrapper only loads them when call() runs.
    """
    import sys
    # Drop anything we might have already loaded so this test is real.
    for mod in list(sys.modules):
        if mod.startswith(("anthropic", "openai")):
            del sys.modules[mod]
    # Re-import the route.client module fresh.
    if "brevix.route.client" in sys.modules:
        del sys.modules["brevix.route.client"]
    import brevix.route.client  # noqa: F401
    assert "anthropic" not in sys.modules
    assert "openai" not in sys.modules
