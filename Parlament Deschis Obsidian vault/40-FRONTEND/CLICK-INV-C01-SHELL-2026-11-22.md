---
id: CLICK-INV-C01
type: evidence
title: "Clickable inventory — C01 shell and routing (2026-11-22)"
description: "Read-only, code-grounded inventory of every clickable/interactive element in the shell, routing, footer, logo, About modal, state components and devtools slice; cross-checks route/nav parity, the /electoral redirect and the uppercase /Voturi path."
status: active
authority: derived
tags: [type/evidence, lifecycle/active, domain/frontend]
source_paths: [frontend/src/router.tsx, frontend/src/components/Footer.tsx, frontend/src/components/HeaderLogo.tsx, frontend/src/components/About.tsx, frontend/src/components/ui/ThemeToggle.tsx, frontend/src/components/ui/DashboardHeader.tsx, frontend/src/components/ErrorState.tsx, frontend/src/components/LoadingState.tsx, frontend/src/components/EmptyState.tsx, frontend/src/components/RetryButton.tsx, frontend/index.html, scripts/check_routes_nav.mjs, frontend/src/i18n.ts]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Clickable inventory — C01 shell and routing (2026-11-22)

Scope: HEAD `8811216`. All 13 assigned files were read in full (12 slice files plus `frontend/src/i18n.ts` for key resolution). No network calls, no browser testing, no runtime claims. Verdicts describe what the code expresses; where the behaviour cannot be determined from this slice, the verdict is `NOT PROVEN` and a resolver is named.

## Table — every clickable/interactive element

Classes: `in-app route` | `external URL` | `API/download` | `state action` | `no-op` | `dead`.
Short i18n notation `ro:NNN / en:NNN` refers to the exact definition lines quoted verbatim in the "i18n definition index" below.

