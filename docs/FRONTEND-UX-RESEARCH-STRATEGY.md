# Frontend UX Improvement Strategy — External Pattern Research (vibeui.online)

**Status:** active reference (Phase G). Every finding must be checked against this document before and after implementation.
**Source:** user directive — investigate https://vibeui.online/ (a UI prompt library with 92 layout prompts across 15 categories) and analyze which elements/patterns could be integrated into parlament-deschis frontend to enhance UX.
**Web-standard source:** Chrome `modern-web-guidance` skill (version `2026_11_09-5bcc021b`), retrieved guides applied to all UI/CSS/client-side JS work.
**Reference:** `docs/FRONTEND-IMPROVEMENT-STRATEGY.md` (Phase F, already written), `docs/REMEDIATION-STRATEGY.md` (remediation baseline).

---

## 1. Non-negotiable principles (inherited + added)

1. **Evidence before edits.** Every finding needs a concrete URL/category/prompt reference from vibeui.online and a code path/line in parlament-deschis frontend where it could apply. No fixing on vibes.
2. **Pattern analysis, not code copying.** vibeui.online is a *prompt library* (text descriptions, not source code). Sub-agents analyze layout structures, layout primitives, and interaction patterns — then translate them into implementable recommendations for the parlament-deschis codebase. Never copy UI verbatim; adapt to the existing dark theme (slate-800 panels, slate-100 text, sky-400 accents).
3. **Smarter alternative before code.** Prefer design-system tokens, existing components, content/layout reorganisation, or config over new code.
4. **Modern web first.** All recommendations follow retrieved `modern-web-guidance` guides.
5. **Non-destructive.** Recommendations target UI layer only; no behaviour regressions without a rollback path.
6. **Honesty.** Document what cannot be integrated and why (e.g., animated video backgrounds may be out of scope for a data-first transparency tool).

## 2. Phase plan and fleet recipes

### G1 — External pattern research (sub-agents)
| Sub-agent | Exclusive ownership (vibeui.online categories) | Recipe focus | Output gate |
|---|---|---|---|
| G1-A | Auth Forms (6), Nav Bars (8), Footer (5) | Login/sign-up layout patterns, nav structures, footer patterns → map to parlament-deschis header/nav/login flows | Findings report w/ evidence (prompt name + pattern) |
| G1-B | Hero Sections (8), CTA Banners (7), Stats Bars (7) | Hero layouts, CTAs, stat displays → map to LiveDashboard hero area, report hero, live-feed stats | Findings report w/ evidence |
| G1-C | Features/Bento (8), Dashboards (6), Stats Bars (7) | Bento grids, dashboard layouts, metric cards → map to dashboard grid, committees, coverage pages | Findings report w/ evidence |
| G1-D | Testimonials (8), FAQ (5), Onboarding (4), Empty States | Onboarding flows, FAQ accordions, empty states → map to empty/loading/error states, about modal, onboarding gaps | Findings report w/ evidence |

### G2 — Integration analysis (implementation research)
| Sub-agent | Exclusive ownership (parlament-deschis files) | Recipe focus | Output gate |
|---|---|---|---|
| G2-A | `frontend/src/pages/LiveDashboard.tsx`, `components/TimeSlider.tsx` | Apply hero/CTA/stats patterns to dashboard hero + time slider area | Integration memo w/ before/after layout description |
| G2-B | `frontend/src/pages/Report.tsx`, `frontend/src/pages/CoverageView.tsx` | Apply bento/stats/footer patterns to report + coverage tables | Integration memo w/ layout description |
| G2-C | `frontend/src/router.tsx`, `components/About.tsx`, pages with empty states | Apply nav/footer/onboarding/empty-state patterns | Integration memo w/ layout description |
| G2-D | `frontend/src/i18n.ts`, `frontend/src/index.css` | Apply typography/color hierarchy patterns from hero/CTA sections | Design token memo |

