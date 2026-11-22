---
id: REPAIR-WAVE-OUTCOMES
type: state
title: "Front-end repair wave outcomes"
description: "Per-wave PASS/FAIL/AMBER decisions with raw gate evidence, backups, commits and next-step decisions during implementation of the nine repair recipes."
status: active
authority: canonical
tags: [type/state, lifecycle/active, domain/frontend]
source_paths:
  - docs/repair-recipes
created: 2026-11-21
updated: 2026-11-21
source_commit: 618849a
---

# Repair wave outcomes

Master record for the supervised implementation of
[FRONTEND-REPAIR-STRATEGY](../20-DIRECTION/FRONTEND-REPAIR-STRATEGY.md) and its
nine recipes. Rule: a wave is PASS only when every blocking gate printed a
green result; an unrun check is NOT PROVEN, never PASS.

## W0 — Safety / backups — **PASS**

| Item | Evidence |
|---|---|
| Baseline | branch `repair/w0-safety` from `origin/main` `618849a` |
| Backup | `/tmp/opencode/backups/W0/618849a/pre-w0.bundle`, `parlament-real.db` (43,589,632 B), `latest-release.txt`, vault copy |
| Manifest | `sha256sum -c MANIFEST.sha256` → `pre-w0.bundle: OK`, `parlament-real.db: OK`, `latest-release.txt: OK` |
| Restore drill | `git clone --no-local` → HEAD `618849a` (matches baseline) |
| Product tree | unchanged — backup + vault outcome note only |
| Blocking gates | G00–G02 GREEN |

**Decision:** PASS. Proceed to W1 (visual foundation: R-01 → R-02) only after the
supervisor plan confirms recipe file ownership and the axe prerequisite is
resolved.

## W1 — Visual foundation (R-01, R-02) — **AMBER (both recipes' owned gates PASS)**

### R-02 — Layout / type scale — **PASS (owned gates); AMBER wave**

| Item | Evidence |
|---|---|
| Commit | `3f1f175` — 26 files, 138 insertions / 138 deletions |
| Scope | 26 R-02-owned files only; `git diff --check` clean; R-01 utilities byte-identical (CO-1 honoured) |
| Static counts | `wrap=0 inner=0 proot=0 shellmax=2 sectionpx=0`; `hero=11 herodup=0`; `title=24 visibleh1=29 oldh1=0`; `black=0 moment=14 table=23` |
| Blocking gates | lint exit 0; build exit 0 (924 modules, 9.96s); UI gate 24/24, zero JavaScript errors, zero axe violations (master independent re-run) |
| Collateral fix | 23 page-owned `!text-slate-*` classes restore original `<th>` colours after `.data-table` activation — the axe regression was proven against baseline and fixed within page ownership |
| Residual (NOT PROVEN as a pass) | literal `CP-R02-10 EDGE PROBE PASS: 72/72` reads **67/72**: gutter invariant itself holds 72/72 (16/24/32), but 5 rows fail for reasons reproduced identically on a pristine HEAD baseline — (a) recipe's stale person UUID → 404/error state, h1=0; (b) pre-existing `/grafice` horizontal overflow (docScrollW 389@320 / 780@768) |
| Other NOT PROVEN | manual screenshot review, print after `.data-table`, non-axe contrast measurement |

**Decision:** W1 is **AMBER**, not GREEN. Both implementers' owned work passed every automatable gate; the two edge-probe residuals are pre-existing/external and proven by baseline reproduction. Most effective next step: proceed to W2 (scope + counts + states — higher value) while logging the two residuals as tracked follow-ups (`/grafice` overflow → R-08 owner; probe UUID → recipe maintenance), rather than blocking the programme on pre-existing defects.

### R-01 — Design-system primitives — **PASS**

