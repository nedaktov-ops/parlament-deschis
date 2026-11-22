#!/usr/bin/env node
/** Every registered route must be nav-reachable, search-reachable, redirect-only, or formally deprecated. */
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "..");
const text = readFileSync(path.join(repo, "frontend/src/router.tsx"), "utf8");
const routes = [...text.matchAll(/path:\s*"([^"]+)"/g)].map((m) => m[1]);
// Four source anchors prove a route is nav-reachable. Each anchor is counted
// independently (the same target may be matched by more than one anchor).
const NAV_ANCHORS = [
  /<NavLink\s+to="([^"]+)"/g,          // 1: <NavLink to="…">
  /\bto="([^"]+)"/g,                    // 2: literal to="…" (incl. <Link to="…">)
  /navigate\(\{\s*to:\s*"([^"]+)"/g,   // 3: navigate({ to: "…" })
  /href="(\/[^"]*)"/g,                  // 4: internal native anchors href="/…"
];
const navTargets = NAV_ANCHORS.flatMap((re) => [...text.matchAll(re)].map((m) => m[1]));
const REACHABLE_OTHERWISE = new Map([
  ["/person/$id", "reachable via global Search (router.tsx:227-231)"],
  ["/electoral", "redirect-only route (router.tsx:322-336)"],
]);
const DEPRECATED_ROUTES = new Map([
  // ["<path>", "<reason + redirect target>"],  // Step 5B entries go here
]);
const normalize = (r) => r.replace(/\/\$[^/]+/g, "");
const linked = routes.filter((r) => {
  const n = normalize(r);
  return navTargets.some((t) => t === n || n === "/" || t.startsWith(`${n}/`));
});
const unlinked = routes.filter((r) => !linked.includes(r)
  && !REACHABLE_OTHERWISE.has(r) && !DEPRECATED_ROUTES.has(r));
console.log(`ROUTES total=${routes.length} nav_links=${navTargets.length} unlinked=${unlinked.length} deprecated=${DEPRECATED_ROUTES.size}`);
for (const r of unlinked) console.log(`  UNLINKED ${r}`);
for (const [r, why] of DEPRECATED_ROUTES) console.log(`  DEPRECATED ${r}: ${why}`);
if (unlinked.length) { console.error("FAIL: routes have no nav link and no deprecation entry"); process.exit(1); }
console.log("PASS: every route is nav-reachable or formally deprecated");
process.exit(0);
