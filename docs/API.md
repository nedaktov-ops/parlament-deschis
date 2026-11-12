# API Reference

The read API is a FastAPI application served by uvicorn. It answers as-of questions from
the local SQLite database; it never scrapes the chamber websites at request time.

- Base URL (local): `http://127.0.0.1:8000`
- All endpoints below are prefixed with `/api`
- Interactive docs: `/docs`
- OpenAPI schema: `/openapi.json`
- Content type: `application/json; charset=utf-8` (exports: JSON or `text/csv`)
- Dates: ISO 8601 `YYYY-MM-DD`; timestamps are ISO 8601 with timezone
- Romanian diacritics are preserved verbatim (UTF-8)

Examples use:

```bash
BASE=http://127.0.0.1:8000
```

> **Implementation note.** Read routes live in `backend/routers/api.py`; exports live in
> `backend/routers/exports.py`. `/openapi.json` is always the authoritative list for a
> running build.

---

## Conventions

### Chambers

`chamber` is one of:

| Value | Meaning |
| --- | --- |
| `deputies` | Camera Deputaților |
| `senate` | Senat |

### As-of semantics

Membership intervals are **end-exclusive**:

```text
start_date <= as_of AND (end_date IS NULL OR end_date > as_of)
```

`end_date` is the first day the tenure is no longer active. A same-day group switch is
resolved to the new group.

### Errors

| Status | When |
| --- | --- |
| `404 Not Found` | Person or evidence id does not exist. |
| `422 Unprocessable Entity` | Invalid date, invalid enum, out-of-range limit, or `to < from`. |
| `500 Internal Server Error` | Unhandled server/database error. |
| `503 Service Unavailable` | Admin poll requested while `PARLAMENT_ADMIN_TOKEN` is unset. |

FastAPI returns errors as:

```json
{"detail": "invalid date: 2024-13-01"}
```

---

## Meta

### `GET /api/meta`

Returns the legislature index and the known organization groups.

**Parameters:** none.

**Response**

```json
{
  "legislatures": {
    "2024": {"label": "2024", "start": "2024-12-21", "end": null},
    "2020": {"label": "2020", "start": "2020-12-21", "end": "2024-12-21"}
  },
  "groups": [
    {
      "id": "…",
      "name": "Grupul parlamentar al Partidului Social Democrat",
      "short_name": "PSD",
      "classification": "group",
      "color": "#E63946",
      "localised_labels": {"name": {"ro": "Partidul Social Democrat", "en": "Social Democratic Party"}}
    }
  ]
}
```

```bash
curl -s "$BASE/api/meta" | jq
```

---

## Chamber composition

### `GET /api/chamber`

Composition of one chamber on a date: groups, seat counts, and member lists.

**Parameters**

| Name | In | Type | Default | Notes |
| --- | --- | --- | --- | --- |
| `chamber` | query | string | `deputies` | `deputies` or `senate`. |
| `as_of` | query | date | today | ISO `YYYY-MM-DD`. |

**Response**

```json
{
  "chamber": "deputies",
  "as_of": "2026-06-15",
  "total": 330,
  "groups": [
    {
      "short_name": "PSD",
      "org": {
        "id": "…",
        "name": "Grupul parlamentar al Partidului Social Democrat",
        "short_name": "PSD",
        "classification": "group",
        "color": "#E63946",
        "localised_labels": {"name": {"ro": "Partidul Social Democrat", "en": "Social Democratic Party"}}
      },
      "count": 120,
      "members": [
        {"person_id": "…", "name": "Ponta Victor-Viorel", "role": "leader"}
      ],
      "color": "#E63946"
    }
  ]
}
```

Groups are sorted by descending count. `total` is the sum of group counts, not the
constitutional seat count.

```bash
curl -s "$BASE/api/chamber?chamber=senate&as_of=2026-06-15" | jq
```

---

## Timeline

### `GET /api/timeline`

Group-size series over an interval, plus group-switch events in that interval.

**Parameters**

