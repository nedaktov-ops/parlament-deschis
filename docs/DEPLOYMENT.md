# Deployment

GitHub `main` is the only deploy control plane. Vercel and Render deploy from
pushes to `main`; a laptop deploy is break-glass only. This page describes the
gates, the verification, and the rollback path.

## Topology

| Layer | Platform | What it serves |
|---|---|---|
| Frontend | Vercel | Static SPA built from `frontend/dist`; `/api/*` is rewritten to Render |
| API | Render | Docker image from `Dockerfile`; SQLite corpus pinned by `data/latest-release.txt` |
| Data | GitHub Actions | Daily rebuild, strict audit, GitHub release, release-marker push |

The API is read-only in production: `PARLAMENT_POLL_INTERVAL_MIN` is empty, so
there is no background polling and no keep-alive traffic. A free Render service
spins down after 15 minutes without inbound traffic; the first request can take
30–60 seconds. That is accepted. Upgrade the Render plan if the cold start is
not acceptable.

## Required GitHub configuration

Repository **Settings → Secrets and variables → Actions**:

| Name | Kind | Purpose |
|---|---|---|
| `VERCEL_TOKEN` | Secret | Read deployments, roll back |
| `RENDER_API_KEY` | Secret | Read deploys, roll back |
| `VERCEL_PROJECT_ID` | Variable | `prj_…` |
| `RENDER_SERVICE_ID` | Variable | `srv-…` |
| `VERCEL_TEAM_ID` | Variable (optional) | Only when the project belongs to a team |

IDs are identifiers, not credentials. Tokens are account/workspace-wide, so
they live only in GitHub and are never printed by the workflows.

Verify the names (values are write-only):

```bash
gh secret list   -R nedaktov-ops/parlament-deschis
gh variable list -R nedaktov-ops/parlament-deschis
```

## Deploy sequence

1. Open a PR. CI runs `test`, `audit`, and `docker`; Vercel publishes a preview.
2. Merge to `main`.
3. CI runs again on the merge commit.
4. Vercel builds only when `frontend/**` or `vercel.json` changed.
5. Render waits for GitHub checks, then deploys when they pass.
6. `Deploy verify` runs after CI succeeds on `main` and proves the result
   against the public contract.
7. The daily `Data` workflow validates a new corpus, publishes a release,
   updates `data/latest-release.txt`, and waits up to 30 minutes for Render to
   serve the new tag. Its marker push triggers CI, which triggers
   `Deploy verify`.

### Vercel build skipping

`vercel.json` contains:

```json
"ignoreCommand": "git rev-parse HEAD^ >/dev/null 2>&1 && git diff --quiet HEAD^ HEAD -- frontend vercel.json"
```

Exit `0` skips the build; exit `1` builds. A backend-only or docs-only push
therefore leaves the last good frontend deployment serving. The stable domain
still returns the SPA, and `Deploy verify` accepts a skipped build.

### Render deploy gating

`render.yaml` declares:

```yaml
branch: main
autoDeployTrigger: checksPass
```

Render deploys `main` only after the GitHub checks pass. **If Render detects
zero checks, it does not deploy**, so CI must run on every push to `main`.
`CI` is configured for `push: branches: [main]`.

Blueprint changes apply when Render syncs `render.yaml`. If the service was
created outside the Blueprint, apply the same settings in the Render dashboard
and confirm with the `Platform status` workflow (`trigger=checksPass`).

### Data releases are fail-closed

`Data` publishes nothing unless collection and the strict corpus audit pass.
If a source is unreachable, the job fails, opens or updates an issue, and the
live service keeps serving the previous release. That is intentional.

## Verification

### Platform status (manual, read-only)

Dispatched from `main`. It reads the Vercel production deployments and the
Render service/deploys, prints rollback IDs, and probes the public endpoints.
It never changes platform state.

```bash
gh workflow run platform-status.yml \
  -R nedaktov-ops/parlament-deschis --ref main
```

### Deploy verify (automatic)

