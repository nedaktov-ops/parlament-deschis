---
id: CLICK-INV-C04
type: evidence
title: "Clickable inventory — C04 vote-analytics pages (2026-11-22)"
description: "Evidence-only enumeration of every clickable/interactive element rendered by Voturi, Radar, Grafice, Topuri, Ideology and Report at source_commit 8811216, with i18n, route and backend cross-checks."
status: active
authority: derived
tags: [type/evidence, lifecycle/active, domain/frontend]
source_paths: [frontend/src/pages/Voturi.tsx, frontend/src/pages/Radar.tsx, frontend/src/pages/Grafice.tsx, frontend/src/pages/Topuri.tsx, frontend/src/pages/Ideology.tsx, frontend/src/pages/Report.tsx, frontend/src/i18n.ts, frontend/src/router.tsx, frontend/src/api/client.ts, frontend/src/hooks/useScope.ts, frontend/src/components/ScopeControls.tsx, frontend/src/components/ui/AsyncState.tsx, frontend/src/components/ErrorState.tsx, frontend/src/components/RetryButton.tsx, frontend/src/components/RollCallTable.tsx, frontend/src/components/ProvenanceStamp.tsx, frontend/src/components/VoteActivityChart.tsx, frontend/src/components/ui/TooltipText.tsx, frontend/src/components/PartyAgreementMatrix.tsx, backend/routers/exports.py, backend/routers/api.py, backend/main.py]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Clickable inventory — C04 vote-analytics pages

Read-only investigation at `8811216`. No code, data, config, git state or
`_generated/*` file was changed. Every claim below is grounded in a verbatim
`file:line` quote. No network calls and no browser observations were made.
Parent synthesis: [CLICK-INVESTIGATION-2026-11-22](CLICK-INVESTIGATION-2026-11-22.md).

## 1. Complete inventory

`file:line` paths are repository-relative. Shared `ScopeControls` inputs are
listed once (C04-001..003) with the exact pages that render them; every other
row is a distinct rendered control. `class` values: `in-app route`, `external
URL`, `API/download`, `state action`, `no-op`, `dead`.

