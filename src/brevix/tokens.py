"""Token counting — uses tiktoken when available, falls back to chars/4.

Importing tiktoken is optional. Apps that want accurate counts can install it;
otherwise the heuristic (1 token ≈ 4 chars) is good enough for stats display.
"""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _encoder():
    try:
        import tiktoken
        return tiktoken.get_encoding("cl100k_base")
    except ImportError:
        return None


def count_tokens(text: str) -> int:
    enc = _encoder()
    if enc is None:
        return max(0, len(text) // 4)
    return len(enc.encode(text))


def count_tokens_method() -> str:
    return "tiktoken" if _encoder() is not None else "char-heuristic"
