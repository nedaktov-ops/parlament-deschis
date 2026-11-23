---
id: CLICK-INVESTIGATION
type: research
title: "Front-end clickable investigation — master report (2026-11-22)"
description: "Evidence-only inventory and defect report for every button, link and click handler in the SPA: 258 elements across seven fleet recipes, verified findings, browser corroboration and a repair-ready action list."
status: active
authority: canonical
tags: [type/research, lifecycle/active, domain/frontend]
source_paths: [frontend/src, backend/routers, scripts/ui_validate.py]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Front-end clickable investigation — master report

**Status: COMPLETE (investigation only; no repairs made).** Journey and wave
log: [CLICK-INVESTIGATION-JOURNEY](../50-RESEARCH/CLICK-INVESTIGATION-JOURNEY-2026-11-22.md).
Supplementary runtime observations:
[CLICK-BROWSER-OBSERVATIONS](../60-EVIDENCE/CLICK-BROWSER-OBSERVATIONS-2026-11-22.md).
Earlier non-click-specific audit: [FRONTEND-AUDIT](FRONTEND-AUDIT-2026-11-21.md).

## 1. Method and evidence contract

Seven read-only specialist agents each read an assigned slice of
`frontend/src` in full at local HEAD `8811216`, resolved labels against both
`i18n.ts` locales, traced every callback to its terminal navigation/API/state
call, and cross-checked every destination against the router route tree and
the FastAPI decorators. Every claim carries `file:line`. Verdicts are limited
to `WORKING-AS-CODED`, `BROKEN`, `SUSPECT` and `NOT PROVEN`; no claim rests on
inference alone. Browser results are kept separate in the evidence note above
and are never the sole basis for a defect. No code, data, config or git state
was changed by the investigation.

## 2. Fleet recipe outputs (full element tables live here)

- [C-01 SHELL — router, nav, footer, modals](CLICK-INV-C01-SHELL-2026-11-22.md) — 61 elements, 0 BROKEN, 5 SUSPECT, 6 NOT PROVEN.
- [C-02 OVERVIEW — dashboard, traseism, scope pages](CLICK-INV-C02-OVERVIEW-2026-11-22.md) — 58 elements, 0 BROKEN, 7 SUSPECT, 1 NOT PROVEN.
- [C-03 ENTITIES — party, MP, committee, person pages](CLICK-INV-C03-ENTITIES-2026-11-22.md) — 51 elements, 1 BROKEN, 5 SUSPECT, 4 NOT PROVEN.
- [C-04 VOTES — vote-analytics pages](CLICK-INV-C04-VOTES-2026-11-22.md) — 26 elements, 1 BROKEN, 3 SUSPECT, 0 NOT PROVEN.
- [C-05 COMPONENTS — shared interactive components](CLICK-INV-C05-COMPONENTS-2026-11-22.md) — 62 elements, 0 BROKEN, 1 SUSPECT, 1 NOT PROVEN, plus 6 dead/unwired controls.
- [C-06 DESTINATIONS — routes, endpoints, external URLs](CLICK-INV-C06-DESTINATIONS-2026-11-22.md) — 100 targets checked, 0 unmatched, 4 SUSPECT, 7 NOT PROVEN.
- [C-07 HARNESS — existing checks and known defects](CLICK-INV-C07-HARNESS-2026-11-22.md) — 6 checks reviewed, 2 clickable-related, 6 gaps.

**Totals:** 258 clickable elements inventoried; 100 navigation/API/URL targets
checked; 2 BROKEN, 25 SUSPECT (before deduplication), 19 NOT PROVEN, 7
defined-but-never-rendered controls (6 from C-05 plus `mps.compareLink`). All 42 navigation call sites resolve to a
registered route and all 42 API paths resolve to a FastAPI decorator — there
is **no missing route or missing endpoint** behind any rendered click target.

## 3. Confirmed BROKEN — repair first

| ID | Location | Expected behaviour | Actual behaviour (evidence) | Improvement | Verified by |
|---|---|---|---|---|---|
| B1 | `frontend/src/pages/Ideology.tsx:253-255`, handler `:250`, fallback `:80`, filter `:84` | "All years" (`value=""`) shows every CHES wave | `:250` maps `""` → `undefined`; `router.tsx:553` drops undefined search keys; `:80` then substitutes `years[0]`; `:84` filters to that one year. Browser: selecting "Toți anii" snapped back to 2024 and the table kept only 2024 rows (B4 in the browser note). | Use an explicit sentinel (e.g. `chesYear="all"`), keep it in the URL, and skip the `:84` filter when it is set; or remove the option if single-wave display is intended. | C04 F1 + my code re-read + browser |
| B2 | `frontend/src/i18n.ts:520` / `:1266` (`mps.compareLink`), route `/compare-mps` at `router.tsx:458` | A visible "Compare MPs →" affordance on `/mps` | `grep compareLink` returns only the two i18n definitions; no `<Link to="/compare-mps">` exists in any page. The label is defined but no element is ever rendered. | Either render the link on `/mps` (the route already exists) or delete the two dead keys. | C03 F4 + my grep |

