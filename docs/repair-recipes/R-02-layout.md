# R-02 — Layout, containers & type scale

**Role:** STRATEGY / RECIPE AGENT R-02 (senior layout + design-system engineer).
**Status:** `STRATEGY + RECIPE ONLY — NOT IMPLEMENTED`. This document edits no product code.
**Project:** `/home/nedaktov/parlament-deschis`
**Baseline (as briefed):** `main @ eb693b4` (merge `docs/triad-audit`, 2026-11-21 19:40 +0200).
**Working HEAD at evidence time:** `80d91a9` (`docs(vault): three-lens frontend audit`).
**Tree identity (verified):** `git rev-parse eb693b4^{tree} HEAD^{tree}` → both
`02ac065d7326df6d801242d17998c9d207a1cb43`; `git diff --stat eb693b4 HEAD -- frontend/src`
is empty (exit 0). **Every path:line below therefore holds on the stated baseline.**
**Inputs (read-only):**
- `Parlament Deschis Obsidian vault/40-FRONTEND/TRIAD-AUDIT-2026-11-21.md` — AP-3 (`index.css:115-120`), AP-6 (per-cluster rows; `index.css:99-104`), §4 item 1.
- `Parlament Deschis Obsidian vault/40-FRONTEND/FRONTEND-AUDIT-2026-11-21.md` — §2 X7, §3 (23 pages), §5 item 7.
- `Parlament Deschis Obsidian vault/40-FRONTEND/DESIGN-CONTRACT.md` — §Success criteria (responsive layout, no lint/build regression, decisions traceable).
- `frontend/src/index.css`, `frontend/src/router.tsx`, all `frontend/src/pages/*.tsx` (23 files), `frontend/src/components/ui/DashboardHeader.tsx`.

---

## 0. Objective

Replace the current **two-owner container model** (shell `main` *and* per-page `.wrap` /
`max-w-7xl mx-auto` / `p-6`) and the **fragmented type/card/table scale** with one enforced
system, without changing data, routes, copy, colours or interaction behaviour:

1. **One container owner** — `main#main-content` owns max-width, centring and the gutter
   `px-4 sm:px-6 lg:px-8`. Equal left/right edges at **320 / 768 / 1024 px** on all 24 routes.
2. **One shared hero recipe** — a documented template with an approved vertical-rhythm
   variant list, one visible `h1` and one `[data-moment]` per hero.
3. **One `.page-title` scale** and **one `.moment-value` scale** — kills every authored
   `text-2xl`, `text-2xl sm:text-3xl`, `text-3xl sm:text-4xl`, `font-black` and `text-5xl`
   variant on headings/moment figures.
4. **One table grammar / card grammar** — `.data-table` fixes text size and cell padding at
   the table layer; `rounded-xl` + `p-4` becomes the only card radius/density.

Out of scope (explicitly): AP-1/AP-2/AP-4/AP-5/AP-7/AP-8, i18n, data honesty (X1–X6),
tactile/a11y (TA-*), route changes, dependency changes, deploy. Those are sibling parts.

---

## 1. Evidence (path:line)

### 1.1 Audit anchors

| ID | Claim | Audit location |
|---|---|---|
| AP-3 | `.wrap` missing on InstitutionalView, Parties, PartyComparison, PartyTimeline, SwitchLeaderboard; doubled on LiveDashboard, CoverageView, Demographics; "equal edges holds nowhere" | TRIAD-AUDIT:28, :36 |
| AP-6 | `font-black` moment figures; Report `sm:text-4xl` vs InstitutionalView `text-2xl`; three card grammars; radii 4/8/12 px; `text-xs` vs `text-sm` tables | TRIAD-AUDIT:31, :39 |
| §4.1 | "add one `surface`, `.page-title`, `.moment-value`, `.data-table` and `.badge` utility. Touches all 23 pages" | TRIAD-AUDIT:78 |
| X7 | design-system fix, no new dependency | FRONTEND-AUDIT:45, :105 |
| Success | responsive layout; no lint/build regression; decisions traceable | DESIGN-CONTRACT:78-83 |

### 1.2 Shell = a competing second container (the root cause)

- `frontend/src/router.tsx:299` — `<main id="main-content" … className="max-w-7xl mx-auto w-full min-w-0 px-4 py-5 flex-1">`.
- `frontend/src/router.tsx:221` — header inner `className="max-w-7xl mx-auto px-4 py-4 …"` (**different gutter breakpoint** than `.wrap`).
- `frontend/src/router.tsx:246` — nav `className="flex gap-1 border-b border-slate-700 px-4 overflow-x-auto"`.
- `frontend/src/index.css:118-120` — `.wrap { @apply max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 min-w-0; }` — a *second* container with different padding steps.
- `frontend/src/index.css:126-130` — reflow rule already anticipates `main .wrap`, proving the double-owner design.

### 1.3 All 23 page roots — container inventory (`frontend/src/pages/`)

Counted: standalone `wrap` utility = **14** occurrences; inner `<div className="max-w-7xl mx-auto">` = **15**; root `<div className="p-6">` = **3**; page-level `max-w-7xl` = **15**.

| Page | Root (path:line) | `wrap` | inner `max-w-7xl` | Extra gutter | Class |
|---|---|---|---|---|---|
| LiveDashboard | `LiveDashboard.tsx:86` `wrap space-y-8` | 1 | 3 (`:89,:165,:190`) | `:164,:189` `px-4` | **double** (3×) |
| Traseism | `Traseism.tsx:721` `wrap space-y-6` | 1 | 1 (`:723`) | — | **double** |
| SwitchLeaderboard | `SwitchLeaderboard.tsx:45` `p-6` | 0 | 1 (`:48`) | `p-6` | **double** (no wrap, own gutter) |
| CoverageView | `CoverageView.tsx:90` `wrap space-y-6`; `:156` `wrap space-y-4` | **2** | 1 (`:93`) | — | **double nested** |
| Demographics | `Demographics.tsx:63` `wrap space-y-6` | 1 | 1 (`:66`) | — | **double** |
| Committees | `Committees.tsx:199` `wrap py-6 print:p-0` | 1 | 0 | — | **double** |
| Mps | `Mps.tsx:69` `wrap space-y-6` | 1 | 1 (`:71`) | — | **double** |
| MpComparison | `MpComparison.tsx:141` `wrap space-y-6` | 1 | 1 (`:143`) | — | **double** |
| Report | `Report.tsx:105` `wrap py-6 print:p-0` | 1 | 0 | — | **double** |
| Coalitions | `Coalitions.tsx:56` `wrap space-y-6` | 1 | 1 (`:59`) | — | **double** |
| SenateHistory | `SenateHistory.tsx:49` `wrap space-y-6` | 1 | 1 (`:51`) | — | **double** |
| PartyProfile | `PartyProfile.tsx:83` `wrap space-y-6` | 1 | 1 (`:86`) | — | **double** |
| PersonDeepDive | `PersonDeepDive.tsx:108` `wrap space-y-6` | 1 | 1 (`:111`) | — | **double** |
| LegislatureDetail | `LegislatureDetail.tsx:53` `wrap space-y-6` | 1 | 1 (`:55`) | — | **double** |
| PartyTimeline | `PartyTimeline.tsx:90` `p-6` | 0 | 1 (`:93`) | `p-6` | **missing wrap + own gutter** |
| PartyComparison | `PartyComparison.tsx:125` `p-6` | 0 | 0 | `p-6` | **missing wrap + own gutter** |
| Parties | `Parties.tsx:44` `space-y-6` | 0 | 0 | — | relies on `main` (works accidentally) |
| InstitutionalView | `InstitutionalView.tsx:24` `space-y-4` | 0 | 0 | — | relies on `main` (works accidentally) |
| Voturi | `Voturi.tsx:62` `space-y-6` | 0 | 0 | — | relies on `main` |
| Radar | `Radar.tsx:108` `space-y-6` | 0 | 0 | — | relies on `main` |
| Grafice | `Grafice.tsx:44` `space-y-6` | 0 | 0 | — | relies on `main` |
| Topuri | `Topuri.tsx:52` `space-y-6` | 0 | 0 | — | relies on `main` |
| Ideology | `Ideology.tsx:226` `space-y-6` (also `:207` empty state) | 0 | 0 | — | relies on `main` |