| ID | file:line | label / i18n (both locales) | purpose (quoted from code/prose) | destination / handler chain (terminal line quoted) | class | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| C04-001 | `frontend/src/components/ScopeControls.tsx:32-34`; rendered by `frontend/src/pages/Voturi.tsx:108-111` (`showDate`) and `frontend/src/pages/Radar.tsx:143-146` (`showDate`) | `t("asOf")` — ro `i18n.ts:76` `"La data de"` / en `i18n.ts:830` `"As of"` | `Voturi.tsx:110` `note={t("scope.note.votesUpTo", { date: scope.date })}` — ro `i18n.ts:89` `"Voturi până la {{date}}."` / en `i18n.ts:843` `"Votes up to {{date}}."` | `ScopeControls.tsx:34` `onChange={(e) => { if (e.target.value) scope.setScope({ date: e.target.value }); }}` → `useScope.ts:51` `navigate({` (functional search updater, `replace: false` at `:64`) → `client.ts:482` `to: scope.date` → `client.ts:566` `params.set("to", query.to)` → backend `api.py:1266` `to_date: str \| None = Query(None, alias="to", ...)`. Terminal: `ScopeControls.tsx:34`. | state action | WORKING-AS-CODED |
| C04-002 | `frontend/src/components/ScopeControls.tsx:40-45`; rendered by `Voturi.tsx:108-111`, `Radar.tsx:143-146`, `frontend/src/pages/Grafice.tsx:71`, `frontend/src/pages/Topuri.tsx:93` | `t("filter.chamber", "Chamber")` — ro `i18n.ts:610` `"Camera"` / en `i18n.ts:1313` `"Chamber"`; options `t("scope.allChambers")` ro `:78` / en `:832`; `t("deputies")` ro `:74` / en `:828`; `t("senate")` ro `:75` / en `:829` | `ScopeControls.tsx:41` `scope.setScope({ chamber: (e.target.value \|\| undefined) as "deputies" \| "senate" \| undefined })` | → `useScope.ts:51` `navigate({` → page query: `Voturi.tsx:56` `chamber: active?.chamber` and `client.ts:563` `params.set("chamber", query.chamber)` → backend `api.py:1263` `chamber: str \| None = Query(None, pattern=r"^(deputies\|senate)$")`; Grafice `:38` `api.voteCohesion(chamber, legislature)`; Topuri `:56` `api.scorecard(legislature, chamber, limit, offset, minVotes)`. Terminal: `ScopeControls.tsx:41`. | state action | WORKING-AS-CODED |
| C04-003 | `frontend/src/components/ScopeControls.tsx:51-55`; same four pages as C04-002 | `t("filter.legislature", "Legislature")` — ro `i18n.ts:613` `"Legislatură"` / en `i18n.ts:1316` `"Legislature"`; `t("scope.allLegislatures")` ro `:79` / en `:833` | `ScopeControls.tsx:52` `scope.setScope({ legislature: e.target.value \|\| undefined })` | → `useScope.ts:51` `navigate({` → `client.ts:564` `params.set("legislature", query.legislature)` → backend `api.py:1264` `legislature: str \| None = Query(None, pattern=r"^\d{4}$")`. Terminal: `ScopeControls.tsx:52`. | state action | WORKING-AS-CODED |
| C04-004 | `frontend/src/pages/Voturi.tsx:136-156` (label `:134`) | `t("view.voturi.scopeSelect", "Vote scope (from the corpus)")` — ro `i18n.ts:544` `"Domeniu de vot (din corpus)"` / en `i18n.ts:1290` `"Vote scope (from the corpus)"`; options text `:153` `{s.chamber} / {s.legislature ?? "—"} — {s.total}` | `Voturi.tsx:28-29` `// R-08: discover data-bearing scopes from the API instead of hardcoding a chamber/legislature. The probe is tiny; the paged query follows it.` | `Voturi.tsx:138-148` `onChange` → `:143` `scope.setScope({` → `useScope.ts:51` `navigate({`; chosen chamber/legislature re-enter the query at `Voturi.tsx:56-57` `chamber: active?.chamber, legislature: active?.legislature ?? undefined` → `client.ts:560-571` `get<VotesResponse>("/votes" ...)` → backend `api.py:1261` `def votes_list(`. Terminal: `Voturi.tsx:146`. Options sourced from the probe `Voturi.tsx:151` `{scopes.map((s) => (`. | state action | WORKING-AS-CODED |
| C04-005 | `frontend/src/pages/Voturi.tsx:162-168` (label `:160`) | `t("filter.search", "Search")` — ro `i18n.ts:617` `"Caută"` / en `i18n.ts:1320` `"Search"`; placeholder `t("view.voturi.searchPlaceholder", "Search by title…")` ro `:553` / en `:1299` | `Voturi.tsx:51` `// Title search stays client-side; only the API-supported scope enters the key.` and `:171` `"{{filtered}} of {{total}} votes on this page ({{from}}–{{to}} of corpus)"` (ro `:545` / en `:1291`) | `Voturi.tsx:165` `onChange={(e) => setQuery(e.target.value)}` → `:21` `navigate({ search: scope.searchFor({ query: value \|\| undefined }) })`; consumed only by `:74-80` `filtered` → terminal `:79` `(v.title_raw ?? "").toLowerCase().includes(needle),`. **No `query` in `queryKey` (`:53`) or `queryFn` (`:54-58`)** — filter does not reach the API query. | state action | SUSPECT |
| C04-006 | `frontend/src/pages/Voturi.tsx:243-250` (button inside each vote row) | visible `{v.title_raw ?? "—"}` (`:249`); aria-label `t("view.voturi.positionsTitle", { id: v.title_raw ?? v.native_vote_id })` — ro `i18n.ts:557` `"Poziții la vot — {{id}}"` / en `i18n.ts:1303` `"Vote positions — {{id}}"` | `Voturi.tsx:16-17` `// Search text and the selected vote are URL-backed so a deep link opens the exact vote and back/forward steps through the filter (FN-7).` | `Voturi.tsx:245` `onClick={() => goToVote(v.native_vote_id)}` → `:82-84` `goToVote` → `:83` `setSelectedVoteId(nativeVoteId)` → `:22-23` → terminal `:23` `navigate({ search: scope.searchFor({ selectedVoteId: value ?? undefined }) })`; enables `voteDetailQuery` `:62-66` → `client.ts:572-573` `get<VoteDetail>(`/votes/${encodeURIComponent(voteId)}`)` → backend `api.py:1344` `@router.get("/votes/{vote_id}")`. | state action | WORKING-AS-CODED |
| C04-007 | `frontend/src/pages/Voturi.tsx:273-280` | `v.source_url.split("/")[2] ?? t("mps.source", "Source")` — ro `i18n.ts:532` `"Sursă"` / en `i18n.ts:1278` `"Source"` | `Voturi.tsx:117` `t("view.voturi.intro", "...Every published row comes from the official cdep.ro feed and carries its source URL.")` (ro `:542` / en `:1288`) | `Voturi.tsx:274` `href={v.source_url}` with `:275-276` `target="_blank" rel="noopener noreferrer"`; value is the API field `client.ts:329` `source_url: string` populated at backend `api.py:1328` `"source_url": v.source_url`. Terminal: `Voturi.tsx:274`. Concrete URL is data-dependent (no literal in repo). | external URL | WORKING-AS-CODED (wiring; concrete href data-dependent — see §3) |
| C04-008 | `frontend/src/pages/Voturi.tsx:313-320` | `t("view.voturi.prev", "Previous")` — ro `i18n.ts:547` `"Anterioare"` / en `i18n.ts:1293` `"Previous"` | `Voturi.tsx:322` `t("view.voturi.pageRange", "{{from}}–{{to}} of {{total}}", ...)` (ro `:546` / en `:1292`); pagination over the votes corpus | `Voturi.tsx:316` `onClick={() => setOffset((o) => Math.max(0, o - limit))}`; disabled `:315` `disabled={offset === 0}`; `offset` from `:25` `useState(0)` enters `:53` `queryKey` and `:55` `votesForScope(scope, { limit, offset })`. Terminal: `Voturi.tsx:316`. Bounded below by `Math.max(0, ...)` and by the disabled guard. | state action | WORKING-AS-CODED |
| C04-009 | `frontend/src/pages/Voturi.tsx:324-331` | `t("view.voturi.next", "Next")` — ro `i18n.ts:548` `"Următoarele"` / en `i18n.ts:1294` `"Next"` | same page-range note as C04-008; `Voturi.tsx:26` `const limit = 100` | `Voturi.tsx:327` `onClick={() => setOffset((o) => o + limit)}`; disabled `:326` `disabled={offset + limit >= total}` where `total` is `:69` `votesQuery.data?.total ?? 0` (backend `api.py:1337` `"total": total`). Terminal: `Voturi.tsx:327`. | state action | WORKING-AS-CODED |
| C04-010 | `frontend/src/pages/Voturi.tsx:341-347` | `t("view.voturi.backToList", "← Back to votes list")` — ro `i18n.ts:559` `"← Înapoi la lista de voturi"` / en `i18n.ts:1305` `"← Back to votes list"` | shown only when `selectedVoteId` is set (`:336` `{selectedVoteId && (`) | `Voturi.tsx:343` `onClick={() => setSelectedVoteId(null)}` → `:22-23` → terminal `:23` `navigate({ search: scope.searchFor({ selectedVoteId: value ?? undefined }) })`; undefined is dropped by `router.tsx:553` `if (value === undefined) continue;`. | state action | WORKING-AS-CODED |
| C04-011 | `frontend/src/pages/Voturi.tsx:93-103` (retry button rendered by `ui/AsyncState.tsx:78-83` → `ErrorState.tsx:38-44` → `RetryButton.tsx:18-25`) | button `t("retry", "Retry")` — ro `i18n.ts:271` `"Reîncearcă"` / en `i18n.ts:1018` `"Retry"` (`RetryButton.tsx:24` `label ?? t("traseismRetry")` overridden by `ErrorState.tsx:41` `label={t("retry", "Retry")}`); error text `t("view.voturi.loadError", "Failed to load votes.")` ro `:561` / en `:1307` | `AsyncState.tsx:78-83` renders retry only for `view === "error"`; `Voturi.tsx:91` `if (view !== "ready")` | `Voturi.tsx:96-99` `onRetry={() => { void scopeProbe.refetch(); void votesQuery.refetch(); }}` → `RetryButton.tsx:20` `onClick={onRetry}`. Terminal: `Voturi.tsx:98`. | state action | WORKING-AS-CODED |
| C04-012 | `frontend/src/pages/Voturi.tsx:348-353` → `frontend/src/components/ProvenanceStamp.tsx:42-50` | `t("viewOriginal")` — ro `i18n.ts:108` `"Vezi sursa originală"` / en `i18n.ts:862` `"View original source"`; rendered text `:47` `{t("viewOriginal")} ↗` | `ProvenanceStamp.tsx:20` `/** Renders provenance only for fields the API actually supplied. */` | `Voturi.tsx:350` `sourceUrl={voteDetailQuery.data.source_url}` → `ProvenanceStamp.tsx:46` `<a href={sourceUrl} target="_blank" rel="noopener noreferrer"`; field `client.ts:364` `source_url: string` / backend `api.py:1375`. Terminal: `ProvenanceStamp.tsx:46`. Guarded by `Voturi.tsx:348` `{voteDetailQuery.data && (`. | external URL | WORKING-AS-CODED (wiring; concrete href data-dependent — see §3) |
| C04-013 | `frontend/src/pages/Voturi.tsx:355` → `frontend/src/components/RollCallTable.tsx:126-134` | `p.source_url.split("/")[2] ?? t("mps.source", "Source")` — ro `i18n.ts:532` / en `i18n.ts:1278` | `RollCallTable.tsx:23` `queryFn: () => api.votePositions(voteId),`; one anchor per returned position row (`:101` `{data.map((p: VotePositionRow) => (`) | `RollCallTable.tsx:128` `href={p.source_url}` with `:129-130` `target="_blank" rel="noopener noreferrer"`; field `client.ts:377` `source_url: string` / backend `api.py:1420` `"source_url": p.source_url`. Terminal: `RollCallTable.tsx:128`. | external URL | SUSPECT (rows beyond backend default limit 100 are never rendered — Finding F3) |
| C04-014 | `frontend/src/pages/Voturi.tsx:355` → `frontend/src/components/RollCallTable.tsx:53-59` (retry via `ErrorState`/`RetryButton`) | button `t("retry", "Retry")` (ro `i18n.ts:271` / en `:1018`); message `t("view.voturi.loadError", "Failed to load votes.")` | `RollCallTable.tsx:53` `if (query.isError) {` | `RollCallTable.tsx:57` `onRetry={() => void query.refetch()}` → `RetryButton.tsx:20` `onClick={onRetry}`. Terminal: `RollCallTable.tsx:57`. | state action | WORKING-AS-CODED |
| C04-015 | `frontend/src/pages/Radar.tsx:125-138` (retry) | button `t("retry", "Retry")` (ro `i18n.ts:271` / en `:1018`); error text `t("view.radar.loadError", "The roll-call alignment matrix could not be loaded.")` ro `i18n.ts:746` / en `i18n.ts:1500` | `Radar.tsx:121-122` `// A failed positions query is an excluded column, not a page-level error.` and `:122` `isError: scopeProbe.isError \|\| votesQuery.isError,` | `Radar.tsx:130-134` `onRetry={() => { void scopeProbe.refetch(); void votesQuery.refetch(); positionQueries.forEach((q) => void q.refetch()); }}`. Terminal: `Radar.tsx:133`. | state action | WORKING-AS-CODED |
| C04-016 | `frontend/src/pages/Grafice.tsx:53-67` (retry) | button `t("retry", "Retry")`; error text `t("view.grafice.loadError", "Cohesion and vote-activity data could not be loaded.")` ro `i18n.ts:747` / en `i18n.ts:1501` | `Grafice.tsx:46` `// Page-level state only when neither independent block can render.` | `Grafice.tsx:58-62` `onRetry={() => { void scopeProbe.refetch(); void summaryQuery.refetch(); void cohesionQuery.refetch(); }}`. Terminal: `Grafice.tsx:61`. | state action | WORKING-AS-CODED |
| C04-017 | `frontend/src/pages/Grafice.tsx:218` → `frontend/src/components/VoteActivityChart.tsx:180-186` (inline retry) | button `t("retry", "Retry")`; error text `t("view.grafice.activityLoadError", "Failed to load vote activity.")` ro `i18n.ts:588` / en `i18n.ts:1351`; empty `t("view.grafice.activityEmpty", ...)` ro `:587` / en `:1350` | `VoteActivityChart.tsx:43` `Powered by the /api/analytics/vote-activity endpoint.` | `VoteActivityChart.tsx:183` `onRetry={() => void activityQuery.refetch()}` → `RetryButton.tsx:20`. Terminal: `VoteActivityChart.tsx:183`. Query: `VoteActivityChart.tsx:55` `api.voteActivity(chamber, legislature)` → `client.ts:605-607` `/analytics/vote-activity` → backend `api.py:1495`. | state action | WORKING-AS-CODED |
| C04-018 | `frontend/src/pages/Topuri.tsx:122-128` (label `:120`) | **hard-coded literal** `"Minimum votes"` (`:120`) — no `t()` call and no key in `i18n.ts` (ro or en); placeholder literal `"1"` (`:126`) | `Topuri.tsx:56` `queryFn: () => api.scorecard(legislature, chamber, limit, offset, minVotes),` | `Topuri.tsx:125` `onChange={(e) => setMinVotes(Math.max(0, Number(e.target.value) \|\| 0))}` → `:28-29` `navigate({ search: scope.searchFor({ minVotes: value }) })` → `:55` queryKey → `:56` → `client.ts:622` `params.set("min_votes", String(min_votes))` → `client.ts:623` `/votes/scorecard?...` → backend `api.py:1566` `@router.get("/votes/scorecard")` (reordered ahead of the dynamic route at `api.py:1731-1740`). Terminal: `Topuri.tsx:29`. Offset reset on change: `Topuri.tsx:50-52` `useEffect(... setOffset(0) ..., [minVotes, legislature, chamber])`. | state action | SUSPECT (untranslated label — Finding F2) |
| C04-019 | `frontend/src/pages/Topuri.tsx:217-224` | `t("view.topuri.prev", "Previous")` — ro `i18n.ts:595` `"Anterioare"` / en `i18n.ts:1358` `"Previous"` | `Topuri.tsx:226` `t("view.topuri.page", "Showing {{from}}–{{to}} of {{total}} MPs", ...)` (ro `:594` / en `:1357`) | `Topuri.tsx:220` `onClick={() => setOffset((o) => Math.max(0, o - limit))}`; disabled `:219` `disabled={offset === 0}`; offset enters `:55` queryKey and `:56` query. Terminal: `Topuri.tsx:220`. | state action | WORKING-AS-CODED |
| C04-020 | `frontend/src/pages/Topuri.tsx:232-239` | `t("view.topuri.next", "Next")` — ro `i18n.ts:596` `"Următoarele"` / en `i18n.ts:1359` `"Next"` | same page note as C04-019; `Topuri.tsx:32` `const limit = 100` | `Topuri.tsx:235` `onClick={() => setOffset((o) => o + limit)}`; disabled `:234` `disabled={offset + limit >= total}` with `total` from `:64` `scorecardQuery.data?.total ?? 0`. Terminal: `Topuri.tsx:235`. | state action | WORKING-AS-CODED |
| C04-021 | `frontend/src/pages/Topuri.tsx:74-88` (retry) | button `t("retry", "Retry")`; error text `t("view.topuri.loadError", "The behavioural scorecard could not be loaded.")` ro `i18n.ts:748` / en `i18n.ts:1502` | `Topuri.tsx:68-73` `view = resolveViewState({...})` + `:74` `if (view !== "ready")` | `Topuri.tsx:79-82` `onRetry={() => { void scopeProbe.refetch(); void scorecardQuery.refetch(); }}`. Terminal: `Topuri.tsx:81`. | state action | WORKING-AS-CODED |
| C04-022 | `frontend/src/pages/Ideology.tsx:248-261` (label `:246`) | `t("filter.year", "Year")` — ro `i18n.ts:611` `"An"` / en `i18n.ts:1314` `"Year"`; options `t("filter.year_all", "All years")` ro `i18n.ts:612` `"Toți anii"` / en `i18n.ts:1315` `"All years"` (`:253-255`) and `years.map` (`:256-260`) | `Ideology.tsx:53` `// CHES survey year is a distinct URL param, never a mapped as_of date.`; `:79` `// Filter data by selected year (show latest year by default)` | `Ideology.tsx:250` `onChange={(e) => setYear(e.target.value \|\| undefined)}` → `:59-60` `navigate({ search: scope.searchFor({ chesYear: value }) })` → `:62-65` `ideologyQuery` → `client.ts:1003-1009` `ideology(year)` / `params.set("year", year)` → backend `api.py:1743` `@router.get("/analytics/ideology")`; client-side display filter terminal `:84` `data.filter((d: IdeologyEntry) => d.survey_year === parseInt(selectedYear, 10))`. **"All years" cannot persist** — Finding F1. | state action | BROKEN |
| C04-023 | `frontend/src/pages/Ideology.tsx:216-227` (retry) | button `t("retry", "Retry")`; error text `t("view.ideology.loadError", "The ideological map could not be loaded.")` ro `i18n.ts:749` / en `i18n.ts:1503`; empty `t("view.ideology.noYear", ...)` ro `:601` / en `:1364` | `Ideology.tsx:211-215` `view = resolveViewState({...})` and `:216` `if (view !== "ready")` | `Ideology.tsx:221` `onRetry={() => void ideologyQuery.refetch()}`. Terminal: `Ideology.tsx:221`. | state action | WORKING-AS-CODED |
| C04-024 | `frontend/src/pages/Report.tsx:164-170` | `t("report.print", "Print / Save as PDF")` — ro `i18n.ts:693` `"Printează / Salvează ca PDF"` / en `i18n.ts:1447` `"Print / Save as PDF"` | `Report.tsx:139-142` `t("report.subtitle", "One-page summary of what the corpus contains — for journalists and citizens.")` (ro `:694` / en `:1448`); `exports.py:193` `this download is the unfiltered snapshot that backs the print view.` | `Report.tsx:166` `onClick={() => window.print()}`. Terminal: `Report.tsx:166`. No navigation, no API call; browser print dialog (effect outside repo scope). Container is `print:hidden` at `Report.tsx:161`. | state action | WORKING-AS-CODED |
| C04-025 | `frontend/src/pages/Report.tsx:171-177` | `t("report.download", "Download JSON")` — ro `i18n.ts:685` `"Descarcă JSON"` / en `i18n.ts:1439` `"Download JSON"` | `Report.tsx:128` `{/* Deliberately unscoped endpoint (exports.py); honest disclosure only. */}`; `exports.py:7-9` `"/report" is deliberately different: it is a single whole-corpus snapshot. It takes no scope parameters ...` | `Report.tsx:172` `href="/api/export/report"` + `:173` `download="transparency-report.json"`; backend `exports.py:25` `router = APIRouter(prefix="/api/export")` + `exports.py:180` `@router.get("/report")` + `main.py:182` `app.include_router(exports_router)` ⇒ **GET /api/export/report exists**; response header `exports.py:204` `headers=_attachment("transparency-report.json")`. Same URL used by `Report.tsx:65` `return get<TransparencyReport>("/export/report")` with `client.ts:487` `const BASE = "/api"`. Terminal: `Report.tsx:172`. | API/download | WORKING-AS-CODED (method + path verified in backend) |
| C04-026 | `frontend/src/pages/Report.tsx:112-123` (retry) | button `t("retry", "Retry")`; error text `t("report.errorTitle", "Failed to load report")` ro `i18n.ts:21` / en `i18n.ts:776`; description `report.errorDesc` ro `:20` / en `:775`; loading `report.loadingTitle` ro `:23` / en `:778` | `Report.tsx:107-111` `view = resolveViewState({...})` and `:112` `if (view !== "ready")` | `Report.tsx:117` `onRetry={() => void report.refetch()}`. Terminal: `Report.tsx:117`. | state action | WORKING-AS-CODED |