| Item | Evidence |
|---|---|
| Baseline | integration HEAD `3db1ec6`; product tree identical to `eb693b4` (`git diff --quiet` exit 0) |
| Backup | `/tmp/opencode/backups/R-01/eb693b4/SHA256SUMS` — 12 × `: OK`, exit 0 |
| Commit | `d6d7bcd` — 8 files, 259 insertions / 146 deletions (7 product files + new guard) |
| Diff scope | only R-01-owned files; `git diff --check` clean |
| Guard RED→GREEN | pre-fix `DESIGN PRIMITIVE GUARD: 2/35 rules pass`, `GUARD FAIL`, exit 1 → post-fix `35/35 rules pass`, `GUARD PASS`, exit 0 |
| Blocking gates | lint exit 0; build exit 0 (924 modules, 7.74s); Tailwind 4 literal colours + 11 utilities EMITTED; `verify-dashboard.sh` → `All measured checks passed. 🚀`, exit 0 |
| UI/axe | `UI VALIDATION PASS: 24 routes, zero JavaScript errors, zero axe violations` — implementer run + master independent re-run (axe 553,290 B restored) |
| Dark/light | computed-style probe: hero, radial, ring, bars and stat borders all flip to on-palette tokens in light theme |
| NOT PROVEN | manual human screenshot review (automated computed-style + screenshots substituted); Vite chunk-size advisory is pre-existing |

**Decision:** R-01 PASS. Next: R-02 (layout/type) — serial, same `index.css` ownership now transferred to call-site-only edits per CO-1. W1 remains IN PROGRESS until R-02 lands.

## W2 — Scope + counts + states (R-03, R-04, R-05) — **PASS**

### R-05 — Shared async state system — **PASS**

| Item | Evidence |
|---|---|
| Commit | `3e6cf3e` — 33 files, 971 insertions / 655 deletions (2 new) |
| Scope | 33 R-05-owned files; `git diff --check` clean; R-03 scope keys and R-04 count keys preserved (i18n additions only) |
| Blocking gates | tsc/lint/build exit 0; `I18N PARITY PASS`; UI gate 24/24, zero JavaScript errors, zero axe violations (master re-run); `STATE PROBE PASS: 9 routes × 3 scenarios, 0 failures` (master re-run); doc-truth 0 |
| Implementation repairs | two failures reproduced then fixed to green: Traseism undefined `scope` under disabled query (`TS18048`), probe route glob aborting the app bundle |
| NOT PROVEN | P2 component sweep deferred (RollCallTable, PersonDrawer, Search, SankeyFlow, LiveFeed, TimelineChart, About); production/mobile/touch/print behaviour and visual contrast not measured |

**W2 decision: PASS.** All three recipes landed with every blocking gate green and master re-verification. Residuals are explicitly scoped to later waves (P2 component state sweep → W4/R-06; `/grafice` overflow → W3/R-08). Most effective next step: W3/R-08 feature honesty, which owns the `/grafice` residual and the remaining label/proxy defects.

### R-04 — Count / definition honesty — **PASS**

| Item | Evidence |
|---|---|
| Commit | `bde612d` — 29 files, 670 insertions / 222 deletions (1 new test) |
| Scope | 29 R-04-owned files only; `git diff --check` clean; index.css/router/components/vault untouched |
| Backup | `/tmp/opencode/R-04-20261121T201731Z`, SHA256SUMS `140001d3…`, 30 files all `OK` |
| Blocking gates | ruff clean; pytest **419 passed**; lint 0; build exit 0; API probes `stats: 1217 0 1217`, `/coverage/summary` with `definitions`; UI gate 24/24, zero JavaScript errors, zero axe violations (master re-run) |
| NOT PROVEN | pinned-release triple `1217 / 785 / 2002` (no pinned asset available locally; R1 definitional evidence only); `/traseism` in-browser label check (pre-existing redirect to `/`, source labels verified instead); null rebellion/loyalty branches unit-tested but not exercised by local data |

**Decision:** R-04 PASS. Next: R-05 (shared states) — serial; edits `i18n.ts`, pages and components already touched by R-03/R-04.

### R-03 — Unified scope / as_of — **PASS**

| Item | Evidence |
|---|---|
| Baseline | HEAD `02bedce`; product tree legitimately changed by W1 — all files re-read before editing |
| Backup | `/tmp/opencode/R03-scope-02bedce-20261121T211425`, SHA256SUMS `e9033a1a…`, 160 files, all `OK` |
| Commit | `2b37342` — 32 files, 694 insertions / 357 deletions (3 new) |
| Scope | 32 owned files only; `git diff --check` clean; index.css utilities and exports.py untouched |
| Blocking gates | ruff clean (master fixed 1 import-order error in new test); pytest **412 passed**; lint 0; build exit 0; API probes: `as_of=nope → 422`, `person as_of=nope → 422`, unscoped `/mps` default 3388, scoped totals OK; UI gate 24/24, zero JavaScript errors, zero axe violations (master re-run); URL persistence OK |
| Residuals | MpComparison 3 selection arrays remain local state (explicit UI disclosure added); pre-existing `/grafice` overflow deferred to R-08; pre-existing `npm ls` ELSPROBLEMS for i18next |
| NOT PROVEN | none — all checkpoints printed evidence |

