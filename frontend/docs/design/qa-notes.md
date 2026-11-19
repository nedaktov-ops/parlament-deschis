# Project Design Contract — QA notes

Use this file to record design/UX and technical QA passes. Keep entries short, dated, and tied to routes or components.

## Baseline (fill per test session)
- **Date:** 2026-11-19
- **Tester:** NedCode4 agent (automated run)
- **Branch/commit:** a655f98 (from `git rev-parse --short HEAD` in `frontend/`)
- **Environment:** local (npm scripts) — ran `npm run lint` and `npm run build` in `frontend/`
- **Browser(s):** TBD for manual pass
- **Viewport(s):** TBD for manual pass

## Tier A checks (target)
These are the **minimum intended checks** for meaningful UI changes. Automate where possible; otherwise record manual results.

### Automated / command-line (this repo)
Run from `frontend/` (or repo root with appropriate path):

```bash
npm run lint
```
- Notes: `lint` is defined as `tsc --noEmit && eslint src --ext .ts,.tsx` in `package.json`. Record pass/fail and key errors.
- Baseline 2026-11-19 (NedCode4 agent, commit a655f98, env local npm scripts): **PASS (warnings only)**. Command: `npm run lint`. Output summary: `tsc --noEmit` then `eslint src --ext .ts,.tsx` completed with **0 errors, 7 warnings** (react-hooks/exhaustive-deps warnings in `src/components/AgeDistributionRadial.tsx`, `src/components/TimelineChart.tsx`, `src/pages/CoverageView.tsx`, `src/pages/MpComparison.tsx`, `src/pages/PartyTimeline.tsx`).

Build sanity:

```bash
npm run build
```
- Notes: runs `tsc -b && vite build`. Record pass/fail.
- Baseline 2026-11-19 (NedCode4 agent, commit a655f98, env local npm scripts): **PASS**. Command: `npm run build`. Output summary: `tsc -b && vite build` succeeded; Vite built production assets (e.g. dist output generated) in ~9.12s with no build errors.

Optional local preview:

```bash
npm run preview
```
- Notes: manual smoke only unless automated.

### Accessibility (Tier A target)
- **Playwright + axe (axe-core) integration:** **not configured in this repo yet** (TBD). When added, document:
  - how to run (command),
  - which routes are covered,
  - failure thresholds,
  - and link to config files.
- **Manual Tier A (minimum until automated):**
  - Keyboard navigation through primary flows (Tab order, visible focus via `:focus-visible` styles in `src/index.css`).
  - Color contrast spot-checks for text on `ink`/`panel` and status colors defined in tokens.
  - Zoom/reflow sanity at 200% where practical.

### Responsive / layout
- Check key routes at mobile, tablet, desktop widths (list routes tested in Notes).
- Verify no horizontal overflow on small screens for main content areas (`.wrap` usage).

### Content & trust (Parlament Deschis context)
- Spot-check that data-adjacent UI states show clear loading/empty/error behavior where applicable (TBD per route).
- Verify dates/scopes/caveats are visible where the product promises transparency (TBD per feature).

