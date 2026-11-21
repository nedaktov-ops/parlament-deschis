---
id: FRONTEND-AUDIT
type: research
title: "Exhaustive front-end audit — 2026-11-21"
description: "Element-by-element audit of all 23 pages plus shell, routing and shared components by 24 specialist agents, with vision discrepancies and prioritised remedies."
status: active
authority: canonical
tags: [type/research, lifecycle/active, domain/frontend]
source_paths:
  - frontend/src
  - docs/CONTINUATION-STRATEGY-2026-11-21.md
created: 2026-11-21
updated: 2026-11-21
source_commit: f70aca3
---

# Exhaustive front-end audit (2026-11-21)

**Method.** 24 read-only specialist agents: one per page (23), plus one for the
shell/router/shared components. Each read its file(s) in full and cross-checked
API contracts, i18n, CSS, backend sources and the vault [VISION](../20-DIRECTION/VISION.md).
No code was changed. All findings are static-code evidence; browser/axe/runtime
claims are explicitly NOT PROVEN.

## 1. Verdict

The front-end implements a broad feature surface (24 registered routes, 23
pages, ~33 components) and has good a11y scaffolding in many tables (scope,
captions, keyboard-scroll regions, focus rings). But it has a **systemic
content-honesty problem**: headline numbers are frequently page-local, capped,
or mislabelled; the project's own trust invariants ("labelled definitions",
"provenance on every row", "never present an estimate as observed") are
repeatedly breached in the presentation layer even when the backend is correct.

## 2. Cross-cutting defects (highest leverage)

| ID | Defect | Evidence | Severity |
|---|---|---|---|
| X1 | **Unlabelled/mislabelled counts** — "Switches" alternates between 1,217 group-only and 2,002 group+party; "Total MPs" on `/mps` and `/compare-mps` is a 60/200-row page cap presented as a corpus total (3,388); SenateHistory sums all 20 coverage rows (5,282) under a "Senate Members" label | LiveDashboard A04, Traseism A2, Mps 1, MpComparison A01, SenateHistory S1, Report A2, LegislatureDetail LD-2, Grafice G5 | P1 |
| X2 | **Date/as-of is accepted in URL but ignored by most pages** — PersonDeepDive, Committees, PartyComparison, LegislatureDetail, Radar, Voturi, Grafice either drop `date` or have no control; "any moment 1990–today" is not delivered | PersonDeepDive A2, Committees A3, PartyComparison C5, Radar A2 | P1 |
| X3 | **Error/empty conflation and zero-valued stats during loading** — several pages render 0/0% as fact, show "no data" on errors, or swallow `isError` | Demographics A8, CoverageView A4, PartyTimeline (stats 0), Coalitions C5, SenateHistory S4/S5 | P1 |
| X4 | **i18n gaps** — dozens of `t(key, "English…")` calls have no ro/en entry; Romanian users see English; a few keys resolve to raw key strings (`nav.parties`, `senateStatLegislatures`) | Shell C-01, LiveDashboard A10, CoverageView A5, Ideology A2, PartyTimeline (5 keys), Report A4, Coalitions C7, Topuri T6 | P1 |
| X5 | **Dead/unreachable UI and routes** — 6 routes with no nav link (`/compare-mps`, `/Voturi`, `/radar`, `/grafice`, `/topuri`, `/ideology`); rich `About.tsx` and `LiveFeed.tsx` have no importer; `Modal`/`Drawer`/`TimelineStrip`/`LoadingState` partially unused; `Traseism` About modal never opens | Shell V-01/D-01/D-04/D-05, LiveDashboard A01, Traseism A1 | P1 |
| X6 | **Provenance dropped at the table layer** — API rows carry source_url/confidence/precision/snapshot_hash; pages discard them (Traseism, Committees, PartyProfile, PersonDeepDive, CoverageView, SenateHistory, PartyTimeline, Ideology) | per-page findings; VISION §2.1 | P1 |
| X7 | **Chart/a11y debt** — canvas charts with only aria-label and no data alternative; hex colours passed as Tailwind class names (`DataBar`), making bars invisible; colour-only legends; unkeyboardable SVG nodes/spans | Grafice G3/G10, Topuri T2, Radar A6/A16, Ideology A4, SankeyFlow A4, LiveDashboard A15 | P1/P2 |
| X8 | **Vision features present only as proxies or placeholders** — Bureau composition static placeholder; Coalition Stability is a switch-wave proxy with hardcoded trigger dates ±90 d, not coalition facts; Ideology claims PopuList as source but queries CHES only; PartyProfile dropped colour/in-out/net from an earlier revision | InstitutionalView IV-1/IV-2, Coalitions C1–C4, Ideology A6/A9, PartyProfile T1/T4 | P1 |

## 3. Page-by-page highlights (all 23)

