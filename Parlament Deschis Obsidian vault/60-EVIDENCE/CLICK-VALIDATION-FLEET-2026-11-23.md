---
id: CLICK-VALIDATION-FLEET
type: evidence
title: "Ten-agent clickable validation fleet — results (2026-11-23)"
description: "Executable Playwright validation of every inventoried clickable element across the SPA by ten specialised agents: 364 items, 342 PASS, 3 FAIL, 19 SKIP, with raw artifacts and two corrective recipes for the real defects."
status: active
authority: canonical
tags: [type/evidence, lifecycle/active, domain/frontend]
source_paths: [frontend/src, tests/frontend_click, 40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md]
created: 2026-11-23
updated: 2026-11-23
source_commit: 863b200e1adc70aadb289fdd4df52a7e5be2c483
---

# Ten-agent clickable validation fleet — results

**Scope.** Executable validation of all 258 clickable elements inventoried by
[CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) plus
106 cross-cutting destination/harness items, on the local dev server
`http://127.0.0.1:5188`. Fleet plan:
[CLICK-VALIDATION-FLEET](../20-DIRECTION/CLICK-VALIDATION-FLEET-2026-11-23.md).
Entry branch `test/clickable-validation` @ `2da191aa…`, verified backup
`/tmp/opencode/backups/click-validation/W13`. All ten agents used their own
Chromium instance, resolved IDs from live APIs, closed browsers in `finally`,
and wrote only their exclusive test/artifact paths. Raw artifacts:
`/tmp/opencode/click-validation/v01-* … v10-*`.

## 1. Reconciled results

Counts were recomputed from the ten `vNN-results.json` files, not from agent prose.

| Agent | Slice | Items | PASS | FAIL | SKIP |
|---|---|---:|---:|---:|---:|
| V-01 | shell / nav / footer / modals | 61 | 58 | 0 | 3 |
| V-02 | overview dashboard | 20 | 20 | 0 | 0 |
| V-03 | traseism / ledger | 19 | 17 | **2** | 0 |
| V-04 | party pages | 17 | 15 | 0 | 2 |
| V-05 | MP / person / demographics | 27 | 24 | 0 | 3 |
| V-06 | institutional / committees / coverage | 26 | 26 | 0 | 0 |
| V-07 | votes list / roll-call | 14 | 13 | **1** | 0 |
| V-08 | vote analytics / report | 12 | 12 | 0 | 0 |
| V-09 | interactive primitives | 52 | 43 | 0 | 9 |
| V-10 | cross-cutting destinations / guards | 116 | 114 | 0 | 2 |
| **Total** | | **364** | **342** | **3** | **19** |

Element-ID reconciliation: V-01…V-09 exactly cover the 258 inventory IDs
(61+20+19+17+27+26+14+12+52 = 248 clickable IDs; the remaining 10 designed-absent
C05 IDs are reconciled by V-10); V-10 adds 100 destination targets and 6 harness
checks. Every result row carries element ID, source `file:line`, action,
expected and observed outcome, verdict and an existing raw evidence path.

## 2. The three real FAILs

| ID | Location | Observed | Root cause | Correction |
|---|---|---|---|---|
| C02-027 | `Traseism.tsx:421-426` | Next fires `offset=25` (HTTP 200, 20 rows) but counter/first row stay on page 1 and Previous stays disabled | W2/L-06 clamp at `Traseism.tsx:312-314` fires while the new query is pending (`total=0 → totalPages=1`), resetting page to 0; 1 h staleTime makes it silent. `staleTime` is **not** the cause | Recipe **L-25** in [LINK-PAGINATION-CORRECTION](../20-DIRECTION/LINK-PAGINATION-CORRECTION-2026-11-23.md) — guard clamp on `query.isSuccess` |
| C02-026 | `Traseism.tsx:414-419` | Previous never enables — dependent on C02-027 | same | same |
| C04-012 | `Voturi.tsx:354-359` → `ProvenanceStamp.tsx:42-50` | Vote-detail HTTP 200 with `data.source_url`, but no provenance anchor renders | Backend returns envelope `{status,data_exists,data}` (`api.py:1344-1381`); `client.ts:351-369` types `VoteDetail` as unwrapped and `get<T>` does not unwrap, so the call site reads top-level `source_url` = undefined | Recipe **L-26** in [LINK-PROVENANCE-CORRECTION](../20-DIRECTION/LINK-PROVENANCE-CORRECTION-2026-11-23.md) — unwrap at the call site, matching `RollCallTable.tsx:29-31` and other consumers |

Both corrective recipes have disjoint exclusive file sets and are scheduled as
W14 and W15 after this fleet, with fresh backups, regression re-runs and
supervisor sign-off. No merge to `main` without the owner gate.

## 3. SKIPs (19) — all with named resolvers

- **C01-002** error-boundary link (no deterministic in-UI trigger → fault injection).
- **C01-059 / C01-060** LoadingState retry and EmptyState CTA — designed-absent
  after W11; resolver: validate against source commit `8811216`.
- **C03-005 / C03-036 / C03-045** Wikidata anchors — 0/37 parties and 0/15
  sampled persons have `wikidata_qid` → rerun with enriched payload.
- **C03-006 / C05-005…010** PersonDrawer openers — party movements payload empty
  for all live parties → rerun with dated movements or a live drawer route.
- **C03-049 / C05-014 / C05-016** archive/snapshot anchors — no `snapshot_url`
  in served corpus → rerun with archived evidence.
- **C05-050** ECharts dataZoom — canvas-only drag; keyboard/AT reachability not
  determinable → accessible out-of-canvas control or `aria.enabled` probe.
- **C06-T092** data-driven external hrefs → API payload comparison.
- **C07-002** axe scan → run `scripts/ui_validate.py` with `/tmp/axe.min.js`
  under the lead's axe gate.

No SKIP was promoted to PASS and no SKIP is a click FAIL.

## 4. Console discipline

Every `console.error` recorded (V-01: 2, V-02: 12, V-06: 22, V-08: 13, V-09: 19,
V-03: 28) is explicitly labelled `test_induced` / injected API abort used to
exercise retry and error states. Zero non-induced product console errors and zero
`pageerror` events were observed by any agent. Nothing was filtered or suppressed.

## 5. Notable validated repairs (post-repair code)

- Ideology "All years": `chesYear=all`, 38 rows across 6 distinct years (V-08).
- Footer/nav/card scope preservation and wave date carry-through (V-01/V-02).
- Compare MPs link and `PAGE_SIZE` pagination bound (V-05).
- Vote-position `limit=500` and honest truncation note (V-07).
- Topuri translation and min-votes URL/API linkage, print and export download
  (V-08).
- Keyboard-only traversal reached all 22 nav links; export returned a valid
  16,523-byte JSON (V-10).

## 6. Scope/honesty limits

Served dev HEAD was `e82e01b9152266bf3fe862029946b24acc2032f8` (vault-only
commits ahead of source commit `863b200e…`); this is recorded in agent evidence.
Results are **local dev only** — no production claim. axe/AT, data-dependent
links and external reachability remain NOT PROVEN with the resolvers above. This
report is an aggregation of executed tests, not a new investigation.

## See also

[CLICK-INVESTIGATION-JOURNEY](../50-RESEARCH/CLICK-INVESTIGATION-JOURNEY-2026-11-22.md) ·
[LINK-REPAIR-JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) ·
[CLICKABLE-FLEET-SUBTASK-REPORT](../40-FRONTEND/CLICKABLE-FLEET-SUBTASK-REPORT-2026-11-23.md)