**No `role="button"`, `onKeyDown` activator, form submit or programmatic
`navigate()` other than the chains above was found in the six page files.**
Focusable scroll regions (`Voturi.tsx:189-194`, `Radar.tsx:160-165`,
`Grafice.tsx:109-110`, `Topuri.tsx:140`, `Ideology.tsx:280`,
`Report.tsx:231-236`, `:365-370`) carry `tabIndex={0}` and `role="region"` but
no activation handler; they are scroll affordances, not activators, and are
therefore not enumerated as clickable elements.

## 2. Findings (defects)

### F1 — C04-022: the Ideology "All years" option can never display all years — BROKEN

**Evidence** (verbatim, `frontend/src/pages/Ideology.tsx`):
- `:80` `const selectedYear = chesYear || (years.length > 0 ? String(years[0]) : undefined);`
- `:81-87` `const filteredData = useMemo(() => selectedYear ? data.filter((d: IdeologyEntry) => d.survey_year === parseInt(selectedYear, 10)) : data, [data, selectedYear]);`
- `:249` `<select value={selectedYear ?? ""}`
- `:250` `onChange={(e) => setYear(e.target.value || undefined)}`
- `:253-255` `<option value="">` / `{t("filter.year_all", "All years")}` / `</option>`
- `:59-60` `const setYear = (value: string | undefined) => navigate({ search: scope.searchFor({ chesYear: value }) });`
- `router.tsx:553` `if (value === undefined) continue;` and `router.tsx:565` `if (value !== "") result[key] = value;`

