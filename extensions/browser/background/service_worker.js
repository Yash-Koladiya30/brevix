// Brevix MV3 service worker.
// Owns: badge text (live token-saved counter) + message routing between
// popup/options pages and the content scripts.

const STATS_KEY = "brevix_stats";
const SETTINGS_KEY = "brevix_settings";

const DEFAULT_SETTINGS = {
  mode: "full",
  enabled: true,
  showToolbar: true,
  injectOncePerConversation: true,
};

function fmtCounter(tokens) {
  if (!tokens) return "";
  if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}k`;
  return String(tokens);
}

async function refreshBadge() {
  const { [STATS_KEY]: stats } = await chrome.storage.local.get([STATS_KEY]);
  const tokens = stats?.tokensSaved || 0;
  const text = fmtCounter(tokens);
  await chrome.action.setBadgeText({ text });
  if (text) await chrome.action.setBadgeBackgroundColor({ color: "#10B981" });
}

chrome.runtime.onInstalled.addListener(async () => {
  const { [SETTINGS_KEY]: existing } = await chrome.storage.local.get([SETTINGS_KEY]);
  if (!existing) {
    await chrome.storage.local.set({ [SETTINGS_KEY]: DEFAULT_SETTINGS });
  }
  await refreshBadge();
});

// Fallback injection path. The manifest already lists page_inject.js as a
// MAIN-world content script, but some Chrome builds load it after the
// page's own JS has already cached window.fetch, which means our patch
// arrives too late. Re-injecting via chrome.scripting.executeScript with
// injectImmediately:true and world:"MAIN" guarantees the patch runs in
// the page's real JS world before any chat-message POST fires.
const TARGET_URL_RE = /^https:\/\/(claude\.ai|chatgpt\.com|chat\.openai\.com)/;

async function injectPageScript(tabId) {
  try {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["content/page_inject.js"],
      world: "MAIN",
      injectImmediately: true,
    });
  } catch (_) {
    // Silent in production. Failures are non-fatal — the manifest's
    // MAIN-world content_scripts entry is the primary injection path.
  }
}

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (!tab?.url || !TARGET_URL_RE.test(tab.url)) return;
  if (changeInfo.status === "loading") injectPageScript(tabId);
});


chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "local") return;
  if (changes[STATS_KEY]) refreshBadge();
});

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === "brevix:get-settings") {
    chrome.storage.local.get([SETTINGS_KEY]).then(({ [SETTINGS_KEY]: s }) => {
      sendResponse({ settings: { ...DEFAULT_SETTINGS, ...(s || {}) } });
    });
    return true;
  }
  if (msg?.type === "brevix:set-settings") {
    chrome.storage.local.get([SETTINGS_KEY]).then(({ [SETTINGS_KEY]: s }) => {
      const next = { ...DEFAULT_SETTINGS, ...(s || {}), ...(msg.patch || {}) };
      chrome.storage.local.set({ [SETTINGS_KEY]: next }).then(() => {
        sendResponse({ settings: next });
      });
    });
    return true;
  }
  if (msg?.type === "brevix:reset-stats") {
    chrome.storage.local.set({ [STATS_KEY]: undefined }).then(() => {
      refreshBadge();
      sendResponse({ ok: true });
    });
    return true;
  }
  return false;
});
