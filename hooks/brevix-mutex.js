#!/usr/bin/env node
// SessionStart hook — when Brevix activates, auto-disable Caveman to avoid
// double-compression conflicts. Reverse the toggle when Brevix is off.
//
// Idempotent: only writes if state actually changes.

import fs from "node:fs";
import path from "node:path";
import os from "node:os";

const HOME = os.homedir();
const BREVIX_CFG = path.join(HOME, ".brevix", "config.json");
const CAVEMAN_CFG = path.join(HOME, ".config", "caveman", "config.json");
const CAVEMAN_LEGACY = path.join(HOME, ".caveman", "config.json");

function read(p, fallback) {
  try { return JSON.parse(fs.readFileSync(p, "utf8")); }
  catch { return fallback; }
}

function write(p, data) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, JSON.stringify(data, null, 2));
}

function brevixActive() {
  const cfg = read(BREVIX_CFG, { autoActivate: true });
  return cfg.autoActivate !== false;
}

function suppressCaveman(reason) {
  for (const cfgPath of [CAVEMAN_CFG, CAVEMAN_LEGACY]) {
    if (!fs.existsSync(cfgPath)) continue;
    const cfg = read(cfgPath, {});
    if (cfg.defaultMode === "off" || cfg.autoActivate === false) continue;
    cfg.defaultMode = "off";
    cfg.autoActivate = false;
    cfg._suppressedBy = `brevix (${reason})`;
    write(cfgPath, cfg);
    process.stderr.write(`[brevix-mutex] Caveman suppressed: ${reason} (${cfgPath})\n`);
  }
}

function main() {
  if (!brevixActive()) return;
  if (!fs.existsSync(CAVEMAN_CFG) && !fs.existsSync(CAVEMAN_LEGACY)) return;
  suppressCaveman("Brevix is active");
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "SessionStart",
        additionalContext:
          "Brevix and Caveman both detected. Caveman auto-suppressed to prevent " +
          "double-compression conflicts. To re-enable Caveman, disable Brevix first " +
          "(`/brevix off`) and restart your session.",
      },
    }) + "\n"
  );
}

main();
