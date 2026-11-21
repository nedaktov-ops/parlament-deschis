---
id: DATA-MODEL
type: reference
title: "Data model — ORM tables, vote scope, latent registers and known gaps"
description: "Distilled reference for the shipped SQLite schema: 18-table pinned release, scope of vote tables, persisted switch waves, licence register, identity constraints and coverage of birth dates and genealogy."
status: active
authority: mirror
tags: [type/reference, lifecycle/active, domain/data]
source_paths: [docs/DATA-MODEL.md, docs/POST-INITIAL-AUDIT-2026-11-21.md, scripts/prepare_db.py, pipeline/db.py]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Data model

The ORM lives in `pipeline/db.py`; the shippable database is a prepared SQLite file whose exact release is pinned in `data/latest-release.txt`. Model rules (what may be inferred, confidence ranks, intervals) are normative in [METHODOLOGY](METHODOLOGY.md).

State context: [RELEASE-AND-VERIFICATION](../10-STATE/RELEASE-AND-VERIFICATION.md).

## Pinned release at a glance

- The pinned release contains **18 tables and zero vote tables**. Roll-call votes and CHES ideology are not part of the published corpus.
- **Scope qualifier:** locally gitignored working DBs do have `vote`, `vote_position`, `vote_import_run` and `source_license` tables, with unreleased vote rows. "Production has no vote data" is a statement about the *published corpus*, not about every database file on disk.
- Current pin: `data-20261117-T213500` — 3,388 persons, **7,349 prepared memberships (7,358 raw release asset)** after dedupe of 9 duplicate closed stints; 142 switch waves; 26 committee organizations (23 with active memberships, 9 with chairs).

## Core tables

| Table | Role |
| --- | --- |
| `person` | Stable identity: `canonical_name`, `normalized_name`, nullable `birth_date`, `wikidata_qid`, `match_status`. |
| `person_identifier`, `person_name` | Official identifiers scoped by `(scheme, identifier, legislature)`; dated canonical names and aliases. |
| `organization` | Chamber/group/party/committee plus `parent_id` and the `previous_party_id` / `successor_party_id` genealogy fields. |
| `post`, `membership` | Seats/roles and bitemporal tenures. `membership` carries valid-time, observation-time and precision columns; unique on `(org_id, person_id, post_id, end_date)`. |
| `evidence`, `fragment`, `pipeline_run` | Source URL, SHA-256 `snapshot_hash`, archived page bytes, and per-run status/row counts. |
| `event` | Derived `join`/`leave`/`switch_group`/… rows with a unique `dedup_key`; confidence inherited from the tenure. |
| `switch_wave`, `key_event`, `coverage`, `vacancy`, `match_review`, `merge_audit`, `asset_declaration` | Analytics inputs, legislature bounds, coverage badges, identity review and auditable merges. |

Enums are stored as strings: chambers `deputies`/`senate`; confidence `official_ledger`, `official_profile`, `derived`, `community`; reasons such as `CHANGED_PARTY`, `WHIP_REMOVED`, `DIED`.

## Resolved contradictions and gaps

- **`switch_wave` is persisted, not computed.** One doc section lists it as computed-on-demand alongside analytics views, but the schema defines it as an ORM table and the shipped DB has **142 rows**. The ORM section is correct.
- **`source_license` is empty/latent.** The pinned release has no such table; both working DBs have it with **0 rows**. `ensure_source_licenses()` is defined in `pipeline/licenses.py` but is not called from the CLI or app startup, so licence enforcement is an incomplete component, not a working gate.
- **Vote positions require identity.** `vote_position.person_id` is **NOT NULL**: an unresolved official position is quarantined in `vote_import_run.report` rather than stored against a guessed person. `choice` is normalised from the published token; `-` means present but did not vote. `dedup_key` values are deterministic (`<source>:<native_vote_id>` and `<vote_key>:<person_id>`).
- **Party genealogy has 0 links.** Both `previous_party_id` and `successor_party_id` are non-null in zero rows; the documented succession/split/merger model is intended, not ingested. GraphQL `PartyType` does not expose `previous`/`successor` either.
- **Birth-date coverage:** 3,113 of 3,388 persons (about 92%) have a sourced `birth_date` from cdep committee ledgers; roughly 275 remain undated.
- Shipped DB is read-only by construction: DELETE journal mode (no WAL side-cars), `user_version = 1`, header bytes 18/19 = `1,1`, integrity and foreign-key checks clean. Details in [DATA-RELEASE-PROCEDURE](DATA-RELEASE-PROCEDURE.md).
