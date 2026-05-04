#!/usr/bin/env node
// SessionStart hook — emits a system-reminder so Brevix mode is active
// from the first turn. Reads ~/.brevix/config.json for the default level.

import fs from "node:fs";
import path from "node:path";
import os from "node:os";

const CONFIG = path.join(os.homedir(), ".brevix", "config.json");

function readConfig() {
  try {
    return JSON.parse(fs.readFileSync(CONFIG, "utf8"));
  } catch {
    return { level: "full", autoActivate: true };
  }
}

function main() {
  const cfg = readConfig();
  if (!cfg.autoActivate) {
    process.stdout.write(JSON.stringify({}) + "\n");
    return;
  }
  const level = cfg.level || "full";
  const message =
    `BREVIX MODE ACTIVE — level: ${level}\n\n` +
    `Apply Brevix compression rules to every response. Drop articles, filler,\n` +
    `pleasantries, and hedging. Fragments OK. Code blocks, commits, and\n` +
    `security-critical text stay normal. Switch with /brevix lite|full|ultra|auto.\n` +
    `Stop with /brevix off, "stop brevix", or "normal mode".`;

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "SessionStart",
        additionalContext: message,
      },
    }) + "\n"
  );
}

main();
