"""Brevix Route — model routing + budget enforcement."""

from brevix.route.router import Router, RoutingDecision
from brevix.route.budget import BudgetTracker, BudgetExceededError, BudgetState
from brevix.route.rules import (
    RouteConfig,
    load_config,
    write_default_config,
    DEFAULT_RULES,
    CONFIG_FILE,
)
from brevix.route.classifier import classify, TASK_PATTERNS
from brevix.route.learn import (
    Suggestion,
    TaskStats,
    analyze,
    apply_suggestions,
    render_suggestions,
    suggest_overrides,
)
from brevix.route.route_stats import (
    LOG_FILE,
    RoutingSummary,
    log_call,
    read_log,
    render_summary,
    reset_log,
    summarize,
)
from brevix.route.client import (
    AnthropicProvider,
    Attempt,
    CallResult,
    OpenAIProvider,
    Provider,
    RoutedClient,
    detect_provider,
)
from brevix.route.confidence import (
    ConfidenceResult,
    ScoreBreakdown,
    ScorerWeights,
    hedge_score,
    length_score,
    score_response,
    semantic_score,
    self_rate_score,
    validity_score,
)
from brevix.route.pricing import price, PRICES

__all__ = [
    "Router",
    "RoutingDecision",
    "BudgetTracker",
    "BudgetExceededError",
    "BudgetState",
    "RouteConfig",
    "load_config",
    "write_default_config",
    "DEFAULT_RULES",
    "CONFIG_FILE",
    "classify",
    "TASK_PATTERNS",
    "price",
    "PRICES",
    "RoutedClient",
    "CallResult",
    "Attempt",
    "Provider",
    "AnthropicProvider",
    "OpenAIProvider",
    "detect_provider",
    "ConfidenceResult",
    "ScoreBreakdown",
    "ScorerWeights",
    "hedge_score",
    "length_score",
    "score_response",
    "semantic_score",
    "self_rate_score",
    "validity_score",
    "RoutingSummary",
    "LOG_FILE",
    "log_call",
    "read_log",
    "render_summary",
    "reset_log",
    "summarize",
    "Suggestion",
    "TaskStats",
    "analyze",
    "apply_suggestions",
    "render_suggestions",
    "suggest_overrides",
]
