# / (LiveDashboard) — Phase 6 pilot wireframe notes (lo-fi, text), Section 1 only

Date: 2026-11-20  
Context: React + Vite + Tailwind (parlament-deschis/frontend). Civic/info site — no shader/scene effects. Focus: standout via clarity/hierarchy, spacing rhythm, typography in hero+stats band. Data integrity: no changes to data fetching/API/query/date logic/interpretation or hiding caveats/dates/scopes; presentation only. No i18n changes in this pilot.

## In scope (Section 1: Hero + Top Stats band)
- `h1` + intro paragraph (`dashboardIntro`) block.
- Four `DashboardCard` links: Current MPs (`/mps`), Party Switches (`/mps`), Switch Waves (`/traseism`), Committee Control (`/committees`) (labels/values from existing i18n + query results; do not reinterpret).
- `HeroGraphic variant="overview"` placement and visual balance with text/cards.
- Legislature “moment” line (text + link to `/legislature/...`) — keep meaning and link behavior.

## Out of scope
- Sections 2–3 (PartyNetwork, SwitchTimeline, CrossChamberFlow, tables/widgets), charts/data widget internals and logic.
- Any data fetching, API, query keys/params, caching, date parsing/logic changes beyond not touching code.
- Router changes, new deps, broad global CSS/Tailwind token changes, i18n file edits (unless explicitly approved later).
- Hiding/removing caveats/dates/scopes if present.

## Layout/hierarchy goals (standout)
- Clear visual hierarchy: hero title larger/stronger, intro readable width, stats cards scannable as a group.
- Improved spacing rhythm between hero row and stats row; consistent vertical gaps.
- On small screens: stack cleanly (text first, graphic below or alongside per existing pattern), cards 1–2 cols as before unless small presentational tweak is necessary; avoid overflow.
- Preserve existing link destinations and semantics.

## Responsive notes
- 390px: single column stacking, cards readable, no horizontal overflow.
- 768px: comfortable 2-col cards; hero can be two-column if already present.
- 1024/1440: 4-col stat cards row as now; generous spacing, balanced hero.

## States/break-ui to consider (Section 1)
- Long `dashboardIntro` text (i18n) wraps gracefully.
- Legislature “moment” missing/empty states already handled in page — do not change logic; only styling if safe.
- Card values show `--` or loading placeholders from existing behavior — keep.

## Evidence plan
- Manual `chrome-devtools` MCP on `/` at 390/768/1024/1440 + quick sanity `/mps`, `/person/$id` if any shared styles touched (likely not). Record text refs in target `docs/design/qa-notes.md`.
- Run `npm run lint` and `npm run build` after edits.