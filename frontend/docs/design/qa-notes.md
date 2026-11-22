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

## QA pass — 2026-11-22 — Hero brand mark, Concept A "Amfiteatrul deschis"
- **Branch:** `design/hero-brand-mark` (repo `/home/nedaktov/parlament-deschis`); worktree had uncommitted edits to `frontend/src/components/HeroGraphic.tsx`, `frontend/docs/design/asset-manifest.md`, `frontend/docs/design/stack-choices.md`, plus new `frontend/docs/design/wireframes/2026-11-22_hero-brand-mark.md`.
- **Tester:** NedCode QA subagent (read-only browser pass; only this file written).
- **Environment:** Vite dev server at `http://127.0.0.1:5188/` (HMR active). `curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:5188/` → `HTTP 200`. Browser: chrome-devtools MCP via the `execute` tool (no standalone browser tool). Page navigated to `http://127.0.0.1:5188/` → app settled at `http://127.0.0.1:5188/?date=2026-11-22`; page title "Prezentare generală — Parlament Deschis". Viewports tested: 1440×900 and 390×844.
- **Scope:** `HeroGraphic` `variant="overview"` SVG only, as rendered in the hero of `LiveDashboard` (`frontend/src/pages/LiveDashboard.tsx:182`), i.e. the "Prezentare generală" page. No other variants were exercised.
- **Source/docs read (shell `read`/`grep`/`sed`):** `frontend/src/components/HeroGraphic.tsx`; `frontend/src/components/ui/ThemeToggle.tsx`; `frontend/src/pages/LiveDashboard.tsx` (lines 160–200); `frontend/src/router.tsx`; `frontend/src/i18n.ts`; `frontend/index.html`; `frontend/src/index.css`; `frontend/docs/design/{brief,tokens,stack-choices,qa-notes}.md`; `frontend/docs/design/wireframes/2026-11-22_hero-brand-mark.md`.

### Exact tools / commands run
- `shell`: `pwd`, `ls -la`, `find … -name HeroGraphic.tsx`, `git branch --show-current`, `git status --short`, `grep -rn "HeroGraphic\|Schimbă tema\|0.1\|opacity" …`, `sed -n '160,200p' frontend/src/pages/LiveDashboard.tsx`, `curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:5188/`, `mkdir -p /tmp/opencode`.
- `chrome-devtools` MCP via `execute`: `list_pages`; `navigate_page({type:"url", url:"http://127.0.0.1:5188/"})`; `take_snapshot`; `evaluate_script` (SVG DOM/geometry extraction, theme recheck, 48px temporary width set + restore, overflow checks, final a11y recheck); `take_screenshot` (`uid:"4_83"` and viewport shots); `click` (`uid:"4_57"` theme toggle, twice); `list_console_messages` (with and without `includePreservedMessages`); `resize_page({width:390,height:844})` (**ineffective** — emulated viewport stayed 1440×900); `emulate({viewport:"390x844"})` and `emulate({viewport:"1440x900"})` (effective).
- `shell` + Python PIL: cropped/upscaled the 48px screenshot to `/tmp/opencode/logo-dark-48-zoom.png` for legibility inspection.
- **No git state-changing commands run. No app code or kit files edited.**