| Name | In | Type | Default | Notes |
| --- | --- | --- | --- | --- |
| `chamber` | query | string | `deputies` | `deputies` or `senate`. |
| `from` | query | date | 1 January of the current year | ISO date. |
| `to` | query | date | today | ISO date. Must be `>= from`. |
| `step_days` | query | int | `30` | `1…365`. The final date is always included. |

**Response**

```json
{
  "chamber": "deputies",
  "dates": ["2026-01-01", "2026-01-31", "…"],
  "totals": [330, 329, "…"],
  "groups": {
    "PSD": [120, 119, "…"],
    "PNL": [80, 80, "…"]
  },
  "switches": [
    {
      "id": "…",
      "type": "switch_group",
      "person": {"id": "…", "name": "Ponta Victor-Viorel"},
      "chamber": "deputies",
      "from_org": {"id": "…", "name": "…", "short_name": "PSD", "classification": "group", "color": "#E63946"},
      "to_org": {"id": "…", "name": "…", "short_name": "UPR", "classification": "group", "color": "#6A4C93"},
      "event_date": "2026-06-15",
      "precision": "2026-06-15",
      "reason": "CHANGED_PARTY",
      "confidence": "official_ledger",
      "summary_ro": "Ponta Victor-Viorel a trecut de la PSD la UPR",
      "summary_en": "Ponta Victor-Viorel moved from PSD to UPR",
      "detected_at": "2026-06-15T10:00:00+00:00"
    }
  ]
}
```

Every series array has the same length as `dates`.

```bash
curl -s "$BASE/api/timeline?chamber=deputies&from=2024-12-21&to=2026-11-12&step_days=30" | jq
```

---

## Persons

### `GET /api/persons`

Search persons by name.

**Parameters**

| Name | In | Type | Default | Notes |
| --- | --- | --- | --- | --- |
| `q` | query | string | none | Case-insensitive substring match on canonical/normalized name. Omit to list persons. |
| `chamber` | query | string | none | `deputies` or `senate`; filters to people with a membership in that chamber. |
| `limit` | query | int | `50` | `1…500`. |

**Response**

```json
[
  {
    "id": "fa70618a-e482-4592-97d4-560f20f55d19",
    "name": "Chiriţă Răzvan-Mirel",
    "birth_date": null,
    "wikidata_qid": null,
    "chambers": ["deputies"],
    "match_status": "unmatched"
  }
]
```

Search covers canonical names and stored normalized names; aliases are available in the
person detail. Results are not ranked by relevance.

```bash
curl -s "$BASE/api/persons?q=ponta&chamber=deputies&limit=10" | jq
```

### `GET /api/persons/{person_id}`

Full person record: identifiers, memberships, events, and evidence.

**Parameters**

| Name | In | Type | Notes |
| --- | --- | --- | --- |
| `person_id` | path | string | Person UUID. |

**Response**

```json
{
  "id": "…",
  "name": "Ponta Victor-Viorel",
  "birth_date": "1972-09-20",
  "wikidata_qid": "Q…",
  "match_status": "auto",
  "identifiers": [
    {"scheme": "cdep_idm", "identifier": "12345", "legislature": "2024"},
    {"scheme": "senat_guid", "identifier": "007FDD23-…", "legislature": "2020"}
  ],
  "memberships": [
    {
      "id": "…",
      "org": {"id": "…", "name": "…", "short_name": "PSD", "classification": "group", "color": "#E63946", "localised_labels": null},
      "party": {"id": "…", "name": "Partidul Social Democrat", "short_name": "PSD", "classification": "party", "color": "#E63946", "localised_labels": null},
      "chamber": "deputies",
      "legislature": "2024",
      "role": "member",
      "start_date": "2024-12-21",
      "end_date": "2026-06-15",
      "start_precision": "2024-12-21",
      "end_precision": "2026-06-15",
      "confidence": "official_ledger",
      "source_url": "https://www.cdep.ro/…"
    }
  ],
  "events": [
    {
      "id": "…",
      "type": "switch_group",
      "person": {"id": "…", "name": "Ponta Victor-Viorel"},
      "chamber": "deputies",
      "from_org": {"id": "…", "short_name": "PSD"},
      "to_org": {"id": "…", "short_name": "UPR"},
      "event_date": "2026-06-15",
      "precision": "2026-06-15",
      "reason": "CHANGED_PARTY",
      "confidence": "official_ledger",
      "summary_ro": "…",
      "summary_en": "…",
      "detected_at": "2026-06-15T10:00:00+00:00"
    }
  ],
  "evidence": [
    {
      "id": "…",
      "membership_id": "…",
      "type": "official_ledger",
      "source_url": "https://www.cdep.ro/…",
      "snapshot_hash": "95592641c8e9c579f4395833b23ce6d286f66ecaa940c1dd8ad6d1486e61152e",
      "snapshot_url": "/snapshots/cdep/95592641…html",
      "note": null,
      "observed_at": "2026-06-15T09:58:00+00:00"
    }
  ]
}
```

