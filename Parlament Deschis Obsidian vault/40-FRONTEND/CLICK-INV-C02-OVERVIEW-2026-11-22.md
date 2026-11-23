---
id: CLICK-INV-C02
type: evidence
title: "Clickable inventory — C02 overview and scope pages (2026-11-22)"
description: "Read-only, code-grounded inventory of every clickable/interactive element rendered by the eight assigned pages plus ScopeControls and the useScope handler terminal at HEAD 8811216; i18n labels resolved in both locales and all navigate targets cross-checked against router.tsx."
status: active
authority: derived
tags: [type/evidence, lifecycle/active, domain/frontend]
source_paths: [frontend/src/pages/LiveDashboard.tsx, frontend/src/pages/Traseism.tsx, frontend/src/pages/SwitchLeaderboard.tsx, frontend/src/pages/CoverageView.tsx, frontend/src/pages/InstitutionalView.tsx, frontend/src/pages/SenateHistory.tsx, frontend/src/pages/LegislatureDetail.tsx, frontend/src/components/ScopeControls.tsx, frontend/src/hooks/useScope.ts, frontend/src/i18n.ts, frontend/src/router.tsx]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Clickable inventory — C02 overview and scope pages (2026-11-22)

Scope: HEAD `8811216` (`88112168237e5c37841b785dccd2375f6cc40115`). All ten assigned source files were read in full (`8 pages` + `ScopeControls.tsx` + `useScope.ts`), plus `frontend/src/i18n.ts` and `frontend/src/router.tsx` for key/route resolution. Child components were opened only to follow a callback passed by an assigned page; their own clickable inventory belongs to C‑05 and is **not** duplicated here (page call sites are cited instead). No code, data, config, git state, network call or browser was touched. Verdicts describe what the code expresses; where a value is data- or runtime-dependent and not determinable from code, the verdict is `NOT PROVEN` and a resolver is named.

Classes: `in-app route` | `external URL` | `API/download` | `state action` | `no-op` | `dead`.
Notation `ro:NNN / en:NNN` = exact definition lines in `frontend/src/i18n.ts`, quoted verbatim in the i18n index below. `client.ts:NNN` = `frontend/src/api/client.ts`, read only to name the terminal API endpoint.

## 1. Complete clickable inventory

