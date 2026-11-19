# Project Design Contract — Brief (Parlament Deschis, frontend)

## Summary (repo-grounded)
- This repository is the **frontend** for **Parlament Deschis** (Romanian parliament openness/transparency project), a public-interest web app that helps people explore parliamentary data (e.g. MPs, parties/groups, activity/metrics as surfaced by the UI). Evidence from repo: `package.json` name `parlament-deschis-frontend`, `index.html` title “Parlament Deschis — transparență parlamentară”, Vite dev proxy to API at `/api` and `/snapshots`, and root project README in the parent repo describes “open, source-cited tracker for the Romanian Parliament…” (Camera Deputaților and Senat).
- Stack context (for design decisions): React 19 + TypeScript + Vite + Tailwind CSS v3 (see `package.json`, `tailwind.config.js`). Global styles in `src/index.css`; app entry `src/main.tsx`.

## Audience
- **Primary (TBD, fill in):** Romanian-speaking citizens, journalists, and civic-tech users who want clear, trustworthy views into parliamentary activity and representation (inferred from product name/positioning; confirm with product owner).
- **Secondary (TBD, fill in):** Researchers/analysts and NGO staff who need quick, readable summaries (not raw dumps) before deeper investigation.
- **Accessibility expectations (TBD, fill in):** Assume WCAG-minded reading (contrast, keyboard navigation, readable type) because the app presents data for public accountability; validate against real users/audits.

## Job-to-be-done
- When a user wants to understand “who represents me / how parties/groups behave / what changed over time” in the Romanian Parliament, they use this site to get **clear, source-aware, easy-to-scan views** so they can form an informed opinion or cite findings—without needing to navigate official chamber sites directly.
- When a user is comparing or verifying information, they need the UI to surface **context and trust signals** (dates, scope, caveats) in plain language (Romanian UI copy is present in page titles/copy patterns seen in the repo context; exact i18n coverage is **TBD**).

## 3 brand adjectives (suggested; confirm with stakeholders)
1. **Trustworthy** — calm, factual presentation; avoid sensational styling.
2. **Clear** — information hierarchy and readable data views over decorative effects.
3. **Civic** — public-service tone; restrained, inclusive, not partisan branding.

## 3 “must not look like…” (suggested; confirm with stakeholders)
1. **A generic SaaS marketing landing page** (no stock-photo hero clichés, no vague “AI startup” gradients as the primary identity).
2. **A partisan campaign site** (no party colors dominating as brand, no emotive propaganda aesthetics).
3. **A cluttered dashboard template with unlabelled charts** (no mystery metrics, no dense UI with no explanation of scope/dates).

## Success criteria
- Users can answer a primary question (e.g. find an MP/group context or interpret a shown metric) within a short session **without confusion about what the numbers mean** (definitions/tooltips or copy where needed) — **measurable via user testing / task success TBD**.
- Visual design remains **consistent with the existing technical stack** (Tailwind v3 + current theme tokens) and does not require new design dependencies unless explicitly approved.
- Key screens pass basic quality checks: responsive layout, readable contrast in the current dark-themed base (`src/index.css`), and no regression to lint/build flows (`npm run lint`, `npm run build`) — see `docs/design/qa-notes.md`.
- Design decisions (colors, type scale, icon/illustration rules) are traceable in `docs/design/stack-choices.md` and `docs/design/tokens.md`.

## Known unknowns (explicit TBDs)
- Exact primary user personas and top tasks (beyond inferences above): **TBD**.
- Brand voice guidelines beyond adjectives: **TBD**.
- Official logo/brand assets and color approvals (if any exist outside repo): **TBD**.
- Full list of supported routes/pages to prioritize in wireframes: **TBD** (derive from `src/` routes when planning).