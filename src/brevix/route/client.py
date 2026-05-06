"""Routed client — wraps LLM SDK calls, picks model via Router, records to budget.

SDKs (anthropic, openai) are imported only inside provider methods so the CLI
cold-start path stays sub-100ms for users who never invoke a real call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from brevix.route.confidence import ScorerWeights, score_response
from brevix.route.route_stats import LOG_FILE, log_call
from brevix.route.router import Router


# Mapping rules for known model name prefixes -> provider key.
# Order matters: longest prefix first.
_PROVIDER_PREFIXES: List[Tuple[str, str]] = [
    ("claude-", "anthropic"),
    ("gpt-", "openai"),
    ("o1-", "openai"),
    ("o3-", "openai"),
    ("gemini-", "google"),
]


@dataclass
class Attempt:
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    confidence: float
    text: str = ""


@dataclass
class CallResult:
    text: str
    model: str
    task: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    confidence: float = 0.0
    escalations: int = 0
    attempts: List[Attempt] = field(default_factory=list)
    raw: Any = None


class Provider:
    """Provider base class. Subclasses implement .call()."""

    name: str = "abstract"

    def call(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Tuple[str, int, int, Any]:
        raise NotImplementedError


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key
        self._client: Any = None

    def _ensure(self) -> Any:
        if self._client is None:
            import anthropic  # lazy: heavy SDK
            kwargs = {"api_key": self._api_key} if self._api_key else {}
            self._client = anthropic.Anthropic(**kwargs)
        return self._client

    def call(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Tuple[str, int, int, Any]:
        client = self._ensure()
        if system:
            kwargs.setdefault("system", system)
        resp = client.messages.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            **kwargs,
        )
        text = "".join(getattr(block, "text", "") for block in resp.content)
        return text, resp.usage.input_tokens, resp.usage.output_tokens, resp


class OpenAIProvider(Provider):
    name = "openai"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key
        self._client: Any = None

    def _ensure(self) -> Any:
        if self._client is None:
            import openai  # lazy
            kwargs = {"api_key": self._api_key} if self._api_key else {}
            self._client = openai.OpenAI(**kwargs)
        return self._client

    def call(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Tuple[str, int, int, Any]:
        client = self._ensure()
        if system:
            messages = [{"role": "system", "content": system}, *messages]
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            **kwargs,
        )
        text = resp.choices[0].message.content or ""
        return text, resp.usage.prompt_tokens, resp.usage.completion_tokens, resp


def detect_provider(model: str) -> str:
    """Return the provider key for a model id."""
    m = model.lower()
    for prefix, name in _PROVIDER_PREFIXES:
        if m.startswith(prefix):
            return name
    return "anthropic"  # safe default


class RoutedClient:
    """Picks model + provider, calls it, records spend.

    Pass `providers={"anthropic": MyFake()}` in tests to skip real SDKs.
    """

    def __init__(
        self,
        router: Optional[Router] = None,
        providers: Optional[Dict[str, Provider]] = None,
        log_enabled: bool = False,
        log_path: Optional[Path] = None,
    ) -> None:
        self.router = router or Router()
        self.providers: Dict[str, Provider] = providers or {}
        self.log_enabled = log_enabled
        self.log_path: Path = Path(log_path) if log_path else LOG_FILE

    def _provider_for(self, model: str) -> Provider:
        name = detect_provider(model)
        if name not in self.providers:
            if name == "anthropic":
                self.providers[name] = AnthropicProvider()
            elif name == "openai":
                self.providers[name] = OpenAIProvider()
            else:
                raise ValueError(f"No provider configured for '{name}' (model={model})")
        return self.providers[name]

    def _invoke(
        self,
        model: str,
        prompt: str,
        max_tokens: int,
        system: Optional[str],
        **kwargs: Any,
    ) -> Tuple[str, int, int, Any, float]:
        from brevix.route.pricing import estimate_tokens, price as model_price
        # Pre-flight budget check for this attempt (Router.route() did this for
        # the first call only; escalation retries need their own check).
        in_est = estimate_tokens(prompt)
        cost_est = model_price(model, in_est, in_est)
        self.router.budget.check(in_est, in_est, cost_est)

        provider = self._provider_for(model)
        messages = [{"role": "user", "content": prompt}]
        text, in_tok, out_tok, raw = provider.call(
            model, messages, max_tokens=max_tokens, system=system, **kwargs
        )
        cost = self.router.record(model, in_tok, out_tok)
        return text, in_tok, out_tok, raw, cost

    def call(
        self,
        prompt: str,
        max_tokens: int = 2000,
        override_model: Optional[str] = None,
        system: Optional[str] = None,
        confidence_check: bool = False,
        weights: Optional[ScorerWeights] = None,
        **kwargs: Any,
    ) -> CallResult:
        """Route, call, and (optionally) escalate based on confidence.

        confidence_check=False -> single call, no scoring.
        confidence_check=True  -> score response; if below the model's threshold,
                                  retry on the next tier (capped by max_escalations).
        """
        decision = self.router.route(prompt, override_model=override_model)
        task = decision.task
        thresholds: Dict[str, float] = self.router.config.confidence.get("thresholds", {})
        max_esc: int = int(self.router.config.confidence.get("max_escalations", 2) or 0)

        attempts: List[Attempt] = []
        current_model = decision.model
        last_text = ""
        last_in = last_out = 0
        last_cost = 0.0
        last_raw: Any = None
        last_conf = 0.0
        escalations = 0

        while True:
            text, in_tok, out_tok, raw, cost = self._invoke(
                current_model, prompt, max_tokens, system, **kwargs
            )
            last_text, last_in, last_out, last_cost, last_raw = text, in_tok, out_tok, cost, raw

            if confidence_check:
                conf_result = score_response(prompt, text, task, weights=weights)
                last_conf = conf_result.score
            else:
                last_conf = 1.0  # disabled -> always emit first attempt

            attempts.append(Attempt(
                model=current_model,
                input_tokens=in_tok,
                output_tokens=out_tok,
                cost_usd=cost,
                confidence=last_conf,
                text=text,
            ))

            if not confidence_check:
                break

            threshold = float(thresholds.get(current_model, 0.0))
            if last_conf >= threshold:
                break
            if escalations >= max_esc:
                break
            next_model = self.router.next_tier(current_model)
            if not next_model or next_model == current_model:
                break

            current_model = next_model
            escalations += 1

        result = CallResult(
            text=last_text,
            model=current_model,
            task=task,
            input_tokens=last_in,
            output_tokens=last_out,
            cost_usd=last_cost,
            confidence=last_conf,
            escalations=escalations,
            attempts=attempts,
            raw=last_raw,
        )

        if self.log_enabled:
            try:
                log_call(
                    task=result.task,
                    model=result.model,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    cost_usd=result.cost_usd,
                    confidence=result.confidence,
                    escalations=result.escalations,
                    attempts=len(result.attempts),
                    path=self.log_path,
                )
            except OSError:
                # Logging must never break the call. Disk failures are silent.
                pass

        return result