| ID | file:line | label/i18n | purpose (quoted from code/prose) | destination / handler chain | class | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| C01-001 | frontend/src/router.tsx:75 | `t("backHome", "Back to overview")`; ro:385 / en:1131 | "// Branded recovery UI for missing routes and render errors" (68) | `<Link to="/" search={{date: localISODate(), chamber: undefined, legislature: undefined}}>` → `indexRoute` (341-346), target registered at 343 `path: "/"` | in-app route | WORKING-AS-CODED |
| C01-002 | frontend/src/router.tsx:90 | `t("backHome", "Back to overview")`; ro:385 / en:1131 | `RouteError` = root `errorComponent` (338) and `defaultErrorComponent` (576) | `<Link to="/" search={...}>` → `indexRoute` (341-346) | in-app route | WORKING-AS-CODED |
| C01-003 | frontend/src/router.tsx:110-118 (instance definition) | `{children}` (call-site labels, rows C01-012..033) | "// Navigation link component" (95) | `<Link to={to} search={(previous) => ({ ...previous, ...scope.searchFor() })}>` (110-113); `isActive` from `useLocation()` (104-108); `scope` from `useScope()` (105, out of slice) | in-app route | WORKING-AS-CODED (exact `scope.searchFor()` payload out of slice — see NOT PROVEN) |
| C01-004 | frontend/src/router.tsx:138-141 | backdrop (no label) | "// About modal" (121) | `onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}` → `closeAbout` (191) → `setAboutOpen(false)` (188, 191) → `AboutModal open={aboutOpen}` (329) closes | state action | WORKING-AS-CODED |
| C01-005 | frontend/src/router.tsx:148-164 | panel (no label) | focus set on open: `panelRef.current?.focus()` (131) | `onKeyDown`: `e.key === "Escape"` → `onClose()` (149); `Tab` trap queries `'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'` (151-153) and wraps first/last (155-163) | state action | WORKING-AS-CODED |
| C01-006 | frontend/src/router.tsx:169 | `t("close")`; ro:272 / en:1019 | header bar of dialog (167-170) | `<button type="button" ... onClick={onClose}>` → `closeAbout` (191) → `setAboutOpen(false)` | state action | WORKING-AS-CODED |
| C01-007 | frontend/src/router.tsx:178 | verbatim `https://github.com/nedaktov-ops/parlament-deschis` | inside licenses block (174-176) | `<a href=... target="_blank" rel="noopener noreferrer">`; no JS handler | external URL | WORKING-AS-CODED |
| C01-008 | frontend/src/router.tsx:231-233 | `t("skipToContent", "Skip to content")`; ro:724 / en:1478 | skip link before `<header>` (234) | `<a href="#main-content">` → `<main id="main-content" tabIndex={-1}>` (325) | state action (in-page fragment) | WORKING-AS-CODED |
| C01-009 | frontend/src/router.tsx:244-248 | `Search onSelect` prop (label defined in Search.tsx, out of slice) | global search in header (243-260) | `router.navigate({ to: "/person/$id", params: { id }, search: scope.searchFor() })` → `personRoute` (378-383), path 380 `"/person/$id"`, `validateSearch` 382 | in-app route | WORKING-AS-CODED (invocation of `onSelect` lives in Search.tsx — out of slice) |
| C01-010 | frontend/src/router.tsx:249-253 | `t("about")`; ro:268 / en:1015 | header About control (249) | `onClick={() => setAboutOpen(true)}` → state (188) → `<AboutModal open={aboutOpen} onClose={closeAbout} />` (329) | state action | WORKING-AS-CODED |
| C01-011 | frontend/src/router.tsx:254-259 | `i18n.language === "ro" ? "EN" : "RO"`; `aria-label={t("changeLanguage")}` ro:127 / en:881 | language switch (254-259) | `onClick={() => i18n.changeLanguage(i18n.language === "ro" ? "en" : "ro")}` → effect sets `document.documentElement.lang = i18n.language` (195-197) | state action | WORKING-AS-CODED |
| C01-012 | frontend/src/router.tsx:264-266 | `t("overview")`; ro:120 / en:874 | main `<nav aria-label={t("mainNavigation")}>` (263) | `<NavLink to="/">` → `indexRoute` (341-346) | in-app route | WORKING-AS-CODED |
| C01-013 | frontend/src/router.tsx:267-269 | `t("traseismShort")`; ro:304 / en:1051 | main nav (263) | `to="/traseism"` → `traseismRoute` (392-397) | in-app route | WORKING-AS-CODED |
| C01-014 | frontend/src/router.tsx:270-272 | `t("nav.leaderboard", "Leaderboard")`; ro:643 / en:1388 | main nav (263) | `to="/leaderboard"` → `switchLeaderboardRoute` (414-419) | in-app route | WORKING-AS-CODED |
| C01-015 | frontend/src/router.tsx:273-275 | `t("nav.demographics", "Demographics")`; ro:642 / en:1387 | main nav (263) | `to="/demographics"` → `demographicsRoute` (421-426) | in-app route | WORKING-AS-CODED |
| C01-016 | frontend/src/router.tsx:276-278 | `t("nav.committees", "Committees")`; ro:640 / en:1406 | main nav (263) | `to="/committees"` → `committeesRoute` (428-433) | in-app route | WORKING-AS-CODED |
| C01-017 | frontend/src/router.tsx:279-281 | `t("nav.compare", "Compare")`; ro:641 / en:1407 | main nav (263) | `to="/compare"` → `partyComparisonRoute` (435-440) | in-app route | WORKING-AS-CODED |
| C01-018 | frontend/src/router.tsx:282-284 | `t("nav.coalitions", "Coalitions")`; ro:639 / en:1386 | main nav (263) | `to="/coalitions"` → `coalitionsRoute` (442-447) | in-app route | WORKING-AS-CODED |
| C01-019 | frontend/src/router.tsx:285-287 | `t("nav.mps", "MPs")`; ro:645 / en:1397 | main nav (263) | `to="/mps"` → `mpsRoute` (449-454) | in-app route | WORKING-AS-CODED |
| C01-020 | frontend/src/router.tsx:288-290 | `t("nav.report", "Report")`; ro:647 / en:1399 | main nav (263) | `to="/report"` → `reportRoute` (463-468) | in-app route | WORKING-AS-CODED |
| C01-021 | frontend/src/router.tsx:291-293 | `t("nav.parties")`; ro:652 / en:1404 | main nav (263) | `to="/parties"` → `partiesRoute` (470-475) | in-app route | WORKING-AS-CODED |
| C01-022 | frontend/src/router.tsx:294-296 | `t("nav.partyTimeline", "Timeline")`; ro:646 / en:1398 | main nav (263) | `to="/party-timeline"` → `partyTimelineRoute` (477-482) | in-app route | WORKING-AS-CODED |
| C01-023 | frontend/src/router.tsx:297-299 | `t("institutional")`; ro:177 / en:931 | main nav (263) | `to="/institutional"` → `institutionalRoute` (364-369) | in-app route | WORKING-AS-CODED |
| C01-024 | frontend/src/router.tsx:300-302 | `t("coverage")`; ro:114 / en:868 | main nav (263) | `to="/coverage"` → `coverageRoute` (399-404) | in-app route | WORKING-AS-CODED |
| C01-025 | frontend/src/router.tsx:303-305 | `t("nav.senateHistory", t("senate"))`; primary ro:651 / en:1403; fallback ro:75 / en:829 | main nav (263) | `to="/senate-history"` → `senateHistoryRoute` (407-412) | in-app route | WORKING-AS-CODED |
| C01-026 | frontend/src/router.tsx:306-308 | `t("nav.legislature", t("legislature"))`; primary ro:644 / en:1389; fallback ro:194 / en:948 | main nav (263) | `to="/legislature/2024"` → `legislatureRoute` (385-390), param path `/legislature/$year` (387) | in-app route | WORKING-AS-CODED |
| C01-027 | frontend/src/router.tsx:309-311 | `t("party")`; ro:273 / en:1020 | main nav (263) | `to="/party/PSD"` → `partyRoute` (371-376), param path `/party/$shortName` (373) | in-app route | WORKING-AS-CODED |
| C01-028 | frontend/src/router.tsx:315 | `t("nav.compareMps", "Compare MPs")`; ro:654 / en:1408 | analytics `<nav aria-label={t("nav.analytics", "Vote analytics")}>` (313-314) | `to="/compare-mps"` → `mpComparisonRoute` (456-461) | in-app route | WORKING-AS-CODED |
| C01-029 | frontend/src/router.tsx:316 | `t("nav.voturi", "Votes")`; ro:655 / en:1409 | analytics nav (313-314) | `to="/Voturi"` → `voturiRoute` (484-489), path 486 `"/Voturi"` (uppercase) | in-app route | WORKING-AS-CODED |
| C01-030 | frontend/src/router.tsx:317 | `t("nav.radar", "Vote radar")`; ro:656 / en:1410 | analytics nav (313-314) | `to="/radar"` → `radarRoute` (491-496) | in-app route | WORKING-AS-CODED |
| C01-031 | frontend/src/router.tsx:318 | `t("nav.grafice", "Charts")`; ro:657 / en:1411 | analytics nav (313-314) | `to="/grafice"` → `graficeRoute` (498-503) | in-app route | WORKING-AS-CODED |
| C01-032 | frontend/src/router.tsx:319 | `t("nav.topuri", "Vote rankings")`; ro:658 / en:1412 | analytics nav (313-314) | `to="/topuri"` → `topuriRoute` (505-510) | in-app route | WORKING-AS-CODED |
| C01-033 | frontend/src/router.tsx:320 | `t("nav.ideology", "Ideology")`; ro:659 / en:1413 | analytics nav (313-314) | `to="/ideology"` → `ideologyRoute` (512-517) | in-app route | WORKING-AS-CODED |
| C01-034 | frontend/src/router.tsx:348-362 (`beforeLoad` 351-359) | no user-facing label — programmatic route-load redirect | `// Route tree` (334) | `throw redirect({ to: "/traseism", search: { date: search.date, chamber: "deputies", legislature: "2024" } })` (352-359) → `traseismRoute` (392-397); serializer comment 546-549; `stringifySearch` 550-558, `parseSearch` 560-568, wired 572-573 | in-app route (redirect) | WORKING-AS-CODED |
| C01-035 | frontend/src/router.tsx:601 | `<ReactQueryDevtools initialIsOpen={false} />` | imported at 3; mounted in `AppRoot` (597-604) | library-internal toggle; no in-slice handler; no `to`/href/onClick | state action | NOT PROVEN (resolver: `@tanstack/react-query-devtools` implementation + build/env conditions; not present in this slice) |
| C01-036 | frontend/src/components/Footer.tsx:65-70 | `t("overview")`; ro:120 / en:874 | "// Footer #1 multi-column sitemap: logo + link groups" (53) | plain `<a href="/">`, no `search`, no `<Link>`; bypasses NavLink handler at router.tsx:110-118 | in-app route (native anchor) | SUSPECT |
| C01-037 | frontend/src/components/Footer.tsx:73-79 | `t("traseismShort")`; ro:304 / en:1051 | sitemap group (53) | plain `<a href="/traseism">`; no `search`, no `<Link>` | in-app route (native anchor) | SUSPECT |
| C01-038 | frontend/src/components/Footer.tsx:81-87 | `t("nav.report")`; ro:647 / en:1399 | sitemap group (53) | plain `<a href="/report">`; no `search`, no `<Link>` | in-app route (native anchor) | SUSPECT |
| C01-039 | frontend/src/components/Footer.tsx:96-104 | `t("about")`; ro:268 / en:1015 | under `t("nav.company")` heading (91-93) | `<a href="https://github.com/nedaktov-ops/parlament-deschis" target="_blank" rel="noopener noreferrer">` → external; header About button opens local `AboutModal` (router.tsx:249-253, 329) | external URL | SUSPECT (label/destination mismatch — see F2) |
| C01-040 | frontend/src/components/Footer.tsx:106-114 | `t("sources")`; ro:269 / en:1016 | under `t("nav.company")` heading (91-93) | `<a href="https://github.com/nedaktov-ops/parlament-deschis" target="_blank" rel="noopener noreferrer">` → external | external URL | WORKING-AS-CODED |
| C01-041 | frontend/src/components/Footer.tsx:123-129 | `t("coverage")`; ro:114 / en:868 | under `t("nav.resources")` heading (118-120) | plain `<a href="/coverage">`; no `search`, no `<Link>` | in-app route (native anchor) | SUSPECT |
| C01-042 | frontend/src/components/HeaderLogo.tsx:38-46 | `alt="" aria-hidden="true"` (40-41); no label | "If no logo has been uploaded (or the API is offline), fall back to the inline SVG so the header is never blank" (15-16) | `src={`/api/logo?color=${encodeURIComponent(COLORS[theme])}`}` (39) is an API image; `onError={() => setFailed(true)}` (45) → `if (failed)` branch → inline `<svg><BrandMark /></svg>` (29-35); theme from `data-theme` via MutationObserver (22-27) | state action (API image source) | WORKING-AS-CODED |
| C01-043 | frontend/src/components/About.tsx:118-121 | no label — global key handler | modal Esc handling | `document.addEventListener("keydown", onKey)` → `if (e.key === "Escape") onClose();` (119) → `Traseism.tsx:960 onClose={() => setAboutOpen(false)}` | state action | WORKING-AS-CODED (wiring confirmed: `Traseism.tsx:14 import About`, `:952 setAboutOpen(true)`, `:960 <About ... onClose=...>`) |
| C01-044 | frontend/src/components/About.tsx:160-163 | backdrop (no label) | modal shell (159-163) | `onClick={onClose}` → same chain as C01-043; inner clicks stopped by C01-045 (170) | state action | WORKING-AS-CODED |
| C01-045 | frontend/src/components/About.tsx:164-186 | panel (no label) | `role="dialog" aria-modal="true"` (166-167) | `onClick={(e) => e.stopPropagation()}` (170); `onKeyDown` Tab trap over `'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'` (173-175) wrapping first/last (177-185) | state action | WORKING-AS-CODED |
| C01-046 | frontend/src/components/About.tsx:197-203 | `t("close")`; ro:272 / en:1019 | modal header (188-204) | `<button type="button" ref={closeRef} ... onClick={onClose}>` → same chain as C01-043 | state action | WORKING-AS-CODED |
| C01-047 | frontend/src/components/About.tsx:75-87 (component button) | `{title}` prop (81) | accordion trigger | `<button type="button" onClick={onToggle} aria-expanded={open}>` (75-79) → per-instance `onToggle` (rows C01-048, 050, 051, 054) | state action | WORKING-AS-CODED |
| C01-048 | frontend/src/components/About.tsx:237 | `t("sources")`; ro:269 / en:1016 | "// Accordion — sources" (236) | `onToggle={() => setSourcesOpen(!sourcesOpen)}` → state (99), expands/collapses list (88-90) | state action | WORKING-AS-CODED |
| C01-049 | frontend/src/components/About.tsx:246-253 | `{source.name} ↗` (252) — data-driven | source list (243-259) | `<a href={source.url} target="_blank" rel="noopener noreferrer">`; `source` from `data?.sources` (244) fed by `api.about` (104-109) / `coverage.data` (110-114) | external URL | NOT PROVEN (exact URL is backend data. Resolver: backend `/api/about` payload via `api.about`, and `/api/coverage` via `api.coverage`; `frontend/src/api/client.ts` out of slice) |
| C01-050 | frontend/src/components/About.tsx:264 | `t("coverageTable")`; ro:249 / en:996 | "// Accordion — coverage" (263) | `onToggle={() => setCoverageOpen(!coverageOpen)}` → state (100) | state action | WORKING-AS-CODED |
| C01-051 | frontend/src/components/About.tsx:301 | `t("licenses")`; ro:252 / en:999 | "// Accordion — licenses" (300) | `onToggle={() => setLicensesOpen(!licensesOpen)}` → state (101) | state action | WORKING-AS-CODED |
| C01-052 | frontend/src/components/About.tsx:305-312 | code license text, ro:253 / en:1000 | licenses list (302-325) | `href={codeLicenseUrl}` where `codeLicenseUrl = licenses?.code_url || CODE_LICENSE_URL_FALLBACK` (151); fallback constant line 9 `https://www.gnu.org/licenses/agpl-3.0.html`; label `codeLicense` (149) | external URL | WORKING-AS-CODED (both branches visible in code; API-provided URL value itself data-dependent) |
| C01-053 | frontend/src/components/About.tsx:316-323 | data license text, ro:254 / en:1001 | licenses list (302-325) | `href={dataLicenseUrl}` where `dataLicenseUrl = licenses?.data_url || DATA_LICENSE_URL_FALLBACK` (152); fallback line 10 `https://creativecommons.org/licenses/by/4.0/` | external URL | WORKING-AS-CODED (both branches visible in code; API-provided URL value itself data-dependent) |
| C01-054 | frontend/src/components/About.tsx:329 | `t("dataFreshness")`; ro:255 / en:1002 | "// Accordion — data freshness" (328) | `onToggle={() => setFreshnessOpen(!freshnessOpen)}` → state (102) | state action | WORKING-AS-CODED |
| C01-055 | frontend/src/components/About.tsx:358-365 | `{t("project")}: parlament-deschis ↗`; ro:261 / en:1008 | modal footer (353-366) | `href={PROJECT_URL}` with `const PROJECT_URL = "https://github.com/parlament-deschis"` (6); `target="_blank"` rel noopener noreferrer | external URL | WORKING-AS-CODED |
| C01-056 | frontend/src/components/ui/ThemeToggle.tsx:32-51 | `t("toggleTheme", "Toggle colour theme")` ro:128 / en:882; visible `t("themeLight","Light")` ro:140 / en:894 or `t("themeDark","Dark")` ro:141 / en:895 | "/** Switches the whole app between the dark default and the light theme. */" (12) | `onClick={() => setTheme(nextTheme)}` (35) → effect writes `document.documentElement.dataset.theme` and `localStorage.setItem(STORAGE_KEY, theme)` (19-26), `STORAGE_KEY = "parlament-deschis-theme"` (6) | state action | WORKING-AS-CODED |
| C01-057 | frontend/src/components/ui/DashboardHeader.tsx:15 | `<ThemeToggle />` — same labels as C01-056 | "Header for the LiveDashboard page – shows the main title and theme toggle." (5-7) | mounts C01-056 unchanged; reachable from `LiveDashboard.tsx:121 <DashboardHeader />` on `indexRoute` (router.tsx:341-346) | state action (reused control, not a new handler) | WORKING-AS-CODED |
| C01-058 | frontend/src/components/ErrorState.tsx:38-45 | `t("retry", "Retry")`; ro:271 / en:1018 | error state body (17-47) | `<RetryButton onRetry={onRetry} ...>` (39-44) → `onRetry` prop (7) → `AsyncState.tsx:82 onRetry={onRetry}` from `StateViewProps` (41) → upstream caller; direct caller also `RollCallTable.tsx:55` | state action | NOT PROVEN (terminal callback not in slice. Resolver: `StateView`/`AsyncState` call sites and `RollCallTable.tsx:55`, outside this slice) |
| C01-059 | frontend/src/components/LoadingState.tsx:46-53 | `retryLabel` prop (6) — caller-supplied | loading state body (16-55) | guard `{onRetry && retryLabel && (<RetryButton .../>)}` (46) → `onRetry` prop (7) | state action | NOT PROVEN (no in-slice caller supplies both props: `AsyncState.tsx:73-76` passes only `label`/`description`; `Committees.tsx:375` passes only `label`. Resolver: all `LoadingState` call sites outside this slice) |
| C01-060 | frontend/src/components/EmptyState.tsx:42-51 | `ctaLabel` prop (5) — caller-supplied | "Optional button label" / "Optional button handler" (5-6) | guard `{onCta && ctaLabel && (<button onClick={onCta}>...)}` (42-50) → `onCta` prop (6) | state action | NOT PROVEN (terminal callback not in slice. Resolver: `StateView` `emptyCtaLabel`/`onEmptyCta` pass-through at `AsyncState.tsx:89-90` and direct callers such as `Committees.tsx:397`, `Parties.tsx:91`) |
| C01-061 | frontend/src/components/RetryButton.tsx:18-25 | `label ?? t("traseismRetry")` (24); ro:365 / en:1111 | "// The single retry control: one 44 px press target with press feedback and the inherited global focus ring." (3-4) | `<button type="button" onClick={onRetry}>` (18-20) → `onRetry` prop (11); used by C01-058, C01-059 and out-of-slice callers | state action | NOT PROVEN (terminal callback is caller-supplied; resolver: all `RetryButton` call sites, several outside this slice) |

