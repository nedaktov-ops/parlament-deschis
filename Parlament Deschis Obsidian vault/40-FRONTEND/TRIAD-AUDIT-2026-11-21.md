---
id: TRIAD-AUDIT
type: research
title: "Three-lens front-end audit — appearance, tactile, functionality (2026-11-21)"
description: "Element-level documentation of page attributes, behaviours and enhancement suggestions by 12 specialist agents across 4 page clusters and 3 disciplines."
status: active
authority: canonical
tags: [type/research, lifecycle/active, domain/frontend]
source_paths:
  - frontend/src
  - docs/CONTINUATION-STRATEGY-2026-11-21.md
created: 2026-11-21
updated: 2026-11-21
source_commit: 1d60492
---

# Three-lens front-end audit (2026-11-21)

**Method.** Twelve read-only agents: three disciplines (Appearance, Tactile/Interaction, Functionality) × four page clusters (A home/movement, B party/person, C vote/analytics, D institutional/reporting). Every page file and its interactive/data components were read in full, cross-checked against `index.css`, `tailwind.config.js`, `api/client.ts`, `router.tsx`, backend endpoints and the vault [VISION](../20-DIRECTION/VISION.md). Complements the page-by-page [FRONTEND-AUDIT](FRONTEND-AUDIT-2026-11-21.md); no code was changed. All findings are **static-code evidence** — browser, axe, touch, print and runtime claims are NOT PROVEN.

## 1. Appearance — visual system

### Systemic findings (highest leverage)
| ID | Finding | Evidence | Severity |
|---|---|---|---|
| AP-1 | **`HeroGraphic` variant colours never apply.** `primary` = bare `"sky-400"` / `"rose-400"` etc. interpolated into `className`; Tailwind generates `text-sky-400`, not `sky-400`. All shapes use `currentColor` → every hero renders inherited slate-100 (monochrome) across all pages. | `HeroGraphic.tsx:24-56,77` (seen in all 4 appearance agents) | P1 |
| AP-2 | **Three class-name-as-paint bugs make visuals invisible.** `DataBar` callers pass hex (`#10b981`) into `className` → no fill on Grafice/Topuri/parts of Demographics; `ProgressRing` uses `stroke="slate-700/40"` / `fill="slate-200"` as SVG paint attributes (invalid CSS colours) → invisible track and black percentage text; `AgeDistributionRadial` clipped by a 200-unit viewBox with radius 115/center 125 at a 250×250 call site. | `DataViz.tsx:62,76,110,129`; `Grafice.tsx:100,108,116`; `Topuri.tsx:146`; `AgeDistributionSection.tsx:34` | P1 |
| AP-3 | **Container discipline broken.** `.wrap` missing entirely (InstitutionalView, Parties, PartyComparison, PartyTimeline, SwitchLeaderboard) while others nest it twice (LiveDashboard, CoverageView, Demographics) → left/right edges differ on nearly every route; "equal edges" holds nowhere. | `index.css:115-120`; per-cluster rows | P1 |
| AP-4 | **Tokens defined but bypassed.** Charts use literal hex/rgba/hsl and `schemeCategory10`; off-palette violet/purple/cyan/`rose` appear; `Mps.tsx:173` uses undefined `slate-750` → hover fill inert; `.stat-card` hardcodes `#38bdf8`. Light-theme overrides only rewrite Tailwind class names, not inline styles or canvas. | `index.css:34-45,76-89,237`; `tailwind.config.js:10-15`; cluster rows | P1 |
| AP-5 | **Muted-text hierarchy inverted.** `text-slate-500/600` are globally remapped to `--color-muted #a8b5c7` (8.59:1) while `text-slate-400` stays `#94a3b8` (6.96:1) → "muted" notes are brighter than regular secondary text. | `index.css:179-183`; Radar/Grafice/Report rows | P2 |
| AP-6 | **Type & surface scale fragmentation.** `font-black` moment figures outside the bold scale; Report `sm:text-4xl` vs InstitutionalView `text-2xl`; Coalitions h2 shrunk to `text-lg`; three card grammars (`InfoStat` / local `StatCard` / `.card`) and radii 4/8/12px; `text-xs` vs `text-sm` tables. | per-cluster rows; `index.css:99-104` | P2 |
| AP-7 | **Canvas charts are theme-blind and small-typed.** ECharts axis/tooltip colours are hardcoded (`#0f172a`, `#94a3b8`), 10–11px labels, violet/pink fallback palettes; contrast on heatmap cells computes ~1.85–2.08:1 (arithmetic, not measured). | `PartyAgreementMatrix.tsx:165-209`; `VoteActivityChart.tsx:28-29`; `TimelineChart.tsx:20-33`; `Ideology.tsx:22-42` | P1 |
| AP-8 | **State visuals not shared.** `ErrorState`/`LoadingState`/`EmptyState` exist but most pages use bare `text-red-400` / `text-slate-500` / hand-rolled panels; error palette alternates `rose-200`, `red-400`, `amber-400`. | cluster rows | P2 |

