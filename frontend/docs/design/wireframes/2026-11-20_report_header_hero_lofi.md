# /report (Transparency Report) — Phase 8 header + hero band (lo-fi, text)

Date: 2026-11-20  
Context: React + Vite + Tailwind (parlament-deschis/frontend). Civic/report page. Focus: standout via hierarchy/spacing/print clarity in header band only. Data integrity: no changes to data fetching, API, query, normalization, or meaning/caveats; presentation only. No i18n key changes planned (CSS/wrapping first).

## In scope (header + hero band)
- Top strip: title, subtitle, generated timestamp, moment block (`d.totals.persons` + label), action buttons (Print/Save PDF, Download JSON), `HeroGraphic variant="report"` placement.
- Print behavior: keep `print:hidden` on actions/hero and existing print text classes unless a minimal legibility tweak is approved; do not remove generated context.

## Out of scope
- All report sections below (totals grid tables, waves, ages, coverage tables), charts logic, fetch/query logic, routes/search validation beyond noting referenced URL has extra params ignored.
- Global tokens/CSS/Tailwind config changes (unless explicitly approved).
- Any hiding of caveats/coverage meaning.

## Hierarchy/spatial goals
- Clear title → subtitle → generated → moment → actions rhythm; avoid cramped wrapping on narrow widths.
- Hero aligned sensibly with text block (stack on small screens, side-by-side on wider when space allows) without pushing actions awkwardly.
- “Moment” number remains prominent but does not overflow at 390px; timestamp wraps cleanly under locale length differences.
- Buttons: consistent focus, wrap gracefully; tap targets comfortable.

## Responsive notes
- 390px: single column feel, actions wrap or stack if needed, hero below or after text block as appropriate, no horizontal overflow.
- 768px: comfortable spacing; consider row layout for text/actions vs hero.
- 1024/1440: balanced two-column header if space allows; generous padding.

## States/break-ui
- Loading/error states: only layout tweaks if they affect header-adjacent area? Prefer not to touch; note if any overlap.
- Long translated strings (subtitle/footer/meta): verify wrapping.

## Evidence
- Manual checks 390/768/1024/1440 + quick print preview; record in `docs/design/qa-notes.md` with commands `npm run lint`, `npm run build`.