---
id: CONSOLE-CAPTURES
type: evidence
title: "Fresh console captures for W3/W4/W6 routes — 2026-11-22"
description: "New local-dev console error/warn observations on the integrated repair branch for the three routes whose wave records lacked a dedicated raw capture; explicitly not retroactive wave evidence."
status: active
authority: derived
tags: [type/evidence, lifecycle/active, domain/frontend]
source_paths: [50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md, frontend/src/pages/Voturi.tsx]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Fresh console captures for W3/W4/W6 routes

**Scope.** Wave W10, recipe L-22, closes follow-up F5. These are **new
observations on the integrated `repair/links-base` code**, not the original wave
captures; no GREEN wave record is altered. Local dev only (`127.0.0.1:5188`).

## Browser evidence — raw captures

| Wave-relevant page | URL observed | Raw DOM capture | Raw console capture | Console error/warn |
|---|---|---|---|---|
| W3 (Voturi) | `/Voturi?date=2026-11-22` | `/tmp/opencode/w10-console-w3.json` | `/tmp/opencode/w10-console-w3-console.json` | no console messages found |
| W4 (Topuri) | `/topuri?date=2026-11-22` | `/tmp/opencode/w10-console-w4.json` | `/tmp/opencode/w10-console-w4-console.json` | no console messages found |
| W6 (retry-state area) | `/coverage?date=2026-11-22` | `/tmp/opencode/w10-console-w6.json` | `/tmp/opencode/w10-console-w6-console.json` | no console messages found |

Method: chrome-devtools `list_console_messages` with `types:["error","warn"]`
after each page settled. Each result was also written as a JSON artifact so the
console status is artifact-backed, addressing the W9 supervisor note.

## Code evidence / limits

No product code was changed in W10. These captures do not re-run axe, contrast,
keyboard or network-reachability checks; none of those is claimed. The W6 row
observes the coverage page, not a forced retry-error state, so it closes only
the "raw capture exists" documentation gap, not a retry runtime claim (the W6
retry click was already proven by its own state-probe capture).

## See also

[LINK-FOLLOWUP-WAVE-PLAN](../20-DIRECTION/LINK-FOLLOWUP-WAVE-PLAN-2026-11-22.md) §6 ·
[CLICK-BROWSER-OBSERVATIONS](CLICK-BROWSER-OBSERVATIONS-2026-11-22.md)
