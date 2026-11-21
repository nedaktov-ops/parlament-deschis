---
id: DATA-RELEASE-PROCEDURE
type: runbook
title: "Data release procedure — manual immutable releases with a pinned marker"
description: "Runbook for building, auditing, preparing, publishing and pinning an immutable dataset release, triggering Render explicitly, verifying the served tag and rolling back safely."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/ops]
source_paths: [docs/adr/0002-manual-data-release.md, scripts/prepare_db.py, scripts/download_dataset.py, data/latest-release.txt, .github/workflows/data.yml]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Data release procedure

Data changes only by publishing a new immutable release and redeploying: the runtime filesystem is read-only and a WAL database cannot even be opened there. Releases are fail-closed — if collection or the strict audit fails, users keep getting the previous release. `workflow_dispatch` (local ingest → release asset) is the supported recovery path when the source is unreachable from automation.

State context: [RELEASE-AND-VERIFICATION](../10-STATE/RELEASE-AND-VERIFICATION.md). Runtime topology: [DEPLOYMENT](DEPLOYMENT.md).

## Steps

1. **Build and audit locally.** Build the corpus and run the strict audit gate (`--strict --baseline data/reference/corpus-audit-baseline.json`): currently **275 known / 0 new** findings. Do not publish on a red audit.
2. **Prepare the shippable DB** with `scripts/prepare_db.py <source.db> <target.db>`. It works on a `VACUUM INTO` copy, deduplicates the **9 duplicate closed stints** in the shipped corpus (repointing their evidence), creates partial indexes, sets `journal_mode=DELETE` (no WAL side-cars), runs `PRAGMA integrity_check` and foreign-key checks, stamps **`PRAGMA user_version = 1`** (so no legacy destructive merge replays at runtime), and sets `query_only=ON`. The pinned asset's file-header bytes 18/19 are `1,1` (DELETE). Output is atomically swapped into place.
3. **Publish an immutable GitHub release** tagged `data-<run-id>-<attempt>` with three assets: `parlament.db`, `manifest.jsonl` (every page and its SHA-256) and `audit-report.json`. The tag is reproducible; no `latest` asset is overwritten in place.
4. **Pin the tag.** Write it into `data/latest-release.txt` and commit. Current pin: `data-20261117-T213500` — 3,388 persons, **7,349 prepared memberships (7,358 raw asset)**, 142 switch waves, 26 committee organizations (23 active, 9 with chairs). The Docker build downloads that exact asset and verifies its SHA-256 before preparing the read-only DB. Mutable analytics use `no-store` so no edge cache outlives a pin.
5. **Trigger Render explicitly** through its API and wait for the new tag. The marker push uses `GITHUB_TOKEN`, so it starts **neither CI nor Render's Git deployment** and does not itself trigger Deploy verify.
6. **Verify the served pin.** `/api/health` must report `dataset.release_tag` equal to `data/latest-release.txt`; confirm the SPA shell, health/live/ready endpoints, non-zero persons/memberships, and valid coverage/traseism responses. See [DEPLOYMENT](DEPLOYMENT.md) and [API](API.md).
7. **Rollback by reverting the pin commit** (`git revert`), never by rewriting data in place. The previous release asset and tag remain available; a later Render push can redeploy over a platform rollback, so freeze auto-deploy first if needed.

## Why this shape

- **Reproducible** — one tag identifies the DB, its page hashes and its audit report; the pin is an auditable commit.
- **Fail-closed** — no green collection + strict audit + verified asset means no new release.
- **Non-destructive** — rollback is a one-file revert; no schema or data rewrite, and the runtime never writes to the DB.
- **Obligations** — publishing is deliberate, not instantaneous; an operator must confirm the asset is current, because a stale pin serves stale-but-correct data rather than failing loudly. A data release requires the pin-driven deploy, while a frontend-only change does not.

Scheduled rebuilds remain best-effort (issue #14 records `cdep.ro` timeouts); the manual local-ingest path is the recovery route. The corpus has no vote data; local working DBs with vote rows are gitignored and are not part of any release.