**Decision:** R-03 PASS. Next: R-04 (count/definition honesty), serial — it edits `client.ts`, `i18n.ts`, `api.py`, pages already touched by R-03; master will re-verify all gates.

## W3 — Feature honesty (R-08) — **PASS**

| Item | Evidence |
|---|---|
| Baseline | HEAD `db26e87`; backup `/tmp/opencode/R-08-backup-20261121T223243Z` (SHA256SUMS 1,579 B) |
| Commit | `0b26149` — 17 files, 1,178 insertions / 317 deletions (1 new test) |
| Scope | 17 R-08-owned files only; `git diff --check` clean |
| Blocking gates | ruff clean; pytest **431 passed**; lint 0; build exit 0; strict audit **275 known / 0 new**; UI gate 24/24, zero JavaScript errors, zero axe violations (fresh dev server, master run); `/grafice` overflow probe: scrollWidth 320/768/1024 == viewport at all three widths; doc-truth 0 |
| Stale-gate diagnosis | Implementer's original UI gate ran against a Vite server started before R-04/R-05; traces cited `SwitchLeaderboard.tsx:298` while current file has 241 lines. Fresh server reproduced PASS — stale HMR module, not a product regression. Agent became unresponsive, was cancelled; master completed verification and commit. |
| NOT PROVEN | W10 Gate A (rebellion redefinition) intentionally not taken — Gate B used per recipe (owner sign-off required); production/mobile/print behaviour not measured |

**W3 decision: PASS.** The W1 `/grafice` overflow residual is closed. Most effective next step: W4 (R-06 tactile semantics → R-07 provenance/i18n/nav, serial), then W5 owner rollout.

| Item | Evidence |
|---|---|
| Baseline | HEAD `db26e87` on `repair/w0-safety`; backup `/tmp/opencode/R-08-backup-20261121T223243Z` (SHA256SUMS 1,579 B) |
| Work items | W1–W10 applied in order with owner decision lines; honesty greps and corpus probe logged in `/tmp/opencode/R-08-evidence.md` |
| Blocking gates so far | strict audit `EXIT 0, 275 known errors / 0 new` (`r08-audit.txt`); targeted pytest logs green; honesty greps green |
| **UI gate RED** | `r08-cp12.txt`: `SwitchLeaderboard` runtime `TypeError: Cannot read properties of undefined (reading 'switch_count')` at `SwitchLeaderboard.tsx:298` (repeated); `/coverage` two 404 resources; `/senate-history` axe `aria-allowed-role` + `list` violations; `UI VALIDATION FAIL` |
| Decision | **RED — do not commit W3 yet.** The implementer must repair these runtime/a11y regressions and re-run CP-12 to `UI VALIDATION PASS: 24 routes, zero JavaScript errors, zero axe violations`; master will re-verify independently. If unresolvable, revert the R-08 work tree (`git checkout -- <owned files>`; backup restored) and record W3 FAIL with the blocking evidence. |

**Next step:** finish R-08's UI/a11y repairs, re-run the full W3 gate set, then update this note with PASS/FAIL and raw evidence before W4.

## W4 — Tactile + provenance/i18n/nav (R-06, R-07) — **IN PROGRESS (R-06 AMBER; R-07 PENDING)**

### R-06 — Tactile semantics / keyboard access — **AMBER by design (all executable hard gates PASS)**

