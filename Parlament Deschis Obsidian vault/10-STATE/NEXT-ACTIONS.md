---
id: NEXT-ACTIONS
type: state
title: "Tasks completed and most recommended next actions"
description: "Single at-a-glance record of what is verifiably done and the ranked actions to take next, with commands, gates, owners and rollbacks."
status: active
authority: canonical
tags: [type/state, lifecycle/active, domain/ops]
source_paths:
  - docs/CONTINUATION-STRATEGY-2026-11-21.md
  - docs/POLICY-DECISIONS-2026-11-21.md
created: 2026-11-21
updated: 2026-11-21
source_commit: d867ff2
---

# Tasks completed / next actions

Snapshot: `main` `d867ff2`, release `data-20261121-votes-001`, 189 live votes,
zero open PRs, branch protection active. Evidence detail is in
[EXECUTION-LOG](EXECUTION-LOG-2026-11-21.md) and [ACTION-LOG](ACTION-LOG.md).

## A. Tasks completed (verified)

| # | Task | Completion evidence |
|---|---|---|
| 1 | CI blocker (hooks after early return) fixed; review/audit/vault reports committed | PR #48 merged as `a518b7d`; four required checks green |
| 2 | Canonical vote/ideology routes, date bounds, analytics `meta`, OpenAPI regenerated | Live OpenAPI: canonical paths, zero `/api/api`; `/api/analytics/ideology` 200 with `meta` |
| 3 | Vote frontend empty/error states, source links, ro/en keys, a11y | UI gate 24/24 live, zero JavaScript errors, zero axe violations |
| 4 | Vote provenance backfill on re-ingest; 3 offline tests | `tests/test_vote_hash_backfill.py`; released votes have 0 missing hashes |
| 5 | Doc-truth checker repaired; UI gate widened 18→24 routes | `check-doc-truth.sh` → 0; live UI gate 24/24 |
| 6 | Licence register wired to `licenses-seed`, `init`, `build-corpus`; new audit check | 15 rows in prepared release DB; audit 275 known / 0 new |
| 7 | Honest per-dimension coverage endpoint | `GET /api/coverage/dimensions`, 20 scopes; legacy responses byte-identical |
| 8 | cdep acquisition resilience: bounded retries + offline `--strict` fallback | fake-failure tests; offline corpus build exits 0 after W2.8 |
| 9 | Count labels (1,217 group / 785 party / 2,002 total; 7,358 raw / 7,349 prepared) | `docs/API.md` "Count definitions"; `README.md` labels |
| 10 | Frontend lint warnings cleared (7→0) and missing `type="button"` fixed | `npm run lint` → 0 errors / 0 warnings |
| 11 | CRLF cache verification bug fixed; W2.8 duplicate closed stints skipped | offline build EXIT 0, 142 waves, `duplicate_stints: 0` |
| 12 | PR #48 + 5 follow-ups merged; branch protection enabled | `test/audit/docker/evidence-guards` required, 1 approval, no force-push/deletion |
| 13 | Backend then frontend deployed; enforcing CSP on both hosts | canonical routes live; byte-identical 226-byte CSP; bundle `index-C3QLvq6v.js` |
| 14 | Vote-containing release published and pinned | `data-20261121-votes-001`, 189 votes / 24,682 positions, 3 SHA-256 assets |
| 15 | Policies P-1/P-2/P-3 decided and implemented | `docs/POLICY-DECISIONS-2026-11-21.md` |
| 16 | PR triage complete | merged #47/#8, closed 7 stale/failing, zero open PRs |
| 17 | Post-release UI defects fixed (runtime person ID, h1 in loading states, gate settle) | PRs #51/#55; two consecutive live UI passes |
| 18 | Obsidian mirror maintained | 43 notes, vault lint clean, `vault_sync --check` clean |

## B. Most recommended next actions (ranked)

| # | Action | Owner | Exact next command / gate | Acceptance | Rollback / blocker |
|---|---|---|---|---|---|
| 1 | **Prove the daily data refresh and close issue #14** — the retry/offline fallback is deployed but no green runner execution has been observed | owner | `gh workflow run data.yml --repo nedaktov-ops/parlament-deschis`, then `gh run watch <id>`; check release tag in `/api/health` | workflow SUCCESS, fresh release published, issue auto-closes | no data changes; blocker: external cdep availability |
| 2 | **Document and surface the new coverage dimensions** — endpoint exists but `docs/API.md` omits it and CLI `coverage` prints mandates only | agent | add endpoint to `docs/API.md`; optionally extend `pipeline/cli.py coverage` output | `curl …/api/coverage/dimensions` shows votes/biographies; doc-truth 0 | `git revert <sha>` |
| 3 | **Close the 60 s-poll residual in docs** — code fixed (P-1) but several strategy docs still describe "real-time" alerts | agent | grep for `refetchInterval`/`real-time` claims; add dated notes in `docs/` | no current doc claims real-time polling; doc-truth 0 | `git revert <sha>` |
| 4 | **Party genealogy decision** — 0 links in the corpus; source licence/coverage must be decided, never inferred | owner + agent | choose Wikidata/Party Facts relation source or drop feature; then new recipe with provenance + audit | `select count(*) from organization where previous_party_id is not null or successor_party_id is not null` > 0, or recorded drop decision | `git revert <sha>`; blocker: source decision |
| 5 | **Senate historical profiles** — discovery guarded (128/134 GUIDs) but ingest deferred on identity risk | owner + agent | copy-DB impact report first; exact-ID-only identity; then ingest with evidence | profiles > 0 and group-semantics outputs bit-identical; audit 0 new | `git revert <sha>`; blocker: identity decision |
| 6 | **H3-D / H4-A frontend polish** — `EmptyState`/`LoadingState` still unused; footer not finished | agent | wire states into live pages; footer at 320 px; UI gate | UI 24/24, zero JS errors, zero axe; lint 0/0 | `git revert <sha>` |
| 7 | **Staging load test + Vercel Cron watchdog** | owner + agent | staging URL decision, record `scripts/load_test.py` output; add `crons` to `vercel.json` | run artifact with timestamp; freshness gate green | `git revert <sha>`; blocker: staging environment |
| 8 | **Close remaining NOT PROVEN items** — exact Vercel commit, runtime read-only enforcement, historic licence seeding, 2025-11-12 research date | agent/owner | platform access for deploy metadata; disposable instance write probe; archive research provenance | each item either proven with raw output or explicitly closed as unresolvable | no code data changes |
| 9 | **Maintain the mirror after every change** | agent | `python3 scripts/vault_sync.py` → `python3 scripts/vault_lint.py` → `bash scripts/check-doc-truth.sh`; commit code and vault together | all three exit 0 | none |

Ordering rationale: #1 removes the only critical operational unknown (freshness); #2–#3 are cheap truth improvements; #4–#6 are the remaining product gaps that need decisions before data work; #7–#8 are hardening; #9 is the habit that keeps this vault trustworthy.

## C. See also

[START-HERE](../00-START/START-HERE.md) · [EXECUTION-LOG](EXECUTION-LOG-2026-11-21.md) · [GAP-REGISTER](GAP-REGISTER.md) · [TASK-REGISTER](../20-DIRECTION/TASK-REGISTER.md) · [CONTRADICTIONS](CONTRADICTIONS.md) · [RESEARCH-LOG](../50-RESEARCH/RESEARCH-LOG.md)
