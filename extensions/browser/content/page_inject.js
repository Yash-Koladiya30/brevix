// Brevix page-world fetch interceptor.
//
// Loaded into the page's main JS world (NOT the isolated content-script world)
// so we can patch the real `window.fetch` that claude.ai / chatgpt.com use to
// send chat messages. When we see an outgoing message POST, we ask the
// content-script side (via postMessage) for the current Brevix rule and
// prepend it to the request body before the original fetch fires.
//
// This bypasses the editor entirely — no DOM mutation, no React fights.

(function () {
  if (window.__brevixPatched) return;
  window.__brevixPatched = true;

  // Quiet by default. Toolbar's status dot already signals "patch live".
  // Set window.__brevixDebug = true in DevTools to enable verbose logs.
  function brevixLog(...args) {
    if (window.__brevixDebug) {
      try { console.log("[Brevix]", ...args); } catch (_) {}
    }
  }
  function brevixWarn(...args) {
    if (window.__brevixDebug) {
      try { console.warn("[Brevix]", ...args); } catch (_) {}
    }
  }
  brevixLog("page-world fetch patch installed");

  // Signal to the isolated-world toolbar that the patch is live, so it
  // can flip its status dot from red to green. Repeated on a heartbeat
  // in case the toolbar arrives after us. CustomEvent on document
  // crosses world boundaries reliably.
  function brevixAnnouncePatch() {
    try {
      document.dispatchEvent(new CustomEvent("brevix:alive"));
    } catch (_) {}
  }
  brevixAnnouncePatch();
  setInterval(brevixAnnouncePatch, 1500);

  const original = window.fetch;

  // Origins we care about. Tight enough to skip analytics/CDN calls.
  const TARGET_HOSTS = /(?:^|\.)(claude\.ai|chatgpt\.com|chat\.openai\.com)$/;

  // URL path patterns for actual chat-message POSTs.
  //
  // Must match (claude.ai): /api/organizations/{org}/chat_conversations/{id}/completion
  // Must match (chatgpt.com): /backend-api/conversation
  // Must NOT match: /title, /event_logging, /notification/channels, /attachments.
  const TARGET_PATHS =
    /\/completion(?:$|\?)|\/append_message(?:$|\?)|\/send_message(?:$|\?)|\/backend-api\/conversation(?:$|\?)|\/v\d+\/messages(?:$|\?)/;

  // Ask the content-script bridge for the rule via DOM CustomEvent.
  // CustomEvents on document cross isolated/main worlds reliably (both
  // worlds see the same DOM); window.postMessage does not in all
  // Chromium builds.
  function getRuleFromBridge() {
    return new Promise((resolve) => {
      const id = "brevix-" + Math.random().toString(36).slice(2);
      let done = false;

      const handler = (e) => {
        if (done) return;
        const detail = e.detail || {};
        if (detail.brevixId !== id) return;
        done = true;
        document.removeEventListener("brevix:rule", handler);
        resolve(detail.rule || null);
      };

      document.addEventListener("brevix:rule", handler);
      document.dispatchEvent(new CustomEvent("brevix:get", {
        detail: { brevixId: id, url: location.href },
      }));

      setTimeout(() => {
        if (done) return;
        done = true;
        document.removeEventListener("brevix:rule", handler);
        resolve(null);
      }, 5000);
    });
  }

  // Walk a parsed JSON body and prepend the rule to the most recent
  // user-authored message. Supports several known shapes; returns the
  // original object unchanged if nothing matches (caller falls back to
  // the unmodified request).
  function tryPrependToBody(obj, rule) {
    if (!obj || typeof obj !== "object") return false;

    // Shape A — claude.ai { prompt: "..." }.
    if (typeof obj.prompt === "string" && obj.prompt.length > 0) {
      obj.prompt = rule + "\n\n" + obj.prompt;
      return true;
    }

    // Shape B — claude.ai newer schema { ..., text: "...", attachments: [], ... }.
    if (typeof obj.text === "string" && obj.text.length > 0) {
      obj.text = rule + "\n\n" + obj.text;
      return true;
    }

    // Shape C — claude.ai { rendering_mode, ..., message: { content, ... } }.
    if (obj.message && typeof obj.message === "object") {
      if (typeof obj.message.content === "string") {
        obj.message.content = rule + "\n\n" + obj.message.content;
        return true;
      }
      if (typeof obj.message.text === "string") {
        obj.message.text = rule + "\n\n" + obj.message.text;
        return true;
      }
    }

    // Shape D — claude.ai / chatgpt.com { messages: [{role:"user",...}] }.
    if (Array.isArray(obj.messages)) {
      for (let i = obj.messages.length - 1; i >= 0; i--) {
        const m = obj.messages[i];
        if (!m) continue;
        const role = m.role || m.author?.role;
        if (role && role !== "user") continue;
        if (typeof m.content === "string") {
          m.content = rule + "\n\n" + m.content;
          return true;
        }
        if (typeof m.text === "string") {
          m.text = rule + "\n\n" + m.text;
          return true;
        }
        if (Array.isArray(m?.content?.parts) && m.content.parts.length > 0) {
          m.content.parts[0] = rule + "\n\n" + (m.content.parts[0] || "");
          return true;
        }
        if (Array.isArray(m.content)) {
          const block = m.content.find((b) => b?.type === "text" && typeof b.text === "string");
          if (block) {
            block.text = rule + "\n\n" + block.text;
            return true;
          }
        }
      }
    }

    // Shape E — claude.ai { completion: { prompt: "..." } } wrapper.
    if (obj.completion && typeof obj.completion === "object") {
      if (typeof obj.completion.prompt === "string") {
        obj.completion.prompt = rule + "\n\n" + obj.completion.prompt;
        return true;
      }
    }

    return false;
  }

  async function readBody(input, init) {
    if (init && typeof init.body === "string") return init.body;
    if (input instanceof Request) {
      try {
        return await input.clone().text();
      } catch (_) {
        return null;
      }
    }
    return null;
  }

  function brevixCommitInjection(url) {
    try {
      document.dispatchEvent(new CustomEvent("brevix:commit", { detail: { url } }));
    } catch (_) {}
  }

  window.fetch = async function patchedFetch(input, init) {
    try {
      const url = typeof input === "string" ? input : (input && input.url) || "";
      const u = new URL(url, location.href);
      if (!TARGET_HOSTS.test(u.hostname)) return original.apply(this, arguments);

      const method = (
        (init && init.method) ||
        (input && input.method) ||
        "GET"
      ).toUpperCase();
      if (method !== "POST") return original.apply(this, arguments);

      // Only consider chat-message endpoints. Skip telemetry, title gen,
      // notification channels, attachments uploads, etc.
      if (!TARGET_PATHS.test(u.pathname)) return original.apply(this, arguments);

      brevixLog("chat POST:", u.pathname);

      const bodyText = await readBody(input, init || {});
      if (!bodyText) return original.apply(this, arguments);

      let parsed;
      try {
        parsed = JSON.parse(bodyText);
      } catch (_) {
        return original.apply(this, arguments);
      }

      const rule = await getRuleFromBridge();
      if (!rule) {
        brevixLog("skip: mode=off or already injected");
        return original.apply(this, arguments);
      }

      const ok = tryPrependToBody(parsed, rule);
      if (!ok) {
        brevixWarn("body shape NOT recognized — keys:", Object.keys(parsed || {}));
        return original.apply(this, arguments);
      }

      // Real injection succeeded — only NOW tell the bridge to mark this
      // conversation as injected.
      brevixCommitInjection(u.pathname);

      const newBody = JSON.stringify(parsed);
      brevixLog("✓ rule injected into", u.pathname, "+" + rule.length, "chars");
      const newInit = {
        ...(init || {}),
        body: newBody,
        method: "POST",
        headers: (init && init.headers) || (input && input.headers) || {},
      };

      // If the original input was a Request, clone its key fields so we
      // don't lose credentials/mode/etc.
      if (input instanceof Request) {
        const reqLike = {
          method: "POST",
          headers: input.headers,
          credentials: input.credentials,
          mode: input.mode,
          cache: input.cache,
          redirect: input.redirect,
          referrer: input.referrer,
          integrity: input.integrity,
          body: newBody,
        };
        return original.call(this, input.url, reqLike);
      }

      return original.call(this, url, newInit);
    } catch (_) {
      return original.apply(this, arguments);
    }
  };
})();