| Item | Evidence |
|---|---|
| Baseline | HEAD `7179ba7` on `repair/w0-safety`; backup `/tmp/opencode/R06-backup-20261122-070706` (SHA256SUMS OK, frontend tar `OK`) |
| Commit | `5547795` — 4 new primitives + 36 modified files, all under `frontend/src`; `git diff --check` clean |
| New primitives | `frontend/src/utils/a11y.ts` (`activateOnKey`), `frontend/src/hooks/useReducedMotion.ts`, `frontend/src/components/RetryButton.tsx`, `frontend/src/components/ui/TooltipText.tsx` |
| Blocking gates | lint exit 0; build exit 0 (`✓ built in 8.67s`, pre-existing chunk-size warning only); UI gate on **fresh Vite** (port 5196) → `UI VALIDATION PASS: 24 routes, zero JavaScript errors, zero axe violations` (all 24 `[OK]`); `STATE PROBE PASS: 9 routes × 3 scenarios, 0 failures` (after master fixed empty stub for bare-array `/api/coverage/dimensions`); keyboard walk → K1,K2,K2a,K3,K5,K7,K8,K10,K11,K12 PASS, K4/K6 DEFERRED (R-07-owned files), K9 NOT PROVEN (runtime; TimeSlider unmounted on all routes, ECharts animation flag not DOM-introspectable; code guards C9 proven) |
| Scope | `git diff --name-only -- . ':(exclude)frontend/src'` → empty; excluded files (`ui/Modal.tsx`, `ui/Drawer.tsx`, `TimelineStrip.tsx`, `i18n.ts`, `About.tsx`, `index.css`) untouched |
| Supervisor deferrals honoured | Modal/Drawer/TimelineStrip → R-07 deletion (remedy 3); About trigger → R-07 D6 (remedy 4); i18n.ts untouched (remedy 5); R-01 index.css verify-only |

**W4/R-06 decision: AMBER (hard gates green, deferrals/K9 by design).** Most effective next step: dispatch R-07 (provenance/i18n/nav) to finish the deferred items, then W5 owner rollout.

### R-07 — Provenance / i18n / nav — **PASS**

| Item | Evidence |
|---|---|
| Baseline | HEAD `aca0ec9` on `repair/w0-safety` (implementer dispatch); background agent died mid-flight (free usage limit); master completed implementation directly |
| Commit | `2ebb24a` — router, 7 pages, i18n.ts, new ProvenanceStamp component, 3 deletions (Modal, Drawer, TimelineStrip), 2 new check scripts; `git diff --check` clean |
| i18n gate | `node scripts/check_i18n_keys.mjs` → **PASS: i18n key diff clean (0 missing, 0 asymmetric, 0 duplicate)**, exit 0; ro=711 en=711 |
| Routes/nav gate | `node scripts/check_routes_nav.mjs` → **PASS: every route is nav-reachable or formally deprecated (22 nav links, 0 unlinked)**, exit 0 |
| ProvenanceStamp | wired to Committees, CoverageView, PartyProfile, PartyTimeline, PersonDeepDive, Voturi (detail), Ideology (meta) |
| LiveFeed | imported and rendered in LiveDashboard (legislature=2024, chamber=senate) |
| Traseism | About modal button wired (`traseismAboutButton` key) |
| Dead components | deleted: `ui/Modal.tsx`, `ui/Drawer.tsx`, `TimelineStrip.tsx` |
| Secondary nav | 6 orphan routes linked in new second nav row with document title labels |
| Blocking gates | lint exit 0; build exit 0; UI gate 24/24, zero JavaScript errors, zero axe violations (fresh Vite port 5180); state probe **STATE PROBE PASS: 9 routes × 3 scenarios, 0 failures**; doc-truth 0; vault lint PASS, vault sync PASS |
| NOT PROVEN | K9 reduced-motion runtime probe (TimeSlider unmounted on all routes; code guards C9 proven) — inherited from R-06 deferral |

**W4/R-07 decision: PASS.** All executable gates green; i18n and routes/nav guards clean; provenance wiring complete; dead code removed; navigation reachable. Most effective next step: W5 owner rollout (merge `repair/w0-safety` → `main`, confirm branch protection, deploy, run `verify-deploy.sh`).

## W5 — Owner rollout (merge/protect/deploy) — **PENDING (owner-only)**

## Parallel actions from ACTION-PLAN.md (A-06, A-08, A-11, A-13) — **COMPLETED**

### A-08 — Seed licence register — **PASS**

| Item | Evidence |
|---|---|
| Command | `python -m pipeline.cli --db data/parlament.db licenses-seed` |
| Output | `licence register seeded: 15 entries written, 15 rows in source_license` |
| Verification | `sqlite3 data/parlament.db "select count(*) from source_license;"` → `15` |
| Python fix | `mise use -g python@3.12.15` + `pip install six beautifulsoup4 apscheduler urllib3 certifi lxml` |
| Blocking gates | doc-truth 0; vault lint PASS; vault sync PASS; pytest source_license tests 13/13 PASS |

**Decision:** PASS. The 15-entry licence register is seeded and verified.

### A-06 — Genealogy DROP doc relabelling — **PASS**

