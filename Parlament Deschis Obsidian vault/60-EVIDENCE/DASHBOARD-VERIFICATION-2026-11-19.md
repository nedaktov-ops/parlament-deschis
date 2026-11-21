---
id: DASHBOARD-VERIFICATION-2026-11-19
type: evidence
title: "Dashboard implementation verification — 2026-11-19 snapshot (superseded)"
description: "Historical, frozen dashboard verification: raw live-stats response, production build output, the 3/18 React #310 RED UI gate, and the 2026-11-21 addendum on membership drift and scope limits."
status: stale
authority: mirror
tags: [type/evidence, lifecycle/stale, domain/frontend]
source_paths: [docs/DASHBOARD-VERIFICATION.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Dashboard verification — 2026-11-19 (historical snapshot)

> **SUPERSEDED. Do not use this note as a current gate.** This is a frozen
> 2026-11-19 evidence snapshot with a dated 2026-11-21 addendum. The UI gate was
> **RED (3 of 18 routes)** at the time; the current repo gate is the **24-route**
> check with zero JavaScript errors and zero axe violations, mirrored in
> [RELEASE-AND-VERIFICATION](../10-STATE/RELEASE-AND-VERIFICATION.md) and summarised in
> [CURRENT-STATE](../10-STATE/CURRENT-STATE.md). Local green does not prove production green.

**Status as of the snapshot:** evidence snapshot — **not deployment-ready**. A
prior version of the source document declared deployment readiness while its own
checklist was unticked and its production numbers were wrong; that claim is
**withdrawn**. The source's earlier placeholder figures for memberships,
switches, legislatures, parties, cross-chamber and coverage were corrected in
place and are not repeated here.

## 1. Live backend contract (raw response, 2026-11-19)

Command: `curl -s https://parlament-deschis.onrender.com/api/dashboard/stats`

```json
{"status":"ok","data":{"persons":3388,"memberships":7358,"switches":2002,"committees":26,"legislatures":20,"parties":37,"cross_chamber":39,"coverage_score":100,"computed_at":"2026-11-19T08:11:01.098808+00:00"}}
```

`computed_at` is regenerated on every request — the timestamp is not a fixed
value. The release pin is read from `data/latest-release.txt`, not hard-coded;
on 2026-11-19 both hosts served a `dataset.release_tag` equal to that file.
Three distinct, simultaneously valid committee counts: 26 orgs in stats, 23
with active dated memberships from `GET /api/committees`, 9 with a dated chair
from `GET /api/analytics/committee-control`.

## 2. Fresh production build (2026-11-19)

`cd frontend && npm ci && npm run build`; `build` is `tsc -b && vite build`.
Available scripts: `dev`, `build`, `preview`, `lint` — **no test script** (a
former instruction to run one was removed).

```text
vite v5.4.21 building for production...
transforming...
✓ 909 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                              0.49 kB │ gzip:   0.33 kB
dist/assets/index-Dz-NDrWN.css              38.39 kB │ gzip:   7.67 kB
dist/assets/LiveDashboard-GEOsRCsd.js       22.79 kB │ gzip:   5.83 kB
dist/assets/Traseism-G2-u1Mz6.js            71.48 kB │ gzip:  23.64 kB
dist/assets/index-7xwk9fe-.js              409.94 kB │ gzip: 126.33 kB
dist/assets/TimelineChart-C3Vzdrqo.js      487.25 kB │ gzip: 164.22 kB
✓ built in 8.94s
```

20 JS chunks emitted in total. Older hashes/sizes in the source were stale and
withdrawn. Python side, same date: `uv sync --extra dev --locked` then
`uv run pytest -q` → **259 passed, 1 warning in 26.62s** (integration tree with
the gitignored data cache present); `npm run lint` (`tsc --noEmit`) is the
frontend type gate. These are historical counts, superseded by the 2026-11-21
final gate (pytest 384).

## 3. UI validation — RED (2026-11-19)

Command: `python3 scripts/ui_validate.py https://parlament-deschis.vercel.app`
Result: exit 1, `UI VALIDATION FAIL`. 15 routes clean; 3 routes each log one
`console.error` (Minified React error **#310**) and 2 moderate axe findings
(`landmark-one-main`, `page-has-heading-one`).

| Route | Status | JS errors |
|---|---|---:|
| `/` (overview) | FAIL | 1 |
| `/party/PSD` | FAIL | 1 |
| `/person/cb5ca84e-7bba-4d0b-bea8-91b81aa8eb53` | FAIL | 1 |
| other 15 routes | OK | 0 |

Tracked at the time as P0-1 (hook ordering) and P0-2 (error boundary / one `h1`
per route) in `docs/REMEDIATION-STRATEGY.md`. The accessibility checkboxes
stayed unticked: Lighthouse audit and manual staging QA were **not run**;
keyboard-only navigation was not re-verified after the P0 fixes.

## 4. Delivered components (historical inventory)

`DashboardCard`, `PartyListTable`, `PartyNetwork`, `AgeDistributionRadial`,
`SwitchTimeline`, `CommitteeControl`, `CrossChamberFlow`, `DataQualityGauge`,
`TimelineStrip`, `PartyComparisonMatrix`. Component sizes were removed from the
source because the old values were estimates, not measurements.

## 5. Dated addendum — 2026-11-21 (read-only re-verification)

The §1 figures are an accurate 2026-11-19 snapshot. Values verified live on
2026-11-21 (`curl` on `/api/dashboard/stats` and `/api/health`, HTTP 200; pin
read from `data/latest-release.txt`):

| Field | 2026-11-19 | Live 2026-11-21 |
|---|---:|---:|
| `dataset.release_tag` | via pin file | `data-20261117-T213500` |
| `persons` | 3,388 | 3,388 |
| `memberships` | 7,358 | **7,349** |
| `switches` | 2,002 | 2,002 |
| `committees` | 26 | 26 |
| `legislatures` | 20 | 20 |
| `parties` | 37 | 37 |
| `cross_chamber` | 39 | 39 |
| `coverage_score` | 100 | 100 |

Membership count drifted **7,358 → 7,349** (nine duplicate closed stints removed
in database preparation); treat 7,349 as live and 7,358 as historical. The drift
is adjudicated in [CONTRADICTIONS](../10-STATE/CONTRADICTIONS.md), R2.

The §3 RED gate is the **pre-integration** snapshot. The remediation ledger
records those crashes as subsequently fixed, with all 18 then-current routes at
zero JavaScript errors and zero axe violations on the integrated tree. **This
audit could not re-run `scripts/ui_validate.py` (no playwright/chromium here),
so the current UI/axe gate is NOT PROVEN by this document.** Do not read the
addendum as a current PASS claim, and do not treat the historical RED as a
current failure.

**Supersession:** the gate was later widened from 18 to **24 routes**; the
fresh re-run proved 24/24 against a local backend with zero JavaScript errors
and zero axe violations, and 23/24 against the live proxy because the ideology
endpoint 404s in production. That widened gate — not this note — is the current
repo-level evidence. See [QA-AND-AXE](../40-FRONTEND/QA-AND-AXE.md).

## 6. Rollback (historical)

Use a baseline tag with path-scoped checkout — no force-push, no data deletion:
`git checkout pre-remediation-2026-11-19 -- <path-to-restore>`. The former
destructive instructions in the source were removed; current policy is
non-destructive rollback (`git revert` / path checkout).

## See also

[CURRENT-STATE](../10-STATE/CURRENT-STATE.md) · [RELEASE-AND-VERIFICATION](../10-STATE/RELEASE-AND-VERIFICATION.md) · [QA-AND-AXE](../40-FRONTEND/QA-AND-AXE.md) · [AUDIT-2026-11-21](AUDIT-2026-11-21.md) · [SOURCE-MAP](../00-START/SOURCE-MAP.md)
