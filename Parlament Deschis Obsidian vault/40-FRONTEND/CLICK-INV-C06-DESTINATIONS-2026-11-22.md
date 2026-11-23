---
id: CLICK-INV-C06
type: evidence
title: "Destination verification — C06 routes, endpoints and URLs (2026-11-22)"
description: "Code-evidence-only destination index for every in-app navigation target, API path and URL literal in frontend/src at commit 8811216; no network calls, no browser claims."
status: active
authority: derived
tags: [type/evidence, lifecycle/active, domain/frontend]
source_paths: [frontend/src/router.tsx, frontend/src/api/client.ts, backend/routers/exports.py, vercel.json]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# C06 — Destination verification (code evidence only)

Scope: repository at HEAD `88112168237e5c37841b785dccd2375f6cc40115` (short `8811216`).
Method: static reads of source only. **No network requests were made, no browser was used, and no URL is claimed to be live, reachable or correct.** Every verdict below is about what the code/configuration literally expresses. Relative Markdown links resolve from this vault folder to the repository.

---

## 1. Route-target table

Route tree: [`frontend/src/router.tsx`](../../frontend/src/router.tsx) lines 335–544. All 25 registered routes use `validateSearch: validateScopeSearch` (definition at router.tsx:43–56: `date` coerced by `isISODate()` or `localISODate()`, `chamber` restricted to `"senate"|"deputies"`, `legislature` restricted to `/^\d{4}$/`, unknown keys preserved via `...search`).

| Target (click site, exact file:line) | Verbatim quote | Destination definition (file:line) | Param / validateSearch shape | Verdict |
| --- | --- | --- | --- | --- |
| router.tsx:264 | `<NavLink to="/" …>` | router.tsx:341–346 `path: "/",` | no params; `validateScopeSearch` | WORKING-AS-CODED |
| router.tsx:267 | `<NavLink to="/traseism" …>` | router.tsx:392–397 `path: "/traseism",` | no params | WORKING-AS-CODED |
| router.tsx:270 | `<NavLink to="/leaderboard" …>` | router.tsx:414–419 `path: "/leaderboard",` | no params | WORKING-AS-CODED |
| router.tsx:273 | `<NavLink to="/demographics" …>` | router.tsx:421–426 `path: "/demographics",` | no params | WORKING-AS-CODED |
| router.tsx:276 | `<NavLink to="/committees" …>` | router.tsx:428–433 `path: "/committees",` | no params | WORKING-AS-CODED |
| router.tsx:279 | `<NavLink to="/compare" …>` | router.tsx:435–440 `path: "/compare",` | no params | WORKING-AS-CODED |
| router.tsx:282 | `<NavLink to="/coalitions" …>` | router.tsx:442–447 `path: "/coalitions",` | no params | WORKING-AS-CODED |
| router.tsx:285 | `<NavLink to="/mps" …>` | router.tsx:449–454 `path: "/mps",` | no params | WORKING-AS-CODED |
| router.tsx:288 | `<NavLink to="/report" …>` | router.tsx:463–468 `path: "/report",` | no params | WORKING-AS-CODED |
| router.tsx:291 | `<NavLink to="/parties" …>` | router.tsx:470–475 `path: "/parties",` | no params | WORKING-AS-CODED |
| router.tsx:294 | `<NavLink to="/party-timeline" …>` | router.tsx:477–482 `path: "/party-timeline",` | no params | WORKING-AS-CODED |
| router.tsx:297 | `<NavLink to="/institutional" …>` | router.tsx:364–369 `path: "/institutional",` | no params | WORKING-AS-CODED |
| router.tsx:300 | `<NavLink to="/coverage" …>` | router.tsx:399–404 `path: "/coverage",` | no params | WORKING-AS-CODED |
| router.tsx:303 | `<NavLink to="/senate-history" …>` | router.tsx:407–412 `path: "/senate-history",` | no params | WORKING-AS-CODED |
| router.tsx:306 | `<NavLink to="/legislature/2024" …>` | router.tsx:385–390 `path: "/legislature/$year",` | literal `2024` binds `$year`; matches no digit constraint in path, `validateScopeSearch` validates the *search* `legislature` key only | WORKING-AS-CODED |
| router.tsx:309 | `<NavLink to="/party/PSD" …>` | router.tsx:371–376 `path: "/party/$shortName",` | literal `PSD` binds `$shortName` | WORKING-AS-CODED |
| router.tsx:315 | `<NavLink to="/compare-mps" …>` | router.tsx:456–461 `path: "/compare-mps",` | no params | WORKING-AS-CODED |
| router.tsx:316 | `<NavLink to="/Voturi" …>` | router.tsx:484–489 `path: "/Voturi",` | no params; case-sensitive literal `V` | WORKING-AS-CODED |
| router.tsx:317 | `<NavLink to="/radar" …>` | router.tsx:491–496 `path: "/radar",` | no params | WORKING-AS-CODED |
| router.tsx:318 | `<NavLink to="/grafice" …>` | router.tsx:498–503 `path: "/grafice",` | no params | WORKING-AS-CODED |
| router.tsx:319 | `<NavLink to="/topuri" …>` | router.tsx:505–510 `path: "/topuri",` | no params | WORKING-AS-CODED |
| router.tsx:320 | `<NavLink to="/ideology" …>` | router.tsx:512–517 `path: "/ideology",` | no params | WORKING-AS-CODED |
| router.tsx:75 | `<Link to="/" search={{ date: localISODate(), … }}>` (NotFound) | router.tsx:341–346 `path: "/",` | search object supplies `date`, `chamber: undefined`, `legislature: undefined` | WORKING-AS-CODED |
| router.tsx:90 | `<Link to="/" search={{ date: localISODate(), … }}>` (RouteError) | router.tsx:341–346 `path: "/",` | same as above | WORKING-AS-CODED |
| router.tsx:245 | `to: "/person/$id",` (Search `onSelect`) | router.tsx:378–383 `path: "/person/$id",` | `params: { id }` at 246; `search: scope.searchFor()` at 247 | WORKING-AS-CODED |
| router.tsx:353 | `to: "/traseism",` inside `throw redirect({…})` | router.tsx:392–397 `path: "/traseism",` | explicit `search` at 354–358 | WORKING-AS-CODED |
| LiveDashboard.tsx:88 | `to: "/party/$shortName",` | router.tsx:371–376 | `params: { shortName }` at 89 | WORKING-AS-CODED |
| LiveDashboard.tsx:96 | `to: "/person/$id",` | router.tsx:378–383 | `params: { id }` at 97 | WORKING-AS-CODED |
| LiveDashboard.tsx:220 | `navigate({ to: "/parties", … })` | router.tsx:470–475 | no params | WORKING-AS-CODED |
| LiveDashboard.tsx:261 | `navigate({ to: "/mps", … })` | router.tsx:449–454 | no params | WORKING-AS-CODED |
| LiveDashboard.tsx:277 | `navigate({ to: "/traseism", … })` | router.tsx:392–397 | no params | WORKING-AS-CODED |
| LiveDashboard.tsx:300 | `navigate({ to: "/person/$id", … })` | router.tsx:378–383 | `params: { id }` same line | WORKING-AS-CODED |
| SwitchLeaderboard.tsx:161 | `to="/person/$id"` | router.tsx:378–383 | `params={{ id: row.person_id }}` at 162 | WORKING-AS-CODED |
| PartyComparison.tsx:167 | `to="/parties"` | router.tsx:470–475 | no params | WORKING-AS-CODED |
| MpComparison.tsx:195 | `to="/person/$id"` | router.tsx:378–383 | `params={{ id: selected[i]!.id }}` at 196 | WORKING-AS-CODED |
| Committees.tsx:34 | `to="/person/$id"` | router.tsx:378–383 | `params={{ id: member.person_id }}` at 35 | WORKING-AS-CODED |
| Committees.tsx:345 | `to="/person/$id"` | router.tsx:378–383 | `params={{ id: c.chair_person_id }}` at 346 | WORKING-AS-CODED |
| PartyTimeline.tsx:128 | `to="/parties"` | router.tsx:470–475 | no params | WORKING-AS-CODED |
| Mps.tsx:158 | `to="/person/$id"` | router.tsx:378–383 | `params={{ id: m.id }}` at 159 | WORKING-AS-CODED |
| LegislatureDetail.tsx:195 | `to: "/person/$id",` | router.tsx:378–383 | `params: { id: m.person.id }` at 196 | WORKING-AS-CODED |
| Parties.tsx:46 | `to: "/party/$shortName",` | router.tsx:371–376 | `params: { shortName }` same line | WORKING-AS-CODED |
| DashboardCard.tsx:81 | `<Link to={linkTo} search={searchParams} …>` | router.tsx — values supplied by LiveDashboard.tsx:140,151,162,174 (`/mps`, `/mps`, `/traseism`, `/committees`) | dynamic; all four literal values match registered routes | WORKING-AS-CODED |