**Reason**: selecting the `value=""` "All years" option calls `setYear(undefined)`,
which drops `chesYear` from the URL. On re-render `chesYear` is `undefined`, so
`:80` substitutes the newest year (`years[0]`); `:249` then binds the `<select>`
value to that newest year, and `:84` filters `data` down to that single year.
The empty option is neither sticky nor able to show all waves. This is fully
determined by the quoted lines; no runtime resolver needed.

**Improvement**: at `Ideology.tsx:59-60,80,84,249-255`, encode the all-years
state explicitly (e.g. `chesYear === "all"` as a sentinel preserved by
`router.tsx:553/565`) and derive `selectedYear = chesYear === "all" ? undefined :
(chesYear ?? String(years[0] ?? ""))`, binding the option value to the same
sentinel. Add a unit/integration assertion that selecting "All years" keeps the
option selected and `filteredData.length === data.length`.

### F2 — C04-018: "Minimum votes" bypasses i18n — SUSPECT

**Evidence**: `frontend/src/pages/Topuri.tsx:120` `Minimum votes` (plain JSX
text, no `t(...)`), versus `Topuri.tsx:119` adjacent
`{t("view.topuri.page", ...)}` and `Topuri.tsx:125` etc. A repository-wide
search finds no `Minimum votes`/`minimumVotes` key in `frontend/src/i18n.ts`
(ro `:1-759`, en `:760-1513`); the only `filter.year_all` hits are
`i18n.ts:612` and `:1315` (Ideology).

