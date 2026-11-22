---
id: CLICK-INV-C03
type: evidence
title: "Clickable inventory — C03 entity pages (2026-11-22)"
description: "Read-only, code-grounded enumeration of every interactive element rendered by the ten C03 entity pages, resolved against i18n.ts and router.tsx at commit 8811216."
status: active
authority: derived
tags: [type/evidence, lifecycle/active, domain/frontend]
source_paths: [frontend/src/pages/Parties.tsx, frontend/src/pages/PartyProfile.tsx, frontend/src/pages/PartyTimeline.tsx, frontend/src/pages/PartyComparison.tsx, frontend/src/pages/Coalitions.tsx, frontend/src/pages/Committees.tsx, frontend/src/pages/Mps.tsx, frontend/src/pages/MpComparison.tsx, frontend/src/pages/Demographics.tsx, frontend/src/pages/PersonDeepDive.tsx, frontend/src/i18n.ts, frontend/src/router.tsx, frontend/src/hooks/useScope.ts, frontend/src/api/client.ts, frontend/src/components/ScopeControls.tsx, frontend/src/components/ProvenanceStamp.tsx, frontend/src/components/CitationPopover.tsx, frontend/src/components/PersonDrawer.tsx, frontend/src/components/MembershipGantt.tsx, frontend/src/components/ui/AsyncState.tsx]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Clickable inventory — C03 entity pages

Read-only investigation. No code, data, config or git state was changed; no network calls or browser claims were made. All ten assigned pages were read in full, plus [i18n.ts](../../frontend/src/i18n.ts), [router.tsx](../../frontend/src/router.tsx), [useScope.ts](../../frontend/src/hooks/useScope.ts), [client.ts](../../frontend/src/api/client.ts) and the child components named in `source_paths`.

**Conventions used below.** `ro` = [i18n.ts](../../frontend/src/i18n.ts) lines 5–759; `en` = lines 760–1513; default language is `ro` (line 1518 `lng: "ro"`), fallback `en` (line 1519). Route targets were cross-checked against [router.tsx](../../frontend/src/router.tsx): `/party/$shortName` at line 373 (component `PartyProfile`, line 374), `/person/$id` at line 380 (component `PersonDeepDive`, line 381), `/mps` line 451, `/compare-mps` line 458, `/parties` line 472, `/party-timeline` line 479, `/compare` line 437, `/coalitions` line 444, `/committees` line 430, `/demographics` line 423. "Delegated" rows are elements these pages render through a shared child component; both the page mount line and the defining line are given.

## 1. Complete element table

