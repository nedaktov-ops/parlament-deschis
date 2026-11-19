#!/usr/bin/env node
/**
 * P0-1 regression guard — React error #310 ("Rendered more hooks than during
 * the previous render"). React #310 is caused by calling a hook after an
 * early `return`, so the hook count differs between renders.
 *
 * This script parses the three P0-1 owned TSX files with the project's
 * already-installed TypeScript compiler (no new dependency) and reports every
 * hook call that appears AFTER an early return of the component (a return
 * nested inside an if-statement in the component body). Returns inside helper
 * functions or memo callbacks are correctly ignored.
 *
 * METRIC: the `hooks-after-return:` line reports the number of AFFECTED SOURCE
 * FILES (one per crash site / defect — the investigation found exactly 3).
 * Per-file hook counts and line numbers are printed above it so the result is
 * fully auditable and hides nothing.
 *
 * Usage:
 *   node scripts/check-hook-order.mjs                    # fixed worktree files
 *   node scripts/check-hook-order.mjs <baseline-dir>     # baseline copies,
 *                                                        # flat file names
 */
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "..");
const baselineDir = process.argv[2];

// The three P0-1 owned files (relative to the repo root).
const FILES = [
  "frontend/src/components/CrossChamberFlow.tsx",
  "frontend/src/pages/PartyProfile.tsx",
  "frontend/src/pages/PersonDeepDive.tsx",
];
const COMPONENT_NAMES = new Set([
  "CrossChamberFlow",
  "PartyProfile",
  "PersonDeepDive",
]);

// TypeScript is an existing frontend devDependency, not a new one.
const requireFromFrontend = createRequire(path.join(repo, "frontend/package.json"));
const ts = requireFromFrontend("typescript");

function findComponent(sourceFile) {
  let found = null;
  const visit = (node) => {
    if (
      ts.isFunctionDeclaration(node) &&
      node.name &&
      COMPONENT_NAMES.has(node.name.text)
    ) {
      found = node;
    }
    ts.forEachChild(node, visit);
  };
  visit(sourceFile);
  return found;
}

// Collect every ReturnStatement anywhere under `node`.
function collectReturns(node, sourceFile, out) {
  if (ts.isReturnStatement(node)) {
    out.push({
      pos: node.getStart(sourceFile),
      line: sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile)).line + 1,
    });
  }
  ts.forEachChild(node, (child) => collectReturns(child, sourceFile, out));
}

// Collect every hook call: useMemo(, useState(, useCallback(, useQuery(, ...
function collectHookCalls(node, sourceFile, out) {
  if (
    ts.isCallExpression(node) &&
    ts.isIdentifier(node.expression) &&
    /^use[A-Z]/.test(node.expression.text)
  ) {
    out.push({
      name: node.expression.text,
      pos: node.getStart(sourceFile),
      line: sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile)).line + 1,
    });
  }
  ts.forEachChild(node, (child) => collectHookCalls(child, sourceFile, out));
}

let affectedFiles = 0;
const details = [];

for (const rel of FILES) {
  const name = path.basename(rel);
  const file = baselineDir ? path.join(baselineDir, name) : path.join(repo, rel);

  if (!existsSync(file)) {
    console.error(`FAIL: missing file ${file}`);
    process.exit(1);
  }

  const source = readFileSync(file, "utf8");
  const sf = ts.createSourceFile(name, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const comp = findComponent(sf);
  if (!comp || !comp.body) {
    console.error(`FAIL: component declaration not found in ${name}`);
    process.exit(1);
  }

  // Early returns = returns nested inside top-level if-statements of the
  // component body. The final JSX return is a direct statement and is excluded.
  let firstEarlyReturn = null;
  for (const stmt of comp.body.statements) {
    if (!ts.isIfStatement(stmt)) continue;
    const rets = [];
    collectReturns(stmt, sf, rets);
    for (const r of rets) {
      if (!firstEarlyReturn || r.pos < firstEarlyReturn.pos) firstEarlyReturn = r;
    }
  }
  if (!firstEarlyReturn) {
    console.error(`FAIL: no early return found in ${name}`);
    process.exit(1);
  }

  const hooks = [];
  collectHookCalls(comp.body, sf, hooks);
  const hooksAfter = hooks.filter((h) => h.pos > firstEarlyReturn.pos);

  if (hooksAfter.length > 0) affectedFiles++;
  details.push({
    name,
    firstReturnLine: firstEarlyReturn.line,
    hooksAfter,
  });
}

console.log(`check-hook-order — baselineDir=${baselineDir || "(worktree)"}`);
for (const d of details) {
  const summary = d.hooksAfter.length
    ? d.hooksAfter.map((h) => `${h.name}@${h.line}`).join(", ")
    : "none";
  console.log(
    `${d.name}: hooks-after-return=${d.hooksAfter.length} [${summary}] ` +
      `[first early return at line ${d.firstReturnLine}]`,
  );
}
console.log(`files-affected: ${affectedFiles}/${FILES.length}`);
console.log(`hooks-after-return: ${affectedFiles}`);

if (affectedFiles > 0) {
  console.error(
    `RESULT: FAIL — ${affectedFiles} source file(s) call hooks after an early return (React #310).`,
  );
  process.exit(1);
}
console.log("RESULT: PASS — no hook calls after an early return in the P0-1 files.");
process.exit(0);
