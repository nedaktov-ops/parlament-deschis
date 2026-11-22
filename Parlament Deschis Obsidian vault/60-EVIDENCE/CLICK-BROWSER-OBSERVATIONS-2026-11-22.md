---
id: CLICK-BROWSER-OBSERVATIONS
type: evidence
title: "Browser observations for the clickable investigation (2026-11-22)"
description: "Supplementary runtime observations from the local dev page and the Vercel page; code evidence remains authoritative and each observation names its scope and limits."
status: active
authority: derived
tags: [type/evidence, lifecycle/active, domain/frontend]
source_paths: [frontend/src/router.tsx, frontend/src/pages/Ideology.tsx, frontend/src/components/Footer.tsx]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Browser observations — clickable investigation

**Scope and authority.** These are runtime observations made this session with
the VS Code preview browser (Chrome DevTools protocol), on the local dev page
`http://127.0.0.1:5188` and the Vercel page
`https://parlament-deschis.vercel.app`. They are **supplementary**: per
[MAINTENANCE-PROTOCOL](../00-START/MAINTENANCE-PROTOCOL.md) §1, executable code
source outranks runtime prose. Each row states what was actually observed and
what was **NOT PROVEN**. Raw captures are at
`/tmp/opencode/click-inv-local-dom.json`, `/tmp/opencode/click-inv-prod-dom.json`,
`/tmp/opencode/click-inv-prod-overview.png` (outside the vault; not committed).

## B1 — clickable-element counts (observed, data-dependent)

| Page | URL observed | Clickable nodes matched by `a[href],button,[role=button],input,select,textarea,[tabindex]:not([tabindex="-1"]),form` |
|---|---|---:|
| Local overview | `http://127.0.0.1:5188/?date=2026-11-22` | 611 |
| Vercel overview | `https://parlament-deschis.vercel.app/?date=2026-11-22` | 604 |

The first 26 clipboard-level anchors match in both captures (same `href`
strings, including the duplicate `/mps` stat cards). Observed text differs:
local overview shows "Parlamentari 3,388 / Mandate 4,461"; Vercel shows
"Parlamentari 3,381 / Mandate 4,401". This is a **data/parity observation**,
not a link defect. Why the corpora differ is **NOT PROVEN** (resolver: compare
the dataset release pinned in each deployment).

## B2 — SPA nav link click (observed, corroborates code)

On the local page, the first-nav `Traseism` link had
`href="/traseism?date=2026-11-22&legislature=2024"`. A `window.__marker` value
survived the click, the URL became
`http://127.0.0.1:5188/traseism?date=2026-11-22&legislature=2024`, the title
became "Traseism — Parlament Deschis", and `aria-current="page"` moved to the
Traseism link. Browser console: no errors or warnings at that moment. This
supports the code-level conclusion that `NavLink` performs client-side
navigation and preserves scope.

**Discarded false lead, recorded for honesty:** an earlier programmatic click
made while the viewport was being emulated appeared to leave the router on `/`
with an added `legislature=2024`. A clean repeat from a settled page did not
reproduce it; direct navigation to `/traseism?date=2026-11-22` also rendered
"Traseism — Parlament Deschis". No defect is claimed from the first attempt.

## B3 — footer in-app anchors cause a full document navigation (observed)

On the Vercel page, a `window.__footerMarker` was set, then the footer anchor
with `href="/"` was clicked. The script's execution context was destroyed
(`Execution context was destroyed, most likely because of a navigation`), and a
follow-up evaluation found `marker: null` and URL
`https://parlament-deschis.vercel.app/?date=2026-11-22`. This corroborates the
code-level SUSPECT in [C-01](../40-FRONTEND/CLICK-INV-C01-SHELL-2026-11-22.md)
and [C-06](../40-FRONTEND/CLICK-INV-C06-DESTINATIONS-2026-11-22.md): the footer
uses native `<a href>` (Footer.tsx:65/73/81/123) rather than the router
`<Link>` (router.tsx:110-118). The exact mechanism that re-adds `date` after the
reload is **NOT PROVEN** by this observation.

## B4 — Ideology "All years" control (observed, corroborates BROKEN finding)

Local page `http://127.0.0.1:5188/ideology?date=2026-11-22`. The year `<select>`
offered options `""` ("Toți anii"), 2024, 2019, 2014, 2010, 2006, 2002; initial
value was `2024`. After setting the select to `""` and dispatching a `change`
event: URL unchanged (`...&date=2026-11-22`), select value snapped back to
`2024`, and the rendered table still showed six rows all with `YEAR 2024`
while the counter read "6 parties in 6 wave(s)". This corroborates the
code-level chain in [C-04](../40-FRONTEND/CLICK-INV-C04-VOTES-2026-11-22.md):
`Ideology.tsx:250` maps `""` → `undefined`, `:80` substitutes `years[0]`, and
`:84` filters to that single year.

On the Vercel page the same route rendered "Se încarcă…" with **zero** `<select>`
elements, so the production behaviour of this control is **NOT PROVEN**;
resolver: a loaded production ideology response.

## B5 — limits

No axe/WCAG measurement, keyboard-only traversal, 320 px reflow, network
reachability of external URLs, or click-through of every one of the 258
inventoried elements was performed. Such claims remain **NOT PROVEN** and are
not used to upgrade any verdict in the master report.

## See also

[CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) ·
[CLICK-INVESTIGATION-JOURNEY](../50-RESEARCH/CLICK-INVESTIGATION-JOURNEY-2026-11-22.md)
