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

## W2 — Scope + counts + states (R-03, R-04, R-05) — **IN PROGRESS (R-03 PASS)**

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

## W3 — Feature honesty (R-08) — **PENDING**

## W4 — Tactile + provenance/i18n/nav (R-06, R-07) — **PENDING**

## W5 — Owner rollout (merge/protect/deploy) — **PENDING (owner-only)**

## Decision log

| Date | Wave | Decision | Rationale | Next step |
|---|---|---|---|---|
| 2026-11-21 | W0 | PASS | bundle/DB/manifest/restore all green | begin W1 after supervisor plan + axe check |
| 2026-11-21 | W1/R-01 | PASS | guard RED→GREEN, lint/build/Tailwind/verify-dashboard green, UI 24/24 zero axe (master re-run) | continue W1 with R-02 (layout/type) |
| 2026-11-21 | W1 overall | AMBER | R-01 and R-02 owned gates PASS; 2 edge-probe rows are proven pre-existing (stale probe UUID, /grafice overflow) | proceed W2 with residuals tracked (grafice overflow -> R-08; probe UUID -> recipe maintenance) |
| 2026-11-21 | W2/R-03 | PASS | ruff clean, pytest 412, lint/build green, API probes incl. 422, UI 24/24 zero axe (master re-run), URL persistence OK | continue W2 with R-04 (counts) |
| 2026-11-21 | W2/R-04 | PASS | ruff clean, pytest 419, lint/build green, API probes 1217/1217/0, UI 24/24 zero axe (master re-run) | continue W2 with R-05 (states) |
