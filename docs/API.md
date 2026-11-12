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

### `GET /api/evidence/{evidence_id}`
Evidence detail with snapshot URL.

### `GET /api/about`
Project metadata, methodology, sources, licenses, coverage, freshness.

---

## Party Endpoints

### `GET /api/party/{short_name}?as_of=2024-12-21`
Party profile with membership counts and switch stats.

### `GET /api/party/{short_name}/movements?as_of=2024-12-21&limit=50`
Party movements (joins, switches, leaves).

### `GET /api/party/{short_name}/timeline?from=2024-12-21&to=2025-06-12`
Party group size timeline.

---

## Analytics Endpoints

### `GET /api/analytics/switch-waves?chamber=deputies&legislature=2024&window_days=30&min_switches=3`
Detect and store switch waves. Returns count created.

### `GET /api/analytics/waves/recompute`
Recompute all switch waves from scratch.

### `GET /api/analytics/switch-waves?chamber=deputies&legislature=2024`
List stored switch waves with filters.

### `GET /api/analytics/party-cohesion?legislature=2024`
Party cohesion index per party:
```json
{
  "data": [
    {
      "party_id": "...",
      "party_name": "PSD",
      "members": 490,
      "switches": 57,
      "switchers": 12,
      "avg_tenure_years": 14.9,
      "switch_rate_per_mp_per_year": 0.0078
    }
  ]
}
```

### `GET /api/analytics/cross-chamber`
Cross-chamber MPs:
```json
{
  "count": 17,
  "data": [
    {"person_id": "...", "name": "Ninel PEIA", "chambers": ["senate", "deputies"]}
  ]
}
```

### `GET /api/analytics/generational-shift?legislature=2024`
Generational shift per party:
```json
{
  "data": [
    {"party": "PSD", "mps_with_birth_dates": 56, "avg_age": 50.1, "median_age": 49}
  ]
}
```

---

## Admin Endpoints

### `POST /api/admin/poll`
Run one poll cycle. Requires `PARLAMENT_ADMIN_TOKEN` and `X-Admin-Token` header.

### `GET /api/health`
Health check with source freshness.

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
