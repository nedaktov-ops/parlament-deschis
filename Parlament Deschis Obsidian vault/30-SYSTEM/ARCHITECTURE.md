---
id: ARCHITECTURE
type: reference
title: "System architecture — one-way pipeline, bitemporal facts, read-only API"
description: "Distilled reference for the ingest pipeline, bitemporal model, evidence and snapshot hashing, as-of API and static React dashboard, with known documentation drift flagged."
status: active
authority: mirror
tags: [type/reference, lifecycle/active, domain/project]
source_paths: [docs/ARCHITECTURE.md, docs/POST-INITIAL-AUDIT-2026-11-21.md, backend/main.py, pipeline/cli.py]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Architecture

Parlament Deschis is a **one-way data pipeline with a read-only query layer**. Official chamber publications are fetched politely, archived by content hash, parsed into typed records, resolved to stable people, reconciled into bitemporal tenures, converted into events, and served as an as-of API to a static React dashboard. The only API write surface is the token-protected admin poll trigger; there is no live scraping from the UI and no browser automation or CAPTCHA bypass.

State context: [CURRENT-STATE](../10-STATE/CURRENT-STATE.md).

## Pipeline stages

| Stage | Where | What it does |
| --- | --- | --- |
| Polite fetch | `pipeline/sources/client.py` | `robots.txt`, per-host pacing (2.5 s, stricter than the 1 req/s ceiling), identifying `User-Agent`, `ETag`/`Last-Modified` with `304` cache reuse, `Retry-After` on 429, backoff on 5xx, stop on CAPTCHA. |
| Chamber adapters | `sources/cdep.py`, `sources/senat.py` | Discover group ledgers / profiles via group index or sitemap; each writes a `pipeline_run` row (`SUCCESS`/`FAILURE`) so one chamber failing does not abort the other. |
| Fragment + snapshot store | `pipeline/fragments.py` | SHA-256 over UTF-8 bytes; `data/snapshots/<source>/<hash>.<ext>`; unchanged content is skipped unless forced; changed content becomes a `fragment` row. Snapshots are content-addressed and gitignored; the DB is the index. |
| Parsers | `pipeline/parse/` | Pure HTML → dataclasses for the Camera group ledger and the Senate profile/group roster. Dates pass through `ApproxDate` (`earliest`, `latest`, `precision`, `source_string`). See [METHODOLOGY](METHODOLOGY.md). |
| Identity | `pipeline/identity.py` | Exact official identifier scoped by scheme **and** legislature first; then a unique name candidate filtered by birth date and conflicting identifiers; otherwise create a new `unmatched` person. Never guesses. |
| Merges | `pipeline/identity.py` | `merge_persons` repoints rows, keeps the loser, and writes a `merge_audit` operation log; `revert_merge` replays it in reverse. Merges are auditable and reversible, not destructive. |
| Reconciliation | `pipeline/reconcile.py` | Authoritative ledgers produce closed tenures that are immutable; derived observations collapse same-org runs. Confidence may improve but is never downgraded by a weaker observation. |
| Evidence + events | `ingest.py` attaches evidence; `pipeline/events.py` derives events | Evidence carries `type`, `source_url`, `snapshot_hash`, `note`. Events (`join`, `leave`, `switch_group`, `group_founded`, …) get a deterministic `dedup_key` so re-runs do not duplicate. |
| Coverage + exports | `pipeline/coverage.py`, `pipeline/export.py` | Coverage counts distinct persons per chamber/legislature against 330 deputies / 136 senators. Export is the single serialization contract for Popolo JSON and five CSV datasets, shared by CLI and API. |
| Read API + dashboard | `backend/`, `frontend/` | FastAPI serves as-of queries and exports from SQLite; a Vite/React/TypeScript SPA (slider, hemicycles, timeline, Sankey, drawer, citation popover) reads only the local API. |

## Bitemporal model

- **Valid time:** `start_date`, `end_date` — when a membership was true in the real world.
- **Transaction/observation time:** `first_seen_at`, `last_seen_at`, plus `event.detected_at` and `evidence.observed_at` — when the pipeline saw it.
- **Publication precision:** `start_precision`, `end_precision` — how precisely the source stated the date.

All as-of queries are **end-exclusive**: `start_date <= :as_of AND (end_date IS NULL OR end_date > :as_of)`. `end_date` is the first day the tenure is *not* active, so a switch on 15 June is counted in the old group through 14 June and in the new group from 15 June. Closed tenures are immutable; a return stint gets a new `membership.id`. Schema detail lives in [DATA-MODEL](DATA-MODEL.md).

## Evidence, snapshot hash, read-only runtime

Each membership points at a source URL and one or more evidence rows; an evidence row may carry the fragment's SHA-256 `snapshot_hash`. `/api/evidence/{id}` resolves the archived copy via that checksum and returns `snapshot_url: null` when no fragment exists. The shipped database is produced by `scripts/prepare_db.py`: deduplicated, `journal_mode=DELETE`, `user_version` stamped, and marked `query_only=ON` — WAL is an ingest-stage concern, not a property of the read-only release. The API reads SQLite; it does not write to it in production (the background poller requires a positive `PARLAMENT_POLL_INTERVAL_MIN`, and the admin trigger requires `PARLAMENT_ADMIN_TOKEN`).

## Known documentation drift (flagged, not repaired here)

- `docs/ARCHITECTURE.md` references a non-existent `pipeline/evidence.py`; evidence is attached in `ingest.py`.
- The doc's operational note says "SQLite in WAL mode". That is the local ingest lifecycle; **the shipped release asset is DELETE-mode** by design for read-only hosting ([DATA-RELEASE-PROCEDURE](DATA-RELEASE-PROCEDURE.md)).
- Older docs claim the `coverage`, `enrich` and `serve` CLI subcommands are not wired. All three **are** present in `pipeline.cli --help` at this commit.
- "No vote data" is a scope statement: the published corpus has no vote tables, while gitignored local working DBs hold unreleased vote rows. See [DATA-MODEL](DATA-MODEL.md) and [RELEASE-AND-VERIFICATION](../10-STATE/RELEASE-AND-VERIFICATION.md).
