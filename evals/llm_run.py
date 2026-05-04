"""Run prompts through Claude with three system prompts: baseline, control, brevix.

Writes a snapshot JSON consumable by measure.py. Requires the `anthropic`
SDK and ANTHROPIC_API_KEY in the environment.

Usage:
  python evals/llm_run.py --prompts evals/prompts/en.txt \\
      --model claude-sonnet-4-6 --out evals/snapshots/latest.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ARMS = {
    "baseline": "",
    "control": "Be terse. Avoid filler.",
    "brevix": (
        "Brevix mode active (full). Drop articles, filler, pleasantries, hedging. "
        "Fragments OK. Code, commits, security stay normal."
    ),
}


def run_arm(client, model: str, system: str, prompt: str) -> str:
    msg = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system or "",
        messages=[{"role": "user", "content": prompt}],
    )
    parts = msg.content if isinstance(msg.content, list) else []
    text = "".join(getattr(p, "text", "") for p in parts if getattr(p, "type", "") == "text")
    return text


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--prompts", default="evals/prompts/en.txt")
    p.add_argument("--model", default="claude-sonnet-4-6")
    p.add_argument("--out", default="evals/snapshots/latest.json")
    args = p.parse_args()

    try:
        import anthropic
    except ImportError:
        print("ERROR: pip install anthropic", file=sys.stderr)
        return 2
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return 2

    client = anthropic.Anthropic()
    prompts = [
        line.strip() for line in Path(args.prompts).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    snapshot = []
    for i, prompt in enumerate(prompts, 1):
        print(f"[{i}/{len(prompts)}] {prompt[:60]}…", file=sys.stderr)
        outputs = {}
        for arm, system in ARMS.items():
            outputs[arm] = run_arm(client, args.model, system, prompt)
        snapshot.append({"prompt": prompt, "outputs": outputs})

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    meta = {
        "model": args.model,
        "n_prompts": len(prompts),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    Path(out_path.with_suffix(".meta.json")).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