## Per-element evidence quotes (verbatim, with line numbers)

C01-001 — `frontend/src/router.tsx:73-75`: `t("notFoundTitle", "Page not found")` ... `<Link to="/" search={{ date: localISODate(), chamber: undefined, legislature: undefined }} className="btn bg-sky-700 hover:bg-sky-600">{t("backHome", "Back to overview")}</Link>`

C01-002 — `frontend/src/router.tsx:88-90`: `<h2 className="text-xl font-semibold">{t("routeErrorTitle", "Something went wrong")}</h2>` ... `<Link to="/" search={{ date: localISODate(), chamber: undefined, legislature: undefined }} className="btn bg-sky-700 hover:bg-sky-600">{t("backHome", "Back to overview")}</Link>`

C01-003 — `frontend/src/router.tsx:110-117`: `<Link` / `to={to}` / `search={(previous) => ({ ...previous, ...scope.searchFor() })}` / `aria-current={isActive ? "page" : undefined}`

C01-004 — `frontend/src/router.tsx:138-141`: `<div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"` / `onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}`

C01-005 — `frontend/src/router.tsx:148-150`: `onKeyDown={(e) => {` / `if (e.key === "Escape") onClose();` / `if (e.key !== "Tab") return;`

C01-006 — `frontend/src/router.tsx:169`: `<button type="button"className="btn bg-slate-700 hover:bg-slate-600" onClick={onClose}>{t("close")}</button>`