## 4. SUSPECT findings — grouped by repair theme

Deduplicated from the recipe notes; each row keeps its source ID and exact code anchor.

### 4.1 Navigation loses or distorts scope

| ID | Evidence | Problem | Improvement |
|---|---|---|---|
| C01 F1 / C06-008 | `Footer.tsx:65,73,81,123` native `<a href>` vs `router.tsx:110-118` `<Link>`; browser B3 destroyed the execution context on click | Full document reload; `date`/`chamber`/`legislature` scope not carried | Replace the four anchors with `Link`/`NavLink` using `scope.searchFor()` |
| C02 F1 | `LiveDashboard.tsx:140,151,162,174` pass `linkTo` but no `searchParams`; `DashboardCard.tsx:81` renders `<Link search={searchParams}>` | Four stat cards drop scope on navigation | Pass `search={scope.searchFor()}` at the four call sites |
| C02 F2 | `LiveDashboard.tsx:277` ignores `wave`, hardcodes `chamber:"deputies", legislature:undefined`, despite the "select one for details" copy | Clicking a specific switch wave opens a generic traseism view | Carry the wave date into the destination search |
| C02 F3 | `Traseism.tsx:294-296,311-313` never clamps `page` when `total` shrinks | Next/prev can point past the last page after data changes | Clamp `page` to `totalPages` in an effect |
| C03 F2 | `Mps.tsx:47` `canNext = offset + rows.length < total`; `PAGE_SIZE=60` at `:12` | Next disables early on a short page | Use `offset + PAGE_SIZE < total` |

### 4.2 Controls that do less than their label says

| ID | Evidence | Problem | Improvement |
|---|---|---|---|
| C04 F4 | `Voturi.tsx:51` comment, `:53` query key, `:74-80` client filter; offset reset only on `activeKey` (`:47-49`) | Title search filters only loaded rows and does not reset pagination | Send `query` to the API (if supported) or label it as page-local and reset offset |
| C04 F3 | `RollCallTable.tsx:23` fetches positions with no limit; backend default 100 at `api.py:1387` | Source anchors for positions beyond 100 never render | Request the full page or paginate the table |
| C02 F4 | `CommitteeControl.tsx:97-116` + `LiveDashboard.tsx:227` guard | Chair button can be a silent no-op when the id is falsy | Disable the button with an explanatory label when no chair exists |
| C03 F1 | `PartyProfile.tsx:177-202` `<button>` with `onClick={() => m.person && ...}` at `:178` | Silent no-op for rows without a person; also wraps a provenance `<a>` (`ProvenanceStamp.tsx:46`) — invalid nested interactive markup | Add `disabled={!m.person}` and move the provenance link outside the button |
| C03 F5 | `PartyComparison.tsx:44-47,178-202` defaults "PSD"/"PNL" not checked against loaded list | Default selections may render with no valid option | Validate defaults after data loads |

### 4.3 Accessibility and markup

| ID | Evidence | Problem | Improvement |
|---|---|---|---|
| C05 F1 | `Hemicycle.tsx:107-120`: `<circle onClick>` inside `<svg aria-hidden="true" focusable="false">`, no `role`/`tabIndex`/`onKeyDown`; keyboard path exists separately at `:142` | Mouse-only primary seat target | Make seats `role="button"` + `tabIndex=0` + `activateOnKey`, or remove `onClick` and rely on the member list |
| C01 F2 | `Footer.tsx:96-104` labels a GitHub URL with `t("about")`, while header `t("about")` opens `AboutModal` (`router.tsx:249-253,329`) | Same label, two different destinations | Rename the footer item (e.g. "Source code") or point it at the in-app About dialog |
| C06-013 | `About.tsx:6` `https://github.com/parlament-deschis` vs `router.tsx:178` and `Footer.tsx:97,107` `https://github.com/nedaktov-ops/parlament-deschis` | Inconsistent project URL literals; which resolves is NOT PROVEN | Use one shared constant |
| C04 F2 | `Topuri.tsx:120` hard-coded "Minimum votes"; no key in either `i18n.ts` locale | Untranslated control label | Add `t("filter.minVotes")` in ro and en |
| C05 F8 | "View all →" literals in three live components | Hard-coded English labels | Add an i18n key and resolve it |

