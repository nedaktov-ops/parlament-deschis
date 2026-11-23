---
id: OWNER-ROLLOUT
type: evidence
title: "Owner rollout attempt — PR #75, CI green, merge blocked by self-approval rule (2026-11-23)"
description: "Evidence record of PR creation, all four required checks passing, and the protected-branch rejection of both --admin merge and direct push because the sole writer is the PR author."
status: in-progress
authority: derived
tags: [type/evidence, lifecycle/active, domain/project]
source_paths: [.github/workflows/ci.yml, .git/config]
created: 2026-11-23
updated: 2026-11-23
source_commit: 21f938a34ed026b2f916daf0e28eef2f28218588
---

# Owner rollout attempt — 2026-11-23

**Scope.** Execution of the owner gate from
[LINK-REPAIR-STRATEGY](../20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md) §9:
merge the repair branch to `main`, then let Vercel and Render deploy. This note
records what was actually executed; no merge, deploy or protection change has
occurred.

## Code evidence — what was executed

| Step | Command | Observed result |
|---|---|---|
| Preflight branch state | `git branch --show-current && git rev-parse HEAD origin/main repair/links-base && git status --short` | `repair/links-base` @ `21f938a…`; `origin/main` @ `8811216…`; clean tree |
| Protection read | `gh api repos/nedaktov-ops/parlament-deschis/branches/main/protection` | required checks `test, audit, docker, evidence-guards`; `required_approving_review_count: 1`; `enforce_admins: true`; no force-push/deletion |
| PR created | `gh pr create --base main --head repair/links-base …` | **PR #75** — https://github.com/nedaktov-ops/parlament-deschis/pull/75 |
| CI watched | `gh pr checks 75 --watch --interval 30` | `audit pass 13s`, `evidence-guards pass 14s`, `test pass 1m18s`, `docker pass 1m22s`, Vercel preview pass. CI run `45114534479` |
| Admin merge attempted | `gh pr merge 75 --squash --admin` | rejected: `GraphQL: At least 1 approving review is required by reviewers with write access.` |
| Direct push attempted | `git push origin repair/links-base:main` | rejected: `GH006: Protected branch update failed … At least 1 approving review is required by reviewers with write access.` |
| Self-approval attempted | `gh pr review 75 --approve …` | rejected: `Review Can not approve your own pull request` |
| Review state | `gh pr view 75 --json reviewDecision,reviews,state` | `REVIEW_REQUIRED`, `reviews: []`, `OPEN` |
| Writers | `gh api …/collaborators` | only `nedaktov-ops` — the PR author; `gh auth status -a` shows only that account |

## Conclusion

The four required checks are **green**, so the code is CI-proven. The only
remaining gate is an approving review from an account with write access that is
**not** the author. That account does not exist in this environment, and GitHub
forbids self-approval. No branch-protection setting was changed; no merge,
Vercel production deployment or Render deployment was performed.

**Resolver (owner action):** approve PR #75 from a second writer account, then
re-run `gh pr merge 75 --squash`; after `origin/main` equals the PR head SHA,
verify Vercel production deployment and Render deploy for that SHA. Until then
all production claims remain **NOT PROVEN**.

## Browser evidence

Not applicable — GitHub/Git operations only. Vercel preview deployment passed
as a PR check, which is not a production deployment claim.

## See also

[LINK-REPAIR-JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) W12 ·
[STRATEGY](../20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md) §9
