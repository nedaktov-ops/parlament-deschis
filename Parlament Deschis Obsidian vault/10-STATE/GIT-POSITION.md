---
id: git-position
type: state
title: Git Position and CI State
description: Branch, HEAD, ahead/behind, unpushed commits, CI conclusions, protection, PR/issue state and required deploy order.
status: active
authority: canonical
tags: [type/state, lifecycle/active, domain/ops]
source_paths: [docs/CONTINUATION-STRATEGY-2026-11-21.md, docs/COMPREHENSIVE-REVIEW-2026-11-21.md, docs/GAP-ANALYSIS-2026-11-21.md, docs/POST-INITIAL-AUDIT-2026-11-21.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 96e6fdd
---

# Git position and CI state

> **Addendum (2026-11-21):** Re-anchored 2026-11-21 from `docs/CONTINUATION-STRATEGY-2026-11-21.md` §0. Vault mirror: [CONTINUATION-STRATEGY](../20-DIRECTION/CONTINUATION-STRATEGY.md).

Directly observed at `96e6fdd`. Interpretation of the live state is in
[CURRENT-STATE](CURRENT-STATE.md); gap IDs in [GAP-REGISTER](GAP-REGISTER.md).

> **Historical (2026-11-21):** at the earlier post-initial-audit snapshot this note recorded HEAD `6fd6028`, 3 ahead / 0 behind; that value is superseded by this re-anchor.

## Branch and commits

| Item | Value |
| --- | --- |
| Branch | `review/completion-20261121` |
| HEAD | `96e6fdd` (full `96e6fdd5d75c3f7f51a6888a693eeca40e954674`) |
| `origin/main` / GitHub default | `6b848f1` |
| Ahead / behind | **8 ahead / 0 behind** |
| Remote branch containing HEAD | none — all eight commits are unpushed |

Unpushed commits, oldest first (8):

| Commit | Summary |
| --- | --- |
| `3eb3c0a` | `fix(review): complete CI, vote API, a11y and docs gaps (2026-11-21 review)` |
| `221cf78` | `docs: add docs-vs-live gap analysis from coordinated six-agent review` |
| `6fd6028` | `docs: exhaustive post-initial audit with contradiction resolutions` (historical audit snapshot) |
| `a311382` | `feat(vault): build Obsidian state mirror with idempotent sync and lint` |
| `537cef7` | `fix(vault-sync): anchor generated notes on last non-vault commit` |
| `bf75556` | `chore(vault): regenerate generated notes at stable source commit` |
| `bc4bee2` | `style(vault-sync): satisfy ruff UP022 (capture_output)` |
| `96e6fdd` | `chore(vault): regenerate notes after style fix` |

## CI check conclusions on main

Recent runs on `main` (e.g. check run `44879894155`):

| Check | Conclusion |
| --- | --- |
| `test` | **failure** — 4 `react-hooks/rules-of-hooks` errors in `Ideology.tsx` |
| `audit` | success |
| `evidence-guards` | success |
| `docker` | skipped |
| `Deploy verify` | skipped |

All six most recent CI runs on main failed on the same hooks-after-return
defect that local HEAD fixes (R9 in [CONTRADICTIONS](CONTRADICTIONS.md)).
`ci.yml:3-5` filters `push` to `branches: [main]` and also runs on
`pull_request` and `workflow_dispatch` (R11) — the RED state is not a missing
trigger.

## Protection, issue and PRs

- **No branch protection on `main`**: `gh api …/branches/main/protection` →
  HTTP 404, no rulesets. Seven consecutive failing pushes reached main.
- **Issue #14 open**: automated dataset refresh/deployment failure with **11
  failed data runs**, all dying in "Collect and ingest" on
  `requests.exceptions.ConnectTimeout` to `www.cdep.ro`, stable across five
  days (G-P0-04).
- **Open PRs: 9** — 8 dependabot, 1 deploy-sync, ages 1–6 days. PRs #29, #9,
  #6 have failing CI checks yet remain mergeable, demonstrating the missing
  enforcement.
- **Release tag match**: latest release `data-20261117-T213500` matches the
  local pin; at the tag itself the pin read an earlier superseded tag, updated
  after publication (R10).

## Required deploy order

Deploy the **backend first**, then the **frontend**:

1. Push the branch, open a PR and get CI green on main; enable required checks.
2. Deploy the backend so canonical routes and `meta` exist and the live
   OpenAPI drops the double-prefixed aliases.
3. Deploy the frontend so the bundle uses single-prefix `/api` paths.
4. Verify live `/api/analytics/ideology` returns 200 and both bundle hashes
   match local HEAD.

Deploying the frontend first would keep sending requests to routes the old
backend does not serve. Deployment ordering itself is NOT PROVEN from the
read-only probe — see [CONTRADICTIONS](CONTRADICTIONS.md).
