# R-06 — Tactile Semantics & Accessibility — strategy + implementation recipe

| Field | Value |
| --- | --- |
| Agent | STRATEGY/RECIPE R-06 (Tactile Semantics & Accessibility) |
| Date | 2026-11-21 |
| Task type | **Design only.** No product code was edited by this agent. |
| Input vault note | `Parlament Deschis Obsidian vault/40-FRONTEND/TRIAD-AUDIT-2026-11-21.md` (TA-1…TA-8) |
| Baseline requested | `main` @ `eb693b4` |
| Baseline observed | `eb693b4` = `Merge pull request #69 from nedaktov-ops/docs/triad-audit`; local `main` = `1d60492`; working HEAD = `80d91a9` (branch `docs/triad-audit`). **All three have byte-identical `frontend/src`** (`git diff --stat eb693b4..HEAD -- frontend/src` → empty). Evidence below therefore applies to the requested baseline product code. |
| Auditor's own source commit | `1d60492` (vault note front-matter `source_commit`) — same product tree. |
| Write policy | This document is the **only** file written. Product files are read-only for this agent. |

---

## 1. Objective

Eliminate the eight tactile/accessibility defects TA-1…TA-8 in the front-end so that every pointer affordance is a real, focusable, named, keyboard-operable control; every scrollable data region is keyboard-scrollable; every retry action is one 44 px press-target with press feedback; every hover-only native tooltip has a focus-reachable `aria-describedby` equivalent; every canvas/autoplay animation honours `prefers-reduced-motion`; both generic dialogs trap correctly and are named; the `About` component's careful focus management becomes reachable; and static rows stop advertising non-existent actions.

Outcome gates: `npm run lint` + `npm run build` exit 0; `scripts/ui_validate.py` reports **24/24 routes, zero JavaScript errors, 0 axe violations**; a documented keyboard walk passes. Each is a checkpoint below; none is asserted as already passing by this design.

---

## 2. Evidence (path:line)

### 2.1 Baseline reconciliation

```
$ git diff --stat eb693b4..HEAD -- frontend/src      # (empty output)
$ git diff --stat eb693b4..main -- frontend/src      # (empty output)
```
Only vault/docs differ between the three commits. No code-drift caveat applies.

### 2.2 Finding → evidence table

| ID | Finding (audit) | Static evidence gathered from baseline tree |
| --- | --- | --- |
| TA-1 | `cursor-pointer` on non-semantic nodes; no `tabIndex`/`role`/`onKeyDown`/focus ring | `SankeyFlow.tsx:240-254` (link `<path>`, title only), `:259-280` (node `<g>`); `AgeDistributionRadial.tsx:79-88` (`<path onClick>` + `cursor-pointer`, callback never supplied — sole consumer `ui/AgeDistributionSection.tsx:34` passes none); `TimelineStrip.tsx:118-141` (wave `<circle onClick={() => {/* TODO */}}>` — empty handler; component is unreferenced — `grep TimelineStrip src` returns only its own file); `PartyNetwork.tsx:56-101` (node `<g onClick>`), `:130-134` (`View all →` `<span onClick>`); `SwitchTimeline.tsx:134-154` (wave `<rect onClick>`), `:163-168` (`View all →` `<span onClick>`); `CrossChamberFlow.tsx:70-81` (two `<div onClick>` bars), `:114-132` (member `<div onClick>`); `CommitteeControl.tsx:77-93` (bar `<div onClick>`); `PartyListTable.tsx:60-99` (row `<div onClick>`), `:105-111` (`View all →` `<span onClick>`). Full `cursor-pointer` census: 22 matches (also `<summary>` at `Committees.tsx:295`, `CommitteeControl.tsx:133`, `TimelineChart.tsx:246`; non-interactive card class at `DashboardCard.tsx:76` — positive pattern, see §2.4). |
| TA-2 | Keyboard scroll containment missing | Already-correct exemplars: `Traseism.tsx:191,234,347,512,628`; `Committees.tsx:109,273`; `Coalitions.tsx:149`; `MpComparison.tsx:257`; `Demographics.tsx:160`; `PartyComparison.tsx:186`; `SwitchLeaderboard.tsx:135`; `SenateHistory.tsx:126`; `TimelineChart.tsx:249`. Missing: `RollCallTable.tsx:72`; `Parties.tsx:96`; `Grafice.tsx:64`; `Topuri.tsx:104`; `Ideology.tsx:271`; `Radar.tsx:128`; `CoverageView.tsx:160`; `Report.tsx:279,410`; `PartyTimeline.tsx:195`; `InstitutionalView.tsx:97`; `Voturi.tsx:104`; `router.tsx:246` (`<nav>`, has `aria-label`, no `tabIndex/role`). Vertical regions missing the same treatment: `LiveFeed.tsx:192`; `PartyProfile.tsx:166`; `PersonDeepDive.tsx:190,227`; `LegislatureDetail.tsx:153`; `PartyComparisonMatrix.tsx:42`. Already-correct vertical: `CrossChamberFlow.tsx:113`; `CommitteeControl.tsx:136`; `PartyListTable.tsx:55`; `Hemicycle.tsx:133`. |
| TA-3 | Focus indication split-brain (positive global rule) | `index.css:198-201` `:focus-visible{outline:2px solid #38bdf8;outline-offset:2px}`, light override `:89`. Local `focus:outline-none focus:ring-2` appears on inputs e.g. `Search.tsx:92`, `About.tsx:79`. |
| TA-4 | Weak press feedback / small targets | `index.css:146-154` `.btn-hover` (hover shadow + `:active{scale:.97}`) exists but is used on few controls; `index.css:171-173` `.btn` has no 44 px min. Bare ~16 px retry links: `PersonDrawer.tsx:122-124`; `ChamberView.tsx:36-37`; `CoverageView.tsx:81-82`; `LegislatureDetail.tsx:114-115,144-145`; `InstitutionalView.tsx:52-53,82-83`; `PartyProfile.tsx:159-160`. Shared retry buttons without `btn-hover`/min-height: `ErrorState.tsx:39-46`; `SankeyFlow.tsx:180-182`; `TimelineChart.tsx:232-234`; `Traseism.tsx:123-127`. Selects ~30–36 px; SVG hit areas 12–32 px (`PartyNetwork.tsx:65`, `SwitchTimeline.tsx:138`, `TimelineStrip.tsx:123`). Positive: `TimeSlider.tsx:61` already uses `min-h-11`. |
| TA-5 | Native `title` only | `SankeyFlow.tsx:249,274`; `Radar.tsx:151,174`; `PartyTimeline.tsx:226,236`; `SwitchLeaderboard.tsx:190`; `Traseism.tsx:99,384,861`; `Committees.tsx:284,383`; `LiveDashboard.tsx:98,109,120,131`; `PersonDrawer.tsx:135`; `MembershipGantt.tsx:59,73,87`; `CitationPopover.tsx:48`; `ThemeToggle.tsx:38`. (`About.tsx:237,264,301,329` are `AccordionItem` **props**, not tooltips — exclude.) |
| TA-6 | Reduced motion honoured in CSS but not canvas/autoplay | CSS: `index.css:203-212`. Only canvas guard: `VoteActivityChart.tsx:69-71,81`. Unguarded ECharts: `PartyAgreementMatrix.tsx:142-213` (option at `:142`, `setOption` `:213`, deps `:226`); `Ideology.tsx:108-185` (option `:108`, deps `:185`); `TimelineChart.tsx:103-182` (option `:103`, deps `:172`). Autoplay loop: `TimeSlider.tsx:39-56` (300 ms `setInterval`, no media-query guard). |
| TA-7 | Dialog defects; About unreachable | `ui/Modal.tsx:29-31` trap selector = `'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'` (omits inputs/selects/textarea); `:32` `if (!items?.length) return;` lets Tab escape; body lock present at `:22-23,46`; no accessible name (`:58-65`). `ui/Drawer.tsx:23-25,26` same selector/empty bug; **no body lock** (`:16-42`); no accessible name (`:53-60`). Exemplars: `About.tsx:116-137,159-204` (Escape, body lock, focus restore, `aria-labelledby="about-title"`, `onKeyDown` trap); `PersonDrawer.tsx:48-79,95-116` (same + `aria-labelledby="person-drawer-title"`). **Unreachable About:** `Traseism.tsx:14` imports `About`, `:668` declares `aboutOpen`, `:945` renders `<About open={aboutOpen} …/>`; `grep setAboutOpen` in Traseism → only `:668` and `:945`, **no `setAboutOpen(true)`**. A *different*, site-wide About exists in `router.tsx:112-173` (`AboutModal`) with a working trigger at `:232-236` and render at `:303`; both dialogs use the same `id="about-title"` (`About.tsx:190`, `router.tsx:158`). |
| TA-8 | False row-hover | `Traseism.tsx:208,271,373,544,641` use `row-hover` on actionless `<tr>` (CSS `index.css:164-169`); `SenateHistory.tsx:146`; `Committees.tsx:26,317`; `Coalitions.tsx:169`; `MpComparison.tsx:277`; `Demographics.tsx:185`; `PartyComparison.tsx:217`; `SwitchLeaderboard.tsx:164`; `Parties.tsx:110` (`hover:bg-… cursor-pointer` row but **no onClick at that site**); `Ideology.tsx:296`; `Voturi.tsx:148`; `RollCallTable.tsx:104`. Audit names Committees, SenateHistory, switch-leaderboard, Coalitions specifically. |

