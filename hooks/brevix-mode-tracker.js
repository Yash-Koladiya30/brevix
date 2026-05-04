#!/usr/bin/env node
// UserPromptSubmit hook — detects /brevix <level> commands and persists the
// active level to ~/.brevix/config.json so the next SessionStart picks it up.

import fs from "node:fs";
import path from "node:path";
import os from "node:os";

const CONFIG_DIR = path.join(os.homedir(), ".brevix");
const CONFIG = path.join(CONFIG_DIR, "config.json");

const VALID = new Set(["lite", "full", "ultra", "auto", "off"]);

function readInput() {
  return new Promise((resolve) => {
    let buf = "";
    process.stdin.on("data", (c) => (buf += c));
    process.stdin.on("end", () => resolve(buf));
  });
}

function loadConfig() {
  try {
    return JSON.parse(fs.readFileSync(CONFIG, "utf8"));
  } catch {
    return { level: "full", autoActivate: true };
  }
}

function saveConfig(cfg) {
  fs.mkdirSync(CONFIG_DIR, { recursive: true });
  fs.writeFileSync(CONFIG, JSON.stringify(cfg, null, 2));
}

function detectMode(prompt) {
  if (!prompt) return null;
  const lower = prompt.trim().toLowerCase();
  if (/^\/brevix\b/.test(lower)) {
    const m = lower.match(/^\/brevix\s+(lite|full|ultra|auto|off)\b/);
    if (m) return m[1];
    return "full";
  }
  if (/(^|\s)stop brevix(\s|$)/.test(lower)) return "off";
  if (/(^|\s)normal mode(\s|$)/.test(lower)) return "off";
  return null;
}

(async () => {
  let payload;
  try {
    payload = JSON.parse(await readInput());
  } catch {
    process.stdout.write(JSON.stringify({}) + "\n");
    return;
  }
  const prompt = payload?.prompt || payload?.user_prompt || "";
  const newLevel = detectMode(prompt);
  if (!newLevel) {
    process.stdout.write(JSON.stringify({}) + "\n");
    return;
  }
  if (!VALID.has(newLevel)) {
    process.stdout.write(JSON.stringify({}) + "\n");
    return;
  }
  const cfg = loadConfig();
  if (newLevel === "off") {
    cfg.autoActivate = false;
  } else {
    cfg.level = newLevel;
    cfg.autoActivate = true;
  }
  saveConfig(cfg);

  const note =
    newLevel === "off"
      ? "Brevix off. Resume normal output."
      : `Brevix: ${newLevel} active.`;
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "UserPromptSubmit",
        additionalContext: note,
      },
    }) + "\n"
  );
})();
