// Common content-script logic shared between claude.ai and chatgpt.com.
//
// Strategy
// --------
// Web chats don't expose API keys, so the only way to apply Brevix
// compression is to nudge the model via prompt: prepend a short system-
// instruction block to the user's message that tells the model to compress
// its responses for the rest of the conversation.
//
// To avoid bloating every turn, we inject the instruction ONCE per
// conversation (tracked by URL pathname) when injectOncePerConversation
// is true (default). Users can re-inject from the toolbar if they switch
// modes mid-conversation.

const BREVIX_INJECT_FLAG_PREFIX = "brevix_injected:";

// Swallow the noisy "Extension context invalidated" errors that older
// content scripts can throw on a still-open tab after the user reloads
// the unpacked extension. They are harmless — the new content script
// will run on the next page reload anyway.
window.addEventListener("unhandledrejection", (e) => {
  const msg = e.reason?.message || String(e.reason || "");
  if (msg.includes("Extension context invalidated")) e.preventDefault();
});

// Page-world script (content/page_inject.js) is now loaded via the
// manifest's "world": "MAIN" content-script entry, so we don't inject a
// <script> tag from here anymore. That bypassed claude.ai's strict CSP
// which silently blocked our previous src injection.

// Bridge: page world asks for the rule via CustomEvent on document.
// CustomEvents cross isolated/main worlds reliably (window.postMessage
// does NOT in all Chromium builds — that was the bug from v0.2.7).
document.addEventListener("brevix:get", async (e) => {
  const detail = e.detail || {};
  const id = detail.brevixId;
  if (!id) return;

  const respond = (rule) => {
    try {
      document.dispatchEvent(new CustomEvent("brevix:rule", {
        detail: { brevixId: id, rule: rule || null },
      }));
    } catch (_) {}
  };

  if (!brevixContextValid()) return respond(null);

  try {
    const settings = Brevix.getSettingsSync();
    if (!settings || settings.enabled === false || settings.mode === "off") {
      return respond(null);
    }
    if (settings.injectOncePerConversation && (await Brevix.hasInjected())) {
      return respond(null);
    }
    const rule = self.BrevixRules.buildSystemInstruction(settings.mode);
    if (!rule) return respond(null);

    if (window.__brevixDebug) {
      try { console.log("[Brevix:bridge] sending rule mode=" + settings.mode + " len=" + rule.length); } catch (_) {}
    }
    respond(rule);
  } catch (_) {
    respond(null);
  }
});

document.addEventListener("brevix:commit", async () => {
  if (!brevixContextValid()) return;
  try {
    const settings = await Brevix.getSettings();
    if (settings && settings.injectOncePerConversation) {
      await Brevix.markInjected();
    }
  } catch (_) {}
});

// Warm the settings cache on content-script start and keep it fresh.
// Settings are tiny; loading is one storage read.
(async () => {
  try { await Brevix.refreshSettings(); } catch (_) {}
})();

if (brevixContextValid()) {
  try {
    chrome.storage.onChanged.addListener((changes, area) => {
      if (area !== "local") return;
      if (changes.brevix_settings) {
        Brevix.state.settings = {
          ...self.BrevixStats.DEFAULT_SETTINGS,
          ...(changes.brevix_settings.newValue || {}),
        };
      }
    });
  } catch (_) {}
}

// True when the extension is still attached to this page. Once the user
// reloads the unpacked extension, old content scripts keep running but
// `chrome.runtime.id` becomes undefined; every `chrome.*` call after that
// throws "Extension context invalidated". We swallow those silently.
function brevixContextValid() {
  try {
    return Boolean(chrome?.runtime?.id);
  } catch (_) {
    return false;
  }
}

function brevixSafe(promiseFactory, fallback = undefined) {
  if (!brevixContextValid()) return Promise.resolve(fallback);
  try {
    return promiseFactory().catch(() => fallback);
  } catch (_) {
    return Promise.resolve(fallback);
  }
}