### 2.3 Audit's own meta-finding

TA-3 is a **positive**: the global focus ring is consistent. Do not replace it with per-component rings; only remove local overrides on elements touched by this recipe and let `:focus-visible` apply. `index.css:203-212` global reduced-motion rule does not reach canvas/JS — hence the JS guards in Step 9.

### 2.4 Positive patterns to preserve (do not modify)

- `Search.tsx:44-71,73-127` — full ARIA combobox (arrows, Escape, outside-click, `aria-activedescendant`, native `<button role="option">`).
- `TimeSlider.tsx:61-100` — native `range`, `aria-pressed`, `min-h-11` (only the autoplay guard is added).
- `DashboardCard.tsx:90-94` — native `<Link>` used specifically to avoid `nested-interactive`; its `cursor-pointer` is on a real link (excluded from TA-1).
- `<summary className="cursor-pointer …">` at `Committees.tsx:295`, `CommitteeControl.tsx:133`, `TimelineChart.tsx:246` — native disclosure semantics; excluded.
- Existing keyboard-scroll exemplars in §2.2 (TA-2 column 1) — use as the copy pattern, do not edit.

---

## 3. Exclusive file list

### 3.1 Write-set (the ONLY files an implementer may change for R-06)

| # | Path | Action |
| --- | --- | --- |
| 1 | `frontend/src/utils/a11y.ts` | **new** — shared SVG keyboard-activation helper |
| 2 | `frontend/src/hooks/useReducedMotion.ts` | **new** — shared reactive media-query hook |
| 3 | `frontend/src/components/RetryButton.tsx` | **new** — the single retry control |
| 4 | `frontend/src/components/ui/TooltipText.tsx` | **new** — `aria-describedby` text element |
| 5 | `frontend/src/components/ui/Modal.tsx` | trap selector, empty-trap, accessible name |
| 6 | `frontend/src/components/ui/Drawer.tsx` | trap selector, empty-trap, body lock, accessible name |
| 7 | `frontend/src/components/About.tsx` | unique dialog id, `btn-hover`/44 px close, preserve exemplar trap |
| 8 | `frontend/src/pages/Traseism.tsx` | wire About trigger; unique local About id; remove `row-hover` |
| 9 | `frontend/src/components/PersonDrawer.tsx` | RetryButton; remove native `title` → `aria-describedby` |
| 10 | `frontend/src/components/SankeyFlow.tsx` | SVG keyboard controls; tooltips; RetryButton |
| 11 | `frontend/src/components/AgeDistributionRadial.tsx` | remove false affordance or wire keyboard arcs; tooltips |
| 12 | `frontend/src/components/TimelineStrip.tsx` | remove empty-click false affordance; tooltips |
| 13 | `frontend/src/components/PartyNetwork.tsx` | SVG node keyboard control; `View all` native button |
| 14 | `frontend/src/components/SwitchTimeline.tsx` | SVG bar keyboard control; `View all` native button |
| 15 | `frontend/src/components/CrossChamberFlow.tsx` | bars + member rows → native buttons; keyboard-scroll already present |
| 16 | `frontend/src/components/CommitteeControl.tsx` | bar → native button; `aria-describedby` |
| 17 | `frontend/src/components/PartyListTable.tsx` | row + `View all` → native buttons |
| 18 | `frontend/src/components/ErrorState.tsx` | delegate retry to `RetryButton` |
| 19 | `frontend/src/components/LoadingState.tsx` | inspect retry at `:47-54`; delegate to `RetryButton` if it duplicates ErrorState |
| 20 | `frontend/src/components/ChamberView.tsx` | RetryButton |
| 21 | `frontend/src/components/CoverageView.tsx` | RetryButton; keyboard-scroll wrapper |
| 22 | `frontend/src/pages/LegislatureDetail.tsx` | RetryButton ×2 (`:114`, `:144`); keyboard-scroll vertical wrapper (`:153`) |
| 23 | `frontend/src/pages/InstitutionalView.tsx` | RetryButton ×2; keyboard-scroll wrapper |
| 24 | `frontend/src/pages/PartyProfile.tsx` | RetryButton; keyboard-scroll vertical wrapper |
| 25 | `frontend/src/pages/PersonDeepDive.tsx` | keyboard-scroll vertical wrappers (`:190`, `:227`) |
| 26 | `frontend/src/pages/Committees.tsx` | remove `hover:bg` on static rows |
| 27 | `frontend/src/pages/SenateHistory.tsx` | remove `hover:bg` on static row |
| 28 | `frontend/src/pages/Coalitions.tsx` | remove `hover:bg` on static row |
| 29 | `frontend/src/pages/MpComparison.tsx` | remove `hover:bg` on static rows |
| 30 | `frontend/src/pages/Demographics.tsx` | remove `hover:bg` on static rows |
| 31 | `frontend/src/pages/PartyComparison.tsx` | remove `hover:bg` on static rows |
| 32 | `frontend/src/pages/SwitchLeaderboard.tsx` | remove `hover:bg` on static row; `aria-describedby` loyalty hint |
| 33 | `frontend/src/pages/Parties.tsx` | keyboard-scroll wrapper; remove false `cursor-pointer` row |
| 34 | `frontend/src/pages/Grafice.tsx` | keyboard-scroll wrapper |
| 35 | `frontend/src/pages/Topuri.tsx` | keyboard-scroll wrapper |
| 36 | `frontend/src/pages/Ideology.tsx` | keyboard-scroll wrapper; reduced-motion guard; remove `hover:bg` row |
| 37 | `frontend/src/pages/Radar.tsx` | keyboard-scroll wrapper; `aria-describedby` on `title` cells |
| 38 | `frontend/src/pages/Report.tsx` | keyboard-scroll wrappers ×2 |
| 39 | `frontend/src/pages/PartyTimeline.tsx` | keyboard-scroll wrapper; `aria-describedby` on `title` cells |
| 40 | `frontend/src/pages/Voturi.tsx` | keyboard-scroll wrapper; remove `hover:bg` row |
| 41 | `frontend/src/components/RollCallTable.tsx` | keyboard-scroll wrapper; remove `hover:bg` row |
| 42 | `frontend/src/components/LiveFeed.tsx` | keyboard-scroll vertical wrapper |
| 43 | `frontend/src/components/PartyComparisonMatrix.tsx` | keyboard-scroll vertical wrapper |
| 44 | `frontend/src/components/TimelineChart.tsx` | reduced-motion guard; RetryButton at `:232-234` |
| 45 | `frontend/src/components/VoteActivityChart.tsx` | consolidate reduced-motion onto shared hook |
| 46 | `frontend/src/components/TimeSlider.tsx` | reduced-motion guard on autoplay |
| 47 | `frontend/src/router.tsx` | **only** the `<nav>` keyboard-scroll attribute, nothing else; keep global AboutModal out of scope |
| 48 | `frontend/src/index.css` | **verify-only** — no edit expected; do not reintroduce global focus/animation hacks |