C01-007 — `frontend/src/router.tsx:178`: `<a href="https://github.com/nedaktov-ops/parlament-deschis" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">https://github.com/nedaktov-ops/parlament-deschis</a>`

C01-008 — `frontend/src/router.tsx:231-233`: `<a href="#main-content" className="sr-only focus:not-sr-only ...">` / `{t("skipToContent", "Skip to content")}` / `</a>`; target `frontend/src/router.tsx:325`: `<main id="main-content" tabIndex={-1} ...>`

C01-009 — `frontend/src/router.tsx:244-248`: `<Search onSelect={(id) => router.navigate({` / `to: "/person/$id",` / `params: { id },` / `search: scope.searchFor(),` / `})} />`

C01-010 — `frontend/src/router.tsx:249-253`: `<button type="button"className="btn bg-slate-700 hover:bg-slate-600"` / `onClick={() => setAboutOpen(true)}` / `{t("about")}`

C01-011 — `frontend/src/router.tsx:254-259`: `onClick={() => i18n.changeLanguage(i18n.language === "ro" ? "en" : "ro")}` / `aria-label={t("changeLanguage")}` / `{i18n.language === "ro" ? "EN" : "RO"}`

C01-012..033 — `frontend/src/router.tsx:264-320`: each instance is `<NavLink to="..." activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">` with the literal `to` and label quoted in the table rows.

