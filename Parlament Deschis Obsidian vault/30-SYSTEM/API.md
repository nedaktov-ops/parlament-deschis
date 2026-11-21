---
id: API
type: reference
title: "API surface — routes, deployment lag, counts and honest empty states"
description: "Distilled reference for the FastAPI read surface: OpenAPI path count, canonical vs double-prefixed legacy routes, local-vs-live differences, committee count definitions, vote/ideology empty states and export gaps."
status: active
authority: mirror
tags: [type/reference, lifecycle/active, domain/project]
source_paths: [docs/API.md, backend/routers/api.py, backend/routers/metrics.py, backend/graphql/schema.py]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# API

Base URL `/api`; all responses are JSON. Errors are plain FastAPI-style `{"detail": "..."}` (`application/json`), **not** RFC 7807 / `application/problem+json`. Observed codes: 401, 404, 405, 422, 502, 503.

State context: [RELEASE-AND-VERIFICATION](../10-STATE/RELEASE-AND-VERIFICATION.md). Architecture: [ARCHITECTURE](ARCHITECTURE.md).

## Surface at a glance

- **48 OpenAPI paths** on 2026-11-21 (40 at the 2026-11-19 check); the generated `openapi.json` is derived from source and must never be hand-edited.
- Core: `/api/meta`, `/chamber`, `/timeline`, `/persons[/{id}[/history]]`, `/movements`, `/events/recent`, `/coverage[/detailed]`, `/evidence/{id}`, `/about`.
- Party/traseism: `/api/party/{short_name}[/movements|/timeline]`, `/parties`, `/mps`, `/traseism/{overview,summary,switches}`.
- Analytics: `/api/analytics/{switch-waves,waves,party-timeline,switch-leaderboard,party-cohesion,cross-chamber,generational-shift,vote-cohesion,vote-activity,ideology}`; dashboard and health routes (`/api/dashboard/stats`, `/api/health`, `/health/live`, `/health/ready`).
- Exports: `/api/export/popolo` and `/api/export/{dataset}.csv` for `persons`, `organizations`, `posts`, `memberships`, `events`. GraphQL playground at `GET /graphql`, POST queries at `/graphql`.

## Canonical vs legacy routes — local vs live

Some handlers are registered at a canonical path and also reachable through a **double-prefixed legacy alias** (`/api/api/...`, kept out of the schema). Local source and the live host can disagree:

| Route | Local source | Live host (verified 2026-11-21) |
| --- | --- | --- |
| `/api/votes/scorecard` | Static path is reordered ahead of `/api/votes/{vote_id}` at import, so it returns the scorecard shape | Still serves the single-vote shape (`data: null`); use `/api/api/votes/scorecard` for the scorecard until redeployed |
| `/api/analytics/ideology` | Registered at the canonical path | 404; the legacy `/api/api/analytics/ideology` serves it |

`meta` from `_analytics_meta` is `{"generated_at": <per-request ISO timestamp>, "count": <rows returned>}`. Source responses include it on `vote-cohesion` / `vote-activity`; **the live deployment predates that field and omits it**. Re-check after the next deployment before relying on any canonical path above.

## Three different committee counts

All three are valid; they answer different questions (live-verified 2026-11-19):

| Field / endpoint | Value | Definition |
| --- | ---: | --- |
| `/api/dashboard/stats` → `data.committees` | 26 | All `organization` rows classified `committee` in the corpus |
| `/api/committees` (array length) | 23 | Committees with active dated memberships |
| `/api/analytics/committee-control` → `data.total_committees` | 9 | Committees with a dated `role='presedinte'` chair (across 5 parties) |

Bureau data is not separately ingested; `/api/committees/{id}/members` returns the dated ledger.

## Vote and ideology endpoints — honest empty states

The published corpus carries **no roll-call vote rows and no CHES ideology rows**. Endpoints return HTTP 200 with `{"status":"ok","data_exists":false,"data":[]}` — `data: null` for the single-vote endpoint — never 404 or 500. An empty `data` array is *not* a zero count. `/api/analytics/party-cohesion` similarly answers `status: "unavailable"` with a reason rather than an empty-but-success shape.

- `/api/votes` params: `chamber`, `legislature`, `from`, `to`, `limit` (1–200), `offset`. A populated row has `native_vote_id`, `vote_time`, the five official counts, `source_url`, `positions_incomplete`.
- `/api/votes/{vote_id}` looks up by `native_vote_id`, not the numeric id. `/api/votes/{vote_id}/positions` lists normalised choices (`-` means present but did not vote, not abstain).
- Date bounds accept ISO `YYYY-MM-DD` or published `DD.MM.YYYY`, compared as calendar dates. An unparseable bound or `to < from` returns **422**; `vote_time` itself is `DD.MM.YYYY HH:MM`.
- `/api/analytics/ideology` serves 0–10 CHES scales (`lrgen`, `galtan`, `eu_position`, …); with no CHES rows, party positions are not invented.

There are **no vote or ideology fields in the GraphQL schema and no votes/ideology CSV export**; do not assume those surfaces exist.

## Other surface notes

- An undocumented `GET /api/metrics` is served (Prometheus-format metrics from `backend/routers/metrics.py`) but is absent from `docs/API.md`; treat it as non-contractual.
- The CSP header on both hosts is **`Content-Security-Policy-Report-Only`** (byte-equal across Vercel and `backend/main.py`), so it reports rather than blocks. See [DEPLOYMENT](DEPLOYMENT.md).
- The two write routes (`POST /api/admin/poll`, wave detection/recompute) require `X-Admin-Token` and `PARLAMENT_ADMIN_TOKEN`; wave reads (`/api/analytics/switch-waves`) are public and read-only.
