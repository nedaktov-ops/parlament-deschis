---
id: DESIGN-CONTRACT
type: reference
title: "Design contract — Parlament Deschis frontend"
description: "Mirrored design contract: audience, job-to-be-done, brand adjectives, anti-patterns, success criteria and open TBDs for the public-interest parliamentary dashboard."
status: stale
authority: mirror
tags: [type/reference, lifecycle/stale, domain/frontend]
source_paths: [frontend/docs/design/brief.md, docs/DASHBOARD-STRATEGY.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Design contract — frontend

> **Mirror, not a decision record.** This note projects
> `frontend/docs/design/brief.md`. The `stale` status records that the brief
> itself still carries open TBDs (audience, brand voice, assets, route
> priorities); do not treat an inferred answer as an approved one. Stack
> decisions that *are* locked live in [STACK-AND-TOKENS](STACK-AND-TOKENS.md).

## Scope and audience

The app is the frontend for **Parlament Deschis**, a public-interest web app
that helps people explore Romanian parliamentary data (Camera Deputaților and
Senat): MPs, parties and groups, and activity metrics as surfaced by the UI.
Repo evidence: `package.json` name `parlament-deschis-frontend`, `index.html`
title "Parlament Deschis — transparență parlamentară", and a Vite dev proxy to
the API at `/api` and `/snapshots`.

- **Primary audience — TBD.** Inferred: Romanian-speaking citizens,
  journalists and civic-tech users who want clear, trustworthy views of
  parliamentary activity and representation. Confirm with the product owner.
- **Secondary audience — TBD.** Inferred: researchers, analysts and NGO staff
  who need a readable summary before deeper investigation.
- **Accessibility expectations — TBD.** Assume WCAG-minded reading (contrast,
  keyboard navigation, readable type) because the app supports public
  accountability; validate with real users and audits rather than assertion.

## Job-to-be-done

1. When a user wants to understand "who represents me / how parties and groups
   behave / what changed over time", the site should give **clear,
   source-aware, easy-to-scan views** so they can form an informed opinion or
   cite a finding — without navigating the official chamber sites directly.
2. When comparing or verifying information, the UI must surface **context and
   trust signals** (dates, scope, caveats, source links) in plain language.
   Romanian UI copy is present in page titles and copy patterns; exact i18n
   coverage is **TBD**.

## Three brand adjectives (proposed; stakeholder confirmation pending)

1. **Trustworthy** — calm, factual presentation; no sensational styling.
2. **Clear** — information hierarchy and readable data views before decorative
   effects.
3. **Civic** — public-service tone; restrained, inclusive, never partisan.

## Anti-patterns — what this must not look like

1. **A generic SaaS marketing landing page** — no stock-photo hero clichés and
   no vague "AI startup" gradients as the primary identity.
2. **A partisan campaign site** — no party colours dominating the brand, no
   emotive propaganda aesthetics.
3. **A cluttered, unexplained dashboard template** — no chart without labels,
   scope, dates or definitions; no mystery metrics.

## Success criteria

- A user can answer a primary question (find an MP/group context, interpret a
  shown metric) in a short session **without confusion about what the numbers
  mean**, with definitions or tooltips where needed. Measurement via user
  testing / task success is **TBD**.
- Visual design stays consistent with the existing stack (Tailwind v3 and the
  current theme tokens) and introduces no new design dependency without
  explicit approval — see [STACK-AND-TOKENS](STACK-AND-TOKENS.md).
- Key screens pass basic quality checks: responsive layout, readable contrast
  in the current dark-themed base, and no regression to `npm run lint` or
  `npm run build`. Observed results and their limits are in
  [QA-AND-AXE](QA-AND-AXE.md).
- Design decisions (colour, type scale, icon and illustration rules) remain
  traceable in `stack-choices.md` and `tokens.md` in the source repo.

## Known unknowns

- Exact primary personas and top tasks beyond the inferences above: **TBD**.
- Brand voice guidelines beyond the three adjectives: **TBD**.
- Official logo/brand assets and colour approvals outside the repo: **TBD**.
- Full route/page priority list for wireframes: **TBD** (derive from `src/`
  routes when planning).
- Votes and biographies are not in the published corpus, so a "clear,
  source-aware view" of how an MP voted cannot yet be built against production
  data. See [SOURCE-RESEARCH](../50-RESEARCH/SOURCE-RESEARCH.md).