| ID | file:line | label / i18n | purpose (quoted from code or prose) | destination / handler chain | class | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| C02-001 | LiveDashboard.tsx:128 | `errorLabel={t("dashboard.loadError")}`; ro:756 / en:1510 | `"onRetry={() => void dashboardStats.refetch()}"` | `AsyncState` → `ErrorState` → `RetryButton` (`ErrorState.tsx:38-45`, `RetryButton.tsx:18-20`) → `dashboardStats.refetch()` → `api.dashboardStats(asOf)` (LiveDashboard.tsx:34; `client.ts:557`) | state action | WORKING-AS-CODED |
| C02-002 | LiveDashboard.tsx:132-142 (`linkTo` at :140) | `t("dashboardStatPersons", "Members of Parliament")`; ro:13 / en:768; sr-only `t("navigateTo")`, ro:101 / en:855 | `"value={stats?.persons ?? "--"}"` metric card | `DashboardCard.tsx:79-84 <Link to={linkTo} search={searchParams}>` → `mpsRoute` `path: "/mps"` (router.tsx:449-454). **`searchParams` not passed by the page** | in-app route | SUSPECT (scope dropped — F1) |
| C02-003 | LiveDashboard.tsx:143-153 (`linkTo` at :151) | `t("dashboardStatMemberships", "Memberships")`; ro:12 / en:767 | `"value={stats?.memberships ?? "--"}"` metric card | same `DashboardCard` → `/mps` (router.tsx:449-454); no `searchParams` passed | in-app route | SUSPECT (scope dropped — F1) |
| C02-004 | LiveDashboard.tsx:154-164 (`linkTo` at :162) | `t("dashboardStatSwitches", "All observed affiliation changes")`; ro:10 / en:765 | `"value={stats?.switches_all ?? "--"}"` metric card | same `DashboardCard` → `traseismRoute` `path: "/traseism"` (router.tsx:392-397); no `searchParams` passed | in-app route | SUSPECT (scope dropped — F1) |
| C02-005 | LiveDashboard.tsx:165-176 (`linkTo` at :174) | `t("dashboardStatCommittees", "Committees")`; ro:11 / en:766 | `"value={stats?.committees ?? "--"}"` metric card | same `DashboardCard` → `committeesRoute` `path: "/committees"` (router.tsx:428-433); no `searchParams` passed | in-app route | SUSPECT (scope dropped — F1) |
| C02-006 | LiveDashboard.tsx:201 (`onSelectLegislature` call site) | child control labels `t("play")`/`t("pause")`, ro:96/97, en:850/851; prev/next ro:199/200, en:953/954 | `"onSelectLegislature={(start, legislature) => scope.setScope({ date: start, legislature })}"`; child doc: `"The slider snaps to the `start` of each legislature ... writes both `date` and `legislature` into the route scope"` (LegislatureSeatExplorer.tsx:8-12) | `LegislatureSeatExplorer.tsx:41 onSelectLegislature(list[next].start, list[next].id)` → `useScope.ts:49-68 setScope` → `navigate({ search: (prev) => {...}, replace: false })` (useScope.ts:51-65) — stays on `/` | state action (route search) | WORKING-AS-CODED |
| C02-007 | LiveDashboard.tsx:202 (`onOpenPerson={openPerson}`) | child `ChamberView` → `Hemicycle` member buttons; aria from `t("a11y.partyNode")` ro:132 / en:886 not used here; member name from API | `"const openPerson = (id: string) => { navigate({ to: "/person/$id", params: { id }, search: scope.searchFor({ date: clamped }) }) }"` (94-100) | `LegislatureSeatExplorer.tsx:147 onSelect={onOpenPerson}` → `ChamberView.tsx:45 <Hemicycle ... onSelect>` → `Hemicycle.tsx:118 / :142 onClick ... onSelect(s.member.person_id)` → `openPerson` → `personRoute` `path: "/person/$id"` (router.tsx:378-383) | in-app route | WORKING-AS-CODED |
| C02-008 | LiveDashboard.tsx:219 (`onPartyClick={openParty}`) | child row button; label `{party.short_name \|\| party.name}` (PartyListTable.tsx:80) | `"const openParty = (shortName: string) => { navigate({ to: "/party/$shortName", params: { shortName }, search: scope.searchFor({ date: clamped }) }) }"` (86-92) | `PartyListTable.tsx:64 onClick={() => onPartyClick?.(party.short_name \|\| party.id)}` → `openParty` → `partyRoute` `path: "/party/$shortName"` (router.tsx:371-376) | in-app route | WORKING-AS-CODED (fallback `party.id` as `shortName` is data-dependent — see NOT PROVEN) |
| C02-009 | LiveDashboard.tsx:220 | child `"View all →"` (PartyListTable.tsx:112) | `"onViewAll={() => navigate({ to: "/parties", search: scope.searchFor({ date: clamped }) })}"` | `PartyListTable.tsx:107-110 onClick={onViewAll}` → `navigate` → `partiesRoute` `path: "/parties"` (router.tsx:470-475); scope carried via `searchFor` (useScope.ts:69-72) | in-app route | WORKING-AS-CODED |
| C02-010 | LiveDashboard.tsx:214 | `t("dashboard.loadError")`; ro:756 / en:1510 | `"onRetry={() => void partiesData.refetch()}"` | `ErrorState.tsx:38-45` → `partiesData.refetch()` → `api.parties` (LiveDashboard.tsx:35) | state action | WORKING-AS-CODED |
| C02-011 | LiveDashboard.tsx:227 (`onChairClick`) | child aria `t("a11y.committeeChair", "Show chair for {{party}}")`; ro:129 / en:883 | `"onChairClick={(chair) => chair.chair_person_id && openPerson(chair.chair_person_id)}"` | `CommitteeControl.tsx:97-116 <button ... onClick={() => chairForParty && onChairClick?.(chairForParty)}>` → page guard → `openPerson` (94-100) → `/person/$id` (router.tsx:378-383). Guard can yield no action when id falsy | in-app route | SUSPECT (conditional silent no-op — F4) |
| C02-012 | LiveDashboard.tsx:229 (`onRetry`) | `t("committeeControl.loadError")` ro:751 / en:1505 (from `CommitteeControl.tsx:58`) | `"onRetry={() => void committeeControlQuery.refetch()}"` | `CommitteeControl.tsx:52-61 StateView onRetry` → `committeeControlQuery.refetch()` → `committeeControl(scope.legislature, asOf)` (LiveDashboard.tsx:37; `client.ts:953`) | state action | WORKING-AS-CODED |
| C02-013 | LiveDashboard.tsx:234 (`onRetry`) | `t("state.empty.dataQuality")` ro:743 / en:1497 (from `DataQualityGauge.tsx:71`) | `"onRetry={() => void coverageDetailed.refetch()}"` | `DataQualityGauge.tsx:64-73 StateView onRetry` → `coverageDetailed.refetch()` → `api.coverage_detailed` (LiveDashboard.tsx:39; `client.ts:552`) | state action | WORKING-AS-CODED |
| C02-014 | LiveDashboard.tsx:255 | `t("dashboard.loadError")`; ro:756 / en:1510 | `"onRetry={() => void partiesData.refetch()}"` (second view of the same query) | `ErrorState.tsx:38-45` → `partiesData.refetch()` → `api.parties` (35) | state action | WORKING-AS-CODED |
| C02-015 | LiveDashboard.tsx:260 (`onNodeClick={openParty}`) | child aria `t("a11y.partyNode", "Party {{party}}: {{members}} members")`; ro:132 / en:886 | `"onNodeClick={openParty}"`; child `"onClick={() => onNodeClick?.(node.short_name \|\| node.id)}"` (PartyNetwork.tsx:105) | `openParty` (86-92) → `partyRoute` `path: "/party/$shortName"` (router.tsx:371-376) | in-app route | WORKING-AS-CODED (same `short_name \|\| id` fallback caveat as C02-008) |
| C02-016 | LiveDashboard.tsx:261 | child `"View all →"` (PartyNetwork.tsx:151) | `"onViewAll={() => navigate({ to: "/mps", search: scope.searchFor({ date: clamped }) })}"` | `PartyNetwork.tsx:145-149 onClick={onViewAll}` → `navigate` → `mpsRoute` `path: "/mps"` (router.tsx:449-454) | in-app route | WORKING-AS-CODED |
| C02-017 | LiveDashboard.tsx:272 | `t("dashboard.loadError")`; ro:756 / en:1510 | `"onRetry={() => void switchWavesQuery.refetch()}"` | `ErrorState.tsx:38-45` → `switchWavesQuery.refetch()` → `switchWaves()` (LiveDashboard.tsx:36; `client.ts:992`) | state action | WORKING-AS-CODED |
| C02-018 | LiveDashboard.tsx:277 (`onWaveClick`) | child wave rect aria `t("a11y.switchWave", "Switch wave on {{date}}: {{count}} switches")` ro:139 / en:893; child `"View all →"` (SwitchTimeline.tsx:230) | prose `"deepDiveSwitchTimelineDesc": "Each bar is a wave of group switches across the whole corpus; select one for details."` ro:632 / en:1379 | `SwitchTimeline.tsx:186 onClick={() => onWaveClick?.(wave)}` and `:187 onKeyDown={(e) => activateOnKey(e, () => onWaveClick?.(wave))}` (`activateOnKey` at `utils/a11y.ts:9-11`: `Enter`/`" "`); child `:214-231 View all` also calls `onWaveClick`; page handler ignores the wave → `navigate({ to: "/traseism", search: scope.searchFor({ date: clamped, chamber: "deputies", legislature: undefined }) })` → `traseismRoute` (router.tsx:392-397) | in-app route | SUSPECT (F2) |
| C02-019 | LiveDashboard.tsx:289 (`onPersonClick={openPerson}`) | child member button, label = `{member.name}` (CrossChamberFlow.tsx:92), aria from `t("crossChamberTableCaption")` ro:188 / en:942 | `"onPersonClick={openPerson}"`; child `"onClick={() => onPersonClick?.(member.person_id)}"` (CrossChamberFlow.tsx:86) | `openPerson` (94-100) → `/person/$id` (router.tsx:378-383). Child button `disabled={!onPersonClick}` is false here because the callback is supplied | in-app route | WORKING-AS-CODED |
| C02-020 | LiveDashboard.tsx:300 (`onSelect`) | child feed row button label = `summary(e)` / alert `"view"` button, ro:727 / en:1481 | `"onSelect={(id) => navigate({ to: "/person/$id", params: { id }, search: scope.searchFor({ date: clamped }) })}"` | `LiveFeed.tsx:254 onClick={() => e.person && onSelect(e.person.id)}` (row, `disabled={!e.person}`) and `:211 onClick={() => onSelect(e.person!.id)}` (alert view) → `navigate` → `/person/$id` (router.tsx:378-383) | in-app route | WORKING-AS-CODED (default props `?? "2024"` / `?? "senate"` at :298-299 noted in F6) |
| C02-021 | Traseism.tsx:839 (`onRetry`) | `t("traseismLoadError")`; ro:363 / en:1109 | `"onRetry={() => void summary.refetch()}"` | `ErrorState.tsx:38-45` → `summary.refetch()` → `traseismSummary(legislature, chamber)` (Traseism.tsx:685-689; `client.ts:754-760`) | state action | WORKING-AS-CODED |
| C02-022 | Traseism.tsx:789-803 (`map` instance `c`) | `t(c)` → `t("deputies")` ro:74 / en:828 or `t("senate")` ro:75 / en:829 | `"onClick={() => routeScope.setScope({ chamber: c })}"`, `aria-pressed={chamber === c}` | `useScope.ts:49-68 setScope` → `navigate({ search: (prev) => merged, replace: false })` (51-65), stays on `/traseism` | state action (route search) | WORKING-AS-CODED |
| C02-023 | Traseism.tsx:789-803 (second `map` instance `c`) | `t(c)` → `t("senate")` ro:75 / en:829 | same button definition as C02-022, `c = "senate"` | same `setScope` chain | state action (route search) | WORKING-AS-CODED |
| C02-024 | Traseism.tsx:813-824 | `t("legislature")`; ro:194 / en:948; options `{year}` :820-822 | `"onChange={(e) => routeScope.setScope({ legislature: e.target.value })}"` | `useScope.ts:49-68 setScope` → in-place `navigate` (51-65). Value `value={legislature}` where `:671 const legislature = routeScope.legislature ?? matchingLegislature ?? "2024"` | state action (route search) | WORKING-AS-CODED |
| C02-025 | Traseism.tsx:391-398 | `t("traseismOfficialSource") ↗`; ro:353 / en:1100 (else `t("traseismNoSource")` ro:354 / en:1101, not a link) | `"traseismLedgerDesc": "Every cited switch, with its date and a link to the official document it was read from."` ro:350 / en:1097 | `<a href={row.source_url} target="_blank" rel="noopener noreferrer">` rendered only when `row.source_url` (390); row from `traseismSwitches` (Traseism.tsx:298-307; `client.ts:764-778`) | external URL | NOT PROVEN (concrete URL is backend data — resolver in §4) |
| C02-026 | Traseism.tsx:414-419 | `t("traseismPreviousPage")`; ro:360 / en:1106 | `"onClick={() => setPage((p) => Math.max(0, p - 1))}"`, `disabled={page === 0}` (415) | `setPage` (state at :292) → new `queryKey: ["traseism-switches", legislature, chamber, page, ...scopeKey]` (299) → `traseismSwitches({ ..., offset: page * PAGE_SIZE })` (301-306; `client.ts:764-778`) | state action | WORKING-AS-CODED |
| C02-027 | Traseism.tsx:421-426 | `t("traseismNextPage")`; ro:361 / en:1107 | `"onClick={() => setPage((p) => p + 1)}"`, `disabled={(page + 1) * PAGE_SIZE >= total}` (422) | `setPage` → query refetch at new offset (299-306). `totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))` (311); no clamp of `page` when `total` shrinks | state action | SUSPECT (F3) |
| C02-028 | Traseism.tsx:331 (`onRetry`) | `t("traseismLoadError")` ro:363 / en:1109; `emptyTitle={t("traseismNoRows")}` ro:357 / en:1104 | `"onRetry={() => void query.refetch()}"` | `ErrorState.tsx:38-45` → `query.refetch()` (query defined :298-307) | state action | WORKING-AS-CODED |
| C02-029 | Traseism.tsx:507 (`sortableHeader("chamber", t("chamber"))`) | `t("chamber")`; ro:250 / en:997 | `"const sortableHeader = (key, label) => ..."`; `"The button toggles setSortKey/setSortDir"` (481-488) | `Traseism.tsx:481-488 onClick` → `setSortKey("chamber")`/`setSortDir` (446-447) → `sortedRows` useMemo (448-463) | state action | WORKING-AS-CODED |
| C02-030 | Traseism.tsx:508 (`"legislature"`) | `t("legislature")`; ro:194 / en:948 | same `sortableHeader` definition (469-499) | `setSortKey("legislature")` → `sortedRows` (448-463) | state action | WORKING-AS-CODED |
| C02-031 | Traseism.tsx:509 (`"members"`) | `t("traseismMembersDenominator")`; ro:315 / en:1062 | same `sortableHeader` definition | `setSortKey("members")` → `sortedRows` | state action | WORKING-AS-CODED |
| C02-032 | Traseism.tsx:510 (`"switches"`) | `t("traseismSwitchesCount")`; ro:316 / en:1063 | same `sortableHeader` definition | `setSortKey("switches")` → `sortedRows` | state action | WORKING-AS-CODED |
| C02-033 | Traseism.tsx:511 (`"switchers"`) | `t("traseismSwitchersCount")`; ro:317 / en:1064 | same `sortableHeader` definition | `setSortKey("switchers")` → `sortedRows` | state action | WORKING-AS-CODED |
| C02-034 | Traseism.tsx:512 (`"switch_rate"`) | `t("traseismSwitchRate")`; ro:318 / en:1065 | same `sortableHeader` definition; `useState<ScopeSortKey \| null>("switch_rate")` (445) is the initial sort key | `setSortKey("switch_rate")` / direction toggle → `sortedRows` | state action | WORKING-AS-CODED |
| C02-035 | Traseism.tsx:513 (`"switches_per_100_members"`) | `t("traseismPer100")`; ro:320 / en:1067 | same `sortableHeader` definition | `setSortKey("switches_per_100_members")` → `sortedRows` | state action | WORKING-AS-CODED |
| C02-036 | Traseism.tsx:617 (`onRetry`) | `t("waves.error", "Failed to load waves.")` ro:736 / en:1490; `emptyTitle` ro:735 / en:1489 | `"onRetry={() => void waves.refetch()}"` | `ErrorState.tsx:38-45` → `waves.refetch()` → `switchWaves(chamber, legislature)` (593-596; `client.ts:992`) | state action | WORKING-AS-CODED |
| C02-037 | Traseism.tsx:928 (`onRetry`) | `t("traseismLoadError")` ro:363 / en:1109; `emptyTitle={t("noData")}` ro:214 / en:961 | `"onRetry={() => void overview.refetch()}"` | `ErrorState.tsx:38-45` → `overview.refetch()` → `traseismOverview()` (681-684; `client.ts:749-751`) | state action | WORKING-AS-CODED |
| C02-038 | Traseism.tsx:942-949 | `t("traseismMethodologyLink") ↗`; ro:380 / en:1126 | `"const METHODOLOGY_URL = \"https://github.com/nedaktov-ops/parlament-deschis/blob/main/docs/METHODOLOGY.md\""` (22-23) | `<a href={METHODOLOGY_URL} target="_blank" rel="noopener noreferrer">`; no JS handler | external URL | WORKING-AS-CODED |
| C02-039 | Traseism.tsx:950-956 | `t("traseismAboutButton")`; ro:382 / en:1128 | `"onClick={() => setAboutOpen(true)}"`; `"<About open={aboutOpen} onClose={() => setAboutOpen(false)} />"` (960) | `setAboutOpen(true)` (state at :660) → `About open` → `About.tsx:139 if (!open) return null` no longer short-circuits → dialog renders (`About.tsx:159-368`); close via backdrop `:162`, close button `:197-203`, Escape `:116-128` → `onClose` → `setAboutOpen(false)` | state action | WORKING-AS-CODED (F5 — modal **can** open; internal controls belong to C‑05/C01) |
| C02-040 | SwitchLeaderboard.tsx:53 (`onRetry`) | `t("leaderboard.error", "Failed to load leaderboard.")` ro:486 / en:1232 | `"onRetry={() => void leaderboard.refetch()}"` (full-page state branch :48-58) | `ErrorState.tsx:38-45` → `leaderboard.refetch()` → `switchLeaderboard(limit, scope.legislature, scope.chamber)` (:31-34; `client.ts:809-820`) | state action | WORKING-AS-CODED |
| C02-041 | SwitchLeaderboard.tsx:100 (`showChamber showLegislature`) | child labels `t("filter.chamber")` ro:610 / en:1313, `t("filter.legislature")` ro:613 / en:1316 | `"<ScopeControls showChamber showLegislature />"`; child `"const setScope = ..."` via `useScope` | `ScopeControls.tsx:40-45` chamber select / `:51-55` legislature select → `scope.setScope(...)` → `useScope.ts:51-65` in-place navigate; stays on `/leaderboard` | state action (route search) | WORKING-AS-CODED |
| C02-042 | SwitchLeaderboard.tsx:103-113 | `t("leaderboard.filter.limit", "Show top")`; ro:489 / en:1235; options `{[10, 20, 50, 100]}` :108-112 | `"const setLimit = (value: number) => navigate({ search: scope.searchFor({ limit: value }) })"` (29); comment `"Page-local filter lives in the URL too (FN-7)"` (23) | `<select onChange={(e) => setLimit(Number(e.target.value))}>` (105) → `navigate({ search: ... })` with `from: "/leaderboard"` (22), no `to` → same route; query key/`:32-33` uses `limit` | state action (route search) | WORKING-AS-CODED (stale URL `limit` edge noted in §5) |
| C02-043 | SwitchLeaderboard.tsx:160-167 | `{row.name}` (166) | `"<Link to=\"/person/$id\" params={{ id: row.person_id }} search={scope.searchFor()}>"` | `Link` → `personRoute` `path: "/person/$id"` (router.tsx:378-383); scope in `search` from `useScope.ts:69-72` | in-app route | WORKING-AS-CODED |
| C02-044 | SwitchLeaderboard.tsx:235-242 | `t("leaderboard.methodology.link", "Full methodology →")`; ro:494 / en:1240 | `"Full methodology →"`; `"<a href=\"https://github.com/nedaktov-ops/parlament-deschis/blob/main/docs/METHODOLOGY.md\" target=\"_blank\" rel=\"noreferrer\">"` | external anchor; no JS handler. `rel` differs from C02-038 (`"noopener noreferrer"`) | external URL | WORKING-AS-CODED |
| C02-045 | CoverageView.tsx:116-119 (`onRetry`) | `t("coverageLoadError")` ro:301 / en:1048; `emptyTitle` `t("coverage.empty", ...)` ro:744 / en:1498 | `"onRetry={() => { void coverage.refetch(); void dimensions.refetch(); }}"` (full-page state branch :111-124) | two refetches → `api.coverage_detailed` (`:49-52`; `client.ts:552`) and `api.coverageDimensions` (`:56-59`; `client.ts:553`) | state action | WORKING-AS-CODED |
| C02-046 | CoverageView.tsx:128 | `t("scope.note.coverage")`; ro:92 / en:846; child labels `t("filter.chamber")` ro:610/en:1313, `t("filter.legislature")` ro:613/en:1316 | `"<ScopeControls showChamber showLegislature note={t("scope.note.coverage")} />"`; `"Chamber/legislature are client-side row filters on the data-availability matrix"` (61-62) | `ScopeControls.tsx:40-55` selects → `setScope` → `useScope.ts:51-65`; `rows`/`dimRows` useMemo (63-78) filter client-side; stays on `/coverage` | state action (route search) | WORKING-AS-CODED |
| C02-047 | InstitutionalView.tsx:45-56 | `t("asOf")`; ro:76 / en:830 | `"onChange={(event) => { if (event.target.value) { navigate({ search: scope.searchFor({ date: event.target.value }), replace: true }); } }}"` | `<input id="institutional-as-of" type="date" max={today}>` → `navigate` with `from: "/institutional"` (11), no `to`, `replace: true` (52); `committees`/`crossChamber` queries keyed on `asOf` (16-23) | state action (route search) | WORKING-AS-CODED |
| C02-048 | InstitutionalView.tsx:65 (`onRetry`) | `t("institutionalLoadError")` ro:174 / en:928; `emptyTitle` `t("committeeDataUnavailable")` ro:181 / en:935 | `"onRetry={() => void committees.refetch()}"` | `ErrorState.tsx:38-45` → `committees.refetch()` → `api.committees(asOf)` (:16-19; `client.ts:905`) | state action | WORKING-AS-CODED |
| C02-049 | InstitutionalView.tsx:90 (`onRetry`) | `t("institutionalLoadError")` ro:174 / en:928; `emptyTitle` `t("crossChamberNoData")` ro:185 / en:939 | `"onRetry={() => void crossChamber.refetch()}"` | `ErrorState.tsx:38-45` → `crossChamber.refetch()` → `api.crossChamber(asOf)` (:20-23; `client.ts:534`) | state action | WORKING-AS-CODED |
| C02-050 | SenateHistory.tsx:75 | `t("scope.note.coverage")` ro:92 / en:846; child label `t("filter.legislature")` ro:613 / en:1316 | `"<ScopeControls showLegislature note={t("scope.note.coverage")} />"`; `"Legislature is a client-side row filter persisted in the URL."` (50) | `ScopeControls.tsx:51-55` → `setScope` → `useScope.ts:51-65`; `allRows` filter (51-54) | state action (route search) | WORKING-AS-CODED |
| C02-051 | SenateHistory.tsx:66 (`onRetry`) | `t("senate.history.loadError", "Senate historical coverage could not be loaded.")` ro:745 / en:1499 | `"onRetry={() => void coverage.refetch()}"` (full-page state branch :61-71) | `ErrorState.tsx:38-45` → `coverage.refetch()` → `api.coverage_detailed` (:41-44; `client.ts:552`) | state action | WORKING-AS-CODED |
| C02-052 | LegislatureDetail.tsx:66 (`onRetry`) | `pageTitle={`${t("legislature")} ${year}`}` ro:194 / en:948; `t("chamberLoadError")` ro:123 / en:877 | `"onRetry={() => void meta.refetch()}"` (meta state branch :61-70) | `ErrorState.tsx:38-45` → `meta.refetch()` → `api.meta` (:23) | state action | WORKING-AS-CODED |
| C02-053 | LegislatureDetail.tsx:158 (`onRetry`) | `t("chamberLoadError")` ro:123 / en:877; `emptyTitle={t("noData")}` ro:214 / en:961 | `"onRetry={() => void chamber.refetch()}"` | `ErrorState.tsx:38-45` → `chamber.refetch()` → `api.chamber(chamberFilter, selectedDate)` (:39-43) | state action | WORKING-AS-CODED |
| C02-054 | LegislatureDetail.tsx:181 (`onRetry`) | `t("electoralLoadError")` ro:172 / en:926; `emptyTitle={t("noData")}` ro:214 / en:961 | `"onRetry={() => void movements.refetch()}"` | `ErrorState.tsx:38-45` → `movements.refetch()` → `api.movements({ from: start, to: selectedDate, limit: 1000, chamber: chamberFilter, legislature: year })` (:44-54) | state action | WORKING-AS-CODED |
| C02-055 | LegislatureDetail.tsx:191-213 | row content `{m.type}`, `{m.event_date}`, `{m.person?.name ?? "—"}` (204-211); region aria `t("recentMovements", "Recent movements")` ro:102 / en:856 | `"<button type="button" key={m.id} disabled={!m.person} onClick={() => { if (m.person) { navigate({ to: "/person/$id", params: { id: m.person.id }, search: scope.searchFor({ date: selectedDate }) }) } }}>"` | `navigate` → `personRoute` `path: "/person/$id"` (router.tsx:378-383). Rendered only for `movements.data?.slice(0, 20)` (:190) of the 1000-row fetch (:49); disabled when `!m.person` | in-app route | WORKING-AS-CODED |
| C02-056 | ScopeControls.tsx:32-34 (definition; instances via C02-041/046/050) | `t("asOf")`; ro:76 / en:830 | `"<input id="scope-date" type="date" className={inputCls} min="1990-01-01" max={today} value={scope.date}"` | `onChange={(e) => { if (e.target.value) scope.setScope({ date: e.target.value }); }}` (34) → `useScope.ts:49-68` in-place navigate. Rendered only when `showDate` (29); none of the three page call sites sets it | state action (route search) | WORKING-AS-CODED |
| C02-057 | ScopeControls.tsx:40-45 (definition; instances via C02-041/046) | `t("filter.chamber", "Chamber")` ro:610 / en:1313; options `t("scope.allChambers")` ro:78/en:832, `t("deputies")` ro:74/en:828, `t("senate")` ro:75/en:829 | `"onChange={(e) => scope.setScope({ chamber: (e.target.value \|\| undefined) as "deputies" \| "senate" \| undefined })}"` (41) | `setScope` → `useScope.ts:51-65`; `value={scope.chamber ?? ""}` (40) | state action (route search) | WORKING-AS-CODED |
| C02-058 | ScopeControls.tsx:51-55 (definition; instances via C02-041/046/050) | `t("filter.legislature", "Legislature")` ro:613 / en:1316; option `t("scope.allLegislatures")` ro:79 / en:833 | `"onChange={(e) => scope.setScope({ legislature: e.target.value \|\| undefined })}"` (52) | `setScope` → `useScope.ts:51-65`; option list from `/api/meta` (19-22) with `FALLBACK_LEGISLATURES` (14) | state action (route search) | WORKING-AS-CODED |

