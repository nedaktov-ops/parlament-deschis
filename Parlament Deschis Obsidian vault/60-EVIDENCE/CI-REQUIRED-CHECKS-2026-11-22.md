---
id: CI-REQUIRED-CHECKS
type: evidence
title: "Required CI checks for repair/links-base — 2026-11-22 (NOT PROVEN)"
description: "GitHub CLI query for CI runs on the pushed repair branch: no runs exist for repair/links-base, so pytest/audit/docker/evidence-guards remain NOT PROVEN with the owner-PR resolver."
status: active
authority: derived
tags: [type/evidence, lifecycle/active, domain/project]
source_paths: [.github/workflows/ci.yml, 20-DIRECTION/LINK-FOLLOWUP-WAVE-PLAN-2026-11-22.md]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Required CI checks for `repair/links-base`

**Scope.** Wave W10, recipe L-21, closes follow-up F6. Raw capture:
`/tmp/opencode/w10-ci-checks.txt`. Repo slug was derived from `git remote -v`
(`nedaktov-ops/parlament-deschis`), not guessed. No workflow, PR, merge or
deployment was changed.

## Code evidence

Required checks are `test`, `audit`, `docker`, `evidence-guards` in
`.github/workflows/ci.yml:17,59,80,111`. W7 of
[LINK-REPAIR-JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) recorded
them as **NOT RUN** locally with CI as resolver.

Query actually executed (repo root):
`gh run list --repo nedaktov-ops/parlament-deschis --branch repair/links-base --limit 20`
→ exit 0, **no output** — no workflow runs exist for that branch. A control query
without the branch filter returned recent successful `CI` runs on `main` and on
older branches/PRs (e.g. run `45049091799`, `CI`, `main`, push), which are for
**different commits** and are not evidence for this repair branch.

## Verdict

`test`, `audit`, `docker`, `evidence-guards` on `repair/links-base`: **NOT PROVEN**.
**Resolver:** owner opens a PR from `repair/links-base` → the four required CI
checks run → record each conclusion with its run ID and URL. No local frontend
gate is converted into a CI pass; no run ID is attributed to this branch.

## Browser evidence

N/A — GitHub CLI query, not a browser action.

## See also

[LINK-FOLLOWUP-WAVE-PLAN](../20-DIRECTION/LINK-FOLLOWUP-WAVE-PLAN-2026-11-22.md) §5 ·
[STRATEGY](../20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md) §9
