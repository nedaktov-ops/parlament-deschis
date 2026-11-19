# API Reference

Base URL: `/api`

All endpoints return JSON. Errors are plain FastAPI-style JSON:
`content-type: application/json` with a `{"detail": "..."}` body. They are **not**
RFC 7807 / `application/problem+json` (verified with a live 404 on 2026-11-19:
`{"detail":"not found"}`). See [Error responses](#error-responses).

---

## Core Endpoints

### `GET /api/meta`
Returns legislatures and groups for UI initialization.

**Response**:
```json
{
  "legislatures": {
    "2024": {"label": "2024", "start": "2024-12-21", "end": null}
  },
  "groups": [{"id": "...", "name": "...", "short_name": "PSD", "color": "#E63946", ...}]
}
```

### `GET /api/chamber?chamber=deputies&as_of=2024-12-21`
Composition of a chamber at a given date.

**Query params**:
- `chamber` (required): `deputies` | `senate`
- `as_of` (optional): ISO date, default today

**Response**:
```json
{
  "chamber": "deputies",
  "as_of": "2024-12-21",
  "total": 330,
  "groups": [
    {"short_name": "PSD", "org": {...}, "count": 92, "members": [...], "color": "#E63946"}
  ]
}
```

### `GET /api/timeline?chamber=deputies&from=2024-12-21&to=2025-06-12&step_days=30`
Group size evolution over time.

### `GET /api/persons?q=popescu&chamber=deputies&limit=50`
Search persons by name.

### `GET /api/persons/{person_id}`
Person detail with memberships, events, evidence.

### `GET /api/persons/{person_id}/history`
Timeline of changes (memberships, events, etc.).

### `GET /api/movements?person_id=...&chamber=deputies&from=...&to=...&limit=200`
Events with optional filters.

### `GET /api/events/recent?limit=50`
Most recent events across all chambers.

### `GET /api/coverage`
Coverage matrix per chamber and legislature.

### `GET /api/coverage/detailed`
Returns the coverage matrix with per-scope membership totals, dated/source
percentages, switch totals, and the latest refresh time. Metrics are derived
when no persisted coverage rows exist. Percentage fields are `null` when their
denominator is zero.

### `GET /api/evidence/{evidence_id}`
Evidence detail with snapshot URL.

### `GET /api/about`
Project metadata, methodology, sources, licenses, coverage, freshness.

---

## Party Endpoints

### `GET /api/party/{short_name}?as_of=2024-12-21`
Party profile with members in the legislature active on `as_of` and dated
party-switch stats through that date. Switch fields are `null` when the corpus
has no dated party-switch records, rather than reporting an unsupported zero.

### `GET /api/party/{short_name}/movements?as_of=2024-12-21&limit=50`
Party movements (joins, switches, leaves) through the inclusive `as_of` date.

### `GET /api/party/{short_name}/timeline?from=2024-12-21&to=2025-06-12`
Party group size timeline.

---

## Analytics Endpoints

### `POST /api/analytics/waves?chamber=deputies&legislature=2024&window_days=30&min_switches=3`
Detect and persist switch waves for a scope. Requires the `X-Admin-Token` header
and `PARLAMENT_ADMIN_TOKEN`; returns the number of rows created.

### `POST /api/analytics/waves/recompute`
Delete and rebuild all stored switch waves from the current event ledger.
Requires the `X-Admin-Token` header and `PARLAMENT_ADMIN_TOKEN`.

### `GET /api/analytics/switch-waves?chamber=deputies&legislature=2024`
List stored switch waves with filters. This endpoint is read-only.

### `GET /api/analytics/party-cohesion?legislature=2024`
Party switching rate per party, based on dated party-switch events attributed
to group memberships. `switches` includes events entering or leaving a party;
`switchers` counts distinct people. The current corpus has no attributable
dated party-switch events, so the response is explicitly unavailable. An empty
`data` array must not be interpreted as zero switching:
```json
{
  "status": "unavailable",
  "data": [],
  "reason": "No dated party-switch events can be attributed to party memberships."
}
```

### `GET /api/analytics/cross-chamber?as_of=2025-01-14`
People with dated mandates in both chambers that started on or before `as_of`
(defaults to today). Mandates without a start date are excluded because they
cannot be placed on the timeline. `deputies` and `senate` list the recorded legislatures:
```json
{
  "status": "ok",
  "as_of": "2025-01-14",
  "count": 38,
  "data": [
    {
      "person_id": "...",
      "name": "Angel TÎLVĂR",
      "chambers": ["deputies", "senate"],
      "deputies": ["2016", "2024"],
      "senate": ["2004"]
    }
  ]
}
```

### `GET /api/analytics/generational-shift?legislature=2024&as_of=2025-01-14`
Age summaries by represented party. Party affiliation comes from group
membership `on_behalf_of` records; repeated group stints by the same person
are counted once per party. For a legislature, ages are measured at its end
(or today if ongoing), unless `as_of` is supplied.
```json
{
  "status": "ok",
  "as_of": "2025-01-14",
  "data": [
    {"party": "PSD", "mps_with_birth_dates": 121, "avg_age": 49.9, "median_age": 48}
  ]
}
```

Committee data is now part of the corpus (release pinned in
`data/latest-release.txt`). Three live counts measure different things and must
not be confused (all verified by GET on 2026-11-19):

| Endpoint / field | Value | What it counts |
|---|---:|---|
| `GET /api/dashboard/stats` → `data.committees` | 26 | **All** `organization` rows with `classification='committee'` in the corpus |
| `GET /api/committees` | 23 | Committees with active dated memberships (the array length) |
| `GET /api/analytics/committee-control` → `data.total_committees` | 9 | Committees with a dated `role='presedinte'` chair (5 parties) |

`GET /api/committees/{committee_id}/members` returns a committee's dated member
ledger. Bureau data is not separately ingested. This section formerly documented
an empty list pending ingest; that limitation no longer applies.

---

## Admin Endpoints

### `POST /api/admin/poll`
Run one poll cycle. Requires `PARLAMENT_ADMIN_TOKEN` and `X-Admin-Token` header.

### `GET /api/health`
Health check with database availability/counts and source freshness.

**Response** includes `status`, `database` (`status`, `persons`, and
`memberships`), and `sources` (the latest pipeline run per source).

---

## GraphQL Endpoint

### `POST /graphql`
GraphQL endpoint with playground at `GET /graphql`.

Example queries:
```graphql
{
  parties(classification: "party", limit: 5) {
    id
    shortName
    name
    color
    wikidataQid
    foundingDate
    dissolutionDate
    chamber
  }
}

{
  switchWaves(chamber: "deputies", limit: 10) {
    label
    startDate
    endDate
    switchCount
    triggerType
    triggerEvent
  }
}

{
  partyCohesion(legislature: "2024") {
    partyName
    members
    switches
    switchRatePerMpPerYear
  }
}
```

---

## Export Endpoints

### `GET /api/export/popolo?chamber=deputies&legislature=2024`
Popolo JSON export.

### `GET /api/export/{dataset}.csv?chamber=deputies&legislature=2024`
CSV exports: `persons`, `organizations`, `posts`, `memberships`, `events`.

---

## Additional live endpoints

These paths are served by the API but were missing from earlier versions of this
reference. All are present in the live `/openapi.json` (40 paths, checked
2026-11-19):

| Endpoint | Purpose |
|---|---|
| `GET /api/dashboard/stats` | Dashboard counts (see the committee-count table above); `computed_at` is regenerated per request |
| `GET /api/health/live` | Liveness probe |
| `GET /api/health/ready` | Database-readiness probe (also the Render healthcheck path) |
| `GET /api/mps` | MP biography cards, filterable/sortable (including by `committees`) |
| `GET /api/parties` | Party list used by the UI |
| `GET /api/traseism/overview` | Traseism overview (`party`, `by_party`, `matrix`, `timing`) |
| `GET /api/traseism/summary` | Per-scope traseism summary |
| `GET /api/traseism/switches` | Dated switch events with filters |
| `GET /api/analytics/party-timeline` | Party group-size timeline |
| `GET /api/analytics/switch-leaderboard` | MPs ranked by switch count |
| `GET /api/export/report` | Aggregated transparency report |

## Error responses

All errors use plain FastAPI `HTTPException` JSON with
`content-type: application/json`. A live 404 returns:

```json
{"detail":"not found"}
```

Validation and authorization errors share that shape — for example
`{"detail":"invalid date: not-a-date"}` (422) and
`{"detail":"invalid admin token"}` (401). There is no `type`, `title`, `status`
or `instance` wrapper, and no `application/problem+json` content type.

Codes observed in the live API / source: `401` (unauthorized), `404` (not
found), `405` (wrong method on a write route), `422` (validation), `502`
(upstream poll failed), `503` (admin disabled).
