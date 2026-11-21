---
id: ACTION-LOG
type: state
title: "Completed actions and remaining tasks"
description: "Evidence-backed log of what was actually completed in Wave 0/1, what remains by priority, and the ranked next steps with exact commands and rollbacks."
status: active
authority: canonical
tags: [type/state, lifecycle/active, domain/ops]
source_paths:
  - docs/CONTINUATION-STRATEGY-2026-11-21.md
  - docs/GATE-EVIDENCE-2026-11-21.md
  - docs/BACKUP-EVIDENCE-2026-11-21.md
created: 2026-11-21
updated: 2026-11-21
source_commit: f7a2325
---

# Action log — completed and remaining

Companion to [START-HERE](../00-START/START-HERE.md),
[TASK-REGISTER](../20-DIRECTION/TASK-REGISTER.md) and
[CONTINUATION-STRATEGY](../20-DIRECTION/CONTINUATION-STRATEGY.md).
Rule: a task is `completed` only with printed command output; a task that
cannot be executed is `blocked` or `NOT PROVEN`, never silently green.

**State at logging:** local HEAD `f7a2325`, branch `review/completion-20261121`
pushed, PR [#48](https://github.com/nedaktov-ops/parlament-deschis/pull/48)
OPEN with `test`, `audit`, `docker`, `evidence-guards` all SUCCESS. Nothing
merged, no branch protection changed, nothing deployed.

## A. Completed actions (Wave 0/1)

| ID | Action | Completion evidence | Status |
|---|---|---|---|
| W0.1 | Freeze verified baseline (HEAD, divergence, pin, CI, PRs, issue) | `docs/BACKUP-EVIDENCE-2026-11-21.md` §Baseline; `VERSIONS.txt` sha `cbc414de…` | completed |
| W0.2 | Full backup: bundle + DB copies + vault + QA + 55-artifact SHA-256 manifest | `git bundle verify` OK (148 refs); `sha256sum -c` all 55 `OK`; bundle sha `89c9c175…` | completed |
| W0.3 | Sandbox restore drill | `git clone --no-local` → HEAD `96e6fdd…` == recorded; clean sandbox | completed |
| W0.4 | Non-destructive rollback policy pinned in `DASHBOARD-STRATEGY.md`; nonexistent `npm test` gate removed; WCAG AA and approved palette | `grep` for `reset --hard`/`origin --force`/`origin --delete`/`npm test` → no current claims; doc-truth 0 | completed |
| W0.5 | Four-way Vite conflict resolved against shipped `^6.0.0`; `fb95e56` cited as real dependency bump | `grep -rn 'Vite 8\|^5.0.0'` → historical only; Node 18 blocker marked obsolete (Node v24 present) | completed |
| W0.6 | Vault re-anchored from "3 ahead / 6fd6028" to real HEAD and 8 commits; strategy note added | `vault_lint` 41 notes clean; [GIT-POSITION](../10-STATE/GIT-POSITION.md) 8-commit list | completed |
| W1.1 | Full pre-push gate sweep | `docs/GATE-EVIDENCE-2026-11-21.md` — 11 gates PASS with exit codes; real browser run 24/24 | completed |
| W1.2 | Push branch + open PR #48 | `git push` exit 0 (new remote branch); `gh pr create` → PR #48 OPEN | completed |
| W1.3 | Make PR CI green | `gh pr checks 48 --watch` → `test`, `audit`, `docker`, `evidence-guards` SUCCESS (twice, after follow-up commits) | completed |
| W1.8 | Record PR/CI evidence in docs and vault | `docs/GATE-EVIDENCE…` W1.2/W1.3 addendum; doc-truth 0 after reword | completed |

Earlier completed work, preserved from the 2026-11-21 review: F1–F11 fixes
(`3eb3c0a`), audit/vault reports (`221cf78`), comprehensive review (`6fd6028`),
Obsidian state-mirror vault (`a311382`), idempotent sync bootstrap
(`537cef7`–`96e6fdd`), continuation program (`7d1c438`–`f7a2325`).

## B. Remaining tasks by priority

| ID | Task | Priority | Owner | Blocker | Next action |
|---|---|---|---|---|---|
| W1.4 | Merge PR #48 to `main` | P0 | owner | none (checks green) | `git tag w1-before-merge origin/main`; `gh pr merge 48 --merge` |
| W1.5 | Enable branch protection with required checks | P0 | owner | W1.4 | Protection API: contexts `test,audit,docker,evidence-guards` |
| W1.6 | Deploy backend first, prove canonical routes + `meta` | P0 | owner | W1.4 + deploy access | `curl …/api/analytics/ideology` → 200 + `meta`; openapi 0 `/api/api` |
| W1.7 | Deploy frontend second, prove new bundle + 24/24 live | P0 | owner | W1.6 | Vercel hash ≠ `index-D61EXxHz.js`; `ui_validate.py` 24/24 live |
| W2.1 | Wire `ensure_source_licenses()` into tested CLI path; seed 15 rows | P0 | agent | none | branch + PR; `select count(*) from source_license` → 15 |
| W2.2 | Publish per-dimension coverage (`votes`, `biographies`) | P0 | agent | none | `pipeline/coverage.py` + API; honest `none` before votes exist |
| W2.3 | Repair cdep.ro acquisition (retry/cache/offline fallback) | P0 | agent | external source | start early — long external lead time; keep `--strict` |
| W2.4 | Ingest votes on copy, publish immutable release, pin, verify live `total>0` | P0 | owner + agent | W2.3, release access | dry-run → approval → `--apply` → release → pin |
| W2.5 | Label 1,217 group / 785 party / 2,002 total; 7,358 raw / 7,349 prepared | P1 | agent | none | `docs/API.md`, `README.md`, UI wording |
| W2.6 | Fix `ChesSource.ingest_ches` committing during dry run, then apply CHES/Party Facts | P1 | agent | none | `sources/ches.py` + tests |
| W2.7 | Genealogy / Senate profile decisions | P1 | owner + agent | identity & licence source | no name-only identity; drop genealogy if no licensed source |
| W3.1 | Frontend H3-D / H4-A, dead code, 7 lint warnings, one missing `type="button"` | P1 | agent | none | `npm run lint` 0 warnings; UI 24/24 |
| W3.2 | Decide 60 s poll vs "on release" alerts; CSP enforcement; GraphQL 404 | P1 | owner + agent | product policy | record decision with date + owner |
| W4.1 | Staging load test, Cron watchdog, end-to-end verify/freshness | P2 | owner + agent | staging | `scripts/load_test.py` artifact; `verify-deploy.sh` |
| W4.2 | Blog/SEO/donations drop-or-scope decision | P2 | owner | donation recipient | written decision closes AMBER |
| Q1 | Triage 9 open PRs (no bulk close) | P1 | owner | none | label/rebase/close with rationale |
| Q2 | Verify live SPA rendering and read-only runtime | P2 | agent | disposable instance | browser + controlled write probe |

Stable-ID tasks T-2026-001…018 from the [TASK-REGISTER](../20-DIRECTION/TASK-REGISTER.md)
remain open unless explicitly superseded here; this log does not renumber them.

## C. Most effective next steps (ranked, dependency-ordered)

1. **Merge the already-green PR** — highest leverage, zero new code. Owner:
   `git tag w1-before-merge origin/main && gh pr merge 48 --merge`, then confirm
   main checks SUCCESS. Rollback: `git revert -m 1 <merge_sha>` on a new branch.
2. **Enable branch protection** immediately after merge — without it every
   later gate is advisory. Owner-only API: contexts `test,audit,docker,evidence-guards`,
   `enforce_admins: true`, block force-push/deletion. Rollback: owner reverses the setting.
3. **Deploy backend before frontend** — the live ideology 404 and double-prefix
   calls are user-visible. Verify `/api/analytics/ideology` 200 with `meta` and
   zero `/api/api` paths in live OpenAPI before touching Vercel.
4. **Deploy frontend second** — verify hashed bundle changed and run the 24-route
   browser gate against the live proxy. Never invert 3 and 4.
5. **Start the cdep acquisition fix on a branch now** — external lead time is the
   critical path to any data release; retry/backoff + warm cache + offline rebuild,
   keep `--strict` and never substitute third-party rows for official ledgers.
6. **Seed the licence register and honest coverage dimensions** — small, testable
   prerequisites for releasing vote data; `source_license` 15 rows and
   `votes: none` shown before ingestion.
7. **Publish the vote-containing release** — the 10× centrepiece is still absent
   in production (`/api/votes total=0`); dry-run on a copy, strict audit 0 new,
   immutable tag, pin marker, owner triggers Render.
8. **Label the two switch and two membership definitions** — cheap, high-trust
   correction that removes contradictory public numbers.
9. **Close owner policy decisions** (poll semantics, CSP enforcement, blog/
   donations) so Wave 3/4 stop being AMBER.
10. **Then** work the vision gaps: genealogy, Senate profiles, H3-D/H4-A.

Steps 1–4 and 9 are owner/deploy gates; 5–8 can be executed as ordinary
branches + PRs by continuation agents under the recipe template in
[CONTINUATION-STRATEGY](../20-DIRECTION/CONTINUATION-STRATEGY.md).

## D. NOT PROVEN register (unchanged)

Exact Vercel build commit; client-side SPA rendering; runtime read-only
enforcement; historical licence seeding; original `2025-11-12` research date.
Each needs a named resolver, not a guess — see
[RESEARCH-LOG](../50-RESEARCH/RESEARCH-LOG.md).

## E. Second execution pass — Wave 2/3 agent steps (2026-11-21)

Five custom recipe agents (X1–X5) implemented the agent-doable steps from
section C with disjoint file ownership. Commit `987536a`; generated vault
notes regenerated at `b2ccea7`.

| ID | Action | Completion evidence | Status |
|---|---|---|---|
| W2.1 | Licence register wired into `licenses-seed` CLI, `init`, `build-corpus`; `check_license_quarantine` audit check | CLI help lists command; seed on copy → 15 rows (9 redistributable / 6 cross-check); second run idempotent; strict audit 275 known / 0 new with 0 new findings; tracked DBs unchanged (SHA manifest) | completed locally |
| W2.2 | Honest per-dimension coverage | `GET /api/coverage/dimensions` 200 with 20 scopes; votes `none`/`partial` never `full`; legacy `/api/coverage*` byte-identical (SHA `4a61ab18…`); 5 new tests | completed locally |
| W2.3 | cdep acquisition resilience | retries 8 / backoff cap 45 s with fake-failure tests; `data.yml` online→offline `--strict` fallback with separate third-party cache; YAML parses; flags verified against `--help` | completed locally; runner fix needs a real workflow run (owner) |
| W2.5 | Count labels | `docs/API.md` "Count definitions" section and `README.md` labels: 1,217 group / 785 party / 2,002 total; 7,358 raw / 7,349 prepared; doc-truth 0 | completed |
| W3.1 | Frontend quick wins | `type="button"` added; all 7 exhaustive-deps warnings resolved with evidence (lint 0 errors / 0 warnings); build exit 0; LiveFeed guard exit 0; UI gate 24/24 real browser | completed |
| — | CRLF cache bug in `pipeline/collect.py` | cached pages now read with `newline=""`; new regression test passes; offline rebuild cleared all 144 profile failures | completed locally |

### Newly discovered residual (do not guess)

The offline rebuild now gets past source fetching but fails with
`UNIQUE constraint failed: index 'ux_membership_closed_stint'` during ingest
(fresh DB, `--offline --skip-committees --strict`). Root cause NOT PROVEN;
it is a separate schema/ingest defect. A dedicated recipe must investigate and
fix it before the workflow offline fallback can succeed. Logged as **W2.8**,
priority P0, owner: agent, blocker: none, next: reproduce on a copy and trace
the duplicate closed-stint group.

### Still remaining after this pass

- Owner gates unchanged: W1.4 merge PR #48, W1.5 branch protection,
  W1.6/W1.7 backend-then-frontend deploy, W4.2 policy decisions.
- W2.4 vote-containing release (needs W2.8 + owner release/dispatch).
- W2.6 CHES dry-run commit bug, W2.7 genealogy/Senate decisions,
  W3.2 60 s poll / CSP / GraphQL decisions, W4.1 staging load test,
  Q1 nine-PR triage, Q2 live SPA/read-only verification.
- Document the new `/api/coverage/dimensions` endpoint in `docs/API.md`
  (X2 did not own that file in this pass; W2.5 agent edited it for labels only).

Verification for this pass: pytest **404 passed**, ruff clean, lint **0 errors /
0 warnings**, build exit 0, doc-truth 0, strict audit **275/0**, UI **24/24**
real browser, vault lint 42 notes, sync `--check` clean, workflow YAML valid.
