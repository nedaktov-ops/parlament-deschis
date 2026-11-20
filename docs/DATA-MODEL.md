# Data Model Reference

This document describes the SQLAlchemy ORM models in `pipeline/db.py` and their corresponding database tables.

---

## Core Tables

### `person`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | Primary key |
| `canonical_name` | String(255) | NOT NULL | Display name |
| `normalized_name` | String(255) | INDEX | Lowercased, diacritics stripped |
| `sort_key` | String(255) | NULLABLE, INDEX | For sorting |
| `birth_date` | Date | NULLABLE | From Wikidata |
| `photo_path` | String(512) | NULLABLE | Local path |
| `wikidata_qid` | String(32) | NULLABLE, INDEX | Wikidata entity |
| `match_status` | String(16) | DEFAULT 'unmatched' | Reconciliation state |
| `created_at` | DateTime | DEFAULT now() | |

**Relationships**: `identifiers`, `names`, `memberships`

---

### `person_identifier`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `person_id` | UUID | FK, INDEX | → person.id |
| `scheme` | String(32) | | e.g., `cdep_idm`, `senat_guid` |
| `identifier` | String(128) | | Value |
| `legislature` | String(16) | NULLABLE | |
| `start_date` | Date | NULLABLE | |
| `end_date` | Date | NULLABLE | |

**Unique**: `(scheme, identifier, legislature)`

---

### `person_name`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `person_id` | UUID | FK, INDEX | |
| `type` | String(16) | DEFAULT 'name' | `name` / `alias` |
| `name` | String(255) | | |
| `normalized_name` | String(255) | INDEX | |
| `sort_key` | String(255) | NULLABLE, INDEX | |
| `start_date` | Date | NULLABLE | |
| `end_date` | Date | NULLABLE | |

---

### `organization`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `classification` | String(16) | INDEX | chamber/group/party/... |
| `name` | String(512) | | Full name |
| `normalized_name` | String(512) | INDEX | |
| `short_name` | String(64) | NULLABLE, INDEX | Acronym |
| `alt_labels` | JSON | NULLABLE | Historical names |
| `color` | String(16) | NULLABLE | Hex color for UI |
| `parent_id` | UUID | FK, NULLABLE | Parent org |
| `wikidata_qid` | String(32) | NULLABLE | Wikidata entity |
| `founding_date` | Date | NULLABLE | |
| `dissolution_date` | Date | NULLABLE | |
| `localised_labels` | JSON | NULLABLE | i18n |
| `chamber` | String(16) | NULLABLE | deputies/senate |
| **`previous_party_id`** | UUID | FK, NULLABLE | **Genealogy: predecessor** |
| **`successor_party_id`** | UUID | FK, NULLABLE | **Genealogy: successor** |

**Unique**: `(classification, normalized_name, founding_date)`

---

### `post`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `org_id` | UUID | FK, INDEX | → organization.id |
| `label` | String(255) | | Seat/role label |
| `role_type` | String(16) | DEFAULT 'seat' | seat / leadership |
| `importance` | Integer | DEFAULT 0 | Sort order |
| `maximum_memberships` | Integer | NULLABLE | Capacity |

---

### `membership`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `person_id` | UUID | FK, INDEX | |
| `org_id` | UUID | FK, INDEX | |
| `post_id` | UUID | FK, NULLABLE | |
| `on_behalf_of_id` | UUID | FK, NULLABLE | Party behind group |
| `chamber` | String(16) | INDEX | deputies/senate |
| `legislature` | String(16) | NULLABLE, INDEX | e.g., "2024" |
| `role` | String(255) | NULLABLE | e.g., "president" |
| `importance` | Integer | DEFAULT 0 | |
| `start_date` | Date | NULLABLE | |
| `end_date` | Date | NULLABLE | |
| `start_precision` | String(10) | NULLABLE | day/month/year |
| `end_precision` | String(10) | NULLABLE | |
| `start_reason` | String(32) | NULLABLE | |
| `end_reason` | String(32) | NULLABLE | |
| `confidence` | String(32) | DEFAULT 'derived' | Enum |
| `source_url` | String(1024) | NULLABLE | |
| `group_acronym_at_event` | String(64) | NULLABLE | Denormalized |
| `first_seen_at` | DateTime | DEFAULT now() | |
| `last_seen_at` | DateTime | DEFAULT now() | |

**Unique**: `(org_id, person_id, post_id, end_date)`

**Indexes**: `ix_membership_person_end (person_id, end_date)`, `ix_membership_org_end (org_id, end_date)`

---

### `evidence`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `membership_id` | UUID | FK, INDEX | |
| `type` | String(32) | | `official_ledger`, `profile`, etc. |
| `source_url` | String(1024) | NULLABLE | |
| `snapshot_hash` | String(64) | NULLABLE | SHA256 |
| `note` | Text | NULLABLE | |
| `observed_at` | DateTime | DEFAULT now() | |

---

