---
id: REPAIR-WAVE-OUTCOMES
type: state
title: "Front-end repair wave outcomes"
description: "Per-wave PASS/FAIL/AMBER decisions with raw gate evidence, backups, commits and next-step decisions during implementation of the nine repair recipes."
status: active
authority: canonical
tags: [type/state, lifecycle/active, domain/frontend]
source_paths:
  - docs/repair-recipes
created: 2026-11-21
updated: 2026-11-21
source_commit: 618849a
---

# Repair wave outcomes

Master record for the supervised implementation of
[FRONTEND-REPAIR-STRATEGY](../20-DIRECTION/FRONTEND-REPAIR-STRATEGY.md) and its
nine recipes. Rule: a wave is PASS only when every blocking gate printed a
green result; an unrun check is NOT PROVEN, never PASS.

## W0 — Safety / backups — **PASS**

| Item | Evidence |
|---|---|
| Baseline | branch `repair/w0-safety` from `origin/main` `618849a` |
| Backup | `/tmp/opencode/backups/W0/618849a/pre-w0.bundle`, `parlament-real.db` (43,589,632 B), `latest-release.txt`, vault copy |
| Manifest | `sha256sum -c MANIFEST.sha256` → `pre-w0.bundle: OK`, `parlament-real.db: OK`, `latest-release.txt: OK` |
| Restore drill | `git clone --no-local` → HEAD `618849a` (matches baseline) |
| Product tree | unchanged — backup + vault outcome note only |
| Blocking gates | G00–G02 GREEN |

**Decision:** PASS. Proceed to W1 (visual foundation: R-01 → R-02) only after the
supervisor plan confirms recipe file ownership and the axe prerequisite is
resolved.

## W1 — Visual foundation (R-01, R-02) — **PENDING**

## W2 — Scope + counts + states (R-03, R-04, R-05) — **PENDING**

## W3 — Feature honesty (R-08) — **PENDING**

## W4 — Tactile + provenance/i18n/nav (R-06, R-07) — **PENDING**

## W5 — Owner rollout (merge/protect/deploy) — **PENDING (owner-only)**

## Decision log

| Date | Wave | Decision | Rationale | Next step |
|---|---|---|---|---|
| 2026-11-21 | W0 | PASS | bundle/DB/manifest/restore all green | begin W1 after supervisor plan + axe check |
