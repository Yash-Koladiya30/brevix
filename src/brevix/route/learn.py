"""Learn loop — analyze routing log, suggest rule overrides.

If a task class consistently escalates past its rule-mapped tier, the rule is
wrong. This module walks the local log and surfaces those mismatches.

Privacy: 100% local. No telemetry, no network.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from brevix.route.route_stats import LOG_FILE, read_log
from brevix.route.rules import CONFIG_FILE, DEFAULT_RULES, RouteConfig, load_config


DEFAULT_MIN_SAMPLES = 20
DEFAULT_ESCALATION_THRESHOLD = 0.5  # 50% of calls for that task


@dataclass
class TaskStats:
    task: str
    total_calls: int = 0
    escalation_count: int = 0
    final_models: Dict[str, int] = field(default_factory=dict)

    @property
    def escalation_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.escalation_count / self.total_calls

    def dominant_final_model(self) -> Optional[str]:
        if not self.final_models:
            return None
        return max(self.final_models.items(), key=lambda kv: kv[1])[0]


@dataclass
class Suggestion:
    task: str
    current_model: str
    suggested_model: str
    samples: int
    escalation_rate: float
    reason: str


def analyze(path: Path = LOG_FILE) -> Dict[str, TaskStats]:
    """Walk the routing log, gather per-task stats."""
    out: Dict[str, TaskStats] = {}
    for entry in read_log(path):
        task = entry.get("task", "unknown")
        ts = out.setdefault(task, TaskStats(task=task))
        ts.total_calls += 1
        if int(entry.get("escalations", 0)) > 0:
            ts.escalation_count += 1
        model = entry.get("model", "unknown")
        ts.final_models[model] = ts.final_models.get(model, 0) + 1
    return out


def suggest_overrides(
    config: Optional[RouteConfig] = None,
    log_path: Path = LOG_FILE,
    min_samples: int = DEFAULT_MIN_SAMPLES,
    escalation_threshold: float = DEFAULT_ESCALATION_THRESHOLD,
) -> List[Suggestion]:
    """Recommend rule changes for tasks that consistently escalate."""
    cfg = config or load_config()
    stats = analyze(log_path)
    suggestions: List[Suggestion] = []
    for task, ts in stats.items():
        if ts.total_calls < min_samples:
            continue
        if ts.escalation_rate < escalation_threshold:
            continue
        current = cfg.rules.get(task) or cfg.rules.get("general", "")
        target = ts.dominant_final_model()
        if not target or target == current:
            continue
        landed = ts.final_models.get(target, 0)
        suggestions.append(Suggestion(
            task=task,
            current_model=current,
            suggested_model=target,
            samples=ts.total_calls,
            escalation_rate=ts.escalation_rate,
            reason=(
                f"{ts.escalation_count}/{ts.total_calls} escalated "
                f"({ts.escalation_rate*100:.0f}%); {landed} of those landed on {target}"
            ),
        ))
    return suggestions


def apply_suggestions(
    suggestions: List[Suggestion],
    config_path: Path = CONFIG_FILE,
) -> Path:
    """Patch the route config with suggestions and write to disk."""
    p = Path(config_path)
    if p.exists():
        try:
            with p.open("r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = copy.deepcopy(DEFAULT_RULES)
    else:
        data = copy.deepcopy(DEFAULT_RULES)
    rules = data.setdefault("rules", {})
    for s in suggestions:
        rules[s.task] = s.suggested_model
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        json.dump(data, f, indent=2)
    return p


def render_suggestions(suggestions: List[Suggestion]) -> str:
    if not suggestions:
        return "No suggestions yet (need more data or no escalating tasks)."
    lines = [
        "Brevix Routing -- Suggested Config Changes",
        "------------------------------------------",
    ]
    for s in suggestions:
        lines.append(
            f"  {s.task}: {s.current_model} -> {s.suggested_model}"
        )
        lines.append(
            f"    samples={s.samples}  escalation_rate={s.escalation_rate*100:.1f}%"
        )
        lines.append(f"    reason: {s.reason}")
    lines.append("")
    lines.append("Apply with: brevix route --learn-apply")
    return "\n".join(lines)
