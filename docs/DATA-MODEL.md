# Data Model Reference

The schema is defined in `pipeline/db.py` with SQLAlchemy 2.x and stored in SQLite in WAL
mode. It follows the Popolo vocabulary where it fits, adds bitemporal observation fields,
and keeps provenance on every membership.

- Database: `data/parlament.db` by default (`--db PATH` or `PARLAMENT_DB` overrides).
- Engine pragmas: `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON`,
  `busy_timeout=5000`.
- Primary keys are UUID strings generated in Python, not database autoincrement values.
- Timestamps default to `datetime.now(UTC)` in Python and are stored by SQLite as text.
- Enum-like columns are plain strings; the allowed values live in `pipeline/db.py` and are
  enforced by application code, not by database `CHECK` constraints.

---

## Relationships at a glance

```
person ──< person_identifier
   │
   ├──< person_name
   ├──< membership >── organization ──< post
   │        │                │
   │        │                └── organization.parent_id (self)
   │        └──< evidence
   ├──< event >── organization (from/to)
   └──< merge_audit (winner); loser_id is a plain id, kept for audit

fragment            independent raw snapshot record
pipeline_run        independent run log per source
key_event           independent legislature/election markers
vacancy             chamber/post vacancy marker
match_review        person_a / person_b proposed match
coverage            chamber × legislature completeness
```

---

## `person`

One row per real person across terms and chambers.

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `canonical_name` | VARCHAR(255) | no | — | Display name as published. |
| `normalized_name` | VARCHAR(255) | no | — | Lowercase, diacritics-stripped key for matching. |
| `sort_key` | VARCHAR(255) | yes | — | Order-insensitive token key (`Popescu Ion` = `Ion Popescu`). |
| `birth_date` | DATE | yes | — | Only when a source states it. |
| `photo_path` | VARCHAR(512) | yes | — | Optional local photo path. |
| `wikidata_qid` | VARCHAR(32) | yes | — | Enrichment identifier. |
| `match_status` | VARCHAR(16) | no | `unmatched` | `auto`, `review`, `unmatched`, `merged`. |
| `created_at` | DATETIME | no | now (UTC) | Creation timestamp. |

**Indexes:** `normalized_name`, `sort_key`, `wikidata_qid`.

**Relationships:** identifiers and names cascade-delete with the person. Memberships and
events are *not* cascade-deleted; merges repoint them instead.

---

## `person_identifier`

Official or external identifiers, scoped to a legislature when the source id is per-term.

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `person_id` | VARCHAR(36) | no | — | FK → `person.id`. |
| `scheme` | VARCHAR(32) | no | — | `cdep_idm`, `senat_guid`, `ep_uuid`, `wikidata`. |
| `identifier` | VARCHAR(128) | no | — | Source id value. |
| `legislature` | VARCHAR(16) | yes | — | Term key (`2024`); null for term-independent schemes. |
| `start_date` | DATE | yes | — | Optional validity start. |
| `end_date` | DATE | yes | — | Optional validity end. |

**Constraints:** `uq_identifier` on `(scheme, identifier, legislature)`.

**Indexes:** `person_id`.

**Note:** Camera `idm` and Senat GUID are per-term, so the same numeric/GUID value in two
legislatures is stored as two identifiers. The unique constraint includes the legislature
for this reason. SQLite treats `NULL`s as distinct in unique indexes; term-independent
identifiers should not be duplicated by application code.

---

## `person_name`

Names and dated aliases for a person (former names, spelling variants, merge aliases).

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `person_id` | VARCHAR(36) | no | — | FK → `person.id`. |
| `type` | VARCHAR(16) | no | `name` | `name` or `alias`. |
| `name` | VARCHAR(255) | no | — | Name text. |
| `normalized_name` | VARCHAR(255) | no | — | Matching key. |
| `sort_key` | VARCHAR(255) | yes | — | Order-insensitive key. |
| `start_date` | DATE | yes | — | When the name applied, if known. |
| `end_date` | DATE | yes | — | End-exclusive, if known. |