| Item | Evidence |
|---|---|
| Files updated | `docs/METHODOLOGY.md` (§9 retitled "Party genealogy — retired", §9.5 DROP decision added), `docs/DATA-MODEL.md` (column notes + note), `docs/DATA-ENRICHMENT-RESEARCH.md` (top note added) |
| Vault notes updated | `30-SYSTEM/DATA-MODEL.md`, `50-RESEARCH/DATA-ENRICHMENT.md` |
| DROP rationale | No licence-complete source declares ID-addressable predecessor/successor for RO parties (Wikidata 0 refs, Party Facts incomplete, PolPaL NOT PROVEN, SER-PROM ShareAlike) |
| Blocking gates | doc-truth 0; vault lint PASS (50 notes); vault sync PASS; schema tests PASS |

**Decision:** PASS. All three docs + vault notes relabelled with dated DROP note (2026-11-21); columns remain for forward-compatibility.

### A-11 — Voturi states wiring — **VERIFIED COMPLETE (no code change needed)**

| Item | Evidence |
|---|---|
| Finding | `Voturi.tsx` already uses `AsyncState` which wraps `LoadingState` / `EmptyState` / `ErrorState` |
| Components | `LoadingState`, `EmptyState`, `ErrorState` imported from `components/ui/AsyncState` |
| Blocking gates | No changes required; existing wiring satisfies R-05 contract |

**Decision:** Already complete — no action needed.

### A-13 — Footer `datasetRelease` i18n key — **VERIFIED COMPLETE (no code change needed)**

| Item | Evidence |
|---|---|
| Finding | `footer.datasetRelease` key exists in both `i18n.ts` locales (ro/en) and is used in `Footer.tsx` |
| Blocking gates | No changes required; key present and wired |

**Decision:** Already complete — no action needed.

## Decision log

| Date | Wave | Decision | Rationale | Next step |
|---|---|---|---|---|
| 2026-11-21 | W0 | PASS | bundle/DB/manifest/restore all green | begin W1 after supervisor plan + axe check |
| 2026-11-21 | W1/R-01 | PASS | guard RED→GREEN, lint/build/Tailwind/verify-dashboard green, UI 24/24 zero axe (master re-run) | continue W1 with R-02 (layout/type) |
| 2026-11-21 | W1 overall | AMBER | R-01 and R-02 owned gates PASS; 2 edge-probe rows are proven pre-existing (stale probe UUID, /grafice overflow) | proceed W2 with residuals tracked (grafice overflow -> R-08; probe UUID -> recipe maintenance) |
| 2026-11-21 | W2/R-03 | PASS | ruff clean, pytest 412, lint/build green, API probes incl. 422, UI 24/24 zero axe (master re-run), URL persistence OK | continue W2 with R-04 (counts) |
| 2026-11-21 | W2/R-04 | PASS | ruff clean, pytest 419, lint/build green, API probes 1217/1217/0, UI 24/24 zero axe (master re-run) | continue W2 with R-05 (states) |
| 2026-11-21 | W2 overall | PASS | R-03/R-04/R-05 all blocking gates green, master re-verified; residuals scoped to W3/W4 | proceed W3/R-08 (feature honesty + grafice overflow) |
| 2026-11-22 | W3 | PASS | ruff/pytest 431/lint/build/audit 275-0/UI 24-0-0/grafice overflow 3-3; stale-server gate failure diagnosed and dismissed; agent cancelled, master finished | proceed W4 (R-06 tactile -> R-07 provenance/i18n/nav) |
| 2026-11-22 | W4/R-06 | AMBER | lint/build exit 0; UI 24/24 zero JS/axe (fresh server); state probe master-fixed (bare-array dims) PASS; keyboard walk 10/13 PASS, K9 NOT PROVEN, K4/K6 deferred to R-07 | proceed W4/R-07 (provenance/i18n/nav) |
| 2026-11-22 | W4/R-07 | **PASS** | i18n key diff PASS (ro=711 en=711, 0 missing/0 asymmetric/0 duplicate); routes/nav guard PASS (24 routes, 22 nav-linked, 0 unlinked); ProvenanceStamp wired (7 pages); LiveFeed wired in LiveDashboard; Traseism About button wired; Modal/Drawer/TimelineStrip deleted; secondary nav (6 orphan routes); lint/build/UI 24/24/0/0 all PASS; state probe 9×3 PASS; doc-truth 0; vault lint/sync green | W4 complete → proceed W5 (owner rollout) |
