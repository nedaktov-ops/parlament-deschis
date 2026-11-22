---
id: CLICK-INV-C05
type: evidence
title: "Clickable inventory — C05 shared components (2026-11-22)"
description: "Read-only, code-grounded enumeration of every clickable/interactive element exposed by the assigned shared components at commit 8811216, with i18n resolution, callback/page wiring, accessibility handler evidence, and dead/unwired proofs."
status: active
authority: derived
tags: [type/evidence, lifecycle/active, domain/frontend]
source_paths: [frontend/src/components/Search.tsx, frontend/src/components/PersonDrawer.tsx, frontend/src/components/CitationPopover.tsx, frontend/src/components/ProvenanceStamp.tsx, frontend/src/components/EmptyState.tsx, frontend/src/components/ErrorState.tsx, frontend/src/components/LoadingState.tsx, frontend/src/components/RetryButton.tsx, frontend/src/components/DashboardCard.tsx, frontend/src/components/Hemicycle.tsx, frontend/src/components/SankeyFlow.tsx, frontend/src/components/SwitchTimeline.tsx, frontend/src/components/PartyNetwork.tsx, frontend/src/components/PartyListTable.tsx, frontend/src/components/PartyComparisonMatrix.tsx, frontend/src/components/CommitteeControl.tsx, frontend/src/components/TimeSlider.tsx, frontend/src/components/LegislatureSeatExplorer.tsx, frontend/src/components/VoteActivityChart.tsx, frontend/src/components/TimelineChart.tsx, frontend/src/components/DataViz.tsx, frontend/src/components/CrossChamberFlow.tsx, frontend/src/components/GroupLegend.tsx, frontend/src/components/InfoStat.tsx, frontend/src/components/AgeDistributionRadial.tsx, frontend/src/components/DataQualityGauge.tsx, frontend/src/components/MembershipGantt.tsx, frontend/src/components/ui/AsyncState.tsx, frontend/src/components/ui/AgeDistributionSection.tsx, frontend/src/components/ui/DashboardHeader.tsx, frontend/src/components/ui/Skeleton.tsx, frontend/src/components/ui/ThemeToggle.tsx, frontend/src/components/ui/TooltipText.tsx, frontend/src/i18n.ts, frontend/src/utils/a11y.ts]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# C05 — Clickable / interaction-semantics inventory

Scope: HEAD `88112168237e5c37841b785dccd2375f6cc40115` of `/home/nedaktov/parlament-deschis`. Every assigned file was read in full. All claims below cite exact line numbers of source at that commit. No network calls, no browser runs, no axe/contrast measurement were made — all runtime/AT claims are **NOT PROVEN** (see §4).

Resolver notes (code-grounded):
- `activateOnKey` = [`utils/a11y.ts`](../../frontend/src/utils/a11y.ts) L5–12: `if (event.key === "Enter" || event.key === " ") { event.preventDefault(); activate(); }` — Enter/Space activator used by `SankeyFlow`, `SwitchTimeline`, `AgeDistributionRadial`.
- i18n has two blocks: `ro` L5–759 and `en` L760–1517 in [`i18n.ts`](../../frontend/src/i18n.ts); default `lng: "ro"`, `fallbackLng: "en"` L1518–1519. Where a label is a `t(key, "default")` call, the literal default is quoted verbatim and the key's ro/en definition lines are given.

## 1. Complete inventory table

Legend — class: `in-app route` = TanStack navigate/Link; `external URL` = `<a target="_blank">`; `state action` = local component/page state or query refetch; `dead` = control unreachable or component with zero importers. Verdict values: `WORKING-AS-CODED`, `BROKEN`, `SUSPECT`, `NOT PROVEN`.

