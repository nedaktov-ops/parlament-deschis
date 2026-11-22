---
id: FRONTEND-REPAIR-STRATEGY
type: runbook
title: "Front-end repair strategy and recipe index (2026-11-21)"
description: "Master strategy for repairing the 23-page front end: nine implementation-ready recipes, wave plan, ownership arbitration, gates, backups and rollbacks. Strategy only — no repairs implemented yet."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/frontend]
source_paths:
  - docs/repair-recipes
  - docs/CONTINUATION-STRATEGY-2026-11-21.md
created: 2026-11-21
updated: 2026-11-22
source_commit: aca0ec9
---

# Front-end repair strategy — master index

**Status: W0–W4 COMPLETE — Wave W5 (owner merge/protect/deploy) is the current open step.** Nine
strategy agents produced 9,179 lines of implementation-ready recipes in
`docs/repair-recipes/`. This note indexes them, fixes cross-recipe ownership
conflicts, and defines the wave/gate envelope. All diagnoses come from the
[TRIAD-AUDIT](../40-FRONTEND/TRIAD-AUDIT-2026-11-21.md) and
[FRONTEND-AUDIT](../40-FRONTEND/FRONTEND-AUDIT-2026-11-21.md). Baseline product
tree is byte-identical at `eb693b4` and the authoring HEAD; later waves landed
on top of the integration HEAD `618849a` then `repair/w0-safety` checkpoints.

## 1. Recipe index

| ID | Recipe | Lines | Scope | Depends on |
|---|---|---:|---|---|
| R-01 | `R-01-design-system.md` | 1,134 | HeroGraphic colours, DataBar, ProgressRing, AgeDistributionRadial, semantic CSS utilities | — |
| R-02 | `R-02-layout.md` | 933 | single container owner, hero template, page-title/moment-value scale, table/card canon | R-01 (utilities) |
| R-03 | `R-03-scope.md` | 922 | `useScope()` hook, date/chamber/legislature from URL, 2 additive backend scope params, 23-page migration | — |
| R-04 | `R-04-counts.md` | 1,638 | canonical switch definitions (1,217 / 785 / 2,002), API aggregates, no null→0, denominator fixes | R-03 (scope keys) |
| R-05 | `R-05-states.md` | 998 | `resolveViewState()`, AsyncState, 23-page state migration, retry, i18n keys | R-01 (surfaces) |
| R-06 | `R-06-tactile.md` | 630 | native controls, keyboard scroll, 44px targets, RetryButton, tooltips, reduced-motion, dialogs, About wiring | R-05 (state), R-07 (i18n) |
| R-07 | `R-07-provenance-i18n-nav.md` | 1,186 | ProvenanceStamp, 132 i18n insertions + key-diff gate, 6 orphan routes, dead-component decisions | — |
| R-08 | `R-08-feature-honesty.md` | 739 | coalition proxy, Bureau gap, Ideology, Senate HOLD, Report/Coverage/Legislature, vote scope/pagination | R-03, R-04 |
| R-09 | `R-09-verification-rollout.md` | 999 | wave plan, G00–G16 gates, backups, PR protocol, browser/axe/i18n/contract checks, rollback | all |

Every recipe contains: objective, path:line evidence, exclusive file list,
preconditions, numbered implementation steps with exact code/commands,
checkpoints (command + expected output + exit code), backup + SHA-256 manifest,
`git revert` rollback, verification gates, acceptance criteria, dependencies,
side-quest policy and NOT PROVEN register. No recipe touches data files, the
release pin, workflows, branch protection or GitHub state.

## 2. Ownership arbitration (resolves R-09 coordination findings)

| Conflict | Decision |
|---|---|
| CO-1: CSS utilities owned by both R-01 and R-02 | **R-01 owns all `index.css` utility definitions** (`.surface`, `.page-title`, `.moment-value`, `.badge`, `.stat`, `.data-table`, token companions); R-02 owns only *call-site* class replacements in page files and may not edit `index.css`. |
| CO-2: AP-7 canvas palette had no owner | **R-01 owns canvas palette tokens** in CSS vars; **R-08 owns the per-chart call-site replacements** (Ideology, TimelineChart, PartyAgreementMatrix, ECharts options). |
| CO-3: `Grafice.tsx` / `Topuri.tsx` appear in R-01 (DataBar colour) and R-08 (scope/pagination) | **R-01 owns their visual primitive usage** (`DataBar` colour/tone) and the shared `DataBar` API; **R-08 owns their query keys, scope controls, pagination and copy**. Sequential waves, never concurrent. |
| CO-4: recipe inventory incomplete at authoring time | Resolved — all R-01…R-09 present and verified above. |