**Unmatched navigation targets: none.** Every `to`/`to:` literal and every resolved `linkTo` value has a matching `path` in the route tree (router.tsx:341–517, children registered at 519–544).

**Registered routes with no inbound click target:** `/electoral` — defined at router.tsx:348 (`path: "/electoral",`) with no `<NavLink>`, `<Link>` or `navigate({ to: ... })` pointing at it in `frontend/src`. Its only code role is a source-side redirect at router.tsx:351–360. Searched: `frontend/src/**/*.ts`, `frontend/src/**/*.tsx` (full `to=`/`to:` sweep, see §5). This is explicitly whitelisted as `REACHABLE_OTHERWISE` in [`scripts/check_routes_nav.mjs`](../../scripts/check_routes_nav.mjs):13 (`["/electoral", "redirect-only route (router.tsx:322-336)"]`). All other 24 routes have at least one inbound target above.

---

## 2. API-path table

Client base: [`frontend/src/api/client.ts`](../../frontend/src/api/client.ts):487 `const BASE = "/api";` and 490 `const res = await fetch(\`${BASE}${path}\`);`. Every call below uses `get<T>()` (client.ts:489) → **HTTP GET**. Backend `api_router` prefix: [`backend/routers/api.py`](../../backend/routers/api.py):29 `router = APIRouter(prefix="/api")`. All matched decorators below are `@router.get(...)` → **HTTP GET**. Method agreement is noted per row.

