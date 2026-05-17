# Chrome Web Store Listing — Brevix

Copy-paste fields for the Chrome Web Store developer console.

## Name (max 45 chars)

```
Brevix — Compress AI Chat
```

## Summary (max 132 chars)

```
Cut Claude.ai + ChatGPT response length 40-75%. Save tokens. Keep meaning. 100% local, no API key, no telemetry.
```

## Category

```
Productivity
```

## Language

```
English (United States)
```

## Long Description (max 16,000 chars)

```
Brevix compresses the output of claude.ai and chatgpt.com chats — without changing the meaning. Pick a mode, send your prompt, and the assistant replies with the same information in 40–75% fewer tokens.

WHY IT EXISTS

Most LLM responses come padded with pleasantries, filler words, hedges, and verbose phrasing. That padding burns through your context window, your screen real estate, and (if you're a paying user of premium models) your monthly token quota. Brevix asks the model to skip it.

HOW IT WORKS

Brevix injects a short, machine-readable rule prefix into the first message you send in a conversation. The rule tells the assistant to compress its output — drop articles, use fragments, prefer bullets, swap verbose phrases for short ones. The rule is invisible after sending (stealth mode is on by default), but it stays in the conversation context, so every subsequent reply follows the same rules.

THREE COMPRESSION MODES

Lite (≈20-30% savings)
  Drops pleasantries, filler, and hedges. Sentences stay complete.

Full (≈40-60% savings) — default
  Above, plus drops articles, allows fragments, uses short synonyms.

Ultra (≈60-80% savings)
  Above, plus arrows for causation (->), equals for definitions (=),
  heavy use of bullets and fragments.

WHAT BREVIX NEVER TOUCHES

Code blocks, URLs, error messages, technical identifiers, numbers, and units pass through verbatim. Security warnings, irreversible-action confirmations, and ordered procedures stay uncompressed so meaning is never at risk.

KEY FEATURES

- Floating toolbar on every chat page (mode toggle, live token-saved counter, patch status dot)
- Per-conversation injection — the rule ships once, then Claude follows it for every reply
- Stealth mode — hides the rule text from your visible message bubble (on by default)
- Local stats dashboard (chrome.storage only — no server, no telemetry)
- Settings page for default mode, stealth, debug logging
- Works on https://claude.ai and https://chatgpt.com (and chat.openai.com)

PRIVACY

100% local. Brevix does not send anything to any server controlled by us — no telemetry, no analytics, no remote API. The only "external" interaction is the rule prefix that travels in your own chat message to Anthropic / OpenAI as part of a normal request you were sending anyway.

The extension stores:
- Your current mode and toggle settings (chrome.storage.local)
- Cumulative tokens-saved counter (chrome.storage.local)
- Nothing else.

OPEN SOURCE

Brevix is MIT-licensed and developed in the open at
https://github.com/Yash-Koladiya30/brevix

If you find a bug, want a new mode, or have a feature request, open an issue.

PERMISSIONS EXPLAINED

storage           — save your mode and settings locally
activeTab         — read the URL of the current tab so we know which site adapter to load
clipboardWrite    — the "copy rule" button copies the active rule text on demand
scripting + tabs  — inject our fetch patch into claude.ai / chatgpt.com page context
Host permissions  — claude.ai, chatgpt.com, chat.openai.com only

Brevix does not request access to any other site, your browsing history, or any other personal data.

CHANGELOG

0.3.0 — Stealth mode default on, compact rule prefix, debug-mode toggle, production-ready
0.2.x — Fetch-interceptor architecture, MV3 polish
0.1.x — Initial release
```

## Single Purpose

```
Compress AI chat responses on claude.ai and chatgpt.com by injecting a short instruction prefix that asks the assistant to drop filler words and use compact formatting.
```

## Permissions Justification

For each permission requested in manifest.json, the developer console asks "Why do you need this?". Paste these:

### storage
```
Persist the user's chosen compression mode, toolbar visibility, stealth mode, and a local-only running counter of tokens saved. No data leaves the user's browser.
```

### activeTab
```
Determine which site adapter to load (claude.ai vs chatgpt.com) when the toolbar popup opens.
```

### clipboardWrite
```
The toolbar exposes a "copy rule" button so the user can paste the active compression rule into a chat manually if automatic injection ever fails. Clipboard is written only on direct user click.
```

### scripting
```
Inject our fetch interceptor into the main JavaScript world of claude.ai / chatgpt.com so we can prepend the compression rule to outgoing chat messages. The patched fetch ONLY modifies POSTs to known chat-completion endpoints; all other traffic is untouched.
```

### tabs
```
Detect navigations to claude.ai / chatgpt.com so we re-inject the page-world fetch patch immediately on each new conversation. We do not read tab history or content beyond the URL pattern check.
```

### Host permissions (claude.ai, chatgpt.com, chat.openai.com)
```
Brevix only works on these chat-product domains. We don't request <all_urls> or any other origin. The extension does nothing on any other site.
```

## Screenshots to Capture (1280x800 each)

1. **Hero screenshot** — claude.ai with Brevix toolbar visible top-right, mode set to "ultra", showing a compressed assistant response with arrows and bullets. Caption: "Compress Claude responses 60-80% with Ultra mode."

2. **Mode selector** — close-up of the toolbar dropdown open, all 4 modes visible. Caption: "Four modes: off, lite, full, ultra."

3. **Stats panel** — popup open (click the extension icon), showing tokens saved, chars saved, compressions count. Caption: "Local stats — no telemetry, no server."

4. **Stealth in action** — claude.ai user message bubble showing only the user's actual question (with the Brevix rule prefix hidden by stealth mode). Caption: "Stealth mode hides the rule prefix from your chat UI."

5. **Side-by-side** — split screenshot: ChatGPT or claude.ai with mode=off (long reply) and mode=ultra (terse reply) — same prompt, different lengths. Caption: "Same answer. Fewer tokens."

## Promo Tiles (optional but boost ranking)

- 440 × 280 small tile — Brevix logo + tagline "Compress AI Chat"
- 920 × 680 marquee — same but bigger
- 1400 × 560 marquee (featured) — Brevix logo + 2 side-by-side reply snippets (long vs short)

Generate with: same logo asset, add tagline text in your design tool.

## Pricing

```
Free
```

## Regions

```
All regions
```

## Submission Checklist

- [ ] Built ZIP via `bash extensions/browser/build.sh`
- [ ] ZIP size < 10 MB (current: ~56 KB)
- [ ] manifest.json has correct version
- [ ] icons/icon-{16,48,128}.png present and visually verified
- [ ] At least one 1280x800 screenshot uploaded
- [ ] Privacy policy URL set (link to docs/PRIVACY.md or GitHub README anchor)
- [ ] Single Purpose field filled
- [ ] All permissions justified
- [ ] $5 one-time Chrome Web Store developer fee paid
- [ ] Submitted for review (typically 1-3 business days)
