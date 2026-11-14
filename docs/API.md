# API Reference

Base URL: `/api`

All endpoints return JSON. Errors follow RFC 7807 (`application/problem+json`).

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

Committee and bureau data are not included in the current corpus. The
`GET /api/committees` endpoint therefore returns an empty list until source
records are ingested; the frontend labels this limitation rather than showing
an empty chart as a zero result.

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
    previous { shortName }
    successor { shortName }
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

## Error Responses

All errors follow RFC 7807:
```json
{
  "type": "https://example.com/probs/validation-error",
  "title": "Invalid date",
  "status": 422,
  "detail": "invalid date: not-a-date",
  "instance": "/api/chamber"
}
```

Common codes: `400` (bad request), `401` (unauthorized), `404` (not found), `422` (validation), `500` (server error), `503` (admin disabled).