### G3 — Verify
- `cd frontend && npx tsc -b && npm run build`
- `python3 scripts/ui_validate.py <base>` — target: 18 routes with no console errors and no axe violations. As of 2026-11-19 the production run FAILS on 3 routes (React #310); see `docs/FRONTEND-IMPROVEMENT-STRATEGY.md`.
- Cross-reference every recommended change against `docs/FRONTEND-IMPROVEMENT-STRATEGY.md`

## 3. G1 findings summary (evidence from fleet)

All four sub-agents returned complete reports. vibeui.online category URLs return 404 (client-side filters, not separate routes), but the homepage contains all 92 prompt descriptions inline — all evidence is real, nothing guessed.

| Sub-agent | Categories | ADAPTABLE patterns | OUT_OF_SCOPE |
|---|---|---|---|
| G1-A | Auth Forms, Nav Bars, Footer | Nav bars: minimal logo+links+CTA, command-palette search, sidebar, bottom mobile nav; Footer: multi-column sitemap, minimal single-row, status indicator | Auth forms (no auth exists), mega menu, transparent-over-hero, giant logo, newsletter |
| G1-B | Hero Sections, CTA Banners, Stats Bars | Blocked by 404s; read all 4 target files (LiveDashboard, Report, LiveFeed, CoverageView) | — |
| G1-C | Features/Bento, Dashboards | ft-2 bento grid → LiveDashboard grid; ds-5 metric cards+chart → Report stat grid; ds-3 three-pane → LiveDashboard; ds-6 empty state → CoverageView/Committees | ft-4 tabs, ft-6 scroll reveal, ft-7 icon wall, ft-8 before/after, ds-2 top nav shell, ds-4 kanban |
| G1-D | Testimonials, FAQ, Onboarding | ob-4 illustrated empty state → PersonDeepDive, Report, LiveDashboard; ts-4 featured testimonial → About; fq-1 accordion → About; ob-2 tour tooltips → TimeSlider | marquee scroll, logo cloud, video backgrounds |

## 4. G2 — Integration analysis (implementation research)

| Sub-agent | Exclusive ownership (parlament-deschis files) | Recipe focus | Output gate |
|---|---|---|---|
| G2-A | `frontend/src/pages/LiveDashboard.tsx` | Apply ft-2 bento grid + ds-5 metric cards to dashboard grid; apply ds-6 empty state to coverage fallback; software-kind hero treatment (one section per screen, dealt hero) | Integration memo w/ before/after layout description; tsc + build |
| G2-B | `frontend/src/pages/Report.tsx` | Apply ds-5 metric cards+chart to stat grid (lines 146-168); apply ob-4 illustrated empty state to loading/error states | Integration memo; tsc + build |
| G2-C | `frontend/src/router.tsx`, `components/About.tsx` | Apply nav bar command-palette elevation + sidebar candidate; apply ts-4 featured testimonial + fq-1 accordion to About | Integration memo; tsc + build |
| G2-D | `frontend/src/index.css`, `frontend/src/i18n.ts` | Apply typography/color hierarchy from hero/CTA patterns; add footer status indicator | Design token memo; tsc + build |

## 5. Decision rules
- **Adapt, don't copy:** vibeui.online prompts are text descriptions. Translate into Tailwind classes + React structure consistent with existing codebase.
- **Theme consistency:** All recommendations must work within existing slate/slate-800/slate-100/sky-400 palette — no new colors without a token.
- **Accessibility first:** Any pattern must pass axe (0 violations) — decorative-only patterns (video backgrounds, gradient meshes) are noted as out of scope unless they add information value.
- **Data-first priority:** parlament-deschis is a transparency tool about MPs and party switches. Patterns that improve data scannability (stats bars, bento grids, clear CTAs) are preferred over pure decoration.

## 6. Rollback
- Per-checkpoint commits; `git revert <sha>`.
- Keep pre-change screenshots for visual diff.

## 7. Acceptance
- Each sub-agent returns a findings/integration memo with evidence (vibeui.online prompt name + category + parliament-deschis file:line target).
- G3 gates green before any change is considered "done."

---

*This file is the reference point for the vibeui.online research effort.*
