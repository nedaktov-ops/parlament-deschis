---
id: R-01-DESIGN-SYSTEM
type: repair-recipe
title: "R-01 — Design-system primitives repair (HeroGraphic, DataBar, ProgressRing, AgeDistributionRadial, token utilities)"
status: ready-for-implementation
authority: proposal
baseline: eb693b4d9faf558b22925fdb07ba6d118d7f6cef
created: 2026-11-21
inputs:
  - "Parlament Deschis Obsidian vault/40-FRONTEND/TRIAD-AUDIT-2026-11-21.md"
  - "Parlament Deschis Obsidian vault/40-FRONTEND/FRONTEND-AUDIT-2026-11-21.md"
  - "Parlament Deschis Obsidian vault/40-FRONTEND/DESIGN-CONTRACT.md"
  - frontend/src/components/HeroGraphic.tsx
  - frontend/src/components/DataViz.tsx
  - frontend/src/components/AgeDistributionRadial.tsx
  - frontend/src/components/ui/AgeDistributionSection.tsx
  - frontend/src/index.css
  - frontend/tailwind.config.js
---

# R-01 — Design-system primitives repair

> **This document is a strategy + implementation recipe, not an implementation.**
> The authoring subagent was READ-ONLY on product code. Every `path:line` below was
> read from the tree at baseline `eb693b4`. A static-code finding is not an observed
> browser defect; see **NOT PROVEN** at the end before claiming success.

---

## 1. Objective

Repair the four broken shared visual primitives and give the app one token-backed
utility vocabulary, so that:

1. Every `HeroGraphic` variant actually renders its authored accent colour in both
   dark and light themes, without changing its geometry, `role="img"`, `aria-label`,
   title or description.
2. `DataBar` can no longer receive a hex string that is silently interpolated into
   `className` (the class is never generated → invisible bar). The API becomes a
   closed set of semantic tones backed by CSS tokens.
3. `ProgressRing` uses valid SVG paint values for its track and percent text, so the
   track is visible in both themes and the text is no longer black-on-dark.
4. `AgeDistributionRadial` renders its full radius at the call site's 250-unit
   geometry, uses theme-aware token colours, drops off-palette violet/pink, shows a
   complete legend, and stops advertising a click it never receives.
5. Add canonical `.surface`, `.page-title`, `.moment-value`, `.badge`, `.stat`,
   `.data-table` and tone-backed `.data-bar-fill--*` utilities in `index.css`, and
   remove the off-palette violet/cyan hooks from the token layer and from
   `DashboardCard`.

**Non-goals:** no data/label honesty work, no i18n, no container/`.wrap` migration,
no canvas/ECharts theming, no state-component unification, no new dependencies, no
deployment. Those are enumerated in **Side-quest policy** (§11).

---

## 2. Evidence (all static-code, baseline `eb693b4`)

### AP-1 — HeroGraphic bare colour classes

| ID | Evidence | What the code does |
|---|---|---|
| E1 | `frontend/src/components/HeroGraphic.tsx:24,31,36,42,48,54` | `primary` holds bare Tailwind steps: `"sky-400"`, `"amber-400"`, `"emerald-400"`, `"rose-400"`. Tailwind generates `.text-sky-400`, never a `.sky-400` class. |
| E2 | `frontend/src/components/HeroGraphic.tsx:77` | `` className={`w-full max-w-[200px] h-auto ${cfg.primary}` as string} `` — the useless class is attached to the `<svg>`; all shapes use `fill/stroke="currentColor"` (lines 82–203), so colour is inherited from `body` (`text-slate-100`, `index.css:92`). All six variants look identical. |
| E3 | `frontend/src/components/HeroGraphic.tsx:17,25,32,37,43,49,55` | `secondary` is declared and populated but **never read** — dead field. |
| E4 | `frontend/src/tailwind.config.js:18` + `index.css:76-84` | Literal `text-sky-400`/`text-amber-400`/`text-emerald-400`/`text-rose-400` classes already have light-theme overrides; dynamic construction (`text-${...}`) would be invisible to the JIT content scanner. |

**Call sites (read-only — no edit needed):** `HeroGraphic` imported in
`pages/Traseism.tsx:16,734`, `pages/PartyProfile.tsx:7,89`,
`pages/LiveDashboard.tsx:6,145`, `pages/SwitchLeaderboard.tsx:7,52`,
`pages/Committees.tsx:13,225`, `pages/MpComparison.tsx:6,152`,
`pages/Coalitions.tsx:4,107`, `pages/Demographics.tsx:5,122`,
`pages/Mps.tsx:6,80`, `pages/LegislatureDetail.tsx:6,66`,
`pages/SenateHistory.tsx:4,62`, `pages/PartyTimeline.tsx:7,151`,
`pages/Report.tsx:4,138`, `pages/PersonDeepDive.tsx:8,154`,
`pages/CoverageView.tsx:5,139`.

### AP-2 — DataBar hex-in-className

| ID | Evidence | What the code does |
|---|---|---|
| E5 | `frontend/src/components/DataViz.tsx:51-64,76` | `DataBarProps.color?: string`, default `"bg-sky-400/70"`; the value is interpolated into `className` at line 76. |
| E6 | `frontend/src/pages/Grafice.tsx:100,108,116` | `color="#10b981"`, `color="#ef4444"`, `color="#f59e0b"` — Tailwind never emits these as classes, so the fill has no background (invisible bar). |
| E7 | `frontend/src/pages/Topuri.tsx:8-14,146` | `LOYALTY_COLOR()` returns raw hex (`#10b981`, `#22c55e`, `#eab308`, `#f59e0b`, `#ef4444`) and is passed to `color={...}` at line 146 — same failure. |
| E8 | `frontend/src/index.css:256-259` | `.data-bar-fill` hardcodes `rgba(56, 189, 248, 0.7)`; the component does not even use this class. |
| E9 | `frontend/src/components/DataViz.tsx:143-152` | `StatBadge` (unused — only definition found) hand-rolls the badge grammar via `color.replace("text-", "bg-")`. |

### AP-2 — ProgressRing invalid SVG paint

