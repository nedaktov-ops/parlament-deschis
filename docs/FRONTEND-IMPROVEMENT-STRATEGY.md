# Frontend Improvement Strategy — UX/UI Deep Audit → 10x

**Status:** active reference (Phase F). Every change made after `2026-11-18` must be checked against this document before and after implementation.
**Source of work:** user directive (2026-11-18) — "take a deep hard look at the front-end… screenshot everything, click on all the buttons, check all the ux and UI elements and figure out what is missing, not working, incomplete, forgotten, built incompletely or incorrectly… 10x improve it."
**Web-standard source:** Chrome `modern-web-guidance` skill (retrieved this session; version `2026_11_09-5bcc021b` via `npx -y modern-web-guidance@latest`), applied to all UI/CSS/client-side JS work.
**Prior context:** `docs/REMEDIATION-STRATEGY.md` (§1–§8, Phase 2.5) — this strategy layers a *frontend deep-audit → improvement* effort on top; do not contradict prior remediation decisions without recording why.

---

## 1. Non-negotiable principles (inherited + added)

1. **Evidence before edits.** Every finding needs code path + screenshot/interaction evidence. No fixing on vibes.
2. **Deep audit before repair.** Screenshot every route, click every button, probe every state. Findings come from the audit, not from taste.
3. **Smarter alternative before code.** Prefer design-system tokens, existing components, content fixes, removal, or config over new code.
4. **Modern web first.** All UI work follows retrieved `modern-web-guidance` guides (accessibility, responsive-table, dialog, persistent-toast, etc.).
5. **Non-destructive.** Fixes target UI only; no behaviour regressions without a rollback path.
6. **Honesty.** Document known gaps; never hide broken states.

## 2. Phase plan and fleet recipes

### F1 — Deep frontend audit (research only)
| Sub-agent | Exclusive ownership | Recipe focus | Output gate |
|---|---|---|---|
| F1-A | `frontend/src/**` + dev-server Playwright runs | Visual/UX screenshots of all routes (18), responsive (375/768/1280), states (loading/empty/error), console errors, axe | Findings list w/ evidence |
| F1-B | `frontend/src/i18n.ts` + routed pages | Translation completeness (RO/EN), missing keys, hardcoded strings, locale switching correctness | Key-diff vs usage |

### F2 — Repair (implementation)
| Sub-agent | Exclusive ownership | Findings it fixes |
|---|---|---|
| F2-A | pages + components (visual/responsive/a11y fixes) | layout, spacing, overflow, focus, states |
| F2-B | i18n + copy/content | missing translations, honest copy |

### F3 — Verify
- `cd frontend && npx tsc -b && npm run build`
- `python3 scripts/ui_validate.py <base>` (18 routes, 0 JS errors, 0 axe)
- prod re-scan after deploy.

## 3. Decision rules
- If a finding is a **design/aesthetic** improvement with no accessibility or correctness cost → fix via tokens/components.
- If a finding is **behavioural/UX** but risky → document as residual, don't half-fix.

## 4. Rollback
- Per-checkpoint commits; UI fixes revert via `git revert <sha>`.
- Keep pre-fix screenshots for visual diff.

## 5. Acceptance
- Deep audit complete with evidence; fixes implemented only for audited findings; gates green; prod UI scan pass.

---

*This file is the reference point for the frontend improvement effort; reconcile with `docs/REMEDIATION-STRATEGY.md` when phases overlap.*