### DOM / SVG evidence (dark theme, 1440×900, current navigation)
- Wrapper: `<div role="img" aria-label="Parliament Deschis" class="flex flex-col items-center justify-center gap-4 text-center mx-auto">`.
- `<svg width="200" height="200" viewBox="0 0 200 200" fill="none" class="w-full max-w-[200px] h-auto text-sky-400">`.
- `svg.getBBox()` → `{x:36, y:86, w:128, h:70}` (visual extent y=86…156). Outer arc path `M36 150 A64 64 0 0 1 164 150` has bbox `{x:36, y:86, w:128, h:64}` → apex at **y=86**, i.e. **above** the centre line y=150. This is direct browser geometry proof the arcs render as an **upper** semicircle (sweep=1, not inverted). Middle arc bbox y=100…150; inner arc bbox y=116.01…149.99.
- Broken floor: `M36 150 L90 150` (bbox x 36→90) and `M110 150 L164 150` (bbox x 110→164) → **20-unit open-door gap x=90…110**. Doorway posts: `M90 144 L90 156` and `M110 144 L110 156`.
- 7 `<circle>` elements at (54,131), (65,115), (81,104), (100,100), (119,104), (135,115), (146,131); measured distances from (100,150) are 49.5–50.0 units → **all sit on the r=50 middle arc**. Apex dot opacity `0.7`, other six `0.55`.
- 7 `<path>` elements, all `stroke="currentColor"`; all `<circle>` `fill="currentColor"`; `textCount=0`.

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Upper semicircle, visible door gap, 7 dots on arc | **PASS** | SVG bbox y=86…156 with arc apex at y=86 (above y=150); floor paths leave x=90…110 gap; 7 circles at 49.5–50.0 units from centre. Screenshots `logo-dark-200.png`, `hero-390-viewport.png`, `hero-1440-viewport.png` visually confirm the hemicycle and bottom gap. |
| 2 | Accent-colour inheritance dark → light | **PASS** | Dark: svg computed `color: rgb(56, 189, 248)` (= `#38bdf8`, Tailwind sky-400) with `data-theme="dark"`. After clicking `Schimbă tema de culori` (uid 4_57): `data-theme="light"`, svg computed `color: rgb(3, 105, 161)` (= `#0369a1`); computed `stroke` of first path and `fill` of apex circle also `rgb(3, 105, 161)`. Cause located in `src/index.css:91-92`: `html[data-theme="light"] .text-sky-300, html[data-theme="light"] .text-sky-400 { color: #0369a1; }`. Toggle `aria-pressed` flips to `true`; body bg `rgb(248, 250, 252)`. Screenshots `logo-dark-200.png` / `logo-light-200.png`. |
| 3 | Legibility at 200px and ~48px | **PASS** | At 200px the mark is clear. `evaluate_script` temporarily set `svg.style` to `width:48px; height:48px` → `getBoundingClientRect()` `{w:48,h:48}`; screenshot `logo-dark-48.png` (zoom `logo-dark-48-zoom.png`) still shows three nested arcs, the seven dots and the open-door gap — silhouette reads, though faint because of the 0.25–0.55 opacity band. Inline style then removed; rect restored to 200×200 and `getAttribute('style') === null`. **No code change persisted.** |
| 4 | Accessibility | **PASS** | Exactly one `[role="img"][aria-label="Parliament Deschis"]` wrapper; `focusableInsideWrapper=0`; `svgTextElements=0`; SVG children tags: 7×`path`, 7×`circle` only; no new interactive element. A11y snapshot shows one `image "Parliament Deschis"` and the single theme toggle button. Current-navigation console (3 messages): 2× `[vite] connecting/connected` debug, 1× React DevTools info — **0 errors, 0 warnings**. (Historical preserved messages from *before* this navigation contained 2 HMR errors about `SwitchTimeline.tsx` 500/failed reload — not from this page load and unrelated to `HeroGraphic`; reported for honesty, not attributed to this change.) |
| 5 | Responsive 390px / 1440px | **PASS** | 390×844: `innerWidth=390`, `scrollWidth=390=clientWidth` → no horizontal overflow; SVG rect x=95…295 (200px), fully inside viewport; screenshot `hero-390-viewport.png` shows centred, unclipped mark. 1440×900: `scrollWidth=1440=clientWidth`, SVG rect x=986.3…1186.3, fully inside viewport; screenshot `hero-1440-viewport.png`. Note: `resize_page` did not change the emulated viewport; `emulate({viewport:...})` was used and verified via `window.innerWidth`. |
| 6 | Apex dot 0.7 vs documented 0.1–0.6 opacity ladder | **OPEN — recommend normalise to 0.6** | Observed: apex `opacity="0.7"`, all other painted elements 0.25–0.55 (within the band). The wireframe `2026-11-22_hero-brand-mark.md:28` itself flags 0.7 as intentionally outside the "0.1–0.6 band stated in the brief's hard-constraint wording" and asks for parent/reviewer confirmation. I could **not** find that hard-constraint wording in `frontend/docs/design/brief.md` or anywhere else in-tree — the only in-repo mention is the wireframe's own note, so I cannot confirm it is a binding rule. Visually the mark reads equally well at 200px and 48px; the brighter apex is not needed for legibility. **Recommendation:** normalise the single apex value from `0.7` to `0.6` (one-attribute change) unless the parent explicitly wants the emphasis; this resolves the open item with negligible visual effect. |

### Screenshot paths (all under `/tmp/opencode/`)
- `logo-dark-200.png` — hero mark wrapper, dark theme, 200px (uid 4_83).
- `logo-light-200.png` — same after theme toggle, light theme, 200px.
- `logo-dark-48.png` — dark theme, SVG temporarily set to 48px.
- `logo-dark-48-zoom.png` — 6× nearest-neighbour crop of the 48px render for legibility inspection.
- `hero-390-viewport.png` — 390×844 viewport, hero scrolled into view.
- `hero-1440-viewport.png` — 1440×900 viewport, hero scrolled into view.

