const $ = (id) => document.getElementById(id);

async function load() {
  const s = await self.BrevixStats.getSettings();
  $("mode").value = s.mode;
  $("enabled").checked = s.enabled !== false;
  $("showToolbar").checked = s.showToolbar !== false;
  $("injectOnce").checked = s.injectOncePerConversation !== false;
  $("stealth").checked = s.stealth !== false;
}

document.addEventListener("DOMContentLoaded", async () => {
  await load();

  $("mode").addEventListener("change", (e) =>
    self.BrevixStats.setSettings({ mode: e.target.value })
  );
  $("enabled").addEventListener("change", (e) =>
    self.BrevixStats.setSettings({ enabled: e.target.checked })
  );
  $("showToolbar").addEventListener("change", (e) =>
    self.BrevixStats.setSettings({ showToolbar: e.target.checked })
  );
  $("injectOnce").addEventListener("change", (e) =>
    self.BrevixStats.setSettings({ injectOncePerConversation: e.target.checked })
  );
  $("stealth").addEventListener("change", (e) =>
    self.BrevixStats.setSettings({ stealth: e.target.checked })
  );
});
