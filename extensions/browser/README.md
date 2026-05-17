# Brevix Browser Extension

Compress Claude / ChatGPT chat output 40–75% directly inside the web UI.
No API key needed. 100% local. MV3.

## What it does

`claude.ai` and `chatgpt.com` don't expose API access, so the extension
applies Brevix compression by **prepending a short system-instruction
block** to your first message in each conversation. The model follows the
rules and produces compressed output for the rest of the conversation.

You get:

- A floating toolbar on chat pages (mode toggle, live token-saved counter).
- A popup (click the extension icon) for mode + stats.
- An options page for default mode and behavior toggles.
- A badge on the extension icon with running token savings.

## Load (developer / unpacked)

While we're not yet on the Chrome Web Store / Firefox Add-ons, you can
load the extension directly from this repo:

### Chrome / Edge / Brave

1. Visit `chrome://extensions`.
2. Toggle **Developer mode** (top right).
3. Click **Load unpacked**.
4. Select `extensions/browser/` from this repo.
5. Open https://claude.ai or https://chatgpt.com — the **BREVIX** toolbar
   appears top-right.

### Firefox

1. Visit `about:debugging#/runtime/this-firefox`.
2. Click **Load Temporary Add-on…**.
3. Select `extensions/browser/manifest.json`.
4. Same as above on Claude / ChatGPT.

> Note: temporary add-ons in Firefox are removed on browser restart.
> Permanent install lands when we publish to AMO.

## How to use

1. Load the extension (see above).
2. Open a chat on https://claude.ai or https://chatgpt.com.
3. The toolbar shows the current mode (`off | lite | full | ultra`) and
   running token savings.
4. Pick your mode — the next message you send will include the Brevix
   rule prefix once. Subsequent messages in the same conversation stay
   plain.
5. Type and send normally. The model follows the rules from message #1
   onward.
6. Click the extension icon for popup stats; click **Settings** for
   default mode and behavior toggles.

## Modes

| Mode  | What changes                                   | Typical savings |
|-------|------------------------------------------------|-----------------|
| Lite  | Drops pleasantries, filler, hedges             | 20–30%          |
| Full  | Above + drop articles, allow fragments         | 40–60%          |
| Ultra | Above + arrows, equals, bullets, max terse     | 60–80%          |

Compression is dropped automatically for code blocks, URLs, error
messages, security warnings, and irreversible-action confirmations.

## Privacy

- 100% local. No telemetry. No external network calls.
- All settings + stats are in `chrome.storage.local`.
- The only "external" interaction is the rule prefix that you send to
  Claude / ChatGPT in a normal chat message.

## Limitations (v0.1.0)

- Works on the current claude.ai and chatgpt.com DOM. Both UIs change
  often; small adapter tweaks may be needed when they redesign.
- For sites using contenteditable inputs (claude.ai), the rule prefix is
  inserted as an editable paragraph at the top of your draft. You can
  edit or remove it before sending.
- Re-injection happens automatically when you start a new conversation.
  Use the toolbar `↻` button to re-inject after switching modes
  mid-conversation.

## Roadmap

- [ ] Inline diff view (orig vs compressed) on each AI response
- [ ] Per-domain mode persistence
- [ ] Chrome Web Store + Firefox Add-ons publish
- [ ] CSV / JSON export from popup

## Contributing

Patches welcome. The whole extension is plain JS — no build step. Edit
files in `extensions/browser/`, hit "Update" on
`chrome://extensions`, and reload the chat tab.

## License

MIT — same as the rest of Brevix.