| # | Client file:line + verbatim path | Effective URL | Backend definition file:line + verbatim decorator | Method (client → backend) | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | client.ts:473 ``get<MpsResponse>(`/mps…`)`` | `/api/mps` | api.py:277 `@router.get("/mps")` | GET → GET | WORKING-AS-CODED |
| 2 | client.ts:511 `get<MetaResponse>("/meta")` | `/api/meta` | api.py:217 `@router.get("/meta")` | GET → GET | WORKING-AS-CODED |
| 3 | client.ts:513 ``get<ChamberResponse>(`/chamber?…`)`` | `/api/chamber` | api.py:222 `@router.get("/chamber")` | GET → GET | WORKING-AS-CODED |
| 4 | client.ts:516 ```/timeline?…` `` | `/api/timeline` | api.py:232 `@router.get("/timeline")` | GET → GET | WORKING-AS-CODED |
| 5 | client.ts:520 ```/persons?q=…` `` | `/api/persons` | api.py:266 `@router.get("/persons")` | GET → GET | WORKING-AS-CODED |
| 6 | client.ts:523 ```/persons/${encodeURIComponent(id)}…` `` | `/api/persons/{id}` | api.py:440 `@router.get("/persons/{person_id}")` | GET → GET | WORKING-AS-CODED |
| 7 | client.ts:525 ```/persons/${…}/history` `` | `/api/persons/{id}/history` | api.py:432 `@router.get("/persons/{person_id}/history")` | GET → GET | WORKING-AS-CODED |
| 8 | client.ts:527 ```/party/${…}?as_of=…` `` | `/api/party/{short_name}` | api.py:792 `@router.get("/party/{short_name}")` | GET → GET | WORKING-AS-CODED |
| 9 | client.ts:529 ```/party/${…}/movements?…` `` | `/api/party/{short_name}/movements` | api.py:802 `@router.get("/party/{short_name}/movements")` | GET → GET | WORKING-AS-CODED |
| 10 | client.ts:531 ```/party/${…}/timeline?…` `` | `/api/party/{short_name}/timeline` | api.py:813 `@router.get("/party/{short_name}/timeline")` | GET → GET | WORKING-AS-CODED |
| 11 | client.ts:532 ``get<CommitteeResponse[]>(`/committees?as_of=${asOf}`)`` | `/api/committees` | api.py:567 `@router.get("/committees")` | GET → GET | WORKING-AS-CODED |
| 12 | client.ts:533 `get<…>("/parties")` | `/api/parties` | api.py:725 `@router.get("/parties")` | GET → GET | WORKING-AS-CODED |
| 13 | client.ts:535 ```/analytics/cross-chamber?as_of=…` `` | `/api/analytics/cross-chamber` | api.py:1015 `@router.get("/analytics/cross-chamber")` | GET → GET | WORKING-AS-CODED |
| 14 | client.ts:545 ``get<EventItem[]>(`/movements…`)`` | `/api/movements` | api.py:449 `@router.get("/movements")` | GET → GET | WORKING-AS-CODED |
| 15 | client.ts:549 ```/events/recent?limit=…` `` | `/api/events/recent` | api.py:464 `@router.get("/events/recent")` | GET → GET | WORKING-AS-CODED |
| 16 | client.ts:551 `get<CoverageItem[]>("/coverage")` | `/api/coverage` | api.py:474 `@router.get("/coverage")` | GET → GET | WORKING-AS-CODED |
| 17 | client.ts:552 `get<CoverageRow[]>("/coverage/detailed")` | `/api/coverage/detailed` | api.py:479 `@router.get("/coverage/detailed")` | GET → GET | WORKING-AS-CODED |
| 18 | client.ts:553 `get<CoverageDimensionRow[]>("/coverage/dimensions")` | `/api/coverage/dimensions` | api.py:485 `@router.get("/coverage/dimensions")` | GET → GET | WORKING-AS-CODED |
| 19 | client.ts:554 `get<CoverageSummaryResponse>("/coverage/summary")` | `/api/coverage/summary` | api.py:499 `@router.get("/coverage/summary")` | GET → GET | WORKING-AS-CODED |
| 20 | client.ts:555 `get<AboutResponse>("/about")` | `/api/about` | api.py:687 `@router.get("/about")` | GET → GET | WORKING-AS-CODED |
| 21 | client.ts:556 `get<HealthResponse>("/health")` | `/api/health` | api.py:848 `@router.get("/health")` | GET → GET | WORKING-AS-CODED |
| 22 | client.ts:558 ```/dashboard/stats?as_of=…` `` / `"/dashboard/stats"` | `/api/dashboard/stats` | api.py:1156 `@router.get("/dashboard/stats")` | GET → GET | WORKING-AS-CODED |
| 23 | client.ts:561 `get<VotesResponse>("/votes" + …)` | `/api/votes` | api.py:1261 `@router.get("/votes")` | GET → GET | WORKING-AS-CODED |
| 24 | client.ts:573 ```/votes/${encodeURIComponent(voteId)}` `` | `/api/votes/{vote_id}` | api.py:1344 `@router.get("/votes/{vote_id}")` | GET → GET | WORKING-AS-CODED |
| 25 | client.ts:581 ```/votes/${…}/positions…` `` | `/api/votes/{vote_id}/positions` | api.py:1384 `@router.get("/votes/{vote_id}/positions")` | GET → GET | WORKING-AS-CODED |
| 26 | client.ts:590 ```/analytics/vote-cohesion…` `` | `/api/analytics/vote-cohesion` | api.py:1434 `@router.get("/analytics/vote-cohesion")` | GET → GET | WORKING-AS-CODED |
| 27 | client.ts:606 ```/analytics/vote-activity…` `` | `/api/analytics/vote-activity` | api.py:1495 `@router.get("/analytics/vote-activity")` | GET → GET | WORKING-AS-CODED |
| 28 | client.ts:623 ``get<ScorecardResponse>(`/votes/scorecard?…`)`` | `/api/votes/scorecard` | api.py:1566 `@router.get("/votes/scorecard")` + reorder at api.py:1726–1740 | GET → GET | WORKING-AS-CODED |
| 29 | client.ts:637 `withScope("/api/export/popolo", …)` | `/api/export/popolo` | exports.py:25 prefix `/api/export`; :40 `@router.get("/popolo")` | GET (download URL) → GET | WORKING-AS-CODED |
| 30 | client.ts:646 ``withScope(`/api/export/${encodeURIComponent(dataset)}.csv`, …)`` | `/api/export/{dataset}.csv` | exports.py:208 `@router.get("/{dataset}.csv")`; allowlist at :214 `if dataset not in CSV_DATASETS:` | GET (download URL) → GET | WORKING-AS-CODED |
| 31 | client.ts:750 `get<TraseismScope[]>("/traseism/overview")` | `/api/traseism/overview` | api.py:1816 `@router.get("/traseism/overview")` | GET → GET | WORKING-AS-CODED |
| 32 | client.ts:759 ```/traseism/summary?…` `` | `/api/traseism/summary` | api.py:1829 `@router.get("/traseism/summary")` | GET → GET | WORKING-AS-CODED |
| 33 | client.ts:776 ```/traseism/switches…` `` | `/api/traseism/switches` | api.py:1841 `@router.get("/traseism/switches")` | GET → GET | WORKING-AS-CODED |
| 34 | client.ts:818 ```/analytics/switch-leaderboard?…` `` | `/api/analytics/switch-leaderboard` | api.py:1865 `@router.get("/analytics/switch-leaderboard")` | GET → GET | WORKING-AS-CODED |
| 35 | client.ts:856 ```/analytics/generational-shift…` `` | `/api/analytics/generational-shift` | api.py:1058 `@router.get("/analytics/generational-shift")` | GET → GET | WORKING-AS-CODED |
| 36 | client.ts:907 ``get<CommitteeListItem[]>(`/committees${qs}`)`` | `/api/committees` | api.py:567 `@router.get("/committees")` | GET → GET | WORKING-AS-CODED |
| 37 | client.ts:917 ```/committees/${encodeURIComponent(committeeId)}/members…` `` | `/api/committees/{committee_id}/members` | api.py:603 `@router.get("/committees/{committee_id}/members")` | GET → GET | WORKING-AS-CODED |
| 38 | client.ts:962 ```/analytics/committee-control…` `` | `/api/analytics/committee-control` | api.py:1031 `@router.get("/analytics/committee-control")` | GET → GET | WORKING-AS-CODED |
| 39 | client.ts:1000 ```/analytics/switch-waves…` `` | `/api/analytics/switch-waves` | api.py:952 `@router.get("/analytics/switch-waves")` | GET → GET | WORKING-AS-CODED |
| 40 | client.ts:1008 ```/analytics/ideology…` `` | `/api/analytics/ideology` | api.py:1743 `@router.get("/analytics/ideology")` | GET → GET | WORKING-AS-CODED |
| 41 | Report.tsx:172 `href="/api/export/report"` | `/api/export/report` | exports.py:25 prefix `/api/export`; :180 `@router.get("/report")` | GET (anchor) → GET | WORKING-AS-CODED |
| 42 | HeaderLogo.tsx:39 ``src={`/api/logo?color=${encodeURIComponent(COLORS[theme])}`}`` | `/api/logo` | logo.py:17 prefix `/api/logo`; :64 `@router.get("")` | GET (image) → GET | WORKING-AS-CODED |

