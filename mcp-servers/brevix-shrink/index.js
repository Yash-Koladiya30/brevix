#!/usr/bin/env node
// brevix-shrink — stdio MCP proxy that compresses tools/list, prompts/list,
// and resources/list response descriptions to save tokens.
//
// Usage:
//   npx brevix-shrink <upstream-command> [args...]
//   e.g. npx brevix-shrink npx -y @modelcontextprotocol/server-filesystem /tmp
//
// Env:
//   BREVIX_SHRINK_FIELDS=description,prompt   override fields to compress
//   BREVIX_SHRINK_DEBUG=1                     log to stderr

import { spawn } from "node:child_process";
import { maybeShrinkResponse } from "./compress.js";

const DEBUG = process.env.BREVIX_SHRINK_DEBUG === "1";
const log = (...a) => DEBUG && process.stderr.write(`[brevix-shrink] ${a.join(" ")}\n`);

const args = process.argv.slice(2);
if (args.length === 0) {
  process.stderr.write(
    "brevix-shrink: missing upstream command.\n" +
      "Usage: brevix-shrink <command> [args...]\n"
  );
  process.exit(2);
}

const [cmd, ...rest] = args;
const child = spawn(cmd, rest, { stdio: ["pipe", "pipe", "inherit"] });

child.on("exit", (code) => process.exit(code ?? 0));
child.on("error", (err) => {
  process.stderr.write(`brevix-shrink: failed to start upstream: ${err.message}\n`);
  process.exit(127);
});

// Track in-flight requests so we know which response method we're shrinking.
const pending = new Map();

const lineSplit = (chunk, buf) => {
  buf.value += chunk.toString("utf8");
  const out = [];
  let idx;
  while ((idx = buf.value.indexOf("\n")) !== -1) {
    out.push(buf.value.slice(0, idx));
    buf.value = buf.value.slice(idx + 1);
  }
  return out;
};

// Client → child: forward verbatim, but remember each request's method.
const reqBuf = { value: "" };
process.stdin.on("data", (chunk) => {
  for (const line of lineSplit(chunk, reqBuf)) {
    const trimmed = line.trim();
    if (!trimmed) {
      child.stdin.write("\n");
      continue;
    }
    try {
      const msg = JSON.parse(trimmed);
      if (msg && msg.id !== undefined && msg.method) {
        pending.set(msg.id, msg);
        log("→", msg.method, msg.id);
      }
    } catch {
      /* not json — passthrough */
    }
    child.stdin.write(line + "\n");
  }
});
process.stdin.on("end", () => child.stdin.end());

// Child → client: compress tools/list etc. responses.
const respBuf = { value: "" };
child.stdout.on("data", (chunk) => {
  for (const line of lineSplit(chunk, respBuf)) {
    const trimmed = line.trim();
    if (!trimmed) {
      process.stdout.write("\n");
      continue;
    }
    let msg;
    try {
      msg = JSON.parse(trimmed);
    } catch {
      process.stdout.write(line + "\n");
      continue;
    }
    if (msg && msg.id !== undefined && pending.has(msg.id)) {
      const req = pending.get(msg.id);
      pending.delete(msg.id);
      maybeShrinkResponse(req, msg);
      log("←", req.method, msg.id, "(shrunk)");
    }
    process.stdout.write(JSON.stringify(msg) + "\n");
  }
});
