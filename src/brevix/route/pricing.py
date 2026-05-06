"""Model pricing table — USD per million tokens (input, output)."""

from __future__ import annotations


PRICES: dict[str, dict[str, float]] = {
    # Anthropic
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-opus-4-7": {"input": 15.00, "output": 75.00},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "claude-3-opus": {"input": 15.00, "output": 75.00},
    # OpenAI
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    # Google
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
}


def price(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return cost in USD for an input/output token pair on the given model.

    Returns 0.0 for unknown models so the router never crashes on a custom model name.
    """
    p = PRICES.get(model)
    if not p:
        return 0.0
    return (input_tokens / 1_000_000) * p["input"] + (output_tokens / 1_000_000) * p["output"]


def estimate_tokens(text: str) -> int:
    """Cheap char-based token estimate. Real call should use brevix.tokens.count_tokens."""
    return max(1, len(text) // 4)