**Unmatched API paths: none.** No `get<T>()` path, export URL builder, or hard-coded `/api/...` string in `frontend/src` lacks a matching FastAPI decorator + prefix. No method mismatch: all client calls are GET and all matched decorators are `@router.get`.

Backend GET routes registered in `api.py` with no corresponding call in `client.ts` (informational, not an unmatched frontend target): `/evidence/{evidence_id}` (api.py:670), `/analytics/waves` (894 and 922), `/analytics/waves/recompute` (927 and 947), `/analytics/party-cohesion` (994), `/analytics/party-timeline` (1089), `/health/live` (858), `/health/ready` (863), `/metrics` (metrics.py:21), `/logo/list` and `/logo/{logo_id}` (logo.py:72,77).

---

## 3. External-URL table (verbatim, reachability NOT PROVEN)

No network calls were performed. The "resolver" column names what the code implies would resolve each string; it is **not** a claim of reachability.

| ID | Literal (verbatim) | Click sites (file:line) | Resolver implied by code | Reachability |
| --- | --- | --- | --- | --- |
| E01 | `https://github.com/nedaktov-ops/parlament-deschis` | router.tsx:178 (`<a href … target="_blank" rel="noopener noreferrer">`), Footer.tsx:97, Footer.tsx:107 | external HTTP(S) navigation / GitHub web server | NOT PROVEN |
| E02 | `https://github.com/parlament-deschis` | About.tsx:6 `const PROJECT_URL = "https://github.com/parlament-deschis";` used at About.tsx:359 `href={PROJECT_URL}` | external HTTP(S) navigation / GitHub web server | NOT PROVEN |
| E03 | `https://github.com/nedaktov-ops/parlament-deschis/blob/main/docs/METHODOLOGY.md` | Traseism.tsx:22–23 `const METHODOLOGY_URL = …` used at Traseism.tsx:943; duplicate literal at SwitchLeaderboard.tsx:236 | external HTTP(S) navigation / GitHub web server | NOT PROVEN |
| E04 | `https://www.wikidata.org/wiki/${p.wikidata_qid}` (template) | PartyProfile.tsx:108, PersonDeepDive.tsx:170, PersonDrawer.tsx:145 | external HTTP(S) navigation / Wikidata web server; QID supplied by API data | NOT PROVEN |
| E05 | `https://www.gnu.org/licenses/agpl-3.0.html` | About.tsx:9 `CODE_LICENSE_URL_FALLBACK`, used via `href={codeLicenseUrl}` at About.tsx:306 | external HTTP(S) navigation / GNU web server | NOT PROVEN |
| E06 | `https://creativecommons.org/licenses/by/4.0/` | About.tsx:10 `DATA_LICENSE_URL_FALLBACK`, used via `href={dataLicenseUrl}` at About.tsx:317 | external HTTP(S) navigation / Creative Commons web server | NOT PROVEN |
| E07 | *no literal* — data-driven `href={source.url}`, `href={ev.source_url}`, `href={ev.snapshot_url}`, `href={p.source_url}`, `href={v.source_url}`, `href={row.source_url}`, `href={h.source_url}`, `href={codeLicenseUrl}`, `href={dataLicenseUrl}` | About.tsx:247; CitationPopover.tsx:74,87; RollCallTable.tsx:128; Voturi.tsx:274; Traseism.tsx:392; PersonDrawer.tsx:245; ProvenanceStamp.tsx:46,66; About.tsx:306,317 | whatever scheme the API-supplied value carries | NOT PROVEN (no literal to resolve) |

Non-clickable URL-like strings, recorded for completeness, not counted as targets: `xmlns="http://www.w3.org/2000/svg"` in HeroGraphic.tsx:72, ErrorState.tsx:27, LoadingState.tsx:29 (SVG namespace declarations). Repo-local files whose names appear in E03/E05/E06 do exist in the tree (`docs/METHODOLOGY.md`, `LICENSE`, whose first line is `GNU AFFERO GENERAL PUBLIC LICENSE / Version 3, 19 November 2007`); that is a local-tree fact only and does not prove anything about the remote URLs.

---