**Shared handler terminal (not a rendered element, so outside the count).** `frontend/src/hooks/useScope.ts:49-68`:
```
49:  const setScope = useCallback(
50:    (patch: Partial<Scope>) => {
51:      navigate({
55:        search: (prev) => {
56:          const merged = { ...(prev as Record<string, unknown>), ...patch };
57:          return {
58:            ...merged,
59:            date: merged.date as string,
60:            chamber: merged.chamber as ChamberScope | undefined,
61:            legislature: merged.legislature as string | undefined,
62:          };
63:        },
64:        replace: false, // back/forward must step through filter changes (FN-7)
65:      });
```
`navigate` is anchored `from: "/"` (`:38`), all three canonical keys are emitted, and page-local params survive via the functional updater (`:52-54` comment). This is the terminal for C02-006, 022, 023, 024, 041, 046, 050, 056, 057, 058. Verdict WORKING-AS-CODED.

## 2. Route-target cross-check (router.tsx)

Every `to:` emitted by an assigned page resolves to a registered route: `/mps` (`router.tsx:449-454`), `/traseism` (`:392-397`), `/committees` (`:428-433`), `/parties` (`:470-475`), `/person/$id` (`:378-383`), `/party/$shortName` (`:371-376`). `SwitchLeaderboard` and `InstitutionalView` navigate with no `to` and an explicit `from` (`:22`, `:11`), so they stay on `/leaderboard` (`:414-419`) and `/institutional` (`:364-369`). Every route uses `validateScopeSearch` (`:43-56`), which materialises `date`/`chamber`/`legislature`; `stringifySearch`/`parseSearch` are wired at `:570-577`. No `to:` in this slice points at an unregistered path.

