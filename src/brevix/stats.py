"""Local stats counter — tracks tokens saved across sessions."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


STATS_DIR = Path.home() / ".brevix"
STATS_FILE = STATS_DIR / "stats.json"


@dataclass
class StatsData:
    total_compressions: int = 0
    total_chars_saved: int = 0
    total_tokens_estimated: int = 0
    by_mode: dict = None
    first_used: str = ""
    last_used: str = ""

    def __post_init__(self):
        if self.by_mode is None:
            self.by_mode = {"lite": 0, "full": 0, "ultra": 0}


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

    def summary(self) -> str:
        d = self.data
        cost_estimate = d.total_tokens_estimated * 0.000003
        return (
            f"Brevix Stats\n"
            f"------------\n"
            f"Compressions:    {d.total_compressions}\n"
            f"Characters saved: {d.total_chars_saved:,}\n"
            f"Tokens saved:    ~{d.total_tokens_estimated:,}\n"
            f"Estimated $$ saved: ~${cost_estimate:.4f}\n"
            f"By mode:         lite={d.by_mode.get('lite', 0)} "
            f"full={d.by_mode.get('full', 0)} ultra={d.by_mode.get('ultra', 0)}\n"
            f"First used:      {d.first_used or 'never'}\n"
            f"Last used:       {d.last_used or 'never'}\n"
        )

    def reset(self) -> None:
        self.data = StatsData(first_used=self._now())
        self._save()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
