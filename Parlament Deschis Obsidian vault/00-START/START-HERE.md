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
- **NEXT →** [TASK-REGISTER](../20-DIRECTION/TASK-REGISTER.md)

## Done (verified)

Local gates are green at HEAD `96e6fdd`: pytest 384 passed, ruff clean, lint 0 errors, build exit 0, strict audit 275 known / 0 new, doc-truth 0, and UI validation 24/24 locally with zero JavaScript errors and zero axe findings. Against the live API proxy the UI gate is 23/24 because the ideology endpoint 404s in production. Fixes F1–F11 are implemented and verified in the repository. See [RELEASE-AND-VERIFICATION](../10-STATE/RELEASE-AND-VERIFICATION.md) for the evidence trail.

Published dataset: `data-20261117-T213500` — 3,388 persons, 7,349 prepared memberships (7,358 raw release asset), 1,217 group switches plus 785 party switches = 2,002 total switch events, 142 waves, and committee counts of 26 orgs / 23 active / 9 chairs.

## In progress / local-only

Branch `review/completion-20261121` was pushed and PR [#48](https://github.com/nedaktov-ops/parlament-deschis/pull/48) is OPEN with all four required checks SUCCESS (`test`, `audit`, `docker`, `evidence-guards`). Local HEAD `f7a2325` is 14 commits ahead of `origin/main` (`6b848f1`). `main` is still RED and unprotected because the PR has not been merged, and nothing has been deployed — the local green is not the production state. Full detail: [GIT-POSITION](../10-STATE/GIT-POSITION.md) and [ACTION-LOG](../10-STATE/ACTION-LOG.md).

## Not done / blocked

Production has **no vote data** (live `/api/votes` reports total 0; the published corpus has no vote tables). The verified fixes have not been deployed — Vercel/Render still serve the pre-fix build, so there is a deploy lag. Issue #14 is open with 11 failed data runs from `cdep.ro` timeouts. Party genealogy has 0 links, Senate historical profile ingest is deferred, and the blog/donations plan has not started. See [GAP-REGISTER](../10-STATE/GAP-REGISTER.md).

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
- **10-STATE** — [ACTION-LOG](../10-STATE/ACTION-LOG.md), [CURRENT-STATE](../10-STATE/CURRENT-STATE.md)
- **20-DIRECTION** — [CONTINUATION-STRATEGY](../20-DIRECTION/CONTINUATION-STRATEGY.md), [TASK-REGISTER](../20-DIRECTION/TASK-REGISTER.md), [VISION](../20-DIRECTION/VISION.md)
- **30-SYSTEM** — [ARCHITECTURE](../30-SYSTEM/ARCHITECTURE.md)
- **40-FRONTEND** — [DESIGN-CONTRACT](../40-FRONTEND/DESIGN-CONTRACT.md)
- **50-RESEARCH** — [RESEARCH-LOG](../50-RESEARCH/RESEARCH-LOG.md)
- **60-EVIDENCE** — [AUDIT-2026-11-21](../60-EVIDENCE/AUDIT-2026-11-21.md)
- **70-ARCHIVE** — [STRATEGY-BLUEPRINTS-HISTORICAL](../70-ARCHIVE/STRATEGY-BLUEPRINTS-HISTORICAL.md)

## Freshness & NOT PROVEN

`as_of` **2026-11-21**, source commit `96e6fdd`. Local green does **not** mean production green. The exact Vercel build commit is unknown (strongly inferred as `6b848f1`), and client-side rendering of SPA routes is unknown (SPA fallback is proven, route rendering is not). See [RESEARCH-LOG](../50-RESEARCH/RESEARCH-LOG.md).