| ID | file:line | label / i18n | purpose (as stated by code/prose) | destination / handler chain (terminal line quoted) | class | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| C03-001 | [Parties.tsx:70–76](../../frontend/src/pages/Parties.tsx), onChange at :73 | `mps.search` — ro :531 "Caută" / en :1277 "Search"; placeholder `parties.search.placeholder` — ro :49 "nume sau acronim…" / en :804 "name or acronym…" | Filter the party table: "All parties in the corpus … Click a party to open its profile for the selected date." (`parties.intro`, ro :47 / en :802) | `setQ` ([Parties.tsx:17](../../frontend/src/pages/Parties.tsx)) → `navigate({ search: scope.searchFor({ q: value \|\| undefined }) })` — terminal line 17 | state action (URL-backed search) | WORKING-AS-CODED |
| C03-002 | [Parties.tsx:83–89](../../frontend/src/pages/Parties.tsx), onRetry at :86 | `parties.loadError` — ro i18n :48 "Nu s-au putut încărca partidele." / en :803 "Failed to load parties." | Retry failed party fetch | `onRetry={() => void partiesQuery.refetch()}` — terminal line 86; button rendered by [ErrorState.tsx:38–40](../../frontend/src/components/ErrorState.tsx) → [RetryButton.tsx:18–20](../../frontend/src/components/RetryButton.tsx) | API (refetch `/parties`, client.ts:533) | WORKING-AS-CODED |
| C03-003 | [Parties.tsx:107–119](../../frontend/src/pages/Parties.tsx), onClick :110, onKeyDown :113–118, `role="button"` :111, `tabIndex={0}` :112 | Row content `{p.name}` (:120) / `{p.short_name}` (:130); region aria `parties.title` ro i18n :45 / en :800 | "Click a party to open its profile for the selected date." (`parties.intro`, ro :47 / en :802) | onClick :110 → `goToParty(p.short_name)` :45–47 → terminal `:46 navigate({ to: "/party/$shortName", params: { shortName }, search: scope.searchFor() })` → route router.tsx:373; keyboard path :113–118 calls the same `goToParty` | in-app route | WORKING-AS-CODED — **keyboard handler IS present** (Enter/Space + `e.preventDefault()` at :115–116) |
| C03-004 | [PartyProfile.tsx:68–76](../../frontend/src/pages/PartyProfile.tsx), onRetry :72 | `partyLoadError` — ro i18n :156 / en :910 | Retry failed party-profile fetch (full-page error state) | `onRetry={() => void party.refetch()}` — terminal line 72 → `api.partyProfile(shortName, asOf)` :30 → client.ts:526–527 | API | WORKING-AS-CODED |
| C03-005 | [PartyProfile.tsx:106–115](../../frontend/src/pages/PartyProfile.tsx) | `Wikidata: {p.wikidata_qid} ↗` (:113), no i18n key | Open the party's Wikidata entity | `href={`https://www.wikidata.org/wiki/${p.wikidata_qid}`}` (:108), `target="_blank"` :109 — terminal line 108 | external URL | WORKING-AS-CODED (rendered only when `p.wikidata_qid` truthy, :106) |
| C03-006 | [PartyProfile.tsx:177–202](../../frontend/src/pages/PartyProfile.tsx), onClick :178 | `{m.type}` / `{m.event_date}` / `{m.person?.name ?? "—"}` (:182–194) + ProvenanceStamp (:196–201); section `recentMovements` ro i18n :102 / en :856 | Open the movement's person in the drawer | `onClick={() => m.person && setPersonId(m.person.id)}` — terminal line 178 → `setPersonId` (:25) → `<PersonDrawer personId={personId} onClose={closePerson} />` (:208) | state action | **SUSPECT** — silent no-op when `m.person` is null; no `disabled` attribute on the button; also wraps an `<a>` (see C03-041) |
| C03-007 | [PartyProfile.tsx:168–174](../../frontend/src/pages/PartyProfile.tsx), onRetry :171 | `electoralLoadError` ro i18n :172 / en :926 | Retry failed movements fetch | `onRetry={() => void movements.refetch()}` — terminal line 171 → `api.partyMovements` :36 → client.ts:528–529 | API | WORKING-AS-CODED |
| C03-008 | [PartyTimeline.tsx:127–133](../../frontend/src/pages/PartyTimeline.tsx) | `ptimeline.viewAllParties` — ro i18n :41 "Vezi toate partidele →" / en :796 "View all parties →" | Navigate to the parties list | `<Link to="/parties" search={scope.searchFor()}>` — terminal line 128 → route router.tsx:472 | in-app route | WORKING-AS-CODED |
| C03-009 | [PartyTimeline.tsx:99–106](../../frontend/src/pages/PartyTimeline.tsx), onRetry :102 | `ptimeline.loadError` — ro i18n :667 / en :1421 | Retry failed timeline fetch | `onRetry={() => void timeline.refetch()}` — terminal line 102 → `fetchTimeline` (:47–49) → `get("/analytics/party-timeline")` :48 | API | WORKING-AS-CODED |
| C03-010 | [PartyComparison.tsx:166–172](../../frontend/src/pages/PartyComparison.tsx) | `compare.viewAllParties` — ro i18n :51 "Vezi toate partidele →" / en :806 "View all parties →" | Navigate to the parties list | `<Link to="/parties" search={scope.searchFor()}>` — terminal line 167 → route router.tsx:472 | in-app route | WORKING-AS-CODED |
| C03-011 | [PartyComparison.tsx:178–188](../../frontend/src/pages/PartyComparison.tsx), onChange :180 | `compare.partyA` — ro i18n :446 "Partidul A" / en :1192 "Party A"; options `{p.short_name}` :185 | Pick party A for comparison | `onChange={(e) => setPartyA(e.target.value)}` :180 → `setPartyA` :46 → `navigate({ search: scope.searchFor({ partyA: value }) })` — terminal line 46, route `/compare` router.tsx:437 | state action (URL-backed) | **SUSPECT** — default `"PSD"` (:44) has no fallback if absent from `partyList` (:183–187); see Finding F5 |
| C03-012 | [PartyComparison.tsx:192–202](../../frontend/src/pages/PartyComparison.tsx), onChange :194 | `compare.partyB` — ro i18n :447 "Partidul B" / en :1193 "Party B"; options `{p.short_name}` :199 | Pick party B for comparison | `onChange={(e) => setPartyB(e.target.value)}` :194 → `setPartyB` :47 → `navigate({ search: scope.searchFor({ partyB: value }) })` — terminal line 47, route router.tsx:437 | state action (URL-backed) | **SUSPECT** — same default-value risk (`"PNL"`, :45) as C03-011 |
| C03-013 | [PartyComparison.tsx:134–147](../../frontend/src/pages/PartyComparison.tsx), onRetry :139–143 | `compare.loadError` — ro i18n :441 / en :1187 | Retry three failed queries | `void parties.refetch(); void ages.refetch(); void control.refetch();` — terminal lines 140–142 | API | WORKING-AS-CODED |
| C03-014 | [Coalitions.tsx:64–73](../../frontend/src/pages/Coalitions.tsx), onRetry :69 | `coalitions.loadError` — ro i18n :402 / en :1148 | Retry failed wave fetch | `onRetry={() => void waves.refetch()}` — terminal line 69 → `switchWaves` :36 → client.ts:992–1000 | API | WORKING-AS-CODED |
| C03-015 | [Committees.tsx:33–40](../../frontend/src/pages/Committees.tsx) | `{member.name}` (:39) | Link from a committee member row to that MP | `<Link to="/person/$id" params={{ id: member.person_id }} search={scope.searchFor()}>` — terminal line 34–35 → route router.tsx:380 | in-app route | **NOT PROVEN** — wiring is complete, but non-emptiness of `member.person_id` is data-dependent; resolver: live `/api/committees/{id}/members` (client.ts:911–919). See F3 |
| C03-016 | [Committees.tsx:96–118](../../frontend/src/pages/Committees.tsx), onClick :98 | `{committee.name}` (:102), count `committees.memberCount` — ro i18n :429 / en :1175, caret :116 | Expand/collapse a committee's member ledger | `onClick={() => setOpen((v) => !v)}` — terminal line 98 → `setOpen` (:80) → `enabled: open` (:85) → `committeeMembers(committee.id, scope.date)` :84 → client.ts:911–919 | state action (+ API on expand) | WORKING-AS-CODED (`aria-expanded={open}` :99) |
| C03-017 | [Committees.tsx:344–351](../../frontend/src/pages/Committees.tsx) | `{c.chair}` (:350) | Link from the control-index chair table to that MP | `<Link to="/person/$id" params={{ id: c.chair_person_id }}>` — terminal lines 345–346 → route router.tsx:380 | in-app route | **NOT PROVEN** — `c.chair_person_id` non-emptiness is data-dependent; resolver: live `/api/analytics/committee-control` (client.ts:953–963). See F3 |
| C03-018 | [Committees.tsx:318–321](../../frontend/src/pages/Committees.tsx) | `control.showChairs` — ro i18n :456 "Arată toți președinții →" / en :1202 "Show all chairs →" | Native expand/collapse of the all-chairs table | `<details>` / `<summary>` — terminal line 318/319; no JS handler | state action (native `<details>`) | WORKING-AS-CODED |
| C03-019 | [Committees.tsx:122–129](../../frontend/src/pages/Committees.tsx), onRetry :126 | `committees.loadError` — ro i18n :428 / en :1174 | Retry failed member fetch | `onRetry={() => void members.refetch()}` — terminal line 126 | API | WORKING-AS-CODED |
| C03-020 | [Committees.tsx:365–372](../../frontend/src/pages/Committees.tsx), onRetry :369 | `control.loadError` — ro i18n :455 / en :1201 | Retry failed control-index fetch | `onRetry={() => void control.refetch()}` — terminal line 369 | API | WORKING-AS-CODED |
| C03-021 | [Committees.tsx:377–384](../../frontend/src/pages/Committees.tsx), onRetry :381 | `committees.loadError` — ro i18n :428 / en :1174 | Retry failed committee-list fetch | `onRetry={() => void list.refetch()}` — terminal line 381 | API | WORKING-AS-CODED |
| C03-022 | [Mps.tsx:113–119](../../frontend/src/pages/Mps.tsx), onChange :116 | `mps.search` ro i18n :531 / en :1277; placeholder `mps.search.placeholder` ro :533 / en :1279 | Type a search query (committed on submit, C03-024) | `onChange={(e) => setQuery(e.target.value)}` — terminal line 116 → local `useState` (:29); `useEffect(() => setQuery(submitted), [submitted])` :30 | state action (local only) | WORKING-AS-CODED |
| C03-023 | [Mps.tsx:123–134](../../frontend/src/pages/Mps.tsx), onChange :125 | `mps.sort` ro :534 / en :1280; options `mps.sort.name` ro :622/en :1369, `mps.sort.switches` ro :623/en :1370, `mps.sort.committees` ro :536/en :1282, `mps.sort.age` ro :535/en :1281 | Change sort order | `onChange={(e) => setSearchParam({ sort: e.target.value, offset: 0 })}` :125 → `setSearchParam` :31–32 → `navigate({ search: scope.searchFor(patch) })` — terminal line 32, route `/mps` router.tsx:451 | state action (URL-backed) | WORKING-AS-CODED |
| C03-024 | [Mps.tsx:104–142](../../frontend/src/pages/Mps.tsx), onSubmit :105–108, submit button :136–141 | `mps.go` — ro i18n :524 "Mergi" / en :1270 "Go" | Commit the search query and reset paging | `e.preventDefault(); setSearchParam({ q: query.trim() \|\| undefined, offset: 0 });` — terminal line 107 → navigate (:32) | state action (URL-backed search) | WORKING-AS-CODED |
| C03-025 | [Mps.tsx:157–164](../../frontend/src/pages/Mps.tsx) | `{m.name}` (:163) | Open the MP's full profile | `<Link to="/person/$id" params={{ id: m.id }}>` — terminal lines 158–159 → route router.tsx:380 | in-app route | **NOT PROVEN** — `m.id` non-emptiness data-dependent; resolver: live `/api/mps` (client.ts:464–473). See F3 |
| C03-026 | [Mps.tsx:190–197](../../frontend/src/pages/Mps.tsx), onClick :193 | `mps.prev` — ro i18n :530 "Anterior" / en :1276 "Previous"; `disabled={!canPrev}` :192 | Previous result page (`canPrev = offset > 0`, :46) | `onClick={() => setSearchParam({ offset: Math.max(0, offset - PAGE_SIZE) })}` — terminal line 193 → navigate (:32) | state action (pagination) | WORKING-AS-CODED (clamped with `Math.max(0, …)`) |
| C03-027 | [Mps.tsx:201–208](../../frontend/src/pages/Mps.tsx), onClick :204 | `mps.next` — ro i18n :527 "Următor" / en :1273 "Next"; `disabled={!canNext}` :203 | Next result page (`canNext = total !== null ? offset + rows.length < total : false`, :47) | `onClick={() => setSearchParam({ offset: offset + PAGE_SIZE })}` — terminal line 204 → navigate (:32) | state action (pagination) | **SUSPECT** — bound uses rendered `rows.length`, not `PAGE_SIZE` (60, :12); see F2 |
| C03-028 | [Mps.tsx:144–150](../../frontend/src/pages/Mps.tsx), onRetry :147 | `mps.loadError` — ro i18n :526 / en :1272 | Retry failed MP-card fetch | `onRetry={() => void cards.refetch()}` — terminal line 147 → `mpsCards` :36 → client.ts:464–473 | API | WORKING-AS-CODED |
| C03-029 | [MpComparison.tsx:218–227](../../frontend/src/pages/MpComparison.tsx), onChange :221 | placeholder `mpc.search` ro i18n :511 "Caută după nume…" / en :1257 "Search name…"; `aria-label` `mpc.searchSlot` ro :512 / en :1258 | Type a name in comparison slot i | `onChange={(e) => setSearch(i, e.target.value)}` — terminal line 221 → `setSearch` :39–51 (local state) | state action (local only) | WORKING-AS-CODED |
| C03-030 | [MpComparison.tsx:228–244](../../frontend/src/pages/MpComparison.tsx), onClick :234 | `{s.name}` + `{s.party ?? ""}` (:237–239) | Pick a suggested MP into slot i | `onClick={() => pick(i, s)}` — terminal line 234 → `pick` :53–64 → `setSelected`/`setSearches` | state action | WORKING-AS-CODED |
| C03-031 | [MpComparison.tsx:192–201](../../frontend/src/pages/MpComparison.tsx) | `{selected[i]!.name}` (:200) | Open the selected MP's profile from its slot | `<Link to="/person/$id" params={{ id: selected[i]!.id }}>` — terminal lines 195–196 → route router.tsx:380 | in-app route | **NOT PROVEN** — id originates from API pool; non-emptiness data-dependent; resolver: live `/api/mps` (client.ts:464). See F3 |
| C03-032 | [MpComparison.tsx:208–214](../../frontend/src/pages/MpComparison.tsx), onClick :210 | `mpc.clear` — ro i18n :502 "șterge" / en :1248 "clear" | Clear comparison slot i | `onClick={() => clearSlot(i)}` — terminal line 210 → `clearSlot` :66–77 → `setSelected`/`setSearches` | state action | WORKING-AS-CODED |
| C03-033 | [MpComparison.tsx:128–136](../../frontend/src/pages/MpComparison.tsx), onRetry :132 | `mpc.loadError` — ro i18n :506 / en :1252 | Retry failed MP-pool fetch | `onRetry={() => void pool.refetch()}` — terminal line 132 → `mpsCards({ limit: 200, … })` :31 → client.ts:464–473 | API | WORKING-AS-CODED |
| C03-034 | [Demographics.tsx:57–66](../../frontend/src/pages/Demographics.tsx), onRetry :62 | `demographics.error` — ro i18n :473 / en :1219 | Retry failed demographics fetch | `onRetry={() => void shift.refetch()}` — terminal line 62 → `generationalShift` :30 → client.ts:847–857 | API | WORKING-AS-CODED |
| C03-035 | [PersonDeepDive.tsx:85–94](../../frontend/src/pages/PersonDeepDive.tsx), onRetry :90 | `personLoadError` — ro i18n :157 / en :911 | Retry failed person fetch | `onRetry={() => void person.refetch()}` — terminal line 90 → `api.person(personId, scope.date)` :43 → client.ts:522–523 | API | WORKING-AS-CODED |
| C03-036 | [PersonDeepDive.tsx:167–174](../../frontend/src/pages/PersonDeepDive.tsx) | `Wikidata: {p.wikidata_qid} ↗` (:171) | Open the person's Wikidata entity | `href={`https://www.wikidata.org/wiki/${p.wikidata_qid}`}` (:170), `target="_blank"` — terminal line 170 | external URL | WORKING-AS-CODED (rendered only when `p.wikidata_qid`, :167) |
| C03-037 | [PersonDeepDive.tsx:253–279](../../frontend/src/pages/PersonDeepDive.tsx), mount at :274 | citations header `citations` ro i18n :107 / en :861 | Mount the per-membership citation control (internals C03-047–050) | `<CitationPopover items={ev} />` — terminal line 274 → [CitationPopover.tsx](../../frontend/src/components/CitationPopover.tsx) | state action (delegated) | WORKING-AS-CODED |
| C03-038 | [ScopeControls.tsx:29–36](../../frontend/src/components/ScopeControls.tsx); mounted by PartyProfile:97, PartyComparison:155, Committees:219, Mps:57, MpComparison:144, Demographics:141, PersonDeepDive:109 | `asOf` ro i18n :76 "La data de" / en :830 "As of" | Scope date picker | `onChange={(e) => { if (e.target.value) scope.setScope({ date: e.target.value }); }}` — terminal line 34 → `setScope` [useScope.ts:49–68](../../frontend/src/hooks/useScope.ts) → `navigate` :51 | state action (URL-backed) | WORKING-AS-CODED |
| C03-039 | [ScopeControls.tsx:37–47](../../frontend/src/components/ScopeControls.tsx); mounted by Committees:219, Mps:57, MpComparison:144 | `filter.chamber` ro i18n :425 / en :1313; options `scope.allChambers` ro :78/en :832, `deputies` ro :74/en :828, `senate` ro :75/en :829 | Scope chamber picker | `onChange={(e) => scope.setScope({ chamber: … })}` — terminal line 41 → `setScope` → navigate | state action (URL-backed) | WORKING-AS-CODED |
| C03-040 | [ScopeControls.tsx:48–57](../../frontend/src/components/ScopeControls.tsx); mounted by PartyComparison:155, Coalitions:78, Committees:219, Mps:57, MpComparison:144, Demographics:141 | `filter.legislature` ro i18n :613 / en :1316; `scope.allLegislatures` ro :79/en :833 | Scope legislature picker | `onChange={(e) => scope.setScope({ legislature: e.target.value \|\| undefined })}` — terminal line 52 → `setScope` → navigate | state action (URL-backed) | WORKING-AS-CODED |
| C03-041 | [ProvenanceStamp.tsx:42–50](../../frontend/src/components/ProvenanceStamp.tsx); mounted by PartyProfile:196–201 (inside button C03-006), Committees:62–65, PersonDeepDive:210–215 and :246 | `viewOriginal` — ro i18n :108 "Vezi sursa originală ↗" / en :862 "View original source ↗" | Open the cited official source | `<a href={sourceUrl} target="_blank" rel="noopener noreferrer">` — terminal line 46 | external URL | **SUSPECT** — in PartyProfile this `<a>` is nested inside the `<button>` at :177–202; click bubbles to C03-006 (invalid nested-interactive markup). Standalone mounts in Committees/PersonDeepDive are fine. See F1 |
| C03-042 | [PersonDrawer.tsx:116–118](../../frontend/src/components/PersonDrawer.tsx); mounted by PartyProfile:208 | `close` — ro i18n :272 "Închide" / en :1019 "Close" | Close the person drawer | `onClick={onClose}` :116 → prop `onClose={closePerson}` (PartyProfile:208) → `closePerson` :26 → `setPersonId(null)` — terminal PartyProfile:26 | state action | WORKING-AS-CODED |
| C03-043 | [PersonDrawer.tsx:97](../../frontend/src/components/PersonDrawer.tsx); mounted by PartyProfile:208 | overlay `<div aria-hidden="true">` (no label) | Click outside to dismiss the drawer | `onClick={onClose}` — terminal line 97 → same chain as C03-042 | state action | WORKING-AS-CODED |
| C03-044 | [PersonDrawer.tsx:57–61](../../frontend/src/components/PersonDrawer.tsx); mounted by PartyProfile:208 | Escape key (no label) | Keyboard dismiss of drawer + focus trap | `if (event.key === "Escape") { onClose(); return; }` — terminal line 58 → same chain as C03-042 | state action (keyboard) | WORKING-AS-CODED |
| C03-045 | [PersonDrawer.tsx:143–152](../../frontend/src/components/PersonDrawer.tsx); mounted by PartyProfile:208 | `{p.wikidata_qid} ↗` (:150) | Open Wikidata entity from the drawer | `href={`https://www.wikidata.org/wiki/${p.wikidata_qid}`}` — terminal line 145 | external URL | WORKING-AS-CODED (conditional on `p.wikidata_qid`, :143) |
| C03-046 | [PersonDrawer.tsx:122–127](../../frontend/src/components/PersonDrawer.tsx); mounted by PartyProfile:208 | `RetryButton` (ro i18n `retry` :271 "Reîncearcă" / en :1018 "Retry") | Retry failed drawer-person fetch | `<RetryButton onRetry={() => person.refetch()} />` — terminal line 125 | API | WORKING-AS-CODED |
| C03-047 | [CitationPopover.tsx:46–55](../../frontend/src/components/CitationPopover.tsx); mounted by PersonDeepDive:274 (and PersonDrawer:184 via PartyProfile) | `{items.length} {t("evidenceCount")}` — `evidenceCount` ro i18n :283 "surse" / en :1030 "sources" | Toggle the citation list | `onClick={() => setOpen((o) => !o)}` — terminal line 46 → local `setOpen` (:25) | state action | WORKING-AS-CODED (`aria-expanded={open}` :49) |
| C03-048 | [CitationPopover.tsx:72–84](../../frontend/src/components/CitationPopover.tsx); mounted by PersonDeepDive:274 | `viewOriginal ↗` ro i18n :108 / en :862 | Open each evidence item's source URL | `<a href={ev.source_url} target="_blank" rel="noopener noreferrer">` — terminal line 74 | external URL | WORKING-AS-CODED |
| C03-049 | [CitationPopover.tsx:85–97](../../frontend/src/components/CitationPopover.tsx); mounted by PersonDeepDive:274 | `viewArchive ↗` ro i18n :113 "Vezi copia arhivată ↗" / en :867 "View archived copy ↗" | Open each evidence item's snapshot URL | `<a href={ev.snapshot_url} target="_blank" rel="noopener noreferrer">` — terminal line 87 | external URL | WORKING-AS-CODED |
| C03-050 | [CitationPopover.tsx:28–40](../../frontend/src/components/CitationPopover.tsx); mounted by PersonDeepDive:274 | outside-click / Escape (no visible label) | Dismiss the citation popover | `const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);` — terminal line 33 (and `onDoc` :30–32) | state action (keyboard/mouse) | WORKING-AS-CODED |
| C03-051 | `mps.compareLink` — [i18n.ts:1266](../../frontend/src/i18n.ts) (en "Compare MPs →") / [i18n.ts:520](../../frontend/src/i18n.ts) (ro "Compară parlamentarii →") | `mps.compareLink` | Intended affordance to reach MP comparison from the MPs page; route `/compare-mps` exists (router.tsx:458) | No render site anywhere: `grep compareLink` returns only i18n.ts:520 and :1266; [Mps.tsx](../../frontend/src/pages/Mps.tsx) contains no `<Link to="/compare-mps">` | dead (label defined, element never rendered) | **BROKEN** — defined affordance with zero call sites (see F4) |

