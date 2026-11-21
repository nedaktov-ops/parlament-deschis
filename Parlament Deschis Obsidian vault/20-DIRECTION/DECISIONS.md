---
id: DECISIONS
type: decision
title: "Parlament Deschis — decision index (2026-11-21)"
description: "Immutable index of accepted ADRs and the R1-R11 adjudications, cross-referenced to stable D-IDs. Reversals are appended, never edited."
status: active
authority: canonical
tags:
  - type/decision
  - lifecycle/active
  - domain/project
source_paths:
  - docs/adr/0001-result-cache.md
  - docs/adr/0002-manual-data-release.md
  - docs/AUDIT-RESOLUTIONS-2026-11-21.md
  - docs/POST-INITIAL-AUDIT-2026-11-21.md
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
---

# Decisions

This index records *what was decided and why*, not what is currently true in
production. Live state belongs in [CURRENT-STATE](../10-STATE/CURRENT-STATE.md);
the contradiction evidence belongs in
[CONTRADICTIONS](../10-STATE/CONTRADICTIONS.md); the resulting work belongs in
[TASK-REGISTER](TASK-REGISTER.md).

## Immutability rule

Decisions are append-only. If a decision is reversed, a **new entry with a new
D-ID** is added, with the old entry marked `superseded` and a pointer to its
replacement. Never edit an accepted entry to change its meaning, and never
delete a superseded one — the history is the audit trail. Aliases (ADR/R-IDs)
are preserved verbatim so older documents still resolve.

Resolution policy used for all adjudications, in order: executable evidence
over prose; scope before conflict; newer wins on the same topic except for
explicitly labelled historical snapshots; dated in-document addendum over
base body; generated artifacts derive from source; no guessing — report NOT
PROVEN and name the resolver.

---

## D-0001 — In-process result cache, 300 s TTL
- **Aliases:** ADR-0001
- **Status:** accepted, implemented; current at `backend/cache.py`
- **Decision:** parameterised in-process TTL cache (`TTL_SECONDS = 300`,
  `MAX_ENTRIES = 512`, oldest third evicted) for read-only endpoint results.
  Exceptions are never cached. A lock-guarded generation counter plus
  `invalidate()` prevents a slow in-flight compute from writing a stale result
  back after an admin write; **every admin write path must call
  `invalidate()`** — that is a correctness obligation, not an optimisation.
- **Boundaries:** mutable analytics stay `no-store`; cache state is per
  process; a release restart empties the cache. Freshness is therefore
  "on release" plus a 5-minute bound between admin writes, **not real-time**.
  Rejected alternatives: no cache (measured p95 far above target), edge
  caching only, shared Redis, longer TTL, per-request cache-busting.
- **Note:** the 1-hour TTL in `SPEC.md` is historical and superseded by this
  300-second decision.

## D-0002 — Manual, immutable data releases with a pinned marker
- **Aliases:** ADR-0002
- **Status:** accepted, implemented; tag pointer current, counts stale
- **Decision:** publish datasets as immutable GitHub release assets (database,
  page manifest with SHA-256, audit report), then pin the exact tag in
  `data/latest-release.txt` with a dedicated commit. The Docker build
  downloads and verifies that asset; the runtime is read-only. A pin commit
  pushed with `GITHUB_TOKEN` does not itself start CI or Render deployment —
  the data workflow triggers Render explicitly and deploy verification checks
  `/api/health` for the expected release tag. Rollback is `git revert` of the
  pin commit; no data is rewritten in place. Scheduled rebuilds are
  best-effort; `workflow_dispatch` is the manual recovery path.
- **Stale detail:** the ADR's 7,358 membership figure describes the raw release
  asset at writing time; the prepared runtime value is 7,349 (see D-0004).
- **Current pin:** `data-20261117-T213500` — 3,388 persons, 7,349 prepared
  memberships, 142 switch waves.

---

## D-0003 — Two switch totals are definitional, not a defect
- **Aliases:** R1
- **Verdict:** not a data bug. The `/api/dashboard/stats` total of 2,002 is
  `switch_group` (1,217) **plus** `switch_party` (785); export and traseism
  surfaces count `switch_group` only (1,217). Both come from the pinned
  release. A fresh audit that queried only local working databases found no
  party-switch rows and therefore could not derive 2,002 — the 785 events
  exist in the published corpus, not in those local copies.