**Reason**: every other label on these six pages is resolved through `t()`, so
this control renders English text even when `i18n.language === "ro"`
(`i18n.ts:1518` `lng: "ro"`). The control's URL/API chain itself is correct
(`Topuri.tsx:125 → :29 → client.ts:622`), hence SUSPECT rather than BROKEN.

**Improvement**: add `"view.topuri.minVotes": "Număr minim de voturi"` at
`i18n.ts` ro block (near `:590-596`) and `"view.topuri.minVotes": "Minimum
votes"` in the en block (near `:1353-1359`), then change `Topuri.tsx:120` to
`{t("view.topuri.minVotes", "Minimum votes")}`.

### F3 — C04-013: position source anchors are silently truncated at 100 rows — SUSPECT

**Evidence**: `frontend/src/components/RollCallTable.tsx:23`
`queryFn: () => api.votePositions(voteId),` (no `limit`); compare
`frontend/src/pages/Radar.tsx:63` `queryFn: () => api.votePositions(v.native_vote_id, { limit: 500 }),`.
Backend `backend/routers/api.py:1387` `limit: int = Query(100, ge=1, le=500),`
and `:1408-1411` `total = db.scalar(...)`, `rows = db.execute(... .offset(offset).limit(limit))...`.
`RollCallTable.tsx` has no pagination control and does not read `total`.

