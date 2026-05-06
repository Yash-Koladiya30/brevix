"""Budget tracker — enforces token + cost limits, persists to ~/.brevix/budget.json."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


BUDGET_FILE = Path.home() / ".brevix" / "budget.json"


class BudgetExceededError(Exception):
    pass


@dataclass
class BudgetState:
    tokens_used: int = 0
    cost_used_usd: float = 0.0
    limit_tokens: int = 0          # 0 = unlimited
    limit_cost_usd: float = 0.0    # 0 = unlimited
    calls: int = 0


class BudgetTracker:
    """Tracks running token + cost spend; raises BudgetExceededError before overshooting."""

    def __init__(
        self,
        limit_tokens: int = 0,
        limit_cost_usd: float = 0.0,
        path: Path = BUDGET_FILE,
    ) -> None:
        self.path = Path(path)
        self.state = self._load()
        if limit_tokens:
            self.state.limit_tokens = limit_tokens
        if limit_cost_usd:
            self.state.limit_cost_usd = limit_cost_usd

    def _load(self) -> BudgetState:
        if not self.path.exists():
            return BudgetState()
        try:
            with self.path.open("r") as f:
                return BudgetState(**json.load(f))
        except (json.JSONDecodeError, OSError, TypeError):
            return BudgetState()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w") as f:
            json.dump(asdict(self.state), f, indent=2)

    def check(
        self,
        est_input_tokens: int = 0,
        est_output_tokens: int = 0,
        est_cost: float = 0.0,
    ) -> None:
        """Raise BudgetExceededError if a projected call would push over limit."""
        if self.state.limit_tokens > 0:
            projected = self.state.tokens_used + est_input_tokens + est_output_tokens
            if projected > self.state.limit_tokens:
                raise BudgetExceededError(
                    f"Token budget would exceed: {projected:,} / {self.state.limit_tokens:,}"
                )
        if self.state.limit_cost_usd > 0:
            projected = self.state.cost_used_usd + est_cost
            if projected > self.state.limit_cost_usd:
                raise BudgetExceededError(
                    f"Cost budget would exceed: ${projected:.4f} / ${self.state.limit_cost_usd:.4f}"
                )

    def record(self, input_tokens: int, output_tokens: int, cost_usd: float) -> None:
        self.state.tokens_used += input_tokens + output_tokens
        self.state.cost_used_usd += cost_usd
        self.state.calls += 1
        self._save()

    def reset(self) -> None:
        self.state = BudgetState(
            limit_tokens=self.state.limit_tokens,
            limit_cost_usd=self.state.limit_cost_usd,
        )
        self._save()

    def summary(self) -> str:
        s = self.state
        lines = ["Brevix Budget", "-------------"]
        if s.limit_tokens > 0:
            pct = s.tokens_used / s.limit_tokens * 100
            lines.append(f"Tokens used: {s.tokens_used:,} / {s.limit_tokens:,} ({pct:.1f}%)")
        else:
            lines.append(f"Tokens used: {s.tokens_used:,} (unlimited)")
        if s.limit_cost_usd > 0:
            pct = s.cost_used_usd / s.limit_cost_usd * 100
            lines.append(f"Cost used:   ${s.cost_used_usd:.4f} / ${s.limit_cost_usd:.2f} ({pct:.1f}%)")
        else:
            lines.append(f"Cost used:   ${s.cost_used_usd:.4f} (unlimited)")
        lines.append(f"Calls:       {s.calls}")
        return "\n".join(lines)