C01-034 — `frontend/src/router.tsx:348-359`: `path: "/electoral",` / `beforeLoad: ({ search }) => {` / `throw redirect({` / `to: "/traseism",` / `search: { date: search.date, chamber: "deputies", legislature: "2024" },` / `});`

C01-035 — `frontend/src/router.tsx:600-601`: `<RouterProvider router={router} />` / `<ReactQueryDevtools initialIsOpen={false} />`

C01-036..041 — `frontend/src/components/Footer.tsx:65`, `73`, `81`, `96`, `106`, `123`: `<a` then `href="/"`, `href="/traseism"`, `href="/report"`, `href="https://github.com/nedaktov-ops/parlament-deschis"` (×2), `href="/coverage"`; every one carries `target="_blank" rel="noopener noreferrer"` only when the href is external (98-99, 108-109), and each has `className="hover:text-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 rounded"`. No `<Link>` is imported in Footer.tsx (imports at 1-3 are `useQuery`, `useTranslation`, `api`).

C01-042 — `frontend/src/components/HeaderLogo.tsx:39-45`: `src={`/api/logo?color=${encodeURIComponent(COLORS[theme])}`}` / `alt=""` / `aria-hidden="true"` / `onError={() => setFailed(true)}`

C01-043 — `frontend/src/components/About.tsx:118-122`: `const onKey = (e: KeyboardEvent) => {` / `if (e.key === "Escape") onClose();` / `};` / `document.addEventListener("keydown", onKey);`

C01-044 — `frontend/src/components/About.tsx:160-163`: `<div className="fixed inset-0 z-[60] flex items-start sm:items-center justify-center bg-black/60 p-4 overflow-y-auto"` / `onClick={onClose}`

C01-045 — `frontend/src/components/About.tsx:170-175`: `onClick={(e) => e.stopPropagation()}` / `onKeyDown={(e) => {` / `if (e.key !== "Tab") return;` / `'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'`

C01-046 — `frontend/src/components/About.tsx:197-203`: `<button type="button"ref={closeRef}` / `onClick={onClose}` / `aria-label={t("close")}` / `{t("close")}`

C01-047 — `frontend/src/components/About.tsx:75-79`: `<button` / `type="button"` / `onClick={onToggle}` / `aria-expanded={open}`

C01-048 — `frontend/src/components/About.tsx:237`: `<AccordionItem title={t("sources")} open={sourcesOpen} onToggle={() => setSourcesOpen(!sourcesOpen)}>`

C01-049 — `frontend/src/components/About.tsx:246-253`: `<a` / `href={source.url}` / `target="_blank"` / `rel="noopener noreferrer"` / `{source.name} ↗`

C01-050 — `frontend/src/components/About.tsx:264`: `<AccordionItem title={t("coverageTable")} open={coverageOpen} onToggle={() => setCoverageOpen(!coverageOpen)}>`

C01-051 — `frontend/src/components/About.tsx:301`: `<AccordionItem title={t("licenses")} open={licensesOpen} onToggle={() => setLicensesOpen(!licensesOpen)}>`

C01-052 — `frontend/src/components/About.tsx:9`: `const CODE_LICENSE_URL_FALLBACK = "https://www.gnu.org/licenses/agpl-3.0.html";`; `:151`: `const codeLicenseUrl = licenses?.code_url || CODE_LICENSE_URL_FALLBACK;`; `:305-306`: `<a` / `href={codeLicenseUrl}`

C01-053 — `frontend/src/components/About.tsx:10`: `const DATA_LICENSE_URL_FALLBACK = "https://creativecommons.org/licenses/by/4.0/";`; `:152`: `const dataLicenseUrl = licenses?.data_url || DATA_LICENSE_URL_FALLBACK;`; `:316-317`: `<a` / `href={dataLicenseUrl}`

C01-054 — `frontend/src/components/About.tsx:329`: `<AccordionItem title={t("dataFreshness")} open={freshnessOpen} onToggle={() => setFreshnessOpen(!freshnessOpen)}>`

C01-055 — `frontend/src/components/About.tsx:6`: `const PROJECT_URL = "https://github.com/parlament-deschis";`; `:358-361`: `<a` / `href={PROJECT_URL}` / `target="_blank"` / `rel="noopener noreferrer"`; `:364`: `{t("project")}: parlament-deschis ↗`

C01-056 — `frontend/src/components/ui/ThemeToggle.tsx:35-38`: `onClick={() => setTheme(nextTheme)}` / `aria-label={label}` / `aria-pressed={theme === "light"}` / `title={label}`; `:20-22`: `document.documentElement.dataset.theme = theme;` / `localStorage.setItem(STORAGE_KEY, theme);`

C01-057 — `frontend/src/components/ui/DashboardHeader.tsx:12-16`: `<h1 className="page-title">` / `{t("overview")}` / `</h1>` / `<ThemeToggle />`

C01-058 — `frontend/src/components/ErrorState.tsx:38-44`: `{onRetry && (` / `<RetryButton` / `onRetry={onRetry}` / `label={t("retry", "Retry")}` / `ariaLabel={t("retry", "Retry")}` / `className="mt-4"`

