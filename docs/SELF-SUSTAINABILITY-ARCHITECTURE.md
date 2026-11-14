# Free-Tier Self-Sustainability Architecture

## Purpose and promise

This document defines a practical path to operate Parlament Deschis with no
paid infrastructure and minimal routine human involvement. The target is
**hands-off during normal operation, observable when something fails, and able
to recover without discarding the last known-good data**.

This is not a promise of 100% uptime or fully autonomous recovery. The project
depends on official parliamentary websites, GitHub Actions, Render, and Vercel.
Any of them can be unavailable, delayed, rate-limited, or change their free
limits. Render explicitly positions its Free services for hobby projects and
testing, not production. A public service that requires an uptime commitment
will eventually need a paid hosting plan or a different reliability model.

## Current state and gaps

- The frontend is a static Vite application on Vercel. Its `/api/*` requests
  are rewritten to the Render API.
- Render runs a Docker service with an ephemeral filesystem. The SQLite
  database is baked into the image and the running API is read-only; this is
  appropriate for Render Free.
- `.github/workflows/data.yml` rebuilds the corpus daily, audits it, prepares a
  database, and publishes a numbered GitHub Release. It has a manual
  `workflow_dispatch` fallback and caches source pages between runs.
- The data workflow does **not** currently trigger a Render deployment after
  a successful release. A new release can therefore exist without being served
  by the live API.
- `Dockerfile` downloads the mutable `latest` release during an image build.
  Render caches Docker build layers, so a deploy alone is not a reliable way
  to prove that a new release was fetched.
- A recent scheduled data run timed out while connecting to `www.cdep.ro`.
  The correct failure behavior is to leave the current release and live
  deployment untouched, not publish partial data.
- The present audit has known findings: 223 mandate-coverage gaps, 50 overlap
  findings documented as inference artifacts, and 2 index-reconciliation
  errors. The audit command currently exits successfully despite findings, so
  a green workflow is not by itself proof that all data-quality gates passed.
- Render Free services spin down after 15 minutes without inbound traffic and
  take about a minute to wake. The frontend can load while API requests are
  waiting for the backend to wake.

## Target architecture

```text
Official parliamentary sources
            |
            v
GitHub Actions daily refresh (plus manual dispatch)
  fetch with bounded retries -> build isolated candidate -> validate
            |                         |
            | failure                 | all gates pass
            v                         v
Keep current release          Immutable dataset release + checksums
Notify maintainers                      |
                                         v
                          Update tracked release-version marker
                                         |
                                         v
                               Render Git deployment
                       build pinned release into Docker image
                                         |
                                         v
                          Health and dataset-version verification
                                         |
                                         v
Vercel static frontend -----------> Render read-only API
```

GitHub Actions remains the data-processing environment; Render serves the
published database; Vercel serves the static frontend. Do not scrape sources
from the live API service, write the database at runtime, or use periodic
keep-alive traffic to defeat Render's free spin-down behavior.

## Data release and deployment contract

Every release must be immutable and independently identifiable. A dataset
version is a release tag, not the word `latest`.

1. **Collect safely.** Reuse the page archive cache, apply bounded retries and
   backoff to transient network errors, and record which official pages were
   fetched, reused, or unavailable. A cached page is evidence from its
   recorded fetch date; it must not be presented as a fresh source response.
2. **Build in isolation.** Construct a candidate database and manifest without
   overwriting the currently published release.
3. **Validate before publishing.** At minimum:
   - SQLite `integrity_check` returns `ok`.
   - Required tables exist and have plausible non-zero counts.
   - Each manifest entry has a source URL and SHA-256; downloaded assets match
     their published checksum.
   - Required source sections are present and parser failures are reported.
   - The database schema version is supported by the deployed API.
   - Audit findings are compared with an explicit, reviewed baseline. New
     critical errors block publication; accepted existing findings remain
     visible and tracked rather than being silently reclassified as success.
4. **Publish only a passing candidate.** Create the release with a unique
   immutable tag and include the database, manifest, and machine-readable
   validation summary. Failed collection or validation leaves the last
   known-good release intact and does not request a deployment.
5. **Pin the build to that release.** After publishing, update a small tracked
   marker such as `data/latest-release.txt` to the exact release tag. The
   Docker build copies that marker before downloading the dataset and asks
   GitHub for that exact tag. Changing the marker invalidates the relevant
   Docker layer and makes the downloaded database reproducible. The build
   should record the selected tag in the image and expose it in health
   metadata.