## 4. Relative / filesystem-style paths and platform routing

Quoted from [`vercel.json`](../../vercel.json):

- line 7: `{ "source": "/api/:path*", "destination": "https://parlament-deschis.onrender.com/api/:path*" },`
- line 8: `{ "source": "/graphql", "destination": "https://parlament-deschis.onrender.com/graphql" },`
- line 9: `{ "source": "/(.*)", "destination": "/index.html" }`
- line 33 (CSP): `"default-src 'self'; … img-src 'self' data:; font-src 'self' data:; connect-src 'self'; …"`

| Relative path (click site) | Line quote | What vercel.json configuration says | Backend/route definition where applicable | Verdict |
| --- | --- | --- | --- | --- |
| `/api/export/report` — Report.tsx:172 | `href="/api/export/report"` | Matches rewrite rule line 7 (`/api/:path*` → `https://parlament-deschis.onrender.com/api/:path*`), because the catch-all at line 9 comes after it | exports.py:180 `@router.get("/report")` + prefix exports.py:25 `/api/export` | WORKING-AS-CODED (config-level only); remote host reachability NOT PROVEN |
| `/` — Footer.tsx:66 | `href="/"` | Falls through to line 9 catch-all → `/index.html` | router.tsx:343 `path: "/",` | WORKING-AS-CODED |
| `/traseism` — Footer.tsx:74 | `href="/traseism"` | Falls through to line 9 catch-all → `/index.html` | router.tsx:394 `path: "/traseism",` | WORKING-AS-CODED |
| `/report` — Footer.tsx:82 | `href="/report"` | Falls through to line 9 catch-all → `/index.html` | router.tsx:465 `path: "/report",` | WORKING-AS-CODED |
| `/coverage` — Footer.tsx:124 | `href="/coverage"` | Falls through to line 9 catch-all → `/index.html` | router.tsx:401 `path: "/coverage",` | WORKING-AS-CODED |
| `#main-content` — router.tsx:231 | `<a href="#main-content" …>` | Not matched by any rewrite `source`; a document fragment | target element at router.tsx:325 `<main id="main-content" …>` | WORKING-AS-CODED (in-document target exists) |
| `/api/logo?color=…` — HeaderLogo.tsx:39 (image `src`, included because it is a relative API path) | `src={`/api/logo?color=${encodeURIComponent(COLORS[theme])}`}` | Matches rewrite line 7 → onrender `/api/logo?color=…` | logo.py:17 prefix `/api/logo`, :64 `@router.get("")` | WORKING-AS-CODED (config-level only); `img-src 'self'` at vercel.json:33 is consistent with the relative path |

The client's `BASE = "/api"` (client.ts:487) plus relative fetch at client.ts:490 is likewise same-origin and therefore consistent with `connect-src 'self'` (vercel.json:33) and the mirrored CSP in [`backend/main.py`](../../backend/main.py):76–77. This is a configuration statement, not a runtime observation.

---

## 5. What is already enforced automatically

[`scripts/check_routes_nav.mjs`](../../scripts/check_routes_nav.mjs):
- line 9 enumerates routes with `/path:\s*"([^"]+)"/g` against `frontend/src/router.tsx` only.
- line 10 enumerates clickables with `/<NavLink\s+to="([^"]+)"/g` **only in router.tsx**. It does not read page files, does not match `<Link to=...>`, `navigate({ to: ... })`, `throw redirect({ to: ... })`, or dynamic `to={linkTo}`.
- lines 11–14 whitelist `/person/$id` ("reachable via global Search") and `/electoral` ("redirect-only route").
- lines 18–22 normalize `$param` segments before comparing.
- lines 23–29 fail (exit 1) on any route that is neither nav-linked nor whitelisted.
- The whitelist comments cite `router.tsx:227-231` and `router.tsx:322-336`; in the current file those ranges are the end of the `document.title` effect and the end of `RootLayout`/start of `rootRoute`, not the Search handler (router.tsx:244–248) or the electoral route (router.tsx:348–362). The comments are stale; the whitelist strings themselves still name real paths.

[`scripts/check_i18n_keys.mjs`](../../scripts/check_i18n_keys.mjs):
- lines 3–8 declare its contract: missing `t("key")` in ro/en, one-locale-only keys, missing dynamic-allowlist keys, and duplicate keys all fail.
- lines 27–34 hold `DYNAMIC_ALLOWLIST` (with source-line comments at 19–26).
- lines 62–69 walk `frontend/src/**/*.{ts,tsx}` excluding `i18n.ts`; lines 77–85 extract literal `t("…")` call sites.
- lines 87–105 compute missing/asymmetric/duplicate keys and `fail()` on any; line 107 prints the PASS line.
- This script checks **only translation-key parity**. It performs no route, API-path, href or external-URL validation.

Neither script asserts reachability of any URL, nor does either validate search-param compatibility beyond the normalization at check_routes_nav.mjs:18.

---

## 6. Findings (Evidence + Reason + Improvement)

### C06-001 — All 22 `<NavLink>` targets resolve into the route tree
- **Click target:** router.tsx:264–320 (22 sites, listed in §1). Evidence: `<NavLink to="/leaderboard" …>` (router.tsx:270).
- **Destination:** router.tsx:414–419 `path: "/leaderboard",`.
- **Classification:** in-app SPA navigation.
- **Reason:** every literal equals a registered `path` exactly; `NavLink` at router.tsx:110–112 adds `search={(previous) => ({ ...previous, ...scope.searchFor() })}`, feeding the three canonical dims expected by `validateScopeSearch` (router.tsx:43–56).
- **Verdict:** WORKING-AS-CODED.
- **Improvement:** none required. Keep the regex gate in sync if routes are renamed (see C06-010).

