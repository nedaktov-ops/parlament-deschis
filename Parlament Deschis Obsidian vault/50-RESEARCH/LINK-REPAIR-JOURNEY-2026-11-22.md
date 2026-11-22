---
id: LINK-REPAIR-JOURNEY
type: research
title: "Link and button repair — journey log (2026-11-22)"
description: "Running record of the repair programme: wave entry state, backups, checkpoint SHAs, gate output, supervisor verdicts and vault write-backs for each wave."
status: in-progress
authority: canonical
tags: [type/research, lifecycle/active, domain/frontend]
source_paths: [frontend/src, scripts, .github/workflows/ci.yml]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Link and button repair — journey log

Strategy: [LINK-REPAIR-STRATEGY](../20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md) ·
Recipes: [LINK-REPAIR-RECIPES](../20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md) ·
Supervision: [LINK-REPAIR-SUPERVISION](../20-DIRECTION/LINK-REPAIR-SUPERVISION-2026-11-22.md) ·
Investigation: [CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md).

**Programme state: STRATEGY + RECIPES COMPLETE; W0 NOT STARTED.**

## Phase S — strategy design (this phase)

Grounded at HEAD `8811216`, `origin/main` identical, product tree clean, with the
investigation vault notes uncommitted (exact paths enumerated at run time by
L-00; an early draft of this note said "11", which was an unproven count).
Gates and CI were read from
`frontend/package.json:6-12` and `.github/workflows/ci.yml:17-154`. A live
`curl -L` probe upgraded one investigation item: `https://github.com/parlament-deschis`
returns HTTP 404 while `https://github.com/nedaktov-ops/parlament-deschis`
returns HTTP 200, so the `About.tsx:6` literal is BROKEN, not merely inconsistent.

Authored in the vault before any repair action:

- [LINK-REPAIR-STRATEGY](../20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md) — principles, scope, eight waves, backup/rollback, gates, supervisor contract, GitHub policy.
- [LINK-REPAIR-RECIPES](../20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md) — 18 bespoke recipes L-00…L-17 with exclusive file lists, exact anchors, checkpoints and rollbacks.
- This journey note — one section added per wave as it runs.

**Gate S:** `python3 scripts/vault_lint.py`, `python3 scripts/vault_sync.py --check`,
`bash scripts/check-doc-truth.sh` and `git diff --check` were run after authoring;
output recorded in the final session report.

### Supervisor audit and corrections (same phase)

The [supervisor protocol](../20-DIRECTION/LINK-REPAIR-SUPERVISION-2026-11-22.md)
audited the draft strategy and recipes and produced 16 findings (S-01…S-16).
Before W0, the lead accepted and applied every blocking correction:

| Finding | Correction applied |
|---|---|
| S-01 (two owners of `LiveDashboard.tsx` in W2) | L-04 and L-05 are one agent, one checkpoint; the wave table names one owner |
| S-02 (i18n.ts multi-owner) | Single i18n owner per wave: W2 L-03, W3 L-07 (all three keys), W4 L-13 (all three keys), W5 none; published in strategy §4.1 |
| S-03 (L-02 delete-keys branch) | Branch deleted; L-02 always renders the link, L-15 keeps the keys |
| S-05 (W3 lacks `LiveDashboard.tsx`) | Added explicitly with L-09 as sole W3 owner |
| S-06 (placeholder file lists) | W4/W5 files enumerated by full repo-relative path in strategy §4 and recipes L-14/L-15 |
| S-07 (broken i18n gate path) | All checkpoints use `cd …/frontend && npm run i18n:check` |
| S-08 ("11 notes" count) | L-00 enumerates exact paths at run time and decides disposition of modified `START-HERE.md` |
| S-09 (`git branch -D`) | `git branch -d` first; `-D` only under verified-bundle conditions |
| S-12 (evidence separation) | Every wave note requires titled **Code evidence** / **Browser evidence** sections |
| S-13 (L-16 anchor pattern) | Third pattern `href="/…"` added, with pre/post count and exit-code contract |
| S-14 (ellipses in commands) | Fully expanded absolute paths required; L-00 checkpoint rewritten |
| S-15 (`wave.start_date` unguarded) | Changed to `wave?.start_date ?? clamped` |
| S-04, S-10, S-11, S-16 | Accepted as written / ADEQUATE; retained |

The four ownership contradictions S-01/S-02/S-05/S-06 are resolved in the
corrected register at strategy §4.1. No code file has been edited in this phase.

## Wave W0 — safety baseline

_Entry: branch, HEAD, backup manifest path, bundle verify result._
_Exit: gate result, supervisor verdict, integration SHA._

## Wave W1 — confirmed BROKEN fixes

_Recipes L-01, L-02. Entry/exit, checkpoint SHAs, gate output, browser result, verdict._

## Wave W2 — navigation and scope integrity

_Recipes L-03…L-06._

## Wave W3 — honest controls

_Recipes L-07…L-11._

## Wave W4 — accessibility, labels, URLs

_Recipes L-12…L-14._

## Wave W5 — dead controls

_Recipe L-15._

## Wave W6 — regression guards

_Recipe L-16._

## Wave W7 — integration and owner hand-off

_Recipe L-17. No merge to main and no deploy without explicit owner decision._

## See also

[CLICK-INVESTIGATION-JOURNEY](CLICK-INVESTIGATION-JOURNEY-2026-11-22.md) ·
[START-HERE](../00-START/START-HERE.md)