## 2. Findings

### F1 — PartyProfile movement button: silent no-op and nested interactive content (C03-006, C03-041)

**Evidence.** [PartyProfile.tsx:177–202](../../frontend/src/pages/PartyProfile.tsx):
```
177:              <button type="button" key={m.id}
178:                onClick={() => m.person && setPersonId(m.person.id)}
179:                className="w-full text-left bg-slate-800/40 hover:bg-slate-800 rounded-md p-2 transition-colors"
...
196:                <ProvenanceStamp
197:                  sourceUrl={m.source_url}
198:                  confidence={m.confidence}
199:                  precision={m.precision}
200:                  note={m.reason}
201:                />
202:              </button>
```
[ProvenanceStamp.tsx:42–48](../../frontend/src/components/ProvenanceStamp.tsx):
```
42:      {sourceUrl && (
...
46:            <a href={sourceUrl} target="_blank" rel="noopener noreferrer"
47:               className="text-sky-400 hover:underline">{t("viewOriginal")} ↗</a>
```
**Reason.** Line 178 is a guarded no-op: when `m.person` is null the button is still rendered, focusable and visually active (line 179 has no `disabled` styling), but clicking does nothing — the "disabled person button" pattern flagged for attention. Separately, when `m.source_url` is present the provenance `<a>` at ProvenanceStamp.tsx:46 is nested inside the `<button>` at PartyProfile.tsx:177–202; this is invalid HTML (interactive content inside a button) and a click on "View original source" opens the new tab *and* bubbles to the button's `onClick`, opening the drawer unintentionally.