48 unique paths: 4 new files, 43 existing files with bounded edits, 1 verify-only. If an implementer finds a listed path does not need a change after inspection, record "inspected, no change" in the handoff rather than silently expanding scope.

### 3.2 Explicitly read-only for R-06

`frontend/src/i18n.ts` (no key edits — use the codebase's `t("key", "English fallback")` pattern), `frontend/src/api/client.ts`, `frontend/src/router.tsx` except the single `<nav>` attribute, `frontend/docs/design/*`, all backend/pipeline/data/tests, and every vault note including the source TRIAD-AUDIT. Out-of-scope defects (AP-*, FN-*) are listed in §11.

---

## 4. Preconditions

1. **Checkout the exact baseline.** `cd /home/nedaktov/parlament-deschis && git rev-parse HEAD` is expected to be `80d91a90…` (or the integrator's R-06 branch off `eb693b4`/`1d60492` with identical `frontend/src`). Run `git diff --stat eb693b4..HEAD -- frontend/src`; if non-empty, **STOP** and reconcile drift before applying anything.
2. **Clean working tree for product code.** `git status --short -- frontend/src` must be empty (the two pre-existing untracked items `.nedcode/` and `Parlament Deschis Obsidian vault/.obsidian/backlink.json` at observation time are unrelated).
3. **Toolchain present** (observed): `node`, `npm`, `python3` with `playwright`, `/usr/bin/chromium`, `git`, `uv`. Confirm with `python3 -c "import playwright" && [ -x /usr/bin/chromium ] && echo OK`.
4. **axe asset precondition — currently UNMET.** `scripts/ui_validate.py:27` reads `/tmp/axe.min.js`; it was **absent** at observation (`[ -f /tmp/axe.min.js ]` → false). Before the UI gate can run, obtain axe-core **4.10.2** at that path, e.g.
   ```
   curl -fsSL https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js -o /tmp/axe.min.js
   test -s /tmp/axe.min.js && echo AXE_READY
   ```
   If the network is unavailable, the UI gate result is **NOT PROVEN** — record that; do not claim 24/24.
5. **Local backend + Vite dev server** for the UI gate (documented pattern, `docs/GATE-EVIDENCE-2026-11-21.md:236-237`):
   ```
   PARLAMENT_DB=/tmp/opencode/g08-parlament-real.db .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8101
   PARLAMENT_API_PROXY_TARGET=http://127.0.0.1:8101 npm run dev -- --host 127.0.0.1 --port 5180 --strictPort   # run in frontend/
   python3 scripts/ui_validate.py http://127.0.0.1:5180
   ```
   (Use any free port; pass it explicitly because Vite defaults to 5173 while `ui_validate.py:26` defaults to 5174. Avoid port 8000 — occupied by a stale Docker uvicorn per `.nedcode/qa/taste-report.md:6`.)
6. **Baseline gates green before edits** (record output): `cd frontend && npm run lint` → observed **exit 0, zero errors, zero warnings** at baseline; `npm run build` → exit 0 expected (documented green). If either is red at baseline, STOP — R-06 does not own pre-existing failures (§11).
7. **No automated unit-test runner** exists for the frontend (`frontend/package.json` has no `npm test`; `QA-AND-AXE.md:68-70`). Do not invent one.

---

## 5. Strategy / design decisions

1. **Native semantics first.** Every HTML `<div onClick>` / `<span onClick>` becomes `<button type="button">`; navigation targets become the project's native `<Link>` where a router target exists, otherwise a `<button>` that calls the existing navigate callback. Buttons inherit the global `:focus-visible` ring; add `btn-hover` and `min-h-11` when the control is a primary/retry action.
2. **SVG cannot contain HTML `<button>`** (invalid namespace; React renders unknown elements). For SVG hit targets the standards-correct pattern is a focusable `<g>`/`rect`/`path` with `role="button"`, `tabIndex={0}`, `aria-label`, an Enter/Space `onKeyDown` via the shared `activateOnKey`, and Tailwind focus utilities (`focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400`). We handle **both** Enter and Space (the `DashboardCard.tsx:90-92` comment warns that hand-rolled handlers miss Space) and never nest another interactive inside the `<g>`. Enlarge the invisible hit area where geometry allows.
3. **False affordances are deleted, not enabled.** `TimelineStrip`'s empty `onClick` TODO and `AgeDistributionRadial`'s never-supplied `onCohortClick` are removed (data markers become labelled graphics with `<title>`); `row-hover` classes on actionless `<tr>` are removed. Do not invent navigation a page owner did not specify.
4. **One primitive per concern** (4 new files in §3.1) instead of copy-paste: `activateOnKey`, `useReducedMotion`, `RetryButton`, `TooltipText`.
5. **Tooltips:** for HTML triggers replace `title=` with `aria-describedby=<id>` + `TooltipText` inside a `relative group` wrapper (shows on hover *and* focus via `group-hover:not-sr-only group-focus-within:not-sr-only`). For SVG shapes, HTML tooltips cannot be positioned per-shape inside `<svg>`; keep the `<title>` child for mouse hover **and** add `aria-describedby` referencing a sibling `sr-only` `TooltipText` rendered next to the `<svg>` — focus users then receive identical text. Document this exception in the commit message.
6. **Reduced motion is opt-in for motion.** `animation: !reducedMotion` on every ECharts option, and autoplay interval disabled when the media query matches. The CSS global rule at `index.css:203-212` stays; do not duplicate it in JS.
7. **No i18n churn.** Reuse existing keys where an exact caption exists; otherwise use the pervasive `t("a11y.<name>", "English fallback")` form so untranslated keys degrade to English without editing `i18n.ts`. Note the translation-parity limitation in §14.
8. **Incremental checkpoints.** Each step ends at a compile-clean state; the full gate runs once at the end (Step 11). SIDEBAR tasks never enter the same commit (§11).

---

## 6. Numbered steps — exact code and commands

### Step 0 — Backup + checksum (do this before the first edit)

```
cd /home/nedaktov/parlament-deschis
BK=/tmp/opencode/R06-backup-$(date +%Y%m%d-%H%M%S)
mkdir -p "$BK"
git ls-files 'frontend/src/**' | tar -cf "$BK/frontend_src.tar" -T -
# capture the 46 write-set files individually too (paths from §3.1)
sha256sum "$BK/frontend_src.tar" | tee "$BK/SHA256SUMS"
echo "$BK" > /tmp/opencode/R06-last-backup-path
```
Keep `$BK` until acceptance is signed off. See §13 for full backup/checksum policy.

### Step 1 — Add the four shared primitives

**`frontend/src/utils/a11y.ts`**
```ts
import type { KeyboardEvent } from "react";

/** Activate a focusable SVG control with the keys a native button uses.
 *  Space is preventDefault-ed so the page does not scroll. */
export function activateOnKey(
  event: KeyboardEvent<SVGElement>,
  activate: () => void,
): void {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    activate();
  }
}
```

**`frontend/src/hooks/useReducedMotion.ts`**
```ts
import { useEffect, useState } from "react";

const QUERY = "(prefers-reduced-motion: reduce)";

export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(
    () =>
      typeof window !== "undefined" &&
      typeof window.matchMedia === "function" &&
      window.matchMedia(QUERY).matches,
  );
  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const mq = window.matchMedia(QUERY);
    const onChange = (e: MediaQueryListEvent) => setReduced(e.matches);
    setReduced(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return reduced;
}
```

**`frontend/src/components/RetryButton.tsx`**
```tsx
import { useTranslation } from "react-i18next";

export default function RetryButton({
  onRetry,
  label,
  className = "",
}: {
  onRetry: () => void;
  label?: string;
  className?: string;
}) {
  const { t } = useTranslation();
  return (
    <button
      type="button"
      onClick={onRetry}
      className={`btn btn-hover min-h-11 bg-slate-700 hover:bg-slate-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400 ${className}`}
    >
      {label ?? t("traseismRetry")}
    </button>
  );
}
```

**`frontend/src/components/ui/TooltipText.tsx`**
```tsx
export default function TooltipText({
  id,
  children,
}: {
  id: string;
  children: React.ReactNode;
}) {
  return (
    <span
      id={id}
      role="tooltip"
      className="pointer-events-none sr-only group-hover:not-sr-only group-focus-within:not-sr-only absolute left-1/2 top-full z-[70] mt-1 -translate-x-1/2 whitespace-nowrap rounded border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-100 shadow-lg"
    >
      {children}
    </span>
  );
}
```
Call-site contract: wrapper has `relative group`; trigger has `aria-describedby={id}`; `id` is unique per instance (derive from a stable key, e.g. `` `tip-sankey-${link.source.name}-${link.target.name}` ``). For the SVG exception use the `sr-only`-only variant and keep `<title>` for mouse hover (§5.5).

**CHECKPOINT C1** — `cd frontend && npm run lint` → exit 0, 0 errors/0 warnings (unused imports in new files must be removed).

### Step 2 — Dialogs: `ui/Modal.tsx`, `ui/Drawer.tsx`

**Modal** — add a `label` prop and use it; widen the selector; stop empty-trap Tab escape. Keep the existing body lock (`:22-23,46`) and focus restore (`:24,47`).

```tsx
export default function Modal({ open, onClose, label, children }: {
  open: boolean;
  onClose: () => void;
  label: string;                       // NEW: accessible name
  children: React.ReactNode;
}) { ... }
```
In `onKey` replace lines 29-32 with:
```ts
      const items = panelRef.current?.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [contenteditable="true"], [tabindex]:not([tabindex="-1"])',
      );
      if (!items?.length) {
        e.preventDefault();             // empty dialog: keep focus on the panel
        panelRef.current?.focus();
        return;
      }
```
On the panel (`:58-65`) add `aria-label={label}` (or `aria-labelledby` if callers pass an id — prefer `aria-label` here; no caller currently passes a label, so add `label={t("about")}` at each call site or default it). Search call sites with `grep -rn "<Modal" frontend/src` before editing.

**Drawer** — same selector/empty-trap change at `:23-26`, plus:
- Body lock: mirror Modal — before `drawerRef.current?.focus()` in the effect, add
  ```ts
  const previousOverflow = document.body.style.overflow;
  document.body.style.overflow = "hidden";
  ```
  and in cleanup add `document.body.style.overflow = previousOverflow;`.
- Accessible name: add `label: string` prop and put `aria-label={label}` on the `<aside>` (`:53-60`). Update all call sites (`grep -rn "<Drawer" frontend/src`).

**CHECKPOINT C2** — `cd frontend && npm run lint` → exit 0; then keyboard-smoke per §8.3 for both dialogs (Tab cannot leave panel/aside; Escape closes; body has `overflow:hidden` while open and restores on close; focus returns to opener).

### Step 3 — Wire the unreachable About (`About.tsx`, `Traseism.tsx`)

**Decision (Option A — wire it):** add a visible trigger in Traseism's methodology section (near `Traseism.tsx:930-943`) that opens the local `<About>`; keep the global `router.tsx` AboutModal as the site-wide About (out of scope, §11). To avoid duplicate `id="about-title"` (axe `duplicate-id`) when both exist in the DOM, rename **only the local About's** id:

- `About.tsx:168` → `aria-labelledby="about-data-title"`; `About.tsx:190` → `<h2 id="about-data-title" …>`. (`router.tsx:136,158` keeps `about-title`.)
- `About.tsx:197-203` close button → add `btn-hover min-h-11` to the class list.
- `Traseism.tsx:945` → keep `<About open={aboutOpen} onClose={() => setAboutOpen(false)} />`.
- Insert immediately before that render (inside the methodology `<section>` after the link at `:935-942`):
```tsx
        <button
          type="button"
          className="btn btn-hover min-h-11 mt-3 bg-slate-700 hover:bg-slate-600"
          onClick={() => setAboutOpen(true)}
        >
          {t("aboutData", "About this data")}
        </button>
```
- Accepted alternative (**Option B**, if the team prefers one About): delete `Traseism.tsx:14`, `:668`, `:945` and rely on `router.tsx:232-236`. Do **not** do both; record the choice in the commit message. Option A is the recipe default because the audit's requirement is "wire the unreachable About".

**CHECKPOINT C3** — `grep -n "setAboutOpen(true)" frontend/src/pages/Traseism.tsx` → one match; `grep -rn 'id="about-title"' frontend/src` → one match (router only). `npm run lint` exit 0.

### Step 4 — HTML pointer-only controls → native buttons

Apply `btn-hover`, `min-h-11` and the inherited focus ring to each converted control; keep existing colours.

| File / lines | Exact change |
| --- | --- |
| `PartyListTable.tsx:60-99` | Replace the row `<div onClick>` with `<button type="button" className="group flex w-full items-center gap-3 p-2 text-left rounded-lg hover:bg-slate-700/30 cursor-pointer transition-all btn-hover min-h-11" onClick={() => onPartyClick?.(...)}> … </button>`. No nested interactive inside (only spans) — safe. |
| `PartyListTable.tsx:105-111` | `<span … onClick={onViewAll}>View all →</span>` → `<button type="button" className="btn-hover min-h-11 text-sky-400 hover:underline" onClick={onViewAll}>View all →</button>`. |
| `PartyNetwork.tsx:130-134` | Same span→button conversion for `View all →`. |
| `SwitchTimeline.tsx:163-168` | Same span→button conversion; keep the synthesized `SwitchWaveData` argument. |
| `CrossChamberFlow.tsx:70-81` | The two overlay `<div onClick>` bars → `<button type="button" aria-label={t("a11y.crossChamberDeputies", "Show deputies")} className="absolute left-0 top-0 h-full … cursor-pointer btn-hover min-h-11" style={{width}} onClick={…}>`. Ensure the second button is not covered by the first (keep DOM order; add `z-10` to the Senate button). |
| `CrossChamberFlow.tsx:114-132` | Member `<div onClick>` → `<button type="button" className="flex w-full items-center justify-between p-2 rounded hover:bg-slate-700/30 cursor-pointer btn-hover min-h-11" onClick={…}>`. |
| `CommitteeControl.tsx:77-93` | Bar `<div onClick>` → `<button type="button" aria-label={t("a11y.committeeChair", { party: party.party })} className="relative flex-1 h-11 rounded-full bg-slate-700/30 overflow-hidden cursor-pointer btn-hover" onClick={…}>`, keep inner coloured divs. |
| `SankeyFlow.tsx:180-182` | Retry button → `<RetryButton onRetry={() => summary.refetch()} className="bg-slate-700" />` (import from `../RetryButton`). |
| `TimelineChart.tsx:232-234` | Same RetryButton replacement (note: TimelineChart is also in Step 9 for reduced motion — both edits in one file, one commit). |

**CHECKPOINT C4** — `grep -rn '<span[^>]*onClick' frontend/src/components` → 0 matches; `npm run lint` exit 0.

### Step 5 — SVG controls: focusable, named, keyboard-operable

Use `activateOnKey` from Step 1. Add `role="button"`, `tabIndex={0}`, `aria-label`, `onKeyDown={(e) => activateOnKey(e, () => …)}` and focus-visible utilities to each target.

**SankeyFlow.tsx** (`:235-280`):
```tsx
{/* links */}
<path … className="cursor-pointer hover:stroke-opacity-0.8 transition-stroke focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
  role="button" tabIndex={0}
  aria-label={t("a11y.sankeyLink", { from: link.source.name, to: link.target.name, count: link.value })}
  onKeyDown={(e) => activateOnKey(e, () => setSelected(link))}
>
  <title>{`${link.source.name} → ${link.target.name}: ${link.value} switches`}</title>
</path>
```
Add `const [selected, setSelected] = useState<SankeyLinkWithPath | null>(null);` near `:81` and render the selected link's description in the existing legend area (`:288-309`) as a visible `<p role="status">` so the keyboard activation has an observable result (no navigation contract exists). For nodes (`:259-280`) apply the same pattern on the `<g>` with `aria-label={t("a11y.sankeyNode", { name: node.name, count: node.value })}`; keep `<title>`.

**AgeDistributionRadial.tsx** (`:79-88`) — sole consumer passes no callback (evidence §2.2). **Remove the false affordance:** drop `onClick` and `cursor-pointer`, add `<title>{`${slice.label}: ${slice.count} (avg ${slice.avgAge.toFixed(1)})`}</title>` inside each `<path>`, and keep the existing HTML legend (`:123-136`) as the accessible text alternative. If a future consumer supplies `onCohortClick`, implement the focusable-`<g>` branch behind `if (onCohortClick)` with `activateOnKey`; do not add it speculatively now.

**TimelineStrip.tsx** (`:118-141`) — empty TODO handler; component is unreferenced. Remove `onClick` and `cursor-pointer` from the `<circle>`; add `<title>{`${wave.start_date}: ${wave.switch_count} switches`}</title>` to the `<g>`. Do not delete the component (out of scope).

**PartyNetwork.tsx** (`:56-101`): on the node `<g>` add
```tsx
role="button" tabIndex={0}
aria-label={t("a11y.partyNode", { party: node.short_name, members: node.total_members })}
onKeyDown={(e) => activateOnKey(e, () => onNodeClick?.(node.short_name || node.id))}
className="cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
```
Add `const { t } = useTranslation();` (import `useTranslation` — file currently has none). The existing `onClick` stays for pointer users.

**SwitchTimeline.tsx** (`:134-153`): same treatment on the wave `<rect>` with `aria-label={t("a11y.switchWave", { count: wave.switch_count, date: wave.start_date ?? "" })}`; import `useTranslation` and `activateOnKey`.

**CHECKPOINT C5** — `grep -rn 'onClick={() => {' frontend/src/components/{SankeyFlow,AgeDistributionRadial,TimelineStrip,PartyNetwork,SwitchTimeline}.tsx` → only real handlers remain (no empty TODOs); `npm run lint` exit 0.

### Step 6 — Keyboard-scroll wrappers (TA-2)

For every wrapper **without** `tabIndex/role/aria-label` in §2.2, add the three attributes (exact copy pattern from `Traseism.tsx:191`):
```tsx
tabIndex={0} role="region" aria-label={t("<existing-caption-key-or-new>", "<English label>")}
```
Per-file label sources (prefer the existing caption key already used on that page):
- `RollCallTable.tsx:72` → `t("rollcall.table", "Roll-call votes")`; also remove `hover:bg-slate-800/40` at `:104` (TA-8).
- `Parties.tsx:96` → `t("parties.title", "Parties")`; remove `cursor-pointer` at `:110`.
- `Grafice.tsx:64`, `Topuri.tsx:104`, `Voturi.tsx:104` → `t("view.grafice.title", "Charts")`-style existing keys; check `grep -n "t(\"view\." <file>` to pick a real key.
- `Ideology.tsx:271` → `t("view.ideology.title", "Ideology")`; also remove `hover:bg-slate-800/40` at `:296`.
- `Radar.tsx:128` → `t("view.radar.title", "Radar")`.
- `CoverageView.tsx:160` → `t("coverage.title", "Coverage")`.
- `Report.tsx:279,410` → distinct labels, e.g. `t("report.table", "Report table")` and `t("report.exportTable", "Export table")`.
- `PartyTimeline.tsx:195` → `t("partyTimeline.table", "Party timeline")`.
- `InstitutionalView.tsx:97` → `t("institutional.table", "Institutional table")`.
- `router.tsx:246` (`<nav>`) → add `tabIndex={0} role="region"` alongside the existing `aria-label={t("mainNavigation")}`.
- Vertical regions: `LiveFeed.tsx:192`, `PartyProfile.tsx:166`, `PersonDeepDive.tsx:190,227`, `LegislatureDetail.tsx:153`, `PartyComparisonMatrix.tsx:42` → `tabIndex={0} role="region" aria-label={t("<caption>", "<English label>")}`.

Rule: each `aria-label` must be unique within a route (axe `landmark-unique` regressed here before — `COMPREHENSIVE-REVIEW-2026-11-21.md:43`), and `role="region"` without an accessible name is a violation — never omit the label.

**CHECKPOINT C6** — `grep -rn 'overflow-x-auto' frontend/src | grep -v 'tabIndex' | grep -v 'router.tsx:246'` → 0 lines after edit (audit the vertical list manually). `npm run lint` exit 0.

### Step 7 — One RetryButton with `btn-hover`

Replace every bare retry link/button in §2.2 TA-4 with `<RetryButton onRetry={…} />`:
```
PersonDrawer.tsx:122-124, ChamberView.tsx:36-37, CoverageView.tsx:81-82,
LegislatureDetail.tsx:114-115 & 144-145, InstitutionalView.tsx:52-53 & 82-83,
PartyProfile.tsx:159-160, SankeyFlow.tsx:180-182, TimelineChart.tsx:232-234
```
`ErrorState.tsx:38-47` replace its `<button>` body with `<RetryButton onRetry={onRetry} className="mt-4" />` (import it). `LoadingState.tsx:47-54` keeps its own retry only if it is not a duplicate of ErrorState — inspect; if it is, switch it to `RetryButton` too (the file is already in the write-set, #19).
`Traseism.tsx:123-127` (local error component) → `RetryButton` as well.
Do **not** change `t("traseismRetry")` labels; `RetryButton` defaults to that key.

**CHECKPOINT C7** — `grep -rn 'ml-3 underline' frontend/src` → 0 matches; `grep -rln 'btn-hover' frontend/src/components | wc -l` increases; `npm run lint` exit 0.

### Step 8 — `aria-describedby` tooltips (TA-5)

For each HTML `title=` in §2.2 TA-5 (excluding `AccordionItem title` props): wrap the trigger in `relative group`, delete `title=`, add `aria-describedby="<unique-id>"`, and render `<TooltipText id="<unique-id>">same text</TooltipText>` as a sibling. Priority sites:
- `SwitchLeaderboard.tsx:190` (loyalty hint — hover-only today).
- `Committees.tsx:284,383`; `PartyTimeline.tsx:226,236`; `Radar.tsx:151,174`; `LiveDashboard.tsx:98,109,120,131`; `MembershipGantt.tsx:59,73,87`; `Traseism.tsx:99,384,861`; `PersonDrawer.tsx:135` (identifier chip — make the chip a `relative group` span with `aria-describedby`).
- `CitationPopover.tsx:46-55` and `ThemeToggle.tsx:38` are already buttons; just swap `title` → `aria-describedby` + `TooltipText`.
For SVG shapes (`SankeyFlow`, `PartyNetwork`, `SwitchTimeline`, `AgeDistributionRadial`, `TimelineStrip`) apply the §5.5 exception: keep `<title>` for mouse hover, add a sibling `sr-only` `TooltipText` referenced by `aria-describedby` on the focusable `<g>`/`<path>`/`<rect>`.

**CHECKPOINT C8** — `grep -rn ' title=' frontend/src --include=*.tsx | grep -v 'AccordionItem' | grep -v '<EmptyState' | grep -v '<Tooltip' | wc -l` → 0 (or a listed, justified exception). `npm run lint` exit 0.

### Step 9 — Reduced-motion guards on all canvases and autoplay (TA-6)

Import `useReducedMotion` in each file and add `animation: !reducedMotion` to the ECharts option with the hook value in the effect deps:

- `VoteActivityChart.tsx:69-71` — delete the inline `matchMedia` block; add `const reducedMotion = useReducedMotion();` in the component body and change `:81` to `animation: !reducedMotion,`; add `reducedMotion` to the deps at `:168`. Behaviour is preserved, source consolidated.
- `PartyAgreementMatrix.tsx` — add import + `const reducedMotion = useReducedMotion();`; insert `animation: !reducedMotion,` after `backgroundColor: "transparent",` at `:143`; add `reducedMotion` to deps at `:226`.
- `Ideology.tsx` — same; option at `:108-109`, deps at `:185`.
- `TimelineChart.tsx` — same; option at `:103,134`, deps at `:172` (and `:182` if the memo is consumed there).
- `TimeSlider.tsx` — add import + `const reducedMotion = useReducedMotion();`; change `:40` to `if (!playing || reducedMotion) return;`; add `reducedMotion` to deps at `:56`; add `disabled={reducedMotion}` to the play button (`:61-66`) and a sibling `<span className="sr-only">{t("a11y.reducedMotionNote", "Animation disabled by your reduced-motion setting.")}</span>`. Keep `min-h-11`.

**CHECKPOINT C9** — `grep -rn 'animation: !reducedMotion\|reducedMotion' frontend/src --include=*.tsx` lists all five files; `grep -rn 'animation:' frontend/src --include=*.tsx` shows no unguarded ECharts option. `npm run lint` exit 0. Browser proof (DevTools "Emulate CSS media feature prefers-reduced-motion: reduce") is part of §8.3 and is **NOT PROVEN** by grep.

### Step 10 — Remove false row-hover (TA-8)

Delete the `row-hover` class from `Traseism.tsx:208,271,373,544,641`. Delete `hover:bg-slate-700/50` from `SenateHistory.tsx:146`, `Coalitions.tsx:169`, `MpComparison.tsx:277`, `Demographics.tsx:185`, `PartyComparison.tsx:217`, `SwitchLeaderboard.tsx:164`; `hover:bg-slate-700/40` from `Committees.tsx:26,317`; `hover:bg-slate-800/40` from `Ideology.tsx:296`, `Voturi.tsx:148`, `RollCallTable.tsx:104`; and `cursor-pointer` from `Parties.tsx:110`. Keep `hover:bg` only where a real click target exists (`LiveFeed.tsx:207`, `PartyListTable` after Step 4, `CrossChamberFlow` after Step 4, `Search.tsx:119-121`). Do **not** edit `index.css:164-169` — `.row-hover` remains defined for legitimate uses.

**CHECKPOINT C10** — `grep -rn 'row-hover' frontend/src --include=*.tsx` → 0 matches in pages; static `<tr>` lines above no longer contain `hover:bg`; `npm run lint` exit 0.

### Step 11 — Full verification (once, after all steps)

Run §8.1 → §8.2 → §8.3 in that order. Capture raw output to `/tmp/opencode/R06-gate-$(date +%Y%m%d-%H%M%S).log` and reference it in the handoff. No step is "done" on assertion alone (§9).

---

## 7. CHECKPOINTS (exact command → expected output → exit)

| CP | Exact command | Expected output | Exit |
| --- | --- | --- | --- |
| C0 | `cd /home/nedaktov/parlament-deschis && git diff --stat eb693b4..HEAD -- frontend/src` | empty | 0 |
| C1–C10 | `cd /home/nedaktov/parlament-deschis/frontend && npm run lint` | `> tsc --noEmit && eslint src --ext .ts,.tsx`; **no** error/warning lines | 0 |
| C2 | `grep -n 'input:not(\[disabled\])' frontend/src/components/ui/{Modal,Drawer}.tsx` | one match per file | 0 |
| C3 | `grep -n 'setAboutOpen(true)' frontend/src/pages/Traseism.tsx` | exactly 1 match | 0 |
| C4 | `grep -rn '<span[^>]*onClick' frontend/src/components` | no matches | 1 (grep = no match) |
| C5 | `grep -rn 'TODO: Add click handler' frontend/src` | no matches | 1 |
| C6 | `grep -rn 'overflow-x-auto' frontend/src --include=*.tsx \| grep -v tabIndex` | only `router.tsx:246` (expected after Step 6 it also has tabIndex → no matches) | 1 |
| C7 | `grep -rn 'ml-3 underline' frontend/src` | no matches | 1 |
| C8 | `grep -rn ' title=' frontend/src --include=*.tsx \| grep -v -E 'AccordionItem\|EmptyState\|TooltipText' \| wc -l` | `0` | 0 |
| C9 | `grep -rln 'useReducedMotion' frontend/src --include=*.tsx \| sort` | 5 files (VoteActivityChart, PartyAgreementMatrix, Ideology, TimelineChart, TimeSlider) | 0 |
| C10 | `grep -rn 'row-hover' frontend/src/pages --include=*.tsx` | no matches | 1 |
| C11 (gate) | `cd frontend && npm run build` | `tsc -b && vite build` completes; no TS error | 0 |
| C12 (gate) | `python3 scripts/ui_validate.py http://127.0.0.1:5180` (with §4.5 servers up) | `UI VALIDATION PASS: 24 routes, zero JavaScript errors, 0 axe violations` | 0 |
| C13 (gate) | keyboard walk §8.3 | all rows in the walkthrough marked PASS in the log | 0 |

A grep "no match" is **exit 1** and is the expected result for C4/C5/C6/C7/C10 — do not treat it as a failure.

---

## 8. Verification gates

### 8.1 Lint / build

```
cd /home/nedaktov/parlament-deschis/frontend
npm run lint     # CP C1…C10; expect exit 0, zero errors, zero warnings
npm run build    # CP C11; expect exit 0
```
Baseline observation: `npm run lint` exit 0 with **zero** warnings at `80d91a9` (the older "7 exhaustive-deps warnings" note in `QA-AND-AXE.md:64-67` is historical). Any new warning is a regression of this recipe. There is no `npm test` (§4.7).

### 8.2 UI gate — 24/24, zero axe

Preconditions from §4.4/§4.5 must hold. Then:
```
cd /home/nedaktov/parlament-deschis
python3 scripts/ui_validate.py http://127.0.0.1:5180 | tee /tmp/opencode/R06-ui-gate.log
echo "EXIT=${PIPESTATUS[0]}"
```
Expected final line: `UI VALIDATION PASS: 24 routes, zero JavaScript errors, 0 axe violations`; exit 0. The per-route table (`ui_validate.py:47-75,156`) must show `[OK]` for all 24. Historical scope caveat: the same gate is 23/24 against the **live** proxy because `/ideology` 404s there (`QA-AND-AXE.md:36-39`) — report the scope (local backend vs live) explicitly. If `/tmp/axe.min.js` is missing or playwright/chromium unavailable, report **NOT PROVEN**, never a pass.

### 8.3 Keyboard walk (manual, Tier A; no script exists)

Run with the same dev server. Record each row PASS/FAIL in the gate log. Use `Tab`, `Shift+Tab`, `Enter`, `Space`, `Escape`, `Arrow*`.

| # | Route / component | Action | Pass condition |
| --- | --- | --- | --- |
| K1 | any route | `Tab` from page top | Skip-link (`router.tsx:217-219`) is first focusable and becomes visible |
| K2 | `/` (LiveDashboard) | Tab through PartyListTable, CommitteeControl, PartyNetwork, SwitchTimeline, CrossChamberFlow | Every converted control receives the sky focus ring; `Enter` **and** `Space` activate; `View all` navigates |
| K3 | `/traseism` | Tab to Sankey nodes/links | Each `<g>/<path>` is reachable, named, activated by Enter/Space; result text appears in the legend/status area |
| K4 | `/traseism` | Focus the new "About this data" button, press Enter | About dialog opens; focus lands on Close; Tab stays inside; Escape closes; focus returns to the button; `document.body.style.overflow` restored |
| K5 | global header (any route) | Focus "About" button, Enter | Site AboutModal opens (unchanged); same trap/restore checks |
| K6 | a route using `ui/Modal` and one using `ui/Drawer` | Tab with a form control present | Focus reaches form controls; Tab cannot leave the dialog; Escape closes; body locked then restored |
| K7 | `/parties`, `/grafice`, `/topuri`, `/ideology`, `/radar`, `/coverage`, `/report`, `/Voturi` | Focus each table region | Focus ring on the region; arrow keys / Page keys scroll horizontally; region has an accessible name |
| K8 | `/person/<id>` (PersonDrawer), `/party/PSD`, `/legislature/2024` | Focus vertical lists | Same as K7 for vertical scroll regions |
| K9 | OS setting `prefers-reduced-motion: reduce` | Load `/radar`, `/grafice`, `/ideology`, `/party-timeline`, and a page with TimeSlider | Canvas renders without intro animation; TimeSlider play button disabled with an announced explanation; toggling the OS setting back re-enables without reload |
| K10 | error branches (force via devtools offline/abort) | Focus each retry | One 44 px `RetryButton` per error; Enter/Space refetch; focus ring visible |
| K11 | all routes from §8.2 | Hover/focus every tooltip trigger | Text announced via `aria-describedby` on focus; visible on focus; no native `title` remains where replaced |
| K12 | Committees, SenateHistory, `/leaderboard`, Coalitions | Hover static rows | No background highlight / pointer cursor on actionless rows |

### 8.4 Full repo gate (optional, integrator scope)

If the integrator requires the repo-wide gate, run (all documented green at baseline):
```
cd /home/nedaktov/parlament-deschis
uv run ruff check pipeline backend scripts tests
uv run pytest -q
bash scripts/check-doc-truth.sh
```
R-06 changes no Python/data, so these should stay green; a failure here is a side-quest (§11), not an R-06 acceptance blocker unless it is caused by an R-06 edit.

---

## 9. Acceptance criteria

- [ ] Every HTML pointer-only control in §2.2 TA-1 is a native `<button>`/`<Link>` with a real handler; every SVG target is focusable, named, has Enter+Space handling and a visible focus ring.
- [ ] `TimelineStrip` empty handler and `AgeDistributionRadial` unreachable callback no longer advertise a click.
- [ ] All wrappers in §2.2 TA-2 have `tabIndex=0 role="region"` + a unique accessible name; keyboard scrolling verified (K7/K8).
- [ ] Global `:focus-visible` remains the single focus system; no new local `focus:outline-none` introduced.
- [ ] Exactly one `RetryButton` implementation exists; all bare `ml-3 underline` retries replaced; press feedback (`btn-hover`) and ≥44 px height present.
- [ ] Native `title` tooltips replaced per §5.5; `aria-describedby` targets exist and are unique.
- [ ] Every ECharts option sets `animation: !reducedMotion`; TimeSlider autoplay guarded and disabled under reduced motion; verified in K9.
- [ ] `ui/Modal` and `ui/Drawer`: widened trap selector, no Tab escape on empty, body lock (Drawer added), accessible names, focus restore; verified K4–K6.
- [ ] Traseism's local About is reachable via a visible button; no duplicate `about-title` id; choice (A or B) recorded.
- [ ] False `row-hover` / `hover:bg` on actionless rows removed; K12 passes.
- [ ] `npm run lint` and `npm run build` exit 0 with no new warnings.
- [ ] `ui_validate.py` reports 24/24, zero JavaScript errors, 0 axe violations **on a named scope**; keyboard walk K1–K12 logged PASS; OR any unrun check is explicitly recorded as **NOT PROVEN** (§14), never as a pass.
- [ ] No file outside §3.1 was modified (`git status --short` review at handoff).

---

## 10. Dependencies

- **Upstream input:** vault `TRIAD-AUDIT-2026-11-21.md` TA-1…TA-8 (canonical, `source_commit: 1d60492`).
- **Runtime deps already present:** React 19, react-i18next, `@tanstack/react-router`, Tailwind 3.4 (`min-h-11`, `sr-only`, `not-sr-only`, `group-focus-within`, `focus-visible:*` all available), ECharts 5.5 modular core. **No new npm dependency** is introduced.
- **Tooling:** Node/npm; system Python with `playwright`; `/usr/bin/chromium`; `/tmp/axe.min.js` (axe-core 4.10.2) — see §4.4.
- **Downstream consumers:** LiveDashboard (`PartyListTable`, `CommitteeControl`, `PartyNetwork`, `SwitchTimeline`, `CrossChamberFlow`, `AgeDistributionSection`), Traseism (`SankeyFlow`, local `About`), router (`AboutModal`, nav). Changing prop signatures of `Modal`/`Drawer` requires updating *all* call sites — discover with `grep -rn '<Modal\|<Drawer' frontend/src` before Step 2.
- **Other recipes:** no hard dependency on R-01…R-05 (appearance/data-functionality work). Shared files with other agents: `index.css` (verify-only), `router.tsx` (one attribute only), `pages/Ideology.tsx` (this recipe adds reduced-motion + scroll label; coordinate if another agent edits the same file). Integrator must merge by path, not by whole branch.

---

## 11. Side-quest policy

**Rule: one concern per commit.** If, while editing, you discover an issue outside TA-1…TA-8, do **not** fix it in the R-06 commit. Log it in the handoff under a "found, not fixed" list with path:line and route it to its owner.

Explicitly out of scope for R-06 (from the same vault audit):
- AP-1…AP-8 (visual system: HeroGraphic colours, DataBar/ProgressRing paint, `.wrap`, token bypass, muted hierarchy, type scale, canvas themes, state visuals) → Appearance recipe.
- FN-1…FN-9 (`useAsOf`, switch definition, scope totals, null→0, state gating, provenance, URL state, vote scope, headline metrics) → Functionality recipe.
- The site-wide `router.tsx` `AboutModal` content duplication (router `:112-173` vs `About.tsx`) — leave as-is; only the id-collision fix in Step 3 is in scope.
- New i18n keys with ro translations, an axe baseline artifact, Playwright CI wiring, and any Python/data changes.
- Deleting the unreferenced `TimelineStrip` component, or adding `onCohortClick` consumers.
- The `DashboardCard.tsx:76` `cursor-pointer` (already a native `<Link>`), `<summary className="cursor-pointer">` instances, and other positive patterns from §2.4.

If a required step (e.g., Step 2's `label` prop) forces a call-site edit in a file not in §3.1, add that file to the write-set in the handoff with a one-line justification before editing — never silently.

---

## 12. ROLLBACK

Per-step and full rollback are both available; no destructive git operations are required.

```
cd /home/nedaktov/parlament-deschis
BK=$(cat /tmp/opencode/R06-last-backup-path)

# Per-file (preferred: surgical, keeps other work intact)
git checkout -- frontend/src/components/ui/Modal.tsx        # repeat per file
# New files created by R-06 must be removed explicitly:
rm -f frontend/src/utils/a11y.ts frontend/src/hooks/useReducedMotion.ts \
      frontend/src/components/RetryButton.tsx frontend/src/components/ui/TooltipText.tsx

# Full restore of the write-set from the Step 0 tar:
tar -xf "$BK/frontend_src.tar" -C /home/nedaktov/parlament-deschis
sha256sum -c "$BK/SHA256SUMS"

# If R-06 was committed on its own branch:
git revert <R06-commit-sha>          # preferred (auditable)
# or, only if the integrator confirms the branch contains nothing else:
git reset --hard eb693b4             # DESTRUCTIVE — requires explicit confirmation
```
After any rollback re-run `npm run lint && npm run build` (C1/C11) and confirm exit 0 before resuming. Never `git checkout -- .` or `git clean -fd` — the repo has untracked user work (`.nedcode/`, vault backlink) that is not R-06's.

---

## 13. BACKUP + checksum

- **Location:** `/tmp/opencode/R06-backup-<YYYYMMDD-HHMMSS>/` (preferred temp root per environment policy).
- **Content:** `frontend_src.tar` = every git-tracked file under `frontend/src` at the moment before Step 1, captured via `git ls-files 'frontend/src/**' | tar -cf … -T -`. This covers all 46 write-set files plus the verify-only files.
- **Manifest:** `sha256sum frontend_src.tar | tee SHA256SUMS`; store the active backup path in `/tmp/opencode/R06-last-backup-path`.
- **Integrity check before any rollback claim:** `cd "$BK" && sha256sum -c SHA256SUMS` → `frontend_src.tar: OK`, exit 0.
- **Retention:** keep until acceptance (§9) is signed off by the integrator; then the integrator may prune. The backup is outside the repo and is never committed.
- **Also capture gate logs** in the same directory: `R06-ui-gate.log`, `R06-keyboard-walk.log`, `R06-gate-<timestamp>.log` (§8).

---

## 14. NOT PROVEN

Everything below is **static-code design evidence** as of the baseline; this agent did not run a browser, axe, touch device, or production comparison. The implementer must prove or explicitly re-label each item.

1. **Browser render / computed styles.** Focus-ring colour/offset, 44 px hit areas after Tailwind compilation, tooltip visibility, and 320 px reflow were not observed.
2. **axe / WCAG AA.** The 0-violation target is a gate to be run, not a result. No committed axe baseline exists (`QA-AND-AXE.md:48-57`); `ui_validate.py` injects an **untracked** `/tmp/axe.min.js`. At observation that file was **missing**, the dev servers were **not running**, so the UI gate was **NOT PROVEN**.
3. **Keyboard walk.** K1–K12 are a procedure, not an executed test.
4. **Reduced motion.** `prefers-reduced-motion` emulation (K9) not executed; `@media (prefers-reduced-motion)` CSS at `index.css:203-212` and the new JS hook are design intent only.
5. **Touch targets.** 44 px is encoded via `min-h-11`; no physical touch-device test was performed. SVG hit-area enlargement where geometry allows is a design decision, not a measured result.
6. **Translation parity.** No `i18n.ts` edits are in scope; new `t(key, "English fallback")` strings will render English in ro mode until keys are added by the i18n owner. Not proven acceptable to Romanian users.
7. **Dialog behaviour.** Modal/Drawer trap, body-lock restoration, and empty-dialog focus behaviour are code-level designs; runtime proof is C2/K4–K6.
8. **Live/production parity.** The repo's live gate is historically 23/24 (`/ideology` 404); production green is **NOT PROVEN** and is not an R-06 acceptance condition.
9. **Baseline commit label.** The task named `main eb693b4`; locally `main` is `1d60492` and HEAD is `80d91a9`. We proved `frontend/src` is byte-identical across them; the *commit label* mismatch is recorded, not resolved.
10. **Dead-code status.** `TimelineStrip` is unreferenced and `AgeDistributionRadial` is called without `onCohortClick` by static grep only; a consumer added after the baseline would change the correct remediation.

---

## 15. Handoff summary (report to integrator)

- Produced: this read-only strategy + executable recipe. **No product file was modified.**
- Root causes addressed: TA-1 (semantics/keyboard), TA-2 (scroll containment), TA-4 (44 px + one RetryButton), TA-5 (aria-describedby), TA-6 (canvas/autoplay reduced motion), TA-7 (dialog trap/lock/name + reachable About), TA-8 (false hover). TA-3 is a positive and is preserved.
- Change shape: 4 new shared primitives + 43 existing files with bounded edits + 1 verify-only file (48 unique paths in §3.1); no new dependencies; no i18n/backend/data/test changes.
- Hard gates before "done": C1–C11, UI gate 24/24 zero axe (named scope), keyboard walk K1–K12, and an explicit NOT PROVEN list for anything that could not run.
- First action for the implementer: **Step 0 backup**, then §4.4 axe precondition (`/tmp/axe.min.js` is currently absent).
