"""Local stats — tracks tokens saved across sessions, plus real-log readout."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path

from brevix.session_logs import (
    SessionStats,
    estimate_savings_from_baseline,
    parse_logs,
)


STATS_DIR = Path.home() / ".brevix"
STATS_FILE = STATS_DIR / "stats.json"


@dataclass
class StatsData:
    total_compressions: int = 0
    total_chars_saved: int = 0
    total_tokens_estimated: int = 0
    by_mode: dict = field(default_factory=lambda: {"lite": 0, "full": 0, "ultra": 0, "auto": 0})
    first_used: str = ""
    last_used: str = ""


class Stats:
    """Persist compression stats to ~/.brevix/stats.json."""

    def __init__(self, path: Path = STATS_FILE) -> None:
        self.path = path
        self.data = self._load()

    def _load(self) -> StatsData:
        if not self.path.exists():
            return StatsData(first_used=self._now())
        try:
            with self.path.open("r") as f:
                raw = json.load(f)
            for key in ("lite", "full", "ultra", "auto"):
                raw.setdefault("by_mode", {}).setdefault(key, 0)
            return StatsData(**raw)
        except (json.JSONDecodeError, TypeError):
            return StatsData(first_used=self._now())

    def record(self, mode: str, chars_saved: int, tokens_saved: int) -> None:
        self.data.total_compressions += 1
        self.data.total_chars_saved += chars_saved
        self.data.total_tokens_estimated += tokens_saved
        self.data.by_mode[mode] = self.data.by_mode.get(mode, 0) + 1
        self.data.last_used = self._now()
        if not self.data.first_used:
            self.data.first_used = self.data.last_used
        self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w") as f:
            json.dump(asdict(self.data), f, indent=2)

    def summary(self, since: str = "all", real: bool = False, share: bool = False) -> str:
        if share:
            return self._share_line(since=since, real=real)
        if real:
            return self._real_summary(since=since)
        return self._estimate_summary()

    def _estimate_summary(self) -> str:
        d = self.data
        cost_estimate = d.total_tokens_estimated * 0.000003
        return (
            f"Brevix Stats (estimated, in-process)\n"
            f"-------------------------------------\n"
            f"Compressions:     {d.total_compressions}\n"
            f"Characters saved: {d.total_chars_saved:,}\n"
            f"Tokens saved:     ~{d.total_tokens_estimated:,}\n"
            f"Estimated $$:     ~${cost_estimate:.4f}\n"
            f"By mode:          lite={d.by_mode.get('lite', 0)} "
            f"full={d.by_mode.get('full', 0)} ultra={d.by_mode.get('ultra', 0)} "
            f"auto={d.by_mode.get('auto', 0)}\n"
            f"First used:       {d.first_used or 'never'}\n"
            f"Last used:        {d.last_used or 'never'}\n"
            f"\nTip: pass --real for token counts parsed from Claude Code logs.\n"
        )

    def _real_summary(self, since: str) -> str:
        s = parse_logs(since=since)
        savings = estimate_savings_from_baseline(s)
        models = ", ".join(f"{k}={v:,}" for k, v in sorted(s.by_model.items())) or "—"
        return (
            f"Brevix Stats (real, parsed from Claude Code logs)\n"
            f"--------------------------------------------------\n"
            f"Window:               {since}\n"
            f"Sessions:             {s.sessions}\n"
            f"Assistant turns:      {s.assistant_turns:,}\n"
            f"Input tokens:         {s.input_tokens:,}\n"
            f"Output tokens:        {s.output_tokens:,}\n"
            f"Cache reads:          {s.cache_read_tokens:,}\n"
            f"Cache creations:      {s.cache_creation_tokens:,}\n"
            f"By model:             {models}\n"
            f"First seen:           {s.first_seen or '—'}\n"
            f"Last seen:            {s.last_seen or '—'}\n"
            f"\nEstimated savings vs. uncompressed baseline (2.5×):\n"
            f"  Baseline output:    ~{savings['estimated_baseline_tokens']:,} tokens\n"
            f"  Tokens saved:       ~{savings['estimated_tokens_saved']:,} ({savings['estimated_pct_saved']}%)\n"
            f"  $$ saved:           ~${savings['estimated_usd_saved']}\n"
        )

    def _share_line(self, since: str, real: bool) -> str:
        if real:
            s = parse_logs(since=since)
            savings = estimate_savings_from_baseline(s)
            return (
                f"⛏ Brevix saved ~{savings['estimated_tokens_saved']:,} tokens "
                f"(~${savings['estimated_usd_saved']}) over {s.assistant_turns:,} turns "
                f"in the last {since}. https://github.com/Yash-Koladiya30/brevix"
            )
        d = self.data
        return (
            f"⛏ Brevix saved ~{d.total_tokens_estimated:,} tokens "
            f"across {d.total_compressions} compressions "
            f"(~${d.total_tokens_estimated * 0.000003:.2f}). "
            f"https://github.com/Yash-Koladiya30/brevix"
        )

    def reset(self) -> None:
        self.data = StatsData(first_used=self._now())
        self._save()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")


def real_session_stats(since: str = "all") -> SessionStats:
    """Convenience re-export so callers can `from brevix.stats import real_session_stats`."""
    return parse_logs(since=since)
