"""Accuracy Guard — semantic similarity check between original and compressed text.

Verifies that rule-based compression preserves meaning. Uses local
sentence-transformers (no API cost). Falls back to a content-word
containment metric tailored for compression (NOT Jaccard, which
structurally penalizes legitimate compression).

This is what separates safe production-grade compression from a blind
text-stripper: every output is scored against the original, and the
caller can choose to warn, fall back, or block when meaning would be lost.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


# Closed-class words that compression is allowed to drop without
# meaning loss. Excluded from the lexical similarity calculation.
_STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "am", "do", "does", "did", "have", "has", "had", "of", "to", "in",
    "on", "at", "for", "by", "with", "from", "as", "and", "or", "but",
    "so", "if", "then", "than", "that", "this", "these", "those",
    "it", "its", "i", "you", "he", "she", "we", "they", "them",
    "your", "my", "our", "his", "her", "their",
    "just", "really", "basically", "actually", "simply", "very",
    "quite", "perhaps", "maybe", "essentially", "literally",
    "however", "therefore", "thus", "hence", "moreover",
    "sure", "certainly", "of", "course",
    "i'd", "i'll", "i've", "i'm", "we'll", "we're",
    "let", "let's",
})


@dataclass
class GuardResult:
    similarity: float
    threshold: float
    passed: bool
    method: str

    @property
    def warning(self) -> Optional[str]:
        if self.passed:
            return None
        return (
            f"Accuracy Guard: similarity {self.similarity:.2f} below threshold "
            f"{self.threshold:.2f} ({self.method}). Compression may have lost meaning."
        )


class AccuracyGuard:
    """Check whether compressed text preserves original meaning."""

    def __init__(self, threshold: float = 0.85, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.threshold = threshold
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        except ImportError:
            self._model = False
        return self._model

    def check(self, original: str, compressed: str) -> GuardResult:
        if not original.strip() or not compressed.strip():
            return GuardResult(similarity=1.0, threshold=self.threshold, passed=True, method="empty")

        model = self._load_model()
        if model:
            similarity = self._semantic_similarity(original, compressed, model)
            method = "semantic"
        else:
            similarity = self._content_containment(original, compressed)
            method = "content-containment"

        return GuardResult(
            similarity=similarity,
            threshold=self.threshold,
            passed=similarity >= self.threshold,
            method=method,
        )

    @staticmethod
    def _semantic_similarity(a: str, b: str, model) -> float:
        from sentence_transformers import util
        emb = model.encode([a, b], convert_to_tensor=True, show_progress_bar=False)
        score = util.cos_sim(emb[0], emb[1]).item()
        return float(max(0.0, min(1.0, score)))

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-z0-9_]+", text.lower())

    @classmethod
    def _content_tokens(cls, text: str) -> set[str]:
        return {t for t in cls._tokenize(text) if t not in _STOPWORDS and len(t) > 1}

    @classmethod
    def _content_containment(cls, original: str, compressed: str) -> float:
        """Fraction of original content words preserved in compressed text.

        Designed for compression: dropping stopwords/articles is expected and
        does NOT lower the score. Score drops only when meaningful content
        words disappear or new unrelated terms appear.
        """
        orig_tokens = cls._content_tokens(original)
        comp_tokens = cls._content_tokens(compressed)
        if not orig_tokens:
            return 1.0 if not comp_tokens else 0.5
        kept = len(orig_tokens & comp_tokens) / len(orig_tokens)
        spurious = (
            len(comp_tokens - orig_tokens) / max(len(comp_tokens), 1)
            if comp_tokens else 0.0
        )
        return max(0.0, min(1.0, kept - 0.5 * spurious))
