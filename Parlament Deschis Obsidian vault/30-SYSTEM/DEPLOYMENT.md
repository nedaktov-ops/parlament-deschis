---
id: DEPLOYMENT
type: runbook
title: "Deployment — Vercel SPA, Render API, CI gates and rollback"
description: "Runbook for the deploy control plane: GitHub main, Vercel rewrite, Render Docker with pinned dataset, CI/deploy-verify workflows, verification gates, known gaps and non-destructive rollback."
status: active
authority: mirror
tags: [type/runbook, lifecycle/active, domain/ops]
source_paths: [docs/DEPLOYMENT.md, render.yaml, vercel.json, .github/workflows/ci.yml, .github/workflows/deploy-verify.yml]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Deployment

GitHub `main` is the only deploy control plane; a laptop deploy is break-glass only. The API is read-only in production (`PARLAMENT_POLL_INTERVAL_MIN` empty): no background polling and no keep-alive traffic.

State context: [RELEASE-AND-VERIFICATION](../10-STATE/RELEASE-AND-VERIFICATION.md). Release construction: [DATA-RELEASE-PROCEDURE](DATA-RELEASE-PROCEDURE.md).

## Topology

| Layer | Platform | Serves |
| --- | --- | --- |
| Frontend | Vercel | Static SPA built from `frontend/dist`; `/api/*` rewritten to the Render API |
| API | Render | Docker image from `Dockerfile`, SQLite corpus pinned by `data/latest-release.txt` |
| Data | GitHub Actions | Scheduled/manual rebuild, strict audit, GitHub release, release-marker push |

## Deploy sequence

1. PR → CI runs **four jobs** (`test`, `audit`, `docker`, `evidence-guards`); Vercel publishes a preview. (Older docs list three jobs — stale.)
2. Merge to `main`; CI runs again on the merge commit. `ci.yml` is configured with `push: branches: [main]` — the filter exists; a claim of a bare `push:` is false.
3. Vercel builds and deploys on every deploy. `vercel.json` has **no `ignoreCommand` key** at this commit (the documented `"ignoreCommand": ""` was removed), so there is no path-based build skipping to rely on.
4. `render.yaml` declares `branch: main` and `autoDeployTrigger: checksPass`. **With zero detected checks Render does not deploy**, which is why CI must run on every push to `main`.
5. `Deploy verify` runs on a `workflow_run` trigger after CI succeeds on `main` (or via `workflow_dispatch`). It waits for the matching Render deploy, then checks the SPA shell, `/api/health` through the Vercel rewrite with the pinned `dataset.release_tag`, Render's health/live/ready endpoints, non-zero persons and memberships, and valid `/api/coverage` and `/api/traseism/overview` JSON.
6. The daily `Data` workflow is fail-closed: no new corpus is published unless collection and the strict audit pass. It updates `data/latest-release.txt`, triggers Render **explicitly through its API**, and waits up to 30 minutes for the new tag. Its marker push uses `GITHUB_TOKEN` and therefore starts **neither CI nor Render's Git deployment**, so it does not itself trigger `Deploy verify`.

## Verification gates

Before a PR, the local gate is `uv sync --extra dev --locked`, `ruff check`, `pytest -q` (384 passed at this commit), the frontend `npm ci && npm run build`, and the **strict corpus audit** with baseline (`--strict --baseline data/reference/corpus-audit-baseline.json`) — currently **275 known / 0 new** findings. A red strict audit blocks publication and keeps the previous release live.

Manual, read-only probes: `Platform status` (`gh workflow run platform-status.yml --ref main`) prints rollback IDs and probes public endpoints without changing state. `Deploy verify` asserts a specific commit, so after a rollback use Platform status and public health checks instead.

## Rollback (non-destructive)

Roll back with `git revert` of the release-pin commit or a platform rollback to a known deployment UID (`dpl_…` on Vercel, `dep_…` on Render); platform rollback is manual, `main`-only, defaults to dry run, and requires `confirm=ROLLBACK` to execute. **Never use `git reset --hard` or force push** to roll back. A Render rollback does not disable auto-deploy — disable it in the dashboard first if production must stay frozen.

## Known gaps and caveats

- **Free-tier cold starts:** a Render service spins down after ~15 minutes idle; the first request can take 30–60 s (verification allows minutes).
- **No branch protection on `main`** at this commit, and the "keep main protected and require test/audit/docker" line in the source doc is an unmet requirement, not a current fact.
- The deployed CSP header is byte-equal across hosts but is **`Content-Security-Policy-Report-Only`** — reporting, not enforcing; HSTS is Vercel-only.
- Issue **#14** is open: 11 failed data runs from `cdep.ro` `ConnectTimeout` (including `leg=1990`), so automated refresh has not published a new release.
- Whether `autoDeployTrigger: checksPass` is applied depends on the Render service being Blueprint-managed; confirm with Platform status. Deploy verify also fails until a Render deploy exists for the asserted commit.