| ID | Evidence | What the code does |
|---|---|---|
| E10 | `frontend/src/components/DataViz.tsx:110` | `stroke="slate-700/40"` is an SVG presentation attribute, not a CSS class: `slate-700/40` is not a colour → track invisible. |
| E11 | `frontend/src/components/DataViz.tsx:129` | `fill="slate-200"` — same bug → percent text falls back to black, unreadable on the dark ring. |
| E12 | `frontend/src/components/DataViz.tsx:98,102,105` | `viewBox="0 0 48 48"`, `cx/cy=24`, `r=24`, `strokeWidth=4` → the outer half of the 4px stroke (radius 26) is outside the viewBox and clipped. |
| E13 | `frontend/src/components/DataViz.tsx:94,108` | `color = "stroke-emerald-400"` is a genuine Tailwind class (valid) but has **no light-theme override**, so `stroke-emerald/amber/slate-400` stay dark-theme hues on white. |
| E14 | call sites | `pages/Demographics.tsx:124` (`stroke-emerald-400`), `pages/CoverageView.tsx:127` (default), `pages/Report.tsx:450-455` (`completenessRingColor()` → `stroke-emerald-400` / `stroke-amber-400` / `stroke-slate-400`, defined at `Report.tsx:97-102`). `Sparkline` also uses `stroke-sky-400` (`DataViz.tsx:30`; `PartyProfile.tsx:143`, `Demographics.tsx:117`, `PersonDeepDive.tsx:143`, `Coalitions.tsx:128`, `PartyTimeline.tsx:154`, `Report.tsx:352,397`). |

### AP-2 / AP-4 — AgeDistributionRadial

| ID | Evidence | What the code does |
|---|---|---|
| E15 | `frontend/src/components/AgeDistributionRadial.tsx:27-29,67` | Geometry is computed for `width/height` props (`radius = min/2 - 10`, center = `width/2`), but the `<svg>` has a **hardcoded** `viewBox="0 0 200 200"`. |
| E16 | `frontend/src/components/ui/AgeDistributionSection.tsx:34` | Sole consumer calls `width={250} height={250}` → radius 115, center 125; drawn into a 200×200 viewBox → everything beyond x/y=200 is clipped (~40% of the ring). |
| E17 | `AgeDistributionRadial.tsx:73-75,95-97,103,113` | Theme-blind literals: `rgba(30,41,59,.5)`, `rgba(255,255,255,.05)`, `rgba(255,255,255,.1)`, `rgba(156,163,175,.3/.5)`, `fill="white"` — white text becomes invisible on a light theme. |
| E18 | `AgeDistributionRadial.tsx:141-152` | `getCohortColor()` palette contains violet `rgba(167,139,250,.6)` and pink `rgba(236,72,153,.6)` (off-palette per `TRIAD-AUDIT AP-4`, `DESIGN-CONTRACT §Anti-patterns`), plus a duplicate amber (`:143` and `:150`). |
| E19 | `AgeDistributionRadial.tsx:124-135` | Legend is `cohorts.slice(0, 4)` only — additional cohorts have arcs with no legend entry; colour-only swatches with no list semantics. |
| E20 | `AgeDistributionRadial.tsx:85-86` + `AgeDistributionSection.tsx:12-19,34` | Arcs always have `onClick` + `cursor-pointer`, but `onCohortClick` is **never passed** by the sole consumer → false affordance (TA-1). |
| E21 | `AgeDistributionRadial.tsx:57-61` | `avgAge` divides by `totalAge` without a zero guard (NaN when cohorts exist but counts are 0). |
| E22 | `frontend/src/pages/LiveDashboard.tsx:12,182` | `AgeDistributionSection` is mounted only on `/` → that is the visual verification route. |

### AP-4 — Tokens defined but bypassed / off-palette

| ID | Evidence | What the code does |
|---|---|---|
| E23 | `frontend/src/index.css:34-45,67-72` | `--color-accent`, `--color-accent-hover`, `--color-success`, `--color-warning`, `--color-danger`, `--color-info`, `--bg-hero`, `--bg-surface` are declared but `grep -r 'var(--color-…)' src` returns **zero usages** — dead tokens. |
| E24 | `index.css:38` | `--color-accent-hover: #22d3ee` is cyan-400, off-palette (`index.css:35` explicitly says "no violet/lavender"; contract forbids a generic gradient identity). |
| E25 | `index.css:87-88` | Light overrides explicitly keep `.text-violet-400` and `.text-cyan-400`. |
| E26 | `index.css:240` | `.stat-card` hardcodes `border-top-color: #38bdf8` — stays bright cyan on a white light theme. |
| E27 | `frontend/src/components/DashboardCard.tsx:10,16,47-59` | `color` union and `COLOR_VARIANTS` expose `violet` and `cyan`. Grep shows all four live usages (`pages/LiveDashboard.tsx:97,108,119,130`) use `sky|emerald|amber|rose` only → the two variants are removable with zero call-site churn. |
| E28 | `index.css:179-183,295-297` | `.text-slate-500/600` → `--color-muted` under `@media screen`; print rule remaps to `#334155`. New utilities must preserve this split. |
| E29 | `index.css:264-267,99-104` | `.moment-badge` exists; no `.page-title`, `.moment-value`, `.badge`, `.surface`, `.stat`, `.data-table`. `font-black` appears in 13 page call sites (AP-6) — migration deferred (§11). |

---

## 3. Exclusive file list (owned by R-01)

The implementer may **write only** these seven product files plus the two new
artifacts listed below. A diff touching any other tracked file is a contract breach.

| # | Path | Why |
|---|---|---|
| 1 | `frontend/src/components/HeroGraphic.tsx` | E1–E3 |
| 2 | `frontend/src/components/DataViz.tsx` | E5, E10–E13, E9 |
| 3 | `frontend/src/components/AgeDistributionRadial.tsx` | E15–E21 |
| 4 | `frontend/src/pages/Grafice.tsx` | E6 — 3 `DataBar` call sites |
| 5 | `frontend/src/pages/Topuri.tsx` | E7 — `DataBar` call site + `LOYALTY_COLOR` helper |
| 6 | `frontend/src/index.css` | E8, E23–E26, E29 — tokens + utilities + light overrides |
| 7 | `frontend/src/components/DashboardCard.tsx` | E27 — remove unused violet/cyan variants |
| 8 | `scripts/check-design-primitives.mjs` **(new)** | red→green static regression guard (Step 8) |
| 9 | `frontend/dist/**` **(build output only)** | produced by `npm run build`; do not hand-edit |

