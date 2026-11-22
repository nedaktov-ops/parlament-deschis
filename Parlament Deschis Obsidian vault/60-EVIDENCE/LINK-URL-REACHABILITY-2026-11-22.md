---
id: LINK-URL-REACHABILITY
type: evidence
title: "External URL reachability probe (2026-11-22)"
description: "Dated HTTP status probe of the literal external URLs used by the front end; closes the F4 follow-up by corroborating the project-URL note claim with a recorded raw capture."
status: active
authority: derived
tags: [type/evidence, lifecycle/active, domain/frontend]
source_paths: [frontend/src/config/links.ts, frontend/src/components/Footer.tsx, frontend/src/components/About.tsx]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# External URL reachability probe

**Scope.** Read-only `curl -L` status probe of the external URL literals in the
front end, executed in wave W8 (recipe L-19) to close follow-up F4. Raw capture:
`/tmp/opencode/w8-url-probe.txt`. All results are a **dated snapshot** at
`2026-11-22T20:49:44Z`, not a guarantee of future reachability.

## Code evidence — probe results

| URL | HTTP status | Effective URL | Interpretation |
|---|---:|---|---|
| `https://github.com/nedaktov-ops/parlament-deschis` | 200 | same | The URL now used by `config/links.ts`, Footer and router is reachable |
| `https://github.com/parlament-deschis` | **404** | same | The former `About.tsx:6` literal was genuinely broken; the L-03 fix was justified |
| `https://github.com/nedaktov-ops/parlament-deschis/blob/main/docs/METHODOLOGY.md` | 200 | same | Methodology link reachable |
| `https://www.wikidata.org/wiki/Q42` | 200 | same | **Host-reachability sample only** — Q42 is not a corpus entity; no data claim |
| `https://www.gnu.org/licenses/agpl-3.0.html` | 200 | same | Code-licence link reachable |
| `https://creativecommons.org/licenses/by/4.0/` | 200 | same | Data-licence link reachable |

Exact probe commands and verbatim output are in the raw capture file above.
Every literal returned a status; no probe was skipped.

## Relationship to the prior note claim

[LINK-REPAIR-STRATEGY](../20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md) §1
recorded the 404/200 observation as a note claim that the supervisor had not
re-run. This probe **corroborates** that claim with a dated raw capture. The
supervisor's caution remains valid as a method rule: a reachability result is
an observation, not a code fact, and any future broken result must become a new
approved recipe (SUPERVISION §E/R7), never an opportunistic edit.

## Browser evidence

Not applicable — this was a network probe, not a browser action. No browser
claim is made.

## Limits

Wikidata Q42 tests host reachability only; data-driven `source_url` /
`snapshot_url` values from API payloads were not probed and remain NOT PROVEN
with resolver "API payload comparison against the live endpoint".

## See also

[CLICK-INV-C06](../40-FRONTEND/CLICK-INV-C06-DESTINATIONS-2026-11-22.md) §3/§7 ·
[LINK-FOLLOWUP-WAVE-PLAN](../20-DIRECTION/LINK-FOLLOWUP-WAVE-PLAN-2026-11-22.md) §3
