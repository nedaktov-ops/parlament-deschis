# /mps (MP directory) — Phase 5 pilot wireframe notes (lo-fi, text)

Date: 2026-11-20  
Context: React + Vite + Tailwind (parlament-deschis/frontend). Civic/info site — no shader/scene effects. Focus: standout via clarity/hierarchy, controls toolbar clarity, card scannability, clear states. Data integrity: no changes to data fetching/meaning; only presentation and clearer (truthful) microcopy allowed.

## Layout blocks (intended)
- **Hero/intro block (top):** page title + short intro paragraph + small hero graphic (right on md+). Stats row (4 cards: Total MPs, With party, With committees, Total switches) — values are from current page/query context in existing UI (note: current implementation shows counts derived from loaded rows; do not reinterpret semantics).
- **Emphasis line (existing):** large number + label “members of parliament in corpus” (keep meaning).
- **Controls toolbar (primary focus):** search input + sort select + submit button. Goal: clear grouping, responsive (stack on small screens, align on larger), obvious labels, good focus styles. Avoid changing query/sort behavior.
- **Results:** loading / error / empty states clearly shown. Grid of MP cards (name link, badges: party/age/switches/committees). Goal: scannable hierarchy (name prominent, badges grouped/readable), consistent spacing.
- **Pagination:** Previous / offset indicator / Next. Keep behavior; improve clarity only if wording stays truthful (avoid implying more than offset marker shows).
- **Coverage note (footer of page section):** keep text as-is in meaning (data sources/caveats) — do not remove or weaken caveats.

## Responsive notes
- 390px: single-column cards, toolbar stacks vertically, stats grid readable (2 cols in current layout is fine; verify no overflow).
- 768px+: 2-col cards, toolbar can be row; stats 4-col on md+ as now.
- 1024/1440: 3-col cards on lg; generous spacing, no cramped controls.

## States to verify (break-ui mindset)
- Loading, error, empty (no results), long MP names, null party/age, high switches/committees counts, many results with pagination.

## Out of scope
- Router, API, data model, adding deps/UI kit, broad redesign of other pages.