**Improvement.** At [PartyProfile.tsx:179](../../frontend/src/pages/PartyProfile.tsx) add `disabled={!m.person}` (plus a `disabled:` opacity class) so the no-op is explicit; move `<ProvenanceStamp>` (lines 196–201) out of the `<button>` into a sibling element (e.g. close the button at line 195 and wrap the stamp in a `<div>`), preserving layout.

### F2 — Mps "Next" bound uses rendered row count instead of page size (C03-027)

**Evidence.** [Mps.tsx:12](../../frontend/src/pages/Mps.tsx), [:43–47](../../frontend/src/pages/Mps.tsx):
```
12: const PAGE_SIZE = 60;
43: const rows = cards.data?.data ?? [];
45: const total = cards.data?.total ?? null;
46: const canPrev = offset > 0;
47: const canNext = total !== null ? offset + rows.length < total : false;
```
**Reason.** `canNext` is derived from `rows.length`, the number of rows actually returned, not the requested `limit: PAGE_SIZE` (line 37). If the API returns a short page while more records exist (e.g. backend cap, sparse/filtered page), `offset + rows.length < total` can be false and the "Next" button at line 203 is disabled prematurely, making later pages unreachable. `canPrev` (line 46) is correctly clamped in its handler (line 193).

**Improvement.** At [Mps.tsx:47](../../frontend/src/pages/Mps.tsx) compute the bound from the requested page size, e.g. `const canNext = total !== null ? offset + PAGE_SIZE < total : false;`, so paging is driven by the API total rather than the current render length.