### What I could not check / limitations
- Dev server + HMR only; no production build, no `npm run lint` / `npm run build` in this pass (not run — no claim made about them).
- No axe/Lighthouse automated accessibility scan; no keyboard tab-order walk beyond counting focusable elements inside the wrapper.
- Only Chromium via chrome-devtools MCP; no cross-browser check; no 768/1024 breakpoints (only the two requested widths).
- Could not verify an authoritative source for the "0.1–0.6" hard constraint (see check 6); the parent/reviewer decision is still required.
- `resize_page` was attempted but did not alter the emulated viewport; viewport evidence relies on `emulate()` + `window.innerWidth` verification.

### Issues / recommendations
1. **(resolved) Apex dot opacity normalised 0.7 → 0.6** after the pass, to sit inside the documented 0.1–0.6 band; the wireframe was updated in the same change. No rendering impact expected (0.1 difference); the before-screenshot remains as evidence of the reviewed version.
2. Historical HMR errors for `SwitchTimeline.tsx` appear only in preserved console history from before this navigation; not reproduced on a fresh load. No action attributed to this change.
3. No functional, visual, a11y or responsive defect observed in the Concept A mark itself.

**VERDICT: PASS** — all six verification targets were observed in-browser; checks 1–5 pass with DOM/SVG and screenshot evidence. Check 6 is an open, non-blocking contract question with a recommendation to normalise the apex opacity to 0.6; it is not a rendering failure.

### Placement pass — 2026-11-22 — header mark (right-click comment)

- **Instruction received:** "Move the logo on the left side of the 'Parlament Deschis' text in the header" (right-click comment from the VS Code preview, relayed by the user).
- Implemented via shared `BrandMark.tsx`, rendered in `router.tsx` header before the title as a 36px `aria-hidden` SVG.
- Browser evidence (chrome-devtools at 1440px): header first child class `flex-1 flex items-center gap-3`; SVG rect x=16 w=36; title rect x=64; `svgLeftOfTitle: true`; title text `Parlament Deschis`; hero mark still present.
- Screenshot: `/tmp/opencode/header-logo-left-vscode.png`.
- `npm run lint` and `npm run build` both exit 0 after the change.
- Verdict: PASS. Open question for the owner: the hero illustration was deliberately kept, so the mark now appears in both the header and the hero — confirm whether "move" meant relocate (remove the hero instance) or duplicate.

### Backend logo store + hero removal — 2026-11-22

- Added `backend/logo_store.py` and `backend/routers/logo.py`; read-only corpus DB untouched. Logo files live in `data/assets/logos/` (gitignored) with a JSON index, atomic writes, MIME/size validation and SVG sanitisation.
- `GET /api/logo` served the seeded SVG with HTTP 200, `image/svg+xml`, 1380 bytes.
- Frontend: removed `<HeroGraphic variant="overview">` from the LiveDashboard hero; the four stat cards now span the full width. Header uses `HeaderLogo`, which renders `<img src="/api/logo">` with an inline `BrandMark` fallback.
- Browser evidence (chrome-devtools at 5188): header `img[src="/api/logo"]` complete with `naturalWidth=150`, rendered width 36px; `path[d^="M36 150"]` count 0 outside the header; hero caption absent. Screenshot: `/tmp/opencode/backend-logo-header.png`.
- `pytest tests/test_logo_store.py` → 3 passed; `ruff check` clean; `npm run lint` exit 0.

### Logo contrast fix — 2026-11-22

- Problem captured: `/tmp/opencode/logo-contrast-before.png` — the header SVG loaded via `<img src="/api/logo">` used `currentColor`, which resolves to black inside an image document, so the mark was nearly invisible on the dark header.
- Root cause: CSS `color` on the `<img>` does not inherit into an externally loaded SVG.
- Fix: `/api/logo?color=…` injects a validated hex on the SVG root; `HeaderLogo` sends `#38bdf8` in dark mode (8.33:1 on `#0f172a`) and `#0369a1` in light mode (5.67:1 on `#f8fafc`), and observes `data-theme` changes. Served opacities are lifted to >=0.55 for 40px legibility. The stored SVG is unchanged.
- Evidence: `/tmp/opencode/logo-contrast-final-dark.png`, `/tmp/opencode/logo-contrast-final-light.png`; DOM probe showed src switching `%2338bdf8` → `%230369a1` → `%2338bdf8` with `data-theme`.
- `pytest tests/test_logo_store.py` → 3 passed; ruff, lint and build clean.