**Reason**: for a vote with >100 recorded positions, the detail panel rendered
by `Voturi.tsx:355` shows only the first 100 source anchors and never reveals
the remaining ones; the API returns `total` (`:1428`) but the component ignores
it (`RollCallTable.tsx:26-27` only reads `data` / `data_exists`). Whether any
real vote exceeds 100 positions is data-dependent and not proven here.

**Improvement**: at `RollCallTable.tsx:23`, pass `{ limit: 500 }` as
`Radar.tsx:63` does, or add offset pagination driven by
`query.data?.total` (`api.py:1428`) with bounds `offset + limit >= total`.

### F4 — C04-005: title search is page-local and does not reset pagination — SUSPECT

**Evidence**: `frontend/src/pages/Voturi.tsx:51`
`// Title search stays client-side; only the API-supported scope enters the key.`;
`:74-80` `const filtered = useMemo(() => { const needle = query.trim().toLowerCase(); if (!needle) return votes; return votes.filter(... (v.title_raw ?? "").toLowerCase().includes(needle)); }, [votes, query]);`;
`:52-60` `votesQuery` — `queryKey: ["votes", ...scope.scopeKey, activeKey, offset]`
(`:53`) and `queryFn` (`:54-58`) contain no title term;
`:47-49` `useEffect(() => { setOffset(0); }, [activeKey]);` — `query`/`offset`
are not dependencies.

