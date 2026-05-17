// Brevix popup logic — mode toggle, enable/disable, stats panel.

const $ = (id) => document.getElementById(id);

async function refresh() {
  const stats = await self.BrevixStats.getStats();
  $("tokens-saved").textContent = stats.tokensSaved.toLocaleString();
  $("chars-saved").textContent = stats.charsSaved.toLocaleString();
  $("compressions").textContent = stats.totalCompressions.toLocaleString();

  const settings = await self.BrevixStats.getSettings();
  $("mode").value = settings.mode;
  $("enabled").checked = settings.enabled !== false;
}

document.addEventListener("DOMContentLoaded", async () => {
  await refresh();

  $("mode").addEventListener("change", async (e) => {
    await self.BrevixStats.setSettings({ mode: e.target.value });
  });

  $("enabled").addEventListener("change", async (e) => {
    await self.BrevixStats.setSettings({ enabled: e.target.checked });
  });

  $("reset-stats").addEventListener("click", async () => {
    if (!confirm("Reset Brevix stats? This cannot be undone.")) return;
    await self.BrevixStats.resetStats();
    await refresh();
  });

  $("open-options").addEventListener("click", () => {
    chrome.runtime.openOptionsPage();
  });

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "local") return;
    if (changes.brevix_stats || changes.brevix_settings) refresh();
  });
});