## 3. Findings with evidence

### F1 — Four dashboard metric cards navigate without scope (C02-002…005) — SUSPECT

**Evidence**
```
LiveDashboard.tsx:132-142   <DashboardCard title={t("dashboardStatPersons", "Members of Parliament")}
...                           value={stats?.persons ?? "--"}
140:                           linkTo="/mps"
141:                           color="sky" />
...                           (same at :151 linkTo="/mps", :162 linkTo="/traseism", :174 linkTo="/committees")
DashboardCard.tsx:79-84     if (linkTo) {
                              return (
                                <Link to={linkTo} search={searchParams} className={cardClass}>
...
```
The `DashboardCardProps` includes `searchParams?: Record<string, string>` (`DashboardCard.tsx:9`), but none of the four call sites passes it. By contrast the page's other navigations explicitly pass `search: scope.searchFor({ date: clamped })` (`:90`, `:98`, `:220`, `:261`, `:277`, `:300`).

**Reason.** The links are live and their targets are registered, so they are not broken; however the code shows `search={undefined}` on all four, so the selected `date`/`chamber`/`legislature` are not carried to the destination. `useScope.ts:40` falls back to `localISODate()` when no `date` is in the URL, and `:41-46` resolve missing chamber/legislature to `undefined`. Code-grounded SUSPECT, not BROKEN.

