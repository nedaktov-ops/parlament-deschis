---
id: LINK-REPAIR-STRATEGY
type: runbook
title: "Link and button repair strategy — waves, gates, safety (2026-11-22)"
description: "Non-destructive repair programme for the 258 clickables investigated on 2026-11-22: scope, eight waves, GREEN/AMBER/RED gates, backups, rollbacks, supervisor contract and GitHub policy."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/frontend]
source_paths: [frontend/src, frontend/package.json, .github/workflows/ci.yml, scripts]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Link and button repair strategy

**Decision:** repair only the defects proven by the
[clickable investigation](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md),
in serialised waves, each with a backup, checkpoints, a rollback and a
supervisor gate. This note is the strategy; the implementable steps are in
[LINK-REPAIR-RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md); the running record is
[LINK-REPAIR-JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md).

## 1. Baseline (verified this session)

| Fact | Evidence |
|---|---|
| Local branch `main`, HEAD `8811216`, clean product tree | `git status`, `git rev-parse HEAD` |
| `origin/main` equals local HEAD | `git rev-parse origin/main` → `8811216…` |
| Investigation produced uncommitted vault notes plus a modified tracked `START-HERE.md` | `git status --short` at strategy authoring; L-00 enumerates **exact paths at run time**, never a count (supervisor S-08) |
| CI required checks: test, audit, docker, evidence-guards | `.github/workflows/ci.yml:17,59,80,111` |
| i18n parity and route/nav guards run in CI | `ci.yml:46-50`; `scripts/check_i18n_keys.mjs`; `scripts/check_routes_nav.mjs` |
| Front end gates available locally | `frontend/package.json:8-11` (`lint`, `build`, `i18n:check`) |
| Browser has local dev (`127.0.0.1:5188`) and Vercel pages | chrome-devtools `list_pages` |
| `https://github.com/parlament-deschis` returns HTTP 404; `https://github.com/nedaktov-ops/parlament-deschis` returns HTTP 200 | `curl -L -o /dev/null -w '%{http_code}'` probe this session — this upgrades C06-013 from SUSPECT to **BROKEN** for the `About.tsx:6` literal |

## 2. Principles (non-negotiable)

1. **Evidence-only scope.** Only items in the investigation master report §3–§5
   may be changed. No opportunistic refactors, no data, no release pin, no
   workflows, no branch protection, no deployment without an explicit owner gate.
2. **One owner per file per wave.** Waves are serialised; recipe file lists are
   exclusive. No two code-editing agents touch the same file in the same wave.
3. **Non-destructive git.** Work on `repair/links-*` branches. No `reset --hard`,
   no force-push, no tag moves, no history rewrite. Integration is `--ff-only`.
4. **Backup before every wave.** Full bundle + worktree archive + SHA-256
   manifest + `git bundle verify` restore drill (§5).
5. **Atomic checkpoints.** One logical change per commit; message states recipe
   ID, evidence anchor, gate output and rollback SHA.
6. **Evidence over assertion.** A wave is GREEN only when its gate commands
   were actually run and their output is recorded in the vault. An unrun check
   is **NOT PROVEN**, never PASS.
7. **Supervisor authority.** The supervisor can issue STOP (RED) or HOLD (AMBER)
   at any checkpoint. Its verdict is recorded with citations.
8. **Honest no-change.** If code inspection shows an item is already correct or
   a fix would trade one defect for another, the recipe records a NO-CHANGE
   decision with evidence rather than inventing a change.

## 3. Scope

**In scope:** the two confirmed BROKEN items, the deduplicated SUSPECT list in
master report §4.1–§4.5, the seven dead controls in §4.4, and the regression
harness additions in §4.5. Plus the newly network-confirmed broken GitHub URL.

**Out of scope:** backend behaviour changes (except reading it to size a frontend
limit), data files, `data/latest-release.txt`, CI workflow edits, dependency
upgrades, branch protection, merging to `main`, deploying to Vercel/Render, and
any of the 19 NOT PROVEN items until a resolver actually runs.

## 4. Wave plan