| ID | file:line | label / i18n (definition lines) | purpose (verbatim from code/prose) | callback / page wiring | class | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| C05-001 | Search.tsx L75–93 | placeholder/aria-label `t("search")`; ro L103 `"Caută un parlamentar…"`, en L857 `"Search an MP…"` | MP search input: `role="combobox"` L86, `aria-autocomplete="list"` L88 | `onChange` L78–82 → `setQ/setOpen/setActiveIndex`; `onFocus` L83 → `setOpen(true)`; `onKeyDown` L84 → handleKeyDown (C05-002) | state action | WORKING-AS-CODED |
| C05-002 | Search.tsx L44–71 | n/a (keyboard activator) | "ArrowDown"/"ArrowUp" move `activeIndex` and `scrollIntoView` L50–65; "Enter" selects L66–70; "Escape" closes L45–49 | `selectPerson` L37–42 → `onSelect(id)` L38 → router.tsx L244–248 `router.navigate({to:"/person/$id"…})` | in-app route | WORKING-AS-CODED |
| C05-003 | Search.tsx L111–125 | `p.name` L123 / `p.chambers.join(" · ")` L124 (data-driven, no i18n key) | `role="option"` L114, `aria-selected` L115; `onMouseEnter` L117, `onClick` L118 | `onClick` → `selectPerson(p.id)` → `onSelect` supplied by router.tsx L244. Native `<button>`; `tabIndex={-1}` L116; keyboard via input's `aria-activedescendant` L91 | in-app route | WORKING-AS-CODED |
| C05-004 | Search.tsx L20–26 | n/a (outside-click close handler) | `if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);` L22 | document `mousedown` listener; no page callback | state action | WORKING-AS-CODED |
| C05-005 | PersonDrawer.tsx L97 | n/a (`aria-hidden="true"` backdrop) | `<div aria-hidden="true" … onClick={onClose} />` | `onClose` from PartyProfile.tsx L208 `closePerson` = L26 `() => setPersonId(null)`. Non-native; **no tabIndex, no onKeyDown**; Escape covered by C05-007 | state action | WORKING-AS-CODED |
| C05-006 | PersonDrawer.tsx L116–118 | `t("close")` L117; ro L272 `"Închide"`, en L1019 `"Close"` | header close button `<button … onClick={onClose}>` | same `onClose` → PartyProfile.tsx L26. Native button | state action | WORKING-AS-CODED |
| C05-007 | PersonDrawer.tsx L51–82 | n/a (document focus trap) | "Escape" → `onClose()` L58–60; "Tab" wraps first/last focusable L62–75; `drawerRef.current?.focus()` L56; `previousFocus?.focus()` L80. Drawer `tabIndex={-1}` L103 | `onClose` → PartyProfile.tsx L26 | state action | WORKING-AS-CODED |
| C05-008 | PersonDrawer.tsx L143–152 | `{p.wikidata_qid} ↗` L150 (data-driven) | `<a href="https://www.wikidata.org/wiki/${p.wikidata_qid}" target="_blank" rel="noopener noreferrer">` L145–147 | no prop callback; static external link | external URL | WORKING-AS-CODED |
| C05-009 | PersonDrawer.tsx L243–255 | `t("viewOriginal") ↗` L250; ro L108 `"Vezi sursa originală"`, en L862 `"View original source"` | history `source_url` link, `target="_blank"` L246 | no prop callback; data URL from `api.personHistory` | external URL | WORKING-AS-CODED |
| C05-010 | PersonDrawer.tsx L125 | fallback `t("traseismRetry")` (RetryButton L24); ro L365 `"Reîncearcă"`, en L1111 `"Try again"` | `onRetry={() => person.refetch()}` | internal `useQuery` refetch | state action | WORKING-AS-CODED |
| C05-011 | CitationPopover.tsx L46–55 | `{items.length} {t("evidenceCount")}` L53; ro L283 `"surse"`, en L1030 `"sources"`; `title={t("citations")}` L48; ro L107 `"Surse"`, en L861 `"Sources"` | toggle `<button … onClick={() => setOpen(o => !o)}>` L46; `aria-expanded={open}` L49 | internal `setOpen`; native button | state action | WORKING-AS-CODED |
| C05-012 | CitationPopover.tsx L28–40 | n/a (outside-click + Escape close) | `onDoc` outside-click L30–32; `onKey` `e.key === "Escape" && setOpen(false)` L33 | document `mousedown`/`keydown`; keyboard Escape supported | state action | WORKING-AS-CODED |
| C05-013 | CitationPopover.tsx L72–84 | `t("viewOriginal") ↗` L79; ro L108 / en L862 | evidence `source_url` link, `target="_blank"` L75 | data URL from `EvidenceItem` | external URL | WORKING-AS-CODED |
| C05-014 | CitationPopover.tsx L85–97 | `t("viewArchive") ↗` L92; ro L113 `"Vezi copia arhivată"`, en L867 `"View archived copy"` | evidence `snapshot_url` link, `target="_blank"` L88 | data URL from `EvidenceItem` | external URL | WORKING-AS-CODED |
| C05-015 | ProvenanceStamp.tsx L42–50 | `t("viewOriginal") ↗` L47; ro L108 / en L862 | `sourceUrl` link, `target="_blank"` L46 | data URL from props | external URL | WORKING-AS-CODED |
| C05-016 | ProvenanceStamp.tsx L61–75 | `{(snapshotHash ?? "link").slice(0,12)} ↗` L68 (data-driven; `title=snapshotHash`) | `snapshotUrl` link, `target="_blank"` L66; else non-interactive `<span title>` L71 | data URL from props | external URL | WORKING-AS-CODED |
| C05-017 | EmptyState.tsx L42–51 | `ctaLabel` / `aria-label={ctaLabel}` L47 (caller string) | `{onCta && ctaLabel && (<button type="button" onClick={onCta} …>)}` L42–45 | only supplier is AsyncState.tsx L89–90 `ctaLabel={emptyCtaLabel} onCta={onEmptyCta}`; **no page supplies either** (proof §3) | dead | WORKING-AS-CODED (unreachable) |
| C05-018 | ErrorState.tsx L38–45 | `label={t("retry","Retry")}` L41, `ariaLabel` L42; ro L271 `"Reîncearcă"`, en L1018 `"Retry"` | `{onRetry && <RetryButton onRetry={onRetry} …/>}` | `onRetry` from StateView.tsx L79–83 ← AsyncState `onRetry` call sites (e.g. LiveDashboard.tsx L128, L214, L229, L234, L255, L272) | state action | WORKING-AS-CODED |
| C05-019 | LoadingState.tsx L46–53 | `label={retryLabel}`, `ariaLabel={retryLabel}` L49–50 (caller string) | `{onRetry && retryLabel && (<RetryButton onRetry={onRetry} …/>)}` L46 | StateView.tsx L73–76 passes only `label`/`description`; Committees.tsx L375 passes only `label`; **no `onRetry`/`retryLabel` ever supplied** (proof §3) | dead | WORKING-AS-CODED (unreachable) |
| C05-020 | RetryButton.tsx L18–25 | `{label ?? t("traseismRetry")}` L24; `aria-label={ariaLabel}` L21; ro L365 / en L1111 | `<button type="button" onClick={onRetry} …>` L18–20 | supplied by PersonDrawer.tsx L125, SankeyFlow.tsx L186, TimelineChart.tsx L237, ChamberView.tsx L37, ErrorState.tsx L39–44, LoadingState.tsx L47–52, LiveFeed.tsx L239 | state action | WORKING-AS-CODED |
| C05-021 | DashboardCard.tsx L79–85 | `title` L68 + sr-only `t("navigateTo","Navigate to") {title}` L83; ro L101 `"Navighează către"`, en L855 `"Navigate to"` | `<Link to={linkTo} search={searchParams} className={cardClass}>` L81 | LiveDashboard.tsx L140 `"/mps"`, L151 `"/mps"`, L162 `"/traseism"`, L174 `"/committees"` | in-app route | WORKING-AS-CODED |
| C05-022 | DashboardCard.tsx L88–92 | `content` = `title` + `value` L64–74 (caller strings) | `<button type="button" className={cardClass} onClick={onClick}>` L89 | only importer LiveDashboard.tsx supplies `linkTo` on all 4 cards (L140/151/162/174); `onClick` never supplied (proof §3) | dead | WORKING-AS-CODED (unreachable) |
| C05-023 | Hemicycle.tsx L108–120 | none (no `aria-label`, no `role`); `<title>` absent; hover tooltip L122–128 | `<circle … onMouseEnter L116 onMouseLeave L117 onClick={() => s.member && onSelect(s.member.person_id)} L118>` | `onSelect` ← ChamberView.tsx L45 ← LegislatureSeatExplorer.tsx L147 `onOpenPerson` ← LiveDashboard.tsx L202 `openPerson` → `/person/$id`. **Non-native: no `tabIndex`, no `onKeyDown`, parent `<svg aria-hidden="true" focusable="false">` L107** | in-app route | **SUSPECT** (see F1) |
| C05-024 | Hemicycle.tsx L129–132 | `t("hemicycleMemberList",{count:total})` L131; ro L124 `"Răsfoiește parlamentarii ({{count}})"`, en L878 `"Browse members ({{count}})"` | native `<details><summary className="cursor-pointer …">` L129–130 | no callback; native disclosure | state action | WORKING-AS-CODED |
| C05-025 | Hemicycle.tsx L133 | `aria-label="List of all MPs in this hemicycle group"` (hardcoded) | keyboard scroll region `<div … max-h-64 overflow-y-auto … tabIndex={0}>` | no callback; focusable scroll container | state action (scroll) | WORKING-AS-CODED |
| C05-026 | Hemicycle.tsx L140–148 | `{member.name}` + `{member.role}` L145–146 (data-driven) | `<button type="button" onClick={() => onSelect(member.person_id)}>` L142 | `onSelect` chain as C05-023 → `/person/$id`. Native button, focus-visible outline L143 | in-app route | WORKING-AS-CODED |
| C05-027 | SankeyFlow.tsx L248–264 | `t("a11y.sankeyLink","Flow from {{from}} to {{to}}: {{count}} switches",…)` L257; ro L134, en L888; `<title>{linkText}</title>` L263 | `<path role="button" tabIndex={0} onClick={() => setSelected(link)} L259 onKeyDown={(e) => activateOnKey(e, () => setSelected(link))} L260>` | internal `setSelected`; non-native but `tabIndex=0` + Enter/Space via `activateOnKey` | state action | WORKING-AS-CODED |
| C05-028 | SankeyFlow.tsx L269–295 | `t("a11y.sankeyNode","Party {{name}}: {{count}} switches total",…)` L275; ro L135, en L889 | `<g role="button" tabIndex={0} onClick={() => setSelectedNode(node)} L277 onKeyDown={…activateOnKey} L278>` | internal `setSelectedNode`; `tabIndex=0` + Enter/Space via `activateOnKey` | state action | WORKING-AS-CODED |
| C05-029 | SankeyFlow.tsx L180–189 | fallback `t("traseismRetry")`; ro L365 / en L1111 | error-state `onRetry={() => summary.refetch()}` L186 | internal `useQuery` refetch; importer Traseism.tsx L15, L892 | state action | WORKING-AS-CODED |
| C05-030 | SwitchTimeline.tsx L170–191 | `t("a11y.switchWave","Switch wave on {{date}}: {{count}} switches",…)` L181; ro L139, en L893; `<title>{waveLabel}</title>` L190 | `<rect role="button" tabIndex={0} onClick={() => onWaveClick?.(wave)} L186 onKeyDown={…activateOnKey} L187>` | `onWaveClick` ← LiveDashboard.tsx L277 `() => navigate({to:"/traseism"…})`; `tabIndex=0` + Enter/Space | in-app route | WORKING-AS-CODED |
| C05-031 | SwitchTimeline.tsx L214–231 | `"View all →"` L230 (hardcoded, not `t()`) | `<button type="button" … onClick={() => onWaveClick?.({id:"all",…} as SwitchWaveData)} L217–228>` | `onWaveClick` ← LiveDashboard.tsx L277 → `/traseism`. Native button | in-app route | WORKING-AS-CODED (i18n gap F8) |
| C05-032 | PartyNetwork.tsx L90–126 | `t("a11y.partyNode","Party {{party}}: {{members}} members",…)` L100–103; ro L132, en L886 | `<button … aria-describedby={`${uid}-node-${node.id}`} onClick={() => onNodeClick?.(node.short_name || node.id)} L105>` | `onNodeClick={openParty}` LiveDashboard.tsx L260 → `/party/$shortName` (L86–92). Native button | in-app route | WORKING-AS-CODED |
| C05-033 | PartyNetwork.tsx L145–153 | `"View all →"` L151 (hardcoded) | `{onViewAll && (<button … onClick={onViewAll} L149>View all →</button>)}` | `onViewAll` ← LiveDashboard.tsx L261 → `/mps`. Native button | in-app route | WORKING-AS-CODED (i18n gap F8) |
| C05-034 | PartyListTable.tsx L60–99 | `{party.short_name || party.name}` L80, rank `#{index+1}` L69 (data-driven) | `<button type="button" onClick={() => onPartyClick?.(party.short_name || party.id)} L64>` | `onPartyClick={openParty}` LiveDashboard.tsx L219 → `/party/$shortName`. Native button, `min-h-11` | in-app route | WORKING-AS-CODED |
| C05-035 | PartyListTable.tsx L55 | `aria-label="List of parties by member count"` (hardcoded) | keyboard scroll region `<div … max-h-64 overflow-y-auto tabIndex={0}>` | no callback; focusable scroll container | state action (scroll) | WORKING-AS-CODED |
| C05-036 | PartyListTable.tsx L106–113 | `"View all →"` L112 (hardcoded) | `{onViewAll && (<button … onClick={onViewAll} L110>View all →</button>)}` | `onViewAll` ← LiveDashboard.tsx L220 → `/parties`. Native button | in-app route | WORKING-AS-CODED (i18n gap F8) |
| C05-037 | PartyComparisonMatrix.tsx L50–72 | `{cell.from} →` L56, `{cell.to}` L71, `{cell.count}` L69 (data-driven) | `<button type="button" onClick={() => onCellClick?.(cell.from, cell.to)} L53>` | `onCellClick` has **zero suppliers** — component has no importers (proof §3) | dead | WORKING-AS-CODED (unreachable) |
| C05-038 | PartyComparisonMatrix.tsx L81–87 | `"View all transitions →"` L86 (hardcoded) | `<button type="button" onClick={() => onCellClick?.('all','all')} L83>` | `onCellClick` has zero suppliers (proof §3) | dead | WORKING-AS-CODED (unreachable) |
| C05-039 | PartyComparisonMatrix.tsx L45 | `t("a11y.switchMatrixScroll","Scrollable party switch matrix")`; ro L138, en L892 | scroll region `<div … tabIndex={0} role="region" aria-label=…>` | no callback; component unused | dead | WORKING-AS-CODED (unreachable) |
| C05-040 | CommitteeControl.tsx L97–116 | `t("a11y.committeeChair","Show chair for {{party}}", {party})` L99; ro L129, en L883; `aria-describedby` L100 | `<button … onClick={() => chairForParty && onChairClick?.(chairForParty)} L102>` | `onChairClick` ← LiveDashboard.tsx L227 `(chair) => chair.chair_person_id && openPerson(chair.chair_person_id)` → `/person/$id`. Native button | in-app route | WORKING-AS-CODED |
| C05-041 | CommitteeControl.tsx L153–167 | `"View all chairs ({chairs.length})"` L157 (hardcoded) | native `<details><summary className="cursor-pointer …">` L155–156 | no callback; native disclosure | state action | WORKING-AS-CODED |
| C05-042 | CommitteeControl.tsx L159 | `aria-label="List of all chairs in committees"` (hardcoded) | keyboard scroll region `<ul … max-h-32 overflow-y-auto tabIndex={0}>` | no callback; focusable scroll container | state action (scroll) | WORKING-AS-CODED |
| C05-043 | TimeSlider.tsx L63–69 | `{playing ? t("pause") : t("play")}` L68; ro L97/L96, en L851/L850 | `<button type="button" onClick={() => setPlaying(p => !p)} aria-pressed={playing} disabled={reducedMotion}>` | internal `setPlaying`; component has no importers (proof §3) | dead | WORKING-AS-CODED (unreachable) |
| C05-044 | TimeSlider.tsx L77–87 | sr-only `<label htmlFor="as-of-date">{t("selectDate")}</label>` L76; ro L144, en L898; `aria-valuetext={value}` L85 | `<input id="as-of-date" type="range" onChange={(e) => onChange(toISO(new Date(Number(e.target.value))))} L84>` | `onChange` prop has zero suppliers (proof §3) | dead | WORKING-AS-CODED (unreachable) |
| C05-045 | LegislatureSeatExplorer.tsx L82–90 | `{playing ? t("pause") : t("play")}` L89; ro L97/L96, en L851/L850 | play/pause `<button onClick={() => setPlaying(p => !p)} aria-pressed L86 disabled={reducedMotion || stops.length < 2} L87>` | internal autoplay interval L44–53; native button | state action | WORKING-AS-CODED |
| C05-046 | LegislatureSeatExplorer.tsx L91–99 | `aria-label={t("chamberEvolutionPrev","Legislatura anterioară")}` L96; ro L199, en L953; glyph `←` L98 | `<button onClick={() => selectIndex(index - 1)} disabled={index <= 0}>` | `selectIndex` L38–42 → `onSelectLegislature(list[next].start, list[next].id)` ← LiveDashboard.tsx L201 `scope.setScope({date,legislature})` | state action | WORKING-AS-CODED |
| C05-047 | LegislatureSeatExplorer.tsx L104–114 | `<label htmlFor="legislature-start-slider" className="sr-only">{t("chamberEvolutionSelect",…)}</label>` L101–103; ro L198, en L952; `aria-valuetext` L112 | `<input type="range" onChange={(e) => selectIndex(Number(e.target.value))} L111>` | `onSelectLegislature` ← LiveDashboard.tsx L201 → scope | state action | WORKING-AS-CODED |
| C05-048 | LegislatureSeatExplorer.tsx L130–138 | `aria-label={t("chamberEvolutionNext","Legislatura următoare")}` L135; ro L200, en L954; glyph `→` L137 | `<button onClick={() => selectIndex(index + 1)} disabled={index < 0 || index >= stops.length - 1}>` | `onSelectLegislature` ← LiveDashboard.tsx L201 → scope | state action | WORKING-AS-CODED |
| C05-049 | VoteActivityChart.tsx L180–186 | `errorLabel={t("view.grafice.activityLoadError","Failed to load vote activity.")}` L184; ro L588, en L1351 | `<AsyncState … onRetry={() => void activityQuery.refetch()}>` → ErrorState → RetryButton | internal `activityQuery.refetch()`; no page callback. Importer Grafice.tsx L8, L218 | state action | WORKING-AS-CODED |
| C05-050 | VoteActivityChart.tsx L106–109 | n/a (chart-library interaction config) | `dataZoom: [{type:"inside",…},{type:"slider",bottom:8,height:18,…}]`; container `role="img"` L191 | no React callback; ECharts canvas. Runtime keyboard/AT reachability **NOT PROVEN** (F9) | state action (zoom) | **NOT PROVEN** |
| C05-051 | TimelineChart.tsx L192–206 | `{t(c)}` L203 → `t("deputies")`/`t("senate")` (defined in i18n `deputies`/`senate` keys) | chamber toggle buttons `<button onClick={() => setChamber(c)} aria-pressed={chamber === c}>` L194–196 | internal `setChamber`; native buttons with `aria-pressed` | state action | WORKING-AS-CODED |
| C05-052 | TimelineChart.tsx L234–239 | fallback `t("traseismRetry")`; ro L365 / en L1111 | `<RetryButton onRetry={() => timeline.refetch()} />` L237 | internal `useQuery` refetch. Importer LegislatureDetail.tsx L13, L223 | state action | WORKING-AS-CODED |
| C05-053 | TimelineChart.tsx L246–250 | `t("timelineTableCaption")` L249; ro L166, en L920 | native `<details><summary className="cursor-pointer …">` L247–248 | no callback; native disclosure | state action | WORKING-AS-CODED |
| C05-054 | TimelineChart.tsx L251 | `t("timelineTableCaption")`; ro L166 / en L920 | scroll region `<div className="overflow-x-auto …" tabIndex={0} role="region" aria-label=…>` | no callback; focusable scroll container | state action (scroll) | WORKING-AS-CODED |
| C05-055 | CrossChamberFlow.tsx L83–107 | `ariaLabel = member.name (+ ": " + chamberNames)` L79–81; visible `{member.name}` L92 (data-driven) | `<button type="button" onClick={() => onPersonClick?.(member.person_id)} disabled={!onPersonClick} L86–87>` | `onPersonClick={openPerson}` LiveDashboard.tsx L289 → `/person/$id` (L94–100). Native button, explicitly disabled when handler absent | in-app route | WORKING-AS-CODED |
| C05-056 | CrossChamberFlow.tsx L65–70 | `aria-label={t("crossChamberTableCaption")}` L69; ro L188, en L942 | scroll region `<div … overflow-y-auto tabIndex={0} role="region">` | no callback; focusable scroll container | state action (scroll) | WORKING-AS-CODED |
| C05-057 | AgeDistributionRadial.tsx L92–112 | `aria-label: "Show details for ${slice.label} cohort"` L102 (hardcoded) + `<title>` L110 | conditional `<path … role="button" tabIndex={0} onClick={() => onCohortClick?.(slice)} L103 onKeyDown={…activateOnKey} L104>` — only when `interactive = Boolean(onCohortClick)` L73 | sole caller AgeDistributionSection.tsx L40 passes **no** `onCohortClick` → `interactive=false`; arc renders non-interactive (proof §3). `tabIndex=0` + Enter/Space exist in the dead branch | dead | WORKING-AS-CODED (unreachable) |
| C05-058 | DataQualityGauge.tsx L26–27, L64–74 | prop `onRetry?: () => void` L27 → `StateView … onRetry={onRetry}` L69; error label `t("dashboard.loadError")` L70; ro L756, en L1510 | retry wiring for inline StateView; rendered RetryButton belongs to ErrorState (C05-018/020) | `onRetry` ← LiveDashboard.tsx L234 `() => void coverageDetailed.refetch()` | state action | WORKING-AS-CODED |
| C05-059 | ui/AsyncState.tsx L78–83 | `errorLabel ?? t("state.error.title")` L80; ro L739, en L1493; retry via `onRetry` L82 | `<ErrorState … onRetry={onRetry} />` → RetryButton | many AsyncState call sites, e.g. LiveDashboard.tsx L125–130, L211–216, VoteActivityChart L180–186, AgeDistributionSection L29–35 | state action | WORKING-AS-CODED |
| C05-060 | ui/AsyncState.tsx L85–92 | `ctaLabel={emptyCtaLabel}` L89, `onCta={onEmptyCta}` L90 (props declared L44–45) | `<EmptyState … ctaLabel onCta … />` → C05-017 | `emptyCtaLabel`/`onEmptyCta` never passed by any call site (proof §3) | dead | WORKING-AS-CODED (unreachable) |
| C05-061 | ui/AgeDistributionSection.tsx L29–35 | `errorLabel={t("ageDistributionError")}` L33; ro L143, en L897 | AsyncState `onRetry={() => void shift.refetch()}` L32 → ErrorState → RetryButton | internal `useQuery` refetch | state action | WORKING-AS-CODED |
| C05-062 | ui/ThemeToggle.tsx L32–51 | `aria-label={label}` L36, `title={label}` L38 where `label = t("toggleTheme","Toggle colour theme")` L29 (ro L128, en L882); visible `{theme === "dark" ? t("themeLight","Light") : t("themeDark","Dark")}` L50 (ro L140/L141, en L894/L895) | `<button onClick={() => setTheme(nextTheme)} aria-pressed={theme === "light"}>` L32–37; toggles `document.documentElement.dataset.theme` + `localStorage` L19–26 | internal `setTheme`; rendered by DashboardHeader.tsx L15 → LiveDashboard.tsx L121 | state action | WORKING-AS-CODED |