**Improvement.** At `LiveDashboard.tsx:140`, `:151`, `:162`, `:174`, add `searchParams={scope.searchFor({ date: clamped })}` to each `<DashboardCard>` so the four cards behave like C02-009/016/020. (`searchFor` returns `ScopeSearch`, `useScope.ts:69-72`; the prop type is `Record<string, string>` so a cast/type widening in `DashboardCard.tsx:9` may also be required.)

### F2 — Wave click ignores the wave and hardcodes the destination scope (C02-018) — SUSPECT

**Evidence**
```
LiveDashboard.tsx:103-112  const waveData: SwitchWaveData[] = waves.map(w => ({
...  110:    legislature: w.legislature,
111:    chamber: w.chamber,
...
277:  onWaveClick={() => navigate({ to: "/traseism", search: scope.searchFor({ date: clamped, chamber: "deputies", legislature: undefined }) })}
SwitchTimeline.tsx:186   onClick={() => onWaveClick?.(wave)}
SwitchTimeline.tsx:187   onKeyDown={(e) => activateOnKey(e, () => onWaveClick?.(wave))}
SwitchTimeline.tsx:214-231  "View all →" button also calls onWaveClick({ id: "all", ... })
i18n.ts:632 (ro) / :1379 (en)  "Each bar is a wave of group switches across the whole corpus; select one for details."
```

**Reason.** The child passes the clicked `wave` (including `wave.chamber` and `wave.legislature`, which the page itself mapped at `:110-111`) to `onWaveClick`, but the page arrow at `:277` declares no parameter and always emits `chamber: "deputies", legislature: undefined`. Keyboard and the "View all →" button go through the same handler. The prose explicitly promises "select one for details"; the code delivers the same generic destination for every wave. This is a wiring/intent mismatch that is fully visible in code — SUSPECT, not BROKEN (the navigation and the target route both exist).

**Improvement.** At `LiveDashboard.tsx:277`, accept the wave: `onWaveClick={(wave) => navigate({ to: "/traseism", search: scope.searchFor({ date: clamped, chamber: wave.chamber === "senate" ? "senate" : "deputies", legislature: wave.legislature ?? undefined }) })}` (guard `wave` for the synthetic `{id:"all"}` object from `SwitchTimeline.tsx:218-227`), or update the copy at i18n `:632`/`:1379` if the generic destination is intentional.

### F3 — Ledger page is never clamped when the row count shrinks (C02-027) — SUSPECT

**Evidence**
```
Traseism.tsx:292   const [page, setPage] = useState(0);
294-296:           useEffect(() => { setPage(0); }, [legislature, chamber]);
298-307:           const query = useQuery({ queryKey: ["traseism-switches", legislature, chamber, page, ...scopeKey],
                       queryFn: () => traseismSwitches({ legislature, chamber, limit: PAGE_SIZE, offset: page * PAGE_SIZE }) });
310-313:           const total = query.data?.total ?? 0;
311:                const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
312:                const from = total === 0 ? 0 : page * PAGE_SIZE + 1;
313:                const to = Math.min((page + 1) * PAGE_SIZE, total);
414-426:           Previous disabled={page === 0} ... Next disabled={(page + 1) * PAGE_SIZE >= total}
```

**Reason.** The reset effect depends only on `[legislature, chamber]` (`:296`). `scopeKey` (which contains `date` and chamber/legislature, `useScope.ts:21-23`) is part of the query key at `:299`, so a date/scope change refetches new data and can reduce `total` without resetting `page`. There is no effect clamping `page` to `totalPages - 1`; `Next` then becomes disabled at `:422` while `page` remains out of range, and `from` (`:312`) can exceed `to` (`:313`). The two buttons themselves are wired correctly (Prev disabled at 0, Next disabled at the end), so this is a state-bounds defect, not a broken handler — SUSPECT.

**Improvement.** Add `useEffect(() => setPage((p) => Math.min(p, Math.max(0, totalPages - 1))), [totalPages]);` after `Traseism.tsx:311`, and include `scopeKey`/the date in the reset dependency list at `:296` so a scope change starts at page 0.

### F4 — Chair button can be a silent no-op (C02-011) — SUSPECT

**Evidence**
```
LiveDashboard.tsx:227  onChairClick={(chair) => chair.chair_person_id && openPerson(chair.chair_person_id)}
CommitteeControl.tsx:97-116  <button ... onClick={() => chairForParty && onChairClick?.(chairForParty)}>  (no disabled prop)
CommitteeControl.tsx:17   chair_person_id: string;   (type says present, not non-empty)
```

**Reason.** Both the child and the page guard on truthiness. If `chair_person_id` is `""` (or the `find` at `CommitteeControl.tsx:89` returns `undefined`), clicking the enabled bar produces no navigation, no state change and no user feedback. The concrete value is backend data, so the frequency cannot be established from code; the possibility is coded.

**Resolver / improvement.** Resolver for the actual data: backend `committeeControl` endpoint via `frontend/src/api/client.ts:953` (out of slice). At `LiveDashboard.tsx:227`, add an explicit else branch (e.g. navigate to `/committees`) or filter out chairless parties in `CommitteeControl.tsx:86-89` and disable the bar there.

### F5 — Traseism About button: modal can open (C02-039) — WORKING-AS-CODED (confirmation, no change needed)

