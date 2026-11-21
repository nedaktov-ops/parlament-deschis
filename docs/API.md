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

### `GET /api/persons/{person_id}?as_of=2024-12-21`
Person detail with memberships, events, evidence.

- `as_of` (optional): ISO date. When supplied, memberships and committee
  tenures are limited to those active on that date and events to those dated on
  or before it; the response echoes `"as_of"`. An invalid date returns **422**;
  omitting it preserves the current whole-corpus behaviour (`"as_of": null`).

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

### `GET /api/coverage/dimensions`
Honest per-scope coverage across three independent dimensions — `mandates`,
`votes` and `biographies` — derived from the rows actually present in the
database. Returns a JSON array with one row per chamber / legislature scope
(20 scopes in the pinned release). Each row has `chamber`, `legislature`,
`period_start`, `period_end` and three objects `mandates`, `votes`,
`biographies`; each object carries `status` (`none` | `partial` | `full`) and
`count`, and `biographies` additionally carries `total` (persons in scope).
Real example row (pinned release, `deputies` / `1990`):

```json
{
  "chamber": "deputies",
  "legislature": "1990",
  "period_start": "1990-06-18",
  "period_end": "1992-10-08",
  "mandates": {"status": "full", "count": 448, "note": null},
  "votes": {"status": "none", "count": 0, "note": "No votes ingested in this scope."},
  "biographies": {
    "status": "partial", "count": 418, "total": 448,
    "note": "418 of 448 persons in scope have a known birth date."
  }
}
```

Status semantics, computed independently per dimension:

- **mandates** — distinct persons holding a group tenure in scope; `full` only
  at ≥ 90% of a verified seat count (seat count unknown ⇒ `partial`, no rows ⇒
  `none`). Reuses the legacy coverage logic unchanged.
- **votes** — rows in the `vote` table for the scope. No rows (or no vote table)
  ⇒ `none`. There is no published expected-total bar for votes, so this
  dimension is **never `full`**; populated scopes are `partial`.
- **biographies** — persons in scope with a known `birth_date` (`count`) over
  the same person set the mandate count uses (`total`). `full` only at 100%,
  otherwise `partial` / `none`.

