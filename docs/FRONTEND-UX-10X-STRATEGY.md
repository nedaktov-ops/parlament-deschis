# Frontend UX/UI 10x Strategy — Parliament Deschis

**Status:** Active reference document (Phase H). All changes must be checked against this document before and after implementation.
**Created:** 2026-11-18
**Foundation:** Builds on completed H1 (design tokens, HeroGraphic, InfoStat, DataViz) and H2 (hero transformations on 10 pages).
**Inspiration sources:** awwwards.com (award-winning design patterns), vibeui.online (component recipes)
**Design framework:** design-taste-frontend (tasteskill 2.5)
**Project kind:** software / transparency data portal — dark theme, sharp radius, one effect allowed, 1-2 moments per page
**Branch:** fix/frontend-ux-10x-vision
**Deploy target:** PR → squash-merge to main → production deploy

---

## 1. Project Identity (Rule 1)

| Field | Value |
|-------|-------|
| page type | software |
| site-kind | software |
| kind | software |
| What is sold | Transparent parliamentary data — MPs, party switches, committee control, loyalty scores |
| Who buys it | Journalists, researchers, citizens, activists |
| One main action | Explore the data: switch waves, loyalty scores, MP biographies, committee control |
| Real material | 3388 persons, 7358 memberships, 7429 events, 142 waves, 26 committees |

`<html data-type="software" data-radius="sharp" data-buttons="solid|tonal" data-motion>` and `<meta name="page-type" content="software">` and `<meta name="site-kind" content="software">` must be present on every page.

**Radius: sharp** (design-taste-frontend: sharp for fintech and developer tools).  
**No violet or lavender** (design-taste-frontend Rule 6 "Never").  
**No stock photographs** — SVG illustrations only.  
**No fake data** — all figures must come from real corpus data.

---

## 2. What's Wrong — Evidence-Based Audit Findings

### Boring / Generic (design-taste-frontend: "looks like an art piece / template")

| # | Issue | Evidence |
|---|-------|----------|
| B1 | All pages use identical `card p-4` styling | Every page uses `bg-slate-800 rounded-xl border border-slate-700/60 shadow-lg` — no visual hierarchy |
| B2 | No hero graphics on 6 pages | SenateHistory, Demographics, Coalitions, Committees, MpComparison, PersonDeepDive lack HeroGraphic |
| B3 | No per-tab information graphics | Every nav tab has identical typography treatment |
| B4 | Empty states are plain text | `text-slate-500` with no illustration or CTA |
| B5 | Loading states are plain spinners | No illustrated loading states |
| B6 | Error states are plain text | No illustrated error states with retry context |
| B7 | Tables lack visual polish | Plain tables with no row striping, no accent cells, no mini-charts |
| B8 | No visual distinction between card types | All cards look identical regardless of content type |
| B9 | Buttons lack consistent hover states | Some buttons have hover, some don't; no consistent press state |
| B10 | Footer is minimal | Only copyright + status, no newsletter, no social proof, no resource links |

### Broken / Missing

| # | Issue | Evidence |
|---|-------|----------|
| M1 | ElectoralDynamics.tsx is an empty stub | References exist but component is empty |
| M2 | CurrentLegislatureView missing | Referenced in router but not built |
| M3 | DefectionSankey variants missing | Referenced but not built |
| M4 | No consistent section headers | Every section uses raw `<h2>` without decorative treatment |
| M5 | No divider elements between sections | Sections run together visually |
| M6 | Mobile overflow on tables | Several tables overflow on 375px width |
| M7 | Table rows missing hover on some pages | Inconsistent hover states across tables |
| M8 | No "data entry" animation on some pages | Some pages lack `data-enter` |

### Redundant

| # | Issue | Evidence |
|---|-------|----------|
| R1 | Duplicate stat card patterns | Report.tsx, LiveDashboard.tsx both build stat cards independently |
| R2 | Duplicate timing logic | `localISODate()` imported in 5+ pages |
| R3 | Duplicate error handling | ErrorState component exists but not used consistently |
| R4 | Duplicate chart wrappers | Sparkline usage inconsistent across pages |

---

## 3. Design System — Palette & Tokens

Keep existing slate/slate-800/slate-100/sky-400 base (proven, accessible). Add:

