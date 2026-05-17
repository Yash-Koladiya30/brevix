// chatgpt.com content script.
//
// Brevix v0.2: rule injection happens via the page-world fetch interceptor
// (content/page_inject.js). This file only installs the floating toolbar
// and the response observer; we don't touch the textarea anymore.

(function () {
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

  self.Brevix.installResponseObserver();
  self.Brevix.installStealth();
})();