Triggered by `CI` completing successfully on `main`. It waits for the Render
deploy matching the commit to become live, tolerates an intentionally skipped
Vercel build, then checks:

- `/` returns the SPA shell;
- `/api/health` through the Vercel rewrite exposes the pinned release;
- Render `/api/health`, `/api/health/live`, `/api/health/ready` are healthy;
- `persons` and `memberships` are non-zero;
- `dataset.release_tag` equals `data/latest-release.txt`;
- `/api/coverage` and `/api/traseism/overview` return valid JSON.

Run it manually for the current `main`:

```bash
gh workflow run deploy-verify.yml \
  -R nedaktov-ops/parlament-deschis --ref main
```

The same checks locally:

```bash
TARGET_SHA="$(git rev-parse HEAD)" \
EXPECTED_RELEASE="$(tr -d '[:space:]' < data/latest-release.txt)" \
VERCEL_PROJECT_ID="prj_…" VERCEL_TOKEN="…" \
RENDER_SERVICE_ID="srv-…" RENDER_API_KEY="…" \
scripts/verify-deploy.sh
```

Do not put those tokens in shell history on a shared machine. Prefer the
workflow. `Deploy verify` asserts a specific commit, so after a rollback use
`Platform status` and the public health checks instead.

### Local gate before a PR

```bash
uv sync --extra dev --locked
uv run ruff check pipeline backend scripts tests
uv run pytest -q
(cd frontend && npm ci && npm run build)
uv run python -m pipeline.cli --db data/parlament.db audit-corpus \
  --strict --baseline data/reference/corpus-audit-baseline.json
```

## Rollback

`Platform rollback` is manual, restricted to `main`, and defaults to a dry run.
It resolves the target and prints it without changing production.

```bash
# 1. Dry run: prove the target exists.
gh workflow run platform-rollback.yml \
  -R nedaktov-ops/parlament-deschis --ref main \
  -f platform=vercel -f target=dpl_… -f dry_run=true

# 2. Execute: requires the literal confirmation.
gh workflow run platform-rollback.yml \
  -R nedaktov-ops/parlament-deschis --ref main \
  -f platform=vercel -f target=dpl_… -f dry_run=false -f confirm=ROLLBACK
```

Use the deployment UID printed by `Platform status` for Vercel, or the
`dep_…` ID for Render.

- **Vercel:** `POST /v1/projects/{projectId}/rollback/{deploymentId}`. On the
  Hobby plan you can roll back only to the immediately previous production
  deployment. Rollback is a routing change and takes effect quickly.
- **Render:** `POST /v1/services/{serviceId}/rollback` with `deployId`. A
  Render rollback does **not** disable auto-deploy; a later push can redeploy
  over it. If production must stay frozen, disable auto-deploy in the Render
  dashboard first, then re-enable it after the fix.

Break-glass: the Vercel and Render dashboards can perform the same rollback.
Use the workflow first so the action is logged in GitHub.

## Security and rotation

- Tokens exist only as GitHub Actions secrets. Never commit them, paste them
  into an issue, or echo them in a workflow.
- Rotate `VERCEL_TOKEN` before its expiry (90 days is a reasonable maximum).
  Render API keys do not expire: rotate on a 90-day calendar reminder, or
  immediately if a laptop or CI log is exposed.
- Rotating: create the new value, update the GitHub secret, run
  `Platform status` to prove it, then revoke the old value.
- Keep `main` protected and require `test`, `audit`, and `docker`. Do not use
  `pull_request_target` with these secrets.
- Audit: Vercel Activity, Render Audit Log, and the GitHub Actions run history.

## Known gaps

- `autoDeployTrigger: checksPass` is declared in `render.yaml`; whether it is
  applied depends on the service being Blueprint-managed. Confirm with
  `Platform status`.
- `ignoreCommand` applies to Git deployments, not to `vercel deploy` from a
  laptop.
- `Deploy verify` requires a Render deploy for the commit. If Render auto-deploy
  is set to `off`, verification fails until a deploy is triggered manually.
- Free-tier cold starts make verification take minutes; the workflow allows 45.
