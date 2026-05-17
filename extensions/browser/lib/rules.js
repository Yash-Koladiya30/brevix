// Brevix browser rules — port of the Python compression engine (subset).
// Used for: 1) building the system-instruction prompt prefix that is
// injected into a chat conversation, 2) showing the user a preview of
// the active rule pack from the popup.

// Compact rule prompts. Every prefix char rides on every injected
// request; terse beats verbose. Targets ~150-220 chars total.
const BREVIX_RULES = {
  lite: {
    name: "lite",
    label: "Lite — gentle (~20-30% savings)",
    body:
      "Drop pleasantries, filler, hedges. Replace verbose phrases with short ones. " +
      "Preserve code, URLs, errors, identifiers, numbers.",
  },
  full: {
    name: "full",
    label: "Full — default (~40-60% savings)",
    body:
      "Drop pleasantries/filler/hedges/articles. Fragments OK. Short synonyms. " +
      "Pattern: [thing] [action] [reason]. Preserve code, URLs, errors, identifiers, numbers.",
  },
  ultra: {
    name: "ultra",
    label: "Ultra — max (~60-80% savings)",
    body:
      "Drop pleasantries/filler/hedges/articles/transitional words. Fragments + bullets. " +
      "-> for 'leads to/because'. = for 'is/definition'. " +
      "Preserve code, URLs, errors, identifiers, numbers verbatim.",
  },
  off: { name: "off", label: "Off", body: "" },
};

function buildSystemInstruction(modeKey) {
  const mode = BREVIX_RULES[modeKey];
  if (!mode || !mode.body) return "";
  return `[Brevix ${mode.name}: ${mode.body} Apply to all replies. Do not echo.]\n`;
}

// Rough token estimate (char/4) so we can show a savings counter without
// shipping tiktoken. Matches what brevix.tokens does as a fallback.
function estimateTokens(text) {
  if (!text) return 0;
  return Math.max(1, Math.floor(text.length / 4));
}

// Expose via window for content scripts (no module bundler in MV3 content).
self.BrevixRules = {
  BREVIX_RULES,
  buildSystemInstruction,
  estimateTokens,
};