**Evidence**
```
Traseism.tsx:660   const [aboutOpen, setAboutOpen] = useState(false);
Traseism.tsx:950-956  <button type="button" onClick={() => setAboutOpen(true)} className={...}>{t("traseismAboutButton")}</button>
Traseism.tsx:960   <About open={aboutOpen} onClose={() => setAboutOpen(false)} />
About.tsx:95      export default function About({ open, onClose }: { open: boolean; onClose: () => void }) {
About.tsx:139     if (!open) return null;
About.tsx:159-169 <div className="fixed inset-0 ..."> <div role="dialog" aria-modal="true" ...>
About.tsx:116-128 useEffect: "if (e.key === \"Escape\") onClose();"  (listener added only when open)
About.tsx:162     <div ... onClick={onClose}>   (backdrop)
About.tsx:170     <div ... onClick={(e) => e.stopPropagation()}>   (panel)
About.tsx:197-203 <button type="button" ref={closeRef} ... onClick={onClose} aria-label={t("close")}>{t("close")}</button>
```

**Reason.** The state is a plain `useState(false)` → button sets `true` → the `open` prop flips → the `if (!open) return null` guard at `About.tsx:139` no longer short-circuits and the dialog renders. All three close paths call `onClose`, which the page maps back to `setAboutOpen(false)`, so the modal unmounts again. There is no stale state, no competing owner and no missing callback in this chain. Verdict WORKING-AS-CODED. The modal's own close/accordion/source-link controls are inventoried by C‑05 and C01 (C01-004…007, C01-049…055) and are not duplicated here.

**Improvement.** None needed for the open/close chain.

### F6 — LiveFeed receives hard-coded scope defaults (observation on C02-020; element verdict unchanged)

**Evidence**
```
LiveDashboard.tsx:297-301  <LiveFeed
298:    legislature={scope.legislature ?? "2024"}
299:    chamber={scope.chamber ?? "senate"}
300:    onSelect={(id) => navigate({ to: "/person/$id", params: { id }, search: scope.searchFor({ date: clamped }) })}
301:  />
useScope.ts:41-46  chamber/legislature are undefined when not requested
LiveFeed.tsx:43-45 queryFn: () => api.recentEvents(40, chamber ?? undefined, legislature ?? undefined)
LiveFeed.tsx:142-151 scopeLabel built from those props
```

**Reason.** When `useScope` reports no chamber/legislature filter, the page still asserts `senate`/`2024` to the feed. The click handler on the feed row (`:300`) itself navigates correctly with the *real* scope via `scope.searchFor`, so C02-020 stays WORKING-AS-CODED; this is a data-context discrepancy, not an interactivity defect.

**Improvement.** At `LiveDashboard.tsx:298-299`, pass `legislature={scope.legislature}` and `chamber={scope.chamber}` (both accept `null`/`undefined` per `LiveFeedProps` at `LiveFeed.tsx:10-14`) if "no filter" is the intended default; otherwise document the deliberate senate/2024 default in the UI.

### F7 — Data-driven official-source anchors cannot be validated from code (C02-025) — NOT PROVEN

**Evidence**
```
Traseism.tsx:390-398  {row.source_url ? (
                        <a href={row.source_url} target="_blank" rel="noopener noreferrer" className={...}>
                          {t("traseismOfficialSource")} ↗
                        </a>
                      ) : (
                        <span className="text-slate-500">{t("traseismNoSource")}</span>
                      )}
Traseism.tsx:298-307  queryFn: () => traseismSwitches({ legislature, chamber, limit: PAGE_SIZE, offset: page * PAGE_SIZE })
client.ts:764-778    traseismSwitches(...) builds URLSearchParams and returns get(`/traseism/switches${qs ? `?${qs}` : ""}`)
```

**Reason.** The click target and the `href` binding are fully coded, but the concrete `source_url` string is returned by the backend and is not present in the repository. Repo code cannot establish whether a given URL is well-formed or reachable. Per the slice convention (cf. C01-049), verdict NOT PROVEN for the destination value.

**Resolver.** Backend `/api/traseism/switches` payload via `frontend/src/api/client.ts:764-778` (out of slice); live HTTP state would be a runtime question, not a code verdict. No network calls were made.

## 4. i18n definition index (both locales, verbatim)

Labels of the inventoried elements resolve as follows. `ro` locale is the configured default (`i18n.ts:1516-1521`: `lng: "ro"`, `fallbackLng: "en"`), so the quoted `ro` text is what renders unless the user switches language (switcher in `router.tsx:254-259`, inventoried by C01).

