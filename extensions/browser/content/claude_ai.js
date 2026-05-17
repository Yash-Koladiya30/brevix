// claude.ai content script.
//
// Brevix v0.2: rule injection happens via the page-world fetch interceptor
// (content/page_inject.js). This file only installs the floating toolbar
// and the response observer; we don't touch the editor anymore.

(function () {
  // Reset injection flag whenever the conversation URL changes so a new
  // chat gets a fresh rule prefix on its first send.
  let lastPath = location.pathname;
  setInterval(() => {
    if (location.pathname !== lastPath) {
      lastPath = location.pathname;
      try { self.Brevix.resetInjected(); } catch (_) {}
    }
  }, 1000);

  function installToolbarSafely() {
    if (document.body) self.Brevix.installToolbar();
    else setTimeout(installToolbarSafely, 100);
  }
  installToolbarSafely();

  // Response observer — captures assistant responses to update stats.
  self.Brevix.installResponseObserver();

  // Stealth — hide injected rule prefix from rendered user bubbles.
  self.Brevix.installStealth();
})();