**Conclusion:** 13 pages add a gutter on top of `main`; 3 add `p-6` on top of `main`; 7 rely on
`main` only. There is no route where the container owner is unambiguous.

### 1.4 Hero grammar inventory

- Already `.hero-section`: `Demographics.tsx:65`, `PartyProfile.tsx:85`, `PartyTimeline.tsx:92`, `PersonDeepDive.tsx:110` (**4**).
- Literal duplicate `min-h-screen flex flex-col justify-center py-8`: `Coalitions.tsx:58`, `CoverageView.tsx:92`, `LegislatureDetail.tsx:54`, `MpComparison.tsx:142`, `Mps.tsx:70`, `SenateHistory.tsx:50` (**6**).
- Other hero variants: `LiveDashboard.tsx:88` `py-8 sm:py-12 lg:py-14`; `Traseism.tsx:722` `py-10 sm:py-14 lg:py-16`; `SwitchLeaderboard.tsx:47` `min-h-screen mb-8`; `Committees.tsx:201` `min-h-screen flex flex-wrap …` (a toolbar given full viewport height); `Report.tsx:106` flex `<div>` (print-aware).
- `[data-moment]` groups: 14 — `:151 LiveDashboard`, `:759 Traseism`, `:112 Coalitions`, `:215 Committees`, `:144 CoverageView`, `:80 Demographics`, `:95 LegislatureDetail`, `:172 MpComparison`, `:105 Mps`, `:103 PartyProfile`, `:141 PartyTimeline`, `:146 PersonDeepDive`, `:127 Report`, `:90 SenateHistory`.
- `index.css:248-250` — `.hero-section { @apply min-h-screen flex flex-col justify-center py-8; }`.

### 1.5 Type scale inventory

29 visible/sr-only `h1` in pages + 1 in `DashboardHeader.tsx`. Visible `h1` classes:
- `text-2xl` (`InstitutionalView.tsx:26`, `PartyComparison.tsx:126`)
- `text-2xl sm:text-3xl` (`Parties.tsx:46`, `Voturi.tsx:64`, `Radar.tsx:110`, `Grafice.tsx:46`, `Topuri.tsx:54`, `Ideology.tsx:209`, `Ideology.tsx:228`)
- `text-3xl` (12 pages: Coalitions:62, Committees:205, CoverageView:96, Demographics:69, LegislatureDetail:58, MpComparison:146, Mps:74, PartyProfile:90, PartyTimeline:96, PersonDeepDive:114, SenateHistory:54, SwitchLeaderboard:53)
- `text-3xl sm:text-4xl` (`Traseism.tsx:726`, `Report.tsx:111`, `DashboardHeader.tsx` → LiveDashboard)
- Base rule `index.css:99` already sets `h1 { @apply text-3xl font-bold tracking-tight; }` — the utility simply makes the choice explicit and greppable.
- 6 `sr-only` h1 in loading/error branches (`PersonDeepDive.tsx:78,87`; `Radar.tsx:90,101`; `Topuri.tsx:34,45`) — leave untouched.

Moment figures (13 `font-black` spans): `Coalitions.tsx:113`, `Committees.tsx:216`, `CoverageView.tsx:145`, `Demographics.tsx:81`, `LegislatureDetail.tsx:96`, `LiveDashboard.tsx:152` (`text-5xl sm:text-6xl`), `MpComparison.tsx:173`, `Mps.tsx:106`, `PartyTimeline.tsx:142`, `PersonDeepDive.tsx:147`, `Report.tsx:128` (`sm:text-6xl`), `SenateHistory.tsx:91`, `Traseism.tsx:760` (`sm:text-6xl`). Outlier: `PartyProfile.tsx:105` `text-2xl font-bold` inside `[data-moment]`.

### 1.6 Radius / density inventory

- `index.css:111-113` `.card` = `rounded-xl` (12 px) + `shadow-lg`; `index.css:237-241` `.stat-card` = `rounded-xl p-4`; `index.css:243-246` `.info-graphic` = `rounded-xl p-4`; `components/InfoStat.tsx` = `rounded-xl p-4`.
- Outliers: `Traseism.tsx:97` local `StatCard` = `rounded p-3` (4 px / 12 px); `Mps.tsx:173` card = `rounded-lg` (8 px); 6 page tables = `rounded-lg` (`Coalitions.tsx:150`, `Demographics.tsx:161`, `MpComparison.tsx:258`, `PartyComparison.tsx:187`, `SenateHistory.tsx:127`, `SwitchLeaderboard.tsx:136`).
- Page `<table>` count = **23**. Explicit sizes: `text-xs` × 5 (`CoverageView.tsx:165`, `Traseism.tsx:192,235,348,513`), `text-sm` × 14, no size × 4. Cell padding observed: `py-1` (42), `py-1.5` (31), `py-2` (52), `py-2.5` (56), `py-3` (51) across pages.

---

## 2. Strategy (locked decisions)

**D1 — `main#main-content` is the ONE container owner.** Rationale: it is the only element on
every route, it already owns `max-w-7xl mx-auto min-w-0`, and removing every page-level
container class makes "equal edges" a structural invariant instead of a per-page convention.
The gutter token is literally `px-4 sm:px-6 lg:px-8` (16 / 24 / 32 px, symmetric) applied to
`main`, the header inner div and the nav. Header/nav are included so brand, nav and content
share the same left edge — this is what "equal edges" means in AP-3 / design-taste Rule 4.

Rejected alternative: keep `.wrap` as owner and add it to 10 pages. It needs the same number
of edits, keeps a second container in `main`, and leaves `p-6` roots as a third grammar.

**D2 — Shared hero recipe (template + approved rhythm variants).** Every hero follows:

```jsx
<section className="{RHYTHM}" data-enter>     {/* RHYTHM from the approved list below */}
  <div>                                       {/* width-neutral: main owns the gutter */}
    <div className="flex flex-col md:flex-row md:items-center gap-8">
      <div className="flex-1 space-y-4">
        <h1 className="page-title">…</h1>
        <p className="text-sm text-slate-400">…</p>
        <div className="mt-8 flex items-center gap-4" data-moment>
          <span className="moment-value">…</span>
          <span className="text-sm text-slate-400">…</span>
        </div>
      </div>
      <div className="w-full md:w-auto max-w-[260px]"><HeroGraphic … /></div>
    </div>
  </div>
</section>
```

Approved `RHYTHM` tokens (only these three):
- `hero-section` — full viewport (`min-h-screen flex flex-col justify-center py-8`). 11 pages.
- `py-8 sm:py-12 lg:py-14` — compact home hero (`LiveDashboard.tsx:88`).
- `py-10 sm:py-14 lg:py-16` — large movement hero (`Traseism.tsx:722`).

Compact list/table pages (`Parties`, `Voturi`, `Radar`, `Grafice`, `Topuri`, `Ideology`,
`InstitutionalView`, `PartyComparison`) keep `py-2`-style headers — they are **not** heroes.
`Committees` and `Report` keep their print-aware header `<div>` (Hero B) with `min-h-screen`
removed from Committees. The width wrapper becomes a plain `<div>` everywhere.