| Key | ro definition | en definition |
| --- | --- | --- |
| `dashboardStatPersons` | `i18n.ts:13` `"dashboardStatPersons: \"Parlamentari\""` | `:768` `"dashboardStatPersons: \"Members of Parliament\""` |
| `dashboardStatMemberships` | `:12` `"dashboardStatMemberships: \"Mandate\""` | `:767` `"dashboardStatMemberships: \"Memberships\""` |
| `dashboardStatSwitches` | `:10` `"dashboardStatSwitches: \"Toate schimbările observate de afiliere\""` | `:765` `"dashboardStatSwitches: \"All observed affiliation changes\""` |
| `dashboardStatCommittees` | `:11` `"dashboardStatCommittees: \"Comisii\""` | `:766` `"dashboardStatCommittees: \"Committees\""` |
| `navigateTo` | `:101` `"navigateTo: \"Navighează către\""` | `:855` `"navigateTo: \"Navigate to\""` |
| `dashboard.loadError` | `:756` `"\"dashboard.loadError\": \"Datele panoului nu au putut fi încărcate.\""` | `:1510` `"\"dashboard.loadError\": \"Dashboard data could not be loaded.\""` |
| `chamberEvolutionTitle` | `:195` `"chamberEvolutionTitle: \"Compoziția camerelor pe legislaturi\""` | `:949` `"chamberEvolutionTitle: \"Chamber composition by legislature\""` |
| `chamberEvolutionSelect` | `:198` `"chamberEvolutionSelect: \"Selectează legislatura după anul de start\""` | `:952` `"chamberEvolutionSelect: \"Select legislature by start year\""` |
| `chamberEvolutionPrev` | `:199` `"chamberEvolutionPrev: \"Legislatura anterioară\""` | `:953` `"chamberEvolutionPrev: \"Previous legislature\""` |
| `chamberEvolutionNext` | `:200` `"chamberEvolutionNext: \"Legislatura următoare\""` | `:954` `"chamberEvolutionNext: \"Next legislature\""` |
| `play` / `pause` | `:96` `"play: \"Redă\""` / `:97` `"pause: \"Pauză\""` | `:850` `"play: \"Play\""` / `:851` `"pause: \"Pause\""` |
| `a11y.partyNode` | `:132` `"\"a11y.partyNode\": \"Partidul {{party}}: {{members}} de membri\""` | `:886` `"\"a11y.partyNode\": \"Party {{party}}: {{members}} members\""` |
| `a11y.committeeChair` | `:129` `"\"a11y.committeeChair\": \"Arată președintele {{party}}\""` | `:883` `"\"a11y.committeeChair\": \"Show chair for {{party}}\""` |
| `a11y.switchWave` | `:139` `"\"a11y.switchWave\": \"Valul de schimbări de la {{date}}: {{count}} de schimbări\""` | `:893` `"\"a11y.switchWave\": \"Switch wave on {{date}}: {{count}} switches\""` |
| `deepDiveSwitchTimelineDesc` | `:632` `"deepDiveSwitchTimelineDesc: \"Fiecare bară arată numărul de schimbări de grup într-un val, în tot corpusul; apasă pentru detalii.\""` | `:1379` `"deepDiveSwitchTimelineDesc: \"Each bar is a wave of group switches across the whole corpus; select one for details.\""` |
| `crossChamberMPs` | `:184` `"crossChamberMPs: \"Carieră în ambele camere\""` | `:938` `"crossChamberMPs: \"Careers in both chambers\""` |
| `crossChamberTableCaption` | `:188` `"crossChamberTableCaption: \"Parlamentari care au avut mandate în Camera Deputaților și Senat\""` | `:942` `"crossChamberTableCaption: \"People who held mandates in both the Chamber of Deputies and Senate\""` |
| `switchAlerts.view` | `:727` `"switchAlerts.view: \"vezi\""` | `:1481` `"switchAlerts.view: \"view\""` |
| `traseismOfficialSource` | `:353` `"traseismOfficialSource: \"sursa oficială\""` | `:1100` `"traseismOfficialSource: \"official source\""` |
| `traseismNoSource` | `:354` `"traseismNoSource: \"fără sursă\""` | `:1101` `"traseismNoSource: \"no source\""` |
| `traseismPreviousPage` | `:360` `"traseismPreviousPage: \"Pagina anterioară\""` | `:1106` `"traseismPreviousPage: \"Previous page\""` |
| `traseismNextPage` | `:361` `"traseismNextPage: \"Pagina următoare\""` | `:1107` `"traseismNextPage: \"Next page\""` |
| `traseismPage` | `:362` `"traseismPage: \"Pagina {{page}} din {{pages}}\""` | `:1108` `"traseismPage: \"Page {{page}} of {{pages}}\""` |
| `traseismLedgerDesc` | `:350-351` `"traseismLedgerDesc: \"Fiecare schimbare citată, cu data și linkul către documentul oficial din care a fost citită.\""` | `:1097-1098` `"traseismLedgerDesc: \"Every cited switch, with its date and a link to the official document it was read from.\""` |
| `chamber` | `:250` `"chamber: \"Cameră\""` | `:997` `"chamber: \"Chamber\""` |
| `legislature` | `:194` `"legislature: \"Legislatura\""` | `:948` `"legislature: \"Legislature\""` |
| `deputies` | `:74` `"deputies: \"Camera Deputaților\""` | `:828` `"deputies: \"Chamber of Deputies\""` |
| `senate` | `:75` `"senate: \"Senat\""` | `:829` `"senate: \"Senate\""` |
| `traseismMembersDenominator` | `:315` `"traseismMembersDenominator: \"Membri în perimetrul de analiză (numitor)\""` | `:1062` `"traseismMembersDenominator: \"Members in scope (denominator)\""` |
| `traseismSwitchesCount` | `:316` `"traseismSwitchesCount: \"Schimbări de grup\""` | `:1063` `"traseismSwitchesCount: \"Group switches\""` |
| `traseismSwitchersCount` | `:317` `"traseismSwitchersCount: \"Parlamentari care au schimbat grupul\""` | `:1064` `"traseismSwitchersCount: \"Members who switched group\""` |
| `traseismSwitchRate` | `:318` `"traseismSwitchRate: \"Rata de traseism\""` | `:1065` `"traseismSwitchRate: \"Switch rate\""` |
| `traseismPer100` | `:320` `"traseismPer100: \"Schimbări la 100 de membri\""` | `:1067` `"traseismPer100: \"Switches per 100 members\""` |
| `traseismLoadError` | `:363-364` `"\"traseismLoadError\": \"Datele nu au putut fi încărcate. Nu afișăm cifre pe care nu le putem verifica.\""` | `:1109-1110` `"\"traseismLoadError\": \"The data could not be loaded. We do not show figures we cannot verify.\""` |
| `traseismNoRows` | `:357-358` `"traseismNoRows: \"Nu există schimbări de grup înregistrate pentru acest domeniu.\""` | `:1104` `"traseismNoRows: \"No group switches are recorded for this scope.\""` |
| `waves.error` | `:736` `"\"waves.error\": \"Nu s-au putut încărca valurile.\""` | `:1490` `"\"waves.error\": \"Failed to load waves.\""` |
| `waves.empty` | `:735` `"\"waves.empty\": \"Nu au fost detectate valuri pentru acest domeniu.\""` | `:1489` `"\"waves.empty\": \"No waves detected for this scope.\""` |
| `noData` | `:214` `"noData: \"Nu există date pentru această perioadă\""` | `:961` `"noData: \"No data for this period\""` |
| `traseismMethodologyLink` | `:380-381` `"traseismMethodologyLink: \"Citește metodologia completă (docs/METHODOLOGY.md)\""` | `:1126-1127` `"traseismMethodologyLink: \"Read the full methodology (docs/METHODOLOGY.md)\""` |
| `traseismAboutButton` | `:382` `"traseismAboutButton: \"Despre proiect și metodă\""` | `:1128` `"traseismAboutButton: \"About the project and the method\""` |
| `traseismRetry` | `:365` `"traseismRetry: \"Reîncearcă\""` | `:1111` `"traseismRetry: \"Try again\""` |
| `retry` | `:271` `"retry: \"Reîncearcă\""` | `:1018` `"retry: \"Retry\""` |
| `close` | `:272` `"close: \"Închide\""` | `:1019` `"close: \"Close\""` |
| `about` | `:268` `"about: \"Despre\""` | `:1015` `"about: \"About\""` |
| `leaderboard.title` | `:498` `"\"leaderboard.title\": \"Clasamentul schimbărilor de partid\""` | `:1244` `"\"leaderboard.title\": \"Party Switching Leaderboard\""` |
| `leaderboard.error` | `:486` `"\"leaderboard.error\": \"Nu s-a putut încărca clasamentul.\""` | `:1232` `"\"leaderboard.error\": \"Failed to load leaderboard.\""` |
| `leaderboard.empty` | `:485` `"\"leaderboard.empty\": \"Nu există date despre schimbări pentru acest domeniu.\""` | `:1231` `"\"leaderboard.empty\": \"No switch data available for this scope.\""` |
| `leaderboard.filter.limit` | `:489` `"\"leaderboard.filter.limit\": \"Arată primii\""` | `:1235` `"\"leaderboard.filter.limit\": \"Show top\""` |
| `leaderboard.col.name` | `:482` `"\"leaderboard.col.name\": \"Parlamentar\""` | `:1228` `"\"leaderboard.col.name\": \"MP\""` |
| `leaderboard.methodology.link` | `:494` `"\"leaderboard.methodology.link\": \"Metodologie completă →\""` | `:1240` `"\"leaderboard.methodology.link\": \"Full methodology →\""` |
| `coverageLoadError` | `:301` `"coverageLoadError: \"Nu s-au putut încărca datele de calitate.\""` | `:1048` `"coverageLoadError: \"Could not load coverage data.\""` |
| `coverage.empty` | `:744` `"\"coverage.empty\": \"Nu există înregistrări de acoperire pentru acest domeniu.\""` | `:1498` `"\"coverage.empty\": \"There are no coverage records for this scope.\""` |
| `filter.chamber` | `:610` `"\"filter.chamber\": \"Camera\""` | `:1313` `"\"filter.chamber\": \"Chamber\""` |
| `filter.legislature` | `:613` `"\"filter.legislature\": \"Legislatură\""` | `:1316` `"\"filter.legislature\": \"Legislature\""` |
| `scope.allChambers` | `:78` `"\"scope.allChambers\": \"Toate camerele\""` | `:832` `"\"scope.allChambers\": \"All chambers\""` |
| `scope.allLegislatures` | `:79` `"\"scope.allLegislatures\": \"Toate legislaturile\""` | `:833` `"\"scope.allLegislatures\": \"All legislatures\""` |
| `scope.note.coverage` | `:92` `"\"scope.note.coverage\": \"Acoperirea este o matrice de disponibilitate a datelor pe cameră și legislatură, nu o imagine la o dată anume.\""` | `:846` `"\"scope.note.coverage\": \"Coverage is a data-availability matrix by chamber × legislature, not a point-in-time snapshot.\""` |
| `asOf` | `:76` `"asOf: \"La data de\""` | `:830` `"asOf: \"As of\""` |
| `institutionalLoadError` | `:174` `"institutionalLoadError: \"Datele instituționale nu au putut fi încărcate.\""` | `:928` `"institutionalLoadError: \"Institutional data could not be loaded.\""` |
| `committeeControl.loadError` | `:751` `"\"committeeControl.loadError\": \"Datele privind controlul comisiilor nu au putut fi încărcate.\""` | `:1505` `"\"committeeControl.loadError\": \"Committee control data could not be loaded.\""` |
| `committeeDataUnavailable` | `:181` `"committeeDataUnavailable: \"Datele despre comisii nu sunt incluse în baza actuală.\""` | `:935` `"committeeDataUnavailable: \"Committee data is not included in the current dataset.\""` |
| `crossChamberNoData` | `:185` `"crossChamberNoData: \"Nu sunt înregistrate mandate în ambele camere până la data selectată.\""` | `:939` `"crossChamberNoData: \"No mandates in both chambers are recorded by the selected date.\""` |
| `senate.history.loadError` | `:745` `"\"senate.history.loadError\": \"Acoperirea istorică a Senatului nu a putut fi încărcată.\""` | `:1499` `"\"senate.history.loadError\": \"Senate historical coverage could not be loaded.\""` |
| `legislatureUnknown` | `:204` `"legislatureUnknown: 'Legislatură necunoscută \"{{year}}\". Acest corpus nu are metadate pentru anul respectiv, deci nu afișăm cifre.'"` | `:1393` `"legislatureUnknown: 'Unknown legislature \"{{year}}\". This corpus has no metadata for that year, so no figures are shown.'"` |
| `chamberLoadError` | `:123` `"chamberLoadError: \"Compoziția camerei nu a putut fi încărcată.\""` | `:877` `"chamberLoadError: \"Chamber composition could not be loaded.\""` |
| `electoralLoadError` | `:172` `"electoralLoadError: \"Schimbările nu au putut fi încărcate.\""` | `:926` `"electoralLoadError: \"Changes could not be loaded.\""` |
| `recentMovements` | `:102` `"recentMovements: \"Mișcări recente\""` | `:856` `"recentMovements: \"Recent movements\""` |
| `state.empty.dataQuality` | `:743` `"\"state.empty.dataQuality\": \"Nu există date de acoperire de afișat.\""` | `:1497` `"\"state.empty.dataQuality\": \"There are no coverage records to show.\""` |

