"""Tests for Accuracy Guard."""

from brevix.accuracy_guard import AccuracyGuard


class TestLexicalFallback:
    def setup_method(self) -> None:
        self.guard = AccuracyGuard(threshold=0.5)
        # Force lexical fallback by skipping the model
        self.guard._model = False

    def test_identical_passes(self) -> None:
        result = self.guard.check("hello world", "hello world")
        assert result.passed
        assert result.similarity == 1.0

    def test_completely_different_fails(self) -> None:
        result = self.guard.check("the cat sat on the mat", "quantum physics is weird")
        assert not result.passed

    def test_compressed_version_overlaps(self) -> None:
        original = "The user wants to compress LLM output to save tokens"
        compressed = "user wants compress LLM output save tokens"
        result = self.guard.check(original, compressed)
        assert result.similarity > 0.7

    def test_method_reported(self) -> None:
        result = self.guard.check("hello", "hello")
        assert result.method in {"semantic", "content-containment", "empty"}

    def test_compression_drops_stopwords_still_passes(self) -> None:
        """Regression: compressed text with stopwords removed must score reasonably."""
        original = "The cat sat on the mat because it was tired."
        compressed = "Cat sat on mat. Tired."
        result = self.guard.check(original, compressed)
        # Content-containment fallback: kept 4/5 content tokens = 0.8.
        # (Old Jaccard implementation scored ~0.45 — well below threshold.)
        assert result.similarity >= 0.75, f"got {result.similarity}"

    def test_no_spurious_score_penalty_for_compression(self) -> None:
        """Compression with all original content words preserved must score 1.0."""
        original = "The user wants to compress LLM output."
        compressed = "User wants compress LLM output."
        result = self.guard.check(original, compressed)
        assert result.similarity == 1.0, f"got {result.similarity}"

    def test_empty_inputs(self) -> None:
        result = self.guard.check("", "")
        assert result.passed


class TestThreshold:
    def test_default_threshold(self) -> None:
        guard = AccuracyGuard()
        assert guard.threshold == 0.85

    def test_custom_threshold(self) -> None:
        guard = AccuracyGuard(threshold=0.9)
        assert guard.threshold == 0.9


class TestWarning:
    def test_warning_when_failed(self) -> None:
        guard = AccuracyGuard(threshold=0.99)
        guard._model = False
        result = guard.check("hello world", "completely unrelated text here")
        assert result.warning is not None
        assert "below threshold" in result.warning

    def test_no_warning_when_passed(self) -> None:
        guard = AccuracyGuard(threshold=0.5)
        guard._model = False
        result = guard.check("hello world", "hello world")
        assert result.warning is None
