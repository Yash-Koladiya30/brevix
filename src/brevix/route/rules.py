"""Rules config loader — JSON at ~/.brevix/route.json (no extra deps)."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


CONFIG_DIR = Path.home() / ".brevix"
CONFIG_FILE = CONFIG_DIR / "route.json"


DEFAULT_RULES: Dict[str, Any] = {
    "rules": {
        "classify": "claude-haiku-4-5",
        "parse_json": "claude-haiku-4-5",
        "extract": "claude-haiku-4-5",
        "format": "claude-haiku-4-5",
        "rename": "claude-haiku-4-5",
        "translate": "claude-haiku-4-5",
        "summarize": "claude-haiku-4-5",
        "write_reply": "claude-sonnet-4-6",
        "code_review": "claude-sonnet-4-6",
        "debug": "claude-sonnet-4-6",
        "refactor": "claude-sonnet-4-6",
        "explain": "claude-sonnet-4-6",
        "architecture": "claude-opus-4-7",
        "general": "claude-haiku-4-5",
    },
    "escalation_chain": [
        "claude-haiku-4-5",
        "claude-sonnet-4-6",
        "claude-opus-4-7",
    ],
    "budget": {
        "tokens": 0,
        "cost_usd": 0.0,
    },
    "confidence": {
        "thresholds": {
            "claude-haiku-4-5": 0.75,
            "claude-sonnet-4-6": 0.60,
            "claude-opus-4-7": 0.0,
        },
        "max_escalations": 2,
    },
}


@dataclass
class RouteConfig:
    rules: Dict[str, str] = field(default_factory=dict)
    escalation_chain: List[str] = field(default_factory=list)
    budget: Dict[str, Any] = field(default_factory=dict)
    confidence: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RouteConfig":
        defaults = copy.deepcopy(DEFAULT_RULES)
        return cls(
            rules={**defaults["rules"], **d.get("rules", {})},
            escalation_chain=d.get("escalation_chain", defaults["escalation_chain"]),
            budget={**defaults["budget"], **d.get("budget", {})},
            confidence={**defaults["confidence"], **d.get("confidence", {})},
        )

    def model_for(self, task: str) -> str:
        return self.rules.get(task) or self.rules.get("general", "claude-haiku-4-5")


def load_config(path: Path = CONFIG_FILE) -> RouteConfig:
    p = Path(path)
    if not p.exists():
        return RouteConfig.from_dict(copy.deepcopy(DEFAULT_RULES))
    try:
        with p.open("r") as f:
            data = json.load(f)
        return RouteConfig.from_dict(data)
    except (json.JSONDecodeError, OSError):
        return RouteConfig.from_dict(copy.deepcopy(DEFAULT_RULES))


def write_default_config(path: Path = CONFIG_FILE) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        json.dump(DEFAULT_RULES, f, indent=2)
    return p