**Indexes:** `person_id`, `normalized_name`, `sort_key`.

**Merge behavior:** the loser's canonical name is converted to `type="alias"` on the
winner, or appended if no matching name exists.

---

## `organization`

Chambers, parliamentary groups, parties, committees, bureaus, delegations, friendship
groups, and other bodies.

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `classification` | VARCHAR(16) | no | — | See organization classifications. |
| `name` | VARCHAR(512) | no | — | Official label. |
| `normalized_name` | VARCHAR(512) | no | — | Diacritics-stripped lowercase label. |
| `short_name` | VARCHAR(64) | yes | — | Acronym (`PSD`, `UPR`). |
| `alt_labels` | JSON | yes | — | Former names / aliases. |
| `color` | VARCHAR(16) | yes | — | Hex color from reference data. |
| `parent_id` | VARCHAR(36) | yes | — | FK → `organization.id` (self). |
| `wikidata_qid` | VARCHAR(32) | yes | — | Optional QID. |
| `founding_date` | DATE | yes | — | From the official ledger when published. |
| `dissolution_date` | DATE | yes | — | When published. |
| `localised_labels` | JSON | yes | — | `{"name": {"ro": …, "en": …}}`. |
| `chamber` | VARCHAR(16) | yes | — | `deputies` or `senate` when chamber-specific. |

**Constraints:** `uq_org` on `(classification, normalized_name, founding_date)`.

**Indexes:** `classification`, `normalized_name`, `short_name`.

**Note:** `founding_date` is nullable and part of the unique key. SQLite allows multiple
`NULL` values in a unique index, so the application's `get_or_create_org` lookup remains
the effective deduplication mechanism.

---

## `post`

A seat or leadership position within an organization (Popolo `Post`).

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `org_id` | VARCHAR(36) | no | — | FK → `organization.id`. |
| `label` | VARCHAR(255) | no | — | e.g. `Deputy`, `Group leader`. |
| `role_type` | VARCHAR(16) | no | `seat` | `seat` or `leadership`. |
| `importance` | INTEGER | no | 0 | Ordering hint. |
| `maximum_memberships` | INTEGER | yes | — | Optional cap (e.g. one leader). |

**Indexes:** `org_id`.

The current pipeline models most roles directly on `membership.role`; the `post` table is
part of the Popolo-compatible surface and is exported when referenced.

---

## `membership`

A dated tenure of a person in an organization. This is the central temporal table.

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `person_id` | VARCHAR(36) | no | — | FK → `person.id`. |
| `org_id` | VARCHAR(36) | no | — | FK → `organization.id`. |
| `post_id` | VARCHAR(36) | yes | — | FK → `post.id`. |
| `on_behalf_of_id` | VARCHAR(36) | yes | — | FK → `organization.id`; the party behind a group membership. |
| `chamber` | VARCHAR(16) | no | — | `deputies` or `senate`. |
| `legislature` | VARCHAR(16) | yes | — | Term key (`2024`). |
| `role` | VARCHAR(255) | yes | — | Role within the organization (`leader`, `member`, …). |
| `importance` | INTEGER | no | 0 | Ordering hint. |
| `start_date` | DATE | yes | — | Inclusive start. |
| `end_date` | DATE | yes | — | **Exclusive** end; `NULL` = open. |
| `start_precision` | VARCHAR(10) | yes | — | `YYYY-MM-DD`, `YYYY-MM`, `YYYY`. |
| `end_precision` | VARCHAR(10) | yes | — | Same. |
| `start_reason` | VARCHAR(32) | yes | — | Reason enum. |
| `end_reason` | VARCHAR(32) | yes | — | Reason enum. |
| `confidence` | VARCHAR(32) | no | `derived` | Confidence enum. |
| `source_url` | VARCHAR(1024) | yes | — | Official page for this fact. |
| `group_acronym_at_event` | VARCHAR(64) | yes | — | Group acronym at the time. |
| `first_seen_at` | DATETIME | no | now (UTC) | First observation by the pipeline. |
| `last_seen_at` | DATETIME | no | now (UTC) | Most recent observation. |