### `asset_declaration`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `person_id` | UUID | FK, INDEX | |
| `year` | Integer | INDEX | e.g., 2024 |
| `asset_type` | String(64) | | real_estate, vehicle, etc. |
| `value_ron` | Float | NULLABLE | Value in RON |
| `description` | Text | NULLABLE | |
| `source_url` | String(1024) | NULLABLE | |
| `created_at` | DateTime | DEFAULT now() | |

---

### `event`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `type` | String(32) | INDEX | join/leave/switch_group/switch_party/... |
| `person_id` | UUID | FK, INDEX, NULLABLE | |
| `chamber` | String(16) | NULLABLE | |
| `from_org_id` | UUID | FK, NULLABLE | |
| `to_org_id` | UUID | FK, NULLABLE | |
| `post_id` | UUID | FK, NULLABLE | |
| `role` | String(255) | NULLABLE | |
| `event_date` | Date | NULLABLE, INDEX | |
| `precision` | String(10) | NULLABLE | |
| `detected_at` | DateTime | DEFAULT now() | |
| `reason` | String(32) | NULLABLE | Enum |
| `confidence` | String(32) | DEFAULT 'derived' | Enum |
| `group_acronym_at_event` | String(64) | NULLABLE | |
| `summary_ro` | Text | NULLABLE | Romanian summary |
| `summary_en` | Text | NULLABLE | English summary |
| `dedup_key` | String(255) | UNIQUE, NULLABLE | Idempotency |

**Event types**: `join`, `leave`, `switch_group`, `switch_party`, `group_founded`, `group_renamed`, `committee_join`, `committee_leave`, `role_change`, `mandate_start`, `mandate_end`

---

### `switch_wave`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `label` | String(255) | NULLABLE | e.g., "Post-2020 election wave" |
| `start_date` | Date | INDEX | Window start |
| `end_date` | Date | INDEX | Window end |
| `switch_count` | Integer | DEFAULT 0 | Switches in window |
| `trigger_type` | String(32) | NULLABLE | election/govt_formation/... |
| `trigger_event` | Text | NULLABLE | Human-readable |
| `legislature` | String(16) | NULLABLE, INDEX | |
| `chamber` | String(16) | NULLABLE | |
| `created_at` | DateTime | DEFAULT now() | |

**Index**: `(legislature, chamber)`

---

### `key_event`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `type` | String(32) | | legislature / election |
| `chamber` | String(16) | NULLABLE | |
| `start_date` | Date | NULLABLE | |
| `end_date` | Date | NULLABLE | |
| `label` | String(255) | NULLABLE | e.g., "2024" |

---

### `vacancy`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `chamber` | String(16) | | |
| `post_id` | UUID | FK, NULLABLE | |
| `start_date` | Date | NULLABLE | |
| `end_date` | Date | NULLABLE | |
| `reason` | String(32) | NULLABLE | |

---

### `match_review`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `person_a` | UUID | FK | |
| `person_b` | UUID | FK | |
| `score` | Float | DEFAULT 0.0 | |
| `reason` | Text | NULLABLE | |
| `status` | String(16) | DEFAULT 'pending' | pending/approved/rejected |
| `created_at` | DateTime | DEFAULT now() | |

---

### `coverage`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `chamber` | String(16) | | deputies/senate |
| `legislature` | String(16) | NULLABLE | |
| `period_start` | Date | NULLABLE | |
| `period_end` | Date | NULLABLE | |
| `completeness` | String(16) | DEFAULT 'partial' | full/partial/none |
| `note` | Text | NULLABLE | |

---

### `merge_audit`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `winner_id` | UUID | FK | |
| `loser_id` | UUID | | Original ID |
| `operations` | JSON | | List of {op, table, ...} |
| `created_at` | DateTime | DEFAULT now() | |
| `reverted` | Boolean | DEFAULT false | |

---

### `pipeline_run`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `source` | String(64) | INDEX | cdep/senat/wikidata/... |
| `status` | String(32) | | SUCCESS/FAILURE/... |
| `checksum` | String(64) | NULLABLE | |
| `idempotency_key` | String(255) | NULLABLE | |
| `started_at` | DateTime | DEFAULT now() | |
| `finished_at` | DateTime | NULLABLE | |
| `rows` | Integer | DEFAULT 0 | |
| `error` | Text | NULLABLE | |

---

### `fragment`
| Column | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | UUID | PK | |
| `model` | String(64) | INDEX | person/organization/... |
| `source_name` | String(64) | INDEX | cdep/senat/... |
| `source_id` | String(255) | NULLABLE | |
| `source_url` | String(1024) | NULLABLE | |
| `timestamp` | DateTime | DEFAULT now() | |
| `group_key` | String(255) | NULLABLE, INDEX | |
| `checksum` | String(64) | INDEX | |
| `data` | JSON | | Raw source data |
| `snapshot_path` | String(512) | NULLABLE | Local file |

---

## Roll-call vote tables (Wave 1)