Notes on key resolution:
- `t("deputies")` / `t("senate")` in `Traseism.tsx:78 chamberLabel()` are literal keys with definitions at `:74`/`:75` (ro) and `:828`/`:829` (en); the non-chamber fallback returns the raw API string unchanged.
- `Traseism.tsx:136 t(key)` with `key ∈ {"full","partial","none"}` resolves to `:115`/`:116`/`:117` (ro) and `:869`/`:870`/`:871` (en).
- `Traseism.tsx:412 t("traseismShowing", {from,to,total})` → ro `:359` / en `:1105`; the page counter is plain text, not a control.
- No call site in this slice uses a key absent from `i18n.ts`; inline fallback strings (e.g. `"Switch waves"`, `"View all →"`) are authored in the components and are not i18n keys.

## 5. Coverage and NOT PROVEN

**Covered in full:** all ten assigned files; every `<button>`, `<a>`, `<Link>`, mapped button instance, `role="button"` SVG rect, `onKeyDown` activator, `onClick`/`onChange` handler, programmatic `navigate`/`setScope`, and every `onRetry` call site. 58 inventory rows were produced. All `to:` targets were cross-checked against the route tree (`router.tsx:334-544`); all i18n labels used by those controls were resolved in both locales. Child components were opened only where a page callback had to be followed (`DashboardCard`, `PartyListTable`, `PartyNetwork`, `CommitteeControl`, `LegislatureSeatExplorer` → `ChamberView` → `Hemicycle`, `CrossChamberFlow`, `SwitchTimeline`, `LiveFeed`, `AsyncState` → `ErrorState` → `RetryButton`, `DataQualityGauge`, `About`, `utils/a11y.ts`); their remaining controls are C‑05's inventory.

**Classification tally:** in-app route = 14 (C02-007, 008, 009, 011, 015, 016, 018, 019, 020, 043, 055 + the four SUSPECT cards C02-002…005); external URL = 3 (C02-025, 038, 044); `API/download` = 0; `state action` = 41 (all remaining rows, including route-search updates that stay on the same page); `no-op` = 0; `dead` = 0. 14 + 3 + 41 = 58.

**NOT PROVEN items and resolvers**
1. C02-025 — concrete `row.source_url` value for each ledger "official source ↗" anchor. Resolver: backend `/api/traseism/switches` payload via `frontend/src/api/client.ts:764-778` (out of slice). Code proves the binding and conditional rendering, not the URL value.
2. C02-008 / C02-015 — whether a party with an empty `short_name` (falling back to `party.id`/`node.id` at `PartyListTable.tsx:64` and `PartyNetwork.tsx:105`) is a valid `shortName` for `PartyProfile`. Resolver: party payload fields from `api.parties` and the out-of-slice `frontend/src/pages/PartyProfile.tsx`.
3. C02-020 — whether the `LiveFeed` rows show the intended corpus slice given the page's `?? "2024"` / `?? "senate"` defaults (`:298-299`). Resolver: backend `/api/events/recent` scope semantics and product intent; the click handler at `:300` is fully wired (F6).
4. C02-011 — how often `chair_person_id` is empty. Resolver: backend `/api/committee-control` via `frontend/src/api/client.ts:953` (F4).
5. Runtime outcomes of every `refetch()` and of each external URL are not asserted: this is a static code inventory, no network calls and no browser observations were made.

**Additional observations (not separate element defects)**
- No `<form>` submit, `<a download>`, `window.open`, `window.print`, `role="button"` on an HTML element, or bare `onClick` with an empty body exists in the assigned files. The only `role="button"` is the SVG `<rect>` in `SwitchTimeline.tsx:179` with both `onClick` and `onKeyDown` (C02-018).
- Disabled states found: `Traseism.tsx:415` (`page === 0`) and `:422` (`(page + 1) * PAGE_SIZE >= total`); `LegislatureDetail.tsx:191` (`!m.person`); `LiveFeed.tsx:255` (`!e.person`); `CrossChamberFlow.tsx:87` (`!onPersonClick`, false from this page); `LegislatureSeatExplorer.tsx:87` (`reducedMotion || stops.length < 2`), `:95` (`index <= 0`), `:134` (`index < 0 || index >= stops.length - 1`). The LegislatureSeatExplorer/LiveFeed/CrossChamberFlow ones are child-internal controls reached through the page call sites C02-006/007/019/020; they are catalogued by C‑05, not repeated as rows here.
- `InstitutionalView` renders committee and cross-chamber person names as static `<span>`/`<th>` (`InstitutionalView.tsx:72`, `:117`), not links; unlike `LegislatureDetail.tsx:191-213`, there is no person-navigation control in those rows. This is an absence, not a clickable element, so it is not a row.
- `SwitchLeaderboard.tsx:24-29`: if the URL carries an out-of-set `limit` (e.g. `37`), `limit` is normalised to `20` for the query and the select, but the URL is only rewritten when the user changes the select. UI and query agree; the URL is transiently stale. No defect verdict assigned.
- `Traseism.tsx:675-679` contains an automatic `setRouteScope({ legislature: matchingLegislature })` effect; it is a programmatic state setter on load, not a clickable element, so it is not a row.
- `CoverageView.tsx:128`, `SenateHistory.tsx:75` and `SwitchLeaderboard.tsx:100` render `ScopeControls`, whose `if (!showDate && !showChamber && !showLegislature && !note) return null` (`ScopeControls.tsx:24`) is not triggered because each call site supplies at least one prop.

Elements: 58 | BROKEN: 0 | SUSPECT: 7 | NOT PROVEN: 1