const Brevix = {
  state: {
    // Cached settings; refreshed each time we need to inject.
    settings: null,
    host: location.hostname.replace(/^www\./, ""),
  },

  async getSettings() {
    if (this.state.settings) return this.state.settings;
    const cur = await brevixSafe(() => self.BrevixStats.getSettings(), self.BrevixStats.DEFAULT_SETTINGS);
    this.state.settings = cur;
    return cur;
  },

  async refreshSettings() {
    this.state.settings = await brevixSafe(
      () => self.BrevixStats.getSettings(),
      self.BrevixStats.DEFAULT_SETTINGS
    );
    return this.state.settings;
  },

  // Sync settings accessor for hot-path bridge calls. Returns the cached
  // value (or DEFAULT_SETTINGS if cache not warmed yet). Cache is kept
  // fresh by chrome.storage.onChanged below.
  getSettingsSync() {
    return this.state.settings || self.BrevixStats.DEFAULT_SETTINGS;
  },

  conversationId() {
    // claude.ai: /chat/<uuid> ; chatgpt.com: /c/<uuid>
    const m = location.pathname.match(/\/(chat|c)\/([\w-]+)/);
    return m ? m[2] : "default";
  },

  injectKey() {
    return BREVIX_INJECT_FLAG_PREFIX + this.state.host + ":" + this.conversationId();
  },

  // In-memory injection tracker. chrome.storage.session is denied to
  // content scripts on claude.ai without a setAccessLevel call, and a
  // chrome.storage.local flag would persist across tab reloads and stale
  // forever. A plain Set on the content-script side is the simplest fit:
  // it lives exactly as long as this tab session, which matches what we
  // want — a per-tab, per-conversation "injected once" flag.
  async hasInjected() {
    if (!this._injectedSet) this._injectedSet = new Set();
    return this._injectedSet.has(this.injectKey());
  },

  async markInjected() {
    if (!this._injectedSet) this._injectedSet = new Set();
    this._injectedSet.add(this.injectKey());
  },

  async resetInjected() {
    if (!this._injectedSet) this._injectedSet = new Set();
    this._injectedSet.delete(this.injectKey());
  },

  async maybePrependInstruction(userText) {
    const settings = await this.getSettings();
    if (!settings.enabled || settings.mode === "off") return userText;

    const instruction = self.BrevixRules.buildSystemInstruction(settings.mode);
    if (!instruction) return userText;

    if (settings.injectOncePerConversation && (await this.hasInjected())) {
      return userText;
    }

    await this.markInjected();
    return `${instruction}\n${userText}`;
  },

  // Stealth mode — hide Brevix rule prefix from rendered user-message
  // bubbles so the user doesn't see the rule text cluttering their own
  // messages. The rule still rides in the outbound API request body.
  installStealth() {
    if (!brevixContextValid()) return;
    const settings = Brevix.getSettingsSync ? Brevix.getSettingsSync() : null;
    if (settings && settings.stealth === false) return;

    const BREVIX_PREFIX_RE = /^\s*\[Brevix\s+(lite|full|ultra)\b/;

    // Walk a DOM node and hide any text-bearing element whose own text
    // starts with `[Brevix ...]`. We hide the closest standalone block
    // (p / li / div) so layout collapses cleanly.
    const hideBrevixIn = (root) => {
      if (!root || !root.querySelectorAll) return;
      // Look at common user-message containers used by claude.ai +
      // chatgpt.com. Conservative: only act on <p>/<div> with our marker.
      const candidates = root.querySelectorAll("p, div, li, span");
      for (const el of candidates) {
        if (el.dataset.brevixHidden) continue;
        const txt = el.textContent || "";
        if (!BREVIX_PREFIX_RE.test(txt)) continue;
        // Only hide if THIS element's own first text node carries the
        // marker — not deeper containers — so we don't nuke whole bubbles.
        const firstText = (el.firstChild && el.firstChild.textContent) || "";
        if (!BREVIX_PREFIX_RE.test(firstText) && !BREVIX_PREFIX_RE.test(txt.slice(0, 200))) continue;
        el.style.display = "none";
        el.dataset.brevixHidden = "1";
      }
    };

    const obs = new MutationObserver((mutations) => {
      for (const m of mutations) {
        for (const n of m.addedNodes) {
          if (n instanceof HTMLElement) hideBrevixIn(n);
        }
      }
    });

    const start = () => {
      const root = document.querySelector("main") || document.body;
      obs.observe(root, { childList: true, subtree: true });
      hideBrevixIn(root); // sweep existing
    };
    if (document.body) start();
    else window.addEventListener("DOMContentLoaded", start);
  },

  // Permissive response observer. Selectors for assistant messages on
  // claude.ai / chatgpt.com change often; instead of locking onto a
  // specific data-testid, watch the whole main-content tree for new
  // text-bearing nodes added after the user clicks send.
  //
  // Heuristic: when the send button is clicked, capture the current
  // text length of the transcript. After the user's message lands and
  // the assistant streams its reply, the transcript's text length grows.
  // The growth between send-click and the next 2-second-quiet moment is
  // the assistant response length. We then estimate what the
  // uncompressed length would have been (mode-specific ratio) and record
  // tokens saved.
  installResponseObserver() {
    const ratios = { lite: 1.3, full: 1.7, ultra: 2.5, off: 1.0 };

    // Find the largest element that holds the chat transcript. Both
    // claude.ai and chatgpt.com put it inside <main>, but fall back to
    // <body> if main is absent.
    const transcriptRoot = () => document.querySelector("main") || document.body;

    let baseline = 0;
    let observerActive = false;
    let settleTimer = null;

    const recordIfPossible = async (deltaChars) => {
      if (deltaChars <= 20) return; // ignore noise
      const settings = await this.getSettings();
      if (!settings.enabled || settings.mode === "off") return;
      const ratio = ratios[settings.mode] || 1.0;
      const wouldBeChars = Math.round(deltaChars * ratio);
      try {
        const stats = await self.BrevixStats.recordResponse({
          originalText: "x".repeat(wouldBeChars),
          compressedText: "x".repeat(deltaChars),
          mode: settings.mode,
          host: this.state.host,
        });
        if (window.__brevixDebug) {
          try { console.log("[Brevix:stats] +" + (wouldBeChars - deltaChars) + " tok saved, total=" + stats.tokensSaved); } catch (_) {}
        }
      } catch (_) { /* context lost */ }
    };

    const armCapture = () => {
      const root = transcriptRoot();
      if (!root) return;
      baseline = (root.innerText || "").length;
      observerActive = true;

      const obs = new MutationObserver(() => {
        if (!observerActive) return;
        clearTimeout(settleTimer);
        settleTimer = setTimeout(async () => {
          observerActive = false;
          const after = (root.innerText || "").length;
          const delta = after - baseline;
          await recordIfPossible(delta);
          obs.disconnect();
        }, 2000);
      });
      obs.observe(root, { childList: true, subtree: true, characterData: true });
    };

    // Hook send button + Enter to start a new capture window.
    document.addEventListener(
      "click",
      (e) => {
        const btn = e.target.closest?.("button");
        if (!btn) return;
        const label = (btn.getAttribute("aria-label") || btn.textContent || "").toLowerCase();
        const isSend =
          label.includes("send") ||
          btn.getAttribute("data-testid") === "send-button" ||
          btn.type === "submit";
        if (isSend) armCapture();
      },
      true
    );

    document.addEventListener(
      "keydown",
      (e) => {
        if (e.key === "Enter" && !e.shiftKey) armCapture();
      },
      true
    );
  },

  installToolbar() {
    if (document.getElementById("brevix-toolbar")) return;
    const div = document.createElement("div");
    div.id = "brevix-toolbar";
    div.className = "brevix-toolbar";
    div.innerHTML = `
      <span class="brevix-status" id="brevix-status" title="Patch loading...">●</span>
      <span class="brevix-tag">BREVIX</span>
      <select id="brevix-mode" class="brevix-mode">
        <option value="off">off</option>
        <option value="lite">lite</option>
        <option value="full">full</option>
        <option value="ultra">ultra</option>
      </select>
      <span id="brevix-saved" class="brevix-saved">0 tok saved</span>
      <button id="brevix-copy" class="brevix-btn" title="Copy rule to clipboard — paste at top of your first message">📋</button>
      <button id="brevix-reinject" class="brevix-btn" title="Re-inject rule on next send">↻</button>
    `;
    document.documentElement.appendChild(div);

    const sel = div.querySelector("#brevix-mode");
    const saved = div.querySelector("#brevix-saved");
    const reinject = div.querySelector("#brevix-reinject");
    const copyBtn = div.querySelector("#brevix-copy");
    const statusDot = div.querySelector("#brevix-status");

    // Status dot: red until page_inject.js confirms it's alive, then green.
    let aliveSeenAt = 0;
    const setStatus = (live) => {
      if (live) {
        statusDot.classList.add("live");
        statusDot.classList.remove("dead");
        statusDot.title = "Brevix patch live — chat output will be compressed";
      } else {
        statusDot.classList.add("dead");
        statusDot.classList.remove("live");
        statusDot.title = "Brevix patch NOT loaded — output won't be compressed";
      }
    };
    setStatus(false);

    document.addEventListener("brevix:alive", () => {
      aliveSeenAt = Date.now();
      setStatus(true);
    });

    // If no heartbeat for 4s, flip back to red.
    setInterval(() => {
      if (Date.now() - aliveSeenAt > 4000) setStatus(false);
    }, 2000);

    copyBtn.addEventListener("click", async () => {
      const s = await this.getSettings();
      const rule = self.BrevixRules.buildSystemInstruction(s.mode || "full");
      if (!rule) {
        copyBtn.textContent = "off";
        setTimeout(() => (copyBtn.textContent = "📋"), 800);
        return;
      }
      try {
        await navigator.clipboard.writeText(rule);
        copyBtn.textContent = "✓";
        setTimeout(() => (copyBtn.textContent = "📋"), 1200);
      } catch (_) {
        copyBtn.textContent = "✗";
        setTimeout(() => (copyBtn.textContent = "📋"), 1200);
      }
    });

    this.getSettings().then((s) => {
      sel.value = s.mode;
    });
    self.BrevixStats.getStats().then((st) => {
      saved.textContent = `${st.tokensSaved} tok saved`;
    });

    sel.addEventListener("change", async (e) => {
      const next = await self.BrevixStats.setSettings({ mode: e.target.value });
      this.state.settings = next;
      await this.resetInjected();
    });

    reinject.addEventListener("click", async () => {
      await this.resetInjected();
      reinject.textContent = "✓";
      setTimeout(() => (reinject.textContent = "↻"), 800);
    });

    if (brevixContextValid()) {
      try {
        chrome.storage.onChanged.addListener((changes, area) => {
          if (!brevixContextValid()) return;
          if (area !== "local") return;
          if (changes.brevix_stats) {
            const tok = changes.brevix_stats.newValue?.tokensSaved || 0;
            saved.textContent = `${tok} tok saved`;
          }
          if (changes.brevix_settings?.newValue?.mode) {
            sel.value = changes.brevix_settings.newValue.mode;
          }
        });
      } catch (_) { /* context already gone */ }
    }
  },
};

self.Brevix = Brevix;
