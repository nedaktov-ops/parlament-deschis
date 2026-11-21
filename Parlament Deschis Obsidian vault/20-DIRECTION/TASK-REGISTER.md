---
id: TASK-REGISTER
type: task
title: "Parlament Deschis — ordered next work (2026-11-21)"
description: "Stable-ID register of the next repairs, with priority, status, acceptance criteria, evidence links and legacy aliases. Nothing is marked done without local verification."
status: active
authority: canonical
tags:
  - type/task
  - lifecycle/active
  - domain/ops
source_paths:
  - docs/POST-INITIAL-AUDIT-2026-11-21.md
  - docs/GAP-ANALYSIS-2026-11-21.md
  - docs/COMPREHENSIVE-REVIEW-2026-11-21.md
  - docs/remediation/STATE.md
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
---

# Task register

Ordered work derived from `docs/POST-INITIAL-AUDIT-2026-11-21.md` §6
(the ten repairs, T-2026-001…010) and `docs/GAP-ANALYSIS-2026-11-21.md` §6
(the six sequencing steps, T-2026-011…016), plus the open items named in
the same reviews (T-2026-017…018). IDs are stable: never renumber, and never
edit a completed entry — append a correction or a new task.

**Baseline:** HEAD `6fd6028`, `origin/main` `6b848f1`, 3 ahead and unpushed.
Local gates are green; CI is RED on main; `main` has no branch protection;
issue #14 is open. **Reach** is `local-only` when the work exists only in the
working tree or in documentation, and `production` when it changes what users
receive. No task below is claimed `done` on the strength of a document alone.

## A. Documentation-truth repairs (audit §6, in priority order)

### T-2026-001 — Commit the audit reports and re-run the doc-truth gate
- **Priority:** P0 · **Status:** open · **Reach:** local-only
- **Legacy aliases:** F8, F9
- **Acceptance:** the post-initial audit, gap analysis and resolution report
  are committed; `check-doc-truth.sh` exits 0 after the commit; the historical
  untracked QA reports are labelled historical or their evidence migrated.
- **Evidence:** [CURRENT-STATE](../10-STATE/CURRENT-STATE.md), [GAP-REGISTER](../10-STATE/GAP-REGISTER.md)

### T-2026-002 — Fix stale CLI claims, invented routes and missing API entry
- **Priority:** P1 · **Status:** open · **Reach:** local-only
- **Acceptance:** `coverage`, `enrich` and `serve` are documented as wired;
  invented routes in `SPEC.md` and `METHODOLOGY.md` are removed or corrected;
  `GET /api/metrics` is added to `docs/API.md`.
- **Evidence:** [GAP-REGISTER](../10-STATE/GAP-REGISTER.md)

### T-2026-003 — Label both switch definitions and both membership counts
- **Priority:** P0 · **Status:** open · **Reach:** local-only and production wording
- **Legacy aliases:** R1, R2 (see [DECISIONS](DECISIONS.md))
- **Acceptance:** 1,217 group-only switches, 785 party switches and their
  2,002 sum are each labelled; 7,358 raw release asset versus 7,349 prepared
  runtime memberships are labelled in `docs/API.md` and `README.md`.
- **Evidence:** [CONTRADICTIONS](../10-STATE/CONTRADICTIONS.md), [GAP-REGISTER](../10-STATE/GAP-REGISTER.md)

### T-2026-004 — Re-license-align strategy and enrichment research
- **Priority:** P1 · **Status:** open · **Reach:** local-only
- **Acceptance:** `MASTER-STRATEGY.md` and `DATA-ENRICHMENT-RESEARCH.md`
  agree with `LICENSE-APPENDIX.md`: the external Romanian civic source
  (ro_281) is cross-check-only, PopuList is unverified, and the four Party
  Facts identifiers are stated consistently.
- **Evidence:** [GAP-REGISTER](../10-STATE/GAP-REGISTER.md)

### T-2026-005 — Icon family lock, AGENTS.md corrections, missing button type
- **Priority:** P1 · **Status:** open · **Reach:** local-only
- **Acceptance:** the design lock matches the de-facto inline-SVG family (or
  Lucide is added deliberately with a dependency and imports); `AGENTS.md`
  no longer claims `overscroll-behavior: contain`, a `popover` attribute or a
  required polyfill that do not exist, and its two conflicting popover
  statements are reconciled; the remaining `type="button"` omission in
  `PartyComparisonMatrix.tsx` is fixed.