**D3 — One title / moment scale.** `.page-title` = `text-3xl font-bold tracking-tight
text-slate-100` (line-height 1.25), applied to **all 24 visible h1s** (23 pages +
`DashboardHeader`). The 6 `sr-only` h1s stay as-is. `.moment-value` = `text-5xl sm:text-6xl
font-bold tracking-tight tabular-nums text-slate-100` (line-height 1.1), applied to **14**
sites (13 former `font-black` + `PartyProfile`). `font-black` (900) is deliberately replaced
by `font-bold` (700) to rejoin the bold scale (AP-6). The `sm:text-6xl` step is kept for all
moments so the "dealt moment" survives; `PartyProfile` is promoted from `text-2xl` — this is
the single intentional visual promotion and is gated by the 320 px probe.

**D4 — One table/card grammar.** `.data-table { @apply w-full text-sm border-collapse; }`
plus `.data-table :is(th, td) { padding: 0.625rem 1rem; }` enforces 14 px text and 10/16 px
cell padding at the table layer, so the four authored padding variants can no longer
fragment density. Added to all **23 page tables**. Card radius canon = `rounded-xl` (12 px),
padding canon = `p-4`; the four outliers are normalized. Component-level tables
(`About.tsx:270`, `RollCallTable.tsx:77`, `TimelineChart.tsx:250`) are a different part — see §11.

---

## 3. Exclusive file list (26 — write ONLY these)

```
frontend/src/index.css
frontend/src/router.tsx
frontend/src/components/ui/DashboardHeader.tsx
frontend/src/pages/Coalitions.tsx
frontend/src/pages/Committees.tsx
frontend/src/pages/CoverageView.tsx
frontend/src/pages/Demographics.tsx
frontend/src/pages/Grafice.tsx
frontend/src/pages/Ideology.tsx
frontend/src/pages/InstitutionalView.tsx
frontend/src/pages/LegislatureDetail.tsx
frontend/src/pages/LiveDashboard.tsx
frontend/src/pages/MpComparison.tsx
frontend/src/pages/Mps.tsx
frontend/src/pages/Parties.tsx
frontend/src/pages/PartyComparison.tsx
frontend/src/pages/PartyProfile.tsx
frontend/src/pages/PartyTimeline.tsx
frontend/src/pages/PersonDeepDive.tsx
frontend/src/pages/Radar.tsx
frontend/src/pages/Report.tsx
frontend/src/pages/SenateHistory.tsx
frontend/src/pages/SwitchLeaderboard.tsx
frontend/src/pages/Topuri.tsx
frontend/src/pages/Traseism.tsx
frontend/src/pages/Voturi.tsx
```

**Do not touch:** any other `components/*` file, `tailwind.config.js`, `package*.json`,
`i18n.ts`, `api/client.ts`, backend/pipeline/data, `.github/`, `vercel.json`, the vault, or
any audit doc. No new dependency, no route/copy/colour change.

---

## 4. Preconditions

1. Worktree at the baseline tree: `git rev-parse HEAD^{tree}` → `02ac065d7326df6d801242d17998c9d207a1cb43`;
   `git status --porcelain -- frontend/src` empty. If not, **stop**.
2. `cd frontend && npm ci` (or existing `node_modules`) so `npm run lint`/`npm run build` work.
3. `python3 -c 'import playwright'` succeeds; `/usr/bin/chromium` exists; `/tmp/axe.min.js`
   exists and is non-empty **for the UI gate**. If absent, fetch once:
   `curl -fsSL https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js -o /tmp/axe.min.js`.
   If fetching is impossible, mark the UI gate **NOT PROVEN** (§12) and still run CP-R02-10.
4. An API proxy target is reachable for the browser gates:
   `PARLAMENT_API_PROXY_TARGET=https://parlament-deschis.onrender.com` (vite reads this at
   `frontend/vite.config.ts:5-9`; dev server default port 5173 — this recipe pins **5174**).
5. Snapshot the pre-edit SHA: `git rev-parse HEAD > /tmp/opencode/R-02-backup/R02_BASE_SHA`.
6. Read-only rule honoured: no product file is edited before CP-R02-01 passes.

---

## 5. Backup + checksum

Path: `/tmp/opencode/R-02-backup/` (outside the repo, so it cannot be committed).

```bash
cd /home/nedaktov/parlament-deschis
mkdir -p /tmp/opencode/R-02-backup
FILES="frontend/src/index.css frontend/src/router.tsx frontend/src/components/ui/DashboardHeader.tsx $(ls frontend/src/pages/*.tsx)"
sha256sum $FILES > /tmp/opencode/R-02-backup/manifest.sha256
sha256sum /tmp/opencode/R-02-backup/manifest.sha256
```

**Expected aggregate checksum (computed at baseline; exact):**
```
20059825d96298cac67f3028c38e92bb0ced4cc3e579a8cc5fdcaa446f0be4e3  /tmp/opencode/R-02-backup/manifest.sha256
```

Full expected manifest (also used by CP-R02-01):

```
4f73a58fc16fffba22b941958afea6946760ae53b69193dd4d3be7c04b3f4e5c  frontend/src/index.css
24abfb6eb6a25d024b3dd7e10ceddfebc39a466746f439b0e42c36fe5cd8fc56  frontend/src/router.tsx
e455e0fe9073dbd905c9770285c313b04508651b0dc8b5fd28d6f1671e616b38  frontend/src/components/ui/DashboardHeader.tsx
ef88a40c2c71b9497bceb980f97ab0bb42e61c8bb9ce2493f3ac8825c1e0660e  frontend/src/pages/Coalitions.tsx
72dea7c418674018f2fed1f1e1f8b435376b76ab703efa2a00eeb658adaae319  frontend/src/pages/Committees.tsx
fcb2069c25be7f2266573a3c221fcbda345bbecfc6959894e2f62ebb8de8669d  frontend/src/pages/CoverageView.tsx
153410d28c26b9d112be4e9330564fc6b0700c2e7b83cfeebeba1fb1d9efbcfd  frontend/src/pages/Demographics.tsx
9d94309f7c93277beb34a6603c750fe9ee3afcfa27cd3266355c89b79eeccdc7  frontend/src/pages/Grafice.tsx
a1ce44e2223365d286523ba76fe3054214677f2bdf0df19ae3bf210c8b17df4f  frontend/src/pages/Ideology.tsx
28760bbf407819abeca4241fc51dbd63a3bd0892917636c6fa6503e8894fa22c  frontend/src/pages/InstitutionalView.tsx
305842ddac7e4cacc300f6477a1a779a5be1df104f119fa6de3eb54e38570d46  frontend/src/pages/LegislatureDetail.tsx
2d2a81ca9710b9a4890a2d5c8f6b8543c4dc0fbb260486e367ca454fb7cd963e  frontend/src/pages/LiveDashboard.tsx
03a548291eb337b4c46cb8540e2f47db490d38589ec7a66cbe16a68ff833d44f  frontend/src/pages/MpComparison.tsx
df4529b1dd752f6069cd4644934654768f07e940aee124f6703bba7f281b7d33  frontend/src/pages/Mps.tsx
339d5361855b27d37072437af68c3e6fe3715841334577af9036f74c6adddc2f  frontend/src/pages/Parties.tsx
a9b1c31624a006b4f5b574adf5def2c42ce55f0272e6bbbdd26524b4b7ec4755  frontend/src/pages/PartyComparison.tsx
9dc15ee50f68cce6596d9e007a7e34a8cca46a1440380108470e7ef924fb296c  frontend/src/pages/PartyProfile.tsx
5add25969f232c2daabfe2742770561fe8262bf70b78749e2d6238181901888e  frontend/src/pages/PartyTimeline.tsx
0c2adbfab1064568734cf12903d0b8d4f063f9a768cc7722e7971527b974cc35  frontend/src/pages/PersonDeepDive.tsx
fef5f87983d7325ad297a65e64536ae5e3d7ea95fed250ea60fe78b379a7627e  frontend/src/pages/Radar.tsx
d6affe721101e7a0dbc23026dd375d7b9f048a7ac9a5f5b723a120f6dc407f13  frontend/src/pages/Report.tsx
282639853d871da3b0d00dfd92bee80d21c94905db4fd8edfebf7158dbb79a06  frontend/src/pages/SenateHistory.tsx
0521f789e88a609c7c674cf0cddc84d5a80bce860dd9e9a05a67f686f24938fe  frontend/src/pages/SwitchLeaderboard.tsx
a07a2a4e2e59c038e17a19ae3f38a8322aac0574a2100d926330e25dcfe9d8d7  frontend/src/pages/Topuri.tsx
6d7c753115d52b4e265f1f5aded775b0f735f20fe3ce622bdb9fe7b433c137d5  frontend/src/pages/Traseism.tsx
1dc2cd39de71a267c4aaebb62ef45d3fd4bfec0d8162107b5e09a59b86018c4c  frontend/src/pages/Voturi.tsx
```