C01-059 — `frontend/src/components/LoadingState.tsx:46-52`: `{onRetry && retryLabel && (` / `<RetryButton` / `onRetry={onRetry}` / `label={retryLabel}` / `ariaLabel={retryLabel}`

C01-060 — `frontend/src/components/EmptyState.tsx:42-50`: `{onCta && ctaLabel && (` / `<button` / `type="button"` / `onClick={onCta}` / `aria-label={ctaLabel}` / `{ctaLabel}`

C01-061 — `frontend/src/components/RetryButton.tsx:18-24`: `<button` / `type="button"` / `onClick={onRetry}` / `aria-label={ariaLabel}` / `{label ?? t("traseismRetry")}`

## i18n definition index (exact lines, both locales)

Every interactive label used in this slice resolves as follows (file: `frontend/src/i18n.ts`; `ro` block 5-759, `en` block 760-1513; `lng: "ro"`, `fallbackLng: "en"` at 1518-1519):

- `backHome` — ro:385 `"backHome": "Înapoi la prezentare generală",` / en:1131 `"backHome": "Back to overview",`
- `close` — ro:272 `close: "Închide",` / en:1019 `close: "Close",`
- `about` — ro:268 `about: "Despre",` / en:1015 `about: "About",`
- `changeLanguage` — ro:127 `changeLanguage: "Schimbă limba",` / en:881 `changeLanguage: "Change language",`
- `skipToContent` — ro:724 `"skipToContent": "Treci la conținut",` / en:1478 `"skipToContent": "Skip to content",`
- `overview` — ro:120 `overview: "Prezentare generală",` / en:874 `overview: "Overview",`
- `traseismShort` — ro:304 `traseismShort: "Traseism",` / en:1051 `traseismShort: "Traseism",`
- `nav.leaderboard` — ro:643 `"nav.leaderboard": "Clasament",` / en:1388 `"nav.leaderboard": "Leaderboard",`
- `nav.demographics` — ro:642 `"nav.demographics": "Demografie",` / en:1387 `"nav.demographics": "Demographics",`
- `nav.committees` — ro:640 `"nav.committees": "Comisii",` / en:1406 `"nav.committees": "Committees",`
- `nav.compare` — ro:641 `"nav.compare": "Compară",` / en:1407 `"nav.compare": "Compare",`
- `nav.coalitions` — ro:639 `"nav.coalitions": "Coaliții",` / en:1386 `"nav.coalitions": "Coalitions",`
- `nav.mps` — ro:645 `"nav.mps": "Parlamentari",` / en:1397 `"nav.mps": "MPs",`
- `nav.report` — ro:647 `"nav.report": "Raport",` / en:1399 `"nav.report": "Report",`
- `nav.parties` — ro:652 `"nav.parties": "Partide",` / en:1404 `"nav.parties": "Parties",`
- `nav.partyTimeline` — ro:646 `"nav.partyTimeline": "Cronologie",` / en:1398 `"nav.partyTimeline": "Timeline",`
- `institutional` — ro:177 `institutional: "Instituțional",` / en:931 `institutional: "Institutional",`
- `coverage` — ro:114 `coverage: "Acoperire",` / en:868 `coverage: "Coverage",`
- `nav.senateHistory` — ro:651 `"nav.senateHistory": "Istoria Senatului",` / en:1403 `"nav.senateHistory": "Senate History",`
- `senate` (nested fallback of `nav.senateHistory`) — ro:75 `senate: "Senat",` / en:829 `senate: "Senate",`
- `nav.legislature` — ro:644 `"nav.legislature": "Legislatură",` / en:1389 `"nav.legislature": "Legislature",`
- `legislature` (nested fallback) — ro:194 `legislature: "Legislatura",` / en:948 `legislature: "Legislature",`
- `party` — ro:273 `party: "Partid",` / en:1020 `party: "Party",`
- `nav.compareMps` — ro:654 `"nav.compareMps": "Compară parlamentari",` / en:1408 `"nav.compareMps": "Compare MPs",`
- `nav.voturi` — ro:655 `"nav.voturi": "Voturi",` / en:1409 `"nav.voturi": "Votes",`
- `nav.radar` — ro:656 `"nav.radar": "Radar voturi",` / en:1410 `"nav.radar": "Vote radar",`
- `nav.grafice` — ro:657 `"nav.grafice": "Grafice",` / en:1411 `"nav.grafice": "Charts",`
- `nav.topuri` — ro:658 `"nav.topuri": "Clasamente vot",` / en:1412 `"nav.topuri": "Vote rankings",`
- `nav.ideology` — ro:659 `"nav.ideology": "Ideologie",` / en:1413 `"nav.ideology": "Ideology",`
- `sources` — ro:269 `sources: "Surse",` / en:1016 `sources: "Sources",`
- `coverageTable` — ro:249 `coverageTable: "Tabel de acoperire",` / en:996 `coverageTable: "Coverage table",`
- `licenses` — ro:252 `licenses: "Licențe",` / en:999 `licenses: "Licenses",`
- `codeLicense` — ro:253 `codeLicense: "Licență cod",` / en:1000 `codeLicense: "Code license",`
- `dataLicense` — ro:254 `dataLicense: "Licență date",` / en:1001 `dataLicense: "Data license",`
- `dataFreshness` — ro:255 `dataFreshness: "Starea datelor",` / en:1002 `dataFreshness: "Data freshness",`
- `project` — ro:261 `project: "Proiect",` / en:1008 `project: "Project",`
- `toggleTheme` — ro:128 `toggleTheme: "Schimbă tema de culori",` / en:882 `toggleTheme: "Toggle colour theme",`
- `themeLight` — ro:140 `themeLight: "Luminos",` / en:894 `themeLight: "Light",`
- `themeDark` — ro:141 `themeDark: "Întunecat",` / en:895 `themeDark: "Dark",`
- `retry` — ro:271 `retry: "Reîncearcă",` / en:1018 `retry: "Retry",`
- `traseismRetry` — ro:365 `traseismRetry: "Reîncearcă",` / en:1111 `traseismRetry: "Try again",`
- `mainNavigation` (nav container label, router.tsx:263) — ro:126 `mainNavigation: "Navigare principală",` / en:880 `mainNavigation: "Main navigation",`
- `nav.analytics` (nav container label, router.tsx:314) — ro:653 `"nav.analytics": "Analiză voturi",` / en:1405 `"nav.analytics": "Vote analytics",`
- `footer.datasetRelease` (non-clickable status, Footer.tsx:147) — ro:152 `"footer.datasetRelease": "Versiune date: {{tag}}",` / en:906 `"footer.datasetRelease": "Dataset release: {{tag}}",`

