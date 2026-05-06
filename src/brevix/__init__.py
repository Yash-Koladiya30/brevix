"""Brevix — compress LLM output safely."""

from brevix.compressor import Compressor, CompressionMode, CompressionResult
from brevix.accuracy_guard import AccuracyGuard, GuardResult
from brevix.stats import Stats
from brevix.adaptive import pick_mode, AdaptiveResult
from brevix.tokens import count_tokens, count_tokens_method
from brevix.install import install, list_targets, TARGETS
from brevix.route import (
    Router,
    RoutingDecision,
    BudgetTracker,
    BudgetExceededError,
    RouteConfig,
    RoutedClient,
    CallResult,
    classify as classify_task,
    price as model_price,
)

__version__ = "0.4.1"
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
    "Router",
    "RoutingDecision",
    "BudgetTracker",
    "BudgetExceededError",
    "RouteConfig",
    "RoutedClient",
    "CallResult",
    "classify_task",
    "model_price",
]
