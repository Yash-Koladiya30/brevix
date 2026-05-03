"""Core compression engine.

Rule-based compression. Three modes: lite, full, ultra.
Code blocks, URLs, and quoted error messages are never modified.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class CompressionMode(str, Enum):
    LITE = "lite"
    FULL = "full"
    ULTRA = "ultra"


ARTICLES = {"a", "an", "the"}

FILLER_FULL = {
    "just", "really", "basically", "actually", "simply", "very",
    "quite", "rather", "somewhat", "perhaps", "maybe", "essentially",
    "literally", "obviously", "clearly", "definitely", "absolutely",
    "merely", "fairly", "pretty", "kind", "sort",
}

FILLER_ULTRA = FILLER_FULL | {
    "however", "therefore", "thus", "hence", "moreover", "furthermore",
    "additionally", "consequently", "indeed", "certainly", "accordingly",
    "subsequently", "nevertheless", "nonetheless",
}

PLEASANTRIES = [
    # Full clause: "I would be happy to help you with that."
    r"\b(i(?:'d| would| am| ?'m)?\s+(?:be\s+)?)?(happy|glad|pleased|delighted)\s+to\s+(help|assist|explain|show|walk|guide|take a look)\b[^.!?]*[.!?]",
    r"\b(sure|certainly|of course|absolutely|gladly)\b[,!.\s]+",
    r"\b(let me|let's|i'll|i will|i can|i could)\s+(help|assist|explain|show|walk|guide|take a look)\b[^.!?]*[.!?]",
    r"\bfeel free to\b[^.!?]*[.!?]",
    r"\b(great|good|excellent)\s+(question|point|catch|observation)\b[!.\s]*",
    r"\bhope (this|that) helps\b[!.\s]*",
    r"\bthat'?s a (great|good|valid) (question|point)\b[!.\s]*",
    r"\bhere'?s (what|how) (you|we) can do\b[:!.\s]*",
    r"\bno problem\b[!.\s]*",
    r"\byou'?re welcome\b[!.\s]*",
    r"\bdon'?t hesitate to\b[^.!?]*[.!?]",
    r"\bplease (note|be aware|keep in mind)\s+(that\s+)?",
]

HEDGES = [
    r"\bit\s+(seems|appears|looks|might be|could be)\s+(that|like)?\s*",
    r"\bi\s+(think|believe|suppose|guess|assume)\s+(that\s+)?",
    r"\bin my opinion\b,?\s*",
    r"\bgenerally speaking\b,?\s*",
    r"\bif i'?m not mistaken\b,?\s*",
    r"\bas far as i (know|can tell)\b,?\s*",
    r"\bfrom what i (can see|understand)\b,?\s*",
    r"\bmore or less\b,?\s*",
    r"\bto some extent\b,?\s*",
    r"\bin a sense\b,?\s*",
]

VERBOSE_TO_TERSE = {
    r"\bin order to\b": "to",
    r"\bdue to the fact that\b": "because",
    r"\bowing to the fact that\b": "because",
    r"\bon account of the fact that\b": "because",
    r"\bfor the reason that\b": "because",
    r"\bat this point in time\b": "now",
    r"\bat the present time\b": "now",
    r"\bat that point in time\b": "then",
    r"\bin the event that\b": "if",
    r"\bin the case (that|of)\b": "if",
    r"\bin situations where\b": "when",
    r"\bfor the purpose of\b": "to",
    r"\bwith regard to\b": "re:",
    r"\bwith respect to\b": "re:",
    r"\bin reference to\b": "re:",
    r"\bin relation to\b": "re:",
    r"\bmake use of\b": "use",
    r"\bmakes use of\b": "uses",
    r"\bmade use of\b": "used",
    r"\btake into (account|consideration)\b": "consider",
    r"\bcarry out\b": "do",
    r"\bcarries out\b": "does",
    r"\bcame to a (decision|conclusion)\b": "decided",
    r"\bcome to a (decision|conclusion)\b": "decide",
    r"\bgive consideration to\b": "consider",
    r"\bimplement(ed|ing)? a solution for\b": r"fix\1",
    r"\bperform(s|ed|ing)? an analysis of\b": r"analyze\1",
    r"\bin spite of the fact that\b": "though",
    r"\bdespite the fact that\b": "though",
    r"\ba large number of\b": "many",
    r"\ba small number of\b": "few",
    r"\bthe majority of\b": "most",
    r"\ba great deal of\b": "much",
    r"\bthe reason (why|that)\b": "why",
    r"\bthe reason is (that|because)\b": "because",
    r"\bis (able|unable) to\b": r"\1",
    r"\bare (able|unable) to\b": r"\1",
    r"\bhas the ability to\b": "can",
    r"\bhave the ability to\b": "can",
    r"\bin the process of\b": "",
    r"\bprior to\b": "before",
    r"\bsubsequent to\b": "after",
    r"\bduring the (time|course) (that|of which)\b": "while",
    r"\bin the (event|case) of\b": "if",
    r"\bgiven the fact that\b": "since",
    r"\bin (light|view) of the fact that\b": "since",
    r"\bbased on the fact that\b": "since",
    r"\ba number of\b": "several",
    r"\bin many cases\b": "often",
    r"\bin most cases\b": "usually",
    r"\bon a regular basis\b": "regularly",
    r"\bon a daily basis\b": "daily",
    r"\bin order for\b": "for",
    r"\bregardless of (whether|the fact that)\b": "regardless",
    r"\bnotwithstanding the fact that\b": "though",
    r"\bin close proximity to\b": "near",
    r"\bin the vicinity of\b": "near",
    r"\bat a later (date|time)\b": "later",
    r"\bat an earlier (date|time)\b": "earlier",
    r"\buntil such time as\b": "until",
    r"\bas a (consequence|result) of\b": "from",
    r"\bin (excess|surplus) of\b": "over",
    r"\bin terms of\b": "for",
    r"\bwith the exception of\b": "except",
    r"\bwith the help of\b": "with",
    r"\bwith reference to\b": "re:",
    r"\bin connection with\b": "re:",
    r"\bfor the most part\b": "mostly",
    r"\bwhether or not\b": "whether",
    r"\bin all (likelihood|probability)\b": "likely",
    r"\bcurrently in the process of\b": "",
}


@dataclass
class CompressionResult:
    original: str
    compressed: str
    mode: CompressionMode
    char_savings: int
    char_savings_pct: float
    token_savings_estimate: int

    def __str__(self) -> str:
        return self.compressed


class Compressor:
    """Compress text per mode while preserving code, URLs, and errors."""

    CODE_FENCE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
    INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
    URL_RE = re.compile(r"https?://\S+|www\.\S+")
    ERROR_QUOTE_RE = re.compile(r'"[^"\n]*(?:Error|Exception|Warning|Failed|Traceback)[^"\n]*"', re.IGNORECASE)

    def __init__(self, mode: CompressionMode = CompressionMode.FULL) -> None:
        self.mode = mode

    def compress(self, text: str) -> CompressionResult:
        if not text or not text.strip():
            return CompressionResult(text, text, self.mode, 0, 0.0, 0)

        protected, stashed_text = self._protect(text)
        compressed = self._apply_rules(stashed_text)
        compressed = self._cleanup_whitespace(compressed)
        compressed = self._restore(compressed, protected)

        original_len = len(text)
        compressed_len = len(compressed)
        savings = max(0, original_len - compressed_len)
        pct = (savings / original_len * 100) if original_len else 0.0

        return CompressionResult(
            original=text,
            compressed=compressed,
            mode=self.mode,
            char_savings=savings,
            char_savings_pct=round(pct, 2),
            token_savings_estimate=savings // 4,
        )

    def _protect(self, text: str) -> tuple[dict[str, str], str]:
        """Replace code/URLs/errors with placeholders so rules skip them."""
        protected: dict[str, str] = {}
        counter = 0

        def stash(match: re.Match[str]) -> str:
            nonlocal counter
            key = f"__BRVX_{counter}__"
            protected[key] = match.group(0)
            counter += 1
            return key

        text = self.CODE_FENCE_RE.sub(stash, text)
        text = self.INLINE_CODE_RE.sub(stash, text)
        text = self.URL_RE.sub(stash, text)
        text = self.ERROR_QUOTE_RE.sub(stash, text)

        return protected, text

    def _restore(self, text: str, protected: dict[str, str]) -> str:
        for key, original in protected.items():
            text = text.replace(key, original)
        return text

    def _apply_rules(self, text: str) -> str:
        if self.mode == CompressionMode.LITE:
            return self._compress_lite(text)
        if self.mode == CompressionMode.FULL:
            return self._compress_full(text)
        return self._compress_ultra(text)

    def _compress_lite(self, text: str) -> str:
        for pattern in PLEASANTRIES:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        for pattern in HEDGES:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        for pattern, replacement in VERBOSE_TO_TERSE.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        text = self._drop_words(text, FILLER_FULL)
        return text

    def _compress_full(self, text: str) -> str:
        text = self._compress_lite(text)
        text = self._drop_articles(text)
        text = self._tighten_full(text)
        return text

    def _compress_ultra(self, text: str) -> str:
        text = self._compress_full(text)
        text = self._drop_words(text, FILLER_ULTRA - FILLER_FULL)
        text = self._collapse_sentences(text)
        text = self._tighten_ultra(text)
        return text

    @staticmethod
    def _drop_words(text: str, words: set[str]) -> str:
        if not words:
            return text
        pattern = r"\b(" + "|".join(re.escape(w) for w in words) + r")\b"
        return re.sub(pattern, "", text, flags=re.IGNORECASE)

    @staticmethod
    def _drop_articles(text: str) -> str:
        pattern = r"\b(" + "|".join(ARTICLES) + r")\b"
        return re.sub(pattern, "", text, flags=re.IGNORECASE)

    @staticmethod
    def _tighten_full(text: str) -> str:
        # Drop weak modal/auxiliary chains that add no info.
        text = re.sub(r"\byou (can|may|should|could|might|need to)\s+", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\bwe (can|may|should|could|might|need to)\s+", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\bthere (is|are|was|were)\s+", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\bit (is|was)\s+", "", text, flags=re.IGNORECASE)
        # "passing X as a prop" → "passing X as prop" already handled by article drop.
        return text

    @staticmethod
    def _collapse_sentences(text: str) -> str:
        text = re.sub(r"\bwhich (is|are|was|were)\b", "=", text, flags=re.IGNORECASE)
        text = re.sub(r"\bbecause\b", "→", text, flags=re.IGNORECASE)
        text = re.sub(r"\bresults? in\b", "→", text, flags=re.IGNORECASE)
        text = re.sub(r"\bleads? to\b", "→", text, flags=re.IGNORECASE)
        text = re.sub(r"\bcauses?\b", "→", text, flags=re.IGNORECASE)
        text = re.sub(r"\bso that\b", "→", text, flags=re.IGNORECASE)
        return text

    @staticmethod
    def _tighten_ultra(text: str) -> str:
        # Aggressive: collapse "X is Y" definitions into "X = Y" only outside protected ranges.
        text = re.sub(r"\bequals? to\b", "=", text, flags=re.IGNORECASE)
        text = re.sub(r"\bequivalent to\b", "=", text, flags=re.IGNORECASE)
        text = re.sub(r"\bsame as\b", "=", text, flags=re.IGNORECASE)
        # Drop demonstrative+linking openers
        text = re.sub(r"^(this|that|these|those)\s+(means|implies|suggests)\s+(that\s+)?", "", text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    @staticmethod
    def _cleanup_whitespace(text: str) -> str:
        text = re.sub(r" {2,}", " ", text)
        text = re.sub(r" +([,.;:!?])", r"\1", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"^\s+", "", text, flags=re.MULTILINE)
        # Collapse leftover empty parens/brackets/comma chains from drops
        text = re.sub(r"\(\s*\)", "", text)
        text = re.sub(r",\s*,+", ",", text)
        # Strip orphan leading punctuation on each line
        text = re.sub(r"^[,;:\s]+", "", text, flags=re.MULTILINE)
        # Strip orphan punctuation after sentence terminators
        text = re.sub(r"([.!?])\s*[,;:]+\s*", r"\1 ", text)
        # Capitalize after sentence terminator
        text = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
        return text.strip()