> **Supersession note (2026-11-21):** this endpoint supersedes the mandate-only
> "full for all scopes" headline of `GET /api/coverage` and
> `GET /api/coverage/detailed`. Those two legacy payloads describe **mandates
> only** and remain unchanged; a scope whose mandates are `full` is never
> claimed here to have full votes or biographies. See also
> [Count definitions](#count-definitions) for why overlapping totals measure
> different things.

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

## Vote and ideology endpoints

Registered by `backend/routers/api.py` (router prefix `/api`). Shapes below are
read from the handlers, not guessed. The current published corpus has **no
roll-call vote rows and no CHES ideology rows**, so the honest empty result is
HTTP 200 with `data_exists: false` and `data: []` (for the single-vote endpoint,
`data: null`) — never 404 or 500. An empty `data` array is not a zero count.

Date bounds `from` / `to` (aliases for `from_date` / `to_date`) accept either ISO
`YYYY-MM-DD` or the published `DD.MM.YYYY` form; they are compared as calendar
dates. An unparseable bound or `to < from` returns 422. `vote_time` itself is
published as `DD.MM.YYYY HH:MM`.

### `GET /api/votes`
Roll-call vote list, newest `vote_time` first.
Params: `chamber` (`deputies`|`senate`), `legislature` (`YYYY`), `from`, `to`,
`limit` (default 50, 1–200), `offset` (default 0).
```json
{"status":"ok","data_exists":false,"data":[],"total":0,"offset":0,"limit":50}
```
A populated `data[]` row has: `id`, `native_vote_id`, `chamber`, `legislature`,
`vote_time`, `title_raw`, `present`, `not_voting`, `yes`, `no`, `abstain`,
`source_url`, `positions_incomplete`.

### `GET /api/votes/{vote_id}`
Single vote looked up by `native_vote_id` (not the numeric `id`). A missing vote
returns `{"status":"ok","data_exists":false,"data":null}`. A found vote adds
`official_vote_url`, `snapshot_hash`, `truth_contract_version`, `position_count`
and the other list fields to `data`.

### `GET /api/votes/{vote_id}/positions`
Individual positions, ordered by `name_raw`.
Params: `limit` (default 100, 1–500), `offset` (default 0), `choice`
(`yes`|`no`|`abstain`|`not_voting`). A missing vote returns `data: []`,
`total: 0`. Row fields: `person_id`, `name_raw`, `group_raw`, `choice`,
`resolution_scheme`, `source_url`, wrapped in
`status` / `data_exists` / `data` / `total` / `offset` / `limit`.

### `GET /api/votes/scorecard`
MP behaviour: loyalty / rebellion / participation, derived only from observed
positions (no attendance score). Params: `chamber`, `legislature`, `limit`
(default 50, 1–200), `offset`, `min_votes` (default 1, ≥ 0). Row fields:
`person_id`, `name_raw`, `canonical_name`, `group_raw`, `party`, `total_votes`,
`yes_votes`, `no_votes`, `abstain_votes`, `not_voting_votes`, `loyalty_pct`,
`rebellion_pct`, `participation_pct`.
**Routing note:** the canonical path was originally shadowed by
`GET /api/votes/{vote_id}` (declared earlier), which captured `scorecard` as a
`vote_id` and returned the single-vote shape. The handler module now reorders
`router.routes` at import time so the static path is matched first — in current
source `/api/votes/scorecard` resolves to the scorecard handler. A
double-prefixed legacy alias `GET /api/api/votes/scorecard` (kept out of the
schema) also returns the scorecard shape. **Live deployment lag (verified
2026-11-21):** the host still serves the old behaviour —
`/api/votes/scorecard` returns
`{"status":"ok","data_exists":false,"data":null}` while
`/api/api/votes/scorecard` returns the scorecard shape. Do not treat the current
live response at the canonical path as a scorecard; re-check after the next
deployment.

### `GET /api/analytics/vote-cohesion`
Party cohesion on roll-call votes. Params: `chamber`, `legislature`. Row fields:
`party`, `yes`, `no`, `abstain`, `not_voting`, `total_votes`, `yes_pct`,
`no_pct`, `abstain_pct`. Response also carries
`denominator: "resolved positions in scope"` and `meta`.

### `GET /api/analytics/vote-activity`
One bucket per published day. Params: `chamber`, `legislature`, `from`, `to`.
There is deliberately **no** `step_days` parameter. Bucket fields: `date`,
`votes`, `yes`, `no`, `abstain`, `present`; response also has `buckets` and
`meta`.

### `GET /api/analytics/ideology`
Party ideology covariates from CHES (CC BY 4.0), 0–10 scales: `lrgen`
(0 left → 10 right), `galtan` (0 TAN → 10 GAL), `eu_position` (0 opposed → 10
favoured), plus `lrecon`, `antielite_salience`, `people_vs_elite`. Param: `year`
(`YYYY`). Row fields: `party_name`, `partyfacts_id`, `survey_year`, `lrgen`,
`lrecon`, `galtan`, `eu_position`, `antielite_salience`, `people_vs_elite`,
wrapped in `status` / `data_exists` / `data` / `meta`. With no CHES rows the
response is `{"status":"ok","data_exists":false,"data":[],"meta":...}` — party
positions are not invented.
**Deployment caveat (verified 2026-11-21):** the canonical path is registered in
current source but the live host still returns 404 for it; the double-prefixed
legacy alias `GET /api/api/analytics/ideology` currently serves it. Re-check
after the next deployment before relying on the canonical path.

`meta` (from `_analytics_meta`) is `{"generated_at": <per-request ISO timestamp>,
"count": <rows actually returned>}`. The live deployment predates the `meta`
field on `vote-cohesion` / `vote-activity`, so those live responses currently omit
it; source responses include it.

There are **no** vote or ideology fields in the GraphQL schema
(`backend/graphql/schema.py` has zero matches for either term), and no
votes/ideology CSV in `GET /api/export/{dataset}.csv`; do not assume those
surfaces exist.

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
reference. All were present in the live `/openapi.json` at the 2026-11-19 check
(40 paths then; **48 paths on 2026-11-21**, including the vote and ideology
endpoints documented above):

| Endpoint | Purpose |
|---|---|
| `GET /api/dashboard/stats` | Dashboard counts (see the committee-count table above); `computed_at` is regenerated per request |
| `GET /api/health/live` | Liveness probe |
| `GET /api/health/ready` | Database-readiness probe (also the Render healthcheck path) |
| `GET /api/mps?as_of=&chamber=&legislature=` | MP biography cards, filterable/sortable (including by `committees`). Optional `as_of` (ISO date), `chamber` (`deputies`\|`senate`) and `legislature` (`YYYY`) scope the cards, their switch/committee aggregates and the displayed party. An invalid `as_of` returns **422**; omitting all three preserves the current whole-corpus behaviour. The response carries `total` and a `scope` echo. |
| `GET /api/parties` | Party list used by the UI |
| `GET /api/traseism/overview` | Traseism overview (`party`, `by_party`, `matrix`, `timing`) |
| `GET /api/traseism/summary` | Per-scope traseism summary |
| `GET /api/traseism/switches` | Dated switch events with filters |
| `GET /api/analytics/party-timeline` | Party group-size timeline |
| `GET /api/analytics/switch-leaderboard` | MPs ranked by switch count |
| `GET /api/export/report` | Aggregated transparency report |

## Count definitions

Three published totals need a label before they are compared: two different
"switch" definitions and two different "membership" artifacts. **These are
definitional differences, not data bugs.** Counts come from the release pinned
in `data/latest-release.txt`; read that file for the current tag rather than
hard-coding one here.

### Switch counts

| Definition | Count | Where it is published |
|---|---:|---|
| Group switches (`switch_group`) | 1,217 | `GET /api/export/report`, `GET /api/traseism/summary` |
| Party switches (`switch_party`) | 785 | Component of the dashboard total only; not a standalone published field |
| All switch events (group + party) | 2,002 | `GET /api/dashboard/stats` → `switches` |

`GET /api/dashboard/stats` counts **both** event types, so its `switches` value
is **2,002** (1,217 group + 785 party). `GET /api/export/report` and
`GET /api/traseism/summary` count **group switches only**, so they report
**1,217**. Evidence from current source:

- `backend/routers/api.py:1047-1049` — the stats query uses
  `Event.type.in_(["switch_group", "switch_party"])`.
- `backend/routers/exports.py:72` — the report total uses
  `Event.type == "switch_group"`.

The pinned release DB confirms the split: `switch_group=1217`,
`switch_party=785` (sum 2,002), as recorded in
`docs/AUDIT-RESOLUTIONS-2026-11-21.md` (R1).

### Membership counts

| Artifact | Count | Definition |
|---|---:|---|
| Raw release asset | 7,358 | Every membership row in the downloaded GitHub release asset named by `data/latest-release.txt` |
| Prepared runtime DB | 7,349 | The same corpus after `scripts/prepare_db.py` removes 9 duplicate closed stints; this is what the served API reports at `GET /api/health` and `GET /api/dashboard/stats` |

`scripts/prepare_db.py` collapses exact-duplicate membership stints (keeping
the lowest id and repointing their evidence rows) so the fail-fast unique
indexes can be created; the shipped corpus contained **9 duplicate closed
stints**. Evidence: `scripts/prepare_db.py` (`_dedupe_memberships` and the
`_create_partial_indexes` note) and the release pin in `data/latest-release.txt`.
The current-state figure for the served API is 7,349; the 7,358 figure is the
raw asset, not a contradictory count. This split is recorded in
`docs/AUDIT-RESOLUTIONS-2026-11-21.md` (R2).

> **Label note (2026-11-21):** These definitions supersede earlier unlabelled
> figures in this reference and in the README. A bare "switches" or
> "memberships" number in older prose did not say which definition it used;
> the numbers were correct for their own artifact, only unlabelled. Always
> use the definitions above when quoting them.

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