`404` if the id does not exist.

```bash
curl -s "$BASE/api/persons/fa70618a-e482-4592-97d4-560f20f55d19" | jq
```

### `GET /api/persons/{person_id}/history`

Deterministic change history for a person, derived from consecutive tenures and the
stored switch events. It answers “where did this person move, and when?”, not “who edited
the database?”.

**Parameters**

| Name | In | Type | Notes |
| --- | --- | --- | --- |
| `person_id` | path | string | Person UUID. |

**Response**

```json
{
  "person_id": "…",
  "history": [
    {
      "field": "group",
      "from": "PSD",
      "to": "UPR",
      "date": "2026-06-15",
      "org": "UPR",
      "event_type": "switch_group",
      "source_url": "https://www.cdep.ro/…"
    },
    {
      "field": "party",
      "from": "Partidul Social Democrat",
      "to": "Uniunea Populară Română",
      "date": "2026-06-15",
      "org": "UPR",
      "event_type": "switch_party",
      "source_url": "https://www.cdep.ro/…"
    },
    {
      "field": "role",
      "from": "member",
      "to": "leader",
      "date": "2026-06-15",
      "org": "UPR",
      "event_type": "role_change",
      "source_url": "https://www.cdep.ro/…"
    }
  ]
}
```

| Field | Meaning |
| --- | --- |
| `field` | `group`, `party`, or `role`. |
| `from` / `to` | Organization label or role before/after. |
| `date` | Change date (ISO); `null` when unknown. |
| `org` | Organization the change belongs to; optional for event-only rows. |
| `event_type` | `switch_group`, `switch_party`, `role_change`, or the stored event type. |
| `source_url` | Official page when known; `null` for event-only rows. |

Rows are newest first, with `null` dates last. Derived rows are deduplicated against
stored switch events, so the same switch is not listed twice. `404` if the person does
not exist.

```bash
curl -s "$BASE/api/persons/fa70618a-e482-4592-97d4-560f20f55d19/history" | jq
```

---

## Movements and events

### `GET /api/movements`

Party/group switching events, newest first.

**Parameters**

| Name | In | Type | Default | Notes |
| --- | --- | --- | --- | --- |
| `person_id` | query | string | none | Restrict to one person. |
| `chamber` | query | string | none | `deputies` or `senate`. |
| `from` | query | date | `1990-01-01` | Inclusive lower bound. |
| `to` | query | date | today | Inclusive upper bound. |
| `limit` | query | int | `200` | `1…1000`. |

**Response:** array of serialized events (`switch_group` and `switch_party` only).

```bash
curl -s "$BASE/api/movements?chamber=senate&from=2024-01-01&limit=20" | jq
```

### `GET /api/events/recent`

Most recent events of any type, ordered by event date then detection time.

**Parameters**

| Name | In | Type | Default | Notes |
| --- | --- | --- | --- | --- |
| `limit` | query | int | `50` | `1…500`. |

**Response:** array of serialized events, including `join`, `leave`, `switch_group`,
`switch_party`, `group_founded`, `group_renamed`, and other derived types.

```bash
curl -s "$BASE/api/events/recent?limit=40" | jq
```

---

## Coverage

### `GET /api/coverage`

Coverage matrix per chamber and legislature.

**Parameters:** none.

**Response**