### F3 — Person-destination links have no guard on their route param (C03-015, C03-017, C03-025, C03-031)

**Evidence.** [Committees.tsx:34–35](../../frontend/src/pages/Committees.tsx) `params={{ id: member.person_id }}`; [Committees.tsx:345–346](../../frontend/src/pages/Committees.tsx) `params={{ id: c.chair_person_id }}`; [Mps.tsx:158–159](../../frontend/src/pages/Mps.tsx) `params={{ id: m.id }}`; [MpComparison.tsx:195–196](../../frontend/src/pages/MpComparison.tsx) `params={{ id: selected[i]!.id }}`; destination [router.tsx:380](../../frontend/src/router.tsx) `path: "/person/$id"`.

**Reason.** Each link passes an id straight into a required `$` param with no runtime check. If any value is `""`, `null` or `undefined`, TanStack cannot build a valid `/person/…` path and the navigation would fail to match the `$id` route (falling through to `NotFound`, router.tsx:69–78). This is a data-dependent risk — the code declares the fields as strings, so actual emptiness cannot be proven from source alone. Resolver: the live payloads of `/api/committees/{id}/members`, `/api/analytics/committee-control` and `/api/mps` (client.ts:911–919, 953–963, 464–473).

**Improvement.** Guard each render, e.g. at [Committees.tsx:33](../../frontend/src/pages/Committees.tsx) use `{member.person_id ? <Link …>{member.name}</Link> : <span>{member.name}</span>}`; apply the same pattern at Committees.tsx:344, Mps.tsx:157 and MpComparison.tsx:194. Same attention applies to the party route: [Parties.tsx:110](../../frontend/src/pages/Parties.tsx) passes `p.short_name` into `/party/$shortName` (router.tsx:373) unguarded.

