# Frontend Improvement Strategy — UX/UI Deep Audit → 10x

**Status:** active reference (Phase F). Every change made after `2026-11-18` must be checked against this document before and after implementation.
**Source of work:** user directive — deep-hard look at the frontend; screenshot everything; click all buttons; check all UX/UI; find what's missing/broken/incomplete; 10x improve it.
**Web-standard source:** Chrome `modern-web-guidance` skill (version `2026_11_09-5bcc021b`, retrieved via `npx -y modern-web-guidance@latest`), applied to all UI/CSS/client-side JS work.
**Prior context:** `docs/REMEDIATION-STRATEGY.md` (§1–§8, Phase 2.5) — frontend bug fixes already merged (PR #33: TimeSlider play loop, scroll-container a11y, electoral redirect). This strategy now covers *visual/UX improvement* beyond bug fixes.

---

## 1. Non-negotiable principles (inherited + added)

1. **Evidence before edits.** Every finding needs code path + screenshot/interaction evidence. No fixing on vibes.
2. **Deep audit before repair.** Screenshot every route, click every button, probe every state. Findings come from the audit, not from taste.
3. **Smarter alternative before code.** Prefer design-system tokens, existing components, content fixes, removal, or config over new code.
4. **Modern web first.** All UI work follows retrieved `modern-web-guidance` guides.
5. **Non-destructive.** Fixes target UI only; no behaviour regressions without a rollback path.
6. **Honesty.** Document known gaps; never hide broken states.

## 2. What's already done (bug fixes, merged PR #33)
- TimeSlider play loop: was stuck at max, now loops continuously; `aria-pressed` toggles correctly
- Scroll containers keyboard-focusable: party-timeline, coverage, institutional, timeline-chart
- Electoral redirect URL encoding: `legislature=2024` unquoted
- i18n: 0 missing keys, RO/EN parity confirmed
- UI validation: **currently FAILING** against production (re-run 2026-11-19). 3 of 18 routes — `/`, `/party/PSD`, `/person/cb5ca84e-7bba-4d0b-bea8-91b81aa8eb53` — log `Minified React error #310` and 2 moderate axe findings each. This is tracked as P0-1/P0-2 in `docs/REMEDIATION-STRATEGY.md`; the earlier "passing" claim was stale.

## 3. What remains for genuine 10x improvement (visual/UX)

| Area | What to look for | Evidence source |
|---|---|---|
| Visual hierarchy | Spacing, typography scale, color contrast, card/grouping consistency | Screenshot audit + code review |
| Empty states | Pages with no data — do they say something helpful? | Route-by-route click-through |
| Loading states | Suspense fallbacks, query loading — are they visible and useful? | Network-slow simulation + code |
| Error states | Does every fetch have a retry path? Is it visible? | Error simulation + code |
| Mobile UX | Touch targets, readable text, no horizontal scroll | 375px viewport audit |
| Focus management | Visible focus rings, logical tab order, dialog focus trap | Keyboard-only navigation |
| Translations | Copy quality, missing context, RO/EN parity | i18n.ts vs page usage |
| Interactions | Button states (hover/active/disabled), form feedback | Click-through every button |

## 4. Phase plan and fleet recipes

### F1 — Deep visual/UX audit (research only)
Screenshots of all routes at 3 viewports, keyboard-only navigation, copy review.

### F2 — Repair/improve (implementation)
Fix visual hierarchy, empty/loading/error states, mobile issues, focus management, copy.

### F3 — Verify
- `cd frontend && npx tsc -b && npm run build`
- `python3 scripts/ui_validate.py <base>` — target: 18 routes with no console errors and no axe violations. As of 2026-11-19 the production run FAILS on 3 routes (see §2); do not report a pass until P0-1/P0-2 land and the command is re-run.
- Keyboard-only navigation check
- Visual diff against pre-fix screenshots

## 5. Decision rules
- Visual improvements must keep the existing color palette (slate/slate-800 dark theme) — no redesign, just polish.
- No new dependencies unless a modern-web-guidance guide requires one.
- Accessibility violations must be fixed; aesthetic preferences are optional.

## 6. Rollback
- Per-checkpoint commits; `git revert <sha>`.
- Keep pre-fix screenshots for visual diff.

## 7. Acceptance
- Deep audit complete with evidence; improvements implemented only for audited findings; gates green; prod UI scan pass.

---

*This file is the reference point for the frontend improvement effort; reconcile with `docs/REMEDIATION-STRATEGY.md` when phases overlap.*