### C06-002 — Literal-param nav targets `/legislature/2024` and `/party/PSD` match the `$` shapes
- **Click target:** router.tsx:306 `<NavLink to="/legislature/2024" …>`; router.tsx:309 `<NavLink to="/party/PSD" …>`.
- **Destination:** router.tsx:387 `path: "/legislature/$year",`; router.tsx:373 `path: "/party/$shortName",`.
- **Classification:** parameterized in-app navigation.
- **Reason:** `2024` binds `$year` and `PSD` binds `$shortName`; both routes use `validateSearch: validateScopeSearch` (router.tsx:389, 375). The path-level param is unconstrained; the `/^\d{4}$/` rule at router.tsx:47 applies to the *search* key `legislature`, not to `$year`.
- **Verdict:** WORKING-AS-CODED.
- **Improvement:** if `$year` must be a 4-digit value, add an explicit param-level check in `LegislatureDetail` rather than relying on the search validator (router.tsx:47).

### C06-003 — Recovery links and global Search target real routes
- **Click target:** router.tsx:75 and router.tsx:90 (`<Link to="/" …>`); router.tsx:245 (`to: "/person/$id",` with `params: { id }` at 246).
- **Destination:** router.tsx:343 `path: "/",`; router.tsx:380 `path: "/person/$id",`.
- **Classification:** error recovery / global search navigation.
- **Reason:** literal and param shape both match; the `search` objects satisfy `validateScopeSearch`.
- **Verdict:** WORKING-AS-CODED.
- **Improvement:** none required.

### C06-004 — The `/electoral` redirect emits a valid target
- **Click source:** router.tsx:351–359 `beforeLoad: ({ search }) => { throw redirect({ to: "/traseism", … }) }` (redirect `to` at 353).
- **Destination:** router.tsx:394 `path: "/traseism",`.
- **Classification:** programmatic redirect.
- **Reason:** target path is registered; `search` at 354–358 passes `date`/`chamber`/`legislature`, and serialization is customized at router.tsx:550–568 to avoid the double-quoted `legislature` value described in the comment at router.tsx:546–549.
- **Verdict:** WORKING-AS-CODED.
- **Improvement:** none required.

### C06-005 — Page-level `<Link>` and `navigate({ to })` targets all resolve
- **Click targets:** LiveDashboard.tsx:88,96,220,261,277,300; SwitchLeaderboard.tsx:161; PartyComparison.tsx:167; MpComparison.tsx:195; Committees.tsx:34,345; PartyTimeline.tsx:128; Mps.tsx:158; LegislatureDetail.tsx:195; Parties.tsx:46.
- **Destinations:** router.tsx:371–376 (`/party/$shortName`), 378–383 (`/person/$id`), 392–397 (`/traseism`), 449–454 (`/mps`), 463–468 (`/report`), 470–475 (`/parties`).
- **Classification:** in-app SPA navigation from page components.
- **Reason:** each `params={{ … }}` binding supplies the single `$` param declared by the matched route; `search={scope.searchFor()}` supplies the validated dims.
- **Verdict:** WORKING-AS-CODED.
- **Improvement:** none required.

### C06-006 — `DashboardCard` dynamic `to={linkTo}` has four concrete values, all registered
- **Click target:** DashboardCard.tsx:81 `<Link to={linkTo} search={searchParams} …>`.
- **Value sources:** LiveDashboard.tsx:140 `linkTo="/mps"`, :151 `linkTo="/mps"`, :162 `linkTo="/traseism"`, :174 `linkTo="/committees"`.
- **Destinations:** router.tsx:449–454, 392–397, 428–433.
- **Classification:** dynamic in-app navigation.
- **Reason:** `linkTo` is typed `string` (DashboardCard.tsx:8) and is not statically constrained to route ids, so a future typo would not be caught by the current gate (check_routes_nav.mjs:10 only matches literal `<NavLink to="...">` in router.tsx).
- **Verdict:** WORKING-AS-CODED (for the four current values).
- **Improvement:** type `linkTo` as `ValidateLinkOptions<RegisteredRouter>["to"]` or extend check_routes_nav.mjs to inspect JSX `linkTo="..."` literals (scripts/check_routes_nav.mjs:10).

### C06-007 — `/electoral` is a registered route with no inbound click target
- **Destination definition:** router.tsx:348–350 `getParentRoute: () => rootRoute, path: "/electoral",` and router.tsx:351–360 `beforeLoad` redirect.
- **Inbound target:** none found — searched `frontend/src/**/*.ts` and `frontend/src/**/*.tsx` for `to=`/`to:`; no `/electoral` literal appears as a destination. Verbatim definition side: router.tsx:350 `path: "/electoral",`.
- **Classification:** registered route, redirect-only, no inbound link.
- **Reason:** the route exists solely as a legacy alias whose `beforeLoad` throws to `/traseism` (router.tsx:352–353). It is whitelisted in scripts/check_routes_nav.mjs:12–14, so the gate does not flag it.
- **Verdict:** WORKING-AS-CODED (intentional redirect-only route; no broken click).
- **Improvement:** if legacy aliases are to be removed, delete router.tsx:348–362 and the whitelist entry at scripts/check_routes_nav.mjs:13 together; otherwise add a short in-code comment at router.tsx:348 stating "redirect-only, keep for old bookmarks" to make the intent local to the definition.

### C06-008 — Footer uses native `<a href>` for in-app destinations, dropping scope search params
- **Click targets:** Footer.tsx:66 `href="/"`, :74 `href="/traseism"`, :82 `href="/report"`, :124 `href="/coverage"`.
- **Destinations:** router.tsx:343, 394, 465, 401.
- **Classification:** in-app destination via native anchor (full document load, not a TanStack `<Link>`).
- **Reason:** contrast with router.tsx:110–112 and DashboardCard.tsx:81, which use `<Link>` with `search={scope.searchFor()}`. The Footer anchors carry no query string, so `validateScopeSearch` (router.tsx:43–56) re-materialises defaults — notably `date: localISODate()` at router.tsx:52 — instead of preserving the user's current scope. The destination *does* resolve; the scope is not carried. vercel.json:9 (`/(.*)` → `/index.html`) is the configuration that would let a full reload reach the SPA.
- **Verdict:** SUSPECT (scope loss on click; destination itself resolves).
- **Improvement:** replace the four native anchors at Footer.tsx:65–66, 73–74, 81–82, 123–124 with `<Link to="…" search={scope.searchFor()}>` as done at router.tsx:110–112.