- **Evidence:** [GAP-REGISTER](../10-STATE/GAP-REGISTER.md)

### T-2026-006 — Date-stamp snapshots and retire stale QA/false-comment rows
- **Priority:** P2 · **Status:** open · **Reach:** local-only
- **Acceptance:** every recon snapshot carries its commit hash; untracked QA
  reports are historical or removed after evidence migration; the two
  already-corrected "false source comment" rows are removed from
  `REMEDIATION-STRATEGY.md` §9.
- **Evidence:** [CURRENT-STATE](../10-STATE/CURRENT-STATE.md)

### T-2026-007 — Wire licence seeding into an explicit tested path
- **Priority:** P1 · **Status:** open · **Reach:** local-only and production
- **Acceptance:** `ensure_source_licenses()` is called from a named CLI or
  startup path with a regression test; the seeded release reports the
  expected non-empty `source_license` table. Seeding is currently latent:
  the shipped release has no such table and the working databases have it
  empty. Whether seeding ever ran in production remains NOT PROVEN.
- **Evidence:** [GAP-REGISTER](../10-STATE/GAP-REGISTER.md)

### T-2026-008 — Resolve the four-way Vite version conflict
- **Priority:** P1 · **Status:** open · **Reach:** local-only
- **Legacy aliases:** R-D0.3, W2 dependency-upgrade stream
- **Acceptance:** one Vite version is stated across title, procedure,
  `STATE.md` and shipped `package.json`; Wave-4 ticks that lack proof are
  marked NOT PROVEN; `fb95e56` is cited as the real dependency-bump commit,
  not the evidence-only commits. Node is now v24, so an upgrade previously
  blocked on Node 18 is no longer blocked by the environment.
- **Evidence:** [WAVE-STATUS](WAVE-STATUS.md), [GAP-REGISTER](../10-STATE/GAP-REGISTER.md)

### T-2026-009 — Replace destructive rollback recipe and align gates/palette
- **Priority:** P1 · **Status:** open · **Reach:** local-only
- **Acceptance:** `DASHBOARD-STRATEGY.md` rollback uses `git revert` or
  `git checkout <tag> -- <path>` with no hard reset, force push or branch
  deletion; the non-existent `npm test` gate is dropped; WCAG AAA is aligned
  to the governing AA level and the forbidden violet variant is removed.
- **Evidence:** [DECISIONS](DECISIONS.md)

### T-2026-010 — Correct the feature tally and decide the 60-second poll
- **Priority:** P0 · **Status:** open · **Reach:** local-only and production wording
- **Legacy aliases:** F11, R6
- **Acceptance:** the 15-feature claim reads 11 PRESENT / 6 PARTIAL / 0 absent;
  a recorded decision either removes the `refetchInterval: 60_000` alert
  polling against immutable data or relabels the alerts as "on release".
  The rule forbidding a 60 s poll is currently violated in the shipped
  configuration even though the writing poller is disabled.
- **Evidence:** [VISION](VISION.md), [DECISIONS](DECISIONS.md)

## B. Shipping sequence (gap analysis §6, in dependency order)

### T-2026-011 — Publish the review branch and protect main
- **Priority:** P0 · **Status:** open · **Reach:** production
- **Legacy aliases:** F1 (CI fix), W2 integration stream
- **Acceptance:** the branch at `6fd6028` is pushed and a PR opened; CI is
  green on main; required checks are enabled in branch protection. The
  hooks-after-return fix is locally verified but absent from `origin/main`.
- **Evidence:** [CURRENT-STATE](../10-STATE/CURRENT-STATE.md)

### T-2026-012 — Deploy backend first, then frontend, and prove parity
- **Priority:** P0 · **Status:** open · **Reach:** production
- **Acceptance:** live `/api/analytics/ideology` returns 200, canonical routes
  carry `meta`, the deployed bundles use single-prefix `/api` paths, and both
  bundle hashes are recorded. Today the live bundle double-prefixes paths and
  the ideology endpoint returns 404; 24 of 24 routes pass with a local
  backend but only 23 of 24 against the live proxy.
- **Evidence:** [GAP-REGISTER](../10-STATE/GAP-REGISTER.md), [CURRENT-STATE](../10-STATE/CURRENT-STATE.md)

### T-2026-013 — Repair source acquisition and publish votes in a release
- **Priority:** P0 · **Status:** open · **Reach:** production
- **Acceptance:** the `cdep.ro` fetch path gains retry, cache or an alternate
  acquisition route; issue #14 is closed; a fresh immutable release contains
  the ingested votes so `GET /api/votes` is non-empty in production. The
  root cause is a ConnectTimeout from CI runners, not a workflow defect.