### F4 — Dead `mps.compareLink` affordance (C03-051)

**Evidence.** [i18n.ts:1266](../../frontend/src/i18n.ts) `"mps.compareLink": "Compare MPs →",` and [i18n.ts:520](../../frontend/src/i18n.ts) `"mps.compareLink": "Compară parlamentarii →",`. A repo-wide literal search for `compareLink` returns only those two definition lines. [Mps.tsx](../../frontend/src/pages/Mps.tsx) renders no link to `/compare-mps`, although that route is registered at [router.tsx:458](../../frontend/src/router.tsx).

**Reason.** A fully defined, translated call-to-action exists with zero call sites — the "dead `compareLink`" handler/label. Users browsing MPs have no rendered control to reach MP comparison from that page.

**Improvement.** Either add the control in [Mps.tsx](../../frontend/src/pages/Mps.tsx) (e.g. after the form at line 142: `<Link to="/compare-mps" search={scope.searchFor()} className="text-sky-400 hover:underline">{t("mps.compareLink")}</Link>`), or delete the unused key at i18n.ts:520 and :1266 so the catalog has one truth.

### F5 — PartyComparison default selections are not validated against the loaded party list (C03-011, C03-012)

**Evidence.** [PartyComparison.tsx:43–47](../../frontend/src/pages/PartyComparison.tsx):
```
43: const local = useSearch({ from: "/compare", select: (s) => s as Record<string, unknown> });
44: const partyA = typeof local.partyA === "string" ? local.partyA : "PSD";
45: const partyB = typeof local.partyB === "string" ? local.partyB : "PNL";
...
81: const a = findParty(partyA);
82: const b = findParty(partyB);
```
```
206:      {a && b && (
```
**Reason.** When the URL has no `partyA`/`partyB`, the selects are pinned to `"PSD"`/`"PNL"` (lines 44–45), but the `<option>` values come from `partyList` (:183–187, :197–201). If `/api/parties` lacks those short names, `findParty` (78–79) returns `undefined`, the comparison table at line 206 never renders, and the selects show no matching value — a silent empty page rather than an error. Whether the names exist is data-dependent; resolver: live `/api/parties` (client.ts:533).