### C06-009 — `check_routes_nav.mjs` coverage is narrower than the click surface, and its line comments are stale
- **Evidence:** scripts/check_routes_nav.mjs:10 `const navTargets = [...text.matchAll(/<NavLink\s+to="([^"]+)"/g)]…`; :12–13 whitelist comments `reachable via global Search (router.tsx:227-231)` and `redirect-only route (router.tsx:322-336)`.
- **Definition side:** the code those comments describe is actually at router.tsx:244–248 (Search `onSelect`) and router.tsx:348–362 (`electoralRoute`).
- **Classification:** automated gate scope / stale evidence pointer.
- **Reason:** the gate cannot detect a broken `to` in the 15 page-level sites of C06-005, the dynamic `DashboardCard` values of C06-006, or a redirect at router.tsx:353. It still enforces its declared contract (scripts/check_routes_nav.mjs:2) for router `<NavLink>`s.
- **Verdict:** SUSPECT.
- **Improvement:** at scripts/check_routes_nav.mjs:10, scan all `frontend/src/**/*.tsx` for `<Link\s+to="…"`, `<NavLink\s+to="…"` and `to:\s*"…"`; at lines 12–13, correct the stale line references to `router.tsx:244-248` and `router.tsx:348-362`.

### C06-010 — All client.ts API paths match FastAPI decorators with GET/GET agreement
- **Click targets:** client.ts:473,511–623,637,646,750,759,776,818,856,907,917,962,1000,1008 (40 paths, §2 rows 1–40); plus Report.tsx:172 and HeaderLogo.tsx:39 (rows 41–42).
- **Definitions:** api.py:217–1865, exports.py:25/40/180/208, logo.py:17/64 as tabulated.
- **Classification:** API destination resolution.
- **Reason:** prefix `/api` at api.py:29, `/api/export` at exports.py:25, `/api/logo` at logo.py:17; every effective URL is covered by a `@router.get` decorator. `get<T>()` uses GET (client.ts:489–490); anchors and the image `src` are GET requests.
- **Verdict:** WORKING-AS-CODED.
- **Improvement:** none required for path existence; see C06-011 for the double-prefix aliases.

### C06-011 — Legacy double-prefix route aliases no longer match the client's actual paths
- **Code evidence:** api.py:1566–1570:
  `@router.get("/votes/scorecard")` then the comment `Legacy alias: the frontend client still prefixes this path with ``/api``.` then `@router.get("/api/votes/scorecard", include_in_schema=False)`. Same pattern at api.py:1743–1745: `@router.get("/analytics/ideology")` / `# Legacy alias for the frontend's double-prefixed path (see scorecard above).` / `@router.get("/api/analytics/ideology", include_in_schema=False)`.
- **Client side:** client.ts:623 ``get<ScorecardResponse>(`/votes/scorecard?${params.toString()}`)`` and client.ts:1008 ``get<IdeologyResponse>(`/analytics/ideology…`)`` — with `BASE = "/api"` (client.ts:487) these are single-prefix.
- **Classification:** stale comment / unreferenced alias route.
- **Reason:** with router prefix `/api` (api.py:29), the alias decorators resolve to `/api/api/votes/scorecard` and `/api/api/analytics/ideology`; neither is used by client.ts. The comments assert the opposite of the current client code. The canonical single-prefix routes at api.py:1566 and 1743 are what the client resolves to.
- **Verdict:** SUSPECT.
- **Improvement:** update the comments at api.py:1567–1569 and api.py:1744 to say the alias is retained only for old callers, and either delete the alias decorators at api.py:1570 and api.py:1745 or add an automated check tying them to an actual consumer.

### C06-012 — Scorecard path resolution depends on an explicit route reorder
- **Evidence:** api.py:1726–1730 `Starlette matches routes in declaration order. ``/votes/{vote_id}`` was declared earlier, so it swallowed ``GET /api/votes/scorecard`` …`; api.py:1731–1740 removes and re-inserts `_scorecard_route` before `_vote_detail_index`.
- **Client side:** client.ts:623 path `/votes/scorecard` → `/api/votes/scorecard`.
- **Classification:** route-ordering dependency.
- **Reason:** the code documents and implements the ordering fix; dynamic `/votes/{vote_id}` at api.py:1344 would otherwise capture `vote_id="scorecard"`.
- **Verdict:** WORKING-AS-CODED.
- **Improvement:** add a regression assertion (in the existing test suite) that `/api/votes/scorecard` maps to `vote_scorecard`, because `router.routes` manipulation at api.py:1739–1740 is fragile under route additions.

### C06-013 — GitHub project URL literals disagree between two components
- **Click targets:** router.tsx:178 `href="https://github.com/nedaktov-ops/parlament-deschis"`; Footer.tsx:97 and :107 same string; About.tsx:6 `const PROJECT_URL = "https://github.com/parlament-deschis";` used at About.tsx:359 `href={PROJECT_URL}`.
- **Destination definition:** none in-repo for either string — no route or file defines the remote target; searched `frontend/src/**`, `vercel.json`, `backend/**`.
- **Classification:** external URL inconsistency.
- **Reason:** the two strings are different (`nedaktov-ops/parlament-deschis` vs `parlament-deschis`). Code alone establishes only the inconsistency, not which one is correct or reachable.
- **Verdict:** SUSPECT (inconsistency); reachability of both NOT PROVEN.
- **Improvement:** pick one canonical owner/repo string and define it once (e.g. a shared constant imported at About.tsx:6, router.tsx:178 and Footer.tsx:97/107). Resolver, if ever verified: GitHub HTTP server. No network check was performed.

