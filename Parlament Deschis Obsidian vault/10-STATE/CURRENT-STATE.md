---
id: state-current
type: state
title: Current State — Authoritative at HEAD
description: What is true now at HEAD 96e6fdd; local fixes are unpushed and production still serves the pre-fix release.
status: active
authority: canonical
tags: [type/state, lifecycle/active, domain/project]
source_paths: [docs/CONTINUATION-STRATEGY-2026-11-21.md, docs/POST-INITIAL-AUDIT-2026-11-21.md, docs/COMPREHENSIVE-REVIEW-2026-11-21.md, docs/GAP-ANALYSIS-2026-11-21.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 96e6fdd
---

# Current State — authoritative at HEAD

> **Addendum (2026-11-21):** Re-anchored 2026-11-21 from `docs/CONTINUATION-STRATEGY-2026-11-21.md` §0. Vault mirror: [CONTINUATION-STRATEGY](../20-DIRECTION/CONTINUATION-STRATEGY.md).

This is the authoritative "what is true now" note. At the 2026-11-21 execution
close, `main` is `ad34bde` and production serves release
`data-20261121-votes-001` with 189 live votes. It is a hub: detailed tracking
lives in the linked notes, not duplicated here. See the dated
[EXECUTION-LOG](EXECUTION-LOG-2026-11-21.md) for the owner-gate evidence.

- [CONTINUATION-STRATEGY](../20-DIRECTION/CONTINUATION-STRATEGY.md) — method, gates, wave status and session boundary.
- [GAP-REGISTER](GAP-REGISTER.md) — open P0/P1/P2 gaps and next actions.
- [CONTRADICTIONS](CONTRADICTIONS.md) — R1–R11 adjudications and NOT PROVEN items.
- [RELEASE-AND-VERIFICATION](RELEASE-AND-VERIFICATION.md) — release pin, counts, gate commands.
- [GIT-POSITION](GIT-POSITION.md) — commits, CI conclusions, PR/issue state, deploy order.

## Production snapshot

- Live release pin `data-20261121-votes-001` (sha256 `eabdb857…`) — matches the
  latest GitHub release and contains 189 roll-call votes / 24,682 positions.
  Historical pin `data-20261117-T213500` was superseded on 2026-11-21.
- Published corpus: **3,388 persons**, **7,349 prepared memberships** (the raw
  release asset holds 7,358; nine duplicate closed stints are removed by
  `prepare_db.py`). Sources status `never_run`.
- Switches: **1,217 group + 785 party = 2,002** events across **142** waves.
  Committee counts: **26** organisations / **23** with active memberships /
  **9** with active chairs.
- **Production has no vote data** (`/api/votes` → `data_exists:false, total:0`;
  the pinned asset has 18 tables and zero vote tables).
- CI is **RED on main** and `main` has **no branch protection**; issue #14 is
  open with **11 failed data refreshes** (`cdep.ro` ConnectTimeout). Full
  detail: [GIT-POSITION](GIT-POSITION.md).

## Local-only fixes (not deployed)

HEAD `96e6fdd` carries eight unpushed commits (see [GIT-POSITION](GIT-POSITION.md)) that repair CI and the API but
are absent from Vercel/Render: the hooks-after-return fix in `Ideology.tsx`
(CI RED root cause), canonical `/api/analytics/ideology` and
`/api/votes/scorecard` routes with `meta`, calendar-aware vote date filters,
vote provenance backfill, a corrected doc-truth pattern, a widened UI gate and
accessibility fixes. Local gitignored working databases *do* hold votes, but
have never been released — see [GAP-REGISTER](GAP-REGISTER.md) (G-P0-01,
G-P0-03) and [GIT-POSITION](GIT-POSITION.md).

## Gates: local vs production

| Gate | Local HEAD `96e6fdd` | Production / CI on `main` |
| --- | --- | --- |
| pytest | 384 passed | not green on main (CI RED) |
| ruff | clean | `audit` job green |
| frontend lint | 0 errors (7 pre-existing warnings) | RED — `Ideology.tsx` rules-of-hooks |
| frontend build | exit 0 | not passing on main |
| strict audit | 275 known / 0 new | `audit` job green |
| doc-truth | 0 false claims | no CI gate |
| UI validation | 24/24, zero JavaScript errors, zero axe | 23/24 via live proxy (ideology 404) |
| Overall CI | n/a (local) | RED on `6b848f1` |

Exact commands and expected outputs:
[RELEASE-AND-VERIFICATION](RELEASE-AND-VERIFICATION.md).

## Stable technical facts

- One-way pipeline: polite fetch → SHA-256 fragments → parse → identity
  resolution → bitemporal tenures → events → as-of API → static React
  dashboard; runtime read-only, dataset baked into the image.
- Regenerated OpenAPI has **48 paths** (canonical vote/ideology routes); the
  deployed backend serves 48 paths with legacy double-prefixed aliases.
- Journal modes differ by lifecycle stage: shipped asset is **DELETE**,
  runtime/working copies are **WAL** (R3 in [CONTRADICTIONS](CONTRADICTIONS.md)).
- CSP is `Content-Security-Policy-Report-Only` (non-enforcing) and byte-equal
  between `vercel.json` and FastAPI; HSTS exists only on Vercel.
- Cache TTL is 300 s. Vercel serves a different bundle hash than local HEAD.

## What is explicitly NOT true in production

- The canonical vote/ideology routes and `meta` on analytics are **not** live.
- Vote data is **not** delivered to users; the 10× centrepiece is unreleased.
- The deployed bundle does **not** use single-prefix `/api` paths (the live
  helper double-prefixes to `/api/api/...`).
- "24/24 routes, zero JavaScript errors, zero axe" is proven **locally only**;
  production is NOT PROVEN (see [CONTRADICTIONS](CONTRADICTIONS.md)).
- No claim of green CI, branch protection, refreshed data, or a successful
  fresh deployment is true at this snapshot.
