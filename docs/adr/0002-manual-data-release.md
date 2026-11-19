# 2. Manual, immutable data releases with a pinned marker

- **Status:** Accepted (implemented)
- **Date:** 2026-11-17
- **Deciders:** data pipeline and deployment owners
- **Related:** `data/latest-release.txt`, `.github/workflows/data.yml`,
  `scripts/prepare_db.py`, `scripts/download_dataset.py`, `docs/DEPLOYMENT.md`,
  `docs/DATA-COMPLETENESS-RECOVERY.md`

## Context

The API serves a SQLite database that is **read-only at runtime** and baked
into the deployment image: free hosts have no persistent disk, and a WAL
database cannot even open on a read-only filesystem. Data therefore changes
only by publishing a new dataset release and redeploying.

A release must be reproducible and verifiable: consumers need the exact
database, the page manifest with SHA-256 hashes, and the audit report. The
source (`cdep.ro`) may be unreachable from automation — the recovery plan
records local ingest → release asset as the supported path — so a purely
scheduled publish cannot be the only route. The service must also be
fail-closed: if collection or the strict audit fails, users keep getting the
previous release rather than partial data.

The current shipped release is the tag pinned in `data/latest-release.txt`
(read that file for the exact tag and provenance); at the time this ADR was
written it carried 3,388 persons / 7,358 memberships, 26 committee
organisations and 142 switch waves.

## Decision

Publish datasets as **immutable GitHub release assets**, then pin the exact tag
with a dedicated commit:

1. Build and audit the corpus locally (or via `workflow_dispatch` recovery
   path), including the strict audit gate; prepare the shippable database with
   `scripts/prepare_db.py`.
2. Publish an immutable tag (`data-<run-id>-<attempt>`) with `parlament.db`,
   `manifest.jsonl` (every page and its SHA-256) and `audit-report.json`.
3. Write the tag into `data/latest-release.txt` and commit it. The Docker build
   downloads that exact asset and verifies its SHA-256 before preparing the
   read-only database.
4. The pin commit does **not** start CI or Render's Git deployment (it is pushed
   with `GITHUB_TOKEN`). The data workflow triggers Render explicitly through its
   API, then deploy verification checks that `/api/health` reports the expected
   `dataset.release_tag` (see `.github/workflows/data.yml`).
5. Rollback is `git revert` of the pin commit — the previous release asset and
   tag remain available. No data is rewritten in place.

Scheduled rebuilds remain best-effort; `workflow_dispatch` is the manual
recovery path. Mutable analytics use `no-store` so no edge cache can outlive a
pin (coordinated with the HTTP caching remediation).

## Consequences

**Positive**

- Reproducible: one tag identifies the database, its source hashes and its
  audit report; the pin is an auditable git commit.
- Fail-closed: without a green collection + strict audit + verified asset no
  new release is published and the live service keeps the prior dataset.
- Rollback is a single revert of a marker file; no data or schema rewrite.
- The runtime never writes to the database.

**Negative / obligations**

- Publishing requires a deliberate pin commit and a post-deploy check; it is
  not instantaneous or fully unattended.
- An operator must confirm the source/asset is current; a stale pin keeps
  serving stale-but-correct data rather than failing loudly.
- Frontend and API deploy together; a frontend change alone does not require a
  new data release, but a data release does require the pin-driven deploy.

## Alternatives

- **Collect and write to the DB at runtime:** rejected — read-only filesystem
  and WAL constraints on the hosts.
- **Mutable `latest` asset overwritten in place:** rejected — no reproducibility
  or reliable rollback, and checksums cannot identify a release.
- **Auto-deploy on every workflow run:** rejected — removes the fail-closed
  audit gate and the explicit identity check.
- **Scheduled-only publishing:** rejected — the source can be unreachable from
  CI; a manual local-ingest path is required for recovery.
