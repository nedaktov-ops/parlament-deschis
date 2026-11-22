---
id: GEN-ROUTES
type: reference
title: "Generated API route inventory"
description: "HTTP route decorators extracted from the backend entry points at the source commit."
status: active
authority: mirror
tags: [type/reference, lifecycle/active, domain/ops]
source_paths: [scripts/vault_sync.py, backend/routers/api.py, backend/main.py]
created: 2026-11-22T08:06:10+02:00
updated: 2026-11-22T08:06:10+02:00
source_commit: 5547795a7c800275bfd417007119255b402ac8d1
generated: true
generator: scripts/vault_sync.py
---

> DO NOT EDIT — regenerated. Edits are overwritten.

# Generated API route inventory

Extracted from the source-commit versions of `backend/routers/api.py` and `backend/main.py`.

Route decorators found: 51.

| Method | Path | Source |
|---|---|---|
| `GET` | `/` | `backend/main.py` |
| `GET` | `/about` | `backend/routers/api.py` |
| `POST` | `/admin/poll` | `backend/routers/api.py` |
| `GET` | `/analytics/committee-control` | `backend/routers/api.py` |
| `GET` | `/analytics/cross-chamber` | `backend/routers/api.py` |
| `GET` | `/analytics/generational-shift` | `backend/routers/api.py` |
| `GET` | `/analytics/ideology` | `backend/routers/api.py` |
| `GET` | `/analytics/party-cohesion` | `backend/routers/api.py` |
| `GET` | `/analytics/party-timeline` | `backend/routers/api.py` |
| `GET` | `/analytics/switch-leaderboard` | `backend/routers/api.py` |
| `GET` | `/analytics/switch-waves` | `backend/routers/api.py` |
| `GET` | `/analytics/vote-activity` | `backend/routers/api.py` |
| `GET` | `/analytics/vote-cohesion` | `backend/routers/api.py` |
| `GET` | `/analytics/waves` | `backend/routers/api.py` |
| `POST` | `/analytics/waves` | `backend/routers/api.py` |
| `GET` | `/analytics/waves/recompute` | `backend/routers/api.py` |
| `POST` | `/analytics/waves/recompute` | `backend/routers/api.py` |
| `GET` | `/api/analytics/ideology` | `backend/routers/api.py` |
| `GET` | `/api/votes/scorecard` | `backend/routers/api.py` |
| `GET` | `/chamber` | `backend/routers/api.py` |
| `GET` | `/committees` | `backend/routers/api.py` |
| `GET` | `/committees/{committee_id}/members` | `backend/routers/api.py` |
| `GET` | `/coverage` | `backend/routers/api.py` |
| `GET` | `/coverage/detailed` | `backend/routers/api.py` |
| `GET` | `/coverage/dimensions` | `backend/routers/api.py` |
| `GET` | `/coverage/summary` | `backend/routers/api.py` |
| `GET` | `/dashboard/stats` | `backend/routers/api.py` |
| `GET` | `/events/recent` | `backend/routers/api.py` |
| `GET` | `/evidence/{evidence_id}` | `backend/routers/api.py` |
| `GET` | `/health` | `backend/routers/api.py` |
| `GET` | `/health/live` | `backend/routers/api.py` |
| `GET` | `/health/ready` | `backend/routers/api.py` |
| `GET` | `/meta` | `backend/routers/api.py` |
| `GET` | `/movements` | `backend/routers/api.py` |
| `GET` | `/mps` | `backend/routers/api.py` |
| `GET` | `/parties` | `backend/routers/api.py` |
| `GET` | `/party/{short_name}` | `backend/routers/api.py` |
| `GET` | `/party/{short_name}/movements` | `backend/routers/api.py` |
| `GET` | `/party/{short_name}/timeline` | `backend/routers/api.py` |
| `GET` | `/persons` | `backend/routers/api.py` |
| `GET` | `/persons/{person_id}` | `backend/routers/api.py` |
| `GET` | `/persons/{person_id}/history` | `backend/routers/api.py` |
| `GET` | `/timeline` | `backend/routers/api.py` |
| `GET` | `/traseism/overview` | `backend/routers/api.py` |
| `GET` | `/traseism/summary` | `backend/routers/api.py` |
| `GET` | `/traseism/switches` | `backend/routers/api.py` |
| `GET` | `/votes` | `backend/routers/api.py` |
| `GET` | `/votes/scorecard` | `backend/routers/api.py` |
| `GET` | `/votes/{vote_id}` | `backend/routers/api.py` |
| `GET` | `/votes/{vote_id}/positions` | `backend/routers/api.py` |
| `GET` | `/{full_path:path}` | `backend/main.py` |

Regenerate with `scripts/vault_sync.py`.
