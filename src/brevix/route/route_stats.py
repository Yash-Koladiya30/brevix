"""Routing stats — append-only JSONL log + summary aggregator.

Why JSONL: appends are O(1) and tolerant to crashes; only `summarize()` reads
the full file, and that's a one-shot for `brevix stats --routing`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from brevix.route.pricing import price as model_price


LOG_FILE = Path.home() / ".brevix" / "routing_log.jsonl"
OPUS_BASELINE_MODEL = "claude-opus-4-7"


def _parse_since(since: str) -> Optional[datetime]:
    """Parse '7d', '24h', '30m', 'all'. Returns cutoff datetime or None for all."""
    if not since or since == "all":
        return None
    units = {"d": "days", "h": "hours", "m": "minutes", "s": "seconds"}
    suffix = since[-1]
    if suffix not in units:
        raise ValueError(f"Invalid 'since' value: {since}")
    try:
        n = int(since[:-1])
    except ValueError as exc:
        raise ValueError(f"Invalid 'since' value: {since}") from exc
    return datetime.now(timezone.utc) - timedelta(**{units[suffix]: n})


def log_call(
    *,
    task: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    confidence: float,
    escalations: int,
    attempts: int,
    path: Path = LOG_FILE,
) -> None:
    """Append one routing call to the JSONL log. No read."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "task": task,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "confidence": confidence,
        "escalations": escalations,
        "attempts": attempts,
    }
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def read_log(path: Path = LOG_FILE) -> Iterator[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return
    with p.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


@dataclass
class RoutingSummary:
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    baseline_cost_usd: float = 0.0     # cost if every call had used Opus
    escalation_count: int = 0
    by_model: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    by_task: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @property
    def saved_usd(self) -> float:
        return max(0.0, self.baseline_cost_usd - self.total_cost_usd)

    @property
    def saved_pct(self) -> float:
        if self.baseline_cost_usd <= 0:
            return 0.0
        return self.saved_usd / self.baseline_cost_usd * 100

    @property
    def escalation_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.escalation_count / self.total_calls * 100


def summarize(since: str = "all", path: Path = LOG_FILE) -> RoutingSummary:
    cutoff = _parse_since(since)
    s = RoutingSummary()
    for entry in read_log(path):
        ts_str = entry.get("ts", "")
        if cutoff and ts_str:
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts < cutoff:
                    continue
            except ValueError:
                continue

        in_tok = int(entry.get("input_tokens", 0))
        out_tok = int(entry.get("output_tokens", 0))
        cost = float(entry.get("cost_usd", 0.0))
        model = entry.get("model", "unknown")
        task = entry.get("task", "unknown")

        s.total_calls += 1
        s.total_input_tokens += in_tok
        s.total_output_tokens += out_tok
        s.total_cost_usd += cost
        s.baseline_cost_usd += model_price(OPUS_BASELINE_MODEL, in_tok, out_tok)
        s.escalation_count += int(entry.get("escalations", 0))

        m = s.by_model.setdefault(model, {"calls": 0, "cost": 0.0, "tokens": 0})
        m["calls"] += 1
        m["cost"] += cost
        m["tokens"] += in_tok + out_tok

        t = s.by_task.setdefault(task, {"calls": 0, "cost": 0.0})
        t["calls"] += 1
        t["cost"] += cost
    return s


def render_summary(summary: RoutingSummary, since: str = "all") -> str:
    lines = ["Brevix Routing Stats", "--------------------"]
    lines.append(f"Window:             {since}")
    lines.append(f"Calls:              {summary.total_calls}")
    if summary.total_calls == 0:
        lines.append("(no routing calls logged yet)")
        return "\n".join(lines)
    lines.append(
        f"Tokens:             {summary.total_input_tokens:,} in / "
        f"{summary.total_output_tokens:,} out"
    )
    lines.append(f"Total cost:         ${summary.total_cost_usd:.4f}")
    lines.append(f"Opus-only baseline: ${summary.baseline_cost_usd:.4f}")
    lines.append(f"Saved:              ${summary.saved_usd:.4f} ({summary.saved_pct:.1f}%)")
    lines.append(
        f"Escalations:        {summary.escalation_count} "
        f"({summary.escalation_rate:.1f}% of calls)"
    )
    lines.append("")
    lines.append("By model:")
    for model, info in sorted(summary.by_model.items(), key=lambda x: -x[1]["cost"]):
        share = info["calls"] / summary.total_calls * 100
        lines.append(
            f"  {model:30s} {info['calls']:5d} ({share:5.1f}%)  ${info['cost']:.4f}"
        )
    lines.append("")
    lines.append("By task:")
    for task, info in sorted(summary.by_task.items(), key=lambda x: -x[1]["calls"]):
        lines.append(f"  {task:20s} {info['calls']:5d} calls   ${info['cost']:.4f}")
    return "\n".join(lines)


def reset_log(path: Path = LOG_FILE) -> None:
    p = Path(path)
    if p.exists():
        p.unlink()