### Per-cluster appearance highlights
- **A (home/movement):** double gutters on LiveDashboard; two stat-card grammars on Traseism; SwitchLeaderboard table has no max-width; SwitchedLeaderboard 40px `HeroGraphic` still renders its caption; Coalitions h2 inverted hierarchy.
- **B (party/person):** `Mps` `slate-750` inert hover; PartyProfile dropped colour and shows a committee hero on a party page; MpComparison 3 stats in a 4-column grid; PersonDeepDive hero layout differs from PartyProfile.
- **C (vote/analytics):** Idealogy's 15-colour palette includes violet/pink and is reassigned on year change; Heatmap gradient label contrast ~2:1; Grafice/Topuri bars invisible; ProgressRing unreadable.
- **D (institutional/reporting):** InstitutionalView no `.wrap` and `text-2xl` h1; SenateHistory "Full Coverage %" uses rose (danger) accent; LegislatureDetail 2 cards in a 3-column grid; Report prints decorative sparkles without `print:hidden`.

## 2. Tactile — interaction & "feel"

### Systemic findings
| ID | Finding | Evidence | Severity |
|---|---|---|---|
| TA-1 | **`cursor-pointer` with no action / keyboard-inert controls.** SVG `<g>/<rect>/<path>/<circle>` and `<div onClick>` advertise clicks but have no `tabIndex`, `role`, `onKeyDown` or focus ring: Sankey links/nodes, `AgeDistributionRadial` arcs (callback never passed by sole consumer), `TimelineStrip` wave circle (empty TODO handler), `PartyNetwork` nodes, `SwitchTimeline` bars, `CrossChamberFlow` bars, `CommitteeControl` bar, `PartyListTable` rows & "View all" span, switch-leaderboard loyalty `title` spans. | tactile A/B/C/D rows | P1 |
| TA-2 | **Keyboard scroll containment missing on wide tables.** Correct pattern (`overflow-x-auto tabIndex=0 role=region aria-label`) exists in many places but is absent on Parties, PartyProfile movements, PersonDeepDive events/committee lists, Grafice, Topuri, Ideology legend, LegislatureDetail movement list, LiveFeed. | tactile A/B/C/D rows | P1 |
| TA-3 | **Focus indication is actually consistent (positive).** Global `:focus-visible{outline:2px solid #38bdf8;outline-offset:2px}` (`index.css:198-201`, light override `:89`) is inherited everywhere; local `focus:outline-none focus:ring-2` on some inputs overrides it and fires on mouse clicks — cosmetic split-brain, not absence. | `index.css:198-201`; rows | P2 |
| TA-4 | **Press feedback and touch targets weak.** Only `.btn-hover` provides `:active{scale:.97}`; many buttons use bare `btn`/`hover:`. Inline `ml-3 underline` retries (~16px) recur in CoverageView, InstitutionalView, LegislatureDetail; selects are 30–36px; SVG hit areas 12–32px; footer links ~16px. Standardize `btn btn-hover min-h-11` and one RetryButton. | `index.css:152-154`; rows | P2 |
| TA-5 | **Tooltips are native `title` only** (Sankey, leaderboard loyalty, heatmap cells, committee bars, timeline bars) — hover-only, no focus/touch, no close control; need `aria-describedby` + `role="tooltip"` on hover/focus. | rows | P2 |
| TA-6 | **Reduced-motion honoured in CSS but not canvas/autoplay.** `index.css:203-212` neutralises CSS animations; only `VoteActivityChart` sets `animation: !reduceMotion`. `PartyAgreementMatrix`, `Ideology`, `TimelineChart` and `TimeSlider`'s 300ms autoplay loop animate regardless. | rows; `TimeSlider.tsx:39-56` | P2 |
| TA-7 | **Dialogs: robust in some, incomplete in others.** `About.tsx` and `PersonDrawer.tsx` trap Tab, Escape-close, lock body scroll and restore focus (exemplars). Generic `ui/Modal`/`ui/Drawer` omit form controls from the trap selector, let Tab escape when empty, and Drawer lacks body scroll lock + accessible name. **All of About's careful interaction is unreachable** — `setAboutOpen(true)` is never called in Traseism. | tactile A/B/D rows | P1 |
| TA-8 | **False affordance on static rows.** `hover:bg-*` on actionless `<tr>` (Committees, SenateHistory, switch-leaderboard, Coalitions) highlights without any action or cursor change. Remove the hover or make the row actionable. | rows | P2 |