6. **Deploy and verify.** The marker update is committed to the connected
   repository so Render's Git integration rebuilds the service. After deploy,
   a bounded verification step checks `/api/health`, confirms the reported
   dataset tag matches the release, and exercises a representative data API
   route. If Render does not deploy the automation-generated commit in the
   existing configuration, use a Render Deploy Hook from the workflow after
   the marker commit; store its URL only as a GitHub Actions secret.
7. **Retain a recovery window.** Keep a small, documented number of recent
   validated releases (for example, the latest 7) and prune older releases
   only after a newer deployment passes verification. Do not delete the
   previous good release as part of the publish step.

An immutable tag plus marker is the cache-invalidation mechanism; a deploy
hook alone is not. Render documents Docker build-layer caching, so the data
version must participate in the cached download step.

## Failure handling

| Failure | Required behavior |
| --- | --- |
| Official source is down, times out, or rate-limits | Retry a small bounded number of times with backoff. If still unavailable, fail the refresh, preserve the current release and live service, and report which sources failed. Do not turn missing pages into empty or zero-valued records. |
| Source content changes and parsing/audit fails | Do not publish or deploy the candidate. Keep logs and a machine-readable validation result; open or update one deduplicated GitHub issue with the failed run and summary. |
| GitHub schedule is delayed or disabled | Treat freshness as a separate health signal. Keep the last good dataset available and report stale data. Keep `workflow_dispatch` documented for recovery. Evaluate a daily Vercel Hobby Cron watchdog only if inactivity-related schedule suspension becomes a practical risk; it requires a narrowly scoped GitHub App credential stored in Vercel and is still subject to Vercel quotas and timing jitter. |
| GitHub Release upload fails | Do not update the release marker. Retry the upload safely or leave the previous release active. |
| Render build or health check fails | Keep serving the last successful deployment where Render permits rollback; do not mark the new version as live. Raise a deduplicated issue with the release tag and deployment link. |
| Render Free service is asleep | Allow the first request to wake it. Show a clear loading/retry state in the frontend; do not send artificial traffic to keep it awake. |
| Free quota is exhausted or the provider suspends service | Existing artifacts/data may remain but new builds or requests can be suspended. Notify the maintainer; recovery may require waiting for the quota reset or choosing a paid plan. |
| Data is older than its freshness threshold | Continue serving the last known-good dataset, label its as-of date clearly, and show that refresh failed or is overdue. Never imply that “API healthy” means “data current.” |

Notifications should include a link to the workflow run, dataset tag (if one
was created), failed gate, and next action. Do not include secret values,
deploy-hook URLs, or full environment dumps in logs or issues.

## Health, data quality, and user trust

The health surface should distinguish:

- **Liveness:** the API process responds.
- **Readiness:** the expected database opens and required tables are available.
- **Dataset identity:** immutable release tag and build timestamp.
- **Freshness:** latest successful source collection time, plus latest attempt
  and whether it succeeded.
- **Coverage/quality:** validation status and known data limitations, with
  counts and scope where meaningful.

The UI should continue to show an available-but-stale dataset during an
upstream outage, but label its age and status. A successful deployment or HTTP
200 response must not be presented as proof that the underlying parliamentary
data is complete or error-free. The currently known audit findings remain
visible until resolved and must not be hidden by a passing process exit code.

## Free-resource boundaries

- **GitHub Actions:** use the existing scheduled workflow, concurrency lock,
  source-page cache, immutable Releases, and `GITHUB_TOKEN` with only the
  permissions needed by the workflow. Scheduled starts can be delayed; the
  existing workflow also documents inactivity as a risk. Treat the schedule as
  best-effort, not a clock or an SLA.
- **Render:** keep the service stateless and read-only. Free web services sleep
  after 15 idle minutes, have ephemeral filesystems, and receive 750 included
  instance hours per workspace per calendar month. Included bandwidth and
  build-pipeline quotas also apply. Render may suspend services or builds when
  limits are reached and states Free services are not for production.
- **Vercel:** use it for the static frontend and API rewrite, not as the source
  of truth for the database. A Vercel Hobby Cron may be a watchdog, but its
  once-per-day limit and timing jitter make it a fallback trigger, not a
  reliability guarantee.
- **GitHub Release retention:** avoid unbounded daily asset growth. Retain
  enough validated versions for rollback and prune older assets/releases with
  a documented policy after successful deployment.