**Reason**: the `query` URL parameter (`:18-21`) filters only the 100 rows
already loaded for the current `offset` (`:26` `const limit = 100`), and typing
a new term while on page 3 leaves `offset` at 200, so matches from earlier pages
are never shown. The behaviour is explicitly documented in-code, so the
element is intentionally state-only, but the user-visible consequence (search
appears corpus-wide per `:117` intro yet is page-local per `:171`) is a suspect
UX/accuracy defect. Runtime impact depends on the corpus and was not measured.

**Improvement**: at `Voturi.tsx:47-49`, add `query` to the reset effect
(`}, [activeKey, query]);`) so a new search starts at page 0; and at `:116-118`
or `:170-177`, disclose that title search scans the current page only, or add a
server-side title filter to `VotesFilters`/`client.ts:432-439` and include it in
the `queryKey`/`queryFn` at `:52-60`.

## 3. Verifications (non-defects) and NOT PROVEN / resolver list

**Verified in code, no defect:**
- **Uppercase `/Voturi`**: route declared `router.tsx:486` `path: "/Voturi"`;
  the only navigation link is `router.tsx:316` `<NavLink to="/Voturi" ...>`;
  page hooks use `Voturi.tsx:15` `useNavigate({ from: "/Voturi" })` and `:18`
  `useSearch({ from: "/Voturi", ... })`; title logic `router.tsx:214`
  `else if (path === "/Voturi") label = t("nav.voturi");`. A repo-wide search
  found no lowercase `/voturi` route target. Case is consistent.
- **Report print / download**: `Report.tsx:166` `window.print()` is present;
  `Report.tsx:172` `href="/api/export/report"` resolves to the real
  `@router.get("/report")` on `APIRouter(prefix="/api/export")`
  (`exports.py:25,180-205`) included at `main.py:182` — exact method GET, exact
  path `/api/export/report`, and a matching `Content-Disposition` filename
  (`exports.py:204` vs `Report.tsx:173`).
- **Scorecard route reachability**: the frontend path `client.ts:623`
  `/votes/scorecard?...` (BASE `/api`) would be shadowed by
  `api.py:1344` `@router.get("/votes/{vote_id}")`, but `api.py:1726-1740`
  explicitly removes and re-inserts the static route ahead of the dynamic one
  (`router.routes.insert(_vote_detail_index, _scorecard_route)`). Docs at
  `api.py:1726-1730` state the same. Not a defect.