| Table | Purpose | Key columns |
| --- | --- | --- |
| `vote` | One official roll-call vote published by a chamber | `source`, `native_vote_id`, `chamber`, `legislature`, `vote_time`, `title_raw`, the five official counts (`present`, `not_voting`, `yes`, `no`, `abstain`), `source_url`, `snapshot_hash`, `truth_contract_version`, `positions_incomplete`, `dedup_key` (unique) |
| `vote_position` | How one member voted in one vote | `vote_id`, `person_id` (**NOT NULL** - a position is never stored against a guessed identity), `idm_raw`, `cam_raw`, `name_raw`, `group_raw`, `raw_vote`, `choice` (`yes`/`no`/`abstain`/`not_voting`), `resolution_scheme`, `source_url`, `snapshot_hash`, `dedup_key` (unique) |
| `vote_import_run` | The audit trail of every import | `manifest_sha`, `parser_version`, `resolver_version`, `policy_version`, `applied`, the seen/written counts, `unresolved_count`, `rejected_count`, `report` (the quarantine list) |
| `source_license` | The licence register - what may be republished | `source_name`, `license_id`, `redistributable`, `share_alike`, `attribution`, `verification_url`, `verification_quote`, `verified_on` |

Rules enforced by the schema and the audit:

* `vote_position.person_id` is mandatory; an unresolved official position is
  quarantined in `vote_import_run.report` instead of being stored.
* `choice` is normalised from the published token. `-` means **present but
  did not vote** (verified against vote 37526), not abstain.
* `dedup_key` values are deterministic: `<source>:<native_vote_id>` for a vote
  and `<vote_key>:<person_id>` for a position, so a re-import never
  duplicates and never depends on a timestamp.
* `source_license.redistributable = 1` is only allowed for `CC0-1.0`,
  `CC-BY-4.0` and `OGL-ROU-1.0` (database CHECK constraint).

---

## Enums (stored as strings)

| Enum | Values |
| --- | --- |
| `CHAMBERS` | `deputies`, `senate` |
| `ORG_CLASS` | `chamber`, `group`, `party`, `committee`, `bureau`, `delegation`, `friendship`, `other` |
| `CONFIDENCE` | `official_ledger`, `official_profile`, `derived`, `community` |
| `REASONS` | `CHANGED_PARTY`, `WHIP_REMOVED`, `WHIP_RESTORED`, `DIED`, `RESIGNED`, `BY_ELECTION`, `GENERAL_ELECTION`, `UNKNOWN` |
| `EVIDENCE_TYPES` | `official_ledger`, `profile`, `jo`, `intervention`, `scrutin`, `other` |
| `EVENT_TYPES` | `join`, `leave`, `switch_group`, `switch_party`, `group_founded`, `group_renamed`, `committee_join`, `committee_leave`, `role_change`, `mandate_start`, `mandate_end` |
| `WAVE_TRIGGERS` | `election`, `government_formation`, `party_congress`, `coalition_breakup`, `other` |
| `RUN_STATUS` | `SUCCESS`, `FAILURE`, `DATA_UNAVAILABLE`, `DATA_UNCHANGED` |
| `MATCH_STATUS` | `auto`, `review`, `unmatched`, `merged` |

---

## Key Relationships

```
Person 1──M Membership M──1 Organization
Person 1──M Membership M──1 Post
Person 1──M Membership M──1 Organization (on_behalf_of_id = party)
Person 1──M Event (person_id)
Event M──1 Organization (from_org_id, to_org_id)
Organization 1──M Organization (parent_id, previous_party_id, successor_party_id)
Membership 1──M Evidence
Vote 1──M VotePosition M──1 Person
```

---

## Indexes Summary

| Table | Index |
| --- | --- |
| `person` | `normalized_name`, `wikidata_qid`, `sort_key` |
| `person_identifier` | `scheme, identifier, legislature` (unique), `person_id` |
| `organization` | `classification`, `normalized_name`, `short_name`, `founding_date` (unique), `wikidata_qid` |
| `membership` | `person_id, end_date`, `org_id, end_date`, `org_id, person_id, post_id, end_date` (unique) |
| `event` | `type`, `person_id`, `event_date`, `dedup_key` (unique) |
| `switch_wave` | `start_date`, `end_date`, `legislature`, `chamber`, `(legislature, chamber)` |
| `coverage` | `chamber`, `legislature` |
| `evidence` | `membership_id` |
| `asset_declaration` | `person_id`, `year` |
| `vote` | `(chamber, legislature, vote_time)`, `dedup_key` (unique) |
| `vote_position` | `(person_id, choice)`, `dedup_key` (unique) |
| `source_license` | `source_name` (primary key) |

---

## Derived / Analytics Tables (not in ORM, computed on demand)

| Table | Purpose |
| --- | --- |
| `switch_wave` | Clustered party switches with trigger labels |
| `party_cohesion` | Switch rate per MP per year per party |
| `cross_chamber_career` | Persons with memberships in both chambers |
| `generational_shift` | Avg/median age per party per legislature |

*These are computed by `pipeline/analytics.py` and exposed via REST + GraphQL, not persisted as ORM models.*
