---
id: ACTION-PLAN
type: runbook
title: "Actionable step register — all remaining work"
description: "Every actionable step to advance Parlament Deschis, with stable IDs, owner, exact command, acceptance gate, rollback and current status."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/ops]
source_paths:
  - docs/DECISION-DATA-REFRESH-2026-11-21.md
  - docs/DECISION-PARTY-GENEALOGY.md
  - docs/SENATE-PROFILE-IMPACT.md
  - docs/LOAD-TEST-EVIDENCE.md
  - docs/POLICY-DECISIONS-2026-11-21.md
created: 2026-11-21
updated: 2026-11-21
source_commit: cf31f3c
---

# Actionable step register

Single source for "what to do next". [NEXT-ACTIONS](../10-STATE/NEXT-ACTIONS.md)
is the short ranked view; this note is the exhaustive register. All steps are
non-destructive (`git revert`, new commits/PRs, no force-push, no tag moves).
An unavailable check is `NOT PROVEN`, never PASS.

## A. Operational — data refresh and release (P0)

| ID | Step | Owner | Exact command / action | Acceptance gate | Rollback | Status |
|---|---|---|---|---|---|---|
| A-01 | Choose workflow-pin option A/B/C/D | owner | read `docs/DECISION-DATA-REFRESH-2026-11-21.md`; record decision in vault | written decision with date + owner | new decision supersedes | RESEARCH DONE — option A + ≥189-vote guard recommended; owner decision pending |
| A-02 | Implement chosen pin option | agent | edit `.github/workflows/data.yml` via PR; all 4 CI checks green | `gh run view <id>` SUCCESS incl. pin step | `git revert <sha>` | BLOCKED by A-01 |
| A-03 | Make automated corpus vote-aware (if option C) | agent | add vote ingest step with runner-reachable source or vote-bearing asset; no live-cdep dependency | fresh release `/api/votes total>0` after pin | `git revert <sha>` | RESEARCH DONE — release-asset merge deterministic (24,682 positions); pending A-01 |
| A-04 | Re-dispatch and prove data workflow | owner | `gh workflow run data.yml`; `gh run watch <id>` | SUCCESS, fresh release, `gh issue view 14 --json state` → CLOSED | no data change | OPEN |
| A-05 | Pin fresh vote-bearing release via PR | agent | branch + PR changing `data/latest-release.txt` | live `/api/health` tag + `/api/votes total>0` | new pin commit reverting marker | BLOCKED by A-03 |

## B. Data completeness

| ID | Step | Owner | Exact command / action | Acceptance gate | Rollback | Status |
|---|---|---|---|---|---|---|
| A-06 | Genealogy DROP follow-through: relabel docs/UI | agent | add dated notes in `METHODOLOGY.md`, `DATA-MODEL.md`, `DATA-ENRICHMENT-RESEARCH.md`, vault notes | no current doc claims populated genealogy; `check-doc-truth.sh` 0 | `git revert <sha>` | **DONE 2026-11-22** — §9 retitled retired + §9.5 DROP decision, column notes, research note, 2 vault notes; `e905682`; doc-truth 0, vault lint/sync clean |
| A-07 | Senate HOLD monitoring / exact-ID source search | agent | research exact GUID→person source; re-open only with ID evidence | report with exact source or explicit HOLD | none (research) | RESEARCH DONE — HOLD confirmed (0 exact GUID→person join); lift conditions named |
| A-08 | Seed licence register in local DBs | agent | `python -m pipeline.cli --db data/parlament.db licenses-seed` | `select count(*) from source_license` → 15, idempotent | DB backup in `/tmp` | **DONE 2026-11-22** — `licence register seeded: 15 entries written, 15 rows`; `select count(*)` → 15; idempotent |
| A-09 | Surface coverage dimensions in UI | agent | optional UI display beside `/api/coverage/dimensions` | UI 24/24, zero axe | `git revert <sha>` | OPEN (low priority) |
| A-10 | Verify no NULL snapshot hashes in future releases | agent | audit check already covers votes; assert in release script | next release has 0 NULL hashes | `git revert <sha>` | OPEN (low) |

## C. Frontend polish