**Read-only / must NOT edit:** `frontend/tailwind.config.js` (already maps CSS
variables for `slate`/`ink`/`panel`; no new Tailwind theme key is required),
`frontend/src/components/ui/AgeDistributionSection.tsx` (the 250/250 call site is
fixed by correcting the child's `viewBox`), `frontend/src/pages/Report.tsx`,
`frontend/src/pages/Demographics.tsx`, `frontend/src/pages/CoverageView.tsx`
(ProgressRing keeps its existing `color` prop — see Step 4), all other `HeroGraphic`
call sites, and every file in **Side-quest policy**.

---

## 4. Preconditions

1. **Baseline verified.** From `/home/nedaktov/parlament-deschis`:
   ```bash
   git rev-parse HEAD
   # expected: eb693b4d9faf558b22925fdb07ba6d118d7f6cef
   git status --porcelain=v1
   # expected: empty (or only pre-existing untracked .nedcode/ and .obsidian/backlink.json)
   ```
   Work in an isolated worktree/branch created from that commit, e.g.
   `git worktree add -b repair/R-01 /tmp/opencode/wt-R-01 eb693b4`.
2. **Backup created and verified** before the first edit (§6).
3. **Toolchain:** `node --version` ≥ 18; `cd frontend && npm ci` (or an existing
   `frontend/node_modules` with the locked versions); `npm run lint` and
   `npm run build` already green at baseline (record their output as the "before"
   checkpoint).
4. **UI-gate prerequisites** (only needed for CP9): a Vite server on port 5174 with
   `/api` proxied to a reachable API, `python3` with `playwright`, `/usr/bin/chromium`,
   and `/tmp/axe.min.js` (axe-core 4.10.2). At baseline `/tmp/axe.min.js` is **absent**:
   download it or report CP9 as `NOT PROVEN`, never as PASS.
5. **Coordination:** no other recipe is editing any of the seven owned product files.
6. **Inputs read in full** by the implementer: the three vault notes listed in the
   frontmatter, plus the nine source inputs.

---

## 5. Target design (decisions, so the implementer does not guess)

### 5.1 Token model

Keep the existing hex tokens (they are part of the public CSS surface) and **add
RGB-triplet companions** so `rgb(var(--token-rgb) / <alpha>)` works in both SVG
paint attributes and plain CSS. Light theme overrides the triplets; that is what
gives dark/light parity without touching call sites.

| Token | Dark `:root` | Light `html[data-theme="light"]` | Use |
|---|---|---|---|
| `--accent-rgb` | `56 189 248` (sky-400) | `3 105 161` (sky-700) | primary bars, stat top border, hero |
| `--success-rgb` | `34 197 94` (green-500) | `21 128 61` (green-700) | yes/loyalty bars, radial cohort 2 |
| `--warning-rgb` | `245 158 11` (amber-500) | `180 83 9` (amber-700) | abstain/loyalty bars, cohort 3 |
| `--danger-rgb` | `251 113 133` (rose-400) | `190 18 60` (rose-700) | no/low-loyalty bars, cohort 4 |
| `--info-rgb` | `100 116 139` (slate-500) | `71 85 105` (slate-600) | neutral bar, cohort 5 |

`--color-accent-hover` changes from cyan `#22d3ee` to on-palette `#7dd3fc`
(sky-300); the light value `#075985` is already on-palette and unchanged.

### 5.2 API contracts after repair

- `HeroGraphic`: `VARIANT_CONFIG[variant].primary` is a **literal** Tailwind class
  (`"text-sky-400"`, …). `secondary` is removed. No `as string` cast.
- `DataBar`: `color?: string` → `tone?: DataBarTone` where
  `DataBarTone = "accent" | "success" | "warning" | "danger" | "info"`; default
  `"accent"`. Hex strings become a **TypeScript error**, so the bug cannot recur.
- `ProgressRing`: `color?: string` **keeps** its meaning as a real `stroke-*`
  Tailwind class (all current callers already pass valid ones); light-theme
  overrides for the four used stroke classes are added in `index.css`. Track and
  text switch from bogus attributes to token-backed SVG paint values. Ring radius
  becomes 22 so the 4px stroke fits the 48-unit viewBox.
- `AgeDistributionRadial`: `viewBox` follows `width`/`height`; SVG fills use
  token-backed CSS colour values; a five-colour on-palette cohort cycle replaces
  violet/pink; legend renders **all** cohorts as a `<ul>`; arc interactivity is
  conditional on `onCohortClick` (with keyboard support when enabled).

### 5.3 Behaviour explicitly preserved

- `HeroGraphic`: same six variants, same SVG paths/geometry/opacities, `role="img"`,
  `aria-label={cfg.title}`, title and description text, and caller `className`
  (including the 40px `SwitchLeaderboard` instance).
- `DataBar`: same clamping math (`max > 0 ? min(100, max(0, v/max*100)) : 0`), same
  label/value row, same `width` inline style, same 300ms transition. Only the
  colour source changes.
- `ProgressRing`: same `pct` clamping, `aria-label={`${pct}% complete`}`, rotation,
  `transition-all duration-500 ease-out`, and rendered percentage text.
- `AgeDistributionRadial`: same cohort angles, `avgAge` weighting formula,
  `w-32 h-32` rendered size, and legend text format `"{label}: {count}"`.
- Print block (`index.css:282-306`) stays; new utilities use screen-scoped tokens
  where relevant so print keeps `#334155` text on white.

---

## 6. Backup path + checksum command

Create a byte-for-byte snapshot **before** any edit:

```bash
cd /home/nedaktov/parlament-deschis
SNAP=/tmp/opencode/backups/R-01/eb693b4
mkdir -p "$SNAP"
for f in \
  frontend/src/components/HeroGraphic.tsx \
  frontend/src/components/DataViz.tsx \
  frontend/src/components/AgeDistributionRadial.tsx \
  frontend/src/components/ui/AgeDistributionSection.tsx \
  frontend/src/pages/Grafice.tsx \
  frontend/src/pages/Topuri.tsx \
  frontend/src/pages/Report.tsx \
  frontend/src/pages/Demographics.tsx \
  frontend/src/pages/CoverageView.tsx \
  frontend/src/components/DashboardCard.tsx \
  frontend/src/index.css \
  frontend/tailwind.config.js; do
  cp -a --parents "$f" "$SNAP"/
done
cd "$SNAP" && find . -type f -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
sha256sum -c SHA256SUMS
```

Expected `sha256sum -c` output (all lines `: OK`), and exit code **0**. The
baseline digests to compare against (measured, not remembered):

```
8c42196f5c3d6729f6b8339cab3926412ace936a1c70a4865fd4434c84c106d5  frontend/src/components/HeroGraphic.tsx
6c7e04cbd907cde806605e93a09ac3793d5e9067ad9007a5240102a89736b436  frontend/src/components/DataViz.tsx
475b9375c9a8983e724f472be67190b24f0bf9f2ae015610b899903ca7935830  frontend/src/components/AgeDistributionRadial.tsx
d8ca67e962f3ec952c4fd37a4e5c054f837061a37086e0bb2125e05e421f4116  frontend/src/components/ui/AgeDistributionSection.tsx
9d94309f7c93277beb34a6603c750fe9ee3afcfa27cd3266355c89b79eeccdc7  frontend/src/pages/Grafice.tsx
a07a2a4e2e59c038e17a19ae3f38a8322aac0574a2100d926330e25dcfe9d8d7  frontend/src/pages/Topuri.tsx
d6affe721101e7a0dbc23026dd375d7b9f048a7ac9a5f5b723a120f6dc407f13  frontend/src/pages/Report.tsx
153410d28c26b9d112be4e9330564fc6b0700c2e7b83cfeebeba1fb1d9efbcfd  frontend/src/pages/Demographics.tsx
fcb2069c25be7f2266573a3c221fcbda345bbecfc6959894e2f62ebb8de8669d  frontend/src/pages/CoverageView.tsx
4f73a58fc16fffba22b941958afea6946760ae53b69193dd4d3be7c04b3f4e5c  frontend/src/index.css
11fc766a8289d47f5d3a9a378c0c4fa2b2bb5540ca96d7c6560ce92d8746b90a  frontend/tailwind.config.js
```
(DashboardCard digest was not captured by the authoring agent; compute it on the
first run and append it to `SHA256SUMS` from the snapshot, not from the edited tree.)

---

## 7. Implementation steps

Work from the worktree root. Run **CP0/CP1 (§8)** before Step 1.

### Step 1 — `HeroGraphic.tsx`: literal classes

Replace the `VARIANT_CONFIG` type and all six entries. Exact target state for
lines 1–57:

```tsx
export interface HeroGraphicProps {
  variant:
    | "overview"
    | "switches"
    | "committee"
    | "people"
    | "wave"
    | "report";
  className?: string;
}

const VARIANT_CONFIG: Record<
  HeroGraphicProps["variant"],
  {
    title: string;
    desc: string;
    // Literal Tailwind classes: the JIT content scanner only sees whole strings.
    primary: string;
  }
> = {
  overview: {
    title: "Parliament Deschis",
    desc: "Transparent data on MPs, party switches, and committee control",
    primary: "text-sky-400",
  },
  switches: {
    title: "Party Switches",
    desc: "Observed group changes across legislatures",
    primary: "text-amber-400",
  },
  committee: {
    title: "Committee Control",
    desc: "Party chair distribution across committees",
    primary: "text-emerald-400",
  },
  people: {
    title: "Members of Parliament",
    desc: "3,388 persons tracked across legislatures",
    primary: "text-rose-400",
  },
  wave: {
    title: "Switch Waves",
    desc: "Bursts of affiliation change over time",
    primary: "text-rose-400",
  },
  report: {
    title: "Transparency Report",
    desc: "One-page summary of parliament data for journalists and citizens",
    primary: "text-sky-400",
  },
};
```

Change line 77 exactly:

```tsx
className={`w-full max-w-[200px] h-auto ${cfg.primary}`}
```

Do **not** build `text-${cfg.primary}` (invisible to Tailwind JIT), and do not
retain the `as string` cast. All `fill="currentColor"` / `stroke="currentColor"`
lines (82–203) and the caption block (206–209) stay byte-identical.

Commit point: not yet — batch Steps 1–7 into one atomic commit.

### Step 2 — `index.css`: tokens, utilities, light parity

In `:root` (after `--color-info: #64748b;`, line 42) add:

```css
  /* RGB companions: let SVG paint and utilities use rgb(var(--…)/<alpha-value>).
     These are the same authored hues as the hex tokens above. */
  --accent-rgb: 56 189 248;
  --success-rgb: 34 197 94;
  --warning-rgb: 245 158 11;
  --danger-rgb: 251 113 133;
  --info-rgb: 100 116 139;
```

Change line 38: `--color-accent-hover: #22d3ee;` → `--color-accent-hover: #7dd3fc;`

In `html[data-theme="light"]` (after `--color-accent-hover: #075985;`, line 69)
add:

```css
  /* Same semantics, AA-tuned for white surfaces. */
  --accent-rgb: 3 105 161;
  --success-rgb: 21 128 61;
  --warning-rgb: 180 83 9;
  --danger-rgb: 190 18 60;
  --info-rgb: 71 85 105;
```

Replace lines 87–88 (`.text-violet-400` / `.text-cyan-400` overrides) with the
four **used** stroke overrides:

```css
html[data-theme="light"] .stroke-sky-400 { stroke: #0369a1; }
html[data-theme="light"] .stroke-emerald-400 { stroke: #047857; }
html[data-theme="light"] .stroke-amber-400 { stroke: #b45309; }
html[data-theme="light"] .stroke-slate-400 { stroke: #475569; }
```

Change line 240 in `.stat-card`: `border-top-color: #38bdf8;` →
`border-top-color: rgb(var(--accent-rgb));`

Replace lines 252–259 (`.data-bar` / `.data-bar-fill`) with:

```css
.data-bar {
  @apply h-1.5 w-full rounded-full bg-slate-700/40 overflow-hidden;
}

.data-bar-fill {
  @apply h-full rounded-full;
  background-color: rgb(var(--accent-rgb) / 0.7);
}
.data-bar-fill--accent { background-color: rgb(var(--accent-rgb) / 0.7); }
.data-bar-fill--success { background-color: rgb(var(--success-rgb) / 0.7); }
.data-bar-fill--warning { background-color: rgb(var(--warning-rgb) / 0.7); }
.data-bar-fill--danger { background-color: rgb(var(--danger-rgb) / 0.7); }
.data-bar-fill--info { background-color: rgb(var(--info-rgb) / 0.7); }
```

Append the canonical utility block after `.moment-badge` (line 267):

```css
/* R-01 — one token-backed utility vocabulary. Existing page classes are
   deliberately left in place; migration of `font-black` / `.stat-card` /
   `.info-graphic` call sites is a separate recipe (see §11). */
.surface {
  @apply bg-panel rounded-xl border border-slate-700/60 shadow-lg;
}

.page-title {
  @apply text-3xl font-bold tracking-tight text-slate-100;
  letter-spacing: -0.025em;
  line-height: 1.25;
}

.moment-value {
  @apply text-5xl font-extrabold tracking-tight tabular-nums text-slate-100;
  line-height: 1.25;
}

.badge {
  @apply inline-flex items-center gap-1 rounded-full border border-slate-700/50 bg-slate-800/50 px-2 py-0.5 text-xs;
}

.stat {
  @apply rounded-xl border border-slate-700/50 p-4 shadow-sm;
  border-top: 2px solid rgb(var(--accent-rgb));
}

.data-table {
  @apply w-full text-left text-sm text-slate-300;
}
.data-table th { @apply px-3 py-2 text-xs uppercase tracking-wide text-slate-400; }
.data-table td { @apply px-3 py-2; }
```

Keep the `@media screen` muted override (179–183), the print block (282–306),
the focus ring (198–201) and reduced-motion rule (203–212) untouched.

### Step 3 — `DataViz.tsx`: DataBar semantic tone

Replace lines 51–82 with:

```tsx
export type DataBarTone = "accent" | "success" | "warning" | "danger" | "info";

export interface DataBarProps {
  value: number;
  max: number;
  label?: string;
  tone?: DataBarTone;
}

const DATA_BAR_TONE: Record<DataBarTone, string> = {
  accent: "data-bar-fill--accent",
  success: "data-bar-fill--success",
  warning: "data-bar-fill--warning",
  danger: "data-bar-fill--danger",
  info: "data-bar-fill--info",
};

export function DataBar({
  value,
  max,
  label,
  tone = "accent",
}: DataBarProps) {
  const width = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <div className="flex justify-between text-xs text-slate-300">
          <span>{label}</span>
          <span className="font-mono text-slate-100">{value}</span>
        </div>
      )}
      <div className="data-bar">
        <div
          className={`data-bar-fill ${DATA_BAR_TONE[tone]}`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}
```

`DATA_BAR_TONE` values are plain CSS classes from Step 2, so there is no Tailwind
JIT dependency. `Sparkline` (1–49) and `sparklinePoints` (8–25) stay unchanged.

### Step 4 — `DataViz.tsx`: ProgressRing valid paint + radius

Replace lines 91–135 with:

```tsx
export function ProgressRing({
  value,
  max = 100,
  color = "stroke-emerald-400",
  size = 60,
}: ProgressRingProps) {
  const pct = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;
  // r=22 + strokeWidth/2=2 lands exactly on the 48-unit viewBox edge;
  // the old r=24 clipped half the stroke.
  const radius = 22;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      role="img"
      aria-label={`${pct}% complete`}
      className={`rotate-[-90deg] ${color}`}
    >
      <circle
        cx="24" cy="24" r={radius}
        fill="none"
        stroke="rgb(var(--slate-700) / 0.4)"
        strokeWidth="4"
      />
      <circle
        cx="24" cy="24" r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth="4"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        className="transition-all duration-500 ease-out"
      />
      <text
        x="24" y="28"
        textAnchor="middle"
        fontSize="10"
        fontFamily="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
        fill="rgb(var(--slate-200))"
      >
        {Math.round(pct)}%
      </text>
    </svg>
  );
}
```

`rgb(var(--slate-700) / 0.4)` and `rgb(var(--slate-200))` are valid CSS colours in
SVG presentation attributes and reverse correctly in light theme
(`index.css:60,62`). Do **not** change call sites in Report/Demographics/CoverageView.

### Step 5 — `DataViz.tsx`: StatBadge uses `.badge`

Line 149 only: `className="flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800/50 border border-slate-700/50"` → `className="badge"`. Leave lines 150–152 as-is (the `text-slate-500` token mapping is intentional, E28).

### Step 6 — `AgeDistributionRadial.tsx`: full target state

Replace the file with the following. It keeps every geometry constant from the
original, fixes the viewBox, replaces hardcoded paint with tokens, removes
violet/pink, renders the full legend, and makes the pointer affordance honest.

```tsx
import { useMemo } from "react";
import type { KeyboardEvent } from "react";

export interface CohortData {
  label: string;
  minAge?: number;
  maxAge?: number;
  count: number;
  avgAge: number;
}

export interface AgeDistributionRadialProps {
  cohorts: CohortData[];
  totalAge: number;
  onCohortClick?: (cohort: CohortData) => void;
  width?: number;
  height?: number;
}

/* On-palette cycle: no violet, purple, cyan or pink. Values are CSS colours so
   the same source works in SVG `fill` and in an inline `style` for the legend. */
const COHORT_FILLS = [
  "rgb(var(--accent-rgb))",
  "rgb(var(--success-rgb))",
  "rgb(var(--warning-rgb))",
  "rgb(var(--danger-rgb))",
  "rgb(var(--info-rgb))",
];

function getCohortColor(index: number): string {
  return COHORT_FILLS[index % COHORT_FILLS.length];
}

export default function AgeDistributionRadial({
  cohorts,
  totalAge,
  onCohortClick,
  width = 200,
  height = 200,
}: AgeDistributionRadialProps) {
  const radius = Math.min(width, height) / 2 - 10;
  const centerX = width / 2;
  const centerY = height / 2;

  const arcs = useMemo(() => {
    if (!cohorts.length || totalAge <= 0) return [];
    let cumulativeAngle = 0;
    return cohorts.map((cohort) => {
      const startAngle = cumulativeAngle;
      const endAngle = cumulativeAngle + (2 * Math.PI * cohort.count / totalAge);
      cumulativeAngle = endAngle;
      return { ...cohort, startAngle, endAngle };
    });
  }, [cohorts, totalAge]);

  const avgAge = useMemo(
    () => totalAge > 0
      ? cohorts.reduce((sum, c) => sum + c.count * c.avgAge, 0) / totalAge
      : 0,
    [cohorts, totalAge],
  );

  const arcPath = (startAngle: number, endAngle: number) => {
    const x1 = centerX + radius * Math.cos(startAngle);
    const y1 = centerY + radius * Math.sin(startAngle);
    const x2 = centerX + radius * Math.cos(endAngle);
    const y2 = centerY + radius * Math.sin(endAngle);
    const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;
    return `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} L ${centerX} ${centerY} Z`;
  };

  const interactive = Boolean(onCohortClick);

  return (
    <div className="surface p-4 overflow-hidden">
      <div className="text-xs text-slate-400 mb-2">Age Distribution</div>
      <div className="flex items-center justify-center">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          fill="none"
          className="w-32 h-32"
          role={interactive ? "group" : "img"}
          aria-label={`Age distribution across ${cohorts.length} cohorts, average age ${avgAge.toFixed(0)}`}
        >
          <circle
            cx={centerX} cy={centerY} r={radius}
            fill="rgb(var(--slate-800) / 0.5)"
            stroke="rgb(var(--slate-600) / 0.4)"
            strokeWidth={1}
          />
          {arcs.map((slice, i) => (
            <path
              key={slice.label}
              d={arcPath(slice.startAngle, slice.endAngle)}
              fill={getCohortColor(i)}
              opacity={0.85}
              {...(interactive
                ? {
                    role: "button",
                    tabIndex: 0,
                    "aria-label": `Show details for ${slice.label} cohort`,
                    onClick: () => onCohortClick?.(slice),
                    onKeyDown: (e: KeyboardEvent<SVGPathElement>) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        onCohortClick?.(slice);
                      }
                    },
                    className: "cursor-pointer hover:opacity-100 transition-opacity",
                  }
                : {})}
            />
          ))}
          <circle
            cx={centerX} cy={centerY} r={(avgAge / 100) * radius}
            fill="rgb(var(--slate-400) / 0.18)"
            stroke="rgb(var(--slate-400) / 0.6)"
            strokeWidth={1}
          />
          <circle cx={centerX} cy={centerY} r={radius * 0.1} fill="rgb(var(--slate-400) / 0.6)" />
          {avgAge > 0 && (
            <text
              x={centerX} y={centerY + 4}
              textAnchor="middle"
              dominantBaseline="middle"
              fill="rgb(var(--slate-100))"
              fontSize={10}
              fontWeight="600"
            >
              {avgAge.toFixed(0)}
            </text>
          )}
        </svg>
      </div>

      <ul className="mt-3 grid grid-cols-2 gap-1 text-xs">
        {cohorts.map((c, i) => (
          <li key={c.label} className="flex items-center gap-2">
            <span
              aria-hidden="true"
              className="w-3 h-3 shrink-0 rounded-full"
              style={{ backgroundColor: getCohortColor(i) }}
            />
            <span className="text-slate-300 truncate">{c.label}: {c.count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

Notes the implementer must not "improve" away:
- `className="w-32 h-32"` (128px rendered) is intentional: the corrected 250-unit
  viewBox now scales the full ring down instead of cropping it.
- `opacity={0.85}` replaces the old double transparency (`0.6` fill alpha ×
  `0.7` path opacity); hover still reaches full opacity.
- When no callback is passed (today's only consumer), paths have **no** `onClick`,
  no `cursor-pointer`, no `tabIndex` — that is the TA-1 fix.

### Step 7 — call sites + DashboardCard

`frontend/src/pages/Grafice.tsx`, exactly three edits:

```
line 100: <DataBar value={c.yes_pct}     max={100} color="#10b981" />  →  tone="success"
line 108: <DataBar value={c.no_pct}      max={100} color="#ef4444" />  →  tone="danger"
line 116: <DataBar value={c.abstain_pct} max={100} color="#f59e0b" />  →  tone="warning"
```

`frontend/src/pages/Topuri.tsx`:

- line 5: `import { DataBar } from "../components/DataViz";` →
  `import { DataBar, type DataBarTone } from "../components/DataViz";`
- replace lines 8–14 with:

```tsx
// Thresholds preserved from LOYALTY_COLOR; intermediate green/yellow steps
// collapse into the two on-palette semantic tones (success / warning).
const LOYALTY_TONE = (pct: number): DataBarTone => {
  if (pct >= 50) return "success";
  if (pct >= 30) return "warning";
  return "danger";
};
```

- line 146: `color={LOYALTY_COLOR(e.loyalty_pct)}` → `tone={LOYALTY_TONE(e.loyalty_pct)}`

`frontend/src/components/DashboardCard.tsx`:

- line 10 and line 16: drop `| "violet" | "cyan"` from both colour unions →
  `color?: "sky" | "emerald" | "amber" | "rose";`
- delete the `violet: { … }` and `cyan: { … }` entries (lines 47–59) from
  `COLOR_VARIANTS`.
- No page changes: all four live `DashboardCard` usages
  (`pages/LiveDashboard.tsx:97,108,119,130`) already use on-palette tones.

### Step 8 — create the static regression guard

Write `scripts/check-design-primitives.mjs` exactly as follows. It is the red→green
proof and the permanent guard for all four bug families.

```js
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
```

### Step 9 — commit atomically

```bash
git add frontend/src/components/HeroGraphic.tsx frontend/src/components/DataViz.tsx \
  frontend/src/components/AgeDistributionRadial.tsx frontend/src/pages/Grafice.tsx \
  frontend/src/pages/Topuri.tsx frontend/src/index.css \
  frontend/src/components/DashboardCard.tsx scripts/check-design-primitives.mjs
