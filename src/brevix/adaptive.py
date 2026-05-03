"""Adaptive mode — auto-pick compression level per text characteristics.

Heuristic: pick the most aggressive mode that still passes Accuracy Guard.
Falls back to a static heuristic (verbosity + density) if guard unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass

from brevix.accuracy_guard import AccuracyGuard, GuardResult
from brevix.compressor import Compressor, CompressionMode, CompressionResult


@dataclass
class AdaptiveResult:
    chosen_mode: CompressionMode
    compression: CompressionResult
    guard: GuardResult


def pick_mode(text: str, threshold: float = 0.85, guard: AccuracyGuard | None = None) -> AdaptiveResult:
    """Pick the most aggressive compression mode that still passes the guard.

    Walks ultra → full → lite. Returns the first that passes, else lite (which
    is the safest non-trivial option).
    """
    guard = guard or AccuracyGuard(threshold=threshold)
    last: AdaptiveResult | None = None
    for mode in (CompressionMode.ULTRA, CompressionMode.FULL, CompressionMode.LITE):
        result = Compressor(mode).compress(text)
        check = guard.check(text, result.compressed)
        last = AdaptiveResult(chosen_mode=mode, compression=result, guard=check)
        if check.passed:
            return last
    assert last is not None
    return last