The manifest is a **verification artifact**, not a restore source. If the commit was never made,
restore from git using the recorded base SHA (full command in §13):
`git restore --source="$(cat /tmp/opencode/R-02-backup/R02_BASE_SHA)" -- frontend/src/index.css frontend/src/router.tsx frontend/src/components/ui/DashboardHeader.tsx frontend/src/pages`.
Never copy files out of `/tmp` into the repo by hand.

---

## 6. Numbered steps (exact changes + commands)

All edit scripts use exact-string replacement with an **occurrence-count assertion**; a
mismatch aborts with a non-zero exit instead of silently doing the wrong thing. Run from
`/home/nedaktov/parlament-deschis`.

### Step 0 — gate the baseline
```bash
cd /home/nedaktov/parlament-deschis
git rev-parse HEAD^{tree}
git diff --quiet eb693b4 HEAD -- frontend/src; echo "baseline-tree-diff-exit=$?"
git status --porcelain -- frontend/src | wc -l
```
Expected: tree `02ac065…`, `baseline-tree-diff-exit=0`, `0`. Then run CP-R02-01 / CP-R02-02.

### Step 1 — `frontend/src/index.css`: add the three utilities, retire `.wrap`
Replace the exact block at lines 115-120:

```css
/* De-facto page wrap: constrains content width, centers it, and applies
   responsive horizontal padding so left/right content edges align across
   every route (design-taste-frontend Rule 4). */
.wrap {
  @apply max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 min-w-0;
}
```

with:

```css
/* R-02 D1 — ONE gutter token. `main#main-content` is the sole container owner:
   it owns max-width, centring and horizontal padding. Page roots MUST NOT
   declare a container class. Keep the three shell sites identical:
   px-4 sm:px-6 lg:px-8 = 16 / 24 / 32 px, symmetric at 320 / 768 / 1024. */
/* (the token is applied literally in router.tsx: main, header inner, nav) */

/* R-02 D3 — ONE page-title scale. Replaces text-2xl, text-2xl sm:text-3xl,
   text-3xl and text-3xl sm:text-4xl h1 variants (AP-6). */
.page-title {
  @apply text-3xl font-bold tracking-tight text-slate-100;
  line-height: 1.25;
}

/* R-02 D3 — ONE moment-value scale. Replaces 13x font-black text-5xl /
   text-5xl sm:text-6xl and PartyProfile's text-2xl outlier (AP-6).
   font-bold (700) rejoins the bold scale; tabular-nums keeps figures aligned. */
.moment-value {
  @apply text-5xl sm:text-6xl font-bold tracking-tight tabular-nums text-slate-100;
  line-height: 1.1;
}

/* R-02 D4 — ONE table grammar. Enforces 14px text and 10px/16px cell padding
   at the table layer so authored py-1 / py-1.5 / py-2.5 / py-3 and text-xs
   variants cannot re-fragment density (AP-6). Placed after @tailwind
   utilities, so its equal/higher specificity wins over per-cell utilities. */
.data-table {
  @apply w-full text-sm border-collapse;
}
.data-table :is(th, td) {
  padding: 0.625rem 1rem;
}
```

Replace the reflow selector at lines 126-130:

```css
main,
main .wrap,
main section {
  min-width: 0;
}
```

with:

```css
main,
main > div,
main section {
  min-width: 0;
}
```

Do **not** change `.hero-section` (`:248-250`), `.card` (`:111-113`), `.stat-card`
(`:237-241`), focus ring, print rules or the muted override.

### Step 2 — `frontend/src/router.tsx`: align the shell to one gutter
Exact single-line replacements (one each):

| Line | Old | New |
|---|---|---|
| 299 | `<main id="main-content" tabIndex={-1} className="max-w-7xl mx-auto w-full min-w-0 px-4 py-5 flex-1">` | `<main id="main-content" tabIndex={-1} className="max-w-7xl mx-auto w-full min-w-0 px-4 sm:px-6 lg:px-8 py-5 flex-1">` |
| 221 | `<div className="max-w-7xl mx-auto px-4 py-4 flex flex-col sm:flex-row sm:items-center gap-3">` | `<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row sm:items-center gap-3">` |
| 246 | `<nav className="flex gap-1 border-b border-slate-700 px-4 overflow-x-auto" aria-label={t("mainNavigation")}>` | `<nav className="flex gap-1 border-b border-slate-700 px-4 sm:px-6 lg:px-8 overflow-x-auto" aria-label={t("mainNavigation")}>` |

### Step 3 — page roots: remove every gutter declaration (17 edits)
```bash
cd /home/nedaktov/parlament-deschis
python3 - <<'PY'
from pathlib import Path
E = [
 ('pages/Coalitions.tsx',      '<div className="wrap space-y-6">',      '<div className="space-y-6">', 1),
 ('pages/Committees.tsx',      '<div className="wrap py-6 print:p-0">', '<div className="py-6 print:p-0">', 1),
 ('pages/CoverageView.tsx',    '<div className="wrap space-y-6">',      '<div className="space-y-6">', 1),
 ('pages/CoverageView.tsx',    '<section className="wrap space-y-4">',  '<section className="space-y-4">', 1),
 ('pages/Demographics.tsx',    '<div className="wrap space-y-6">',      '<div className="space-y-6">', 1),
 ('pages/LegislatureDetail.tsx','<div className="wrap space-y-6">',     '<div className="space-y-6">', 1),
 ('pages/LiveDashboard.tsx',   '<div className="wrap space-y-8">',      '<div className="space-y-8">', 1),
 ('pages/MpComparison.tsx',    '<div className="wrap space-y-6">',      '<div className="space-y-6">', 1),
 ('pages/Mps.tsx',             '<div className="wrap space-y-6">',      '<div className="space-y-6">', 1),
 ('pages/PartyProfile.tsx',    '<div className="wrap space-y-6">',      '<div className="space-y-6">', 1),
 ('pages/PersonDeepDive.tsx',  '<div className="wrap space-y-6">',      '<div className="space-y-6">', 1),
 ('pages/Report.tsx',          '<div className="wrap py-6 print:p-0">', '<div className="py-6 print:p-0">', 1),
 ('pages/SenateHistory.tsx',   '<div className="wrap space-y-6">',      '<div className="space-y-6">', 1),
 ('pages/Traseism.tsx',        '<div className="wrap space-y-6">',      '<div className="space-y-6">', 1),
 ('pages/PartyComparison.tsx', '<div className="p-6">',                 '<div className="py-6">', 1),
 ('pages/PartyTimeline.tsx',   '<div className="p-6">',                 '<div className="py-6">', 1),
 ('pages/SwitchLeaderboard.tsx','<div className="p-6">',                '<div className="py-6">', 1),
]
base = Path('frontend/src')
for f, old, new, n in E:
    p = base / f; s = p.read_text(); found = s.count(old)
    assert found == n, f'{f}: expected {n} of {old!r}, found {found}'
    p.write_text(s.replace(old, new)); print(f'OK {f}: {found}')
print(f'TOTAL {len(E)} root edits')
PY
```
`p-6` → `py-6` deliberately keeps the old vertical rhythm while deleting the horizontal gutter.

