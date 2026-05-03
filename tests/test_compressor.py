"""Tests for the compression engine."""

import pytest

from brevix.compressor import Compressor, CompressionMode


class TestLiteMode:
    def setup_method(self) -> None:
        self.c = Compressor(CompressionMode.LITE)

    def test_drops_pleasantries(self) -> None:
        text = "Sure! I'd be happy to help. The answer is 42."
        result = self.c.compress(text)
        assert "Sure" not in result.compressed
        assert "happy to help" not in result.compressed
        assert "42" in result.compressed

    def test_drops_filler(self) -> None:
        text = "This is just basically a really simple example."
        result = self.c.compress(text)
        for word in ["just", "basically", "really", "simply"]:
            assert word not in result.compressed.lower().split()

    def test_keeps_articles(self) -> None:
        text = "The cat sat on a mat."
        result = self.c.compress(text)
        assert "the" in result.compressed.lower() or "The" in result.compressed

    def test_replaces_verbose_phrases(self) -> None:
        text = "We need to make use of this function in order to fix the bug."
        result = self.c.compress(text)
        assert "make use of" not in result.compressed.lower()
        assert "in order to" not in result.compressed.lower()
        assert "use" in result.compressed.lower()


class TestFullMode:
    def setup_method(self) -> None:
        self.c = Compressor(CompressionMode.FULL)

    def test_drops_articles(self) -> None:
        text = "The cat sat on a mat."
        result = self.c.compress(text)
        compressed_lower = result.compressed.lower()
        assert " the " not in f" {compressed_lower} "
        assert " a " not in f" {compressed_lower} "

    def test_savings_meaningful(self) -> None:
        text = (
            "Sure! I'd be happy to help you with that. "
            "The reason your code is failing is basically because "
            "you are just simply passing the wrong type to the function."
        )
        result = self.c.compress(text)
        assert result.char_savings_pct > 30


class TestUltraMode:
    def setup_method(self) -> None:
        self.c = Compressor(CompressionMode.ULTRA)

    def test_uses_arrow_for_causation(self) -> None:
        text = "Cache miss leads to slow lookup."
        result = self.c.compress(text)
        assert "→" in result.compressed

    def test_max_compression(self) -> None:
        text = (
            "Of course! Let me explain that for you. "
            "Generally speaking, when a process forks, it actually creates "
            "a new child process which is essentially a copy of the parent."
        )
        result = self.c.compress(text)
        assert result.char_savings_pct > 50


class TestProtectedRegions:
    def setup_method(self) -> None:
        self.c = Compressor(CompressionMode.ULTRA)

    def test_code_blocks_unchanged(self) -> None:
        text = "Here is the code:\n```python\nfor i in range(10):\n    print(i)\n```\nThat will work."
        result = self.c.compress(text)
        assert "```python\nfor i in range(10):\n    print(i)\n```" in result.compressed

    def test_inline_code_unchanged(self) -> None:
        text = "The function `useState(0)` is just a hook."
        result = self.c.compress(text)
        assert "`useState(0)`" in result.compressed

    def test_urls_unchanged(self) -> None:
        text = "Visit https://example.com/path?q=1 for the docs."
        result = self.c.compress(text)
        assert "https://example.com/path?q=1" in result.compressed

    def test_error_quotes_unchanged(self) -> None:
        text = 'The error was "TypeError: cannot read property of undefined" basically.'
        result = self.c.compress(text)
        assert '"TypeError: cannot read property of undefined"' in result.compressed


class TestEdgeCases:
    def test_empty_string(self) -> None:
        c = Compressor(CompressionMode.FULL)
        result = c.compress("")
        assert result.compressed == ""
        assert result.char_savings == 0

    def test_whitespace_only(self) -> None:
        c = Compressor(CompressionMode.FULL)
        result = c.compress("   \n\n   ")
        assert result.char_savings == 0

    def test_already_terse(self) -> None:
        c = Compressor(CompressionMode.FULL)
        text = "Run `ls`."
        result = c.compress(text)
        assert "ls" in result.compressed


@pytest.mark.parametrize("mode", [CompressionMode.LITE, CompressionMode.FULL, CompressionMode.ULTRA])
def test_compression_never_grows(mode: CompressionMode) -> None:
    c = Compressor(mode)
    samples = [
        "Sure! I'd be happy to help with that.",
        "The reason your code is failing is that you are passing the wrong type.",
        "In order to fix this, you need to make use of the new API.",
    ]
    for text in samples:
        result = c.compress(text)
        assert len(result.compressed) <= len(result.original)