## 2. Findings with Evidence, Reason, Improvement

### F1 — Hemicycle seats are exposed as clickable but have no keyboard path (C05-023) — SUSPECT
**Evidence** ([Hemicycle.tsx](../../frontend/src/components/Hemicycle.tsx) L107, L108–120):
```
107: <svg viewBox="0 0 100 56" className="w-full" aria-hidden="true" focusable="false">
109: <circle
115:   className="cursor-pointer transition-opacity hover:opacity-70"
116:   onMouseEnter={() => setHover(s)}
117:   onMouseLeave={() => setHover(null)}
118:   onClick={() => s.member && onSelect(s.member.person_id)}
119: />
```
No `role`, no `tabIndex`, no `onKeyDown`, and the parent SVG is `aria-hidden="true" focusable="false"`. `activateOnKey` is not imported (imports L1–3 only).
**Reason**: A non-native interactive node with `onClick` only is not keyboard-operable and is removed from the accessibility tree by the ancestor `aria-hidden`. The accessible member list (C05-026) is a separate mouse/keyboard path, but the seat itself — the primary `onSelect` target — is mouse-only. This is a code-grounded keyboard/AT gap, not a runtime measurement.
**Improvement**: At Hemicycle.tsx L109–119, either (a) add `role="button"`, `tabIndex={0}`, an `aria-label` naming the member, and `onKeyDown={(e) => activateOnKey(e, () => s.member && onSelect(s.member.person_id))}` using the existing resolver from `../utils/a11y`, and remove `aria-hidden`/`focusable="false"` from the L107 SVG (or give it `role="group"` with a label); or (b) mark the SVG purely decorative and rely solely on the L142 member buttons, deleting the seat `onClick` L118 so no interactive affordance is exposed without a keyboard equivalent.