### Positive patterns to preserve
`Search.tsx` full ARIA combobox (arrow keys, Escape, outside-click, `aria-activedescendant`); `TimeSlider` native range + `aria-pressed` + `min-h-11`; `PersonDrawer`/`About` focus traps; global focus ring; keyboard-scroll regions where implemented.

## 3. Functionality — behaviour & data contracts

### Systemic findings
| ID | Finding | Evidence | Severity |
|---|---|---|---|
| FN-1 | **`date`/`as_of` is a URL veneer.** Routes validate and propagate `?date=` but almost no page reads it. Only InstitutionalView and LegislatureDetail wire it into query keys/params. Committees, CoverageView, SenateHistory, Report, Parties, PartyComparison, PersonDeepDive, Mps, MpComparison, Voturi, Radar, Grafice, Topuri, Ideology, Demographics, PartyTimeline ignore it. One shared `useAsOf()` hook is the root fix. | functional A/B/C/D rows | P1 |
| FN-2 | **"Switch" has ≥3 incompatible definitions under one label.** group-only (`traseism.py:39`, leaderboard, `switches_in`, Report/export), group+party all-time (`api.py:1061-1066`), dated membership joins shown as "Total switches" (PartyTimeline), merged group+party under "Group switches" (PersonDeepDive). Each SQL is consistent; the UI is mutually unintelligible. | rows | P1 |
| FN-3 | **Page-local slices labelled corpus totals.** Mps 60-row page, MpComparison 200-row pool, SwitchLeaderboard top-N sums, Topuri 100-row cap, CoverageView overall % derived from rounded percentages, "Total members" = expanded committee cards, SenateHistory all-chamber count under "Senate Members". | rows | P1 |
| FN-4 | **Unknown/null coerced to displayed 0 or fabricated values.** PartyProfile missing party-switch data → 0; PartyComparison `status:"unavailable"` chairs → 0; CoverageView null `dated_pct` → 0; Report `"partial"` coverage → fabricated 60% ring; Ideology null CHES scores → plotted `0.00`; sparklines interpolate unseen calendar days as zeros; Topuri rebellion counts abstain/not-voting as "rebel". | rows | P1 |
| FN-5 | **Loading/error/empty states inverted or missing.** Zero-valued stats render as facts during fetch (Demographics, PartyTimeline, CoverageView, SenateHistory); errors shown as "no data" (Coalitions, Radar, PartyComparison, SenateHistory); LiveDashboard widgets show perpetual "Loading…"; retries absent on most error branches. | rows | P1 |
| FN-6 | **Provenance exists in API, absent from DOM.** `source_url`, `confidence`, `date_precision`, `snapshot_hash`, `CoverageRow.note`, committee member source/precision, movement reason — all dropped at render. EN report footer falsely calls derived metrics "observed". | rows | P1 |
| FN-7 | **Filter/sort/pagination/selection state not in URL.** All in component `useState`; deep links, back/forward and shareable filtered views do not work. Vote detail (`selectedVoteId`) not deep-linkable; Ideology "All years" is a no-op; ChES year options collapse to one after filtering. | rows | P2 |
| FN-8 | **Vote analytics scoped to empty data.** Grafice hardcodes `2024/deputies` while the local corpus is entirely `2020/deputies`; Radar hardcodes limit 30 and any failed positions query blanks the matrix; hard 100-row caps ignore the backend `total`; `positions_incomplete=true` on all 52 local votes is never surfaced though vote-level and position-level yes counts diverge (11008 vs 6258). | functional C rows | P1 |
| FN-9 | **Mislabelled or wrong headline metrics on reporting pages.** Report "Party switches"=group-only, "deputies in corpus"=all persons; SenateHistory "%" stat is an integer count; LegislatureDetail unknown year renders 1990 data; its movements endpoint has no legislature filter; Demographics "Total MPs"=birth-dated only, mean-of-means, 100% coverage by construction. | functional D rows | P1 |