- **Evidence:** [GAP-REGISTER](../10-STATE/GAP-REGISTER.md)

### T-2026-014 — Publish the switch-total reconciliation alongside T-2026-003
- **Priority:** P0 · **Status:** open · **Reach:** production wording
- **Acceptance:** `/api/dashboard/stats` (2,002) and the export/traseism
  surfaces (1,217) are explicitly labelled as group-plus-party versus
  group-only in the API documentation and the user interface. The numbers
  are definitional, not a data defect; see decision D-0003.
- **Evidence:** [DECISIONS](DECISIONS.md), [CONTRADICTIONS](../10-STATE/CONTRADICTIONS.md)

### T-2026-015 — Close P1 vision gaps in dependency order
- **Priority:** P1 · **Status:** open · **Reach:** production
- **Acceptance:** in order — genealogy links, Senate historical profiles,
  multi-dimensional coverage (mandates plus votes and biographies), then H3–H5
  frontend states; each closes with a documented gate and a release decision.
  Decide explicitly to drop or scope blog/SEO/donations.
- **Evidence:** [VISION](VISION.md), [GAP-REGISTER](../10-STATE/GAP-REGISTER.md)

### T-2026-016 — Refresh stale documentation from the new live state
- **Priority:** P2 · **Status:** open · **Reach:** local-only
- **Acceptance:** licence, robots and version claims are mirrored from the
  corrected sources; the supersession chain in
  [VISION](VISION.md) still resolves after the refresh.
- **Evidence:** [CURRENT-STATE](../10-STATE/CURRENT-STATE.md)

## C. Named open residuals

### T-2026-017 — H3-D: applied states in interactive components
- **Priority:** P1 · **Status:** open · **Reach:** local-only
- **Acceptance:** the "states applied" H3-D work listed as pending in
  `FRONTEND-UX-10X-STRATEGY.md` is implemented and visible in UI validation;
  neighbouring H3-A/B/C and H5 dead-code removals are recorded as already
  completed, not silently reopened.
- **Evidence:** [GAP-REGISTER](../10-STATE/GAP-REGISTER.md)

### T-2026-018 — H4-A: footer polish
- **Priority:** P2 · **Status:** open · **Reach:** local-only
- **Acceptance:** the H4-A footer item is implemented, checked at 320 px and
  at the 24-route UI gate with zero JavaScript errors and zero axe violations.
- **Evidence:** [GAP-REGISTER](../10-STATE/GAP-REGISTER.md)

## D. Legacy alias index

Aliases are historical labels only. They are not evidence of completion and
must never be renumbered into a stable ID.

| Alias family | Origin | Mapping to stable IDs |
| --- | --- | --- |
| F1–F11 | Completion-review fix set (`COMPREHENSIVE-REVIEW-2026-11-21.md` §2): CI hooks, canonical routes, vote date filters, `meta`, docstring, vote UI, provenance backfill, doc-truth gate, documentation truth, UI coverage, accessibility | Locally verified at review time but unpushed. Residual follow-ups: F1→T-2026-011, F8/F9→T-2026-001, F11→T-2026-010. Others are historical, not reopened. |
| P0-1…P0-7 | Remediation Wave 1 part ledger (`docs/remediation/STATE.md`) | Superseded by the on-branch fix; their per-part commit SHAs are not ancestors of main. See [WAVE-STATUS](WAVE-STATUS.md). Next-work equivalent T-2026-011. |
| W2-… | Wave 2 blueprint workstreams (`MASTER-INTEGRATION-BLUEPRINT-WAVE2.md`) | Planning aliases only; sequencing equivalents T-2026-011…T-2026-016. No completion claim. |
| R-D0.1 / R-D0.2 / R-D0.3 | Wave 4 dependency-upgrade recipes (`docs/remediation/WAVE-4-RECIPES.md`) | T-2026-008 for the Vite conflict and approval-tick honesty. Evidence-only commits are not upgrade proof. |

## E. Gate vocabulary

- `open` — no verified completion.
- `in-progress` — work started; evidence not yet green.
- `done` — reserved for a re-verified state with a printed gate result; no
  task in this register currently qualifies.

Local green gates (pytest, ruff, lint, build, strict audit 275 known / 0 new,
doc-truth, UI 24/24) apply to the working tree at `6fd6028` only. They are
not evidence that anything is deployed.