- **Filter-to-query tracing**: scope date/chamber/legislature reach the API
  (`client.ts:482,563,564`); min-votes reaches `min_votes` (`client.ts:622`);
  CHES year reaches `year` (`client.ts:1007`). The only filters that do **not**
  reach the query are the Voturi title search (F4) and Ideology's client-side
  year partition (`:81-87`), which is intentional and mirrors the API `year`
  param.

**NOT PROVEN from code (resolver named per item):**
- Concrete `href` values of C04-007 (`Voturi.tsx:274`), C04-012
  (`ProvenanceStamp.tsx:46`) and C04-013 (`RollCallTable.tsx:128`): the code
  binds them to API-supplied strings (`client.ts:329,364,377` populated at
  `api.py:1328,1375,1420`); no literal URLs are in the repo. Wiring, `target`
  and `rel` are verified. **Resolver**: inspect a live `/api/votes` and
  `/api/votes/{id}/positions` response for the actual `source_url` values.
- Exact DOM rendering/activation of ECharts canvas controls (legend, dataZoom
  slider, tooltip) inside `Ideology.tsx:269` and `Grafice.tsx:218`: they are
  created by `echarts` at `Ideology.tsx:128` and `VoteActivityChart.tsx:67`,
  not authored as DOM anchors/buttons with labels in this repo. **Resolver**:
  browser DOM/pointer inspection by the QA harness; no browser claims made here.
- `TooltipText` (`frontend/src/components/ui/TooltipText.tsx:13-19`) is
  `role="tooltip"` with `pointer-events-none` (`:16`) and is referenced via
  `aria-describedby` (`Radar.tsx:184,210`); it is not clickable by code.

**Coverage boundary**: the six assigned page files were read in full, as were
`i18n.ts`, `router.tsx`, `api/client.ts`, `useScope.ts`, `ScopeControls.tsx`,
`AsyncState.tsx`, `ErrorState.tsx`, `RetryButton.tsx`, `RollCallTable.tsx`,
`ProvenanceStamp.tsx`, `VoteActivityChart.tsx`, `TooltipText.tsx`,
`PartyAgreementMatrix.tsx`, `backend/routers/exports.py`,
`backend/routers/api.py` and `backend/main.py`. Pages in this slice render no
other interactive child components: `DataBar`, `Sparkline`, `ProgressRing`,
`InfoStat` and `HeroGraphic` (`Grafice.tsx:7`, `Topuri.tsx:8`,
`Report.tsx:4-6`) contain no `onClick`/`href`/`onChange` per repo search, and
`PartyAgreementMatrix.tsx:241-248` is `role="img"`. `Report.tsx:129` and
`Ideology.tsx:232` pass only `note` to `ScopeControls`, whose `ScopeControls.tsx:24`
early return is bypassed by the note, so those two pages render **no** scope
inputs — consistent with `Report.tsx:128` "Deliberately unscoped endpoint".

Sources (relative): [Voturi.tsx](../../frontend/src/pages/Voturi.tsx) ·
[Radar.tsx](../../frontend/src/pages/Radar.tsx) ·
[Grafice.tsx](../../frontend/src/pages/Grafice.tsx) ·
[Topuri.tsx](../../frontend/src/pages/Topuri.tsx) ·
[Ideology.tsx](../../frontend/src/pages/Ideology.tsx) ·
[Report.tsx](../../frontend/src/pages/Report.tsx) ·
[i18n.ts](../../frontend/src/i18n.ts) ·
[router.tsx](../../frontend/src/router.tsx) ·
[client.ts](../../frontend/src/api/client.ts) ·
[useScope.ts](../../frontend/src/hooks/useScope.ts) ·
[ScopeControls.tsx](../../frontend/src/components/ScopeControls.tsx) ·
[AsyncState.tsx](../../frontend/src/components/ui/AsyncState.tsx) ·
[ErrorState.tsx](../../frontend/src/components/ErrorState.tsx) ·
[RetryButton.tsx](../../frontend/src/components/RetryButton.tsx) ·
[RollCallTable.tsx](../../frontend/src/components/RollCallTable.tsx) ·
[ProvenanceStamp.tsx](../../frontend/src/components/ProvenanceStamp.tsx) ·
[VoteActivityChart.tsx](../../frontend/src/components/VoteActivityChart.tsx) ·
[TooltipText.tsx](../../frontend/src/components/ui/TooltipText.tsx) ·
[PartyAgreementMatrix.tsx](../../frontend/src/components/PartyAgreementMatrix.tsx) ·
[exports.py](../../backend/routers/exports.py) ·
[api.py](../../backend/routers/api.py) ·
[main.py](../../backend/main.py)

Elements: 26 | BROKEN: 1 | SUSPECT: 3 | NOT PROVEN: 0
