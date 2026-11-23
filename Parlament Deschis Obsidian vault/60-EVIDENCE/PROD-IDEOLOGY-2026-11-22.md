---
id: PROD-IDEOLOGY
type: evidence
title: "Production /ideology observation — 2026-11-22 (NOT PROVEN)"
description: "Second production attempt to load the ideology year control; the page still shows a loading state with zero selects, so the B1 repair's production effect remains NOT PROVEN with a named resolver."
status: active
authority: derived
tags: [type/evidence, lifecycle/active, domain/frontend]
source_paths: [frontend/src/pages/Ideology.tsx, 60-EVIDENCE/CLICK-BROWSER-OBSERVATIONS-2026-11-22.md]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Production `/ideology` observation

**Scope.** Wave W9 (recipe L-20) retried the production ideology page to close
follow-up F3. Raw capture: `/tmp/opencode/w9-prod-ideology.json`. Production host
was taken from the existing vault evidence, not guessed. No code, deploy,
release-pin or production-config change was made.

## Code evidence

- Anchor re-read: [CLICK-BROWSER-OBSERVATIONS](CLICK-BROWSER-OBSERVATIONS-2026-11-22.md) B4
  recorded the same loading state with zero selects in the earlier session.
- W1 of [LINK-REPAIR-JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md)
  proved the B1 fix only on local dev (`chesYear=all`, 38 rows / 6 years).
- Entry identity and verified backup for W9 are recorded in that journey note.

## Browser evidence (production scope)

`https://parlament-deschis.vercel.app/ideology?date=2026-11-22`, waited 5 s:
title "Ideologie — Parlament Deschis", `<select>` count **0**, options empty,
`loading: true`, body text contains "Harta ideologică Se încarcă…". Console
error/warn list: no console messages found. The year control therefore could
not be re-tested in production, and the "All years" fix's production effect is
**NOT PROVEN**.

**Resolver:** a loaded production ideology response plus deployment metadata
identifying the served SHA. Then repeat the select test from W1.

No defect is opened from this observation: a loading state is not proof of a
broken endpoint, and a production defect would require a new recipe plus an
owner decision. This note does not change any GREEN wave verdict.

## See also

[LINK-FOLLOWUP-WAVE-PLAN](../20-DIRECTION/LINK-FOLLOWUP-WAVE-PLAN-2026-11-22.md) §4 ·
[CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) §6
