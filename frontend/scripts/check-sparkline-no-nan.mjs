// Regression checker for P0-7: the sparkline normalizer must never emit NaN.
// It compiles the REAL source file (not a copy of the logic) and calls the
// exported `sparklinePoints` on degenerate inputs, including n === 1 (two
// events on the same date -> a one-element series on /person/...).
import { build } from "esbuild";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const cases = [
  { name: "empty", data: [] },
  { name: "single sample (the NaN reproducer)", data: [42] },
  { name: "single zero", data: [0] },
  { name: "two equal samples", data: [5, 5] },
  { name: "normal rising series", data: [1, 2, 3, 4] },
  { name: "flat series", data: [7, 7, 7] },
];

const built = await build({
  entryPoints: ["src/components/DataViz.tsx"],
  bundle: true,
  platform: "node",
  format: "esm",
  jsx: "automatic",
  write: false,
});

const dir = mkdtempSync(join(tmpdir(), "pd-sparkline-"));
const file = join(dir, "DataViz.mjs");
writeFileSync(file, built.outputFiles[0].text);
const { sparklinePoints } = await import(pathToFileURL(file).href);

let failed = false;
for (const { name, data } of cases) {
  const points = sparklinePoints(data);
  const hasNaN = /NaN|Infinity/.test(points);
  // Every emitted coordinate must be a finite number.
  const coords = points.split(" ").filter(Boolean).flatMap((pair) => pair.split(","));
  const allFinite = coords.every((c) => c === "" || Number.isFinite(Number(c)));
  const ok = !hasNaN && allFinite;
  console.log(`${ok ? "OK  " : "FAIL"} ${name}: data=[${data.join(",")}] points="${points}"`);
  if (!ok) failed = true;
}

if (failed) {
  console.log("\nsparkline-no-nan: FAIL (NaN/Infinity found in points)");
  process.exit(1);
}
console.log(`\nsparkline-no-nan: PASS (${cases.length} cases, 0 NaN)`);
