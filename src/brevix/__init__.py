"""Brevix — compress LLM output safely."""

from brevix.compressor import Compressor, CompressionMode, CompressionResult
from brevix.accuracy_guard import AccuracyGuard, GuardResult
from brevix.stats import Stats
from brevix.adaptive import pick_mode, AdaptiveResult
from brevix.tokens import count_tokens, count_tokens_method
from brevix.install import install, list_targets, TARGETS

__version__ = "0.4.0"
__all__ = [
    "Compressor",
    "CompressionMode",
    "CompressionResult",
    "AccuracyGuard",
    "GuardResult",
    "Stats",
    "pick_mode",
    "AdaptiveResult",
    "count_tokens",
    "count_tokens_method",
    "install",
    "list_targets",
    "TARGETS",
]