- **No paid monitoring or uptime pings:** use workflow summaries, GitHub
  Actions notifications/issues, provider logs, and the health endpoint. Do not
  add a third-party monitor that keeps the Render service awake.

Free-tier policies and quotas can change. Review the current provider limits
before relying on this plan for a public service.

## Phased implementation plan

### Phase 1 — Trustworthy release gates

- Make audit output machine-readable and return non-zero for new critical
  failures.
- Record a reviewed baseline for the 223 coverage gaps, 50 overlap findings,
  and 2 index-reconciliation errors; define which changes block publication.
- Validate SQLite integrity, manifest hashes, required data counts, source
  coverage, and schema compatibility before publishing.
- Ensure failed refreshes preserve the last successful release.

**Acceptance:** Injected source, integrity, manifest, and audit failures all
stop publication; a valid candidate produces a release with a validation
summary; prior releases remain available.

### Phase 2 — Deterministic automatic deployment

- Add a tracked exact-release marker and make the downloader accept a release
  tag instead of fetching `latest`.
- Place the marker before the dataset download layer in the Docker build.
- Publish, update the marker, and trigger Render only after all data gates pass.
- Report the release tag from `/api/health` and verify the tag and a data route
  after deployment.
- Add bounded retries and a deduplicated failure notification.

**Acceptance:** A new tag produces a new image containing that exact database;
a failed build leaves the previous healthy version active; logs and health
output identify the version actually being served.

### Phase 3 — Freshness and recovery visibility

- Show last successful refresh, last attempt, and dataset as-of date in the
  UI.
- Separate API liveness from database readiness and data freshness.
- Add a stale-data threshold and a user-visible stale state.
- Document one safe manual recovery route: rerun the data workflow with its
  normal cache, and use forced refetch only when appropriate.
- Exercise the rollback procedure using a retained release.

**Acceptance:** A source outage leaves the site usable with an explicit stale
warning; operators can identify the failed stage and restore a known-good
release without modifying the live database.

### Phase 4 — Free-tier continuity and maintenance

- Track GitHub schedule activity and Render/Vercel usage against their current
  free limits.
- Confirm whether repository activity from daily data runs prevents the
  schedule inactivity safeguard from applying. If not, add the Vercel Hobby
  Cron watchdog described above or accept the explicit manual re-enable step.
- Prune old releases only after successful verification; review retention and
  quota behavior periodically.
- Add a short monthly owner checklist covering failed runs, stale data,
  provider notices, and known audit findings.

**Acceptance:** There is a documented response when schedules stop, quotas
approach their limits, or a provider changes its free plan. No hidden paid
resource or expiring personal credential is required for the selected mode.

## One-time setup required

The base design uses the existing GitHub, Render, and Vercel projects and
requires no new paid service. A maintainer needs to:

1. Confirm the Render service is connected to the repository and automatically
   deploys commits to the intended branch.
2. Add the release marker/deployment verification changes through the normal
   CI-reviewed code path.
3. Grant the data workflow only the GitHub repository permissions it needs to
   publish releases and update the marker.
4. Decide whether the optional Vercel Cron watchdog is warranted. If enabled,
   install a GitHub App with workflow-dispatch permission and store its
   private key/IDs as Vercel environment secrets; do not use a personal access
   token with broad permissions.
5. Check Render monthly included usage and set account billing protections
   appropriate to the owner's preference.

Do not configure secrets, alter provider settings, or deploy as part of merely
approving this architecture.

## Completion definition

The project is considered operationally self-sustaining for its free-tier
target when successful source refreshes are validated, published, and served
without manual steps; failed refreshes cannot replace good data; deployments
prove which release they contain; stale data and failures are visible; and a
documented recovery path exists.

This means **routine hands-off operation**, not guaranteed freshness, uptime,
or unattended resolution of upstream changes. If uninterrupted public access
or a service-level commitment becomes necessary, move the API to a paid,
persistent hosting plan and add an independent monitoring/backup strategy.

## Provider references

- [Render Free services and limits](https://render.com/docs/free)
- [Render Docker builds and layer caching](https://render.com/docs/docker)
- [Render deploy hooks](https://render.com/docs/deploy-hooks)
- [Render build pipeline and included minutes](https://render.com/docs/build-pipeline)
- [GitHub Actions scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [Vercel Cron usage and Hobby limits](https://vercel.com/docs/schedules/cron-jobs/usage-and-pricing)
- [Vercel platform limits](https://vercel.com/docs/limits)