**Improvement.** After `partyList` loads, if the URL params are absent, initialise them to the first two available `short_name`s (or add an explicit "no matching party" message when `!a || !b`) around [PartyComparison.tsx:64](../../frontend/src/pages/PartyComparison.tsx).

### Verified items raised for attention — no functional defect found

* **Parties.tsx `role="button"` (<tr>) at lines 107–119 has a keyboard handler.** Lines 113–118 implement `onKeyDown` for `"Enter"` and `" "` with `e.preventDefault()` and call the same `goToParty`; `tabIndex={0}` is at line 112. Verdict WORKING-AS-CODED. Improvement (semantics only): use a real `<button>`/`<Link>` inside the cell, or add `role="grid"`/`aria-rowindex`, because an ARIA `button` role on a `<tr>` overrides the expected row semantics.
* **Retry buttons are genuine controls.** `AsyncState` forwards `onRetry` to `StateView` ([AsyncState.tsx:78–83](../../frontend/src/components/ui/AsyncState.tsx)), which renders `RetryButton`; [RetryButton.tsx:18–20](../../frontend/src/components/RetryButton.tsx) is a `<button onClick={onRetry}>`. All 14 page-level `onRetry` handlers (C03-002/004/007/009/013/014/019/020/021/028/033/034/035) are therefore real, wired buttons. No page passes `onEmptyCta`, so empty states have no actionable CTA.
* **No `onKeyDown`-only or `onClick` interactive element was found without a keyboard equivalent** among the ten page files other than the drawer/popover document listeners (C03-044, C03-050), which do implement Escape.
* **Wikidata link targets (C03-005, C03-036, C03-045)** are string-interpolated from `wikidata_qid`; URL validity of the runtime value is data-dependent and not provable from source. Resolver: API payload + manual URL check.