| Wave | Branch | Recipes | Files owned (exact, repo-relative) | Gate | Supervisor |
|---|---|---|---|---|---|
| W0 | `repair/links-base` | L-00 | vault notes only (exact paths enumerated at run time) | baseline clean + backup verified | protocol authored |
| W1 | `repair/links-w1` | L-01, L-02 | `frontend/src/pages/Ideology.tsx`, `frontend/src/pages/Mps.tsx` — **no `i18n.ts`** (keys already exist) | lint + build + browser Ideology | audit |
| W2 | `repair/links-w2` | L-03, L-04+L-05 (one agent, two atomic commits), L-06 | `frontend/src/components/Footer.tsx`, `frontend/src/components/About.tsx`, `frontend/src/router.tsx`, `frontend/src/config/links.ts` (new), `frontend/src/pages/LiveDashboard.tsx`, `frontend/src/pages/Traseism.tsx`, `frontend/src/pages/Mps.tsx`, `frontend/src/i18n.ts` — **only L-03 owns i18n in W2** | lint + build + routes + i18n + browser nav/scope | audit |
| W3 | `repair/links-w3` | L-07, L-08, L-09, L-10, L-11 | `frontend/src/pages/Voturi.tsx`, `frontend/src/components/RollCallTable.tsx`, `frontend/src/components/CommitteeControl.tsx`, `frontend/src/pages/LiveDashboard.tsx` (**L-09 sole W3 owner**), `frontend/src/pages/PartyProfile.tsx`, `frontend/src/pages/PartyComparison.tsx`, `frontend/src/i18n.ts` (**L-07 sole W3 owner, adds all three W3 keys**) | lint + build + i18n + browser click-through | audit |
| W4 | `repair/links-w4` | L-12, L-13, L-14 | `frontend/src/components/Hemicycle.tsx`, `frontend/src/pages/Topuri.tsx`, `frontend/src/components/SwitchTimeline.tsx`, `frontend/src/components/PartyNetwork.tsx`, `frontend/src/components/PartyListTable.tsx`, `frontend/src/i18n.ts` (**L-13 sole W4 owner, adds all three W4 keys**) | lint + build + i18n + keyboard probe | audit |
| W5 | `repair/links-w5` | L-15 | `frontend/src/components/EmptyState.tsx`, `frontend/src/components/LoadingState.tsx`, `frontend/src/components/DashboardCard.tsx`, `frontend/src/components/PartyComparisonMatrix.tsx`, `frontend/src/components/TimeSlider.tsx`, `frontend/src/components/ui/AgeDistributionSection.tsx` — **`i18n.ts` is read-only in W5** | lint + build + importer re-grep | audit |
| W6 | `repair/links-w6` | L-16 | `scripts/check_routes_nav.mjs`, `scripts/ui_state_probe.py` | guard scripts exit 0 + CI-equivalent | audit |
| W7 | `repair/links-w7` | L-17 | none (integration) | all wave gates replayed | final sign-off; **owner gate for merge/deploy** |

Integration after each GREEN wave: `git checkout repair/links-base &&
git merge --ff-only repair/links-wN`. A RED wave is never merged.

### 4.1 Corrected file and i18n ownership register (supervisor S-01, S-02, S-05, S-06)

A file may appear in only **one recipe per wave**. Two recipes needing the same
file in one wave are executed by **one agent in two atomic commits** (L-04+L-05), or
moved to a later wave (L-09 stays in W3, where `LiveDashboard.tsx` is now listed).
`frontend/src/i18n.ts` has exactly one owner per wave:

| Wave | Sole i18n owner | Keys it may add |
|---|---|---|
| W1 | none | none |
| W2 | L-03 | `footer.sourceCode` |
| W3 | L-07 | `view.voturi.searchHint`, `vote.positionsTruncated`, `committee.noChair` |
| W4 | L-13 | `filter.minVotes`, `filter.minVotesPlaceholder`, `common.viewAll` |
| W5 | none (read-only) | none; `mps.compareLink` stays because L-02 renders it |

L-02's delete-keys alternative was removed: it now always renders the link, so
the supervisor's S-03 contradiction no longer exists.

## 5. Backup and rollback protocol

Before each wave, from the current integration branch:

```bash
WAVE="<WAVE_ID>"   # expand literally in the wave note, e.g. W0, W1
ROOT="/tmp/opencode/backups/link-repair/$WAVE"
mkdir -p "$ROOT"
git bundle create "$ROOT/pre.bundle" --all
git rev-parse HEAD > "$ROOT/pre.sha"
git status --porcelain > "$ROOT/pre.status"
tar -czf "$ROOT/worktree.tgz" -C /home/nedaktov/parlament-deschis \
  --exclude=.git --exclude=node_modules --exclude=.venv --exclude=.next --exclude=dist .
(cd "$ROOT" && sha256sum pre.bundle pre.sha pre.status worktree.tgz > SHA256SUMS)
git bundle verify "$ROOT/pre.bundle"
tar -tzf "$ROOT/worktree.tgz" >/dev/null
(cd "$ROOT" && sha256sum -c SHA256SUMS)
```

Rollback of a checkpoint: `git revert <checkpoint-sha>` (additive; never reset).
Rollback of a whole wave: stay on the wave branch, revert checkpoints in reverse
order, re-run the gate; do not merge. Catastrophic restore: create a new branch
from `pre.sha` in `pre.bundle` and extract `worktree.tgz` into a scratch path.
The manifest must verify before any wave starts.

## 6. Gate definitions

| Gate | Meaning | Required evidence |
|---|---|---|
| GREEN | every listed command exited 0 and output is recorded | command + exit code + output excerpt in the wave note |
| AMBER | code is sound but one check cannot run in this environment | name the missing check and its resolver; do not merge without supervisor approval |
| RED | any check failed, a file outside the recipe list changed, or a new defect appeared | stop, revert wave checkpoints, record evidence |

Per-wave gate commands (run from repo root unless noted):

```bash
cd frontend && npm run lint && npm run build && cd ..
node scripts/check_i18n_keys.mjs
node scripts/check_routes_nav.mjs
python3 scripts/vault_sync.py --check
python3 scripts/vault_lint.py
bash scripts/check-doc-truth.sh
git diff --check
```

Browser spot-check is performed by the lead on the local dev server with
chrome-devtools. Every wave note must contain two explicitly titled subsections,
**Code evidence** and **Browser evidence**, each stating scope, a raw capture
path where applicable, the observed result and its limits. A browser check that
cannot run is AMBER/NOT PROVEN for that acceptance item only, with a named
resolver — never PASS, never a reason to mark the whole wave GREEN (supervisor
S-12). `pytest` and the strict corpus audit are not frontend gates; they are
replayed at W7 only if the environment can run them (otherwise AMBER/NOT PROVEN).

## 7. Supervisor contract

A supervisor sub-agent is dispatched once with the investigation master report,
all seven recipe notes, this strategy and the recipes note as its inputs. It
authors [LINK-REPAIR-SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md): the
stop conditions, per-wave audit checklist, agent-behaviour rubric and sign-off
template. After every wave it is re-entered with the wave note, the diff
summary and the gate output, and issues GREEN / AMBER / RED with citations. It
is read-only on product code; it can only write its supervision note and its
verdicts into the vault. It does not merge or deploy.

## 8. Tool and skill allocation

Recipes are bespoke prompts mapped onto available specialist agents; the recipe
note is the durable, reusable artefact.

| Role | Agent speciality | Used in |
|---|---|---|
| Safety / git | `git-master`, `devops-automator` | L-00, L-17 |
| Surgical frontend edits | `minimal-change-engineer` | L-01, L-02, L-09, L-13, L-14, L-15 |
| Router/scope/navigation | `frontend-developer` | L-03…L-08, L-11 |
| Interaction semantics | `accessibility-auditor` | L-10, L-12 |
| Regression guards | `qa-reviewer` | L-16 |
| Supervision | `general` (dedicated, persistent session) | all waves |

## 9. GitHub policy

Permission to push exists, but only `repair/links-*` branches are pushed, and
only after their wave is GREEN and supervisor-signed. **No push to `main`, no
PR merge and no deploy** without an explicit owner decision; those are owner
gates recorded in the vault. Required CI checks remain test / audit / docker /
evidence-guards with one approval and no force-push.

## 10. Vault write-back

At every wave: create/update the wave section in
[LINK-REPAIR-JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md), bump
`updated`, run `vault_sync.py --check`, `vault_lint.py`, doc-truth and
`git diff --check`, then commit the vault note together with that wave's code
checkpoints. No `_generated/*` file is ever hand-edited.

## See also

[CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) ·
[LINK-REPAIR-RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) ·
[FRONTEND-REPAIR-STRATEGY](FRONTEND-REPAIR-STRATEGY.md)