**Constraints:** `uq_stint` on `(org_id, person_id, post_id, end_date)`.

**Indexes:** `person_id`, `org_id`, `chamber`, `legislature`;
`ix_membership_person_end (person_id, end_date)`;
`ix_membership_org_end (org_id, end_date)`.

**Semantics**

- As-of query: `start_date <= D AND (end_date IS NULL OR end_date > D)`.
- An open tenure has `end_date IS NULL`.
- A closed tenure is never reopened; a returning member gets a new row/id.
- Repeat stints coexist because the unique key includes `end_date` (and `post_id`).
- Inverted intervals are clamped so `end_date >= start_date`.
- Confidence ranks `official_ledger` < `official_profile` < `derived` < `community`
  (lower is stronger); a write may improve confidence but not downgrade it.

**Note on `uq_stint`:** `post_id` and `end_date` are nullable. SQLite permits duplicate
rows when a key component is `NULL`, so the writer's `_existing()` lookup is responsible
for idempotency in the open-tenure case.

---

## `evidence`

Provenance attached to a membership.

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `membership_id` | VARCHAR(36) | no | — | FK → `membership.id`. |
| `type` | VARCHAR(32) | no | — | `official_ledger`, `profile`, `jo`, `intervention`, `scrutin`, `other`. |
| `source_url` | VARCHAR(1024) | yes | — | Exact official page. |
| `snapshot_hash` | VARCHAR(64) | yes | — | SHA-256 of the archived page; matches `fragment.checksum`. |
| `note` | TEXT | yes | — | Human explanation, e.g. “start inferred (founding/continuing member)”. |
| `observed_at` | DATETIME | no | now (UTC) | When the evidence was recorded. |

**Indexes:** `membership_id`.

One membership may have multiple evidence rows (ledger plus profile, for example). The
API's `/api/evidence/{id}` resolves `snapshot_hash` to a `/snapshots/...` URL; a missing
fragment yields `snapshot_url: null`, never a fake link.

---

## `fragment`

A raw archived fetch, decoupled from the normalized model.

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `model` | VARCHAR(64) | no | — | Parser/model name (`group_ledger`, `senator_profile`, `group_roster`). |
| `source_name` | VARCHAR(64) | no | — | `cdep` or `senat`. |
| `source_id` | VARCHAR(255) | yes | — | `idg` or GUID. |
| `source_url` | VARCHAR(1024) | yes | — | Fetched URL. |
| `timestamp` | DATETIME | no | now (UTC) | Record creation time. |
| `group_key` | VARCHAR(255) | yes | — | Deduplication key, e.g. `2024:1` or a GUID. |
| `checksum` | VARCHAR(64) | no | — | SHA-256 of the content. |
| `data` | JSON | no | — | Small parsed metadata (`short_name`, `name`, roster counts). |
| `snapshot_path` | VARCHAR(512) | yes | — | `data/snapshots/<source>/<hash>.html`. |

**Indexes:** `model`, `source_name`, `group_key`, `checksum`.

Unchanged content is skipped unless `force=True`; the check compares the new checksum with
the latest fragment for `(source_name, group_key)`.

---

## `pipeline_run`

One row per source ingestion/poll attempt.

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `source` | VARCHAR(64) | no | — | `cdep` or `senat`. |
| `status` | VARCHAR(32) | no | — | `SUCCESS`, `FAILURE`, `DATA_UNAVAILABLE`, `DATA_UNCHANGED`. |
| `checksum` | VARCHAR(64) | yes | — | Optional run checksum. |
| `idempotency_key` | VARCHAR(255) | yes | — | e.g. `groups:2024`, `profiles`. |
| `started_at` | DATETIME | no | now (UTC) | Start. |
| `finished_at` | DATETIME | yes | — | Finish. |
| `rows` | INTEGER | no | 0 | Rows written or processed. |
| `error` | TEXT | yes | — | Error text on failure. |