## 3. Coverage and NOT PROVEN

**Coverage.** All ten assigned page files were read in full (Parties 145 lines, PartyProfile 211, PartyTimeline 295, PartyComparison 295, Coalitions 299, Committees 416, Mps 221, MpComparison 335, Demographics 217, PersonDeepDive 282). Every page-level `onClick`, `onKeyDown`, `onChange`, `onSubmit`, `<button>`, `<a>`, `<Link>`, `role="button"`, `disabled`, `<details>/<summary>` and `navigate(...)` call was enumerated. i18n keys attached to interactive labels were resolved in both locales with definition lines quoted (ro block :5–759, en block :760–1513). Route targets were checked against the registrations in [router.tsx:335–544](../../frontend/src/router.tsx); the `$`-parameter routes used here are `/party/$shortName` (:373) and `/person/$id` (:380). Shared components that render controls on these pages (ScopeControls, ProvenanceStamp, CitationPopover, PersonDrawer, MembershipGantt, AsyncState/ErrorState/RetryButton) were read and their interactive internals included as delegated rows C03-038–C03-050. `MembershipGantt` was read in full and contains **no** clickable element (only `title` tooltips at :59, :73, :87).

**NOT PROVEN (data-dependent; resolver named).** No network calls or browser interaction were performed, per the read-only constraint. Consequently:
1. Non-emptiness/validity of `member.person_id`, `c.chair_person_id`, `m.id`, `selected[i]!.id`, `p.short_name` and `wikidata_qid` cannot be established from source; resolver = live API payloads (`/api/mps`, `/api/committees*`, `/api/analytics/committee-control`, `/api/parties`, `/api/persons/*`; client.ts:464–473, 511–533, 911–919, 953–963). Rows C03-015/017/025/031 are marked NOT PROVEN for destination correctness for this reason; wiring itself is present in code.
2. Whether `"PSD"`/`"PNL"` exist in `/api/parties` cannot be established; resolver = live `/api/parties` response (F5).
3. Actual runtime reachability of a short page in Mps pagination cannot be observed; resolver = live `/api/mps?limit=60` payload versus the recorded `total` (F2).
4. Whether a click on the nested provenance link in PartyProfile actually opens the drawer as well is a browser-event-bubbling consequence; the markup nesting is code-proven (F1), the runtime double-action is inferred from DOM semantics, not observed.
5. No claim is made about rendered appearance, focus order in a real browser, screen-reader output, or production reachability of any page; those require a browser and are out of scope for this read-only, code-grounded note.

Elements: 51 | BROKEN: 1 | SUSPECT: 5 | NOT PROVEN: 4