```json
[
  {
    "chamber": "deputies",
    "legislature": "2024",
    "period_start": "2024-12-21",
    "period_end": null,
    "completeness": "partial",
    "note": "152 of ~330 seats ingested.",
    "persons": 120
  }
]
```

`completeness` is `full`, `partial`, or `none`. If the `coverage` table is empty, the API
derives `partial`/`none` from the presence of memberships; the `coverage` step persists the
full calculation (including `full`). Its CLI subcommand is not wired in this checkout —
`pipeline.coverage` is implemented and used by the API/tests.

```bash
curl -s "$BASE/api/coverage" | jq
```

---

## Evidence

### `GET /api/evidence/{evidence_id}`

One citation record, including a resolvable archived-copy URL when a snapshot exists.

**Parameters**

| Name | In | Type | Notes |
| --- | --- | --- | --- |
| `evidence_id` | path | string | Evidence UUID. |

**Response**

```json
{
  "id": "…",
  "membership_id": "…",
  "type": "official_ledger",
  "source_url": "https://www.cdep.ro/ords/pls/parlam/structura2015.gp?cam=2&leg=2024&idg=1",
  "snapshot_hash": "95592641c8e9c579f4395833b23ce6d286f66ecaa940c1dd8ad6d1486e61152e",
  "snapshot_url": "/snapshots/cdep/95592641c8e9c579f4395833b23ce6d286f66ecaa940c1dd8ad6d1486e61152e.html",
  "note": null,
  "observed_at": "2026-06-15T09:58:00+00:00"
}
```

`snapshot_url` is `null` when no archived fragment matches the checksum or source URL. In
that case the UI offers only the live original — it never fabricates an archive link.

`404` if the id does not exist.

```bash
curl -s "$BASE/api/evidence/<evidence-id>" | jq
```

---

## Health

### `GET /api/health`

Latest pipeline run per source, plus a check timestamp.

**Parameters:** none.

**Response**

```json
{
  "status": "ok",
  "sources": {
    "cdep": {
      "status": "SUCCESS",
      "started_at": "2026-11-12T09:00:00+00:00",
      "finished_at": "2026-11-12T09:03:12+00:00",
      "rows": 330,
      "error": null
    },
    "senat": {"status": "never_run"},
    "checked_at": "2026-11-12T10:00:00+00:00"
  }
}
```

Source `status` values: `SUCCESS`, `FAILURE`, `DATA_UNAVAILABLE`, `DATA_UNCHANGED`, or
`never_run`.

```bash
curl -s "$BASE/api/health" | jq
```

---

## About

### `GET /api/about`

Machine-readable version of the in-app About modal: methodology summary, sources,
coverage, and licenses.

**Parameters:** none.

**Response**

```json
{
  "name": "Parlament Deschis",
  "version": "0.1.0",
  "description": "Romanian Parliament transparency tracker — party/group/committee memberships 1990→present, dated and source-cited.",
  "project_url": "https://github.com/parlament-deschis",
  "methodology": {
    "ro": ["Fiecare mandat are date de început/sfârșit, precizie temporală…"],
    "en": ["Every tenure carries start/end dates, temporal precision…"]
  },
  "sources": [
    {
      "name": "Camera Deputaților",
      "url": "https://www.cdep.ro",
      "note": "Group membership ledgers and deputy profiles (official)."
    },
    {
      "name": "Senatul României",
      "url": "https://www.senat.ro",
      "note": "Senator profiles and parliamentary group listings (official)."
    },
    {
      "name": "Wikidata",
      "url": "https://www.wikidata.org",
      "note": "Cross-chamber person identity reconciliation (community)."
    }
  ],
  "licenses": {
    "code": "AGPL-3.0-or-later",
    "data": "CC-BY-4.0",
    "code_url": "https://www.gnu.org/licenses/agpl-3.0.html",
    "data_url": "https://creativecommons.org/licenses/by/4.0/"
  },
  "coverage": [ … same rows as /api/coverage … ],
  "freshness": { … same shape as /api/health sources … },
  "generated_at": "2026-11-12T10:00:00+00:00"
}
```

The About modal uses the same endpoint, so the in-app methodology and licenses cannot
drift from the API.