### Step 4 — inner width wrappers: 15 × `<div className="max-w-7xl mx-auto">` → `<div>`
```bash
cd /home/nedaktov/parlament-deschis
python3 - <<'PY'
from pathlib import Path
OLD='<div className="max-w-7xl mx-auto">'; NEW='<div>'; total=0
for p in sorted(Path('frontend/src/pages').glob('*.tsx')):
    s=p.read_text(); n=s.count(OLD)
    if n:
        p.write_text(s.replace(OLD,NEW)); total+=n
        print(f'OK {p.name}: {n}')
assert total==15, f'expected 15 inner wrappers, found {total}'
print(f'TOTAL {total}')
PY
```
Expected per-file counts: LiveDashboard 3; Coalitions, CoverageView, Demographics,
LegislatureDetail, MpComparison, Mps, PartyProfile, PartyTimeline, PersonDeepDive,
SenateHistory, SwitchLeaderboard, Traseism = 1 each.

### Step 5 — LiveDashboard's two extra section gutters
```bash
cd /home/nedaktov/parlament-deschis
python3 - <<'PY'
from pathlib import Path
p=Path('frontend/src/pages/LiveDashboard.tsx'); s=p.read_text()
old='<section className="px-4 pb-8 sm:pb-10" data-enter>'
new='<section className="pb-8 sm:pb-10" data-enter>'
assert s.count(old)==2, s.count(old)
p.write_text(s.replace(old,new)); print('OK LiveDashboard.tsx: 2')
PY
```

### Step 6 — hero grammar (7 edits)
```bash
cd /home/nedaktov/parlament-deschis
python3 - <<'PY'
from pathlib import Path
OLD='className="min-h-screen flex flex-col justify-center py-8"'
NEW='className="hero-section"'
E=[('Coalitions.tsx',1),('CoverageView.tsx',1),('LegislatureDetail.tsx',1),
   ('MpComparison.tsx',1),('Mps.tsx',1),('SenateHistory.tsx',1)]
for f,n in E:
    p=Path('frontend/src/pages')/f; s=p.read_text()
    assert s.count(OLD)==n, f'{f}: {s.count(OLD)}'
    p.write_text(s.replace(OLD,NEW)); print(f'OK {f}: {n}')
p=Path('frontend/src/pages/SwitchLeaderboard.tsx'); s=p.read_text()
assert s.count('className="min-h-screen mb-8"')==1
p.write_text(s.replace('className="min-h-screen mb-8"','className="hero-section"')); print('OK SwitchLeaderboard.tsx: 1')
p=Path('frontend/src/pages/Committees.tsx'); s=p.read_text()
o='className="min-h-screen flex flex-wrap items-start justify-between gap-3 mb-6 print:mb-3"'
n='className="flex flex-wrap items-start justify-between gap-3 mb-6 print:mb-3"'
assert s.count(o)==1, s.count(o)
p.write_text(s.replace(o,n)); print('OK Committees.tsx: 1 (Hero B: full-height toolbar removed)')
PY
```
No change to `LiveDashboard.tsx:88`, `Traseism.tsx:722`, `Report.tsx:106`, or the four
existing `.hero-section` pages — they already follow the approved recipe.

### Step 7 — all 24 visible `h1` → `.page-title`
```bash
cd /home/nedaktov/parlament-deschis
python3 - <<'PY'
from pathlib import Path
# (relative path, exact <h1 className="…"> opening tag, replacement, count)
E=[
 ('pages/Coalitions.tsx','<h1 className="text-3xl font-bold tracking-tight text-slate-100">','<h1 className="page-title">',1),
 ('pages/Committees.tsx','<h1 className="text-3xl font-bold tracking-tight text-slate-100 print:text-slate-900">','<h1 className="page-title print:text-slate-900">',1),
 ('pages/CoverageView.tsx','<h1 className="text-3xl font-bold tracking-tight">','<h1 className="page-title">',1),
 ('pages/Demographics.tsx','<h1 className="text-3xl font-bold tracking-tight text-slate-100">','<h1 className="page-title">',1),
 ('pages/Grafice.tsx','<h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">','<h1 className="page-title">',1),
 ('pages/Ideology.tsx','<h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">','<h1 className="page-title">',2),
 ('pages/InstitutionalView.tsx','<h1 className="text-2xl font-bold mb-3">','<h1 className="page-title mb-3">',1),
 ('pages/LegislatureDetail.tsx','<h1 className="text-3xl font-bold tracking-tight">','<h1 className="page-title">',1),
 ('pages/MpComparison.tsx','<h1 className="text-3xl font-bold tracking-tight">','<h1 className="page-title">',1),
 ('pages/Mps.tsx','<h1 className="text-3xl font-bold tracking-tight">','<h1 className="page-title">',1),
 ('pages/Parties.tsx','<h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">','<h1 className="page-title">',1),
 ('pages/PartyComparison.tsx','<h1 className="text-2xl font-bold text-slate-100 mb-2">','<h1 className="page-title mb-2">',1),
 ('pages/PartyProfile.tsx','<h1 className="text-3xl font-bold tracking-tight text-slate-100">','<h1 className="page-title">',1),
 ('pages/PartyTimeline.tsx','<h1 className="text-3xl font-bold tracking-tight">','<h1 className="page-title">',1),
 ('pages/PersonDeepDive.tsx','<h1 className="text-3xl font-bold tracking-tight">','<h1 className="page-title">',1),
 ('pages/Radar.tsx','<h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">','<h1 className="page-title">',1),
 ('pages/Report.tsx','<h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-100 print:text-slate-900">','<h1 className="page-title print:text-slate-900">',1),
 ('pages/SenateHistory.tsx','<h1 className="text-3xl font-bold tracking-tight">','<h1 className="page-title">',1),
 ('pages/SwitchLeaderboard.tsx','<h1 className="text-3xl font-bold tracking-tight text-slate-100">','<h1 className="page-title">',1),
 ('pages/Topuri.tsx','<h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">','<h1 className="page-title">',1),
 ('pages/Traseism.tsx','<h1 className="text-3xl sm:text-4xl font-bold tracking-tight">','<h1 className="page-title">',1),
 ('pages/Voturi.tsx','<h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">','<h1 className="page-title">',1),
 ('components/ui/DashboardHeader.tsx','<h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-100">','<h1 className="page-title">',1),
]
base=Path('frontend/src'); total=0
for f,old,new,n in E:
    p=base/f; s=p.read_text(); found=s.count(old)
    assert found==n, f'{f}: expected {n} of {old!r}, found {found}'
    p.write_text(s.replace(old,new)); total+=found; print(f'OK {f}: {found}')
assert total==24, total
print(f'TOTAL {total} visible h1s normalized')
PY
```
Do **not** touch the 6 `<h1 className="sr-only">` loading/error headings.