| Token | Usage |
|-------|-------|
| `--color-accent` | sky-400 (#38bdf8) — primary actions |
| `--color-accent-hover` | sky-300 (#22d3ee) |
| `--color-success` | emerald-400 (#22c55e) — full coverage, active status |
| `--color-warning` | amber-400 (#f59e0b) — partial coverage, warnings |
| `--color-danger` | rose-400 (#fb7185) — errors, failures |
| `--color-info` | slate-400 (#64748b) — neutral info |
| `--bg-hero` | bg-slate-900/80 — hero section background |
| `--bg-surface` | rgba(30, 41, 59, 0.5) — surface layer |
| `--radius` | sharp (0.25rem) — per design-taste-frontend |

---

## 4. Phase Plan & Fleet Recipes

Each recipe is written for one subagent with **exclusive file ownership**. Agents run in parallel only on disjoint files. Every agent prompt must include: project path, "READ current code before editing", the exact file list, the specific root cause from the audit, the guide quote that applies, the verification command, and "report evidence, no claims".

### Phase I — Visual Design System (foundation)

| ID | Fleet recipe | Files | Gate |
|----|-------------|-------|------|
| H1-A | Design tokens + hero CSS | `frontend/src/index.css` | tsc + build |
| H1-B | Hero graphic component | `frontend/src/components/HeroGraphic.tsx` | tsc + build |
| H1-C | InfoStat component | `frontend/src/components/InfoStat.tsx` | tsc + build |
| H1-D | DataViz primitives | `frontend/src/components/DataViz.tsx` | tsc + build |

*(Phases H1-A through H1-D are COMPLETE — see completed work below)*

### Phase II — Page-by-page hero transformation

| ID | Fleet recipe | Files | Gate |
|----|-------------|-------|------|
| H2-A | LiveDashboard hero | `frontend/src/pages/LiveDashboard.tsx` | ui_validate 18/0/0 |
| H2-B | Report hero | `frontend/src/pages/Report.tsx` | ui_validate 18/0/0 |
| H2-C | Traseism hero | `frontend/src/pages/Traseism.tsx` | ui_validate 18/0/0 |
| H2-D | SwitchLeaderboard hero | `frontend/src/pages/SwitchLeaderboard.tsx` | ui_validate 18/0/0 |
| H2-E | Demographics hero | `frontend/src/pages/Demographics.tsx` | ui_validate 18/0/0 |
| H2-F | Committees hero | `frontend/src/pages/Committees.tsx` | ui_validate 18/0/0 |
| H2-G | Coalitions hero | `frontend/src/pages/Coalitions.tsx` | ui_validate 18/0/0 |
| H2-H | Mps hero | `frontend/src/pages/Mps.tsx` | ui_validate 18/0/0 |
| H2-I | MpComparison hero | `frontend/src/pages/MpComparison.tsx` | ui_validate 18/0/0 |
| H2-J | PartyProfile hero | `frontend/src/pages/PartyProfile.tsx` | ui_validate 18/0/0 |
| H2-K | PersonDeepDive hero | `frontend/src/pages/PersonDeepDive.tsx` | ui_validate 18/0/0 |
| H2-L | LegislatureDetail hero | `frontend/src/pages/LegislatureDetail.tsx` | ui_validate 18/0/0 |
| H2-M | InstitutionalView hero | `frontend/src/pages/InstitutionalView.tsx` | ui_validate 18/0/0 |
| H2-N | CoverageView hero | `frontend/src/pages/CoverageView.tsx` | ui_validate 18/0/0 |
| H2-O | PartyTimeline hero | `frontend/src/pages/PartyTimeline.tsx` | ui_validate 18/0/0 |
| H2-P | SenateHistory hero | `frontend/src/pages/SenateHistory.tsx` | ui_validate 18/0/0 |

*(Phases H2-A through H2-P are COMPLETE — see completed work below)*

### Phase III — Empty states, loading, error states

| ID | Fleet recipe | Files | Gate |
|----|-------------|-------|------|
| H3-A | Illustrated empty state component | `frontend/src/components/EmptyState.tsx` (new) | tsc + build |
| H3-B | Illustrated loading state component | `frontend/src/components/LoadingState.tsx` (new) | tsc + build |
| H3-C | Illustrated error state component | `frontend/src/components/ErrorState.tsx` (new) | tsc + build |
| H3-D | Apply to all pages | All pages with `isLoading`/`isError`/`length === 0` | ui_validate 18/0/0 |

### Phase IV — Footer & header polish

| ID | Fleet recipe | Files | Gate |
|----|-------------|-------|------|
| H4-A | Footer — social proof, newsletter, better hierarchy | `frontend/src/components/Footer.tsx` | ui_validate 18/0/0 |
| H4-B | Header — brand mark, better nav, command palette elevation | `frontend/src/router.tsx` (RootLayout) | ui_validate 18/0/0 |

### Phase V — Dead code removal

| ID | Fleet recipe | Files | Gate |
|----|-------------|-------|------|
| H5-A | Remove ElectoralDynamics.tsx | `frontend/src/pages/ElectoralDynamics.tsx` | tsc + build |
| H5-B | Remove DefectionSankey stubs | `frontend/src/components/DefectionSankey*.tsx` | tsc + build |
| H5-C | Remove CurrentLegislatureView stub | `frontend/src/components/CurrentLegislatureView.tsx` | tsc + build |
| H5-D | Update router.tsx to remove dead route references | `frontend/src/router.tsx` | tsc + build |

### Phase VI — Verify & ship

| ID | Fleet recipe | Files | Gate |
|----|-------------|-------|------|
| H6-A | Full verification loop | All | ruff, pytest 259, tsc, build, ui_validate, CI green |

---

## 4. Detailed Recipes (exclusive ownership)

### H1-A — Design tokens + hero CSS (COMPLETE)
File: `frontend/src/index.css`
**Status:** DONE — Added CSS custom properties: `--color-accent`, `--color-accent-hover`, `--color-success`, `--color-warning`, `--color-danger`, `--color-info`, `--bg-hero`, `--bg-surface`. Added utility classes: `.hero-gradient`, `.stat-card`, `.info-graphic`, `.hero-section`, `.data-bar`, `.data-bar-fill`, `.sparkline`, `.moment-badge`. Verified: tsc OK, build OK.

### H1-B — HeroGraphic component (COMPLETE)
File: `frontend/src/components/HeroGraphic.tsx`
**Status:** DONE — Variants: overview, switches, committee, people, wave, report. SVG-only, no external dependencies, WCAG AA contrast, respects prefers-reduced-motion.

### H1-C — InfoStat component (COMPLETE)
File: `frontend/src/components/InfoStat.tsx`
**Status:** DONE — Props: label, value, max, barValue, accent, showBar, showTrend. Uses existing `.card-hover` and `.data-bar` classes. WCAG AA contrast verified.

### H1-D — DataViz primitives (COMPLETE)
File: `frontend/src/components/DataViz.tsx`
**Status:** DONE — Sparkline, DataBar, ProgressRing, StatBadge. All SVG-only, no external dependencies, respect prefers-reduced-motion.

### H2-A — LiveDashboard hero (COMPLETE)
File: `frontend/src/pages/LiveDashboard.tsx`
**Status:** DONE — HeroGraphic variant="overview", InfoStat cards (4), min-h-screen data-enter hero, dealt moment with legislature count.

### H2-B — Report hero (COMPLETE)
File: `frontend/src/pages/Report.tsx`
**Status:** DONE — HeroGraphic variant="report", InfoStat cards with barValue, Sparkline for waves and ages, ProgressRing for coverage, ProgressRing for coverage completeness.

### H2-C — Traseism hero (COMPLETE)
File: `frontend/src/pages/Traseism.tsx`
**Status:** DONE — HeroGraphic variant="switches", InfoStat cards (4), Sparkline wave timeline, dealt moment.

### H2-D — SwitchLeaderboard hero (COMPLETE)
File: `frontend/src/pages/SwitchLeaderboard.tsx`
**Status:** DONE — HeroGraphic variant="switches", InfoStat cards (3), dealt moment, existing table row hover retained.

### H2-E — Demographics hero (COMPLETE)
File: `frontend/src/pages/Demographics.tsx`
**Status:** DONE — HeroGraphic variant="people", InfoStat cards (4), Sparkline age distribution, ProgressRing coverage.

### H2-F — Committees hero (COMPLETE)
File: `frontend/src/pages/Committees.tsx`
**Status:** DONE — HeroGraphic variant="committee", InfoStat cards (3), dealt moment.

### H2-G — Coalitions hero (COMPLETE)
File: `frontend/src/pages/Coalitions.tsx`
**Status:** DONE — HeroGraphic variant="wave", InfoStat cards (4), Sparkline wave timeline, dealt moment.

### H2-H — Mps hero (COMPLETE)
File: `frontend/src/pages/Mps.tsx`
**Status:** DONE — HeroGraphic variant="people", InfoStat cards (4), Dealt moment.

### H2-I — MpComparison hero (COMPLETE)
File: `frontend/src/pages/MpComparison.tsx`
**Status:** DONE — HeroGraphic variant="people", InfoStat cards (3), dealt moment.

### H2-J — PartyProfile hero (COMPLETE)
File: `frontend/src/pages/PartyProfile.tsx`
**Status:** DONE — HeroGraphic variant="committee", InfoStat cards (4), Sparkline switch timeline, dealt moment.

### H2-K — PersonDeepDive hero (COMPLETE)
File: `frontend/src/pages/PersonDeepDive.tsx`
**Status:** DONE — HeroGraphic variant="people", InfoStat cards (4), Sparkline event timeline, dealt moment.

### H2-L — LegislatureDetail hero (COMPLETE)
File: `frontend/src/pages/LegislatureDetail.tsx`
**Status:** DONE — HeroGraphic variant="wave", InfoStat cards (4), Dealt moment.

### H2-M — InstitutionalView hero (COMPLETE)
File: `frontend/src/pages/InstitutionalView.tsx`
**Status:** DONE — HeroGraphic variant="committee", InfoStat cards (4), Dealt moment.

### H2-N — CoverageView hero (COMPLETE)
File: `frontend/src/pages/CoverageView.tsx`
**Status:** DONE — HeroGraphic variant="overview", InfoStat cards (4), ProgressRing overall coverage, Dealt moment.

### H2-O — PartyTimeline hero (COMPLETE)
File: `frontend/src/pages/PartyTimeline.tsx`
**Status:** DONE — HeroGraphic variant="wave", InfoStat cards (4), Sparkline party count timeline, Dealt moment.

### H2-P — SenateHistory hero (COMPLETE)
File: `frontend/src/pages/SenateHistory.tsx`
**Status:** DONE — HeroGraphic variant="people", InfoStat cards (4), Dealt moment.

### H3-A — Illustrated empty state component (PENDING)
File: `frontend/src/components/EmptyState.tsx` (new)
**Recipe:**
1. Create `EmptyState` component accepting `icon`, `title`, `description`, `ctaLabel`, `onCta` props
2. SVG illustration (document/chart icon) — centered, `py-12`
3. Centered layout with max-width constraint
4. Accepts optional CTA button
5. Export `EmptyState` default export
6. Wire into all pages that show empty states (see H3-D)

**Gate:** `npx tsc -b` passes, `npm run build` passes

### H3-B — Illustrated loading state component (PENDING)
File: `frontend/src/components/LoadingState.tsx` (new)
**Recipe:**
1. Create `LoadingState` component accepting `label`, `description`, `retryLabel`, `onRetry` props
2. SVG spinner — centered, `py-12`
3. Centered layout with max-width constraint
4. Optional retry button
5. Export `LoadingState` default export

**Gate:** `npx tsc -b` passes, `npm run build` passes

### H3-C — Illustrated error state component (PENDING)
File: `frontend/src/components/ErrorState.tsx` (new)
**Recipe:**
1. Create `ErrorState` component accepting `message`, `onRetry` props
2. SVG alert icon — centered, `py-12`
3. Centered layout with max-width constraint
4. Retry button
5. `role="alert"`
6. Export `ErrorState` default export

**Gate:** `npx tsc -b` passes, `npm run build` passes

### H3-D — Apply to all pages (PENDING)
Files: All pages with `isLoading`/`isError`/`length === 0`
**Recipe:**
1. Replace plain text loading states with `<LoadingState>`
2. Replace plain text error states with `<ErrorState>`
3. Replace plain text empty states with `<EmptyState>`
4. Keep all existing functionality (retry buttons, refetch, etc.)

**Gate:** `ui_validate.py 18/0/0`

### H4-A — Footer polish (PENDING)
File: `frontend/src/components/Footer.tsx`
**Recipe:**
1. Add newsletter signup section
2. Add social proof (logos or "trusted by" text)
3. Enhance link hierarchy with better typography
4. Add "last updated" timestamp
5. Keep status indicator (already good)

**Gate:** `ui_validate.py 18/0/0`

### H4-B — Header polish (PENDING)
File: `frontend/src/router.tsx` (RootLayout)
**Recipe:**
1. Enhance brand mark (logo + tagline)
2. Add command palette elevation (search already exists, make more prominent)
3. Add user/account placeholder
4. Enhance nav link styling with hover states

**Gate:** `ui_validate.py 18/0/0`

### H5-A — Delete dead code (PENDING)
Files: `frontend/src/pages/ElectoralDynamics.tsx`, `frontend/src/components/DefectionSankey*.tsx`, `frontend/src/components/CurrentLegislatureView.tsx`
**Recipe:**
1. Delete confirmed-dead modules (0 importers)
2. Update router.tsx to remove references to deleted routes
3. Remove unused imports

**Gate:** `npx tsc -b` passes, `npm run build` passes

---

## 5. Completed Work Summary

**Phases H1-H2 fully complete (16 phases, 16 PRs):**

| Phase | PR | Files | Status |
|-------|-----|-------|--------|
| H1-A | #31 | `index.css` | Merged |
| H1-B | #31 | `HeroGraphic.tsx` | Merged |
| H1-C | #31 | `InfoStat.tsx` | Merged |
| H1-D | #31 | `DataViz.tsx` | Merged |
| H2-A | #32 | `LiveDashboard.tsx` | Merged |
| H2-B | #33 | `Report.tsx` | Merged |
| H2-C | #34 | `Traseism.tsx` | Merged |
| H2-D | #35 | `SwitchLeaderboard.tsx` | Merged |
| H2-E | #35 | `Demographics.tsx` | Merged |
| H2-F | #36 | `Committees.tsx` | Merged |
| H2-G | #36 | `Coalitions.tsx` | Merged |
| H2-H | #37 | `Mps.tsx` | Merged |
| H2-I | #38 | `MpComparison.tsx` | Merged |
| H2-J | #39 | `PartyProfile.tsx` | Merged |
| H2-K | #40 | `PersonDeepDive.tsx` | Merged |
| H2-L | #41 | `LegislatureDetail.tsx` | Merged |
| H2-M | #42 | `InstitutionalView.tsx` | Merged |
| H2-N | #43 | `CoverageView.tsx` | Merged |
| H2-O | #44 | `PartyTimeline.tsx` | Merged |
| H2-P | #45 | `SenateHistory.tsx` | Merged |

**Final verification (post-merge on `main @ 93af684`):**
- ruff: All checks passed
- pytest: 259 passed
- tsc + build: Built OK
- LiveFeed guard: PASS
- ui_validate (dev + prod): 18 routes / 0 JS errors / 0 axe violations
- Production `/api/health`: OK, release `data-20261117-T213500`
- Post-merge CI: Success (test/audit/docker/evidence-guards)

---

## 5. Detailed Recipe — H3-A EmptyState Component

**Files:** `frontend/src/components/EmptyState.tsx` (new)

**Task:**
Create `EmptyState` component accepting `icon`, `title`, `description`, `ctaLabel`, `onCta` props:

```tsx
export interface EmptyStateProps {
  icon: React.ReactNode;      // SVG icon
  title: string;              // Heading text
  description: string;        // Supporting text
  ctaLabel?: string;          // Optional button label
  onCta?: () => void;         // Optional button handler
  className?: string;         // Optional CSS class
}
```

**Structure:**
- Outer div: centered layout with max-width constraint, `py-12`
- SVG illustration: `aria-hidden="true"`, appropriate color
- Title: `text-lg font-semibold text-slate-200`
- Description: `text-sm text-slate-400 text-center max-w-xs`
- Optional CTA button: uses existing `.btn` class, `mt-4`
- All text centered

**Rules:**
- No new dependencies
- SVG only, no bitmap images
- Accessible: `aria-hidden="true"` on decorative SVG
- Respect `prefers-reduced-motion` (static SVG)
- WCAG AA contrast

**Verify:**
- `cd frontend && npx tsc -b` (must pass)
- `npm run build` (must pass)

**Report:** Component structure, props interface, verification outputs, rollback (git revert), residual. Max 400 words.

---

## 6. Detailed Recipe — H3-B LoadingState Component

**Files:** `frontend/src/components/LoadingState.tsx` (new)

**Task:**
Create `LoadingState` component accepting `label`, `description`, `retryLabel`, `onRetry` props:

```tsx
export interface LoadingStateProps {
  label?: string;
  description?: string;
  retryLabel?: string;
  onRetry?: () => void;
}
```

**Structure:**
- Outer div: centered layout with max-width constraint, `py-12`
- SVG spinner: `aria-hidden="true"`, `role="status"`
- Title: `text-sm font-semibold text-slate-200`
- Description: `text-xs text-slate-400 text-center max-w-xs`
- Optional retry button: uses existing `.btn` class, `mt-4`
- All text centered

**Rules:**
- No new dependencies
- SVG only
- Accessible: `aria-hidden="true"` on decorative SVG
- Respect `prefers-reduced-motion`
- WCAG AA contrast

**Verify:**
- `cd frontend && npx tsc -b` (must pass)
- `npm run build` (must pass)

**Report:** Component structure, props interface, verification outputs, rollback (git revert), residual. Max 400 words.

---

## 7. Detailed Recipe — H3-C ErrorState Component

**Files:** `frontend/src/components/ErrorState.tsx` (new)

**Task:**
Create `ErrorState` component accepting `message`, `onRetry` props:

```tsx
export interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}
```

**Structure:**
- Outer div: centered layout with max-width constraint, `py-12`
- SVG alert icon: `aria-hidden="true"`, `role="alert"`
- Title: `text-sm font-semibold text-slate-200`
- Description: `text-xs text-slate-400 text-center max-w-xs`
- Optional retry button: uses existing `.btn` class, `mt-4`
- All text centered
- `role="alert"` on outer div

**Rules:**
- No new dependencies
- SVG only
- Accessible: `aria-hidden="true"` on decorative SVG, `role="alert"` on outer div
- Respect `prefers-reduced-motion`
- WCAG AA contrast

**Verify:**
- `cd frontend && npx tsc -b` (must pass)
- `npm run build` (must pass)

**Report:** Component structure, props interface, verification outputs, rollback (git revert), residual. Max 400 words.

---

## 8. Detailed Recipe — H3-D Apply to all pages

**Files:** All pages with `isLoading`/`isError`/`length === 0`

**Recipe:**
1. Replace plain text loading states with `<LoadingState>`
2. Replace plain text error states with `<ErrorState>`
3. Replace plain text empty states with `<EmptyState>`
4. Keep all existing functionality (retry buttons, refetch, etc.)

**Verify:**
- `ui_validate.py 18/0/0`

**Report:** Per page change — path:line changed, verification outputs, rollback (git revert), residual. Max 400 words.

---

## 7. Decision Rules (from strategy)

- **Adapt, don't copy:** vibeui.online prompts are text descriptions. Translate into Tailwind classes + React structure consistent with existing codebase.
- **Theme consistency:** All recommendations must work within existing slate/slate-800/slate-100/sky-400 palette — no new colors without a token.
- **Accessibility first:** Any pattern must pass axe (0 violations) — decorative-only patterns (video backgrounds, gradient meshes) are noted as out of scope unless they add information value.
- **Data-first priority:** parlament-deschis is a transparency tool about MPs and party switches. Patterns that improve data scannability (stats bars, bento grids, clear CTAs) are preferred over pure decoration.
- **No violet or lavender** (design-taste-frontend Rule 6 "Never").
- **No stock photographs passed off as real** — use SVG illustrations only.
- **One section per screen** — hero alone on first screen, every section 1-2 screens tall.
- **Equal edges** — `.wrap` on every page.
- **Hover micro-animations** — cards lift 2px, buttons shadow + scale, links underline draw.

---

## 8. Rollback Matrix

| Change type | Rollback |
|------------|----------|
| Code commit | `git revert <checkpoint-sha>` |
| Component deletion | `git revert <checkpoint-sha>` |
| Config change | `git revert <checkpoint-sha>` |

---

## 9. Acceptance Criteria (final gate)

Before any change is considered "done":

1. `uv run ruff check pipeline backend scripts tests` — clean
2. `uv run pytest tests/ -q` — 259 passed
3. `cd frontend && npx tsc -b` — exit 0
4. `cd frontend && npm run build` — exit 0
5. `python3 scripts/ui_validate.py http://127.0.0.1:5175` — 18 routes, 0 JS errors, 0 axe violations
6. Production `/api/health` — ok
7. Post-merge CI (test/audit/docker/evidence-guards) — green

---

*This document is the reference point for the frontend 10x transformation. Reconcile with `docs/REMEDIATION-STRATEGY.md` when phases overlap.*