### F2 — EmptyState CTA is unreachable (C05-017 / C05-060) — dead
**Evidence** ([EmptyState.tsx](../../frontend/src/components/EmptyState.tsx) L42–45; [AsyncState.tsx](../../frontend/src/components/ui/AsyncState.tsx) L89–90):
```
42: {onCta && ctaLabel && (
43:   <button
45:     onClick={onCta}
```
```
89: ctaLabel={emptyCtaLabel}
90: onCta={onEmptyCta}
```
Importer search: `grep -rn "onEmptyCta\|emptyCtaLabel" frontend/src` returns only AsyncState.tsx L44–45, L61–62, L89–90 (declarations/forwarding). Direct EmptyState users pass only `title`: Parties.tsx L91, Committees.tsx L397–402.
**Reason**: Both guards (`onCta`, `ctaLabel`) are always falsy at every call site, so the button never renders. Correct code, zero wiring.
**Improvement**: Either supply `onEmptyCta` + `emptyCtaLabel` at an AsyncState call site that needs recovery (e.g. LiveDashboard.tsx L211–216), or delete the CTA branch L42–51 and the four props L5–6/L26–27/L44–45 if no caller will ever use it.

### F3 — LoadingState retry is unreachable (C05-019) — dead
**Evidence** ([LoadingState.tsx](../../frontend/src/components/LoadingState.tsx) L46–48; [AsyncState.tsx](../../frontend/src/components/ui/AsyncState.tsx) L72–77; [Committees.tsx](../../frontend/src/pages/Committees.tsx) L375):
```
46: {onRetry && retryLabel && (
47:   <RetryButton
48:     onRetry={onRetry}
```
```
73: <LoadingState
74:   label={loadingLabel ?? t("loading")}
75:   description={loadingDescription}
76: />
```
```
375: <LoadingState label={t("loading", "Loading…")} />
```
**Reason**: No supplier passes `onRetry` or `retryLabel` to LoadingState; the retry control is dead. (ErrorState's retry IS wired — C05-018.)
**Improvement**: Remove the retry branch L46–53 and props L6–7/L13–14, or have StateView forward `onRetry`/`retryLabel` to LoadingState for long-running loads at AsyncState.tsx L72–77.

### F4 — DashboardCard's button branch is unreachable (C05-022) — dead
**Evidence** ([DashboardCard.tsx](../../frontend/src/components/DashboardCard.tsx) L79–92; [LiveDashboard.tsx](../../frontend/src/pages/LiveDashboard.tsx) L132–176):
```
79: if (linkTo) {
81:   <Link to={linkTo} search={searchParams} className={cardClass}>
88: return (
89:   <button type="button" className={cardClass} onClick={onClick}>
```
All four call sites pass `linkTo` (L140 `"/mps"`, L151 `"/mps"`, L162 `"/traseism"`, L174 `"/committees"`); importer search shows LiveDashboard.tsx is the only importer of DashboardCard.
**Reason**: The `onClick` prop (DashboardCard.tsx L12, L57) is never supplied; the `<button>` branch cannot render.
**Improvement**: Delete the `onClick` prop and button branch L88–92, or add a no-`linkTo` card with a real `onClick` at a call site.

### F5 — PartyComparisonMatrix is a fully unwired component (C05-037/038/039) — dead
**Evidence**: `grep -rn "PartyComparisonMatrix" --include='*.tsx' frontend/src` returns only self-references in PartyComparisonMatrix.tsx L9, L15, L19. No import, no JSX usage.
**Reason**: Both clickable buttons L50–72 and L81–87 call `onCellClick?.()`, which no caller supplies; the component never mounts.
**Improvement**: Either wire it into a page (its matrix/switch data shape matches `traseismSummary().matrix`) with `onCellClick` navigating to a filtered `/traseism` view, or delete the file (and its test fixtures, if any) to avoid shipping dead interactive code.

### F6 — TimeSlider is a fully unwired component (C05-043/044) — dead
**Evidence**: `grep -rn "TimeSlider" --include='*.tsx' frontend/src` returns only TimeSlider.tsx L9 (its own declaration).
**Reason**: The play/pause button L63–69 and the range input L77–87 (whose `onChange` prop L13/L19 has zero suppliers) are unreachable; autoplay `setInterval` L41–58 can never start.
**Improvement**: Wire TimeSlider into a page that owns an `onChange(iso)` date setter, or delete it. Note `LegislatureSeatExplorer` (C05-045–048) already provides the live date/legislature slider, so deletion is the lower-risk option.

### F7 — AgeDistributionRadial's interactive arcs are unreachable (C05-057) — dead
**Evidence** ([AgeDistributionRadial.tsx](../../frontend/src/components/AgeDistributionRadial.tsx) L73, L98–108; [AgeDistributionSection.tsx](../../frontend/src/components/ui/AgeDistributionSection.tsx) L40):
```
73: const interactive = Boolean(onCohortClick);
98: {...(interactive
100:   role: "button", tabIndex: 0,
103:   onClick: () => onCohortClick?.(slice),
```
```
40: <AgeDistributionRadial cohorts={cohorts} totalAge={total} width={250} height={250} />
```
**Reason**: The only caller omits `onCohortClick`, so `interactive` is false and the spread object (including `role="button"`, `tabIndex=0`, keyboard and click handlers) is never applied; arcs are plain `<path>` under a `role="img"` SVG L83.
**Improvement**: Pass an `onCohortClick` from AgeDistributionSection.tsx L40 (e.g. navigate/filter by party cohort) to activate the existing accessible controls, or remove the dead conditional branch L98–108.

### F8 — Hardcoded English "View all" labels in three live controls — minor i18n gap
**Evidence**: SwitchTimeline.tsx L230 `"View all →"`; PartyNetwork.tsx L151 `"View all →"`; PartyListTable.tsx L112 `"View all →"`; PartyComparisonMatrix.tsx L86 `"View all transitions →"`; CommitteeControl.tsx L157 `"View all chairs ({chairs.length})"`. None is wrapped in `t()`, while sibling chrome is (e.g. C05-032 `a11y.partyNode`).
**Reason**: Factually hardcoded literals; with `lng: "ro"` (i18n.ts L1518) these render English text in the Romanian default locale. Code-grounded; visual/runtime impact NOT PROVEN.
**Improvement**: Add a `viewAll` key to both i18n blocks and replace each literal with `t("viewAll")`, keeping the arrow as a separate `aria-hidden` span.

### F9 — ECharts dataZoom interaction reachability not determinable from this repo (C05-050) — NOT PROVEN
**Evidence** ([VoteActivityChart.tsx](../../frontend/src/components/VoteActivityChart.tsx) L106–109, L188–195):
```
106: dataZoom: [
107:   { type: "inside", start: 0, end: 100 },
108:   { type: "slider", bottom: 8, height: 18, start: 0, end: 100 },
192:   role="img"
```
**Reason**: The zoom/slider controls are created by the third-party ECharts canvas at runtime; no repo code defines their focusability, keyboard handling, or ARIA. Whether a keyboard/screen-reader user can operate them cannot be resolved from source, and no browser run was performed.
**Improvement**: If the chart must be operable by keyboard, add an out-of-canvas accessible date-range control (e.g. reuse TimeSlider after F6) or verify ECharts' ARIA option (`aria.enabled`) in a browser test and document the result. Runtime claims remain NOT PROVEN until then.

## 3. Dead / unwired components list with proof

| Component | Proof (importer search at commit 8811216) | Consequence |
| --- | --- | --- |
| [TimeSlider.tsx](../../frontend/src/components/TimeSlider.tsx) | `grep -rn "TimeSlider" --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' .` → only `./frontend/src/components/TimeSlider.tsx:9:export default function TimeSlider({` | C05-043, C05-044 dead |
| [PartyComparisonMatrix.tsx](../../frontend/src/components/PartyComparisonMatrix.tsx) | same search → only self refs at L9, L15, L19 | C05-037, C05-038, C05-039 dead |
| EmptyState CTA (component is used, control is not) | `grep -rn "onEmptyCta\|emptyCtaLabel" frontend/src` → only AsyncState.tsx L44–45, L61–62, L89–90; `grep -rn "<EmptyState" frontend/src` → Parties.tsx L91 and Committees.tsx L397 pass only `title` | C05-017, C05-060 dead |
| LoadingState retry (component is used, control is not) | `<LoadingState` call sites: AsyncState.tsx L73–76 (label/description only) and Committees.tsx L375 (label only) — no `onRetry`/`retryLabel` anywhere | C05-019 dead |
| DashboardCard button branch (component is used, branch is not) | only importer LiveDashboard.tsx; all 4 usages pass `linkTo` at L140, L151, L162, L174 | C05-022 dead |
| AgeDistributionRadial arcs (component is used, control is not) | only caller AgeDistributionSection.tsx L40 omits `onCohortClick`; `grep -rn "onCohortClick" frontend/src` → only AgeDistributionRadial.tsx L16, L38, L73, L103, L105 | C05-057 dead |

Counter-proof (components that ARE wired): Search ← router.tsx L244; PersonDrawer ← PartyProfile.tsx L208; Hemicycle ← ChamberView.tsx L45; SankeyFlow ← Traseism.tsx L15/L892; VoteActivityChart ← Grafice.tsx L8/L218; TimelineChart ← LegislatureDetail.tsx L13/L223; PartyNetwork, SwitchTimeline, CrossChamberFlow, PartyListTable, CommitteeControl, DataQualityGauge, LegislatureSeatExplorer, DashboardCard(Link branch) ← LiveDashboard.tsx L198, L217, L224, L231, L257, L274, L287, L132–176.

## 4. Coverage and NOT PROVEN

Files read IN FULL: all 27 named component files plus all 6 files under `frontend/src/components/ui/` (AsyncState, AgeDistributionSection, DashboardHeader, Skeleton, ThemeToggle, TooltipText). Resolvers read: `utils/a11y.ts` (L1–13), `i18n.ts` (full, 1522 lines). Call-site files read/grepped: `router.tsx`, `pages/LiveDashboard.tsx` (full), `pages/PartyProfile.tsx`, `pages/Traseism.tsx`, `pages/Grafice.tsx`, `pages/LegislatureDetail.tsx`, `pages/Committees.tsx`, `pages/Parties.tsx`, plus repo-wide importer greps.

Components with **no clickable/interactive element** (verified by full read; no `onClick`, `onChange`, `onKeyDown`, `<a`, `<button`, `<input`, `<select`, `role="button"`, `tabIndex`, `onSelect*` prop activator):
- [DataViz.tsx](../../frontend/src/components/DataViz.tsx): `Sparkline` `role="img" aria-hidden` L42–43; `DataBar` static L76–91; `ProgressRing` `role="img" aria-label` L119–120; `StatBadge` static L163–169. No handlers.
- [GroupLegend.tsx](../../frontend/src/components/GroupLegend.tsx): static `<div>` list L7–23.
- [InfoStat.tsx](../../frontend/src/components/InfoStat.tsx): static card; `card-hover hover:shadow-lg` L54 is CSS-only, no click handler — visual affordance only (code-grounded).
- [MembershipGantt.tsx](../../frontend/src/components/MembershipGantt.tsx): `title` tooltips L59/L73/L87 only; no handlers/focusable nodes.
- [Skeleton.tsx](../../frontend/src/components/ui/Skeleton.tsx): static placeholder L8–10.
- [TooltipText.tsx](../../frontend/src/components/ui/TooltipText.tsx): `role="tooltip"` + `pointer-events-none` L15–16 — description target, not activatable.
- [ProvenanceStamp.tsx](../../frontend/src/components/ProvenanceStamp.tsx): the `snapshotHash`-only case L71 is a `<span title>`, not interactive.
- [DashboardHeader.tsx](../../frontend/src/components/ui/DashboardHeader.tsx): no handler of its own; delegates to ThemeToggle (C05-062).

Accessibility dimension (from code only): every non-native interactive node was checked for a keyboard handler and `tabIndex`:
- Have both: SankeyFlow path C05-027 (`tabIndex={0}` L256, `onKeyDown` L260), SankeyFlow g C05-028 (L274, L278), SwitchTimeline rect C05-030 (L180, L187), AgeDistributionRadial path C05-057 (L101, L104 — dead branch). All use `activateOnKey` (Enter/Space, `preventDefault`) — `utils/a11y.ts` L5–12.
- Native buttons/links/inputs (focusable by default): C05-001/003/006/008/009/011/013/014/015/016/017/018/019/020/021/022/024/026/031/032/033/034/036/037/038/040/041/043/044/045/046/047/048/051/052/053/055/059/061/062. `<details>/<summary>` C05-024/041/053 are native disclosures; scroll regions C05-025/035/039/042/054/056 carry `tabIndex={0}` with `aria-label`.
- Missing both: Hemicycle seat C05-023 (F1). Backdrop C05-005 is `aria-hidden` with `onClick` only, but Escape-close is provided document-wide by C05-007, so close remains keyboard-reachable.

**NOT PROVEN** (no browser/AT/axe run, no network): all runtime rendering, focus order in the live DOM, screen-reader announcements (including `role="status"`/`aria-live` nodes), visual focus-ring visibility, 200%/400% zoom, forced-colors/reduced-motion *effects*, contrast ratios, and ECharts canvas interaction (C05-050/F9). Mentions of `focus-visible:*` classes are code observations only, not verified rendering. No claim of WCAG conformance is made.

Relative source links used above resolve from this note's directory (`40-FRONTEND/`) to the repo via `../../frontend/...`.

Elements: 62 | BROKEN: 0 | SUSPECT: 1 | NOT PROVEN: 1