### Step 8 — 14 moment figures → `.moment-value`
```bash
cd /home/nedaktov/parlament-deschis
python3 - <<'PY'
from pathlib import Path
A='<span className="text-5xl font-black block tracking-tight">'
B='<span className="moment-value block">'
E=[
 ('pages/Coalitions.tsx','<span className="text-5xl font-black block tracking-tight text-slate-100">',B),
 ('pages/Committees.tsx',A,B),
 ('pages/CoverageView.tsx',A,B),
 ('pages/Demographics.tsx','<span className="text-5xl font-black block tracking-tight text-slate-200">',B),
 ('pages/LegislatureDetail.tsx',A,B),
 ('pages/LiveDashboard.tsx','<span className="text-5xl sm:text-6xl font-black tracking-tight text-slate-100">','<span className="moment-value">'),
 ('pages/MpComparison.tsx',A,B),
 ('pages/Mps.tsx',A,B),
 ('pages/PartyTimeline.tsx',A,B),
 ('pages/PersonDeepDive.tsx',A,B),
 ('pages/Report.tsx','<span className="text-5xl sm:text-6xl font-black block tracking-tight text-slate-100 print:text-slate-900">','<span className="moment-value block print:text-slate-900">'),
 ('pages/SenateHistory.tsx',A,B),
 ('pages/Traseism.tsx','<span className="text-5xl sm:text-6xl font-black block tracking-tight">',B),
 ('pages/PartyProfile.tsx','<span className="text-2xl font-bold text-slate-100">','<span className="moment-value">'),
]
base=Path('frontend/src')
for f,old,new in E:
    p=base/f; s=p.read_text(); found=s.count(old)
    assert found==1, f'{f}: expected 1 of {old!r}, found {found}'
    p.write_text(s.replace(old,new)); print(f'OK {f}: 1')
print(f'TOTAL {len(E)} moment values normalized')
PY
```
Keep every `moment-badge` span and `[data-moment]` wrapper unchanged.

### Step 9 — 23 page tables → `.data-table` (also fixes 6 `rounded-lg` tables)
```bash
cd /home/nedaktov/parlament-deschis
python3 - <<'PY'
from pathlib import Path
base=Path('frontend/src/pages')
G=[
 ('<table className="min-w-full bg-slate-800 rounded-lg overflow-hidden">',
  '<table className="min-w-full bg-slate-800 rounded-xl overflow-hidden data-table">',6),
 ('<table className="min-w-full text-sm">',
  '<table className="min-w-full text-sm data-table">',6),
 ('<table className="min-w-full text-sm mt-3">',
  '<table className="min-w-full text-sm mt-3 data-table">',1),
 ('<table className="w-full text-xs border-collapse">',
  '<table className="w-full data-table border-collapse">',5),
 ('<table className="w-full text-sm text-left">',
  '<table className="w-full text-sm text-left data-table">',1),
]
total=0
for old,new,n in G:
    c=0
    for p in sorted(base.glob('*.tsx')):
        s=p.read_text(); k=s.count(old)
        if k:
            p.write_text(s.replace(old,new)); c+=k; print(f'OK {p.name}: {k} ({old[:34]}…)')
    assert c==n, f'expected {n}, found {c} for {old!r}'
    total+=c
# 4 multi-line <table … className="min-w-full text-sm" …> openings
M=[
 ('Grafice.tsx','                className="min-w-full text-sm"\n              >','                className="min-w-full text-sm data-table"\n              >'),
 ('Radar.tsx',  '              className="min-w-full text-sm"\n            >','              className="min-w-full text-sm data-table"\n            >'),
 ('Topuri.tsx', '              className="min-w-full text-sm"\n            >','              className="min-w-full text-sm data-table"\n            >'),
 # Voturi has aria-label AFTER className, so disambiguate with that next line
 ('Voturi.tsx', '              className="min-w-full text-sm"\n              aria-label=', '              className="min-w-full text-sm data-table"\n              aria-label='),
]
for f,old,new in M:
    p=base/f; s=p.read_text(); assert s.count(old)==1, f'{f}: {s.count(old)}'
    p.write_text(s.replace(old,new)); total+=1; print(f'OK {f}: 1 (multiline)')
assert total==23, total
print(f'TOTAL {total} tables grammar-bound')
PY
```
`text-xs` is removed from the five tables that had it (the `.data-table` rule supplies
`text-sm`); `min-w-full` / `w-full` and all `role`/`aria-*`/`<caption>` stay untouched.

### Step 10 — card radius/density outliers (2 edits)
```bash
cd /home/nedaktov/parlament-deschis
python3 - <<'PY'
from pathlib import Path
E=[
 ('pages/Traseism.tsx','<div className="bg-slate-800/50 rounded p-3">','<div className="bg-slate-800/50 rounded-xl p-4">',1),
 # Mps.tsx:173 has the className on its own line after key={m.id}
 ('pages/Mps.tsx','            className="card-hover bg-slate-800 rounded-lg p-4 border border-slate-700/50 hover:bg-slate-750/60 transition-colors"',
                  '            className="card-hover bg-slate-800 rounded-xl p-4 border border-slate-700/50 hover:bg-slate-750/60 transition-colors"',1),
]
base=Path('frontend/src')
for f,old,new,n in E:
    p=base/f; s=p.read_text(); assert s.count(old)==n, f'{f}: {s.count(old)}'
    p.write_text(s.replace(old,new)); print(f'OK {f}: {n}')
PY
```
`.card`, `.stat-card`, `InfoStat` and `.info-graphic` already use `rounded-xl`; no change.

### Step 11 — static gates, then lint/build
Run CP-R02-03 … CP-R02-08 (§7) **in order**. Any failure → stop, fix, re-run from Step 0's
checkpoint; never weaken an assertion to make it pass.

### Step 12 — browser gates
Run CP-R02-09 (UI gate) and CP-R02-10 (320/768/1024 edge probe), §7. Capture raw output to
`/tmp/opencode/R-02-backup/{ui_validate.log,edge_probe.log}`.

### Step 13 — atomic commit (only after every checkpoint passes)
```bash
cd /home/nedaktov/parlament-deschis
git add frontend/src/index.css frontend/src/router.tsx frontend/src/components/ui/DashboardHeader.tsx frontend/src/pages
git diff --cached --stat
git commit -m "fix(R-02): one container owner, shared hero, one title/moment/table scale"
git rev-parse HEAD | tee /tmp/opencode/R-02-backup/R02_SHA
git log -1 --format='%h %s'
```
Expected `git diff --cached --stat`: **26 files changed**. No push, no tag, no deploy.

---

## 7. CHECKPOINTS (exact command → expected printed output → exit code)

Run from `/home/nedaktov/parlament-deschis` unless noted.

### CP-R02-00 — baseline identity
```bash
git rev-parse HEAD^{tree}; git diff --quiet eb693b4 HEAD -- frontend/src; echo "exit=$?"
```
Output: `02ac065d7326df6d801242d17998c9d207a1cb43` then `exit=0`. Exit **0**.

### CP-R02-01 — backup manifest
```bash
sha256sum /tmp/opencode/R-02-backup/manifest.sha256
```
Output (exact): `20059825d96298cac67f3028c38e92bb0ced4cc3e579a8cc5fdcaa446f0be4e3  /tmp/opencode/R-02-backup/manifest.sha256`. Exit **0**.
Also `wc -l < /tmp/opencode/R-02-backup/manifest.sha256` → `26`.

### CP-R02-02 — BEFORE counts (red evidence; run before Step 1)
```bash
cd frontend/src
printf 'wrap=%s inner=%s proot=%s black=%s herodup=%s title=%s moment=%s table=%s\n' \
 "$(grep -hE '(^|[[:space:]"])wrap([[:space:]]|")' pages/*.tsx | wc -l)" \
 "$(grep -hoF '<div className="max-w-7xl mx-auto">' pages/*.tsx | wc -l)" \
 "$(grep -hF '<div className="p-6">' pages/*.tsx | wc -l)" \
 "$(grep -hoF 'font-black' pages/*.tsx | wc -l)" \
 "$(grep -hF 'className="min-h-screen flex flex-col justify-center py-8"' pages/*.tsx | wc -l)" \
 "$(grep -rhoF 'page-title' pages/*.tsx components/ui/DashboardHeader.tsx index.css | wc -l)" \
 "$(grep -rhoF 'moment-value' pages/*.tsx index.css | wc -l)" \
 "$(grep -h '<table' pages/*.tsx | wc -l)"
```
Output (exact): `wrap=14 inner=15 proot=3 black=13 herodup=6 title=0 moment=0 table=23`. Exit **0**.

