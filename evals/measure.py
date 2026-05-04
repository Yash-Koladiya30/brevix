"""Token-counting analyzer for Brevix eval snapshots.

Reads a snapshot JSON produced by `llm_run.py` and computes token deltas
across three arms: baseline (no system prompt), control (be terse), brevix.

No API calls. Uses tiktoken o200k_base if available, else char/4 heuristic.

Usage:
  python evals/measure.py [snapshots/latest.json]
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path


def count_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding("o200k_base")
        return len(enc.encode(text))
    except Exception:
        return max(0, len(text) // 4)


def load_snapshot(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def measure(snapshot: list[dict]) -> dict:
    arms = ["baseline", "control", "brevix"]
    results: dict = {a: [] for a in arms}
    for entry in snapshot:
        outputs = entry.get("outputs", {})
        for arm in arms:
            text = outputs.get(arm, "")
            results[arm].append(count_tokens(text))

    summary: dict = {}
    for arm in arms:
        counts = results[arm]
        if not counts:
            continue
        summary[arm] = {
            "n": len(counts),
            "median": statistics.median(counts),
            "mean": round(statistics.mean(counts), 1),
            "stdev": round(statistics.pstdev(counts), 1),
            "total": sum(counts),
        }

    base = summary.get("baseline")
    if base and "brevix" in summary:
        summary["brevix"]["pct_vs_baseline"] = round(
            100 * (1 - summary["brevix"]["total"] / base["total"]), 1
        ) if base["total"] else 0.0
    if "control" in summary and base:
        summary["control"]["pct_vs_baseline"] = round(
            100 * (1 - summary["control"]["total"] / base["total"]), 1
        ) if base["total"] else 0.0
    if "brevix" in summary and "control" in summary and summary["control"]["total"]:
        summary["brevix"]["pct_vs_control"] = round(
            100 * (1 - summary["brevix"]["total"] / summary["control"]["total"]), 1
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    snap_path = Path(args[0]) if args else Path("evals/snapshots/latest.json")
    if not snap_path.exists():
        print(f"No snapshot at {snap_path}. Run llm_run.py first.", file=sys.stderr)
        return 2
    snap = load_snapshot(snap_path)
    summary = measure(snap)

    print(f"# Brevix eval — {snap_path.name}")
    print(f"# n={len(snap)} prompts, tokenizer={'tiktoken/o200k_base' if _has_tiktoken() else 'char/4'}\n")
    rows = [
        ("arm", "n", "median", "mean", "stdev", "total", "vs baseline", "vs control"),
    ]
    for arm in ("baseline", "control", "brevix"):
        d = summary.get(arm, {})
        rows.append((
            arm,
            d.get("n", "—"),
            d.get("median", "—"),
            d.get("mean", "—"),
            d.get("stdev", "—"),
            d.get("total", "—"),
            f"{d.get('pct_vs_baseline', '—')}%" if "pct_vs_baseline" in d else "—",
            f"{d.get('pct_vs_control', '—')}%" if "pct_vs_control" in d else "—",
        ))
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  ".join(str(v).ljust(widths[i]) for i, v in enumerate(r)))
    return 0


def _has_tiktoken() -> bool:
    try:
        import tiktoken  # noqa: F401
        return True
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(main())