### 4.4 Dead / unwired code (no user-visible break, but a future trap)

`EmptyState` CTA (`C05 F2`: no caller passes `onCta`), `LoadingState` retry
(`C05 F3`), `DashboardCard` button branch (`C05 F4`: all four callers pass
`linkTo`), `PartyComparisonMatrix` (`C05 F5`), `TimeSlider` (`C05 F6`),
`AgeDistributionRadial` arcs (`C05 F7`: sole caller `AgeDistributionSection.tsx:40`
omits `onCohortClick`), `mps.compareLink` (B2 above). Delete or wire them;
each one is a control that can never be reached.

### 4.5 Verification/harness gaps

`check_routes_nav.mjs:10` scans only literal `<NavLink to="...">` text, missing
15 page-level links, dynamic `linkTo` and redirects; its line comments are
stale (C06-009). `ui_validate.py` visits 24 routes by URL and runs axe but
never clicks; `ui_state_probe.py:84,95` counts retry buttons without clicking
them (C07). `ci.yml:130,136,138` explicitly skips `ui_validate.py`. Six minimal
test additions are specified in [C-07](CLICK-INV-C07-HARNESS-2026-11-22.md) §4.

## 5. What was checked and found correct

- All 22 `NavLink` targets, recovery links, global Search, redirect targets and
  page-level `<Link>`/`navigate` targets resolve to registered routes, with
  correct `$` param shapes (C06-001…006).
- `/Voturi` uppercase spelling is consistent at `router.tsx:316,486` and the
  page's own navigate calls (C04); no lowercase target exists.
- `/electoral` is intentionally redirect-only (`router.tsx:348-362`) and is the
  only registered route with no inbound click (C06-007).
- The Traseism About button can open the modal: `Traseism.tsx:952` → `setAboutOpen(true)`
  → `About.tsx:139` guard releases (C02 F5). The older audit's "never opens"
  claim is contradicted at HEAD.
- All 42 API paths in `frontend/src/api/client.ts` match a FastAPI decorator
  with GET/GET agreement; the scorecard shadowing is explicitly neutralised at
  `api.py:1726-1740` (C06-010, C06-012).
- `Report.tsx:166` `window.print()` and `:172` `/api/export/report` resolve to
  `exports.py:25,180-205`, including the matching attachment filename (C04).
- `Parties.tsx:107-119` `role="button"` row has a real Enter/Space handler —
  not a keyboard dead end (C03, special check).
- The four dashboard stat cards and the two `/mps` cards are intentional
  duplicates by code, not an accidental double-binding (C01/C06 observations;
  the scope-drop issue is separate, §4.1).

## 6. NOT PROVEN register

Reachability of all external URLs (GitHub, Wikidata, methodology, licenses) —
resolver: network probe. Data-driven `source_url`/`snapshot_url` correctness —
resolver: API payload comparison. ECharts `dataZoom` keyboard reachability
(`VoteActivityChart.tsx:106-109`) — resolver: AT runtime test. Browser behaviour
of `/ideology` in production — resolver: a loaded production response (the
page showed only "Se încarcă…" with zero selects). Runtime axe/contrast,
320 px reflow, keyboard-only traversal, and print/PDF — resolver: dedicated
browser pass. Which SHA each live host serves and why local/production counts
differ (B1 in browser note) — resolver: deployment metadata and release pin.
No NOT PROVEN item has been promoted to a defect.

## 7. Repair hand-off order

1. **B1** Ideology "All years" — one file, browser-confirmed.
2. **§4.1** scope preservation (footer links, four stat cards, wave click,
   pagination bounds) — the highest-volume navigation risk.
3. **§4.2** silent no-ops and the truncated vote-position source links.
4. **§4.3** nested-interactive markup, Hemicycle keyboard path, URL/label
   consistency, untranslated labels.
5. **§4.4** delete or wire dead controls.
6. **§4.5** add click-through checks so the fleet's work is regression-proof.

Each repair must bump `updated` on the affected recipe note in the vault and
re-run `python3 scripts/vault_sync.py --check` plus
`python3 scripts/vault_lint.py`, per [AGENTS](../00-START/AGENTS.md).

## See also

[TRIAD-AUDIT](TRIAD-AUDIT-2026-11-21.md) ·
[FRONTEND-REPAIR-STRATEGY](../20-DIRECTION/FRONTEND-REPAIR-STRATEGY.md) ·
[START-HERE](../00-START/START-HERE.md)
