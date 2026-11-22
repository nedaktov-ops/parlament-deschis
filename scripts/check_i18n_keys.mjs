#!/usr/bin/env node
/**
 * i18n key-diff gate. Fails (exit 1) when:
 *   - a literal t("key") call site is missing from ro or en;
 *   - a key is defined in only one locale;
 *   - a dynamic allowlist key is missing from either locale;
 *   - any key is defined twice in one locale.
 * Nested objects (confidence: { … }) are flattened to confidence.<key>.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "..");
const I18N = path.join(repo, "frontend/src/i18n.ts");
const SRC = path.join(repo, "frontend/src");

// Dynamic t() call sites (verified at audit time; keep this list commented with
// its source so a future refactor can update it deliberately):
//  Traseism.tsx:76,797 t(chamber|"deputies"|"senate"), :156,577 t("full"|"partial"|"none")
//  CoverageView.tsx:220 t("full"|"partial"|"none"), ChamberView.tsx:25 t(chamber)
//  MembershipGantt.tsx:54 / About.tsx:230 t(`confidence.${...}`)
//  CitationPopover.tsx:64 TYPE_LABEL map -> confidence.*
//  About.tsx:290 t(row.completeness), LiveFeed.tsx:124 event-label map
//  TimelineChart.tsx:199 t(chamber)
const DYNAMIC_ALLOWLIST = [
  "deputies", "senate", "full", "partial", "none",
  "confidence.official_ledger", "confidence.official_profile",
  "confidence.derived", "confidence.community",
  "joined", "left", "switchGroup", "switchParty", "groupFounded", "groupRenamed",
  "committeeJoined", "committeeLeft", "roleChanged", "mandateStarted",
  "mandateEnded", "event",
];

const fail = (m) => { console.error(`FAIL: ${m}`); process.exit(1); };

function localeBlock(text, open, close) {
  const a = text.indexOf(open);
  if (a < 0) fail(`cannot find ${open} in i18n.ts`);
  const b = text.indexOf(close, a + open.length);
  if (b < 0) fail(`cannot find ${close} after ${open} in i18n.ts`);
  return text.slice(a + open.length, b);
}

function definitions(block) {
  const counts = new Map();
  let nest = null;
  for (const raw of block.split(/\r?\n/)) {
    const line = raw.trim();
    if (/^confidence\s*:\s*\{/.test(line)) { nest = "confidence"; continue; }
    if (nest && /^\},?$/.test(line)) { nest = null; continue; }
    const m = line.match(/^["']([^"']+)["']\s*:/) || line.match(/^([A-Za-z_$][\w$]*)\s*:/);
    if (!m) continue;
    const key = nest ? `${nest}.${m[1]}` : m[1];
    if (key === "translation" || key === "confidence") continue;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return counts;
}

function walk(dir, out = []) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (/\.(ts|tsx)$/.test(e.name) && e.name !== "i18n.ts") out.push(p);
  }
  return out;
}

try {
  const text = readFileSync(I18N, "utf8");
  const ro = definitions(localeBlock(text, "ro: {", "\n  en: {"));
  const en = definitions(localeBlock(text, "\n  en: {", "\n};"));

  const used = new Map();
  for (const file of walk(SRC)) {
    const body = readFileSync(file, "utf8");
    const re = /\bt\(\s*(["'])([^"']+)\1/g;
    let m;
    while ((m = re.exec(body))) {
      if (!used.has(m[2])) used.set(m[2], new Set());
      used.get(m[2]).add(path.relative(repo, file));
    }
  }

  const wanted = new Set([...used.keys(), ...DYNAMIC_ALLOWLIST]);
  const missingRo = [...wanted].filter((k) => !ro.has(k)).sort();
  const missingEn = [...wanted].filter((k) => !en.has(k)).sort();
  const asymmetric = [...new Set([...ro.keys(), ...en.keys()])]
    .filter((k) => ro.has(k) !== en.has(k)).sort();
  const duplicates = [...new Set([...ro.keys(), ...en.keys()])]
    .filter((k) => (ro.get(k) ?? 0) > 1 || (en.get(k) ?? 0) > 1).sort();

  console.log(`I18N KEY DIFF ro=${ro.size} en=${en.size} used=${used.size} dynamic=${DYNAMIC_ALLOWLIST.length}`);
  for (const [name, list] of [
    ["MISSING_IN_RO", missingRo], ["MISSING_IN_EN", missingEn],
    ["ASYMMETRIC_DEFINITIONS", asymmetric], ["DUPLICATE_DEFINITIONS", duplicates],
  ]) {
    console.log(`${name} ${list.length}`);
    for (const k of list.slice(0, 20)) console.log(`  - ${k}`);
    if (list.length > 20) console.log(`  … and ${list.length - 20} more`);
  }
  if (missingRo.length || missingEn.length || asymmetric.length || duplicates.length) {
    fail("i18n key diff is not clean");
  }
  console.log("PASS: i18n key diff clean (0 missing, 0 asymmetric, 0 duplicate)");
  process.exit(0);
} catch (err) {
  fail(err && err.message ? err.message : String(err));
}
