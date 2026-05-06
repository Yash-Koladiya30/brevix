"""Main Router — picks model per prompt + enforces budget.

Phase 1: static rule + budget. Confidence-driven escalation lands in Phase 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from brevix.route.budget import BudgetTracker
from brevix.route.classifier import classify
from brevix.route.pricing import estimate_tokens, price
from brevix.route.rules import RouteConfig, load_config


@dataclass
class RoutingDecision:
    task: str
    model: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    reason: str
    escalation_chain: List[str] = field(default_factory=list)


class Router:
    """Pick the cheapest model that fits the task; track budget."""

    def __init__(
        self,
        config: Optional[RouteConfig] = None,
        budget: Optional[BudgetTracker] = None,
    ) -> None:
        self.config = config or load_config()
        if budget is None:
            self.budget = BudgetTracker(
                limit_tokens=int(self.config.budget.get("tokens", 0) or 0),
                limit_cost_usd=float(self.config.budget.get("cost_usd", 0.0) or 0.0),
            )
        else:
            self.budget = budget

    def route(
        self,
        prompt: str,
        est_input_tokens: Optional[int] = None,
        est_output_tokens: Optional[int] = None,
        override_model: Optional[str] = None,
    ) -> RoutingDecision:
        in_tok = est_input_tokens if est_input_tokens is not None else estimate_tokens(prompt)
        out_tok = est_output_tokens if est_output_tokens is not None else in_tok

        if override_model:
            task = "override"
            model = override_model
            reason = f"manual override -> {model}"
        else:
            task = classify(prompt)
            model = self.config.model_for(task)
            reason = f"task={task} -> {model} (rule match)"

        est_cost = price(model, in_tok, out_tok)
        self.budget.check(in_tok, out_tok, est_cost)

        return RoutingDecision(
            task=task,
            model=model,
            estimated_input_tokens=in_tok,
            estimated_output_tokens=out_tok,
            estimated_cost_usd=est_cost,
            reason=reason,
            escalation_chain=list(self.config.escalation_chain),
        )

    def record(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Record actual token usage post-call. Returns the cost recorded."""
        cost = price(model, input_tokens, output_tokens)
        self.budget.record(input_tokens, output_tokens, cost)
        return cost

    def next_tier(self, current_model: str) -> Optional[str]:
        """Return the next model up in the escalation chain, or None if at top."""
        chain = self.config.escalation_chain
        if current_model not in chain:
            return chain[-1] if chain else None
        idx = chain.index(current_model)
        if idx + 1 < len(chain):
            return chain[idx + 1]
        return None
