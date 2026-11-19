# Dashboard Implementation Verification Report

**Date:** 2026-11-19
**Status:** Evidence snapshot — **NOT deployment-ready**. The production UI
validation gate is RED (3 of 18 routes crash with React #310). A prior version
of this document declared deployment readiness while its own checklist was
unticked and its production numbers were wrong; that claim is withdrawn.

All numbers below come from commands re-run on 2026-11-19. Raw outputs are quoted
so the figures can be re-checked rather than trusted.

---

## 1. Live backend contract

Command:

```bash
curl -s https://parlament-deschis.onrender.com/api/dashboard/stats
```

Raw response (2026-11-19):

```json
{"status":"ok","data":{"persons":3388,"memberships":7358,"switches":2002,"committees":26,"legislatures":20,"parties":37,"cross_chamber":39,"coverage_score":100,"computed_at":"2026-11-19T08:11:01.098808+00:00"}}
```

| Field | Live value | Previous (wrong) value in this document |
|---|---:|---:|
| `persons` | 3388 | 3388 (correct) |
| `memberships` | 7358 | 12445 |
| `switches` | 2002 | 7429 |
| `committees` | 26 | 26 (correct, all committee organisations) |
| `legislatures` | 20 | 10 |
| `parties` | 37 | 62 |
| `cross_chamber` | 39 | 461 |
| `coverage_score` | 100 | 85 |
| `computed_at` | `2026-11-19T08:11:01.098808+00:00` | `2026-11-19T00:00:00Z` (placeholder) |

`computed_at` is regenerated on every request; do not treat the timestamp above
as a fixed value. The release tag is pinned in `data/latest-release.txt` — read
that file instead of hard-coding a tag here. On 2026-11-19 both hosts served a
`dataset.release_tag` equal to the value in `data/latest-release.txt` (verified
with `jq -e` against the live `/api/health` response).

Note the three distinct, simultaneously valid committee counts: `/api/dashboard/stats`
counts 26 committee organisations in the corpus, `GET /api/committees` returns 23
with active dated memberships, and `GET /api/analytics/committee-control` returns
9 with a dated chair. See `docs/API.md`.

---

## 2. Fresh production build

Commands (from the repository root):

```bash
cd frontend && npm ci && npm run build
```

`package.json` defines `build` as `tsc -b && vite build`. The available scripts
are `dev`, `build`, `preview` and `lint` — there is no test script. The former
instruction to run a non-existent script was removed from this document.

Raw build output (2026-11-19, exit 0):

```
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

(20 JS chunks were emitted in total; the full output is reproducible with the
command above.) The former "910 modules / 6.13s / `LiveDashboard-Dh0NPS6p.js` /
`index-CuO-B1Hr.js` / `TimelineChart-DkHdqrGq.js"` figures were stale hashes and
sizes and are withdrawn.

Python side, same date:

```bash
uv sync --extra dev --locked
uv run pytest -q
```

Result: `259 passed, 1 warning in 26.62s` (integration tree with the gitignored
data cache present). `npm run lint` (`tsc --noEmit`) is the frontend type gate.

---

## 3. UI validation — RED

Command:

```bash
python3 scripts/ui_validate.py https://parlament-deschis.vercel.app
```

Result: exit 1, `UI VALIDATION FAIL`. 15 routes are clean; 3 routes each log one
`console.error` (`Minified React error #310`) and 2 moderate axe findings
(`landmark-one-main`, `page-has-heading-one`):

| Route | Status | JS errors |
|---|---|---:|
| `/` (overview) | FAIL | 1 |
| `/party/PSD` | FAIL | 1 |
| `/person/cb5ca84e-7bba-4d0b-bea8-91b81aa8eb53` | FAIL | 1 |
| other 15 routes | OK | 0 |

Consequence: the accessibility and UI checkboxes below stay unticked. Fixes are
tracked as P0-1 (hook ordering) and P0-2 (error boundary / one `h1` per route)
in `docs/REMEDIATION-STRATEGY.md`. Re-run the validator after those land; do not
copy a PASS from an earlier report.

---

## 4. Components delivered (historical inventory)

| Component | Purpose |
|---|---|
| `DashboardCard.tsx` | Clickable stat cards with color variants |
| `PartyListTable.tsx` | Scrollable party representation table |
| `PartyNetwork.tsx` | Force-directed party switching graph |
| `AgeDistributionRadial.tsx` | Generational age cohort visualization |
| `SwitchTimeline.tsx` | Legislative timeline with wave indicators |
| `CommitteeControl.tsx` | Party chair distribution bars |
| `CrossChamberFlow.tsx` | Dual-chamber MP flow diagram |
| `DataQualityGauge.tsx` | Data completeness progress gauge |
| `TimelineStrip.tsx` | Legislative period timeline |
| `PartyComparisonMatrix.tsx` | Party-to-party switch matrix |

Component sizes were removed from this table because the old values (~2KB,
~3KB, etc.) were estimates, not measurements of the current bundle.

---

## 5. Verification checklist

### Build and tests
- [x] `npm run build` succeeds (2026-11-19, exit 0, 909 modules)
- [x] `uv run pytest -q` — 259 passed (2026-11-19)
- [x] `npm run lint` (`tsc --noEmit`) — part of `npm run build`, exit 0

### UI and accessibility
- [ ] `python3 scripts/ui_validate.py` passes all 18 routes — **RED: 3 routes
      fail with React #310** (2026-11-19)
- [ ] axe: no violations on any route — **RED: 2 moderate findings on each of
      the 3 failing routes** (2026-11-19)
- [ ] Lighthouse audit — not run in this pass
- [ ] Manual QA on staging — not run in this pass

### Interaction and navigation
- [x] Visualizations carry navigation targets (table below)
- [ ] Keyboard-only navigation re-verified after the P0-1/P0-2 fixes

Because the UI/accessibility boxes are unticked, this document does **not**
claim deployment readiness.

---

## 6. Navigation targets

| Element | Click target | Target page |
|---|---|---|
| DashboardCard (Persons) | Party ID | `/mps` |
| DashboardCard (Memberships) | Party ID | `/mps` |
| DashboardCard (Switches) | Party ID | `/traseism` |
| DashboardCard (Committees) | Party ID | `/committees` |
| PartyListTable row | Party ID | `/party/{shortName}` |
| PartyNetwork node | Party ID | `/party/{shortName}` |
| SwitchTimeline wave | Wave ID | `/traseism?legislature={id}` |
| CommitteeControl bar | Chair ID | `/person/{chairPersonId}` |
| CrossChamberFlow item | Person ID | `/person/{id}` |

---

## 7. Next steps (honest)

1. Land P0-1/P0-2, then re-run `python3 scripts/ui_validate.py` against production.
2. Re-run the Lighthouse audit and manual staging QA; tick the boxes above only
   with the captured output.
3. Only then re-assess deployment readiness.

---

## 8. Rollback

Use the remediation baseline tag — no force-push, no data deletion:

```bash
cd /home/nedaktov/parlament-deschis
git checkout pre-remediation-2026-11-19 -- <path-to-restore>
```

The former instructions here (`git reset --hard` and `git push origin --force`)
were removed: they are destructive and contradict the project's non-destructive
rollback policy.

---

**Evidence collected by:** direct command execution
**Date:** 2026-11-19