### CP-R02-03 — containers after Steps 3-5
```bash
cd frontend/src
printf 'wrap=%s inner=%s proot=%s shellmax=%s sectionpx=%s\n' \
 "$(grep -hE '(^|[[:space:]"])wrap([[:space:]]|")' pages/*.tsx | wc -l)" \
 "$(grep -hoF '<div className="max-w-7xl mx-auto">' pages/*.tsx | wc -l)" \
 "$(grep -hF '<div className="p-6">' pages/*.tsx | wc -l)" \
 "$(grep -c 'max-w-7xl' router.tsx)" \
 "$(grep -hF '<section className="px-4 pb-8 sm:pb-10" data-enter>' pages/LiveDashboard.tsx | wc -l)"
```
Output: `wrap=0 inner=0 proot=0 shellmax=2 sectionpx=0`. Exit **0**.
(`shellmax=2` = `main` + header inner; nav has no max-width.)

### CP-R02-04 — hero grammar after Step 6
```bash
cd frontend/src
printf 'hero=%s herodup=%s fullheight-toolbar=%s\n' \
 "$(grep -hoF 'hero-section' pages/*.tsx | wc -l)" \
 "$(grep -hF 'className="min-h-screen flex flex-col justify-center py-8"' pages/*.tsx | wc -l)" \
 "$(grep -hF 'className="min-h-screen flex flex-wrap' pages/Committees.tsx | wc -l)"
```
Output: `hero=11 herodup=0 fullheight-toolbar=0`. Exit **0**.

### CP-R02-05 — title scale after Step 7
```bash
cd frontend/src
printf 'title=%s visibleh1=%s sronly=%s oldh1=%s\n' \
 "$(grep -rhoF 'className="page-title' pages/*.tsx components/ui/DashboardHeader.tsx | wc -l)" \
 "$(grep -h '<h1' pages/*.tsx | wc -l)" \
 "$(grep -hF '<h1 className="sr-only">' pages/*.tsx | wc -l)" \
 "$(grep -hE '<h1 className="text-(2xl|3xl)' pages/*.tsx components/ui/DashboardHeader.tsx | wc -l)"
```
Output: `title=24 visibleh1=29 sronly=6 oldh1=0`. Exit **0**.

### CP-R02-06 — moment + table grammar after Steps 8-10
```bash
cd frontend/src
printf 'black=%s moment=%s table=%s oldsize=%s radiuslg=%s\n' \
 "$(grep -hoF 'font-black' pages/*.tsx | wc -l)" \
 "$(grep -rhoF 'moment-value' pages/*.tsx | wc -l)" \
 "$(grep -rhoF 'data-table' pages/*.tsx | wc -l)" \
 "$(grep -hF 'w-full text-xs border-collapse' pages/*.tsx | wc -l)" \
 "$(grep -hF 'min-w-full bg-slate-800 rounded-lg' pages/*.tsx | wc -l)"
```
Output: `black=0 moment=14 table=23 oldsize=0 radiuslg=0`.
(Counts are page uses only; the CSS definitions are checked separately in CP-R02-07.) Exit **0**.

### CP-R02-07 — CSS utility presence
```bash
cd frontend/src
grep -nE '^\.page-title \{|^\.moment-value \{|^\.data-table \{|^\.data-table :is\(th, td\)|^\.wrap \{' index.css
```
Output: exactly **4** matches (line numbers will shift with the edit, so do not assert them):
```
N:.page-title {
N:.moment-value {
N:.data-table {
N:.data-table :is(th, td) {
```
Assertion: `grep -cE '^\.page-title \{|^\.moment-value \{|^\.data-table \{|^\.data-table :is\(th, td\)' index.css` → `4`
and `grep -c '^\.wrap {' index.css` → `0`. Exit **0**.

### CP-R02-08 — lint + build
```bash
cd frontend && npm run lint; echo "lint_exit=$?"; npm run build; echo "build_exit=$?"
```
Expected printed tail (build): `✓ built in …s` / `dist/index.html …`; exact:
`lint_exit=0` and `build_exit=0`. Exit **0**.

### CP-R02-09 — UI gate (needs §4.3 axe + §4.4 API proxy)
```bash
cd /home/nedaktov/parlament-deschis
cd frontend && PARLAMENT_API_PROXY_TARGET=https://parlament-deschis.onrender.com npm run dev -- --host 127.0.0.1 --port 5174 &
# wait for "Local: http://127.0.0.1:5174/", then:
python3 scripts/ui_validate.py http://127.0.0.1:5174 | tee /tmp/opencode/R-02-backup/ui_validate.log
echo "ui_exit=${PIPESTATUS[0]}"
```
Expected final line (exact):
`UI VALIDATION PASS: 24 routes, 0 JS errors, 0 axe violations`
and `ui_exit=0`. Exit **0**. If axe is missing, the script prints `axe-SCAN-ERROR` and exits 1 → report **NOT PROVEN**, do not claim pass.

### CP-R02-10 — 320 / 768 / 1024 edge probe
Save as `/tmp/opencode/R-02-backup/edge_probe.py`, then run `python3 … http://127.0.0.1:5174`:

