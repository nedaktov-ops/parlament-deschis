---
id: START-HERE
type: moc
title: "Parlament Deschis — agent entry point"
description: "The single first-read note: what is done, what is local-only, what is blocked, and the next actions for an LLM agent."
status: active
authority: canonical
tags: [type/moc, lifecycle/active, domain/project]
source_paths: [docs/CONTINUATION-STRATEGY-2026-11-21.md, docs/POST-INITIAL-AUDIT-2026-11-21.md, docs/GAP-ANALYSIS-2026-11-21.md, docs/AUDIT-RESOLUTIONS-2026-11-21.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 96e6fdd
---

# Parlament Deschis — agent entry point

> **Addendum (2026-11-21):** Re-anchored 2026-11-21 from `docs/CONTINUATION-STRATEGY-2026-11-21.md` §0. Vault mirror: [CONTINUATION-STRATEGY](../20-DIRECTION/CONTINUATION-STRATEGY.md).

Read this note first. It is the canonical, date-stamped snapshot of the project as of **2026-11-21** at local HEAD `96e6fdd`. Every claim below is qualified by scope: local repository, GitHub, or production (Vercel + Render). When in doubt, follow [MAINTENANCE-PROTOCOL](MAINTENANCE-PROTOCOL.md).

## 30-second answer

- **DONE →** [CURRENT-STATE](../10-STATE/CURRENT-STATE.md)
- **IN PROGRESS →** [GIT-POSITION](../10-STATE/GIT-POSITION.md)
- **NOT DONE →** [GAP-REGISTER](../10-STATE/GAP-REGISTER.md)
- **NEXT →** [NEXT-ACTIONS](../10-STATE/NEXT-ACTIONS.md) (ranked actions, completed tasks)
- **FULL REGISTER →** [TASK-REGISTER](../20-DIRECTION/TASK-REGISTER.md)
- **EXECUTED OWNER GATES →** [EXECUTION-LOG](../10-STATE/EXECUTION-LOG-2026-11-21.md)

## Done (verified)

Local gates are green at HEAD `96e6fdd`: pytest 384 passed, ruff clean, lint 0 errors, build exit 0, strict audit 275 known / 0 new, doc-truth 0, and UI validation 24/24 locally with zero JavaScript errors and zero axe findings. Against the live API proxy the UI gate is 23/24 because the ideology endpoint 404s in production. Fixes F1–F11 are implemented and verified in the repository. See [RELEASE-AND-VERIFICATION](../10-STATE/RELEASE-AND-VERIFICATION.md) for the evidence trail.

Published dataset: `data-20261117-T213500` — 3,388 persons, 7,349 prepared memberships (7,358 raw release asset), 1,217 group switches plus 785 party switches = 2,002 total switch events, 142 waves, and committee counts of 26 orgs / 23 active / 9 chairs.

## In progress / local-only

PR #48, #47, #8, #49, #50 and #51 were merged into `main` (now `ad34bde`), all four required checks green on each; branch protection is active with four required checks, one approval, no force-push/deletion. Backend and frontend were deployed; production serves release `data-20261121-votes-001` with 189 live votes and an enforcing CSP. Local green is now production green. There are **no open PRs**. Full evidence: [EXECUTION-LOG](../10-STATE/EXECUTION-LOG-2026-11-21.md) and [GIT-POSITION](../10-STATE/GIT-POSITION.md).

## Not done / blocked

Issue #14 remains open (11 historic failed data runs from `cdep.ro` timeouts; the retry/offline fallback is deployed but a green scheduled run has not yet been observed). Party genealogy has 0 links, Senate historical profile ingest is deferred, H3-D/H4-A frontend polish and the staging load test remain. Blog/donations was formally dropped from active scope (P-3). See [GAP-REGISTER](../10-STATE/GAP-REGISTER.md) and [EXECUTION-LOG](../10-STATE/EXECUTION-LOG-2026-11-21.md).

## How to move forward

1. **Owner:** merge the already-green PR #48, then enable branch protection with the four required checks.
2. **Owner:** deploy the backend first (canonical routes and universal `meta`), then the frontend (single-prefix API paths).
3. **Agent:** start the `cdep.ro` retry/cache/offline fix on a branch now — external lead time is the critical path to any data release.
4. **Agent:** seed the licence register and per-dimension coverage, then publish a release containing vote data (owner triggers the release/deploy).
5. **Agent:** label 1,217 group / 785 party / 2,002 total switches and 7,358 raw / 7,349 prepared memberships.
6. **Owner + agent:** record policy decisions (60 s poll, CSP enforcement, blog/donations), then close the vision gaps in dependency order.

The completed-action evidence and the full ranked list are in [ACTION-LOG](../10-STATE/ACTION-LOG.md).

For the ordered five-agent continuation plan, gates and session boundary, see [CONTINUATION-STRATEGY](../20-DIRECTION/CONTINUATION-STRATEGY.md).

## Authority order

1. Executable evidence (source, DB queries, API responses, CI/CLI output, generated artifacts) beats prose.
2. Scope before conflict — decide whether two claims describe the same artifact before calling a defect.
3. Newer wins on the same topic, unless a source is explicitly labelled historical.
4. An addendum or dated current-state banner beats the base body of the same file.
5. Generated artifacts derive from source — never hand-edit generated files such as `openapi.json` or `_generated/*`.
6. No guessing — report NOT PROVEN and name the resolver.

Enforced by [MAINTENANCE-PROTOCOL](MAINTENANCE-PROTOCOL.md) and the machine contract in [AGENTS](AGENTS.md).

## Note index

- **00-START** — [START-HERE](START-HERE.md) (this note)
- **10-STATE** — [NEXT-ACTIONS](../10-STATE/NEXT-ACTIONS.md), [EXECUTION-LOG](../10-STATE/EXECUTION-LOG-2026-11-21.md), [ACTION-LOG](../10-STATE/ACTION-LOG.md), [CURRENT-STATE](../10-STATE/CURRENT-STATE.md)
- **20-DIRECTION** — [FRONTEND-REPAIR-STRATEGY](../20-DIRECTION/FRONTEND-REPAIR-STRATEGY.md) (9 recipes, waves, gates; AMBER), [ACTION-PLAN](../20-DIRECTION/ACTION-PLAN.md), [CONTINUATION-STRATEGY](../20-DIRECTION/CONTINUATION-STRATEGY.md), [TASK-REGISTER](../20-DIRECTION/TASK-REGISTER.md), [VISION](../20-DIRECTION/VISION.md)
- **30-SYSTEM** — [ARCHITECTURE](../30-SYSTEM/ARCHITECTURE.md)
- **40-FRONTEND** — [TRIAD-AUDIT](../40-FRONTEND/TRIAD-AUDIT-2026-11-21.md) (appearance/tactile/functionality), [FRONTEND-AUDIT](../40-FRONTEND/FRONTEND-AUDIT-2026-11-21.md) (23-page audit), [DESIGN-CONTRACT](../40-FRONTEND/DESIGN-CONTRACT.md)
- **50-RESEARCH** — [RESEARCH-FLEET](../50-RESEARCH/RESEARCH-FLEET-2026-11-21.md) (missing-component research), [RESEARCH-LOG](../50-RESEARCH/RESEARCH-LOG.md)
- **60-EVIDENCE** — [AUDIT-2026-11-21](../60-EVIDENCE/AUDIT-2026-11-21.md)
- **70-ARCHIVE** — [STRATEGY-BLUEPRINTS-HISTORICAL](../70-ARCHIVE/STRATEGY-BLUEPRINTS-HISTORICAL.md)

## Freshness & NOT PROVEN

`as_of` **2026-11-21**. Local green is production green for the current checks: GitHub status ties Vercel deployment IDs to specific SHAs, and the live browser gate passes 24/24 with zero JavaScript errors and zero axe violations. Still NOT PROVEN: which SHA the live Vercel alias serves (needs a Vercel token), runtime read-only enforcement at the OS level, historic licence seeding, and the original research date. See [RESEARCH-FLEET](../50-RESEARCH/RESEARCH-FLEET-2026-11-21.md) and [RESEARCH-LOG](../50-RESEARCH/RESEARCH-LOG.md).