## 3. Wave plan (from R-09, adapted)

| Wave | Recipes | Goal | Gate |
|---|---|---|---|
| W0 | R-09 | Safety: backup bundle, checksum manifest, restore drill, branch/PR protocol | G00–G02 GREEN |
| W1 | R-01 → R-02 | Visual foundation: working primitives, one container, one type scale | lint/build + Tailwind emission + UI 24/24 + 320px probe |
| W2 | R-03 → R-04, R-05 | Scope + honest numbers + honest states | pytest + API contract + i18n + state probe |
| W3 | R-08 | Feature honesty (coalition, Bureau, Ideology, Senate, Report, vote scope) | audit 275/0 + UI gate + targeted API probes |
| W4 | R-06, R-07 | Tactile semantics + provenance/i18n/nav | keyboard walk K1–K12 + key-diff 0 + axe 0 + route guard |
| W5 | owner | Merge/protect/deploy (🔒 owner-only) | production health + deploy-verify |

No wave starts until the previous gate is GREEN. AMBER = blocked on owner
decision; RED = stop, revert the wave checkpoint, do not proceed. An unrun
check is **NOT PROVEN**, never PASS.

## 4. Non-destructive execution contract

- One branch per wave; atomic checkpoint commit per step; no `git reset --hard`,
  no force-push, no tag moves, no data-file or release-pin edits.
- Backup before every wave: `git bundle create /tmp/opencode/backups/<wave>/pre.bundle --all`,
  DB checkpoint, vault copy, sealed SHA-256 manifest, restore drill.
- Required PR checks remain `test`, `audit`, `docker`, `evidence-guards` with
  1 approval and no force-push/deletion (current protection verified intact).
- Each commit message states: recipe ID, evidence, gate output, rollback SHA.
- Vault mirror maintained after every change: `vault_sync.py` → `vault_lint.py`
  → `check-doc-truth.sh`, committed with the code change.

## 5. Current verification and gaps

Local gates as of 2026-11-22 (Waves W0–W4 executed): doc-truth **false-claims: 0**,
vault lint clean, `vault_sync --check` clean, `git diff --check` clean. Waves W0
(R-09 safety), W2 (R-03/R-04/R-05), W3 (R-08 honesty), and **W4 (R-06 tactile → R-07 provenance/i18n/nav)** completed with every blocking gate green; W1
(R-01/R-02) AMBER with two pre-existing residuals tracked (stale probe UUID, `/grafice` overflow → R-08 owner).

**NOT PROVEN across all recipes:** touch/reduced-motion runtime emulation (K9
runtime probe pending — TimeSlider not mounted on any route), print/PDF, live API
payloads and production parity. `/tmp/axe.min.js` restored (axe-core 4.10.2); UI
gate re-verified green on fresh dev servers after the stale-HMR diagnosis. These
are recorded as named preconditions/gaps, not claimed as green.

## 6. Next decision

**Current next step:** W5 owner rollout (merge `repair/w0-safety` → `main`, confirm branch protection, deploy, run `verify-deploy.sh` — 🔒 owner-only). The next step
after that is the explicit owner decision to begin Wave W0/W1 with one
recipe-owned agent per step (implementer fleet), following
[ACTION-PLAN](ACTION-PLAN.md) and the R-09 gate envelope. Until then this note
must not be read as a repair-completion claim.

## See also

[ACTION-PLAN](ACTION-PLAN.md) · [NEXT-ACTIONS](../10-STATE/NEXT-ACTIONS.md) · [TRIAD-AUDIT](../40-FRONTEND/TRIAD-AUDIT-2026-11-21.md) · [FRONTEND-AUDIT](../40-FRONTEND/FRONTEND-AUDIT-2026-11-21.md) · [RESEARCH-FLEET](../50-RESEARCH/RESEARCH-FLEET-2026-11-21.md)