```python
import asyncio, sys
from playwright.async_api import async_playwright
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5174").rstrip("/")
ROUTES = ["/", "/traseism", "/leaderboard", "/demographics", "/committees", "/compare",
          "/coalitions", "/mps", "/compare-mps", "/report", "/party-timeline", "/coverage",
          "/senate-history", "/electoral", "/institutional", "/party/PSD", "/person/cb5ca84e-7bba-4d0b-bea8-91b81aa8eb53",
          "/legislature/2024", "/parties", "/Voturi", "/radar", "/grafice", "/topuri", "/ideology"]
WIDTHS = [(320, 768), (768, 1024), (1024, 768)]
JS = """() => {
  const root = document.querySelector('main > div');
  const r = root ? root.getBoundingClientRect() : null;
  const vis = el => { const b = el.getBoundingClientRect(); return b.width > 2 && b.height > 2; };
  const h1 = [...document.querySelectorAll('main h1')].filter(vis);
  return {
    left: r ? Math.round(r.left) : -1,
    right: r ? Math.round(innerWidth - r.right) : -1,
    overflow: document.documentElement.scrollWidth - innerWidth,
    h1: h1.length,
    title: h1.length ? (h1[0].classList.contains('page-title') ? 1 : 0) : 0
  };
}"""
async def main():
    ok = 0; bad = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        for route in ROUTES:
            for w, h in WIDTHS:
                p = await b.new_page(viewport={"width": w, "height": h})
                await p.goto(BASE + route, wait_until="load", timeout=30_000)
                try: await p.wait_for_load_state("networkidle", timeout=8_000)
                except Exception: pass
                await p.wait_for_timeout(3_000)
                r = await p.evaluate(JS)
                good = (r["left"] >= 0 and abs(r["left"] - r["right"]) <= 1
                        and r["overflow"] <= 1 and r["h1"] == 1 and r["title"] == 1)
                print(f"[{'OK ' if good else 'FAIL'}] {route:48s} {w:4d} L={r['left']:3d} R={r['right']:3d} ovf={r['overflow']:2d} h1={r['h1']} title={r['title']}")
                ok += good; bad += [] if good else [(route, w, r)]
                await p.close()
        await b.close()
    print(f"\nEDGE PROBE {'PASS' if not bad else 'FAIL'}: {ok}/{len(ROUTES)*len(WIDTHS)} checks")
    for route, w, r in bad: print(f"  {route}@{w}: {r}")
    return 0 if not bad else 1
if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

Expected printed tail (exact):
```
EDGE PROBE PASS: 72/72 checks
```
Expected gutter per width (symmetric, ±1 px): `320 → L=16 R=16`, `768 → L=24 R=24`,
`1024 → L=32 R=32`. Exit **0**. Any `FAIL` row → the route still owns a gutter or has an
oversized root; fix and re-run; do not widen the tolerance.

---

## 8. Verification gates (all mandatory, in this order)

| Gate | Command | Pass condition |
|---|---|---|
| Static counts | CP-R02-02 → CP-R02-07 | exact printed values in §7 |
| Type | `cd frontend && npm run lint` | exit 0 (`tsc --noEmit` + eslint) |
| Build | `cd frontend && npm run build` | exit 0 |
| UI gate | `python3 scripts/ui_validate.py …` | `UI VALIDATION PASS: 24 routes, 0 JS errors, 0 axe violations` |
| 320/768/1024 probe | CP-R02-10 | `EDGE PROBE PASS: 72/72 checks`, gutters 16/24/32 |
| Diff scope | `git diff --cached --stat` | 26 files, no file outside §3 |
| Commit | `git log -1 --format='%h %s'` | single atomic R-02 commit |

A gate that cannot run is **NOT PROVEN** (§12) — never recorded as PASS.

---

## 9. Acceptance criteria

1. `frontend/src/router.tsx:299` is the only max-width + gutter owner; `grep -hE '(^|[[:space:]"])wrap([[:space:]]|")' frontend/src/pages/*.tsx` → **0**; `grep -c 'max-w-7xl' frontend/src/router.tsx` → **2**.
2. At 320 / 768 / 1024 every one of the 24 routes has `left == right` (±1 px) at 16 / 24 / 32 px and `scrollWidth <= innerWidth + 1`.
3. Exactly 24 visible `h1` carry `page-title`; 6 `sr-only` h1s unchanged; no `text-2xl`/`text-3xl sm:text-4xl` h1 remains.
4. `font-black` count in pages = 0; `moment-value` count = 14; each hero has one `[data-moment]`.
5. All 23 page tables carry `data-table`; no `text-xs` table or `rounded-lg` stat/table remains.
6. `.card`, `.stat-card`, `InfoStat` radius/density unchanged (`rounded-xl`, `p-4`).
7. Lint, build, UI gate and edge probe all green; 26-file atomic commit; no push/deploy.
8. No data/route/i18n/colour/interaction change — `git diff --cached` shows only class strings and the three new CSS blocks.

---

## 10. Dependencies

- **Before R-02:** clean baseline tree; §4 preconditions. No other agent may be editing the 26 files.
- **After R-02:** R-01 (HeroGraphic colour/paint) inherits the shared hero template; R-03 (state
  components) and R-04 (component-level tables: `About.tsx`, `RollCallTable.tsx`,
  `TimelineChart.tsx`) can proceed independently. R-02 does **not** wait for those.
- **Tools:** Node/npm (locked), system `python3` + `playwright` + `/usr/bin/chromium`,
  `/tmp/axe.min.js`, reachable API proxy.
- **No new npm dependency, no config file, no CI change.**

---

## 11. Side-quest policy (REJECT on sight)

Out of scope for R-02 — do not fix even if noticed while editing:
1. AP-1 `HeroGraphic` variant colours; AP-2 `DataBar`/`ProgressRing` paint; AP-4 tokens;
   AP-5 muted hierarchy; AP-7 canvas colours; AP-8 shared state components.
2. X1–X6 content honesty, `useAsOf`, i18n keys, orphan routes, provenance rendering.
3. TA-* keyboard/semantics, `min-h-11`, tooltips, dialogs, reduced-motion on canvases.
4. Component-level tables (`About.tsx:270`, `RollCallTable.tsx:77`, `TimelineChart.tsx:250`).
5. Print layout polish (Report sparkles `print:hidden`) beyond keeping existing `print:*` classes.
6. Adding a badge utility or a `surface` utility — those belong to the sibling "visual
   primitives" part; this recipe only adds `page-title`, `moment-value`, `data-table`.
7. Editing the vault, audit docs, other recipes, or the baseline tag/commit.

If a checkpoint fails because of one of these, record it and continue — do not "drive by" fix it.

---

## 12. NOT PROVEN (must be stated, not inferred)

Everything in this recipe is **static-code evidence + proposed edits**. At authoring time:
- No browser render, screenshot, computed-style or contrast measurement was taken.
- **320/768/1024 reflow is a proposed probe, not an observed result.** The 16/24/32 gutter
  values are arithmetic from `px-4 sm:px-6 lg:px-8`; they must be confirmed by CP-R02-10.
- The UI gate (CP-R02-09) was **not run**: `/tmp/axe.min.js` was absent at authoring time and
  no dev server was started. Until it runs green, "0 axe violations" is NOT PROVEN.
- `npm run lint` / `npm run build` were not run as part of authoring; exit 0 is a target, not an observation.
- Contrast of `.moment-value` / `.page-title` is inherited from the verified `text-slate-100`
  on `--ink`/`--panel`; it is **arithmetic**, not measured.
- `PartyProfile`'s promotion from `text-2xl` to `text-5xl sm:text-6xl` and Committees'
  `min-h-screen` removal are deliberate visual changes; their acceptability is only proven by
  the browser probe + human review, not by this document.
- Print rendering after the `.data-table` padding override is NOT PROVEN (no print preview).

---

## 13. ROLLBACK (`git revert`)

Primary rollback — undo the atomic R-02 commit **without force-push or tag deletion**:

```bash
cd /home/nedaktov/parlament-deschis
SHA=$(cat /tmp/opencode/R-02-backup/R02_SHA)      # written by Step 13
git rev-parse --verify "$SHA"
git revert --no-edit "$SHA"
echo "revert_exit=$?"
git log -2 --format='%h %s'                       # newest = Revert "fix(R-02): …"
npm --prefix frontend run lint && npm --prefix frontend run build
sha256sum /tmp/opencode/R-02-backup/manifest.sha256   # still 20059825… (backup intact)
```

Expected: `revert_exit=0`; two top commits (`Revert "fix(R-02)…"` then `fix(R-02)…`);
lint/build exit 0; restored files hash-match the §5 manifest (verify with
`FILES=…; sha256sum $FILES | diff - /tmp/opencode/R-02-backup/manifest.sha256` → empty diff).

If the commit was never created (failure during Steps 1-12), restore from the recorded base:

```bash
BASE=$(cat /tmp/opencode/R-02-backup/R02_BASE_SHA)
git restore --source="$BASE" -- frontend/src/index.css frontend/src/router.tsx \
  frontend/src/components/ui/DashboardHeader.tsx frontend/src/pages
git status --porcelain -- frontend/src | wc -l    # -> 0
```

If the commit was already merged by the supervisor, revert on that branch with the same
`git revert --no-edit <R02_SHA>`; never rewrite shared history.

---

## 14. Output / evidence log (agent must return this)

```
ID / ROLE              R-02 — layout, containers, type scale
BASELINE               eb693b4 (tree 02ac065…); HEAD 80d91a9 (same tree)
BACKUP                 /tmp/opencode/R-02-backup/manifest.sha256 (20059825…)
COMMIT SHA             <from Step 13>
DIFF STAT              <26 files changed>
CHECKPOINTS            CP-R02-00 … CP-R02-10: command → raw output → PASS/FAIL
LINT / BUILD           exit codes + raw tail
UI GATE                raw ui_validate.log tail (or NOT PROVEN + reason)
EDGE PROBE             raw edge_probe.log tail (72/72 or FAIL rows)
SELF-VERDICT           PASS only if every gate above is green; otherwise REJECT
NOT PROVEN             list every unrun gate from §12
```
