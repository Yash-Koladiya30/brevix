"""Task classifier — keyword/regex based, no API call."""

from __future__ import annotations

import re
from typing import List, Pattern, Tuple


# Order matters: more specific patterns first. First match wins.
TASK_PATTERNS: List[Tuple[str, List[str]]] = [
    ("parse_json", [r"\bparse\b.*\bjson\b", r"\bextract\b.*\bjson\b", r"\bjson schema\b"]),
    ("classify", [r"\bclassif\w*\b", r"\bcategoriz\w*\b", r"\blabel\s+(this|the|a)\b"]),
    ("extract", [r"\bextract\w*\b", r"\bpull out\b"]),
    ("format", [r"\bformat\b", r"\bprettify\b", r"\blint\b", r"\bindent\b"]),
    ("rename", [r"\brename\b", r"\bsubstitut\w*\b"]),
    ("translate", [r"\btranslat\w*\b"]),
    ("summarize", [r"\bsummariz\w*\b", r"\btl;?dr\b"]),
    ("write_reply", [r"\breply\b", r"\bplay\s*store reply\b", r"\brespond to (a |the )?(user|customer)\b"]),
    ("architecture", [
        r"\barchitect\w*\b",
        r"\bdesign (a |the )?system\b",
        r"\bsystem design\b",
        r"\bmulti[- ]agent\b",
        r"\bdistributed system\b",
    ]),
    ("debug", [r"\bdebug\b", r"\bfix\b.*\bbug\b", r"\bwhy\b.*\b(fail|crash|error)\w*\b"]),
    ("refactor", [r"\brefactor\b", r"\brestructur\w*\b"]),
    ("code_review", [r"\b(code )?review\b", r"\baudit\b.*\bcode\b"]),
    ("explain", [r"\bexplain\b", r"\bdescribe\b", r"\bwhat does\b", r"\bhow does\b"]),
]


# Precompiled at import for hot-path speed; classify() should not re-compile.
_COMPILED: List[Tuple[str, List[Pattern[str]]]] = [
    (task, [re.compile(p) for p in patterns]) for task, patterns in TASK_PATTERNS
]


def classify(prompt: str) -> str:
    """Return task type for a prompt. Default: 'general'."""
    if not prompt:
        return "general"
    p = prompt.lower()
    for task, patterns in _COMPILED:
        for pat in patterns:
            if pat.search(p):
                return task
    return "general"
