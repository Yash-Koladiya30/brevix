"""Confidence scoring — fast, deterministic signals to decide when to escalate.

Default scorers (no API/model required):
  - hedge      : count hedge phrases ("I think", "maybe", ...) -> low conf
  - validity   : task-specific format check (JSON parses, classify is short, ...)
  - length     : empty / too short -> low conf

Optional, opt-in:
  - semantic   : Brevix AccuracyGuard similarity (lazy-loads sentence-transformers)
  - self_rate  : ask the model to rate its own confidence (extra mini-call, costs money)

Skipped scorers are dropped and remaining weights renormalize, so disabling
something never silently lowers a response's score.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional


# ---------- hedges ----------

HEDGE_PATTERNS: List[str] = [
    r"\bi (?:think|believe|guess|suppose|assume)\b",
    r"\bnot (?:sure|certain|confident)\b",
    r"\bi'?m not (?:sure|certain|confident)\b",
    r"\bmaybe\b",
    r"\bperhaps\b",
    r"\bcan'?t (?:tell|determine|say)\b",
    r"\bunclear\b",
    r"\bit (?:may|might|could) (?:be|depend)\b",
    r"\bi don'?t know\b",
    r"\bhard to say\b",
    r"\bprobably\b",
    r"\bi am unable\b",
    r"\bcannot answer\b",
]
_HEDGE_RE = [re.compile(p, re.IGNORECASE) for p in HEDGE_PATTERNS]


def hedge_score(text: str) -> float:
    """Higher = fewer hedges = more confident. 0 hedges -> 1.0, 5+ -> 0.0."""
    if not text:
        return 0.5
    hits = sum(1 for r in _HEDGE_RE if r.search(text))
    return max(0.0, 1.0 - hits * 0.2)


# ---------- validity ----------

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL)


def validity_score(text: str, task: str) -> Optional[float]:
    """Format check per task. Returns None if no rule applies for this task."""
    if not text:
        return 0.0
    t = text.strip()
    if task == "parse_json":
        candidate = t
        m = _JSON_FENCE_RE.search(t)
        if m:
            candidate = m.group(1)
        try:
            json.loads(candidate)
            return 1.0
        except (json.JSONDecodeError, ValueError):
            return 0.2
    if task == "classify":
        words = t.split()
        if len(words) <= 5:
            return 1.0
        if len(words) <= 20:
            return 0.7
        return 0.4
    return None


# ---------- length ----------

def length_score(text: str, task: str) -> float:
    """Empty/very short = low; reasonable = high. Tuned per task."""
    if not text:
        return 0.0
    chars = len(text.strip())
    # classify expects short answers
    if task == "classify":
        return 1.0 if 1 <= chars <= 200 else 0.7
    if chars < 10:
        return 0.2
    if chars < 50:
        return 0.6
    return 1.0


# ---------- semantic (optional) ----------

def semantic_score(prompt: str, response: str) -> float:
    """Use Brevix AccuracyGuard. Heavy: lazy-imports sentence-transformers.

    Returns 0.5 (neutral) if Guard fails to load — never raises.
    """
    if not prompt or not response:
        return 0.5
    try:
        from brevix.accuracy_guard import AccuracyGuard  # lazy
        guard = AccuracyGuard(threshold=0.85)
        return float(guard.check(prompt, response).similarity)
    except Exception:
        return 0.5


# ---------- self-rate (optional) ----------

_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def self_rate_score(
    rater: Callable[[str], str],
    prompt: str,
    response_text: str,
) -> Optional[float]:
    """Ask the model to rate its own response. `rater` takes a prompt and returns text."""
    rate_prompt = (
        "On a scale of 0.0 to 1.0, how confident are you that the response "
        "below correctly answers the question? Output ONLY the number.\n\n"
        f"Question: {prompt}\n\nResponse: {response_text}"
    )
    try:
        out = rater(rate_prompt)
        m = _NUM_RE.search(out)
        if not m:
            return None
        v = float(m.group(0))
        return max(0.0, min(1.0, v))
    except Exception:
        return None


# ---------- aggregator ----------

@dataclass
class ScoreBreakdown:
    name: str
    score: float
    weight: float


@dataclass
class ConfidenceResult:
    score: float
    breakdown: List[ScoreBreakdown] = field(default_factory=list)

    def __str__(self) -> str:
        parts = [f"{b.name}={b.score:.2f}*{b.weight:.2f}" for b in self.breakdown]
        return f"conf={self.score:.2f} ({', '.join(parts)})"


@dataclass
class ScorerWeights:
    hedge: float = 0.4
    validity: float = 0.3
    length: float = 0.3
    semantic: float = 0.0     # off by default; set > 0 to enable
    self_rate: float = 0.0    # off by default

    @classmethod
    def from_dict(cls, d: dict) -> "ScorerWeights":
        return cls(
            hedge=float(d.get("hedge", 0.4)),
            validity=float(d.get("validity", 0.3)),
            length=float(d.get("length", 0.3)),
            semantic=float(d.get("semantic", 0.0)),
            self_rate=float(d.get("self_rate", 0.0)),
        )


def score_response(
    prompt: str,
    response_text: str,
    task: str,
    weights: Optional[ScorerWeights] = None,
    rater: Optional[Callable[[str], str]] = None,
) -> ConfidenceResult:
    """Score a response 0..1. Inapplicable scorers are dropped and weights renormalize."""
    w = weights or ScorerWeights()
    parts: List[ScoreBreakdown] = []

    if w.hedge > 0:
        parts.append(ScoreBreakdown("hedge", hedge_score(response_text), w.hedge))
    if w.length > 0:
        parts.append(ScoreBreakdown("length", length_score(response_text, task), w.length))
    if w.validity > 0:
        v = validity_score(response_text, task)
        if v is not None:
            parts.append(ScoreBreakdown("validity", v, w.validity))
    if w.semantic > 0:
        parts.append(ScoreBreakdown("semantic", semantic_score(prompt, response_text), w.semantic))
    if w.self_rate > 0 and rater is not None:
        sr = self_rate_score(rater, prompt, response_text)
        if sr is not None:
            parts.append(ScoreBreakdown("self_rate", sr, w.self_rate))

    total_w = sum(p.weight for p in parts)
    if total_w == 0:
        return ConfidenceResult(score=0.5, breakdown=parts)
    score = sum(p.score * p.weight for p in parts) / total_w
    return ConfidenceResult(score=score, breakdown=parts)