Caller-supplied labels (not defined in `i18n.ts`): `ctaLabel` (EmptyState.tsx:5,26,49), `retryLabel` (LoadingState.tsx:6,13,49), `label`/`ariaLabel` on RetryButton (RetryButton.tsx:7,8). Their concrete values are outside this slice.

## Findings

### F1 (SUSPECT) — Footer uses plain `<a href>` instead of router `<Link>` in this SPA; scope search is not carried

**Affected:** C01-036, C01-037, C01-038, C01-041.

**Evidence**
- `frontend/src/components/Footer.tsx:65-70`: `<a` / `href="/"` / `{t("overview")}` / `</a>`.
- `frontend/src/components/Footer.tsx:73-79`: `href="/traseism"`; `:81-87`: `href="/report"`; `:123-129`: `href="/coverage"`.
- `frontend/src/components/Footer.tsx:1-3`: imports are `useQuery`, `useTranslation`, `api` — no `Link` and no `useScope`.
- `frontend/src/router.tsx:110-118`: the in-app nav path is `<Link to={to} search={(previous) => ({ ...previous, ...scope.searchFor() })} ...>`.
- `frontend/src/router.tsx:43-56`: `validateScopeSearch` materialises `date`, `chamber`, `legislature` from search; all 24 routes use `validateSearch: validateScopeSearch` (e.g. 345, 396, 488).

**Reason:** The footer's in-app destinations are expressed as native anchors with no `search` argument, so the code path at router.tsx:110-118 (which preserves previous search and merges `scope.searchFor()`) is not used by these four controls. The footer therefore expresses a different navigation mechanism from every other in-app link in the slice. This is a code-level discrepancy; no runtime behaviour is asserted.

**Improvement:** At `frontend/src/components/Footer.tsx:65`, `:73`, `:81` and `:123`, replace `<a href="...">` with TanStack `<Link to="..." search={scope.searchFor()}>` (import `Link` from `@tanstack/react-router` and `useScope` from `../hooks/useScope`, matching `frontend/src/router.tsx:1` and `:10`). If native full navigation is intentional, add a short comment at Footer.tsx:64 stating that choice explicitly.

### F2 (SUSPECT) — Footer "About" link is labelled as the About feature but its destination is the GitHub repository

**Affected:** C01-039.

**Evidence**
- `frontend/src/components/Footer.tsx:96-104`: `href="https://github.com/nedaktov-ops/parlament-deschis"` with `target="_blank"` and `{t("about")}` as the link text.
- `frontend/src/i18n.ts:268` / `:1015`: `about: "Despre",` / `about: "About",` — a feature label, not a repository label.
- `frontend/src/router.tsx:249-253`: header `t("about")` button calls `setAboutOpen(true)`; `:329`: `<AboutModal open={aboutOpen} onClose={closeAbout} />`.
- `frontend/src/components/Footer.tsx:106-114`: the adjacent `t("sources")` link points to the exact same GitHub URL.

**Reason:** Two controls with different labels (`about`, `sources`) in the same footer group resolve to one identical external URL, while the same `about` label elsewhere in the shell opens the local about dialog. The code therefore does not support the label as a description of the destination.

**Improvement:** At `frontend/src/components/Footer.tsx:97`, either (a) change the label to a distinct key that describes a repository link (reusing `t("sources")` at i18n.ts:269/1016 or adding a new `footer.repository` key in both locale blocks), or (b) rewire the control to the in-app about surface. Keep the two adjacent footer entries from sharing one URL unless that duplication is intentional and documented at Footer.tsx:95.

## Cross-checks (code-derived)

**Route tree.** `frontend/src/router.tsx:519-544` registers 24 routes under `rootRoute` (335-339). Counting `path:` literals at 343, 350, 366, 373, 380, 387, 394, 401, 409, 416, 423, 430, 437, 444, 451, 458, 465, 472, 479, 486, 493, 500, 507, 514 = 24 paths. All 24 carry `validateSearch: validateScopeSearch` (43-56); `electoralRoute` is the only one without a `component` because it declares `beforeLoad` (348-362).

**Nav coverage.** 22 `<NavLink>` instances exist (router.tsx:264, 267, 270, 273, 276, 279, 282, 285, 288, 291, 294, 297, 300, 303, 306, 309 in the first nav; 315, 316, 317, 318, 319, 320 in the second). The two registered routes with **no** nav link are:
- `/person/$id` — route declared at `frontend/src/router.tsx:378-383` (`path` at 380); no `<NavLink to="/person/...">` anywhere in router.tsx. Reachability is via global Search at `frontend/src/router.tsx:244-248` (`router.navigate({ to: "/person/$id", params: { id }, ... })`), which is also the exemption recorded in `scripts/check_routes_nav.mjs:12`.
- `/electoral` — route declared at `frontend/src/router.tsx:348-362` (`path` at 350); no `<NavLink to="/electoral">`; it is redirect-only by `beforeLoad` (351-359), matching `scripts/check_routes_nav.mjs:13`.
- Parameterised routes `/legislature/$year` (387) and `/party/$shortName` (373) are covered by the concrete nav links `/legislature/2024` (306) and `/party/PSD` (309); `check_routes_nav.mjs:18-22` normalises `/$param` and accepts `t.startsWith(`${n}/`)`.
- By the script's own regexes (`scripts/check_routes_nav.mjs:9-10`), it reads 24 route paths and 22 nav targets from router.tsx; lines 23-28 exempt exactly the two routes above, so its logic classifies `unlinked=0`. (Statement derived from reading the script and router.tsx; the script was not executed.)

