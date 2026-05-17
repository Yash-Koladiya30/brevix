// Brevix browser stats — chrome.storage.local persistence.
//
// Stored under key 'brevix_stats':
//   {
//     totalCompressions: int,
//     charsSaved: int,
//     tokensSaved: int,        // rough estimate
//     byMode: { lite, full, ultra, auto, off },
//     byHost: { 'claude.ai': N, 'chatgpt.com': N },
//     firstUsed: ISO,
//     lastUsed: ISO
//   }

const STATS_KEY = "brevix_stats";
const SETTINGS_KEY = "brevix_settings";

const DEFAULT_STATS = {
  totalCompressions: 0,
  charsSaved: 0,
  tokensSaved: 0,
  byMode: { lite: 0, full: 0, ultra: 0, off: 0 },
  byHost: {},
  firstUsed: "",
  lastUsed: "",
};

const DEFAULT_SETTINGS = {
  mode: "full",
  enabled: true,
  showToolbar: true,
  injectOncePerConversation: true,
  stealth: true,
  debug: false,
};

function _ctxValid() {
  try {
    return Boolean(chrome?.runtime?.id);
  } catch (_) {
    return false;
  }
}

async function _getStorage(key, fallback) {
  if (!_ctxValid()) return fallback;
  return new Promise((resolve) => {
    try {
      chrome.storage.local.get([key], (res) => {
        if (chrome.runtime.lastError) return resolve(fallback);
        resolve(res && res[key] ? res[key] : fallback);
      });
    } catch (_) {
      resolve(fallback);
    }
  });
}

async function _setStorage(key, value) {
  if (!_ctxValid()) return;
  return new Promise((resolve) => {
    try {
      chrome.storage.local.set({ [key]: value }, () => {
        // Drain lastError to silence unhandled-promise warnings on context loss.
        void chrome.runtime.lastError;
        resolve();
      });
    } catch (_) {
      resolve();
    }
  });
}

async function getStats() {
  return _getStorage(STATS_KEY, structuredClone(DEFAULT_STATS));
}

async function recordResponse({ originalText, compressedText, mode, host }) {
  const stats = await getStats();
  const now = new Date().toISOString();
  const charSaved = Math.max(0, (originalText?.length || 0) - (compressedText?.length || 0));
  const tokSaved = Math.max(
    0,
    (self.BrevixRules?.estimateTokens(originalText) || 0) -
      (self.BrevixRules?.estimateTokens(compressedText) || 0)
  );
  stats.totalCompressions += 1;
  stats.charsSaved += charSaved;
  stats.tokensSaved += tokSaved;
  stats.byMode[mode] = (stats.byMode[mode] || 0) + 1;
  if (host) stats.byHost[host] = (stats.byHost[host] || 0) + 1;
  if (!stats.firstUsed) stats.firstUsed = now;
  stats.lastUsed = now;
  await _setStorage(STATS_KEY, stats);
  return stats;
}

async function resetStats() {
  await _setStorage(STATS_KEY, structuredClone(DEFAULT_STATS));
}

async function getSettings() {
  const cur = await _getStorage(SETTINGS_KEY, structuredClone(DEFAULT_SETTINGS));
  // Backfill any new settings keys.
  return { ...DEFAULT_SETTINGS, ...cur };
}

async function setSettings(patch) {
  const cur = await getSettings();
  const next = { ...cur, ...patch };
  await _setStorage(SETTINGS_KEY, next);
  return next;
}

self.BrevixStats = {
  STATS_KEY,
  SETTINGS_KEY,
  DEFAULT_STATS,
  DEFAULT_SETTINGS,
  getStats,
  recordResponse,
  resetStats,
  getSettings,
  setSettings,
};