| ID | Step | Owner | Exact command / action | Acceptance gate | Rollback | Status |
|---|---|---|---|---|---|---|
| A-11 | H3-D: wire shared states into remaining pages | agent | apply `EmptyState`/`LoadingState` where props fit (e.g. Voturi) | lint 0/0, build 0, UI 24/24 | `git revert <sha>` | **DONE 2026-11-22 (verified, no change needed)** — `Voturi.tsx` already renders `AsyncState`, which wraps `LoadingState`/`EmptyState`/`ErrorState`; R-05 wiring satisfies the contract |
| A-12 | H4-A newsletter/social proof | owner | decide data source or drop; no invented endorsements | written decision | new decision | RESEARCH DONE — DROP recommended (no endpoint/data); decision pending |
| A-13 | Add `footer.datasetRelease` ro/en key | agent | i18n key + use it in Footer | key diff script 0 missing | `git revert <sha>` | **DONE 2026-11-22 (verified, no change needed)** — `footer.datasetRelease` present in both `i18n.ts` locales and consumed by `Footer.tsx`; i18n key diff PASS |
| A-14 | WCAG AA re-check of touched UI | agent | axe gate via `ui_validate.py` | 24/24, zero axe | `git revert <sha>` | OPEN (continuous) |

## D. Platform and security

| ID | Step | Owner | Exact command / action | Acceptance gate | Rollback | Status |
|---|---|---|---|---|---|---|
| A-15 | Prove runtime read-only on disposable instance | agent/owner | controlled write probe on throwaway Render-like instance | write rejected with raw output | instance disposable | OPEN — research queued |
| A-16 | Formalize Vercel build-commit metadata | agent | capture GitHub status → deploy ID mapping in vault | note with SHA + deploy URL | none | PARTIAL (observed `afd1944`) |
| A-17 | Staging environment + staging load test | owner | supply staging URL; run `scripts/load_test.py` there | artifact with timestamp | none | OPEN — research queued |
| A-18 | Vercel Cron watchdog revisit | owner | only if a Vercel Function exists; otherwise keep DEFER | 200 from a real endpoint | `git revert <sha>` | DEFERRED (no Function) |
| A-19 | CSP tightening (remove unsafe-inline/eval) | agent/owner | staged change with browser evidence | enforcing CSP + UI 24/24 | `git revert <sha>` | OPEN (post-staging) |
| A-20 | GraphQL 404 recheck | agent | `curl -s -o /dev/null -w '%{http_code}' …/graphql` | 200 or documented as undeployed | none | RESEARCH DONE — POST returns 200 on both hosts; GET 404 was a probe artifact |

## E. Documentation, history and habit

| ID | Step | Owner | Exact command / action | Acceptance gate | Rollback | Status |
|---|---|---|---|---|---|---|
| A-21 | Research-date anomaly (`2025-11-12` vs git `2026-11-12`) | agent | provenance search in archives/git metadata | proven or explicitly unresolvable | none | OPEN — research queued |
| A-22 | Historic licence-seeding proof | agent | search CI logs/releases for `source_license` rows | proof or explicit NOT PROVEN | none | OPEN — research queued |
| A-23 | Vault maintenance after every change | agent | `vault_sync.py` → `vault_lint.py` → `check-doc-truth.sh` | all exit 0 | none | ACTIVE (habit) |
| A-24 | Keep PR queue empty | owner | `gh pr list --state open` triage with reasons | zero unexplained open PRs | reopen closed PR | ACTIVE |
| A-25 | Self-sustainability Phase 4 closure | owner | record watchdog/staging decisions | written decision | none | OPEN |
| A-26 | Blog/donations — remain dropped | owner | no action unless recipient supplied | decision doc unchanged | new decision | CLOSED |

## Dependency order

1. A-01 → A-02/A-03 → A-04 → A-05 (only P0 chain).
2. In parallel with research: A-16, A-20, A-21, A-22, A-23 (A-06, A-08, A-11, A-13 completed 2026-11-22).
3. After owner decisions: A-07, A-12, A-15, A-17, A-19, A-21, A-22, A-25.

## Research fleet for missing components

All six tailored research agents have delivered. Full evidence and updated
recommendations: [RESEARCH-FLEET](../50-RESEARCH/RESEARCH-FLEET-2026-11-21.md).
No code, data or settings were changed by the research.

## See also

[NEXT-ACTIONS](../10-STATE/NEXT-ACTIONS.md) · [EXECUTION-LOG](../10-STATE/EXECUTION-LOG-2026-11-21.md) · [GAP-REGISTER](../10-STATE/GAP-REGISTER.md) · [DECISIONS](DECISIONS.md)