## Notes
| Date | Area/route | What was tested | Commands run | Result (pass/fail/TBD) | Follow-ups |
|---|---|---|---|---|---|
| 2026-11-19 | repo-wide (frontend) | Baseline automated checks: TypeScript + ESLint lint; production build (tsc -b + Vite). | `npm run lint`; `npm run build` | lint: pass with warnings (0 errors, 7 warnings); build: pass | Address lint warnings when convenient (react-hooks deps/exhaustive-deps noted in commands output). |
| 2026-11-20 | `/mps` (pilot Phase 5) | UI/UX pass (standout loop): controls toolbar grouped (subtle panel + better focus/hover on submit); cards more scannable (larger name, link-hover + focus ring, spacing/border tweaks); loading/error/empty styled (meaning unchanged). Data integrity guardrails respected (no data fetching/logic/meaning changes). Wireframe note: `docs/design/wireframes/2026-11-20_mps_pilot_lofi.md`. | `npm run lint`; `npm run build` | lint: pass (0 errors, 7 warnings, same set as baseline); build: pass (vite build OK) | Manual chrome-devtools checks (390/768/1024/1440), keyboard/focus + contrast spot checks on `/mps` (and quick `/`, `/person/$id` sanity) — record text refs in this file. |
| 2026-11-20 | `/` (LiveDashboard, Phase 6 Section 1) | Scoped to Hero + top stats band only (Sections 2–3 untouched). Presentation: stronger hero hierarchy (larger h1, intro leading/width), adjusted spacing rhythm, legislature moment emphasis with top border spacing. No data fetching/API/query/date logic/meaning changes; no i18n edits. Wireframe note: `docs/design/wireframes/2026-11-20_livedashboard_section1_pilot_lofi.md`. | `npm run lint`; `npm run build` | lint: pass (0 errors, 7 warnings, same baseline set); build: pass (vite build OK) | Manual chrome-devtools checks on `/` at 390/768/1024/1440 + quick sanity `/mps`, `/person/$id`; record text refs here. |
| 2026-11-20 | `/` (LiveDashboard, Phase 6.1 Section 2 header+top row) | Scoped to Section 2 “Party Ecosystem”: header typography/spacing + section padding rhythm; top-row grid gaps and `lg:items-start`. No changes to PartyListTable/CommitteeControl/DataQualityGauge components, no data fetching/API/query/date logic/meaning/caveat changes, no i18n edits. | `npm run lint`; `npm run build` | lint: pass (0 errors, 7 warnings, same baseline set); build: pass (vite build OK) | Manual chrome-devtools checks on `/` (390/768/1024/1440) focusing Section 2 stack/alignment, empty/loading states still readable; quick sanity `/mps` if desired. Record text refs here. |
| 2026-11-20 | `/` (LiveDashboard, Phase 6.2 Section 3 header+grid) | Scoped to Section 3 “Deep Dive Views”: header typography/spacing + section padding rhythm; grid gap tweak (`lg:gap-5`). No changes to chart/widget components or data logic, no i18n edits. | `npm run lint`; `npm run build` | lint: pass (0 errors, 7 warnings, same baseline set); build: pass (vite build OK) | Manual chrome-devtools checks on `/` (390/768/1024/1440) focusing Section 3 layout/wrapping; quick sanity interactions not required unless visual issues suspected. Record text refs here. |
| 2026-11-20 | `/traseism` (Phase 7 Scope & Context panel) | Scoped to Scope panel only: improved heading hierarchy/spacing, label styling, control grouping/gaps, period styling; added `btn-hover`, minor responsive tweaks (aria-labelledby on heading). No route/search/derived-legislature/setScope changes, no data fetching/API/query/metric/coverage logic changes, no i18n text changes. | `npm run lint`; `npm run build` | lint: pass (0 errors, 7 warnings, same baseline set); build: pass (vite build OK) | Manual chrome-devtools checks at 390/768/1024/1440 on example URL (`?date=2026-11-19&chamber=deputies&legislature=2024`) + alt `chamber=senate`; verify chamber/select behavior unchanged, keyboard focus, no overflow, break-ui notes in this file. |
| 2026-11-20 | `/traseism` (Phase 7b Hero + stats band) | Presentation-only: removed forced full-height hero, improved heading/intro hierarchy and spacing, stats grid gaps, added moment border/spacing. No data fetching/API/query/logic/meaning changes. | `npm run lint`; `npm run build` | lint: pass (0 errors, 7 warnings, same baseline set); build: pass (vite build OK) | Manual chrome-devtools checks at 390/768/1024/1440 (hero layout, no overflow); quick sanity with example URL. Record notes in this file. |
| 2026-11-20 | `/traseism` (Phase 7c Stats grids spacing) | Presentation-only: adjusted gaps on the two StatCard grids after coverage for better rhythm. No data/logic changes. | `npm run lint`; `npm run build` | lint: pass (0 errors, 7 warnings, same baseline set); build: pass (vite build OK) | Quick visual check at breakpoints if desired; no behavior changes. |
| 2026-11-20 | `/report` (Phase 8 header + hero band) | Scoped to header/hero band in Report.tsx: restructured layout (no full-height), improved hierarchy/spacing/wrapping, moment emphasis with border, print class tweaks kept intent. No data fetching/API/query/logic/meaning/caveat changes; no i18n key changes. Wireframe note: `docs/design/wireframes/2026-11-20_report_header_hero_lofi.md`. | `npm run lint`; `npm run build` | lint: pass (0 errors, 7 warnings, same baseline set); build: pass (vite build OK) | Manual checks 390/768/1024/1440 + quick print preview; sanity with referenced URL (`?date=2026-11-19&chamber=deputies&legislature=2024`, ignored params) — record notes here. |
| 2026-11-20 | `/report` (Phase 8b Corpus card spacing) | Presentation-only: spacing/padding tweaks in first “Corpus at a glance” card (heading rhythm, grid gaps). No data/logic changes. | `npm run lint`; `npm run build` | lint: pass (0 errors, 7 warnings, same baseline set); build: pass (vite build OK) | Quick visual check; no behavior changes. |
| 2026-11-20 | `/report` (Phase 8c Middle/third card rhythm) | Presentation-only: heading/spacing rhythm tweaks in committee/waves and ages cards (padding, gaps, heading tracking/margins). No data/logic changes. | `npm run lint`; `npm run build` | lint: pass (0 errors, 7 warnings, same baseline set); build: pass (vite build OK) | Quick visual check; no behavior changes. |

## Open items
- Add Playwright + axe to devDependencies and CI when ready; update this file with exact commands.