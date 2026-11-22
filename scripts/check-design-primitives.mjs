import { readFileSync } from "node:fs";
import { join } from "node:path";

const ROOT = process.cwd(); // run from /home/nedaktov/parlament-deschis
const read = (rel) => readFileSync(join(ROOT, rel), "utf8");
const rules = [];
const forbid = (file, needle, why) =>
  rules.push({ ok: !read(file).includes(needle), label: `${file}: no ${JSON.stringify(needle)} (${why})` });
const need = (file, needle, why) =>
  rules.push({ ok: read(file).includes(needle), label: `${file}: has ${JSON.stringify(needle)} (${why})` });

const hero = "frontend/src/components/HeroGraphic.tsx";
const viz = "frontend/src/components/DataViz.tsx";
const radial = "frontend/src/components/AgeDistributionRadial.tsx";
const grafice = "frontend/src/pages/Grafice.tsx";
const topuri = "frontend/src/pages/Topuri.tsx";
const css = "frontend/src/index.css";
const card = "frontend/src/components/DashboardCard.tsx";

for (const bare of ['"sky-400"', '"amber-400"', '"emerald-400"', '"rose-400"'])
  forbid(hero, `primary: ${bare}`, "bare Tailwind step is not a generated class");
need(hero, 'primary: "text-sky-400"', "literal class visible to Tailwind JIT");
need(hero, 'primary: "text-rose-400"', "literal class visible to Tailwind JIT");
forbid(hero, "text-${", "dynamic class construction invisible to Tailwind JIT");
forbid(hero, "as string", "cast no longer needed once primary is a real class");

forbid(viz, 'color = "bg-sky-400/70"', "class-in-className API removed");
need(viz, "tone?: DataBarTone", "DataBar uses a closed semantic tone");
forbid(viz, 'stroke="slate-700/40"', "invalid SVG paint");
forbid(viz, 'fill="slate-200"', "invalid SVG paint");
need(viz, 'stroke="rgb(var(--slate-700) / 0.4)"', "valid track paint");
need(viz, 'fill="rgb(var(--slate-200))"', "valid text paint");
forbid(grafice, 'color="#', "no hex in className");
forbid(topuri, 'color="#', "no hex in className");
forbid(topuri, "LOYALTY_COLOR", "helper replaced by tone mapper");
need(grafice, 'tone="success"', "Grafice yes-bar uses a semantic tone");

forbid(radial, 'viewBox="0 0 200 200"', "static viewBox clips 250-unit geometry");
need(radial, "viewBox={`0 0 ${width} ${height}`}", "viewBox follows props");
forbid(radial, "rgba(167, 139, 250", "off-palette violet");
forbid(radial, "rgba(236, 72, 153", "off-palette pink");
forbid(radial, 'fill="white"', "theme-blind text");
need(radial, 'fill="rgb(var(--slate-100))"', "theme-aware text");

forbid(css, ".text-violet-400", "off-palette light override");
forbid(css, ".text-cyan-400", "off-palette light override");
forbid(css, "--color-accent-hover: #22d3ee", "cyan accent hover");
forbid(css, "border-top-color: #38bdf8", "hardcoded stat accent");
forbid(card, '"violet"', "off-palette card variant");
forbid(card, '"cyan"', "off-palette card variant");
for (const t of ["accent", "success", "warning", "danger", "info"])
  need(css, `--${t}-rgb:`, "token exists");

let failed = 0;
for (const r of rules) {
  console.log(`[${r.ok ? "PASS" : "FAIL"}] ${r.label}`);
  if (!r.ok) failed++;
}
console.log(`\nDESIGN PRIMITIVE GUARD: ${rules.length - failed}/${rules.length} rules pass`);
if (failed) {
  console.log("GUARD FAIL");
  process.exit(1);
}
console.log("GUARD PASS");