**The /electoral redirect.** `frontend/src/router.tsx:351-359` throws `redirect({ to: "/traseism", search: { date: search.date, chamber: "deputies", legislature: "2024" } })`; `search` is the validated input because `validateScopeSearch` is attached at 361. The custom serializers `stringifySearch` (550-558) and `parseSearch` (560-568) are passed to `createRouter` at 572-573, with the comment at 546-549 explaining that numbers would otherwise be JSON-stringified into quoted values (`legislature=%222024%22`). Code shows the redirect target `/traseism` is registered at 392-397. No claim is made about observed URL output.

**Uppercase /Voturi.** The uppercase spelling is used consistently in all three places in this slice: route declaration `frontend/src/router.tsx:486 path: "/Voturi"`, nav target `frontend/src/router.tsx:316 <NavLink to="/Voturi" ...>`, and document-title selector `frontend/src/router.tsx:214 else if (path === "/Voturi") label = t("nav.voturi");`. The lazy import name at :33 and the i18n keys `nav.voturi` (`i18n.ts:655`/`:1409`) and `view.voturi.*` are identifiers/keys, not route paths. Lowercase `/voturi` does not appear as a `path:` or `to=` in router.tsx. No defect is asserted from case alone.

**Modal pair.** Two distinct about surfaces exist in the codebase: `AboutModal` defined at `frontend/src/router.tsx:122-183` and mounted at `:329` from the header button at `:249-253`; and `About` defined at `frontend/src/components/About.tsx:95` and mounted at `frontend/src/pages/Traseism.tsx:960` from the button at `:952` (label `t("traseismAboutButton")`, `i18n.ts:382`/`:1128`). They are not dead; neither is a substitute for the other within this slice.

**window.print / window.open.** No call occurs in any assigned slice file. The only match under `frontend/src` is `frontend/src/pages/Report.tsx:166 onClick={() => window.print()}`, which is outside this slice; the labels `report.print` (`i18n.ts:693`/`:1447`) and `report.download` (`i18n.ts:685`/`:1439`) likewise belong to the out-of-slice Report page. No slice element was classified `no-op` or `dead`.

**index.html.** No clickable elements. `frontend/index.html:8-19` contains a synchronous IIFE reading `localStorage.getItem("parlament-deschis-theme")` (13) and setting `document.documentElement.dataset.theme` (15) — the same key and attribute written by C01-056 (`ThemeToggle.tsx:6`, `:20-22`). `:6` is a favicon `<link>` and `:23` the module script; neither is an element invocation.

**scripts/check_routes_nav.mjs.** A read-only Node checker (no clickable elements). Its rules: route regex at :9, nav regex at :10, exemptions at :11-17, param normalisation at :18, matching at :19-24, exit behaviour at :25-29. Its doc comment at :2 states: "Every registered route must be nav-reachable, search-reachable, redirect-only, or formally deprecated."

## Coverage and NOT PROVEN

**Covered in full:** all 13 assigned files, all `<button>`, `<a>`, `<Link>`/NavLink, `onClick`, `onKeyDown`/keydown activators, modal backdrop/close handlers, skip link, devtools mount, programmatic `router.navigate` and `redirect`, `onError` image fallback, and every i18n label used by those elements (both locales). 61 inventory rows were produced.

**NOT PROVEN items and their resolvers**
1. C01-035 — `<ReactQueryDevtools initialIsOpen={false} />` visibility/toggle. Resolver: `@tanstack/react-query-devtools` source plus build-mode/env configuration (not in this slice).
2. C01-049 — concrete `source.url` values for the About sources links. Resolver: backend `/api/about` (`api.about`) / `/api/coverage` (`api.coverage`) payload shape and values; `frontend/src/api/client.ts` (out of slice).
3. C01-058 — terminal `onRetry` for `ErrorState`. Resolver: `StateView`/`AsyncState` call sites (`frontend/src/components/ui/AsyncState.tsx:41,82`) and `frontend/src/components/RollCallTable.tsx:55` (out of slice).
4. C01-059 — terminal `onRetry`/`retryLabel` for `LoadingState`; no in-slice caller supplies both (`AsyncState.tsx:73-76`, `Committees.tsx:375`). Resolver: all `LoadingState` call sites outside this slice.
5. C01-060 — terminal `onCta`/`ctaLabel` for `EmptyState`. Resolver: `AsyncState.tsx:44-45,89-90` pass-through and direct callers (`Committees.tsx:397`, `Parties.tsx:91`), outside this slice.
6. C01-061 — terminal `onRetry` for the reusable `RetryButton`. Resolver: all `RetryButton` call sites, e.g. `PersonDrawer.tsx:125`, `SankeyFlow.tsx:186`, `TimelineChart.tsx:237`, `LiveFeed.tsx:239`, `ChamberView.tsx:37` (out of slice).

**Additional unknowns recorded (not separate inventory rows)**
- Exact payload of `scope.searchFor()` merged by every NavLink and by C01-009 (`frontend/src/router.tsx:112`, `:247`). Resolver: `frontend/src/hooks/useScope.ts` (out of slice).
- Invocation condition for `Search.onSelect` (C01-009). Resolver: `frontend/src/components/Search.tsx` (out of slice).
- Whether `/api/logo` (C01-042) returns an image on any given request. Resolver: backend logo endpoint / HTTP state — a runtime question, not a code-verdict question.
- API-provided license URL values for C01-052/053 (fallback constants are in code at About.tsx:9-10; the `licenses.code_url` / `licenses.data_url` values are data-dependent). Resolver: backend `/api/about` payload.

**Classification tally by class:** in-app route = 31 (C01-001, 002, 003, 009, 012–033 [22 rows], 034, 036, 037, 038, 041); external URL = 7 (C01-007, 039, 040, 049, 052, 053, 055); state action = 23 (all remaining rows, including C01-008's in-page fragment and C01-042's `onError` fallback); API/download as a standalone class = 0 (the API image source appears only as a note on C01-042); no-op = 0; dead = 0. Total 31 + 7 + 23 = 61.

Elements: 61 | BROKEN: 0 | SUSPECT: 5 | NOT PROVEN: 6
