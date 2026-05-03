"""Tests for adaptive mode + token counter."""

from brevix.adaptive import pick_mode
from brevix.compressor import CompressionMode
from brevix.tokens import count_tokens, count_tokens_method


class TestAdaptive:
    def test_picks_a_valid_mode(self) -> None:
        text = (
            "Sure! I'd be happy to help. The reason your code is failing is "
            "that you are basically just passing the wrong type to the function."
        )
        result = pick_mode(text)
        assert result.chosen_mode in {CompressionMode.LITE, CompressionMode.FULL, CompressionMode.ULTRA}
        assert result.compression.compressed
        assert result.guard.similarity > 0.0

    def test_short_text_still_works(self) -> None:
        result = pick_mode("Use sorted().")
        assert result.compression.compressed


class TestTokens:
    def test_count_returns_int(self) -> None:
        n = count_tokens("hello world")
        assert isinstance(n, int)
        assert n > 0

    def test_method_reported(self) -> None:
        assert count_tokens_method() in {"tiktoken", "char-heuristic"}

    def test_empty(self) -> None:
        assert count_tokens("") == 0