git commit -m "fix(R-01): repair design-system primitives and token utilities"
git rev-parse HEAD   # record this SHA for ROLLBACK (§10)
```

No push, no deploy, no tag, no secrets.

---

## 8. Checkpoints (exact command + expected printed output + exit code)

Run CP0–CP2 **before** Step 1 (RED evidence), CP3+ after Step 9 (GREEN).

### CP0 — baseline identity
```bash
cd /home/nedaktov/parlament-deschis && git rev-parse HEAD
```
Expected stdout: `eb693b4d9faf558b22925fdb07ba6d118d7f6cef` · exit **0**.

### CP1 — RED evidence (pre-fix)
```bash
grep -n 'primary: "sky-400"\|cfg.primary}` frontend/src/components/HeroGraphic.tsx
```
Expected: prints `24:    primary: "sky-400",` and a line 77 containing `cfg.primary` followed by `as string` · exit **0**.

```bash
grep -nE 'color="#[0-9a-f]{6}"|color=\{LOYALTY_COLOR' frontend/src/pages/Grafice.tsx frontend/src/pages/Topuri.tsx
```
Expected: 4 matching lines (Grafice 100/108/116, Topuri 146) · exit **0**.

```bash
grep -n 'stroke="slate-700/40"\|fill="slate-200"' frontend/src/components/DataViz.tsx
```
Expected: `110:` and `129:` lines · exit **0**.

```bash
grep -n 'viewBox="0 0 200 200"' frontend/src/components/AgeDistributionRadial.tsx
```
Expected: `67:` line · exit **0**.

### CP2 — guard RED (pre-fix; run after Step 8 file exists but before Steps 1–7)
```bash
node scripts/check-design-primitives.mjs
```
Expected stdout contains multiple `[FAIL]` lines (at least the bare-class, hex,
SVG-paint and violet/cyan rules), ends with `GUARD FAIL`; exit **1**. If it exits 0
before the fix, the guard is wrong — stop and fix the guard.

### CP3 — backup integrity
```bash
cd /tmp/opencode/backups/R-01/eb693b4 && sha256sum -c SHA256SUMS
```
Expected: one `<path>: OK` per line, no `FAILED`; exit **0**.

### CP4 — guard GREEN
```bash
cd /home/nedaktov/parlament-deschis && node scripts/check-design-primitives.mjs
```
Expected stdout ends with:
```
DESIGN PRIMITIVE GUARD: N/N rules pass
GUARD PASS
```
exit **0**. No `[FAIL]` line anywhere.

### CP5 — lint
```bash
cd /home/nedaktov/parlament-deschis/frontend && npm run lint
```
Expected: npm banner `> parlament-deschis-frontend@0.1.0 lint`, then
`> tsc --noEmit && eslint src --ext .ts,.tsx`, **no** TypeScript/ESLint diagnostics;
exit **0**. In particular no error about `DataBarTone`, `KeyboardEvent<SVGPathElement>`
or unused `secondary`.

### CP6 — build
```bash
cd /home/nedaktov/parlament-deschis/frontend && npm run build
```
Expected: `> tsc -b && vite build`, Vite asset list, `✓ built in <n>s`; exit **0**;
`frontend/dist/index.html` exists.

### CP7 — Tailwind emitted the literal hero classes
```bash
cd /home/nedaktov/parlament-deschis/frontend && grep -oE 'text-(sky|amber|emerald|rose)-400' dist/assets/*.css | sort -u
```
Expected: all four strings appear (they are literals in `HeroGraphic.tsx` now) ·
exit **0**. Note this proves emission, not visual correctness (see NOT PROVEN).

### CP8 — artifact verification script
```bash
cd /home/nedaktov/parlament-deschis && bash scripts/verify-dashboard.sh
```
Expected: `✓ Build exists`, `✓ TypeScript compiles with 0 errors`, measured
`LiveDashboard-*.js` size, `✓ 8 present, 0 missing` for component exports,
`✓ /api/dashboard/stats endpoint defined`, final `All measured checks passed. 🚀`;
exit **0**.

### CP9 — UI / a11y gate (browser; run with server up)
```bash
# terminal A
cd /home/nedaktov/parlament-deschis/frontend && npx vite --host 127.0.0.1 --port 5174
# terminal B
cd /home/nedaktov/parlament-deschis && python3 scripts/ui_validate.py http://127.0.0.1:5174
```
Expected final line:
`UI VALIDATION PASS: 24 routes, 0 JS errors, 0 axe violations` · exit **0**.
If `/tmp/axe.min.js` or Chromium is missing, print `NOT PROVEN` for this gate —
**never** mark it PASS.

### CP10 — manual dark/light visual gate (evidence, not automation)
Toggle `ThemeToggle` (`src/components/ui/ThemeToggle.tsx:12-37`, persisted in
`localStorage` key `parlament-deschis-theme`) and inspect:

| Route | What must be visible | Maps to |
|---|---|---|
| `/` | six `HeroGraphic` variants? (overview here), full radial ring, coloured bars in legend, age text readable | E1/E2, E15–E18 |
| `/traseism`, `/committees`, `/mps`, `/coalitions`, `/report` | amber / emerald / rose / rose / sky hero respectively, **distinct** from each other | E1 |
| `/grafice` | yes/no/abstain bars filled green/red/amber | E5–E7 |
| `/topuri` | loyalty bars filled by tone; no invisible rows | E7 |
| `/coverage`, `/demographics`, `/report` | ring track visible; percentage text readable; no clipped stroke | E10–E12 |
| dark **and** light | hero accents, bars, ring text and radial centre text retain ≥4.5:1 for text / ≥3:1 for UI | E24–E26 |

Record screenshots under `docs/evidence/R-01/` (new untracked evidence only; do not
commit binaries without approval). If screenshots/contrast measurement are not
taken, report `NOT PROVEN`.

---

## 9. Verification gates summary

| Gate | Command | Required |
|---|---|---|
| Static guard | `node scripts/check-design-primitives.mjs` | yes (CP4) |
| Lint | `npm run lint` (in `frontend/`) | yes (CP5) |
| Build | `npm run build` (in `frontend/`) | yes (CP6) |
| Artifact check | `bash scripts/verify-dashboard.sh` | yes (CP8) |
| UI / axe | `python3 scripts/ui_validate.py http://127.0.0.1:5174` | yes, or `NOT PROVEN` (CP9) |
| Visual dark/light pass | CP10 table | yes, or `NOT PROVEN` |

A failure in CP4–CP8 blocks the commit's acceptance. CP9/CP10 may be `NOT PROVEN`
with an explicit reason, but then the work is **not** claimed as fully verified.

---

## 10. Rollback

- **Pre-commit (discard edits only):**
  ```bash
  cd /home/nedaktov/parlament-deschis
  git checkout eb693b4 -- \
    frontend/src/components/HeroGraphic.tsx \
    frontend/src/components/DataViz.tsx \
    frontend/src/components/AgeDistributionRadial.tsx \
    frontend/src/pages/Grafice.tsx \
    frontend/src/pages/Topuri.tsx \
    frontend/src/index.css \
    frontend/src/components/DashboardCard.tsx
  rm -f scripts/check-design-primitives.mjs
  ```
- **Post-commit (recorded SHA from Step 9):**
  ```bash
  git revert <sha>          # one atomic revert of the R-01 commit
  git rev-parse HEAD        # verify revert commit created
  ```
  Then re-run CP4–CP8; the guard must return to RED (exit 1) on the reverted
  baseline — that is the proof the revert actually undid the fix.
- **Catastrophic/local loss:** restore from the §6 snapshot:
  ```bash
  cd /tmp/opencode/backups/R-01/eb693b4 && sha256sum -c SHA256SUMS
  # then cp -a the seven owned files back into the worktree
  ```
- Never `git push`, never force-push, never `git tag -d`, never delete data.

---

## 11. Side-quest policy (explicitly OUT of R-01)

An implementer who notices any of the following must **record it, not fix it**.
Each item belongs to another recipe/reason; touching it here invalidates the
exclusive file list.

| Finding | Where | Why deferred |
|---|---|---|
| `.wrap` missing/doubled on ~10 routes (AP-3) | many `pages/*.tsx`, `index.css:118-120` | container recipe; R-01 adds `.surface` but does not rewrap pages |
| Muted-text inversion (AP-5) | `index.css:179-183`, Radar/Grafice/Report | token-semantics recipe; R-01 preserves the existing `text-slate-500` mapping |
| `font-black` ×13 (AP-6), type-scale fragmentation | 13 pages listed by `grep -rn font-black src`, `index.css:99-104` | `.moment-value` is added but migration is a separate type recipe |
| Three card grammars / radii 4-8-12px (AP-6), `Mps.tsx:173 slate-750` | `InfoStat`, local `StatCard`, `.stat-card`, `Mps.tsx` | R-01 adds `.stat`; migration of call sites deferred |
| Canvas/ECharts hardcodes + palettes (AP-7) | `Ideology.tsx:22-42` (`#8b5cf6`, `#ec4899`, `#06b6d4`, `#a855f7`, `#c026d3`, `#6366f1`, `#14b8a6`), `SankeyFlow.tsx:4,211` (`schemeCategory10`), `VoteActivityChart.tsx:129-150`, `TimelineChart.tsx:23-24`, `PartyAgreementMatrix.tsx:165-209` | R-02 canvas charts; R-01 removes violet/cyan only from the **DOM/CSS primitives it owns** |
| `DataQualityGauge.tsx:96` inline hex | component | R-02 |
| State visuals `ErrorState`/`LoadingState`/`EmptyState` (AP-8), `AgeDistributionSection.tsx:19` `text-red-400` | shared + pages | state-system recipe |
| TA-1 keyboard semantics on Sankey/leaderboard/other SVG nodes | many components | tactile/semantics recipe; R-01 only makes **its own radial arcs** honest |
| i18n gaps, `date`/`as_of`, switch definitions, provenance, mislabelled counts | whole app | separate functional recipes (FN-1…FN-9, X1…X6) |
| `SwitchLeaderboard.tsx:52` 40px hero still renders caption | component | behaviour preserved by instruction; not a paint bug |

---

## 12. Dependencies

- **No runtime dependency** on another recipe's product changes: all seven owned
  files are independent of R-02/R-03 at compile time.
- **Verification dependency:** CP9 needs a reachable API behind the Vite `/api`
  proxy and the axe script at `/tmp/axe.min.js`; CP10 needs a browser with a theme
  toggle. These are environment prerequisites, not code dependencies.
- **Completion dependency:** the "no off-palette violet/cyan" acceptance item is
  **partial** until R-02 removes the canvas/ECharts violet/pink/cyan hexes listed
  in §11. R-01 owns only the DOM/CSS surface. Acceptance criterion AC-8 below is
  scoped accordingly.
- `DataBarTone` is exported from `DataViz.tsx` and imported by `Topuri.tsx` —
  compile order within the atomic commit is irrelevant (`tsc` sees the whole tree).

---

## 13. Acceptance criteria

1. **AC-1** `node scripts/check-design-primitives.mjs` exits **0** with `N/N` PASS and
   the pre-fix run demonstrably exited 1 (CP2 evidence retained).
2. **AC-2** `npm run lint` and `npm run build` both exit 0 (CP5, CP6).
3. **AC-3** No owned file contains a hex colour inside `className`, no SVG paint
   attribute contains a Tailwind step name, and no dynamic `text-${...}` class
   construction remains (guard rules).
4. **AC-4** All six `HeroGraphic` variants render distinct, theme-aware accents;
   geometry, caption text, `role="img"` and `aria-label` unchanged (diff review +
   CP10).
5. **AC-5** `DataBar` accepts only `DataBarTone`; Grafice (3) and Topuri (1) call
   sites migrated; the old 90/70/50/30 thresholds remain observable in
   `LOYALTY_TONE`.
6. **AC-6** `ProgressRing` track and percentage text are visible in dark **and**
   light; stroke is not clipped at the viewBox edge; `aria-label` unchanged.
7. **AC-7** `AgeDistributionRadial` at `width=250 height=250` shows the entire ring
   (no flat cut), uses only the five on-palette token colours, lists **all** cohorts
   in a `<ul>`, has readable centre text in both themes, and exposes no
   `cursor-pointer` without a callback.
8. **AC-8** In the seven owned files: zero occurrences of `violet`, `cyan`,
   `#22d3ee`, `#38bdf8` as a CSS value, `rgba(167,139,250`, or
   `rgba(236,72,153`. Canvas palettes are tracked under R-02 (§12).
9. **AC-9** The new utilities `.surface`, `.page-title`, `.moment-value`, `.badge`,
   `.stat`, `.data-table` and the five `.data-bar-fill--*` classes exist in
   `index.css` and are backed by `rgb(var(--*-rgb))` where colour is involved.
10. **AC-10** `bash scripts/verify-dashboard.sh` exits 0 (CP8) and CP9/CP10 are
    either PASS with recorded evidence or explicitly `NOT PROVEN`.
11. **AC-11** Diff touches only the nine artifacts in §3; backup checksums (§6)
    still verify; commit is atomic; rollback SHA recorded.

---

## 14. NOT PROVEN (do not upgrade to fact without a browser pass)

- All "invisible bar", "invisible track", "black text", "monochrome hero" and
  "clipped ring" conclusions are **CSS/SVG semantics inferred from source**, not
  observed pixels. The triad audits themselves state this at
  `TRIAD-AUDIT-2026-11-21.md:19,87-89` and `FRONTEND-AUDIT-2026-11-21.md:22-23,109-114`.
- No browser render, screenshot, computed-style or contrast measurement was taken
  by the recipe author (read-only subagent). Contrast numbers for the new light
  tokens are **authored values**, not measured ratios.
- Tailwind JIT emission of `text-sky-400` etc. is not proven until CP6/CP7 run.
- `rgb(var(--slate-700) / 0.4)` in an SVG presentation attribute is standards-valid
  but has **not** been rendered here; CP10 must confirm in Chromium.
- `role="group"` + `role="button"` on SVG `<path>` (the conditional interactive
  branch) has not been axe-scanned — no current consumer passes `onCohortClick`,
  so the branch is dormant at baseline. Re-run CP9 if a future consumer enables it.
- The shape of `generationalShift()` cohort rows is inferred from
  `AgeDistributionSection.tsx:22-26`; no live API payload was inspected.
- No JavaScript unit test exists in `frontend/` despite the comment at
  `DataViz.tsx:7` referring to a "no-NaN unit test" — a red→green unit test could
  not be captured; the static guard (Step 8) is the substitute.
- CP9 cannot run at baseline: `/tmp/axe.min.js` is absent. UI/axe results are
  `NOT PROVEN` until it is installed and the gate is actually executed.
- `scripts/verify-dashboard.sh` and `ui_validate.py` were **read**, not executed,
  by the recipe author; their expected outputs in §8 are derived from their source
  and must be confirmed by the implementer.
- The 40px `HeroGraphic` caption issue and the `font-black`/card-grammar items are
  known but deliberately unfixed; no claim of AP-6/AP-8 resolution is made.

---

## 15. See also

`TRIAD-AUDIT-2026-11-21.md` §1 (AP-1, AP-2, AP-4, AP-5, AP-6), §4 item 1 ·
`FRONTEND-AUDIT-2026-11-21.md` §2 X7, §5 item 7 ·
`DESIGN-CONTRACT.md` §Anti-patterns / §Success criteria ·
`docs/remediation/RECIPES.md` (universal recipe template and prohibitions) ·
`docs/CONTINUATION-STRATEGY-2026-11-21.md`.