- **Residual obligation:** the UI and API documentation must label the two
  definitions. Tracked as T-2026-003 and T-2026-014.

## D-0004 — Membership totals differ by artifact
- **Aliases:** R2
- **Verdict:** both numbers are correct for different artifacts. 7,358 is the
  raw GitHub release asset; 7,349 is the prepared database after nine
  duplicate closed stints were removed, served at runtime. **Current-state
  truth is 7,349.** SQLite journal mode follows the same pattern: the shipped
  asset is DELETE, local and runtime copies are WAL.

## D-0005 — WAL versus DELETE is a lifecycle difference
- **Aliases:** R3
- **Verdict:** no contradiction. The release asset uses DELETE journal mode
  for read-only filesystem compatibility; local and runtime copies open in
  WAL. Trust release evidence when describing the shipped artifact.

## D-0006 — Vote tables: published corpus versus working databases
- **Aliases:** R4
- **Verdict:** scope difference. The pinned release has no vote tables; local
  gitignored working databases do hold votes and positions but have never
  been released. Always qualify the statement as "no vote data **in the
  published corpus**". This is the central unshipped item of the 10x thesis.

## D-0007 — OpenAPI path count: 41 stale, 48 current
- **Aliases:** R5
- **Verdict:** the generated file at 41 paths was stale; regeneration from the
  current application yields 48 paths including canonical vote and ideology
  routes. The live backend also reports 48 paths but with legacy aliases and
  without universal `meta`. Generated files derive from source and are never
  hand-edited.

## D-0008 — "All 15 features completed" withdrawn
- **Aliases:** R6
- **Verdict:** historical claim, withdrawn. The feature table contains 17 rows
  including two duplicates; the audited tally is **11 PRESENT, 6 PARTIAL,
  0 wholly absent**. Genealogy has zero links, alerts are disabled in the
  deployment configuration, and no blog or donation UI exists. The corrected
  claim is in [VISION](VISION.md).

## D-0009 — Error-tracking hook claim withdrawn
- **Aliases:** R7
- **Verdict:** withdrawn. No hook file, no symbol and no tracked file exists.
  The dated correction in `EVIDENCE.md` wins over the older base body and over
  `WAVE-4-COMPLETION.md`, which still calls the hook "available for
  integration".

## D-0010 — UI gate status is scope-dependent
- **Aliases:** R8
- **Verdict:** all historical readings were true in their scope; **24 of 24
  routes with zero JavaScript errors and zero axe violations** is current for
  the repository. A fresh probe scored 23 of 24 against the live proxy because
  `/api/analytics/ideology` returns 404 there. Production parity remains NOT
  PROVEN; the `DASHBOARD-VERIFICATION.md` addendum is correct for its own
  audit only.

## D-0011 — "CI green" meant local-only fixes
- **Aliases:** R9
- **Verdict:** review fixes are local and unpushed. At review time
  `origin/main` was `6b848f1` while the fixed branch was ahead; all recent main
  CI runs failed on rules-of-hooks errors. Both the "green in review" and
  "RED on GitHub" statements are correct in their own scope. As of this index
  HEAD is `6fd6028`, 3 ahead of main and still unpushed.

## D-0012 — Release pin chronology is not a contradiction
- **Aliases:** R10
- **Verdict:** chronological. The tag snapshot captured an earlier tag; the
  marker was updated after publication. Historical documents that mention the
  earlier tag are intentionally excluded by the doc-truth gate.

## D-0013 — `ci.yml` does filter pushes to main
- **Aliases:** R11
- **Verdict:** the claim of a bare `push:` trigger was false and has been
  corrected. The workflow filters `push` to `branches: [main]` and also runs
  on pull requests and `workflow_dispatch`. `docs/DEPLOYMENT.md` was right.

---

## Open, not decided

- The exact commit Vercel built from: strongly inferred `6b848f1`, no deploy
  identifier in response headers.
- Runtime read-only enforcement and client-side rendering of SPA routes: no
  mutation or browser session was performed in the read-only audits.
- Whether licence seeding ever ran in production: the seeding function is
  defined but not wired to a called path (T-2026-007).
- The 60-second alert poll against immutable data: either remove it or relabel
  alerts as "on release"; owner decision outstanding (T-2026-010).
- Blog, SEO and donations: strategy only; an owner must decide to drop or
  scope it before it becomes committed work.