### Positive patterns to preserve
InstitutionalView's full `useSearch → asOf → query key + API param → navigate(replace)` wiring; LegislatureDetail's date clamping; Report/Committees loading/error gating with retry; `api/meta` as a real scope source where used.

## 4. Enhancement order (cross-discipline, highest leverage first)

1. **Visual primitives** — fix `HeroGraphic` colour classes, `DataBar` paint API, `ProgressRing` SVG colours and radial clipping; add one `surface`, `.page-title`, `.moment-value`, `.data-table` and `.badge` utility. Touches all 23 pages.
2. **One scope hook** — `useAsOf()` + chamber/legislature from route search, included in every query key and API call; add in-page date controls where missing.
3. **One canonical switch definition** — return both counts with labels from the backend; relabel every card, table and page; use API `total`/aggregates, never rendered arrays, for headline figures.
4. **One state system** — shared `LoadingState/EmptyState/ErrorState` with retry, gated `isLoading → isError → empty → data`; never render 0 as data.
5. **Semantics for tactile controls** — native `<button>/<a>` for every pointer affordance; keyboard-scroll wrappers; `min-h-11`; `btn-hover` + one RetryButton; `aria-describedby` tooltips; `animation: !reduceMotion` on all canvases.
6. **Provenance at the table layer** — render source URL, confidence, precision, snapshot hash and backend notes wherever the API supplies them.
7. **i18n sweep + key-diff gate** — the missing keys are documented per page in the prior audit; this triad confirms the pattern across all clusters.
8. **Vote-scope correction** — make vote pages query the legislature/chamber where data actually exists, surface `positions_incomplete`, paginate with `total`.

## 5. NOT PROVEN

No browser render, screenshot, computed-style/contrast measurement, 320px reflow, axe/WCAG-AA run, keyboard walk, touch-device test, print preview, live API payload or production-parity check was performed by these agents. All contrast figures are arithmetic on authored values; all "invisible" conclusions are CSS/SVG semantics. They must be confirmed with a browser pass before being claimed as observed facts.

## See also

[FRONTEND-AUDIT](FRONTEND-AUDIT-2026-11-21.md) · [ACTION-PLAN](../20-DIRECTION/ACTION-PLAN.md) · [QA-AND-AXE](QA-AND-AXE.md) · [STACK-AND-TOKENS](STACK-AND-TOKENS.md) · [DESIGN-CONTRACT](DESIGN-CONTRACT.md)
