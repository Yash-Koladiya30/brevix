// Minimal output-prose compressor for MCP description fields.
// Mirrors Brevix's full-mode rule set, kept tiny for proxy hot-path use.
// Does NOT touch code, URLs, error quotes, or technical identifiers.

const CODE_FENCE = /```[\s\S]*?```/g;
const INLINE_CODE = /`[^`\n]+`/g;
const URL_RE = /(https?:\/\/\S+|www\.\S+)/g;
const ERROR_QUOTE = /"[^"\n]*(?:Error|Exception|Warning|Failed|Traceback)[^"\n]*"/gi;

const PLEASANTRIES = [
  /\b(?:i(?:'d| would| am| ?'m)?\s+(?:be\s+)?)?(?:happy|glad|pleased|delighted)\s+to\s+(?:help|assist|explain|show|walk|guide|take a look)\b[^.!?]*[.!?]/gi,
  /\b(?:sure|certainly|of course|absolutely|gladly)\b[,!.\s]+/gi,
  /\b(?:great|good|excellent)\s+(?:question|point|catch|observation)\b[!.\s]*/gi,
  /\bhope (?:this|that) helps\b[!.\s]*/gi,
  /\bplease (?:note|be aware|keep in mind)\s+(?:that\s+)?/gi,
];
const HEDGES = [
  /\bit\s+(?:seems|appears|looks|might be|could be)\s+(?:that|like)?\s*/gi,
  /\bi\s+(?:think|believe|suppose|guess|assume)\s+(?:that\s+)?/gi,
  /\bin my opinion\b,?\s*/gi,
  /\bgenerally speaking\b,?\s*/gi,
];
const VERBOSE = [
  [/\bin order to\b/gi, "to"],
  [/\bdue to the fact that\b/gi, "because"],
  [/\bat this point in time\b/gi, "now"],
  [/\bin the event that\b/gi, "if"],
  [/\bfor the purpose of\b/gi, "to"],
  [/\bmake use of\b/gi, "use"],
  [/\bin spite of the fact that\b/gi, "though"],
  [/\ba large number of\b/gi, "many"],
  [/\bthe majority of\b/gi, "most"],
  [/\bprior to\b/gi, "before"],
  [/\bsubsequent to\b/gi, "after"],
];
const FILLER = /\b(?:just|really|basically|actually|simply|very|quite|perhaps|maybe|essentially|literally|obviously|clearly|definitely|absolutely)\b/gi;
const ARTICLES = /\b(?:a|an|the)\b/gi;

export function compressProse(text) {
  if (!text || typeof text !== "string") return text;
  const stash = [];
  const stashFn = (m) => {
    const k = `__BRVX_${stash.length}__`;
    stash.push(m);
    return k;
  };
  let t = text
    .replace(CODE_FENCE, stashFn)
    .replace(INLINE_CODE, stashFn)
    .replace(URL_RE, stashFn)
    .replace(ERROR_QUOTE, stashFn);

  for (const re of PLEASANTRIES) t = t.replace(re, "");
  for (const re of HEDGES) t = t.replace(re, "");
  for (const [re, rep] of VERBOSE) t = t.replace(re, rep);
  t = t.replace(FILLER, "");
  t = t.replace(ARTICLES, "");
  t = t.replace(/ {2,}/g, " ").replace(/ +([,.;:!?])/g, "$1").replace(/^[,;:\s]+/gm, "").trim();

  for (let i = stash.length - 1; i >= 0; i--) {
    t = t.replace(`__BRVX_${i}__`, stash[i]);
  }
  return t;
}

const SHRINK_FIELDS = (process.env.BREVIX_SHRINK_FIELDS || "description,prompt,instructions")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

export function shrinkRecord(rec) {
  if (!rec || typeof rec !== "object") return rec;
  for (const key of Object.keys(rec)) {
    const val = rec[key];
    if (SHRINK_FIELDS.includes(key) && typeof val === "string") {
      rec[key] = compressProse(val);
    } else if (Array.isArray(val)) {
      rec[key] = val.map(shrinkRecord);
    } else if (val && typeof val === "object") {
      rec[key] = shrinkRecord(val);
    }
  }
  return rec;
}

const SHRINK_RESULTS_FOR = new Set([
  "tools/list",
  "prompts/list",
  "resources/list",
  "resources/templates/list",
]);

export function maybeShrinkResponse(req, response) {
  if (!response || !req || !req.method) return response;
  if (!SHRINK_RESULTS_FOR.has(req.method)) return response;
  if (!response.result) return response;
  shrinkRecord(response.result);
  return response;
}
