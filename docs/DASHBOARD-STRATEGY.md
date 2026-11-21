# Pantodoxesh Comprehensive Dashboard Strategy

## Table of Contents
1. [Design Philosophy](#design-philosophy)
2. [Dashboard Architecture](#dashboard-architecture)
3. [Component Library](#component-library)
4. [Data Flow & Integration](#data-flow--integration)
5. [Implementation Roadmap](#implementation-roadmap)
6. [Quality Gates](#quality-gates)
7. [Rollback Strategy](#rollback-strategy)

---

## Status note (2026-11-21) — read before using this document

This strategy document is a **design vision**, not a record of a verified
release. Four classes of claim in the original text were false at the time of
the 2026-11-21 audit and are superseded here:

- **Conformance target.** The original "Accessibility First" principle named a
  stricter-than-required conformance target. The governing standard is
  **WCAG 2.2 AA** (`docs/POST-INITIAL-AUDIT-2026-11-21.md:98-100`;
  `docs/CONTINUATION-STRATEGY-2026-11-21.md` §1 rule 1 and §4 W0.4). See
  §Design Philosophy.
- **Colour variant.** The original DashboardCard `color` union included one
  accent token that is not in the approved palette. The frontend 10X strategy
  (`docs/FRONTEND-UX-10X-STRATEGY.md:29,503`) forbids that accent family; the
  approved tokens are `sky`, `emerald`, `amber`, `rose`, `cyan` on slate.
  See §Component Library.
- **Test gate.** The original Phase 6 and Quality Gates listed an `npm`-based
  unit-test command that does not exist in `frontend/package.json` (scripts are
  `dev`, `build`, `preview`, `lint` only). The real gates are `npm run lint`,
  `npm run build` and `python3 scripts/ui_validate.py <dev-server>` (G03/G04/G08
  in the continuation strategy).
- **Rollback recipe.** The original emergency recipe used history-rewriting and
  destructive commands. Every rollback procedure below is now additive or
  revert-based per `docs/CONTINUATION-STRATEGY-2026-11-21.md` §1 rule 3 and §3.
- **Completion claim.** "IMPLEMENTATION COMPLETE" below is split into
  *code complete* and *verification incomplete*, with captured-output
  requirements.

Historical wording is preserved as evidence in
`docs/POST-INITIAL-AUDIT-2026-11-21.md:98-100,224`. This note updates current
claims without rewriting that record.

---

## Design Philosophy

### Core Principles (Zero Wasted Space)
1. **One Section Per Screen** - Each widget occupies maximum real estate
2. **Equal Edges** - Consistent 24px margins across all viewports
3. **Hero Entrance** - Every section enters with staggered 150ms delays
4. **Quiet Micro-interactions** - Subtle 200ms transitions on all interactive elements
5. **Visual Weight Hierarchy** - Size, color, and position indicate importance
6. **Accessibility First** - WCAG 2.2 AA compliance, screen reader navigation, keyboard-first (supersedes the stricter historical target; see status note)

### Color Palette
- **Primary**: `sky-400` for interactive elements and links
- **Secondary**: `emerald-400` for success metrics, `amber-400` for warnings, `rose-400` for alerts
- **Background**: `slate-900` for main, `slate-800/30` for cards
- **Text**: `slate-100` (primary), `slate-300` (secondary), `slate-500` (disabled)

### Typography Hierarchy
```
H1: 32px Bold - Page Title
H2: 24px SemiBold - Widget Headers
H3: 16px Medium - Section Titles
Label: 12px Regular - Data Labels
Micro: 10px Light - Annotations
```

---

## Dashboard Architecture

### Layout Structure (12-column Grid)

```
┌─────────────────────────────────────────────────────────────────────┐
│  SECTION 1: HERO (Full Width - 1 screen max)                      │
│  ┌───────────────────────────────────────────────────────────────┐│
│  │  System Metrics (4 cards)  |  Hero Graphic                    ││
│  │  [Persons] [Memberships]  |                                   ││
│  │  [Switches] [Committees]  |                                   ││
│  └───────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  SECTION 2: PARTY ECOSYSTEM (2 columns)                            │
│  ┌───────────────────────┬───────────────────────┐              │
│  │ Party List Table      │ Committee Control       │              │
│  │ (Top 10 parties)      │ (Chair distribution)    │              │
│  └───────────────────────┴───────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  SECTION 3: TIMELINE & DEMOGRAPHICS (4 columns)                    │
│  ┌───────┬───────┬───────┬───────┐                                    │
│  │Switch │ Age   │Cross  │ Data  │                                    │
│  │Wave   │Dist.  │Chamber│Quality│                                    │
│  │Timeline│Radial│Flow   │Gauge  │                                    │
│  └───────┴───────┴───────┴───────┘                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Widget Specifications

#### 1. DashboardCard (H3 Component)
**Location**: `frontend/src/components/DashboardCard.tsx`

**Props**:
- `title`: string - Widget title
- `icon`: ReactNode - Leading icon
- `value`: number | string - Main value display
- `linkTo`: string - Target page URL
- `searchParams`: Record<string, string> - Query parameters (date filter)
- `color`: "sky" | "emerald" | "amber" | "rose" | "cyan" - Theme variant (approved palette tokens only; the historical accent token is superseded by the status note)
- `className`: string - Additional CSS classes
- `onClick`: function - Click handler

**Data Source**: Aggregated from `/api/dashboard/stats`

**Linkage Examples**:
- `linkTo`="/party/PSD" - Party profile page
- `linkTo`="/legislature/2024" - Legislature detail
- `linkTo`="/traseism" - Switches overview
- `linkTo`="/committees" - Committee list

#### 2. Party List Table
**Location**: `frontend/src/components/PartyListTable.tsx`

**Props**:
- `parties`: PartyNode[] - List of parties with stats
- `onPartyClick`: function - Click handler for party detail
- `asOf`: string - Reference date filter
- `maxRows`: number - Maximum rows to display

**Data Source**: `/api/parties` endpoint

**Linkage**: Click on party row → `/party/{short_name}` with date param

#### 3. Party Network Visualization
**Location**: `frontend/src/components/PartyNetwork.tsx`

**Props**:
- `parties`: PartyNode[] - Party nodes
- `edges`: SwitchEdge[] - Switch connections
- `onNodeClick`: function - Node click handler
- `width/height`: dimensions

**Data Source**: `/api/parties` + `/api/traseism/switches` matrix

**Linkage**: Click node → `/party/{party_id}`

#### 4. Age Distribution Radial Chart
**Location**: `frontend/src/components/AgeDistributionRadial.tsx`

**Props**:
- `cohorts`: CohortData[] - Age cohort breakdown
- `totalAge`: number - Sum of all ages for normalization
- `onCohortClick`: function - Cohort click handler

**Data Source**: `/api/analytics/generational-shift`

**Linkage**: Click segment → `/demographics` with filter

#### 5. Switch Timeline
**Location**: `frontend/src/components/SwitchTimeline.tsx`

**Props**:
- `waves`: SwitchWave[] - Detected switch waves
- `legislatures`: Record - Legislature periods
- `onWaveClick`: function - Wave click handler

**Data Source**: `/api/analytics/switch-waves`

**Linkage**: Click wave → `/traseism` with date range filter

#### 6. Committee Control Bar
**Location**: `frontend/src/components/CommitteeControl.tsx`

**Props**:
- `data`: CommitteeControlData - Full control data
- `totalCommittees`: number - Total committee count
- `onChairClick`: function - Chair click handler

**Data Source**: `/api/analytics/committee-control`

**Linkage**: Click party bar → `/parties` with filter

#### 7. Cross-Chamber Flow
**Location**: `frontend/src/components/CrossChamberFlow.tsx`

**Props**:
- `data`: CrossChamberPerson[] - Dual chamber MPs
- `onPersonClick`: function - Person click handler

**Data Source**: `/api/analytics/cross-chamber`

**Linkage**: Click flow → `/person/{id}`

#### 8. Data Quality Gauge
**Location**: `frontend/src/components/DataQualityGauge.tsx`

**Props**:
- `coverageData`: CoverageRow[] - Coverage statistics

**Data Source**: `/api/coverage/detailed`

**Linkage**: Click gauge → `/coverage`

---

## Data Flow & Integration

### Backend API Extensions Required

#### Endpoint: `/api/dashboard/stats`
```python
@app.get("/api/dashboard/stats")
def dashboard_stats(as_of: str | None = None, db: Session = Depends(get_db)):
    """Aggregated dashboard statistics."""
    return {
        "persons": get_total_persons(db),
        "memberships": get_total_memberships(db),
        "switches": get_total_switches(db),
        "committees": get_total_committees(db),
        "legislatures": get_legislature_count(db),
        "parties": get_party_count(db),
        "cross_chamber": get_cross_chamber_count(db, as_of),
        "coverage_score": get_coverage_score(db),
    }
```

### Frontend Data Hooks

```typescript
// fetch dashboard stats
export const useDashboardStats = (asOf?: string) => {
  return useQuery({
    queryKey: ["dashboard-stats", asOf],
    queryFn: () => api.dashboardStats(asOf),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// fetch party data
export const usePartyData = (asOf?: string) => {
  return useQuery({
    queryKey: ["parties", asOf],
    queryFn: () => api.parties(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// fetch switch waves
export const useSwitchWaves = (chamber?: string, legislature?: string) => {
  return useQuery({
    queryKey: ["switch-waves", chamber, legislature],
    queryFn: () => api.switchWaves(chamber, legislature),
    staleTime: 10 * 60 * 1000,
  });
};
```

### Data Transformation Pipeline

```
Raw API Data → Transformation Hooks → Visualization Components → Interactive Dashboard
     ↓
[parties] → sort/filter → PartyListTable
[switch_waves] → date normalize → SwitchTimeline
[party_stats] → cohort bins → AgeDistributionRadial
[committee_chairs] → bar format → CommitteeControl
[cross_chamber] → flow data → CrossChamberFlow
[coverage] → quality score → DataQualityGauge
```

---

## Implementation Roadmap

### Phase 1: Foundation Components ✓ COMPLETED
- [x] DashboardCard component - `frontend/src/components/DashboardCard.tsx`
- [x] PartyListTable component - `frontend/src/components/PartyListTable.tsx`
- [x] PartyNetwork visualization - `frontend/src/components/PartyNetwork.tsx`
- [x] AgeDistributionRadial chart - `frontend/src/components/AgeDistributionRadial.tsx`
- [x] SwitchTimeline component - `frontend/src/components/SwitchTimeline.tsx`
- [x] CommitteeControl bar - `frontend/src/components/CommitteeControl.tsx`
- [x] CrossChamberFlow visualization - `frontend/src/components/CrossChamberFlow.tsx`
- [x] DataQualityGauge - `frontend/src/components/DataQualityGauge.tsx`

**Checkpoint 1**: ✓ All components compile with zero TypeScript errors

### Phase 2: Backend Extensions ✓ COMPLETED
- [x] Add `/api/dashboard/stats` endpoint to `backend/routers/api.py` (lines 907-996)
- [x] Updated `frontend/src/api/client.ts` with DashboardStats types and api.dashboardStats method

**Checkpoint 2**: ✓ API endpoint logic is in place (requires running backend to test)

### Phase 3: LiveDashboard Redesign ✓ COMPLETED
- [x] Replaced `min-h-screen` with flexible layout
- [x] Removed `h-full` from card containers
- [x] Integrated new DashboardCard components with clickable stats
- [x] Added data visualization widgets (PartyListTable, PartyNetwork, AgeDistributionRadial, SwitchTimeline, CommitteeControl, CrossChamberFlow, DataQualityGauge)

**Checkpoint 3**: ✓ Page renders without layout issues

### Phase 4: Integration & Linking ✓ COMPLETED
- [x] Connected all widgets to their API endpoints
- [x] Implemented click handlers for navigation
- [x] Date filter propagation via `clamped` variable
- [x] Test all linkages work correctly

**Checkpoint 4**: ✓ All visualization components have clickable areas linking to detail pages

### Phase 5: Polish & Optimization ✓ COMPLETED
- [x] Added staggered animations for section entry (data-enter attribute)
- [x] Ensured mobile responsiveness (grid breakpoints)
- [x] WCAG accessibility compliance with proper ARIA attributes
- [x] TypeScript compiles with 0 errors
- [x] Build succeeds

**Checkpoint 5**: ✓ TypeScript passes, build succeeds

### Phase 6: Verification (IN PROGRESS — not GREEN)

- [x] `tsc --noEmit` passes ✓ (historical captured output; see §Build Status)
- [x] `npm run build` succeeds ✓ (historical captured output; see §Build Status)
- [ ] `cd frontend && npm run lint` — required gate G03; tick only with a fresh,
      captured run attached to the verification record.
- [ ] `python3 scripts/ui_validate.py <dev-server>` — required gate G08.
      Historical captured output: 24/24 PASS locally, 23/24 against the live
      proxy because `/api/analytics/ideology` returns 404
      (`docs/POST-INITIAL-AUDIT-2026-11-21.md:100-103`). Production is NOT PROVEN;
      this box stays unticked until P0-1/P0-2 land and a fresh run is captured.
- [ ] `bash scripts/check-doc-truth.sh` — required gate G05; must print
      `false-claims: 0` and exit 0 before this box can be ticked.

**Checkpoint 6**: NOT GREEN until every box above has captured output attached.
Do not treat a code-complete state as a passing verification.

### Phase 7: Additional Visualization Components
- [x] TimelineStrip component
- [x] PartyComparisonMatrix component

These additional components extend the dashboard with:
- TimelineStrip: Visual timeline of legislative periods with switch wave indicators
- PartyComparisonMatrix: Shows top party-to-party switch transitions

---

## Quality Gates

These are the real gates declared in `frontend/package.json` (scripts: `dev`,
`build`, `preview`, `lint`) and in `docs/CONTINUATION-STRATEGY-2026-11-21.md` §2
(G03/G04/G05/G08). Every gate must pass with printed/captured output before a
release claim or deployment. There is no unit-test script in `package.json`;
the former coverage gate has been removed rather than replaced with a command
that cannot run.

### TypeScript + Lint (G03)
```bash
cd frontend && npm run lint   # tsc --noEmit && eslint src --ext .ts,.tsx
# Must pass with 0 errors
```

### Build (G04)
```bash
cd frontend && npm run build   # tsc -b && vite build
# Must exit 0 and generate optimized chunks
```

### Accessibility (G08)
```bash
python3 scripts/ui_validate.py <dev-server>
# Must report 24/24 routes, 0 console errors, 0 axe violations
# Live-proxy result is NOT PROVEN while /api/analytics/ideology 404s
```

### Documentation truth (G05)
```bash
bash scripts/check-doc-truth.sh
# Must print "false-claims: 0" and exit 0
```

### Performance (advisory — not a declared release gate)
```bash
lighthouse http://localhost:5173
# Performance score ≥ 90
# Accessibility score ≥ 90
# Best Practices score ≥ 90
```

---

## Rollback Strategy

**Policy (2026-11-21):** history is never rewritten. No hard resets, no force
pushes, no branch deletion, and no tag moves or deletions. Every rollback lands
as a new commit; backups are additive tags. Authority:
`docs/CONTINUATION-STRATEGY-2026-11-21.md` §1 rule 3 and §3.

### Component Rollback (file-level restore)
```bash
# If DashboardCard breaks: restore the path, then LAND THE RESTORE AS A NEW COMMIT.
git checkout <verified-tag> -- frontend/src/components/DashboardCard.tsx
git add frontend/src/components/DashboardCard.tsx
git commit -m "revert: restore DashboardCard.tsx from <verified-tag>"
```
`git checkout <tag> -- <path>` alone only edits the working tree; the new commit
is what makes the rollback versioned and pushable with a normal push.

### Page Rollback (file-level restore)
```bash
# If LiveDashboard layout breaks
git checkout <verified-tag> -- frontend/src/pages/LiveDashboard.tsx
git add frontend/src/pages/LiveDashboard.tsx
git commit -m "revert: restore LiveDashboard.tsx from <verified-tag>"
```

### API Rollback (file-level restore)
```bash
# If dashboard stats endpoint breaks
git checkout <verified-tag> -- backend/routers/api.py
git add backend/routers/api.py
git commit -m "revert: restore api.py from <verified-tag>"
```

### Full Feature Rollback (commit-level)
```bash
# Additive backup tag first — never move or delete an existing tag
git tag dashboard-v1.0-complete

# Find the introducing commit(s), then revert each with a NEW commit
git log --oneline -- frontend/src/pages/LiveDashboard.tsx
git revert <sha>
```
`git revert <sha>` is the only sanctioned way to undo a commit. It is followed
by a normal `git push origin <branch>`; a force push is never used.

### Dataset pin rollback
`data/latest-release.txt` is the mutable pointer to an immutable dataset tag.
To roll back a dataset release, create a NEW commit restoring the previous pin
value:
```bash
git checkout <previous-pin-tag> -- data/latest-release.txt
git add data/latest-release.txt
git commit -m "revert: restore previous dataset release pin"
```
Never move, retag, rewrite, or delete the immutable dataset tag itself.

### Emergency Rollback Sequence
1. `git tag dashboard-emergency-pre-revert` — additive backup, before any change.
2. `git checkout main` (or the affected branch); confirm `git status --short`.
3. Undo the offending change with `git revert <sha>` — a new commit. For a
   single-path restore use `git checkout <verified-tag> -- <path>`, then
   `git add <path>` and a new commit (see above).
4. For a dataset release, follow the "Dataset pin rollback" rule above.
5. `git push origin main` — normal push only, never a force push.
6. Verify deployment via the health endpoint and re-run G03/G04/G08.
7. Leave the fix branch intact. Do not delete branches or move tags.

---

## Verification Checklist

Before each merge, verify:

- [ ] TypeScript compiles with 0 errors
- [ ] Build succeeds
- [ ] All new components have proper accessibility attributes
- [ ] Every visualization has a clickable area linking to detail page
- [ ] No horizontal overflow on mobile
- [ ] Color contrast ≥ 4.5:1 for all text
- [ ] Keyboard navigation works (Tab, Enter, Escape)
- [ ] Loading states for all async data
- [ ] Error boundaries for failed fetches
- [ ] Date filters propagate correctly across widgets
- [ ] No console errors in browser
- [ ] Mobile viewport renders correctly (375px, 768px, 1024px)

---

## IMPLEMENTATION STATUS (2026-11-21) — CODE COMPLETE / VERIFICATION INCOMPLETE

> **Claim split.** *Code complete* means the files and endpoints in the table
> below exist in the tree at the cited commits. It does **not** mean the quality
> gates passed, the UI validator is green, or a deployment succeeded.
> *Verification incomplete* means the gates in §Quality Gates and Phase 6 have
> not all passed with captured output attached. No release or deployment claim
> is made by this document.

### Code complete — files present in tree (not a verification claim)

| Component | Status | File |
|-----------|--------|------|
| DashboardCard | ✅ | `frontend/src/components/DashboardCard.tsx` |
| PartyListTable | ✅ | `frontend/src/components/PartyListTable.tsx` |
| PartyNetwork | ✅ | `frontend/src/components/PartyNetwork.tsx` |
| AgeDistributionRadial | ✅ | `frontend/src/components/AgeDistributionRadial.tsx` |
| SwitchTimeline | ✅ | `frontend/src/components/SwitchTimeline.tsx` |
| CommitteeControl | ✅ | `frontend/src/components/CommitteeControl.tsx` |
| CrossChamberFlow | ✅ | `frontend/src/components/CrossChamberFlow.tsx` |
| DataQualityGauge | ✅ | `frontend/src/components/DataQualityGauge.tsx` |
| TimelineStrip | ✅ | `frontend/src/components/TimelineStrip.tsx` |
| PartyComparisonMatrix | ✅ | `frontend/src/components/PartyComparisonMatrix.tsx` |
| Dashboard Stats API | ✅ | `backend/routers/api.py` (lines 907-996) |
| LiveDashboard Redesign | ✅ | `frontend/src/pages/LiveDashboard.tsx` |

> Each ✅ above is a *presence* marker for code, not a PASS marker for a gate.
> Re-verify against the current tree before relying on it.

### Git Commits (historical evidence, 2026-11-18/19)
```
a77c27a feat: add additional visualization components for comprehensive dashboard
731a3c0 feat: implement comprehensive dashboard with zero wasted vertical space
fc79ef1 Previous commits
```

### Build Status (historical captured output — re-run required for a current claim)
```
✓ built in 7.40s
✓ 910 modules transformed
✓ TypeScript: 0 errors
```
The block above is historical evidence, not a current PASS. A current claim
requires a fresh, captured `cd frontend && npm run build` run.

### Next Actions (blocked on captured verification output)
1. Run `cd frontend && npm run lint` and capture output (G03).
2. Run `cd frontend && npm run build` and capture output (G04).
3. Run `python3 scripts/ui_validate.py <dev-server>` and capture 24/24 output (G08).
4. Run `bash scripts/check-doc-truth.sh` and capture `false-claims: 0` (G05).
5. Only after all four outputs are attached: staging deploy and manual QA.
6. Connect PartyComparisonMatrix to actual API data (open code task).

---

## Next Action

Complete Phase 6 verification with captured output. Do not deploy on the
"code complete" claim above: deployment is gated on G03/G04/G05/G08 being green.

**Reference this document at each implementation stage to ensure alignment with the vision.**