```bash
curl -s "$BASE/api/about" | jq
```

---

## Exports

### `GET /api/export/popolo`

Popolo 1.0 JSON document for the requested scope.

**Parameters**

| Name | In | Type | Default | Notes |
| --- | --- | --- | --- | --- |
| `chamber` | query | string | none | `deputies` or `senate`. |
| `legislature` | query | string | none | e.g. `2024`. |

**Response shape**

```json
{
  "meta": {
    "generated_at": "2026-11-12T10:00:00+00:00",
    "generator": "Parlament Deschis",
    "project_url": "https://github.com/parlament-deschis",
    "popolo_version": "1.0",
    "code_license": "AGPL-3.0-or-later",
    "data_license": "CC-BY-4.0",
    "scope": {"chamber": "deputies", "legislature": "2024"},
    "counts": {"persons": 120, "organizations": 37, "posts": 0, "memberships": 152, "events": 132}
  },
  "persons": [ … ],
  "organizations": [ … ],
  "posts": [ … ],
  "memberships": [ … ],
  "events": [ … ]
}
```

Field lists are in the [Export schema](#export-schema) section. Scope filters apply to
every section, so foreign keys in `memberships` and `events` point only at included
persons/organizations.

```bash
curl -s "$BASE/api/export/popolo?chamber=deputies&legislature=2024" \
  -o popolo.json
```

### `GET /api/export/{dataset}.csv`

One CSV dataset.

**Path parameters:** `dataset` ∈ `persons`, `organizations`, `posts`, `memberships`,
`events`.

**Query parameters:** `chamber`, `legislature` (same as Popolo).

**Response:** `text/csv; charset=utf-8`, header row, UTF-8 without BOM, Romanian
diacritics preserved. List/dict fields are serialized as JSON strings. The response
carries `Content-Disposition: attachment; filename="{dataset}.csv"`.

**Errors**

| Status | Meaning |
| --- | --- |
| `404` | `dataset` is not one of the five supported names (`unknown dataset: …`). |
| `422` | `chamber` or `legislature` fails validation. |

```bash
curl -s "$BASE/api/export/memberships.csv?chamber=senate&legislature=2024" \
  -o memberships.csv
```

---

## Admin

### `POST /api/admin/poll`

Trigger one live poll cycle. This is the only write endpoint on the API surface.

**Headers**

| Header | Required | Value |
| --- | --- | --- |
| `X-Admin-Token` | yes | Must equal the `PARLAMENT_ADMIN_TOKEN` environment variable. |

**Parameters:** none required; an optional `legislature` query parameter selects the term
(default `2024`).

**Responses**

| Status | Meaning |
| --- | --- |
| `200` | Poll cycle completed. Body: `{"status": "ok", "legislature": "2024", "results": {…}}`, where `results` is the poller's per-source summary. |
| `401` | Token missing or does not match `PARLAMENT_ADMIN_TOKEN`. |
| `502` | The poll cycle raised an exception before completing. |
| `503` | Admin polling is disabled because `PARLAMENT_ADMIN_TOKEN` is unset. |

```bash
curl -s -X POST "$BASE/api/admin/poll?legislature=2024" \
  -H "X-Admin-Token: $PARLAMENT_ADMIN_TOKEN" | jq
```

---

## Export schema

The JSON and CSV exports share the same field contract (`pipeline/export.py`).

### `persons`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Person UUID. |
| `name` | string | Canonical name. |
| `sort_name` | string \| null | Order-insensitive sort key. |
| `birth_date` | date \| null | ISO date. |
| `wikidata_qid` | string \| null | QID when known. |
| `match_status` | string | `auto`, `review`, `unmatched`, `merged`. |
| `identifiers` | array | `{scheme, identifier, legislature}`. In CSV: `scheme:identifier (legislature)` joined by `; `. |
| `other_names` | array | `{name, note}` aliases (JSON only). |

### `organizations`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Organization UUID. |
| `name` | string | Official label. |
| `short_name` | string \| null | Acronym. |
| `classification` | string | `chamber`, `group`, `party`, `committee`, `bureau`, `delegation`, `friendship`, `other`. |
| `parent_id` | string \| null | Parent organization. |
| `chamber` | string \| null | `deputies` or `senate`. |
| `color` | string \| null | Display color. |
| `founding_date` | date \| null | ISO date. |
| `dissolution_date` | date \| null | ISO date. |
| `wikidata_qid` | string \| null | QID when known. |
| `alt_labels` | array | Former names/aliases. |
| `localised_labels` | object \| null | `{"name": {"ro": …, "en": …}}` (JSON only). |

### `posts`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Post UUID. |
| `organization_id` | string | Organization UUID. |
| `label` | string | Post label. |
| `role` | string | `seat` or `leadership`. |
| `importance` | integer | Ordering hint. |
| `maximum_memberships` | integer \| null | Optional cap. |

### `memberships`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Membership UUID. |
| `person_id` | string | Person UUID. |
| `organization_id` | string | Organization UUID. |
| `post_id` | string \| null | Post UUID. |
| `on_behalf_of_id` | string \| null | Party behind a group membership. |
| `role` | string \| null | Role within the organization. |
| `legislative_period_id` | string \| null | Legislature key, e.g. `2024`. |
| `chamber` | string | `deputies` or `senate`. |
| `start_date` | date \| null | Inclusive start. |
| `end_date` | date \| null | **Exclusive** end. |
| `start_precision` | string \| null | `YYYY-MM-DD`, `YYYY-MM`, `YYYY`. |
| `end_precision` | string \| null | Same. |
| `start_reason` | string \| null | e.g. `GENERAL_ELECTION`. |
| `end_reason` | string \| null | e.g. `CHANGED_PARTY`. |
| `confidence` | string | `official_ledger`, `official_profile`, `derived`, `community`. |
| `source_url` | string \| null | Official page. |
| `group_acronym_at_event` | string \| null | Group acronym at the time. |
| `first_seen_at` | timestamp | Observation time. |
| `last_seen_at` | timestamp | Last observation time. |

### `events`

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Event UUID. |
| `type` | string | See event types in [docs/DATA-MODEL.md](DATA-MODEL.md). |
| `person_id` | string \| null | Null for organization-only events. |
| `chamber` | string \| null | `deputies` or `senate`. |
| `from_organization_id` | string \| null | Source organization. |
| `to_organization_id` | string \| null | Destination organization. |
| `post_id` | string \| null | Post, when relevant. |
| `role` | string \| null | Role, when relevant. |
| `date` | date \| null | Event date (CSV column `date`; DB column `event_date`). |
| `precision` | string \| null | Date precision. |
| `reason` | string \| null | Reason enum. |
| `confidence` | string | Confidence enum. |
| `summary_ro` | string \| null | Romanian summary. |
| `summary_en` | string \| null | English summary. |

### CSV field order

```text
persons:       id,name,sort_name,birth_date,wikidata_qid,match_status,identifiers
organizations: id,name,short_name,classification,chamber,parent_id,color,founding_date,dissolution_date,wikidata_qid,alt_labels
posts:         id,organization_id,label,role,importance,maximum_memberships
memberships:   id,person_id,organization_id,post_id,on_behalf_of_id,role,legislative_period_id,chamber,start_date,end_date,start_precision,end_precision,start_reason,end_reason,confidence,source_url,group_acronym_at_event,first_seen_at,last_seen_at
events:        id,type,person_id,chamber,from_organization_id,to_organization_id,post_id,role,date,precision,reason,confidence,summary_ro,summary_en
```

### Example export

```bash
BASE=http://127.0.0.1:8000
mkdir -p exports
curl -s "$BASE/api/export/popolo?chamber=deputies&legislature=2024" -o exports/popolo.json
for ds in persons organizations posts memberships events; do
  curl -s "$BASE/api/export/$ds.csv?chamber=deputies&legislature=2024" \
    -o "exports/$ds.csv"
done

ls exports
# popolo.json  persons.csv  organizations.csv  posts.csv  memberships.csv  events.csv
```

> The CLI equivalent, `parlament export --out data/exports --format json,csv`, is part of
> the command contract but is not wired in this checkout. It would write the same six
> files using the same builders.