| Page | Top finding(s) | Severity |
|---|---|---|
| LiveDashboard | LiveFeed/switch alerts unreachable; stat links drop `date`; two cards share `/mps`; hardcoded English widget copy; unequal edges | P1/P2 |
| Traseism | Sankey says "both directions" but drops 108 cycle pairs; ledger omits confidence/snapshot; party-switch view never rendered; 142 waves truncated to 10 | P1 |
| SwitchLeaderboard | Scope note inverted vs backend; 1-switch MPs score 100 "loyal"; hero stats are top-N sums; "party switching" counts group-only | P1 |
| Demographics | Default view is current-only, mislabelled "all"; "Total MPs" = birth-dated only; mean-of-means not population age | P1 |
| Committees | 23/9 vs 26 unlabelled; "Total members" = expanded cards only; no `as_of`; no row provenance; Senate filter always empty | P1 |
| Mps | Page-local 60-row stats labelled corpus totals; no scope/date filters; phantom pagination; dead `compareLink` | P1 |
| MpComparison | 200-row pool shown as "Total MPs" (3,388); search only over pool; orphan route; false committee-scope note | P1 |
| Parties | Entire copy English fallback; "Switches in" group-only vs profile party-switch; no sort/date | P1/P2 |
| PartyComparison | Committee "0" hides missing/unavailable; no `as_of`; "▲ better" on switch counts | P1 |
| PartyProfile | Redesign dropped colour/in-out/net; "Total switches" = party-only null→0; no provenance on movements; no committee/loyalty/export | P1 |
| PartyTimeline | 5 missing i18n keys; "Total switches" = dated joins; gap panel permanently 0; wrong hero graphic | P1 |
| PersonDeepDive | "Group switches" merges party switches; `date` param ignored; event provenance absent; no loyalty/network/export | P1 |
| Voturi | Orphan route; two hard 100-row caps; `positions_incomplete` hidden; both-chamber claim vs cdep-only; no server filters | P1 |
| Radar | Orphan route; no scope; pooled chambers; limit 30/500; tie-dependent "dominant"; no colour legend | P1 |
| Grafice | Promises cohesion timeline/defection markers that don't exist; DataBar hex-in-className; switch block hidden behind vote empty state | P1 |
| Topuri | Table not ranked by loyalty/rebellion; DataBar invisible; rebellion counts abstentions; hardcoded English headers | P1 |
| Ideology | "Not yet ingested" note rendered on top of populated chart; 5 missing i18n keys; null→0 fabricated points; PopuList misclaim | P1 |
| Report | "Partial" coverage converted to fabricated 60%; "Party switches" = group-only; EN footer calls derived metrics observed | P1 |
| CoverageView | Not wired to `/api/coverage/dimensions`; definitions/note dropped; six English labels; misleading zeros | P1 |
| SenateHistory | All-chamber 5,282 under "Senate Members"; "%" stat is a count; HOLD decision not disclosed; wrong licence claim | P1 |
| InstitutionalView | Bureau card permanent placeholder; committee names only; no control data or provenance | P1 |
| LegislatureDetail | Unknown year renders 1990 data; group-only capped "Switches"; raw event codes; no date control | P1 |
| Coalitions | Hardcoded trigger dict ±90 d sold as corpus facts; methodology text false; false empty states during load | P1 |

## 4. Discrepancies with vision/objectives

1. **"Trustworthy statistical source" (VISION §1–§2) vs presentation layer**: most
   trust invariants hold in the pipeline/DB but fail in the UI through labels,
   caps and dropped provenance. The fix is largely presentational, not new data.
2. **"Any moment from 1990 to today" (README tagline)**: URL date is accepted
   but ignored on nearly every page; only a few pages have date inputs.
3. **"Bilingual Romanian-first"**: widespread English fallbacks and raw keys.
4. **"Votes as first-class events"**: the centrepiece pages are orphaned, capped
   at 100 rows, and empty in production.
5. **"15-feature platform"**: bureau composition, loyalty score, network,
   genealogy (formally dropped), assets, coalition facts exist only as proxies
   or placeholders.
6. **"One coherent design system / WCAG AA"**: hex colours, invisible bars,
   unlabelled canvases, keyboard-inert SVG nodes, inconsistent state components.

## 5. Recommended order (highest leverage first)

1. **Label every count and denominator** (X1) — add explicit definitions to all
   "Switches"/"Total MPs"/"Coverage" cards; derive totals from API `total`, not
   page arrays. Background agent-owned fix, one row per page.
2. **Make `date`/`as_of` real** (X2) — wire route search params into queries and
   add controls; start with Committees, PersonDeepDive, PartyComparison.
3. **Honest states** (X3) — gate stats behind `isLoading/isError`, add retry,
   stop rendering 0 as data; reuse shared `EmptyState/ErrorState/LoadingState`.
4. **i18n sweep** (X4) — add missing keys to both locales; enforce a key-diff gate.
5. **Nav/route cleanup** (X5) — link the 6 orphan routes or mark them deprecated;
   wire `About.tsx` and `LiveFeed.tsx` or delete them.
6. **Provenance at the table layer** (X6) — render source/confidence/precision.
7. **Design-system fix** (X7) — DataBar hex→style, chart data alternatives, legends.
8. **Vision proxies** (X8) — relabel Coalition Stability honestly, make Bureau a
   labelled gap or remove it, condition Ideology's note on `dataExists`.

## 6. NOT PROVEN

No browser render, axe/WCAG-AA measurement, 320 px reflow, JS-error count, live
API payload, or production parity was tested by these agents. Several findings
are code-level inferences (e.g. invisible DataBar fills, contrast ratios) and
must be confirmed with a browser pass before being claimed as observed facts.

## See also

[ACTION-PLAN](../20-DIRECTION/ACTION-PLAN.md) · [NEXT-ACTIONS](../10-STATE/NEXT-ACTIONS.md) · [QA-AND-AXE](QA-AND-AXE.md) · [STACK-AND-TOKENS](STACK-AND-TOKENS.md) · [RESEARCH-FLEET](../50-RESEARCH/RESEARCH-FLEET-2026-11-21.md)
