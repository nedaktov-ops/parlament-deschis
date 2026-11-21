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

Exhaustive register: [ACTION-PLAN](../20-DIRECTION/ACTION-PLAN.md). Quick view: [START-HERE](../00-START/START-HERE.md) · [EXECUTION-LOG](EXECUTION-LOG-2026-11-21.md) · [GAP-REGISTER](GAP-REGISTER.md) · [TASK-REGISTER](../20-DIRECTION/TASK-REGISTER.md) · [CONTRADICTIONS](CONTRADICTIONS.md) · [RESEARCH-LOG](../50-RESEARCH/RESEARCH-LOG.md)

## D. Execution results for items 1–9 (2026-11-21)

| # | Outcome | Evidence |
|---|---|---|
| 1 | **PARTIAL — issue #14 stays OPEN.** Dispatched run `44909412878`: cache seed worked, collect/audit/prepare/release all succeeded, new release `data-44909412878-1` published. Pin step failed because branch protection blocks the bot's direct push (`GH006`). The new corpus has **no vote tables**, so pinning it would regress production; the vote release remains pinned. Owner options A–D recorded in `docs/DECISION-DATA-REFRESH-2026-11-21.md`. | run log + `gh release list` + live `/api/votes total=189` |
| 2 | **DONE** — `/api/coverage/dimensions` documented in `docs/API.md`, CLI prints dimensions, 4 new tests; pytest 408. | PR #59 |
| 3 | **DONE** — dated P-1 supersession notes on real-time/60 s claims in strategy docs; `check-doc-truth.sh` 0. | PR #59 |
| 4 | **DECIDED: DROP** party genealogy — no licence-complete source declares an ID-addressable relation; Wikidata relations have zero references, Party Facts codebook says coding incomplete, PolPaL licence NOT PROVEN, SER-PROM ShareAlike. Report: `docs/DECISION-PARTY-GENEALOGY.md`. | PR #59 |
| 5 | **DECIDED: HOLD** Senate historical profiles — 0 exact `senat_guid` identifiers, name-only auto-link is prohibited; copy-DB baseline and traseism SHA recorded in `docs/SENATE-PROFILE-IMPACT.md`. | PR #59 |
| 6 | **DONE** — shared `EmptyState`/`LoadingState` wired to Mps/Committees/Parties; footer shows real dataset release tag; lint 0/0, build 0, UI 24/24. H4-A newsletter/social proof remains unimplemented (no backing data). | PR #59 |
| 7 | **DONE (local) / DEFER (cron)** — load test: 900 requests, 0 errors, p95 297.6 ms (parties p99 505.4 ms noted); evidence in `docs/LOAD-TEST-EVIDENCE.md`. Vercel cron deferred: no Vercel Function exists, a cron would 404. Staging NOT PROVEN. | PR #59 |
| 8 | **PARTIAL** — Vercel build commit now tied to `afd1944` via GitHub status; runtime write path probed (`POST /api/admin/poll` → 503 without token) but a true disposable-instance write probe remains NOT PROVEN; historic licence seeding and research date remain unresolvable. | master probes |
| 9 | **DONE** — mirror maintained after every change: `vault_sync.py`, `vault_lint.py`, `check-doc-truth.sh` all green at each checkpoint. | vault checks |

### Revised top priority after this pass

1. Owner chooses option A/B/C/D for the data workflow pin (item 1) — the only remaining P0 operational unknown.
2. Then: staging load test, H4-A newsletter/social polish (needs data source), and the two decision follow-throughs (genealogy relabelling, Senate hold monitoring).

## E. Progress snapshot — plugin install and Docker remedy (2026-11-21)

**Completed in this pass**
- Obsidian now carries the exhaustive [ACTION-PLAN](../20-DIRECTION/ACTION-PLAN.md)
  (26 stable-ID steps) and the six-agent [RESEARCH-FLEET](../50-RESEARCH/RESEARCH-FLEET-2026-11-21.md)
  evidence note; vault lint 46 notes, doc-truth 0, sync clean.
- Vercel plugin installed **globally** with `opencode plugin add github:vercel/vercel-plugin`
  (global config diff: added `"plugins": ["github:vercel/vercel-plugin"]`). Vercel
  skills are now available in-session (deployment, routing, CSP, schedules,
  verification, CLI); the Vercel MCP still needs `/mcps` → vercel → sign-in, so
  no new Vercel tools are exposed yet. `npx vercel-plugin doctor` is not
  available as an npm executable in this environment.
- Docker CI failure root cause proven: `download_dataset.py` in the Docker
  `data` stage calls `api.github.com` **unauthenticated**, so a shared-runner
  rate limit returns `HTTP 403: rate limit exceeded` (run `44914654135`).
  `scripts/download_dataset.py` already accepts `GITHUB_TOKEN` from the
  environment and strips Authorization on cross-host redirects, so the fix is
  a BuildKit secret mount in `Dockerfile` plus `secrets:` on the build step in
  `.github/workflows/ci.yml` — no new secret values introduced.

**Remaining after this pass**
- Implement and verify the authenticated dataset download in Docker (in progress).
- Owner decision A/B/C/D for the workflow pin; then option A + ≥189-vote guard.
- Release-asset vote merge + `assert-votes` gate (A-03).
- Genealogy/Senate relabelling, i18n key, Voturi state wiring, staging load
  test, staged CSP tightening, and the owner-only policy decisions.

See [RESEARCH-FLEET](../50-RESEARCH/RESEARCH-FLEET-2026-11-21.md) for evidence
and [ACTION-PLAN](../20-DIRECTION/ACTION-PLAN.md) for gates and rollbacks.