### C06-014 — Methodology and license links record literals without in-repo destination definitions
- **Click targets:** Traseism.tsx:22–23 → used at :943; SwitchLeaderboard.tsx:236 (same literal); About.tsx:9 → :306 and About.tsx:10 → :317.
- **Destination definition:** no in-app route; local files named `docs/METHODOLOGY.md` and `LICENSE` exist in the tree (local fact only).
- **Classification:** external URL (code states intent only).
- **Reason:** the strings are passed straight to `href` with `target="_blank"`. Nothing in code validates them; no fetch was made.
- **Verdict:** NOT PROVEN (reachability).
- **Improvement:** if these links must be reliable, add a CI link-check step; until then keep the literals centralized (the methodology URL is already duplicated at Traseism.tsx:23 and SwitchLeaderboard.tsx:236 — import the constant instead).

### C06-015 — Wikidata links are built from API data and have no literal destination to verify
- **Click targets:** PartyProfile.tsx:108, PersonDeepDive.tsx:170, PersonDrawer.tsx:145 ``href={`https://www.wikidata.org/wiki/${p.wikidata_qid}`}``.
- **Destination definition:** none in-repo; the QID comes from `PersonDetail.wikidata_qid` / party data (client.ts:79, 93, 264).
- **Classification:** data-driven external URL.
- **Reason:** rendering is guarded by `p.wikidata_qid &&` (PartyProfile.tsx:106, PersonDeepDive.tsx:167, PersonDrawer.tsx:143), but no format check on the QID appears in these expressions.
- **Verdict:** NOT PROVEN (reachability and value correctness).
- **Improvement:** anchor at PartyProfile.tsx:108 — validate `wikidata_qid` against `^Q\d+$` before rendering, or use the API-provided QID verbatim only when the backend has validated it.

### C06-016 — Data-driven source/snapshot/license hrefs have no code-level destination
- **Click targets:** ProvenanceStamp.tsx:46,66; CitationPopover.tsx:74,87; RollCallTable.tsx:128; Voturi.tsx:274; Traseism.tsx:392; PersonDrawer.tsx:245; About.tsx:247,306,317.
- **Destination definition:** none in-repo — values come from API fields (`source_url`, `snapshot_url`, `licenses.code_url`, `licenses.data_url`; client.ts:61,68,70,245,246,284,377).
- **Classification:** data-driven external URL.
- **Reason:** code only forwards the data value to `href`; no scheme allowlist is present in these sites.
- **Verdict:** NOT PROVEN.
- **Improvement:** at ProvenanceStamp.tsx:46, add an `http(s)` scheme guard before rendering to avoid `javascript:`/`data:` values arriving from data.

### C06-017 — Relative export/report path resolves at the platform layer by configuration only
- **Click target:** Report.tsx:172 `href="/api/export/report"` with `download="transparency-report.json"` at :173.
- **Destination:** exports.py:180 `@router.get("/report")` with exports.py:25 `router = APIRouter(prefix="/api/export")`; platform rewrite vercel.json:7.
- **Classification:** relative filesystem-style path → platform rewrite → backend endpoint.
- **Reason:** vercel.json:7 rewrites `/api/:path*` before the catch-all at :9, so the configured destination path matches the FastAPI prefix/decorator. Configuration says nothing about whether the destination host answers.
- **Verdict:** WORKING-AS-CODED (configuration); remote reachability NOT PROVEN.
- **Improvement:** none required for resolution; if the onrender host is ever changed, keep vercel.json:7–8 and any other hard-coded host references in sync.

### C06-018 — `check_i18n_keys.mjs` enforces key parity only
- **Evidence:** scripts/check_i18n_keys.mjs:3–8 (declared contract), :79–85 (literal `t("…")` extraction), :104–107 (fail/pass).
- **Destination definition:** `frontend/src/i18n.ts` (ro/en blocks) — not a route or API definition.
- **Classification:** automated gate coverage boundary.
- **Reason:** the script never opens `router.tsx`, `client.ts`, `vercel.json` or any backend file; it cannot catch a broken navigation target or API path.
- **Verdict:** WORKING-AS-CODED (for translation-key parity only).
- **Improvement:** if route/endpoint drift must be gated, add a separate script rather than extending this one; extend scripts/check_routes_nav.mjs as described in C06-009.

---

## 7. Coverage and NOT PROVEN

- Route tree inspected: router.tsx:335–544 (25 registered routes, all with `validateScopeSearch` at router.tsx:43–56).
- Navigation targets catalogued: 42 unique call sites (22 router `<NavLink>` + 2 recovery `<Link>` + 1 Search `navigate` + 1 redirect + 15 page-level `navigate`/`<Link>` + 1 dynamic `DashboardCard` link). All matched; 0 unmatched; 1 registered route without inbound click (`/electoral`, router.tsx:348).
- API paths catalogued: 40 in client.ts plus 2 hard-coded outside it (Report.tsx:172, HeaderLogo.tsx:39). All matched with GET→GET; 0 unmatched.
- External URL literals: 11 call sites across 6 distinct literal/template strings (§3 E01–E06), plus one data-driven category (E07). None resolved over the network; reachability NOT PROVEN for every external destination. Resolvers named per row in §3.
- Relative paths: 5 root-relative hrefs/sources plus 1 document fragment, interpreted only against vercel.json:7–9 and :33 (§4). No runtime/platform behaviour was observed.
- NOT PROVEN items: E01–E07 in §3 (7 external destination entries); the onrender host named in vercel.json:7–8; whether any local file named by a URL (docs/METHODOLOGY.md, LICENSE) corresponds to the remote resource; any claim that a rewritten route or API call actually returns a response. No network call, browser session, or deployment observation was used.
- Searched for unmatched definitions: `frontend/src/**/*.ts`, `frontend/src/**/*.tsx`, `backend/routers/*.py`, `backend/main.py`, `vercel.json`, `scripts/check_routes_nav.mjs`, `scripts/check_i18n_keys.mjs`.
- Files not modified: all source, data, config and git state. Only this note was written; `_generated/*` untouched.

Targets checked: 100 | Unmatched: 0 | SUSPECT: 4 | NOT PROVEN: 7