**Indexes:** `source`.

`/api/health` reads the latest row per source and reports `never_run` when none exists.

---

## `event`

A derived, typed movement or organizational change.

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `type` | VARCHAR(32) | no | — | Event type enum. |
| `person_id` | VARCHAR(36) | yes | — | FK → `person.id`; null for organization-only events. |
| `chamber` | VARCHAR(16) | yes | — | `deputies` or `senate`. |
| `from_org_id` | VARCHAR(36) | yes | — | FK → `organization.id`. |
| `to_org_id` | VARCHAR(36) | yes | — | FK → `organization.id`. |
| `post_id` | VARCHAR(36) | yes | — | FK → `post.id`. |
| `role` | VARCHAR(255) | yes | — | Role, when relevant. |
| `event_date` | DATE | yes | — | Date of the event. |
| `precision` | VARCHAR(10) | yes | — | Date precision. |
| `detected_at` | DATETIME | no | now (UTC) | Derivation timestamp. |
| `reason` | VARCHAR(32) | yes | — | Reason enum. |
| `confidence` | VARCHAR(32) | no | `derived` | Confidence enum. |
| `group_acronym_at_event` | VARCHAR(64) | yes | — | Acronym at the time. |
| `summary_ro` | TEXT | yes | — | Romanian summary. |
| `summary_en` | TEXT | yes | — | English summary. |
| `dedup_key` | VARCHAR(255) | yes | — | **Unique** deterministic key. |

**Indexes:** `type`, `person_id`, `event_date`; unique on `dedup_key`.

`dedup_key` examples: `switch:<person>:<from>:<to>:<date>`,
`join:<person>:<org>:<date>`, `leave:<person>:<org>:<date>`,
`founded:<org>:<date>`, `renamed:<org>:<old_label>`.

---

## `key_event`

Legislature and election markers seeded from `data/reference/legislatures.json`.

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `type` | VARCHAR(32) | no | — | `legislature` or `election`. |
| `chamber` | VARCHAR(16) | yes | — | `deputies` or `senate`. |
| `start_date` | DATE | yes | — | Term start. |
| `end_date` | DATE | yes | — | Term end; null for the current term. |
| `label` | VARCHAR(255) | yes | — | Term key (`2024`). |

No explicit indexes. Coverage and meta derive chamber/term boundaries from these rows.

---

## `vacancy`

A dated vacancy in a chamber or post.

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `chamber` | VARCHAR(16) | no | — | `deputies` or `senate`. |
| `post_id` | VARCHAR(36) | yes | — | FK → `post.id`. |
| `start_date` | DATE | yes | — | Vacancy start. |
| `end_date` | DATE | yes | — | Vacancy end (end-exclusive by convention). |
| `reason` | VARCHAR(32) | yes | — | Reason enum. |

The table is present for completeness of the temporal model; current ingestion focuses on
memberships and events.

---

## `match_review`

Proposed person matches awaiting human review.

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `person_a` | VARCHAR(36) | no | — | FK → `person.id`. |
| `person_b` | VARCHAR(36) | no | — | FK → `person.id`. |
| `score` | FLOAT | no | 0.0 | Similarity score. |
| `reason` | TEXT | yes | — | Explanation. |
| `status` | VARCHAR(16) | no | `pending` | `pending`, `approved`, `rejected`. |
| `created_at` | DATETIME | no | now (UTC) | Creation timestamp. |

No explicit indexes. A review row is a proposal, not a merge.

---

## `coverage`

Persisted completeness matrix per chamber and legislature.

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `chamber` | VARCHAR(16) | no | — | `deputies` or `senate`. |
| `legislature` | VARCHAR(16) | yes | — | Term key. |
| `period_start` | DATE | yes | — | Term start. |
| `period_end` | DATE | yes | — | Term end; null for current. |
| `completeness` | VARCHAR(16) | no | `partial` | `full`, `partial`, `none`. |
| `note` | TEXT | yes | — | Human explanation, e.g. “152 of ~330 seats ingested.” |

