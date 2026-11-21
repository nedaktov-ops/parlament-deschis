# R-05 — One shared loading / empty / error state system

**Role:** STRATEGY + RECIPE AGENT R-05 (read-only product code; this document is the only artefact authored)
**Baseline (authoritative):** `eb693b4` = `eb693b4d9faf558b22925fdb07ba6d118d7f6cef` ("Merge pull request #69 from nedaktov-ops/docs/triad-audit")
**Status:** STRATEGY AND IMPLEMENTATION PLAN ONLY — **no product file was edited by the author.** Every code block below is an instruction for an implementer, not a claim that it is already in the tree.
**Verification philosophy:** evidence over assertion. Every gate in §7–§8 carries exact command, expected output and exit code. A gate that cannot run is reported NOT PROVEN, never as a pass.

---

## 0. Objective

Replace the ad-hoc, inconsistent and often *dishonest* data-state handling across the front end with **one state system**:

1. Every data region obeys the explicit precedence **`isLoading → isError → empty → data`**, computed once by `resolveViewState()`.
2. **No `0`, `0%`, `0.00`, empty array or placeholder is ever presented as a fact while a query is pending or failed.** Derived statistics are computed only for rendering *inside the `ready` branch*.
3. **Retry everywhere**: every error branch renders the shared `ErrorState` with an `onRetry` handler wired to `query.refetch()`. No bare `text-red-400` / `text-rose-200` error text without a retry.
4. **Honest empty copy, distinct from error copy**: a successful-but-empty result says "no records for this scope"; a failed request says "could not load" and offers retry. The two strings are never shared.
5. **Consistent styling and accessibility**: one `StateView` shell, one button grammar (`btn btn-hover min-h-11`), one `role="alert"` error, one `role="status"` loading, one sr-only `<h1>` in full-page pending states (keeps axe's heading rule green), `data-state` attribute on every state root for deterministic probes.
6. **i18n parity**: every new string exists in both `ro` and `en`, in a single delimited block in `frontend/src/i18n.ts` that other recipes must not edit.
7. **Per-page migration** with exact line anchors and exact replacement wrappers (§6), plus a targeted route probe (§8.3) that *proves* the three non-ready states on real routes.

This recipe implements cross-cutting finding **FN-5**, appearance finding **AP-8** and exhaustive-audit finding **X3**. It explicitly does **not** attempt the neighbouring content-honesty fixes (FN-1…FN-4, FN-6…FN-9), the visual-primitive fixes (AP-1/AP-2) or the bulk i18n sweep (X4) — see §11 Side-quest policy.

---

## 1. Evidence (path:line, all at baseline `eb693b4`)

> Paths are relative to `/home/nedaktov/parlament-deschis`. Vault paths include the vault directory name. The audited source commits in the vault frontmatter (`1d60492`, `f70aca3`) are the *audit* commits; the product tree at working HEAD (`80d91a9`) and at `eb693b4` is byte-identical for all files in §2 (`git diff HEAD eb693b4 -- frontend/src scripts/ui_validate.py` → empty output, exit 0), so the line numbers below hold at both.

### 1.1 Audit findings that authorize this work

| ID | Finding | Evidence |
|---|---|---|
| FN-5 | Loading/error/empty inverted or missing: zero-valued stats render as facts during fetch (Demographics, PartyTimeline, CoverageView, SenateHistory); errors shown as "no data" (Coalitions, Radar, PartyComparison, SenateHistory); LiveDashboard widgets show perpetual "Loading…"; retries absent on most error branches | `Parlament Deschis Obsidian vault/40-FRONTEND/TRIAD-AUDIT-2026-11-21.md:67` |
| AP-8 | State visuals not shared: `ErrorState`/`LoadingState`/`EmptyState` exist but most pages use bare `text-red-400` / `text-slate-500` / hand-rolled panels; error palette alternates `rose-200`, `red-400`, `amber-400` | `…/TRIAD-AUDIT-2026-11-21.md:33` |
| Enhancement order #4 | "One state system — shared `LoadingState/EmptyState/ErrorState` with retry, gated `isLoading → isError → empty → data`; never render 0 as data" | `…/TRIAD-AUDIT-2026-11-21.md:81` |
| X3 | Error/empty conflation and zero-valued stats during loading; reuse shared states | `…/FRONTEND-AUDIT-2026-11-21.md:41`, remedy at `:99-100` |
| X3 (Coalitions) | "False empty states during load" | `…/FRONTEND-AUDIT-2026-11-21.md:74` |
| Positive pattern | Report/Committees already gate + retry (behaviour to preserve while normalising markup) | `…/TRIAD-AUDIT-2026-11-21.md:74` |

### 1.2 The three existing primitives (present but barely used)

| File | Evidence | Defect relevant to R-05 |
|---|---|---|
| `frontend/src/components/LoadingState.tsx` | wrapper `:14-15`; spinner `:16-40`; optional retry `:47-56`; `role="status"` incorrectly on `<svg>` at `:18` | Not reused on most pages; no `data-state`; retry button lacks `btn-hover min-h-11` |
| `frontend/src/components/EmptyState.tsx` | wrapper `:30-33`; default magnifier `:11-23`; CTA `:41-50` | No `data-state`; no shared shell with the other two; CTA button styling differs |
| `frontend/src/components/ErrorState.tsx` | `role="alert"` `:15-18`; `text-rose-400` icon `:19-34`; retry via `t("retry","Retry")` `:38-47` | Imported by only two components (`Voturi.tsx:5`, `VoteActivityChart.tsx:16`, `RollCallTable.tsx:4`); no description slot; `data-state` absent |
| Usage count | `LoadingState`: `Mps.tsx:8,161`, `Parties.tsx:6,83`, `Committees.tsx:15,363`; `EmptyState`: `Mps.tsx:9,206`, `Parties.tsx:7,92`, `Committees.tsx:16,382`; `ErrorState`: `Voturi.tsx:5,54`, `VoteActivityChart.tsx:16,180`, `RollCallTable.tsx:4,55` | 3 of 23 pages use the loading/empty primitives; 1 page uses the error primitive |

### 1.3 Zero-as-fact and error-as-empty (P0 evidence)

| Page | Exact lines | Observed behaviour |
|---|---|---|
| `frontend/src/pages/Demographics.tsx` | stats derived `:34-60`; rendered `:80-125`; loading `:150-152`; error `:153-157`; "empty" `:214-221`; coverage `:223-230` | Hero moment `totalMPs=0`, `avgAge=0`, `medianAge=0`, `coveragePct=0` render during load and error; error is a red line with no retry |
| `frontend/src/pages/PartyTimeline.tsx` | `datedJoins` `:61`; `gapsCount ?? 0` `:69-71`; hero stats `:114-148`; loading `:184-186`; error `:187-191`; table `:193-261`; empty `:263-265`; methodology `:267-274` | `0` "Total switches" and `0` "Gap events" render as facts during fetch; red error line with no retry |
| `frontend/src/pages/CoverageView.tsx` | totals `:34-52`; `fullPct/partialPct/overallPct` `:61-66`; loading `:68-74`; error `:76-87` (inline `ml-3 underline` retry); **no empty branch** | Gating exists but not via shared components; `rows.length === 0` renders an empty table with hero zeros |
| `frontend/src/pages/SenateHistory.tsx` | hero `value={… ?? "--"}` `:65-89`; moment `:90-97`; table `:126-170`; "noData" row `:161-167` | **No `isLoading`/`isError` handling at all**; `new Set(rows…).size = 0` and `No coverage data available` are shown while loading and on error; error palette `text-rose-200` |
| `frontend/src/pages/Coalitions.tsx` | loading `:71-75`; error `:76-80`; stats `:81-104`; moment `:110-135`; breakups empty `:144-147`; formations empty `:221-225`; congresses empty `:244-248` | Empty branches test only `!waves.isLoading`, so they render during **error**; no retry |
| `frontend/src/pages/LiveDashboard.tsx` | stats `?? "--"` `:104-141`; fake widget fallback `{ as_of: clamped, total_committees: 0, parties: [], chairs: [] }` `:174-178`; gauge `?? []` `:179-181`; `AgeDistributionSection` `:182` | Widgets render zero/empty placeholder data during fetch; no unified error/retry for the dashboard queries |
| `frontend/src/components/CommitteeControl.tsx` | `if (!parties?.length) … "Loading committee data..."` `:43-52` | Perpetual "Loading…" when the parent passes the fake empty fallback or the query failed — indistinguishable states |
| `frontend/src/components/DataQualityGauge.tsx` | `if (!stats) … "Loading..."` `:57-66` | Same conflation; also `completenessScore = 0` would be shown as fact if empty data were passed |
| `frontend/src/components/ui/AgeDistributionSection.tsx` | loading `Skeleton` `:15-17`; error `text-red-400` `:18-20`; no empty branch | No retry; empty array renders a radial with total 0 |
| `frontend/src/pages/Radar.tsx` | loading `:87-96` (Skeleton + inline "Loading…"); error `:98-105` (`text-red-400`, **no retry**, wrong copy `view.voturi.loadError`); empty `:122-126` | Error copy borrowed from the votes page; no retry |
| `frontend/src/pages/Grafice.tsx` | loading `:25-33`; error `:35-41` (`text-red-400`, no retry, wrong copy); empty `:58-62` | Same |
| `frontend/src/pages/Topuri.tsx` | loading `:31-40`; error `:42-49`; redundant/dead inline states `:84-100`; empty `:95-101` | Same; duplicated unreachable state UI |
| `frontend/src/pages/Ideology.tsx` | loading `:187-195`; error `:197-203`; empty `:205-223`; `?? 0` scatter points `:77-85`, `:305-311`; "not yet ingested" note rendered above populated chart `:320-323` | Wrong error copy; fabricated `0.00` points are a neighbour finding (FN-4) — gate the chart, do not fix the data here |

### 1.4 Error branches with no retry / wrong palette (P1 evidence)

| Page | Exact lines |
|---|---|
| `frontend/src/pages/PartyComparison.tsx` | only `parties` query gated `:176-183`; ages/control queries unguarded; committee "unavailable" → `"0"` `:109-110`; error has no retry |
| `frontend/src/pages/MpComparison.tsx` | hero `poolList.length` `:155-179` renders 0 during load; error `:249-254` no retry; "pick two" `:320-324` shows on error |
| `frontend/src/pages/SwitchLeaderboard.tsx` | hero stats `:63-80` render 0 during load; loading `:125-127`; error `:128-132` no retry |
| `frontend/src/pages/Parties.tsx` | shared loading `:82-84`, inline error `:85-89` (no retry), shared empty `:91-93` |
| `frontend/src/pages/Mps.tsx` | shared loading `:160-162`, bespoke error `:163-167` (no retry), shared empty `:205-207` |
| `frontend/src/pages/Committees.tsx` | member error `:110-114`; control error amber `:341-345`; list loading `:362-364`, error `:365-369`, empty `:381-388` |
| `frontend/src/pages/InstitutionalView.tsx` | committee branch `:49-68`; cross-chamber branch `:79-90`; `ml-3 underline` retries `:52`, `:82` |
| `frontend/src/pages/LegislatureDetail.tsx` | meta error `:39-50`; hero `?? "--"` `:69-102`; chamber branch `:109-134`; movements branch `:139-184`; permanent pulse `:188-193` |
| `frontend/src/pages/PersonDeepDive.tsx` | loading `:75-82`; error `:84-94` (bespoke, has retry) |
| `frontend/src/pages/PartyProfile.tsx` | loading `:57-63`; error `:65-74`; movements branch `:154-166`; `?? 0` at `:78` (neighbour finding) |
| `frontend/src/pages/Traseism.tsx` | **local shadow `ErrorState`** `:107-132` instead of the shared one; call sites `:342`, `:838`, `:924`; loading `text-slate-500` `:339-340`, `:617-618`, `:833-835`, `:921-922`; waves error text `:620-622` |
| `frontend/src/pages/Report.tsx` | bespoke loading `:158-195` and error `:196-230` (both already have retry — behaviour to preserve, markup to normalise) |
| `frontend/src/pages/Voturi.tsx` | shared `ErrorState` `:52-59`; inline Skeleton loading `:40-50` — the one page already close to target |

### 1.5 Gate infrastructure (read-only evidence)

| File | Evidence | Use |
|---|---|---|
| `scripts/ui_validate.py` | 24 route tuples `:47-75`; zero-JS-error capture `:82-90`; axe-core scan `:113-124`; pass line `UI VALIDATION PASS: {n} routes, …` `:177`; exit 1 on any finding `:174-176` | Primary UI gate (§8.2) |
| `frontend/src/router.tsx` | `<main id="main-content" …>` `:299-301`; `QueryClient` `retry: 1` `:566-575` | Pending states live inside the main landmark; probe must wait for the single retry |
| `frontend/src/i18n.ts` | `ro` object `:5-566`; `en` object `:568-1129`; existing `loading` `:160`/`:718`, `retry` `:161`/`:719`, `traseismRetry` `:255`/`:812`; insertion anchors: last key `"waves.title"` at `:565`/`:1128`, closing `},` at `:566`/`:1129` | Place the delimited R-05 block here |
| `frontend/src/index.css` | `.btn` `:171-173`; `.btn-hover` `:146-154`; global focus ring `:198-201`; `--color-danger` `:41`; light-theme rose override `:83-84` | Reuse existing utilities; **R-05 does not edit CSS** |
| `frontend/package.json` | `lint` = `tsc --noEmit && eslint src --ext .ts,.tsx`; `build` = `tsc -b && vite build` | §8.1 |
| `docs/GATE-EVIDENCE-2026-11-21.md` | G03/G04 `:24-25`, G08 `:27`; server recipe `:236-237` | Reproduce the proven gate environment |
| `.github/workflows/ci.yml` | frontend lint+build `:36-41`; evidence guards `:95-123` | CI parity |

---

## 2. Exclusive file list

### 2.1 Files R-05 owns (no other recipe may edit these while R-05 is open)

**New (2):**
- `frontend/src/components/ui/AsyncState.tsx` — `resolveViewState`, `StateView`, `AsyncState`.
- `scripts/ui_state_probe.py` — targeted 3-scenario route probe (§8.3).

**Modified primitives (3):**
- `frontend/src/components/LoadingState.tsx`
- `frontend/src/components/EmptyState.tsx`
- `frontend/src/components/ErrorState.tsx`

**Modified i18n (1), delimited block only:**
- `frontend/src/i18n.ts` — only between `// R-05 state-system keys — BEGIN` and `// R-05 state-system keys — END` in each locale.

**Modified pages (23):**
`Demographics.tsx`, `PartyTimeline.tsx`, `CoverageView.tsx`, `SenateHistory.tsx`, `Coalitions.tsx`, `Radar.tsx`, `Grafice.tsx`, `Topuri.tsx`, `Ideology.tsx`, `LiveDashboard.tsx`, `PartyComparison.tsx`, `MpComparison.tsx`, `SwitchLeaderboard.tsx`, `Parties.tsx`, `Mps.tsx`, `Committees.tsx`, `InstitutionalView.tsx`, `LegislatureDetail.tsx`, `PersonDeepDive.tsx`, `PartyProfile.tsx`, `Traseism.tsx`, `Report.tsx`, `Voturi.tsx` — all under `frontend/src/pages/`.

**Modified components (4):**
`frontend/src/components/CommitteeControl.tsx`, `frontend/src/components/DataQualityGauge.tsx`, `frontend/src/components/ui/AgeDistributionSection.tsx`, `frontend/src/components/VoteActivityChart.tsx`.

Total: **30 modified files + 2 new files**. (The P2 component sweep at §6.4 adds `RollCallTable.tsx`, `PersonDrawer.tsx`, `ChamberView.tsx`, `Search.tsx`, `SankeyFlow.tsx`, `LiveFeed.tsx`, `TimelineChart.tsx`, `About.tsx` **only if explicitly authorised** — otherwise record them as deferred in the verdict.)

### 2.2 Read-only for R-05 (never edit)

`frontend/src/index.css`, `frontend/src/api/client.ts`, `frontend/src/router.tsx`, `frontend/src/main.tsx`, `frontend/src/components/DataViz.tsx`, `scripts/ui_validate.py`, `scripts/check-doc-truth.sh`, all vault audits, all backend/pipeline/data files.

### 2.3 Coordination rule

Another recipe owns the bulk i18n sweep (X4) and the visual-primitive fixes (AP-1/AP-2). Both must stay out of the R-05 delimited i18n block and out of the three state primitives. R-05 must not add or move CSS classes in `index.css`; all state styling uses existing `btn`, `btn-hover`, `min-h-11`, `card`, `text-slate-*`, `text-rose-400`, `role=alert` semantics.

---

## 3. Preconditions

1. **Clean, identified tree.** `git -C /home/nedaktov/parlament-deschis rev-parse HEAD` → `eb693b4d9faf558b22925fdb07ba6d118d7f6cef`, or an implementer worktree created from it (§5 Step 0). If HEAD differs, stop and reconcile — do not rebase line anchors onto an unknown tree.
2. **Backup manifest verified** (§13): 30 files, combined digest `0bd63b3e22e31151b28809371463b4a86828b285265c931a77280b542d83fd41`.
3. **Green starting gates** (record output before editing): `cd frontend && npm run lint` exit 0; `npm run build` exit 0; `bash scripts/check-doc-truth.sh` prints `false-claims: 0`; `python3 scripts/ui_validate.py <base>` prints `UI VALIDATION PASS: 24 routes, zero JavaScript errors, zero axe violations`, exit 0. If any is red at baseline, **stop**: R-05 is not the owner of that failure.
4. **Gate environment available**: system `python3` with `playwright`, `/usr/bin/chromium`, `axe.min.js` at `/tmp/axe.min.js` (as used by `scripts/ui_validate.py:27,116`), Node/npm deps installed in `frontend/`, a local API. Evidence recipe at `docs/GATE-EVIDENCE-2026-11-21.md:236-237`:
   ```bash
   # terminal A — backend over a COPIED database (never the shipped one)
   PARLAMENT_DB=/tmp/opencode/g08-parlament-real.db .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8101
   # terminal B — Vite with /api proxy
   PARLAMENT_API_PROXY_TARGET=http://127.0.0.1:8101 npm run dev -- --host 127.0.0.1 --port 5180 --strictPort
   ```
   If the API is unavailable, the UI gate and probe are **NOT PROVEN** (§14), not waived.
5. **Translation discipline**: default `lng: "ro"`, `fallbackLng: "en"` (`frontend/src/i18n.ts:1132-1136`). Every new key must be added to **both** locales; English text must not leak to Romanian users (X4).
6. **Modern-web note (project `AGENTS.md`)**: all new buttons must carry `type="button"`; do not introduce colour-only status encoding; respect the global focus ring.
7. **Do not fix neighbouring findings inside this recipe.** Zero-as-fact is fixed by *gating*, not by silently changing metric definitions.

---

## 4. Design — exact code to implement

### 4.1 NEW `frontend/src/components/ui/AsyncState.tsx` (paste verbatim)

```tsx
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import LoadingState from "../LoadingState";
import EmptyState from "../EmptyState";
import ErrorState from "../ErrorState";

export type ViewState = "loading" | "error" | "empty" | "ready";
export type PendingViewState = Exclude<ViewState, "ready">;

export interface ResolveViewStateArgs {
  isLoading: boolean;
  isError: boolean;
  isEmpty: boolean; // MUST be derived from loaded data only (rows.length === 0)
}

/**
 * The single precedence rule for every data region: loading → error → empty → ready.
 * A pending fetch can never yield "empty" (isLoading wins).
 * A failed fetch can never yield "empty" (isError wins).
 */
export function resolveViewState({
  isLoading,
  isError,
  isEmpty,
}: ResolveViewStateArgs): ViewState {
  if (isLoading) return "loading";
  if (isError) return "error";
  if (isEmpty) return "empty";
  return "ready";
}

export interface StateViewProps {
  view: PendingViewState;
  /** sr-only h1 for full-page states; omit when the page's visible h1 stays rendered. */
  pageTitle?: string;
  variant?: "page" | "inline";
  loadingLabel?: string;
  loadingDescription?: string;
  errorLabel?: string;
  errorDescription?: string;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyCtaLabel?: string;
  onEmptyCta?: () => void;
  className?: string;
}

/** Renders exactly one non-ready state. `data-state` makes probes deterministic. */
export function StateView({
  view,
  pageTitle,
  variant = "page",
  loadingLabel,
  loadingDescription,
  errorLabel,
  errorDescription,
  onRetry,
  emptyTitle,
  emptyDescription,
  emptyCtaLabel,
  onEmptyCta,
  className,
}: StateViewProps) {
  const { t } = useTranslation();
  return (
    <div
      data-state={view}
      className={variant === "inline" ? "py-6" : "py-12"}
    >
      {pageTitle ? <h1 className="sr-only">{pageTitle}</h1> : null}
      {view === "loading" && (
        <LoadingState
          label={loadingLabel ?? t("loading")}
          description={loadingDescription}
        />
      )}
      {view === "error" && (
        <ErrorState
          message={errorLabel ?? t("state.error.title")}
          description={errorDescription ?? t("state.error.description")}
          onRetry={onRetry}
        />
      )}
      {view === "empty" && (
        <EmptyState
          title={emptyTitle ?? t("state.empty.title")}
          description={emptyDescription ?? t("state.empty.description")}
          ctaLabel={emptyCtaLabel}
          onCta={onEmptyCta}
          className={className}
        />
      )}
    </div>
  );
}

export interface AsyncStateProps extends Omit<StateViewProps, "view"> {
  view: ViewState;
  children?: ReactNode; // optional: full-page early returns render a state with no children
}

/** Gate one data region. `children` render only when view === "ready". */
export default function AsyncState({
  view,
  children,
  ...state
}: AsyncStateProps) {
  if (view === "ready") return <>{children}</>;
  return <StateView {...state} view={view} />;
}
```

**Invariants this code enforces**
- `children` (all numbers, bars, tables, canvases) are *not mounted* unless `view === "ready"`. No `0` is ever rendered by the state layer.
- `onRetry` is a prop on **every** error state; the recipe forbids calling `StateView`/`AsyncState` in an error case without it (§9 acceptance criterion AC-4).
- `data-state` is present on every pending root; the probe keys on it (§8.3).
- `pageTitle` emits exactly one sr-only `<h1>` per full-page pending view; no duplicate heading in the ready view.

### 4.2 Modified primitives — exact replacements

**`frontend/src/components/LoadingState.tsx`** — replace the whole file with:

```tsx
export interface LoadingStateProps {
  label?: string;
  description?: string;
  retryLabel?: string;
  onRetry?: () => void;
}

export default function LoadingState({
  label,
  description,
  retryLabel,
  onRetry,
}: LoadingStateProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col items-center justify-center py-12 max-w-xs mx-auto text-center"
    >
      <svg
        aria-hidden="true"
        className="animate-spin text-sky-400 mb-6"
        width="40"
        height="40"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle
          className="opacity-25"
          cx="12" cy="12" r="10"
          stroke="currentColor" strokeWidth="4" strokeLinecap="round"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      {label && <h2 className="text-sm font-semibold text-slate-200">{label}</h2>}
      {description && (
        <p className="text-xs text-slate-400 text-center max-w-xs">{description}</p>
      )}
      {onRetry && retryLabel && (
        <button
          type="button"
          onClick={onRetry}
          className="btn btn-hover min-h-11 mt-4 bg-slate-700 hover:bg-slate-600"
          aria-label={retryLabel}
        >
          {retryLabel}
        </button>
      )}
    </div>
  );
}
```
(Changes: live region moved from `<svg>` to the wrapper; heading demoted `h3→h2` so the sr-only page `h1` remains the only `h1`; one button grammar.)

**`frontend/src/components/EmptyState.tsx`** — keep the file, apply these three exact edits:
1. Wrapper at `:31-33`: add `aria-live="polite"` after `className={...}`:
   ```tsx
       <div
         aria-live="polite"
         className={`flex flex-col items-center justify-center py-12 max-w-xs mx-auto text-center ${className ?? ""}`}
       >
   ```
2. CTA button at `:42-49`: class becomes
   `className="btn btn-hover min-h-11 mt-4 bg-slate-700 hover:bg-slate-600"`.
3. No other change; the default magnifier and `title`/`description` API stay.

**`frontend/src/components/ErrorState.tsx`** — replace the whole file with:

```tsx
import { useTranslation } from "react-i18next";

export interface ErrorStateProps {
  message?: string;
  description?: string;
  onRetry?: () => void;
}

export default function ErrorState({
  message,
  description,
  onRetry,
}: ErrorStateProps) {
  const { t } = useTranslation();

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="flex flex-col items-center justify-center py-12 max-w-xs mx-auto text-center"
    >
      <svg
        aria-hidden="true"
        className="text-rose-400 mb-6"
        width="40" height="40" viewBox="0 0 24 24" fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          fill="currentColor" fillRule="evenodd" clipRule="evenodd"
          d="M18.486 15.286a3 3 0 0 1-3.972-.002L8.2 10.082a2 2 0 0 1 .055-2.898L12 4.774l3.745 2.412a2 2 0 0 1 .055 2.898l-6.317 5.204a3 3 0 0 1-3.972 0M12 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m0 10a1 1 0 1 0 0 2 1 1 0 0 0 0-2"
        />
      </svg>
      {message && <h2 className="text-sm font-semibold text-slate-200">{message}</h2>}
      {description && (
        <p className="text-xs text-slate-400 text-center max-w-xs">{description}</p>
      )}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="btn btn-hover min-h-11 mt-4 bg-slate-700 hover:bg-slate-600"
          aria-label={t("retry", "Retry")}
        >
          {t("retry", "Retry")}
        </button>
      )}
    </div>
  );
}
```
(Changes: `description` slot; `h3→h2`; one button grammar; `aria-live="assertive"`. Existing call sites that pass only `message`/`onRetry` remain source-compatible.)

### 4.3 i18n — delimited block, exact values

Insert into `frontend/src/i18n.ts` **after the last key of the `ro` translation object** (anchor: `"waves.title": "Valuri de schimbări",` at baseline `:565`, closing `},` at `:566`):

```ts
      // R-05 state-system keys — BEGIN (do not edit outside this block)
      "state.error.title": "Nu s-au putut încărca datele.",
      "state.error.description": "Sursa de date nu răspunde. Verifică conexiunea și încearcă din nou.",
      "state.empty.title": "Nu există date în această privire.",
      "state.empty.description": "Această secțiune nu are înregistrări în versiunea curentă a corpusului.",
      "state.empty.dataQuality": "Nu există date de acoperire de afișat.",
      "coverage.empty": "Nu există înregistrări de acoperire pentru acest domeniu.",
      "senate.history.loadError": "Acoperirea istorică a Senatului nu a putut fi încărcată.",
      "view.radar.loadError": "Matricea de aliniere la scrutin nu a putut fi încărcată.",
      "view.grafice.loadError": "Datele de coesiune și activitate nu au putut fi încărcate.",
      "view.topuri.loadError": "Clasamentul de comportament nu a putut fi încărcat.",
      "view.ideology.loadError": "Harta ideologică nu a putut fi încărcată.",
      "ageDistribution.empty": "Nu există date privind vârsta de afișat.",
      "committeeControl.loadError": "Datele privind controlul comisiilor nu au putut fi încărcate.",
      "committeeControl.empty": "Nu există date despre controlul comisiilor în această versiune.",
      "compare.empty": "Nu există partide de comparat în această versiune.",
      "person.empty": "Nu există date despre acest parlamentar.",
      "partyProfile.empty": "Nu există date despre acest partid.",
      "dashboard.loadError": "Datele panoului nu au putut fi încărcate.",
      // R-05 state-system keys — END
```

Insert the matching block into the `en` object after `"waves.title": "Switch waves",` (baseline `:1128`, closing `},` at `:1129`):

```ts
      // R-05 state-system keys — BEGIN (do not edit outside this block)
      "state.error.title": "The data could not be loaded.",
      "state.error.description": "The data source is not responding. Check the connection and try again.",
      "state.empty.title": "No data in this view.",
      "state.empty.description": "This section has no records in the current corpus release.",
      "state.empty.dataQuality": "There are no coverage records to show.",
      "coverage.empty": "There are no coverage records for this scope.",
      "senate.history.loadError": "Senate historical coverage could not be loaded.",
      "view.radar.loadError": "The roll-call alignment matrix could not be loaded.",
      "view.grafice.loadError": "Cohesion and vote-activity data could not be loaded.",
      "view.topuri.loadError": "The behavioural scorecard could not be loaded.",
      "view.ideology.loadError": "The ideological map could not be loaded.",
      "ageDistribution.empty": "There are no age records to show.",
      "committeeControl.loadError": "Committee control data could not be loaded.",
      "committeeControl.empty": "There is no committee-control data in this release.",
      "compare.empty": "There are no parties to compare in this release.",
      "person.empty": "There are no data for this member.",
      "partyProfile.empty": "There are no data for this party.",
      "dashboard.loadError": "Dashboard data could not be loaded.",
      // R-05 state-system keys — END
```

Reuse existing keys (do **not** duplicate them): `loading` (`ro:160`/`en:718`), `retry` (`:161`/`:719`), `traseismRetry` (`:255`/`:812`), `demographics.error`/`demographics.empty`, `ptimeline.loadError`/`ptimeline.empty`, `coverageLoadError`, `senate.history.noData`, `coalitions.loadError`, `coalitions.noBreakups`/`noFormations`/`noCongresses`, `empty.rollcall`, `topuri.empty`, `empty.ideology`, `ageDistributionError`, `compare.loadError`, `mpc.loadError`, `mpc.pickTwo`, `leaderboard.error`/`leaderboard.empty`, `parties.loadError`/`parties.empty`, `mps.loadError`/`mps.empty`, `committees.loadError`/`committees.empty`/`control.loadError`, `institutionalLoadError`/`committeeDataUnavailable`/`crossChamberNoData`, `chamberLoadError`/`electoralLoadError`/`noData`, `personLoadError`, `partyLoadError`, `traseismLoadError`/`waves.error`/`traseismNoRows`, `report.errorTitle`/`report.errorDesc`, `view.voturi.loadError`/`view.voturi.empty`.

### 4.4 The two usage patterns (apply mechanically)

**Pattern A — full-page early return** (Radar, Grafice, Topuri, Ideology, Voturi, CoverageView, PersonDeepDive, PartyProfile, LegislatureDetail-meta):

```tsx
import AsyncState, { resolveViewState } from "../components/ui/AsyncState";
// …
const view = resolveViewState({
  isLoading: query.isLoading,
  isError: query.isError,
  isEmpty: rows.length === 0,
});
if (view !== "ready") {
  return (
    <AsyncState
      view={view}
      pageTitle={t("view.radar.title", "Roll-call alignment matrix")}
      onRetry={() => void query.refetch()}
      errorLabel={t("view.radar.loadError")}
      emptyTitle={t("empty.rollcall")}
    />
  );
}
// existing ready-state JSX follows verbatim
```
Note `AsyncState` with no `children` renders only the state — intentional: `children` is declared optional in `AsyncStateProps` (§4.1), so this compiles. `<StateView view={view} … />` from the same module is equivalent if a stricter local lint prefers it.

**Pattern B — regional gate** (Demographics, PartyTimeline, SenateHistory, Coalitions, LiveDashboard, widget components): keep the visible `<h1>` and static controls outside; wrap each *data* region:

```tsx
<AsyncState
  view={view}
  variant="inline"
  onRetry={() => void query.refetch()}
  errorLabel={t("page.error")}
  emptyTitle={t("page.empty")}
>
  {/* existing data JSX verbatim — no inner edits required */}
</AsyncState>
```

**Rules for both patterns**
- `isEmpty` is computed from a **successfully loaded** value only: `rows.length === 0`, never `data ?? []` evaluated during pending.
- Multiple queries: `isLoading: a.isLoading || b.isLoading`, `isError: a.isError || b.isError`, `isEmpty: a.isSuccess && b.isSuccess && (rows.length === 0)`.
- `onRetry` refetches **every** failed query: `onRetry={() => { void a.refetch(); void b.refetch(); }}`.
- Never write `role="alert"`, `text-red-*`, `text-rose-*`, `text-amber-*` or a bare `"Loading…"` in a page again — those strings move into the three primitives.
- Keep existing `Suspense` fallbacks (`Skeleton`) for lazy chunks; they are not data states.

---

## 5. Numbered implementation steps (exact commands)

**Notation:** `⟨KEEP⟩` means "retain the existing JSX verbatim inside the new wrapper". Line numbers are baseline numbers; after each edit re-check with `grep -n` before the next edit.

### Step 0 — isolate, back up, prove baseline (no edits)
```bash
git -C /home/nedaktov/parlament-deschis worktree add -b repair/R-05-states /tmp/opencode/wt-R05 eb693b4
cd /tmp/opencode/wt-R05
git rev-parse HEAD                       # expect eb693b4d9faf558b22925fdb07ba6d118d7f6cef
# backup manifest — exact command and expected combined digest in §13
sha256sum $(sed -n '1,30p' /tmp/opencode/R-05-baseline.sha256 | awk '{print $2}') > /tmp/opencode/R-05-backup.sha256
sha256sum /tmp/opencode/R-05-backup.sha256 | cut -d' ' -f1   # expect 0bd63b3e22e31151b28809371463b4a86828b285265c931a77280b542d83fd41
git diff --exit-code eb693b4 -- frontend/src scripts/ui_validate.py   # exit 0, empty output
```

### Step 1 — create the shared state module (§4.1)
Write `frontend/src/components/ui/AsyncState.tsx` with the exact code from §4.1. Run CP-1 (§7).

### Step 2 — normalise the three primitives (§4.2)
Apply the exact edits to `LoadingState.tsx`, `EmptyState.tsx`, `ErrorState.tsx`. Run CP-2.

### Step 3 — add i18n keys (§4.3)
Insert both delimited blocks. Run CP-3 (key parity script).

### Step 4 — P0 pages: zero-as-fact, error-as-empty, missing retry
In the order listed; for each, apply the exact row from §6.1. After each page: `cd frontend && npx tsc --noEmit` (must exit 0) before moving on.

### Step 5 — P1 pages: normalize remaining ad-hoc states
Apply §6.2 rows. After each page, re-run `npx tsc --noEmit`.

### Step 6 — LiveDashboard widgets + components
Apply §6.3 rows. Note `CommitteeControl`/`DataQualityGauge` gain two optional props (`view?: ViewState`, `onRetry?: () => void`); when omitted they fall back to `view="empty"` only if their data is genuinely empty — never to "Loading…".

### Step 7 — optional P2 component sweep
Only with explicit authorisation; apply §6.4 rows, otherwise record as deferred.

### Step 8 — run all gates
CP-4 → CP-9 (§7) and the full §8 verification, including the 24-route UI gate and the targeted probe. Capture raw output to `/tmp/opencode/R-05-gate-logs/`.

### Step 9 — commit atomically
```bash
cd /tmp/opencode/wt-R05
git add frontend/src/components/ui/AsyncState.tsx frontend/src/components/{LoadingState,EmptyState,ErrorState}.tsx \
        frontend/src/i18n.ts frontend/src/pages frontend/src/components/{CommitteeControl,DataQualityGauge,VoteActivityChart}.tsx \
        frontend/src/components/ui/AgeDistributionSection.tsx scripts/ui_state_probe.py
git diff --cached --check                       # exit 0, empty output
git commit -m "fix(R-05): one gated loading/error/empty/data state system with retry"
```
Do **not** push, merge or deploy (owner-gated).

---

## 6. Per-page migration checklist — exact replacements

All page paths are `frontend/src/pages/`; component paths are `frontend/src/components/`. Each row: **add** the shown `view` computation after the last query declaration; **delete** the listed old blocks; **insert** the shown wrapper around the preserved markup. `t(...)` defaults are the current English literals from the audited files and may be replaced by the listed i18n key.

### 6.1 P0 — zero-as-fact / error-as-empty / no retry

| # | File | `view` computation to add | Exact old blocks to delete | Exact replacement / action |
|---|---|---|---|---|
| 1 | `Demographics.tsx` | after `:29`: `const view = resolveViewState({ isLoading: shift.isLoading, isError: shift.isError, isEmpty: rows.length === 0 });` | `:150-157` loading+error; `:214-221` empty | Wrap `:80-125` in `<AsyncState view={view} variant="inline" onRetry={() => void shift.refetch()} errorLabel={t("demographics.error")} emptyTitle={t("demographics.empty")}>`; wrap `:159-212` and `:223-230` in two more gates with the same props (drop `variant="inline"` for the table). The `rows.length > 0 &&` guards at `:112`,`:123` may stay. |
| 2 | `PartyTimeline.tsx` | after `:56`: `const view = resolveViewState({ isLoading: timeline.isLoading, isError: timeline.isError, isEmpty: rows.length === 0 });` | `:184-191` loading+error; `:263-265` empty | Gate `:114-148` (hero stats+moment), `:166-182` (gap panel), `:193-261` (table) and `:267-274` (methodology, uses `datedJoins`) with `<AsyncState view={view} … onRetry={() => void timeline.refetch()} errorLabel={t("ptimeline.loadError")} emptyTitle={t("ptimeline.empty")}>`; use `variant="inline"` for the gap panel and methodology. |
| 3 | `CoverageView.tsx` | after `:33`: `const view = resolveViewState({ isLoading: coverage.isLoading, isError: coverage.isError, isEmpty: rows.length === 0 });` | `:68-74` loading; `:76-87` error (incl. `ml-3 underline` retry) | Replace with Pattern A full-page guard using `pageTitle={t("coverageTitle")}`, `onRetry={() => void coverage.refetch()}`, `errorLabel={t("coverageLoadError")}`, `emptyTitle={t("coverage.empty")}`. Insert `<AsyncState view={view} …>` around the table region `:157-252` so `rows.length === 0` gets an honest empty state (currently absent). |
| 4 | `SenateHistory.tsx` | after `:42`: `const view = resolveViewState({ isLoading: coverage.isLoading, isError: coverage.isError, isEmpty: allRows.length === 0 });` | none to delete (there is no gating); remove the `allRows.length === 0` row at `:161-167` | Gate hero stats `:65-97` with `errorLabel={t("senate.history.loadError")}`, `emptyTitle={t("senate.history.noData")}`; gate table `:126-170` with the same props + `onRetry={() => void coverage.refetch()}`. Keep the static "Known Gaps" `:100-124` and methodology `:172-208` outside the gates. |
| 5 | `Coalitions.tsx` | after `:33`: `const view = resolveViewState({ isLoading: waves.isLoading, isError: waves.isError, isEmpty: all.length === 0 });` | `:71-80` inline loading/error; conditions `!waves.isLoading && !waves.isError` at `:81`, `:110`, `:221`, `:244`; `:144-147` breakups empty | Gate hero stats `:81-104`, moment+sparkline `:110-135`, breakups `:144-198`, formations `:206-226`, congresses `:234-249` with `<AsyncState view={view} … onRetry={() => void waves.refetch()} errorLabel={t("coalitions.loadError")} emptyTitle={…}>`; use existing `coalitions.noBreakups`/`noFormations`/`noCongresses` for each section's empty copy. Remove the `!waves.isLoading` only checks — an error must never reach an empty branch. |
| 6 | `Radar.tsx` | after `:31` (keep `dataExists`): `const view = resolveViewState({ isLoading: votesQuery.isLoading \|\| positionQueries.some(q => q.isLoading), isError: votesQuery.isError \|\| positionQueries.some(q => q.isError), isEmpty: !dataExists \|\| votes.length === 0 \|\| matrix.parties.length === 0 });` | `:87-96` Skeleton loading; `:98-105` red error | Pattern A full-page guard; `pageTitle={t("view.radar.title")}` (preserve the sr-only h1), `onRetry={() => { void votesQuery.refetch(); positionQueries.forEach(q => void q.refetch()); }}`, `errorLabel={t("view.radar.loadError")}`, `emptyTitle={t("empty.rollcall")}`. Keep `:122-126` inside the ready branch as the empty guard — now unreachable when empty, so delete it and let `AsyncState` own it. |
| 7 | `Grafice.tsx` | after `:23`: `const view = resolveViewState({ isLoading: summaryQuery.isLoading \|\| cohesionQuery.isLoading, isError: summaryQuery.isError \|\| cohesionQuery.isError, isEmpty: !cohesionExists \|\| cohesion.length === 0 });` | `:25-33` loading; `:35-41` error; `:58-62` empty guard | Pattern A; `pageTitle={t("view.grafice.title")}`, retry both queries, `errorLabel={t("view.grafice.loadError")}`, `emptyTitle={t("empty.rollcall")}`. Keep `VoteActivityChart` (`:169`) in the ready branch — its own state handling is fixed in §6.3. |
| 8 | `Topuri.tsx` | after `:29`: `const view = resolveViewState({ isLoading: scorecardQuery.isLoading, isError: scorecardQuery.isError, isEmpty: !dataExists \|\| entries.length === 0 });` | `:31-40` loading; `:42-49` error; `:84-100` dead inline states | Pattern A; `pageTitle={t("view.topuri.title")}`, `onRetry={() => void scorecardQuery.refetch()}`, `errorLabel={t("view.topuri.loadError")}`, `emptyTitle={dataExists ? t("topuri.empty") : t("empty.rollcall")}`. Keep the minimum-votes input `:65-82` in the ready branch. |
| 9 | `Ideology.tsx` | after `:55`: `const view = resolveViewState({ isLoading: ideologyQuery.isLoading, isError: ideologyQuery.isError, isEmpty: !dataExists \|\| filteredData.length === 0 });` | `:187-195` loading; `:197-203` error; `:205-223` empty branch | Pattern A; `pageTitle={t("view.ideology.title")}`, `onRetry={() => void ideologyQuery.refetch()}`, `errorLabel={t("view.ideology.loadError")}`, `emptyTitle={t("empty.ideology")}`. **Keep the `useEffect` at `:102-185` unconditionally above the guard** (hook order); `containerRef.current` is null in pending states and the effect already early-returns. Do not touch the `?? 0` scatter values (FN-4, out of scope). |
| 10 | `LiveDashboard.tsx` | per query group: `statsView`, `partiesView`, `committeeView`, `coverageView`, `crossView` using `resolveViewState` with the corresponding query and `isEmpty` from the loaded array/object | `:96-142` raw `?? "--"` cards; `:168-183` fake fallback widget props; `:193-213` Suspense skeletons (keep) | Gate each hero-card group and each widget region with `<AsyncState view={…} variant="inline" onRetry={…} errorLabel={t("dashboard.loadError")} />`; pass `view` and `onRetry` into `CommitteeControl`, `DataQualityGauge` (new optional props). Delete the fabricated `{ as_of: clamped, total_committees: 0, parties: [], chairs: [] }` fallback at `:175` and `stats?.committees ?? 0` at `:176`. Keep `Suspense` skeletons (lazy chunks, not data states). |

### 6.2 P1 — remaining page state branches

| # | File | Exact old blocks | Exact replacement |
|---|---|---|---|
| 11 | `PartyComparison.tsx` | `:176-183` loading/error (only `parties` query) | Compute one `view` over `parties`, `ages`, `control` (`isEmpty: parties.isSuccess && partyList.length === 0`) and gate the selector+table region with `<AsyncState view={view} onRetry={() => { void parties.refetch(); void ages.refetch(); void control.refetch(); }} errorLabel={t("compare.loadError")} emptyTitle={t("compare.empty")} />`. Do **not** change the `"0"` chair fallback at `:109-110` (FN-4 — separate recipe). |
| 12 | `MpComparison.tsx` | `:249-254` loading/error; `:320-324` "pick two" | Add `view` over `pool` (`isEmpty: pool.isSuccess && poolList.length === 0`); gate hero `:155-179` and the comparison area `:256-324` with `errorLabel={t("mpc.loadError")}` and `emptyTitle={t("mpc.pickTwo")}`; retry via `pool.refetch()`. Hero `poolList.length` must not render while pending. |
| 13 | `SwitchLeaderboard.tsx` | `:125-132` loading/error | Add `view`; gate hero stats `:63-80` and table `:134-219` with `errorLabel={t("leaderboard.error")}`, `emptyTitle={t("leaderboard.empty")}`, retry. Keep `:119-123` scope note outside the gate. |
| 14 | `Parties.tsx` | `:85-89` inline error (no retry) | Keep shared `LoadingState`/`EmptyState` calls but replace the error div with `<StateView view="error" onRetry={() => void partiesQuery.refetch()} errorLabel={t("parties.loadError")} />`; or migrate the whole section to one `<AsyncState view={…}>`. Preserve the `filtered.length === 0` empty check (it is a *search filter* empty, still distinct from error). |
| 15 | `Mps.tsx` | `:163-167` bespoke error panel | Replace with `<StateView view="error" onRetry={() => void cards.refetch()} errorLabel={t("mps.loadError")} />`; keep `:160-162` and `:205-207`. |
| 16 | `Committees.tsx` | `:110-114` member error; `:341-345` amber control error; `:365-369` list error | Replace each with `StateView view="error"` + retry (`members.refetch`, `control.refetch`, `list.refetch`) and the existing keys `committees.loadError`/`control.loadError`. Keep `:362-364` LoadingState and `:381-388` EmptyState (both already shared). |
| 17 | `InstitutionalView.tsx` | `:49-68` committee ternary; `:79-90` cross-chamber ternary including `ml-3 underline` retries | Convert each ternary to `<AsyncState view={committeeView/crossView} … onRetry={() => void committees.refetch()/crossChamber.refetch()} errorLabel={t("institutionalLoadError")} emptyTitle={t("committeeDataUnavailable")/t("crossChamberNoData")}>⟨KEEP data JSX⟩</AsyncState>`. |
| 18 | `LegislatureDetail.tsx` | `:39-50` meta error; `:109-134` chamber ternary; `:139-184` movements ternary | Replace meta early-return with Pattern A; convert the two ternaries to `AsyncState` with `onRetry` to `chamber.refetch()`/`movements.refetch()` and existing keys. Replace the permanent pulse at `:188-193` with the `Suspense` fallback already used elsewhere (`<Skeleton className="h-64 w-full" />`) — it is a chunk placeholder, not a data state. Keep `?? "--"` hero values inside the ready branch. |
| 19 | `PersonDeepDive.tsx` | `:75-82` loading; `:84-94` bespoke error | Pattern A with `pageTitle={t("personDeepDive.title")}`, `onRetry={() => void person.refetch()}`, `errorLabel={t("personLoadError")}`, `emptyTitle={t("person.empty")}` for the `!p` case after success. |
| 20 | `PartyProfile.tsx` | `:57-63` loading; `:65-74` bespoke error; `:154-166` movements ternary | Pattern A for the page; `AsyncState` for movements with `onRetry={() => void movements.refetch()}` and `emptyTitle={t("noData")}`. Do not change `?? 0` at `:78` (FN-4). |
| 21 | `Traseism.tsx` | local `ErrorState` `:107-132`; loading `:339-340`, `:617-618`, `:833-835`, `:921-922`; waves error `:620-622` | Delete the local component and `import ErrorState from "../components/ErrorState";`. Replace every `<ErrorState onRetry={…} />` call site (`:342`, `:838`, `:924`) with shared `ErrorState` (API-compatible). Convert each loading/error pair to one `AsyncState`/`StateView` with the same `onRetry`; use `traseismLoadError` / `waves.error` / `traseismNoRows`. |
| 22 | `Report.tsx` | `:158-195` bespoke loading; `:196-230` bespoke error | Normalise to `<AsyncState view={reportView} pageTitle={t("report.title")} onRetry={() => void report.refetch()} errorLabel={t("report.errorTitle")} errorDescription={t("report.errorDesc")} />`. **Behaviour already correct — preserve the retry and the `role="alert"`/`role="status"` semantics.** Keep `report.loadingTitle`/`loadingDesc` as `loadingLabel`/`loadingDescription` if desired. |
| 23 | `Voturi.tsx` | `:40-50` Skeleton+inline loading; `:52-59` shared ErrorState | Convert both to one `AsyncState` with `pageTitle={t("view.voturi.title")}`, `onRetry={() => void votesQuery.refetch()}`, `errorLabel={t("view.voturi.loadError")}`, `emptyTitle={t("view.voturi.empty")}`. |

### 6.3 Widget components

| # | File | Exact old blocks | Exact replacement |
|---|---|---|---|
| 24 | `CommitteeControl.tsx` | `:43-52` perpetual "Loading committee data..." | Add `view?: ViewState; onRetry?: () => void` to `CommitteeControlProps`; import `StateView` from `./ui/AsyncState`; replace the block with `if (view && view !== "ready") return <StateView view={view} variant="inline" onRetry={onRetry} errorLabel={t("committeeControl.loadError")} emptyTitle={t("committeeControl.empty")} />;` followed by `if (!parties?.length) return <StateView view="empty" variant="inline" emptyTitle={t("committeeControl.empty")} />;`. Add `useTranslation`. |
| 25 | `DataQualityGauge.tsx` | `:57-66` "Loading..." | Add `view?: ViewState; onRetry?: () => void` props and the same `StateView` early return with `emptyTitle={t("state.empty.dataQuality")}`. Remove the literal "Loading…"; `stats === null` now means *empty*, never *loading*. |
| 26 | `AgeDistributionSection.tsx` | `:15-17` Skeleton; `:18-20` red error | Replace with one `AsyncState view={resolveViewState({ isLoading: shift.isLoading, isError: shift.isError, isEmpty: cohorts.length === 0 })} onRetry={() => void shift.refetch()} errorLabel={t("ageDistributionError")} emptyTitle={t("ageDistribution.empty")}>` wrapping the radial block `:29-35`. Compute `cohorts` before the guard (already the case at `:22-27`). |
| 27 | `VoteActivityChart.tsx` | `:179-193` inline error; `:195` inline loading; `:200` empty | Use one `AsyncState` with `activityQuery` state and `onRetry={() => void activityQuery.refetch()}`, `errorLabel={t("view.grafice.activityLoadError")}`, `emptyTitle={t("view.grafice.activityEmpty")}`. **Keep the effect guard at `:64` and its dependency at `:168`** (`activityQuery.isError`) unchanged. |

### 6.4 P2 component sweep — authorised only

| File | Lines | Replacement (uniform) |
|---|---|---|
| `RollCallTable.tsx` | loading `:44-52`, error `:53-61`, empty `:62-…` | Already imports shared `ErrorState` (`:4`); replace all three with one `AsyncState` using `query`, `dataExists`, `onRetry={() => void query.refetch()}`, keys `view.voturi.loadError` / `view.voturi.empty`. |
| `PersonDrawer.tsx` | loading `:118`, error `:119-121`, empty `:192` | `StateView`/`AsyncState` with `variant="inline"`; retry `person.refetch()`. |
| `ChamberView.tsx` | loading `:32`, error `:33-35` | `AsyncState` + `data.refetch()`. |
| `Search.tsx` | loading/error `:101-106`, empty `:107-…` | `AsyncState`; keep combobox keyboard behaviour; retry `results.refetch()`. |
| `SankeyFlow.tsx` | loading `:163-173`, error `:174-…` | `AsyncState`; preserve `empty` derivation at `:152` and effect deps at `:161`. |
| `LiveFeed.tsx` | loading `:193`, error `:194-196`, empty `:216` | `AsyncState`; retry `events.refetch()`. |
| `TimelineChart.tsx` | loading `:225-229`, error `:230-236`, empty `:238-240` | `AsyncState`; keep the effect at `:214` and the `empty` derivation at `:99`. |
| `About.tsx` | error `:206-…`, loading/empty text at `:240`, `:265-267`, `:330-332` | `AsyncState`; retry `about.refetch()`. |

---

## 7. CHECKPOINTS (exact command + expected output + exit)

| CP | When | Exact command (run from the worktree root unless stated) | Expected output | Exit |
|---|---|---|---|---:|
| CP-1 | after Step 1 | `cd frontend && npx tsc --noEmit` | no diagnostics | 0 |
| CP-2 | after Step 2 | `cd frontend && npm run lint` | `tsc --noEmit` clean; ESLint reports **zero errors** (pre-existing warnings permitted, as in G03) | 0 |
| CP-3 | after Step 3 | `python3 - <<'PY'` (parity script in §8.4) | `I18N PARITY PASS: ro=en, R-05 block keys present in both locales` | 0 |
| CP-4 | after each P0/P1 page | `cd frontend && npx tsc --noEmit` | no diagnostics | 0 |
| CP-5 | after all pages | `grep -RInE 'text-(red|rose|amber)-[0-9]{3}|ml-3 underline|Loading committee data|Loading\.\.\.' frontend/src/pages frontend/src/components/ui/AgeDistributionSection.tsx frontend/src/components/CommitteeControl.tsx frontend/src/components/DataQualityGauge.tsx \|\| true` | **empty output** in pages/widgets except legitimate amber *warnings* (e.g. `PartyTimeline.tsx:169`, `Leaderboard.tsx:120`, `LegislatureDetail.tsx:151`) and semantic event colours (e.g. `PersonDeepDive.tsx:16-22`, `PartyProfile.tsx:173`, `LegislatureDetail.tsx:168`) — review each remaining hit and record why it is not a data-state message | 0 |
| CP-6 | after all pages | `grep -RIn 'data-state=' frontend/src/components/ui/AsyncState.tsx` | one hit: `data-state={view}` | 0 |
| CP-7 | after Step 8 | `cd frontend && npm run build` | `✓ built in …s`, exit 0 | 0 |
| CP-8 | after servers up | `python3 scripts/ui_validate.py http://127.0.0.1:5180` | `UI VALIDATION PASS: 24 routes, zero JavaScript errors, zero axe violations` | 0 |
| CP-9 | after probe written | `python3 scripts/ui_state_probe.py http://127.0.0.1:5180` | `STATE PROBE PASS: 9 routes × 3 scenarios, 0 failures` | 0 |
| CP-10 | final | `bash scripts/check-doc-truth.sh` | `false-claims: 0` | 0 |
| CP-11 | final | `git diff --check` | empty output | 0 |

**On any non-zero CP:** stop, fix the cause, re-run from the failing CP. Do not proceed to the next page with a red type-check.

---

## 8. Verification gates

### 8.1 Lint and build (G03/G04 parity)

```bash
cd /tmp/opencode/wt-R05/frontend
npm run lint      # CP-2 — expected exit 0; ESLint warnings may remain (G03 baseline: 7 warnings, 0 errors)
npm run build     # CP-7 — expected exit 0, "✓ built in …s"
```
CI parity: `.github/workflows/ci.yml:36-41` runs exactly these two after `npm ci`. A green local run is necessary but not sufficient — the UI gate below is mandatory.

### 8.2 UI gate — 24/24, zero axe, zero JavaScript errors (G08 parity)

Start the two servers exactly as in §3.4, then:

```bash
cd /tmp/opencode/wt-R05
python3 scripts/ui_validate.py http://127.0.0.1:5180
```

Expected (one line per route, all `OK`):
```
[OK ] overview            /                                          rendered              0 js-err  0 axe
…
UI VALIDATION PASS: 24 routes, zero JavaScript errors, zero axe violations
```
Exit **0**. Any `FAIL`, any non-zero axe count, any `console.error`/`pageerror`, any `error boundary shown`, or a scan error → gate RED; fix and re-run. The script itself exits 1 on any finding (`scripts/ui_validate.py:174-178`). Never report a pass from an earlier run after a later edit.

**Evidence discipline:** if Playwright/Chromium or the API proxy is unavailable, record G08 as **NOT PROVEN** in the verdict and attach the failure output; do not downgrade it to "waived".

### 8.3 Targeted route probes — NEW `scripts/ui_state_probe.py`

The 24-route gate scans the *settled* UI. It does **not** prove that loading/error/empty states are honest. This probe intercepts `/api/**` and asserts the three pending states on the highest-risk routes. Create it with this exact content:

```python
"""Targeted state-system probe for R-05 (companion to scripts/ui_validate.py).

For each route, three scenarios:
  abort  -> [data-state="error"] + retry control + NO [data-state="empty"]
  slow   -> [data-state="loading"] and no "0"/"0%" inside [data-moment]
  empty  -> [data-state="empty"] + NO [data-state="error"] + no retry control

Usage: python3 scripts/ui_state_probe.py [base_url]
Requires system python3 with playwright + /usr/bin/chromium (same as ui_validate.py).
"""
from __future__ import annotations

import asyncio
import re
import sys
from urllib.parse import urlparse

from playwright.async_api import async_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5180").rstrip("/")
AXE_PATH = "/tmp/axe.min.js"

ROUTES = [
    ("demographics", "/demographics"),
    ("party-timeline", "/party-timeline"),
    ("coverage", "/coverage"),
    ("senate-history", "/senate-history"),
    ("coalitions", "/coalitions"),
    ("radar", "/radar"),
    ("grafice", "/grafice"),
    ("topuri", "/topuri"),
    ("ideology", "/ideology"),
]

RETRY = re.compile(r"retry|re[îi]ncearc|try again", re.I)
ZERO = re.compile(r"^\s*0+(?:[.,]0+)?%?\s*$")


def _empty_body(path: str) -> str:
    # /coverage/detailed returns a bare array; other endpoints wrap in {data: []}.
    if "/coverage/detailed" in path:
        return "[]"
    return '{"status":"ok","data":[],"data_exists":false,"count":0}'


async def _probe(browser, name: str, route: str, mode: str) -> list[str]:
    errors: list[str] = []
    page = await browser.new_page()

    async def abort(route_):
        await route_.abort()

    async def slow(route_):
        await asyncio.sleep(2.0)
        await route_.continue_()

    async def empty(route_):
        await route_.fulfill(
            status=200,
            content_type="application/json",
            body=_empty_body(urlparse(route_.request.url).path),
        )

    await page.route("**/api/**", {"abort": abort, "slow": slow, "empty": empty}[mode])
    try:
        await page.goto(BASE + route, wait_until="domcontentloaded", timeout=30_000)
        if mode == "abort":
            await page.wait_for_selector('[data-state="error"]', timeout=8_000)
            if await page.locator('[data-state="empty"]').count():
                errors.append("error branch also rendered empty copy")
            if not await page.get_by_role("button", name=RETRY).count():
                errors.append("error branch has no retry control")
        elif mode == "slow":
            await page.wait_for_selector('[data-state="loading"]', timeout=2_000)
            for moment in await page.locator("[data-moment]").all():
                if ZERO.match((await moment.inner_text()) or ""):
                    errors.append("zero rendered as a fact while loading")
        else:
            await page.wait_for_selector('[data-state="empty"]', timeout=8_000)
            if await page.locator('[data-state="error"]').count():
                errors.append("empty branch also rendered error copy")
            if await page.get_by_role("button", name=RETRY).count():
                errors.append("empty branch offers retry (error/empty conflated)")
        # No axe regressions in any of the three pending states.
        await page.add_script_tag(path=AXE_PATH)
        violations = await page.evaluate(
            "async () => (await axe.run(document, {resultTypes:['violations']}))"
            ".violations.map(v => v.id)"
        )
        if violations:
            errors.append("axe: " + ", ".join(violations))
    except Exception as exc:  # noqa: BLE001 - probe must report, never crash
        errors.append(f"{mode}: {str(exc)[:160]}")
    finally:
        await page.close()
    return errors


async def main() -> int:
    failures = 0
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path="/usr/bin/chromium", args=["--no-sandbox"]
        )
        for name, route in ROUTES:
            route_errors: list[str] = []
            for mode in ("abort", "slow", "empty"):
                for msg in await _probe(browser, name, route, mode):
                    route_errors.append(f"[{mode}] {msg}")
            status = "OK " if not route_errors else "FAIL"
            failures += len(route_errors)
            print(f"[{status}] {name:16s} {route:22s} {len(route_errors)} findings")
            for msg in route_errors:
                print("   - " + msg)
        await browser.close()
    if failures:
        print(f"\nSTATE PROBE FAIL: {failures} findings")
        return 1
    print(f"\nSTATE PROBE PASS: {len(ROUTES)} routes × 3 scenarios, 0 failures")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

**Expected output** (9 lines of `[OK ]` followed by):
```
STATE PROBE PASS: 9 routes × 3 scenarios, 0 failures
```
Exit **0**. Any finding is a genuine state-system defect; fix the page, not the probe (unless the probe itself mis-models an endpoint — then document the correction in the verdict).

> Note: `retry: 1` in `frontend/src/router.tsx:571` means the abort scenario needs the 8 s wait; do not shorten it. Each probe uses a fresh browser page, so the 1-hour `staleTime` (`:569`) cannot leak cached data between scenarios.

### 8.4 i18n parity check (CP-3)

```bash
cd /tmp/opencode/wt-R05 && python3 - <<'PY'
import re
src = open("frontend/src/i18n.ts", encoding="utf-8").read()
blocks = re.findall(r"// R-05 state-system keys — BEGIN.*?\n(.*?)// R-05 state-system keys — END", src, re.S)
assert len(blocks) == 2, f"expected ro+en blocks, got {len(blocks)}"
def keys(b): return set(re.findall(r'^\s*"([^"]+)":', b, re.M))
ro, en = map(keys, blocks)
assert ro == en, f"parity failure: ro-only={ro-en}, en-only={en-ro}"
assert len(ro) == 18, f"expected 18 keys, got {len(ro)}"
print("I18N PARITY PASS: ro=en, R-05 block keys present in both locales")
PY
```
Expected exit **0** and the exact printed line above.

### 8.5 Full gate sequence (record all outputs)

```bash
cd /tmp/opencode/wt-R05
cd frontend && npm run lint && npm run build && cd ..
python3 scripts/ui_state_probe.py http://127.0.0.1:5180
python3 scripts/ui_validate.py http://127.0.0.1:5180
bash scripts/check-doc-truth.sh
git diff --check
```
All five exit 0. If the local API cannot be started, mark CP-8/CP-9 and the corresponding gates **NOT PROVEN** with the captured error.

---

## 9. Acceptance criteria

- **AC-1 (precedence):** every one of the 23 pages + 4 widgets listed in §6 computes `view` via `resolveViewState()`; there is no remaining `isLoading && …` / `isError && …` / `length === 0` triple duplicated inside a page. Prove with CP-5/CP-6.
- **AC-2 (no zero as fact):** the slow-mode probe finds no `0`/`0%` inside `[data-moment]` on any of the 9 probed routes; no hero `InfoStat`/`DashboardCard` with value 0 is mounted before `view === "ready"`.
- **AC-3 (error ≠ empty):** abort-mode probe shows `[data-state="error"]` and no `[data-state="empty"]`; empty-mode probe shows the reverse. Every visible error string differs from the corresponding empty string (compare the ro/en key tables in §4.3).
- **AC-4 (retry everywhere):** every `StateView`/`AsyncState` error branch passes `onRetry` wired to `refetch()`; no bare `text-red-*`/`role="alert"` error div remains in the files of §2.1 (CP-5). Probe confirms a retry control in abort mode on all 9 routes.
- **AC-5 (one look):** all pending states render through `StateView`; same `py-12`/`py-6` shell, same `btn btn-hover min-h-11`, one `role="status"` loading, one `role="alert"` error, `data-state` on every pending root.
- **AC-6 (a11y):** UI gate is 24/24 with zero axe violations and zero JavaScript errors; the probe's axe check is clean in loading, error and empty states (not only the settled state).
- **AC-7 (i18n):** CP-3 passes; no English fallback leaks into the ro locale for any R-05 key.
- **AC-8 (honesty preserved):** this recipe did not change any metric definition, denominator, label or data value; it only moved rendering behind gates. Report/Committees retry behaviour is preserved (TRIAD positive pattern).
- **AC-9 (evidence):** all gate outputs saved under `/tmp/opencode/R-05-gate-logs/` and summarised with exact commands/exits in the implementer's verdict document. A gate that could not run is listed under NOT PROVEN.

---

## 10. Dependencies

| Dependency | Nature | Required before |
|---|---|---|
| Baseline `eb693b4` + clean worktree | hard | Step 0 |
| `frontend/node_modules` installed (`npm ci`) | hard | CP-1/2/3, build |
| System `python3` + `playwright` + `/usr/bin/chromium` + `/tmp/axe.min.js` | hard for UI gates | §8.2/§8.3 (otherwise NOT PROVEN) |
| Local API (copied DB) + Vite with `/api` proxy on 5180 | hard for UI gates | §8.2/§8.3 |
| `react-i18next` `useTranslation` | already a dependency (`frontend/package.json`) | §4.1/§4.2 |
| X4 i18n sweep recipe | **soft / coordination** — must not touch the R-05 delimited block | merge order |
| AP-1/AP-2 visual-primitive recipe | **soft / coordination** — must not touch the 3 state primitives or `index.css` | merge order |
| FN-4 unknown-as-zero recipe | **soft** — R-05 gates the view; that recipe fixes the underlying `?? 0` values | follow-up |
| Nav/route cleanup (X5) | none — all 9 probe routes are already in `ui_validate.py:47-75` | n/a |

No backend, database, dataset or deployment change is required or permitted by this recipe.

---

## 11. Side-quest policy

**Do not fix, in this recipe:**
- FN-1 (`date`/`as_of` URL veneer), FN-2 (switch definitions), FN-3 (page-local slices labelled corpus totals), FN-4 (unknown/null coerced to 0), FN-6 (provenance), FN-7 (state in URL), FN-8 (vote scope), FN-9 (mislabelled reporting metrics). These are separate content-honesty recipes; R-05 only *gates* their outputs.
- X4's pre-existing missing keys elsewhere in `i18n.ts` (dozens of `t(key, "English…")` calls) — add only the 18 R-05 keys in the delimited block.
- AP-1/AP-2 visual bugs (`HeroGraphic` colours, `DataBar` hex-in-className, `ProgressRing` SVG paint, radial clipping) — different owners.
- TA-* tactile issues (retry button touch targets are improved only insofar as the shared button gains `min-h-11`; tooltips, keyboard-scroll wrappers, focus traps are out of scope).
- The "Ideology not yet ingested" note at `Ideology.tsx:320-323` (X8) — leave it; another recipe conditions it on `dataExists`.
- Any server/deploy/branch-protection action. No push, no merge, no deploy.
- Any edit to `frontend/src/index.css` — reuse existing utilities only.

If an implementer discovers a defect outside R-05 scope, record it as a finding in the verdict (file:line, recipe id, owner) and continue. If an out-of-scope defect **blocks** a gate (e.g. an existing axe violation on a probed route), stop and escalate rather than fixing it silently.

---

## 12. ROLLBACK

Atomic, per-file, no history rewriting:

```bash
cd /tmp/opencode/wt-R05
# Full rollback of every R-05-owned tracked file to the verified baseline:
git checkout eb693b4 -- \
  frontend/src/components/LoadingState.tsx \
  frontend/src/components/EmptyState.tsx \
  frontend/src/components/ErrorState.tsx \
  frontend/src/i18n.ts \
  frontend/src/pages/Demographics.tsx frontend/src/pages/PartyTimeline.tsx \
  frontend/src/pages/CoverageView.tsx frontend/src/pages/SenateHistory.tsx \
  frontend/src/pages/Coalitions.tsx frontend/src/pages/Radar.tsx \
  frontend/src/pages/Grafice.tsx frontend/src/pages/Topuri.tsx \
  frontend/src/pages/Ideology.tsx frontend/src/pages/LiveDashboard.tsx \
  frontend/src/pages/PartyComparison.tsx frontend/src/pages/MpComparison.tsx \
  frontend/src/pages/SwitchLeaderboard.tsx frontend/src/pages/Parties.tsx \
  frontend/src/pages/Mps.tsx frontend/src/pages/Committees.tsx \
  frontend/src/pages/InstitutionalView.tsx frontend/src/pages/LegislatureDetail.tsx \
  frontend/src/pages/PersonDeepDive.tsx frontend/src/pages/PartyProfile.tsx \
  frontend/src/pages/Traseism.tsx frontend/src/pages/Report.tsx \
  frontend/src/pages/Voturi.tsx \
  frontend/src/components/CommitteeControl.tsx \
  frontend/src/components/DataQualityGauge.tsx \
  frontend/src/components/VoteActivityChart.tsx \
  frontend/src/components/ui/AgeDistributionSection.tsx
rm -f frontend/src/components/ui/AsyncState.tsx scripts/ui_state_probe.py
sha256sum -c /tmp/opencode/R-05-baseline.sha256 | grep -c ': OK'   # expect 30
cd frontend && npx tsc --noEmit   # exit 0
```

For a partial rollback (single page), use `git checkout eb693b4 -- <that one file>` and re-run CP-4 → CP-7.

If a commit was already made: `git revert <R-05 commit>` (never `reset --hard` on a shared branch). If a server was started for gates, stop the exact PIDs recorded in the gate log (baseline evidence stopped ports 8101/5180 — `docs/GATE-EVIDENCE-2026-11-21.md:236-246`).

---

## 13. BACKUP + checksum

Baseline manifest (SHA-256, 30 owned files, captured at `eb693b4` by the author):

```text
f4e33a245fb76e59dad20ec8551e5df018962fc7ce4f626bc6616df6559cea86  frontend/src/components/LoadingState.tsx
c97a9f7669ed3fabeb28670ea8e2ba3ad998c8158d24d40dea4229bc92bb1d8e  frontend/src/components/EmptyState.tsx
b305c8ff3896d3eb6bbb17248b577a3ae7558a58c2cb49a3f25218e3c40d6020  frontend/src/components/ErrorState.tsx
30ff9b8a9fe2cbcef47a1b2f833207d08257ac08a78ec8230b86be479cdd07cd  frontend/src/i18n.ts
153410d28c26b9d112be4e9330564fc6b0700c2e7b83cfeebeba1fb1d9efbcfd  frontend/src/pages/Demographics.tsx
5add25969f232c2daabfe2742770561fe8262bf70b78749e2d6238181901888e  frontend/src/pages/PartyTimeline.tsx
fcb2069c25be7f2266573a3c221fcbda345bbecfc6959894e2f62ebb8de8669d  frontend/src/pages/CoverageView.tsx
282639853d871da3b0d00dfd92bee80d21c94905db4fd8edfebf7158dbb79a06  frontend/src/pages/SenateHistory.tsx
ef88a40c2c71b9497bceb980f97ab0bb42e61c8bb9ce2493f3ac8825c1e0660e  frontend/src/pages/Coalitions.tsx
fef5f87983d7325ad297a65e64536ae5e3d7ea95fed250ea60fe78b379a7627e  frontend/src/pages/Radar.tsx
9d94309f7c93277beb34a6603c750fe9ee3afcfa27cd3266355c89b79eeccdc7  frontend/src/pages/Grafice.tsx
a07a2a4e2e59c038e17a19ae3f38a8322aac0574a2100d926330e25dcfe9d8d7  frontend/src/pages/Topuri.tsx
a1ce44e2223365d286523ba76fe3054214677f2bdf0df19ae3bf210c8b17df4f  frontend/src/pages/Ideology.tsx
2d2a81ca9710b9a4890a2d5c8f6b8543c4dc0fbb260486e367ca454fb7cd963e  frontend/src/pages/LiveDashboard.tsx
81d08e4a2a746295651ef4b8fd21c113489ac08fc590bfb969e39caa87c7cd51  frontend/src/components/CommitteeControl.tsx
d8ca67e962f3ec952c4fd37a4e5c054f837061a37086e0bb2125e05e421f4116  frontend/src/components/ui/AgeDistributionSection.tsx
56b8c7353118d79905910e76750aaa9f6fc84a7bb31479e293049af109770d7a  frontend/src/components/DataQualityGauge.tsx
a9b1c31624a006b4f5b574adf5def2c42ce55f0272e6bbbdd26524b4b7ec4755  frontend/src/pages/PartyComparison.tsx
03a548291eb337b4c46cb8540e2f47db490d38589ec7a66cbe16a68ff833d44f  frontend/src/pages/MpComparison.tsx
0521f789e88a609c7c674cf0cddc84d5a80bce860dd9e9a05a67f686f24938fe  frontend/src/pages/SwitchLeaderboard.tsx
339d5361855b27d37072437af68c3e6fe3715841334577af9036f74c6adddc2f  frontend/src/pages/Parties.tsx
df4529b1dd752f6069cd4644934654768f07e940aee124f6703bba7f281b7d33  frontend/src/pages/Mps.tsx
72dea7c418674018f2fed1f1e1f8b435376b76ab703efa2a00eeb658adaae319  frontend/src/pages/Committees.tsx
28760bbf407819abeca4241fc51dbd63a3bd0892917636c6fa6503e8894fa22c  frontend/src/pages/InstitutionalView.tsx
305842ddac7e4cacc300f6477a1a779a5be1df104f119fa6de3eb54e38570d46  frontend/src/pages/LegislatureDetail.tsx
0c2adbfab1064568734cf12903d0b8d4f063f9a768cc7722e7971527b974cc35  frontend/src/pages/PersonDeepDive.tsx
9dc15ee50f68cce6596d9e007a7e34a8cca46a1440380108470e7ef924fb296c  frontend/src/pages/PartyProfile.tsx
6d7c753115d52b4e265f1f5aded775b0f735f20fe3ce622bdb9fe7b433c137d5  frontend/src/pages/Traseism.tsx
d6affe721101e7a0dbc23026dd375d7b9f048a7ac9a5f5b723a120f6dc407f13  frontend/src/pages/Report.tsx
1dc2cd39de71a267c4aaebb62ef45d3fd4bfec0d8162107b5e09a59b86018c4c  frontend/src/pages/Voturi.tsx
```

Recreate and verify at implementation time:

```bash
cd /tmp/opencode/wt-R05
# author's baseline manifest is already at /tmp/opencode/R-05-baseline.sha256
sha256sum -c /tmp/opencode/R-05-baseline.sha256 | grep -c ': OK'    # expect 30
sha256sum /tmp/opencode/R-05-baseline.sha256 | cut -d' ' -f1          # expect 0bd63b3e22e31151b28809371463b4a86828b285265c931a77280b542d83fd41
git rev-parse HEAD                                                   # expect eb693b4d9faf558b22925fdb07ba6d118d7f6cef
```
Keep a copy of the manifest outside the worktree (`/tmp/opencode/…`) so rollback is possible even if the worktree is deleted.

---

## 14. NOT PROVEN

Everything below is a **static-code / plan** claim made by the author of this recipe. An implementer must convert each into observed evidence or explicitly mark it NOT PROVEN in the verdict:

1. **No browser render, screenshot, computed-style or contrast measurement** was performed by this recipe's author. All styling/contrast statements are CSS-semantics inferences from `frontend/src/index.css:171-184,198-201` and the audit's arithmetic.
2. **No axe run, no Playwright route run** was performed here. CP-8/CP-9 and §8.2/§8.3 expected outputs are targets copied from the *historical* G08 evidence (`docs/GATE-EVIDENCE-2026-11-21.md:27`), not fresh results. They are **NOT PROVEN** for the post-change tree.
3. **The new code in §4 and the probe in §8.3 were not executed or compiled** by the author. TypeScript/ESLint/Playwright compatibility must be established by CP-1/CP-2/CP-9.
4. **The abort/slow/empty scenarios were not exercised** against a live API. Whether every probed endpoint honours the generic empty body in `_empty_body()` (`{"data":[],"data_exists":false}`) is a hypothesis; if an endpoint needs a different shape, the probe must be corrected *and the correction documented*.
5. **The 24-route gate's historical PASS** is evidence about the baseline tree only (`docs/GATE-EVIDENCE-2026-11-21.md:27`, `docs/COMPREHENSIVE-REVIEW-2026-11-21.md:43`); the note at `docs/AUDIT-RESOLUTIONS-2026-11-21.md:33` records that a fresh agent once got 23/24 against the live API proxy because `/api/analytics/ideology` 404s. R-05 does not fix that backend condition; if it recurs, report it — do not mask it by weakening the probe.
6. **The claim that removing `<h1>` from a data region cannot break headings** is an inference; axe must confirm (the sr-only `pageTitle` in `StateView` is the mitigation).
7. **The P2 component sweep (§6.4) was not authorised or executed**; those files remain untouched by this recipe.
8. **No deployment, production parity, mobile/touch, print or keyboard walk** was performed. Production behaviour of the new states remains NOT PROVEN until deployed and re-probed by the owner.

---

## See also

`Parlament Deschis Obsidian vault/40-FRONTEND/TRIAD-AUDIT-2026-11-21.md` · `…/FRONTEND-AUDIT-2026-11-21.md` · `docs/GATE-EVIDENCE-2026-11-21.md` · `docs/CONTINUATION-STRATEGY-2026-11-21.md` · `docs/COMPREHENSIVE-REVIEW-2026-11-21.md` · `docs/remediation/REMEDIATION-STRATEGY.md`
