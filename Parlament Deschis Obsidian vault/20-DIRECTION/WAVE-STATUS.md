---
id: WAVE-STATUS
type: state
title: "Remediation wave ledger — dated 2026-11-19 (stale)"
description: "Historical Wave 0-5 ledger from docs/remediation/STATE.md, preserved as a dated record and superseded by the 2026-11-21 reviews."
status: stale
authority: historical
tags:
  - type/state
  - lifecycle/stale
  - domain/ops
source_paths:
  - docs/remediation/STATE.md
  - docs/remediation/WAVE-4-COMPLETION.md
  - docs/POST-INITIAL-AUDIT-2026-11-21.md
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
---

# Wave status — historical ledger

> **Superseded.** This is a dated **2026-11-19** remediation ledger preserved
> as history. It has been superseded by the **2026-11-21** reviews
> (`COMPREHENSIVE-REVIEW-2026-11-21.md`, `GAP-ANALYSIS-2026-11-21.md`,
> `POST-INITIAL-AUDIT-2026-11-21.md`, `AUDIT-RESOLUTIONS-2026-11-21.md`).
> Do not use it as current state — see
> [CURRENT-STATE](../10-STATE/CURRENT-STATE.md). Facts that were re-verified
> on 2026-11-21 are marked below; everything else is a snapshot claim.

Baseline at writing: `eb069d2b1de953a89489245ef6418a66a7b652ba`, tag
`pre-remediation-2026-11-19`, backup checksum verified. Current HEAD for this
note is `6fd6028`, three commits ahead of `origin/main` `6b848f1` and
unpushed.

## 1. Wave table (as recorded 2026-11-19)

| Wave | Theme | Recorded status |
| --- | --- | --- |
| 0 | Backups + strategy + recipes | DONE — tag, branch, 152 MB snapshot, checksum verified |
| 1 | P0 critical fixes | VERIFIED — 7/7 parts `APPROVE_INTEGRATE`; integrated gate green (C-2 residuals fixed in Wave 3) |
| 2 | P1 correctness/security | VERIFIED — 5/5 parts `APPROVE_INTEGRATE`; integrated gate green |
| 3 | Looks + accessibility | VERIFIED — 0 residuals; all five axe C-2 findings fixed via the W3-C2 commit |
| 4 | Modernization | STRATEGY — strategy document created with action plans, checkpoints and risks; **recipes pending stakeholder review** |
| 5 | Fresh forensic re-verification | VERIFIED — forensic check passed, all gates green |

The Wave 4 documentation table repeats that only the strategy, recipes and
supervisor documents were *created*, with the next step recorded as
"stakeholder review of `WAVE-4-STRATEGY.md`, then begin with R-D0.1".
`WAVE-4-SUPERVISOR.md` ticks "STRATEGY.md approved" and "recipes for each
task", while `STATE.md:52` says approval is pending — **approval is NOT
PROVEN**. Tick marks in these files are not gate evidence.

## 2. Wave 4 Phase 3 — blocked, then obsolete

- Phase 1 (dependency upgrades) and Phase 2 (infrastructure) were recorded
  COMPLETE. Phase 3 (environment-restricted upgrades) was recorded
  **BLOCKED**: Vite 7/8, ECharts 6, Tailwind 4 and i18next 27 were gated on
  "Node.js 20+", while the machine ran Node v18.19.1.
- **The blocker is obsolete.** The environment now runs **Node v24**, so the
  stated environment constraint no longer applies. The correct follow-up is
  to re-evaluate those upgrades on their merits, not to keep carrying a
  "blocked" label. See T-2026-008 in [TASK-REGISTER](TASK-REGISTER.md).
- Upgrade evidence in the ledger is misleading: `dd463d1`, `23b5b81` and
  `1d72d06` changed only evidence files. The shipped React/Vite bump is
  `fb95e56`, and `npm ls` reports React 19.3.1 rather than the recorded
  19.0.0. The four-way Vite version conflict (title "Vite 8", procedure
  `^5.0.0`, ledger "Vite 6", shipped `^6.0.0`) is still unresolved.
- The "stable, production-ready state" line in `WAVE-4-COMPLETION.md` is a
  dated snapshot: open residuals, no branch protection on `main`, and a live
  ideology endpoint returning 404 were all true at that time and remain
  unresolved in the published state. The error-tracking hook it calls
  "available for integration" does not exist (decision D-0009).

## 3. Per-part commits are not ancestors of main

The part ledger lists P0-1 `1fcd577`, P0-2 `d7fb3c7`, P0-3 `74f20f7`,
P0-4 `d56456c`, P0-5 `f46c660`, P0-6 `76ed275`, P0-7 `2aa5401`, with
integration at `58ec23f` in worktree `wt-INTEGRATE`. These are real git
objects but **are not ancestors of `main` or of the current branch** — they
describe abandoned worktrees. Their `APPROVE_INTEGRATE` verdicts certify the
worktree cherry-picks, not the deployed product. The on-branch fix is
`b69c820`. Do not cite the per-part SHAs as proof that a fix is shipped.

## 4. What was actually re-verified on 2026-11-21

- Release pin `data-20261117-T213500`; live `GET /api/health` reports
  3,388 persons and 7,349 prepared memberships. The 2026-11-19 snapshot of
  7,358 described the raw asset and was intentionally not rewritten.
- CI run `44879894155` failed only in the `test` job, in the frontend
  lint/type-check/build step, on four rules-of-hooks errors; `audit` and
  `evidence-guards` passed, `docker` skipped. Those hooks fixes are local
  and unpushed, so CI remains RED on main.
- `main` branch protection check returns 404 (absent); issue #14 remains open
  with repeated ConnectTimeout failures against the external Romanian civic
  source (ro_281).
- The doc-truth gate was repaired by narrowing two overbroad token patterns;
  clean tree exits 0, and seeded false claims still fail it.

This ledger therefore answers "what was claimed and when", not "what is
true now". Current truth lives in [CURRENT-STATE](../10-STATE/CURRENT-STATE.md)
and the gaps in [GAP-REGISTER](../10-STATE/GAP-REGISTER.md).