No explicit indexes. The coverage upsert keys rows by `(chamber, legislature)`
(`pipeline.coverage`; the `parlament coverage` subcommand is not wired in this checkout).

---

## `merge_audit`

Auditable, reversible person merges.

| Column | Type | Null | Default | Meaning |
| --- | --- | --- | --- | --- |
| `id` | VARCHAR(36) | no | UUID | Primary key. |
| `winner_id` | VARCHAR(36) | no | — | FK → `person.id`. |
| `loser_id` | VARCHAR(36) | no | — | Plain id; deliberately **not** a FK so the audit survives row changes. |
| `operations` | JSON | no | — | Ordered list of `repoint` / `append` / `replace` operations. |
| `created_at` | DATETIME | no | now (UTC) | Merge timestamp. |
| `reverted` | BOOLEAN | no | false | Whether the merge was reversed. |

`operations` examples:

```json
[
  {"op": "repoint", "table": "person_identifier", "id": "…", "from": "loser", "to": "winner"},
  {"op": "repoint", "table": "membership", "id": "…", "from": "loser", "to": "winner"},
  {"op": "append", "table": "person_name", "name": "Former Name"},
  {"op": "replace", "field": "birth_date", "value": "1972-09-20"}
]
```

`revert_merge` replays these in reverse and sets `reverted=true`.

---

## Enumerations

Values are stored as strings. Keep application code, exports, and documentation in sync
when adding one.

### Chambers

```text
deputies
senate
```

### Organization classifications

```text
chamber
group
party
committee
bureau
delegation
friendship
other
```

### Confidence (strongest → weakest)

```text
official_ledger
official_profile
derived
community
```

`CONFIDENCE_RANK` assigns 0–3; a lower rank is stronger. Writers may improve a row's
confidence but do not downgrade it.

### Reasons

```text
CHANGED_PARTY
WHIP_REMOVED
WHIP_RESTORED
DIED
RESIGNED
BY_ELECTION
GENERAL_ELECTION
UNKNOWN
```

### Evidence types

```text
official_ledger
profile
jo
intervention
scrutin
other
```

### Event types

```text
join
leave
switch_group
switch_party
group_founded
group_renamed
committee_join
committee_leave
role_change
mandate_start
mandate_end
```

The current derivation emits `join`, `leave`, `switch_group`, `group_founded`, and
`group_renamed`; the remaining types are part of the vocabulary for committee/role/mandate
events.

### Pipeline run statuses

```text
SUCCESS
FAILURE
DATA_UNAVAILABLE
DATA_UNCHANGED
```

`/api/health` also reports `never_run` when no run row exists.

### Person match statuses

```text
auto
review
unmatched
merged
```

### Match review statuses

```text
pending
approved
rejected
```

### Coverage completeness

```text
full
partial
none
```

### Post role types

```text
seat
leadership
```

### Person name types

```text
name
alias
```

### Identifier schemes (observed)

```text
cdep_idm     Camera Deputaților per-term member id
senat_guid   Senat per-term profile GUID
ep_uuid      reserved for EveryPolitician-style ids
wikidata     Wikidata QID
```

---

## Date precision and storage

`ApproxDate` produces a `precision` tag:

| Source expression | `earliest` | `latest` | `precision` |
| --- | --- | --- | --- |
| `15 iun. 2026` | 2026-06-15 | 2026-06-15 | `2026-06-15` |
| `iunie 2026` | 2026-06-01 | 2026-06-30 | `2026-06` |
| `2026` | 2026-01-01 | 2026-12-31 | `2026` |

Membership rows store the **earliest** bound in `start_date` and the precision tag in
`start_precision`; they never store a fabricated mid-month or mid-year day. `end_date` is
end-exclusive in queries. See [METHODOLOGY.md](METHODOLOGY.md).
