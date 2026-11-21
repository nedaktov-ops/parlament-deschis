# R-03 — Unified `useScope()` hook + date scope controls (STRATEGY/RECIPE)

**Status:** recipe only. No product code was edited to produce this document.
**Baseline:** `eb693b4` (merge PR #69, `docs/triad-audit`). Working tree at planning time was
`80d91a90` (descendant, docs-only); `git diff --stat eb693b4..HEAD -- frontend/src backend tests docs/API.md scripts`
is **empty**, so every `path:line` below is valid for both commits. Re-verify before implementation:
`git rev-parse HEAD` and re-run that diff.

**Owner:** backend + frontend implementer assigned after plan approval.
**Write scope:** this document only. Product edits are authorised **only** for the file list in §3,
and only after the preconditions in §4 and a fresh backup (§9).

---

## 1. Objective

Make `?date=…` (and `?chamber=…`, `?legislature=…`) a **real scope** instead of a URL veneer, with one
source of truth and honest disclosure where the backend cannot honour a dimension.

1. One `useScope()` hook reads route search once and returns `{date, chamber, legislature, scopeKey, setScope, searchFor}`.
2. Every scope-dependent `useQuery` includes `...scopeKey` in its key and passes **only the params the endpoint actually supports**.
3. Every filter control writes to the URL; back/forward and deep links restore it (FN-7).
4. Where an endpoint cannot apply `as_of`, either (a) map `date` to a supported temporal param with an
   honest label, (b) wire chamber/legislature and expose client-side row filters, or (c) **relabel the
   view as unscoped** — never show a control that silently does nothing (§6 decision table).
5. Exactly two small, additive backend extensions (§5.5) for the two pages where point-in-time data is
   otherwise unreachable; no changes to the deliberately unscoped export/coverage surfaces.

**Non-goals (explicitly another recipe's work):** count labels/denominators (X1/FN-3/FN-9), null→0 and
state gating (FN-4/FN-5), i18n key sweep beyond the new scope keys (X4), design-system/visual fixes
(AP-1…AP-7), nav/route de-orphaning (X5), provenance rendering (X6). Do not fold them in (§12).

---

## 2. Evidence (static-code reading, `path:line`)

### 2.1 Audit inputs
| Finding | Source |
|---|---|
| FN-1 — `date`/`as_of` is a URL veneer; only InstitutionalView and LegislatureDetail wire it; "One shared `useAsOf()` hook is the root fix" | `Parlament Deschis Obsidian vault/40-FRONTEND/TRIAD-AUDIT-2026-11-21.md:63` |
| FN-7 — filter/sort/pagination/selection state not in URL | same vault file `:69` |
| Positive pattern to preserve: InstitutionalView's `useSearch → asOf → query key + API param → navigate(replace)`; LegislatureDetail's date clamping | same vault file `:74` |
| Enhancement order #2 — "One scope hook … included in every query key and API call; add in-page date controls where missing" | same vault file `:79` |
| X2 — date accepted in URL but ignored by most pages; "any moment 1990–today is not delivered" | `Parlament Deschis Obsidian vault/40-FRONTEND/FRONTEND-AUDIT-2026-11-21.md:40` |
| Recommended order #2 — wire route search into queries, start with Committees/PersonDeepDive/PartyComparison | same file `:97-98` |
| Both audits: no browser/axe/runtime proof | TRIAD `:19,87-89`; FRONTEND `:22-23,109-114` |

### 2.2 Router / URL contract
- `frontend/src/router.tsx:37-43` — `validateDateSearch()` returns **only** `{date}`; invalid → `localISODate()`.
- `frontend/src/router.tsx:90-109` — `NavLink` re-validates `date` from `location.href` and spreads `previous` search.
- `frontend/src/router.tsx:182-184` — `RootLayout` re-parses `date` for the global search box.
- `frontend/src/router.tsx:315-498` — 24 route definitions; **all** use `validateDateSearch` except `/traseism`
  (`:366-378`, which adds `chamber`/`legislature`) and `/electoral` (`:322-336`, a redirect that emits all three).
- `frontend/src/router.tsx:500-525` — route tree. `:531-549` — `stringifySearch` skips `undefined`, `parseSearch`
  drops empty values (so absent scope stays out of the URL). `:566-575` — `QueryClient` 1 h stale / 24 h gc —
  **scope must be in the key or a date change serves stale cache**.
- `frontend/src/utils/date.ts:1-15` — `isISODate()` (strict `YYYY-MM-DD`, real calendar date) and `localISODate()`.

### 2.3 API client (which endpoint takes what)
- `frontend/src/api/client.ts:408-409` `chamber(asOf, chamber)`; `:418` `person(id)` — **no as_of**; `:427`
  `committees(asOf)`; `:429-430` `crossChamber(asOf)`; `:449-450` `dashboardStats(asOf)`;
  `:452-463` `votes({chamber, legislature, from, to, limit, offset})`; `:476-500` `voteCohesion(chamber,
  legislature)` / `voteActivity(chamber, legislature, from, to)`; `:502-516` `scorecard(legislature, chamber, …)`;
  `:519-539` `withScope()` + export URLs (chamber/legislature only); `:640-669` traseism (chamber/legislature);
  `:720-731` `generationalShift(legislature, asOf)`; `:778-791` `committees(asOf)` / `committeeMembers(id, asOf)`;
  `:826-837` `committeeControl(legislature, asOf)`; `:874-880` `ideology(year)` — **survey year, not a date**.
- No hooks directory exists (`frontend/src` subdirs: `api`, `components`, `components/ui`, `pages`, `utils`);
  `grep -rn "useAsOf\|useScope" frontend/src` → no match.

### 2.4 Backend scope surface (`backend/routers/api.py`, prefix `/api`)
| Endpoint | as_of | chamber | legislature | other temporal | line |
|---|---|---|---|---|---|
| `/meta` | – | – | – | – | `:217-219` |
| `/chamber` | ✅ | ✅ | – | – | `:222-229` |
| `/timeline` | – | ✅ | – | `from`/`to`, `step_days` | `:232-263` |
| `/persons` | – | ✅ | – | – | `:266-274` |
| `/mps` | ❌ | ❌ | ❌ | – | `:277-375` |
| `/persons/{id}` | ❌ | – | – | – | `:386-392` |
| `/movements` | – | ✅ | – | `from`/`to` | `:395-406` |
| `/events/recent` | – | ✅ | ✅ | – | `:409-416` |
| `/coverage`, `/coverage/detailed`, `/coverage/dimensions` | ❌ | ❌ | ❌ | – | `:419-441` |
| `/committees` | ✅ | ❌ | ❌ | – | `:444-477` |
| `/committees/{id}/members` | ✅ | ❌ | ❌ | – | `:480-545` |
| `/parties` | ❌ | ❌ | ❌ | – | `:602-666` |
| `/party/{short}`, `/party/{short}/movements` | ✅ | – | – | – | `:669-687` |
| `/party/{short}/timeline` | – | – | – | `from`/`to` | `:690-701` |
| `/analytics/cross-chamber` | ✅ | – | – | – | `:886-899` |
| `/analytics/committee-control` | ✅ | ❌ | ✅ | – | `:902-926` |
| `/analytics/generational-shift` | ✅ | ❌ | ✅ | – | `:929-947` |
| `/analytics/party-timeline` | ❌ | ❌ | ❌ | – | `:955-1019` |
| `/dashboard/stats` | ✅ | – | – | – | `:1022-1112` |
| `/votes` | – | ✅ | ✅ | `from`/`to` | `:1115-1185` |
| `/analytics/vote-cohesion` | ❌ | ✅ | ✅ | – | `:1276-1334` |
| `/analytics/vote-activity` | – | ✅ | ✅ | `from`/`to` | `:1337-1406` |
| `/votes/scorecard` | ❌ | ✅ | ✅ | – | `:1408-1462` |
| `/analytics/ideology` | – | – | – | `year` (CHES survey year) | `:1562-1591` |
| `/traseism/summary`, `/traseism/switches` | – | ✅ | ✅ | – | `:1648-1682` |
| `/analytics/switch-leaderboard`, `/analytics/switch-waves` | – | ✅ | ✅ | – | `:1684-1720`, `:829-863` |
| `/api/export/report` | ❌ **by design** | ❌ | ❌ | – | `backend/routers/exports.py:162-187` |
| `/api/export/popolo`, `/*.csv` | – | ✅ | ✅ | – | `backend/routers/exports.py:25-33,40-45,190-198` |

Supporting contracts:
- `_parse_date()` at `backend/routers/api.py:75-81` — invalid `as_of` is a **422**, never a silent fallback.
- `_parse_vote_bound()` at `:95-116` — accepts ISO or `DD.MM.YYYY`; `/votes` filters in Python via `_vote_day`
  (`:1142-1153`) because `Vote.vote_time` is `String(32)` (`pipeline/db.py:368`), **not** a SQL date.
- `backend/cache.py:38-74` — cache key is label + every non-session arg, so adding optional scope params cannot
  cross-contaminate cached responses. (Still add scope to the React Query key; §1.2.)
- `tests/test_export_report.py:195-232` — asserts `/api/export/report` returns `scope == "all"`, ignores legacy
  `?chamber=&legislature=`, and advertises **no** scope params in OpenAPI. Hard constraint: do not extend it.

### 2.5 Pages that already wire date (preserve + migrate to the hook)
- `frontend/src/pages/InstitutionalView.tsx:9-21` (key + param), `:32-43` (date input, `navigate(..., replace:true)`).
- `frontend/src/pages/LegislatureDetail.tsx:14-37` (clamp to legislature start/end, key, param), `:161` (nav link).
- Also partially wired: `PartyProfile.tsx:18-32`, `LiveDashboard.tsx:26-36,49-77`, `Traseism.tsx:667-696`,
  `SwitchLeaderboard.tsx:34`, `Parties.tsx:14-16` (reads date but does not use it in the query).

### 2.6 Pages that ignore it (migration targets)
`Committees.tsx:159-171` (local `chamber` state, unscoped keys/APIs; links `:31,:323` use `localISODate()`);
`CoverageView.tsx:28-31`; `SenateHistory.tsx:37-40`; `Report.tsx:62-72`; `Parties.tsx:19-22`;
`PartyComparison.tsx:36-54`; `PersonDeepDive.tsx:33-40`; `Mps.tsx:31-62`; `MpComparison.tsx:31-50`;
`Voturi.tsx:11-24`; `Radar.tsx:22-39`; `Grafice.tsx:11-19`; `Topuri.tsx:18-24`; `Ideology.tsx:47-52`;
`Demographics.tsx:24-29`; `PartyTimeline.tsx:50-54,108`.

### 2.7 Tooling / gates
`frontend/package.json:6-11` — `lint` = `tsc --noEmit && eslint src --ext .ts,.tsx`; `build` = `tsc -b && vite build`;
**no `npm test`** (`Parlament Deschis Obsidian vault/40-FRONTEND/QA-AND-AXE.md:68-70`).
`scripts/ui_validate.py:26-27,47-75,78-120` — 24 routes, needs `/tmp/axe.min.js` (axe-core 4.10.2), Playwright +
Chromium in **system** python3; zero JavaScript errors + 0 axe violations. `frontend/vite.config.ts:12-19` — dev port **5173**,
`/api` proxied to `127.0.0.1:8000`. `backend/main.py:161-183` — `app = create_app()`; routers carry `/api` prefix.
`pyproject.toml:24-30,42-57` — dev extras pytest/ruff/httpx, `testpaths=["tests"]`, ruff line-length 100.

---

## 3. Exclusive file list (implementer may touch ONLY these)

**New**
1. `frontend/src/hooks/useScope.ts`
2. `frontend/src/components/ScopeControls.tsx`
3. `tests/test_scope_backend.py`

**Modified — shell/API/i18n**
4. `frontend/src/router.tsx`
5. `frontend/src/api/client.ts`
6. `frontend/src/i18n.ts` (scope keys only, both locales)
7. `backend/routers/api.py` (only the two additive extensions in §5.5)
8. `backend/queries.py` (only `get_person(..., as_of=...)`)
9. `docs/API.md` (document the two new query params)

**Modified — pages (23; "adopt" = no behaviour change, just switch to the hook)**
10. `InstitutionalView.tsx` (adopt) 11. `LegislatureDetail.tsx` (adopt, keep clamp)
12. `PartyProfile.tsx` (adopt) 13. `LiveDashboard.tsx` (adopt) 14. `Traseism.tsx` (adopt)
15. `SwitchLeaderboard.tsx` (adopt) 16. `Coalitions.tsx` (adopt — wire existing `switchWaves` scope)
17. `Committees.tsx` 18. `CoverageView.tsx` 19. `SenateHistory.tsx` 20. `Report.tsx`
21. `Parties.tsx` 22. `PartyComparison.tsx` 23. `PersonDeepDive.tsx` 24. `Mps.tsx`
25. `MpComparison.tsx` 26. `Voturi.tsx` 27. `Radar.tsx` 28. `Grafice.tsx` 29. `Topuri.tsx`
30. `Ideology.tsx` 31. `Demographics.tsx` 32. `PartyTimeline.tsx`
(all under `frontend/src/pages/`)

**Explicitly OUT of scope — do not edit:** `backend/routers/exports.py`, `tests/test_export_report.py`,
`frontend/package.json`, `docs/FRONTEND-AUDIT*`, any Obsidian vault file, any design-system component other than
the new `ScopeControls.tsx`, `frontend/src/components/DataViz.tsx`, `index.css`, `tailwind.config.js`.
If a fix seems to require one of these, stop and log it under §12.

---

## 4. Preconditions

- [ ] Product tree clean for §3 files: `git status --porcelain -- frontend/src backend tests docs/API.md` empty
      (it was empty at planning time; untracked `.nedcode/` and the vault backlink file are unrelated).
- [ ] Baseline confirmed: `git rev-parse HEAD`; if it is neither `eb693b4` nor a docs-only descendant,
      stop and re-baseline the `path:line` evidence in §2.
- [ ] No other agent is editing §3 files concurrently (exclusive lock announced to the coordinator).
- [ ] Backup created and checksum recorded per §9 **before the first edit**.
- [ ] Python dev env: `.venv/bin/python -V` → 3.12+; `.venv/bin/pytest --version`; `.venv/bin/ruff --version`.
- [ ] Node env: `node -v`, `npm -v`, `npm --prefix frontend ls --depth=0` resolves without error.
- [ ] Backend runnable: `.venv/bin/python -c 'from backend.main import app; print(len(app.routes))'` (no import error).
- [ ] API server for probes: `.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --log-level warning`
      (background). Vite dev server for UI gate: `npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173`
      (background). Both respond: `curl -fsS http://127.0.0.1:8000/api/health | head -c 120`;
      `curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:5173/` → `200`.
- [ ] UI gate prerequisites: system `python3 -c 'import playwright'`, a Chromium binary, and
      `/tmp/axe.min.js`. If missing: `curl -fsSL https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js -o /tmp/axe.min.js`
      then `sha256sum /tmp/axe.min.js` (record the hash). **Gate is NOT PROVEN without this file.**
- [ ] Read §6 decision table and §10 acceptance criteria before touching a page.

---

## 5. Numbered implementation steps (with exact code)

### 5.1 Step 1 — Router: one validator, all routes (file 4)

Replace `validateDateSearch` (`router.tsx:37-43`) with the scope validator. **Delete the old name entirely** —
`frontend/tsconfig.json` sets `noUnusedLocals: true`, so a leftover alias fails lint. Update all 24 route
references in the same edit:

```ts
import { isISODate, localISODate } from "./utils/date";

export type ChamberScope = "deputies" | "senate";

function validateScopeSearch(search: Record<string, unknown>) {
  const chamber: ChamberScope | undefined =
    search.chamber === "senate" || search.chamber === "deputies" ? search.chamber : undefined;
  const legislature =
    typeof search.legislature === "string" && /^\d{4}$/.test(search.legislature)
      ? search.legislature
      : undefined;
  return {
    ...search,                       // preserve unknown/page-local params (FN-7)
    date: isISODate(search.date) ? search.date : localISODate(),
    chamber,
    legislature,
  };
}
```

- In `router.tsx:370-378` (`/traseism`), delete the local inline validator and use `validateScopeSearch`
  (it now produces exactly the same three fields, with `/^\d{4}$/` validation).
- Apply `validateScopeSearch` to **every** `createRoute` from `:315` to `:498` (24 routes), replacing each
  `validateDateSearch` reference. Do not change `beforeLoad` of `/electoral` (`:322-336`) — it already emits
  all three fields and is now type-consistent.
- In `NavLink` (`:90-109`) replace the local `validateDateSearch({date: new URLSearchParams(query).get("date")}).date`
  with one `useScope()` call (§5.2) and `search={(prev) => ({...prev, ...scope.searchFor()})}` so navigation
  preserves chamber/legislature instead of only date. Keep the existing `isActive` logic verbatim.
- In `RootLayout` (`:182-184`) replace the hand parse with `const scope = useScope();` and use `scope.date`
  for the global `Search → /person/$id` navigation (`:227-231`); add `...scope.searchFor()`.
- Leave `stringifySearch`/`parseSearch` (`:531-549`) and `QueryClient` (`:566-575`) unchanged. `undefined`
  scope values are omitted from the URL automatically.

**CHECKPOINT CP-1** — exact command / expected / exit:
```
cd /home/nedaktov/parlament-deschis/frontend && npm run lint
```
Expected: `> tsc --noEmit && eslint src --ext .ts,.tsx`; **0 errors**; at most the 7 documented pre-existing
`react-hooks/exhaustive-deps` warnings (QA-AND-AXE.md:64-66). Exit **0**. If new TS errors mention
`validateSearch`/`search` types, the route validator was not applied uniformly — fix before continuing.

---

### 5.2 Step 2 — The hook (new file 1: `frontend/src/hooks/useScope.ts`)

```ts
import { useCallback } from "react";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { isISODate, localISODate } from "../utils/date";
import type { ChamberScope } from "../router";

export interface Scope {
  date: string;                    // always a validated ISO date
  chamber?: ChamberScope;          // undefined = no chamber filter requested
  legislature?: string;            // undefined = no legislature filter requested
}

/** Stable, cache-safe representation of the active scope (order matters). */
export function scopeKeyOf(s: Scope): readonly [string, string, string] {
  return [s.date, s.chamber ?? "*", s.legislature ?? "*"];
}

/**
 * Single source of truth for route-driven scope. Pure: no fetching, no clamping.
 * Pages that need legislature bounds (LegislatureDetail) apply their own clamp
 * to `date` after `api.meta` resolves — the classic pattern at LegislatureDetail.tsx:20-29.
 */
export function useScope(): Scope & {
  scopeKey: readonly [string, string, string];
  setScope: (patch: Partial<Scope>) => void;
  searchFor: (extra?: Record<string, unknown>) => Record<string, unknown>;
} {
  const raw = useSearch({ strict: false }) as Record<string, unknown>;
  const navigate = useNavigate();

  const date = isISODate(raw.date) ? raw.date : localISODate();
  const chamber: ChamberScope | undefined =
    raw.chamber === "senate" || raw.chamber === "deputies" ? raw.chamber : undefined;
  const legislature =
    typeof raw.legislature === "string" && /^\d{4}$/.test(raw.legislature)
      ? raw.legislature
      : undefined;
  const scope: Scope = { date, chamber, legislature };

  const setScope = useCallback(
    (patch: Partial<Scope>) => {
      navigate({
        // functional updater: never drop page-local params (q, sort, offset, year, …)
        search: (prev) => ({ ...(prev as Record<string, unknown>), ...patch }),
        replace: false, // back/forward must step through filter changes (FN-7)
      });
    },
    [navigate],
  );
  const searchFor = useCallback(
    (extra: Record<string, unknown> = {}) => ({ ...scope, ...extra }),
    [date, chamber, legislature], // eslint-disable-line react-hooks/exhaustive-deps
  );

  return { ...scope, scopeKey: scopeKeyOf(scope), setScope, searchFor };
}
```

Rules for implementers:
- **Never** read `location.href`/`URLSearchParams` for scope in a page again (that is the old split-brain).
- `setScope({chamber: undefined})` clears the param; `stringifySearch` drops `undefined` from the URL.
- Keep `replace: false` for select/filter changes. Date inputs may pass `replace: true` via a direct
  `navigate` only if the page already did so (`InstitutionalView.tsx:39`) — preserve that behaviour there.
- `scopeKey` is `[date, chamber ?? "*", legislature ?? "*"]` — spread it as the **last** elements of every
  scope-dependent query key so cache entries can never collide across dates.

**CHECKPOINT CP-2** —
```
cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build
```
Expected: CP-2 passes lint; `> tsc -b && vite build` ends with `✓ built in …s`; exit **0**.

---

### 5.3 Step 3 — Shared controls (new file 2: `frontend/src/components/ScopeControls.tsx`)

One component so no page re-invents a date input. It renders only the dimensions a page actually honours.

```tsx
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { useScope } from "../hooks/useScope";
import { localISODate } from "../utils/date";

interface Props {
  showDate?: boolean;
  showChamber?: boolean;
  showLegislature?: boolean;
  /** Honest disclosure, e.g. "no point-in-time data for this view". */
  note?: string;
}
const FALLBACK_LEGISLATURES = ["1990","1992","1996","2000","2004","2008","2012","2016","2020","2024"];

export default function ScopeControls({ showDate, showChamber, showLegislature, note }: Props) {
  const { t } = useTranslation();
  const scope = useScope();
  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  const legislatures = Object.keys(meta.data?.legislatures ?? {}).length
    ? Object.keys(meta.data!.legislatures)
    : FALLBACK_LEGISLATURES;
  const today = localISODate();
  if (!showDate && !showChamber && !showLegislature && !note) return null;
  const inputCls =
    "bg-slate-800 border border-slate-600 rounded-md px-3 py-2 text-sm min-h-11 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400";
  return (
    <fieldset className="card p-3 flex flex-wrap items-end gap-4" aria-label={t("scope.title", "Scope")}>
      {showDate && (
        <label className="flex flex-col gap-1 text-xs text-slate-300">
          {t("asOf")}
          <input id="scope-date" type="date" className={inputCls}
            min="1990-01-01" max={today} value={scope.date}
            onChange={(e) => { if (e.target.value) scope.setScope({ date: e.target.value }); }} />
        </label>
      )}
      {showChamber && (
        <label className="flex flex-col gap-1 text-xs text-slate-300">
          {t("filter.chamber", "Chamber")}
          <select id="scope-chamber" className={inputCls} value={scope.chamber ?? ""}
            onChange={(e) => scope.setScope({ chamber: (e.target.value || undefined) as "deputies" | "senate" | undefined })}>
            <option value="">{t("scope.allChambers", "All chambers")}</option>
            <option value="deputies">{t("deputies", "Deputies")}</option>
            <option value="senate">{t("senate", "Senate")}</option>
          </select>
        </label>
      )}
      {showLegislature && (
        <label className="flex flex-col gap-1 text-xs text-slate-300">
          {t("filter.legislature", "Legislature")}
          <select id="scope-legislature" className={inputCls} value={scope.legislature ?? ""}
            onChange={(e) => scope.setScope({ legislature: e.target.value || undefined })}>
            <option value="">{t("scope.allLegislatures", "All legislatures")}</option>
            {legislatures.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </label>
      )}
      {note && <p className="text-xs text-slate-500 max-w-xl" role="note">{note}</p>}
    </fieldset>
  );
}
```

All new keys (`scope.title`, `scope.allChambers`, `scope.allLegislatures`, plus the per-page notes in §6)
must be added to **both** `ro` and `en` blocks of `frontend/src/i18n.ts` (file 6); existing `asOf`, `chamber`,
`legislature`, `filter.chamber`, `filter.legislature`, `deputies`, `senate` already exist
(`i18n.ts:11,140,457,458,574` and `:92`).

---

### 5.4 Step 4 — API client additions (file 5)

Add an exported response type and a scope-aware helper next to the existing `VotesFilters` (`:374-381`), and
extend `person`/`mps` accessors. Keep every existing signature working (default parameters).

```ts
export interface MpCard {
  id: string;
  name: string;
  birth_date: string | null;
  age: number | null;
  party: string | null;
  switches: number;
  committees: number;
}
export interface MpsResponse {
  status: string;
  data: MpCard[];
  offset: number;
  limit: number;
  total: number;
  scope: { as_of: string | null; chamber: string | null; legislature: string | null };
}
export interface MpsQuery {
  q?: string; sort?: string; offset?: number; limit?: number;
  chamber?: string; legislature?: string; asOf?: string;
}
export function mpsCards(query: MpsQuery = {}): Promise<MpsResponse> {
  const p = new URLSearchParams();
  if (query.q) p.set("q", query.q);
  if (query.sort) p.set("sort", query.sort);
  if (query.offset !== undefined) p.set("offset", String(query.offset));
  if (query.limit !== undefined) p.set("limit", String(query.limit));
  if (query.chamber) p.set("chamber", query.chamber);
  if (query.legislature) p.set("legislature", query.legislature);
  if (query.asOf) p.set("as_of", query.asOf);
  return get<MpsResponse>(`/mps${p.toString() ? `?${p.toString()}` : ""}`);
}

/** Map a route scope to /votes' supported parameters (date ⇒ upper bound). */
export function votesForScope(scope: { date: string; chamber?: string; legislature?: string },
                              extra: VotesFilters = {}): VotesFilters {
  return {
    chamber: scope.chamber,
    legislature: scope.legislature,
    to: scope.date,              // "votes up to <date>" — label it that way in the UI
    ...extra,                    // caller may override limit/offset/from/to
  };
}
```

Inside `api = { … }` change only `person` (`:418`):

```ts
person: (id: string, asOf?: string) =>
  get<PersonDetail>(`/persons/${encodeURIComponent(id)}${asOf ? `?as_of=${encodeURIComponent(asOf)}` : ""}`),
```

Do **not** add `as_of` to `voteCohesion`, `scorecard`, `ideology`, `parties`, `coverage*`, or export URLs —
§6 relabels those. `withScope()` (`:519-525`) stays chamber/legislature-only.

---

### 5.5 Step 5 — Two additive backend extensions (files 7, 8, 9; new test file 3)

Both are optional params that **default to today's exact current behaviour**. Both are cache-safe
(`backend/cache.py:38-74`). Invalid dates keep the existing 422 contract (`_parse_date`, api.py:75-81).

#### 5.5.a `GET /api/persons/{id}?as_of=YYYY-MM-DD` (PersonDeepDive)

`backend/queries.py:325` — change signature and filter the three dated collections:

```python
def get_person(session: Session, person_id: str, as_of: date | None = None) -> dict | None:
    ...
    if as_of is not None:
        events = [e for e in events if e.event_date is not None and e.event_date <= as_of]
        def _active(m: Membership) -> bool:
            return (
                m.start_date is not None
                and m.start_date <= as_of
                and (m.end_date is None or m.end_date > as_of)
            )
        ms = [m for m in ms if _active(m)]
        committee_ms = [m for m in committee_ms if _active(m)]
    ...
    return { ..., "as_of": as_of.isoformat() if as_of else None }
```

`backend/routers/api.py:386-392` — pass it through:

```python
@router.get("/persons/{person_id}")
@cache_result("person")
def person(person_id: str, as_of: str | None = None, db: Session = Depends(get_db)):
    data = queries.get_person(db, person_id, _parse_date(as_of, date.today()) if as_of else None)
    if data is None:
        raise HTTPException(status_code=404, detail="person not found")
    return data
```

`frontend/src/api/client.ts` — add `as_of?: string | null` to `PersonDetail` (`:75-86`).

#### 5.5.b `GET /api/mps?as_of=&chamber=&legislature=` (Mps, MpComparison)

`backend/routers/api.py:277-285` — add params and compute the reference date:

```python
@router.get("/mps")
@cache_result("mps")
def mps_cards(
    q: str | None = Query(None, max_length=200),
    limit: int = Query(60, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort: str = Query("name", pattern="^(name|age|switches|committees)$"),
    as_of: str | None = Query(None, description="Reference date (ISO format)"),
    chamber: str | None = Query(None, pattern="^(deputies|senate)$"),
    legislature: str | None = Query(None, pattern=r"^\d{4}$"),
    db: Session = Depends(get_db),
):
    ref_date = _parse_date(as_of, date.today()) if as_of else None
    from sqlalchemy import or_   # keep the existing local imports; add or_
```

Then, inside the function (line numbers shift after the edit; anchor on the commented blocks):

```python
    # Scope: persons who actually held a membership in the requested scope.
    if chamber or legislature or ref_date:
        scoped = select(Membership.person_id).where(Membership.start_date.is_not(None))
        if ref_date:
            scoped = scoped.where(
                Membership.start_date <= ref_date,
                or_(Membership.end_date.is_(None), Membership.end_date > ref_date),
            )
        if chamber:
            scoped = scoped.where(Membership.chamber == chamber)
        if legislature:
            scoped = scoped.where(Membership.legislature == legislature)
        base = base.where(Person.id.in_(scoped))

    # "switches" subquery: add to its .where(...) chain when scope is present:
    #   if ref_date: .where(Event.event_date <= ref_date)
    #   if chamber:  .where(Event.chamber == chamber)
    #   if legislature: .where(Event.legislature == legislature)
    # "committees" subquery: if ref_date add the same active-tenure predicate;
    #   if chamber add .where(Organization.chamber == chamber).
    # "latest_party" subquery: if ref_date add start_date <= ref_date and the
    #   or_(end_date is None, end_date > ref_date) predicate; if chamber/legislature
    #   add the matching Membership columns. This makes the displayed party the
    #   party *on the selected date*, not merely the latest in the corpus.
```

Implementer: apply those predicates **in the existing subquery `.where()` chains** rather than rewriting the
SQL; never change the unscoped result set when all three params are absent. Age keeps using `today`
(the person's age is not an as-of quantity) — say so in the UI note.

Return envelope (`:375`):

```python
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    return {
        "status": "ok", "data": cards, "offset": offset, "limit": limit, "total": total,
        "scope": {"as_of": ref_date.isoformat() if ref_date else None,
                  "chamber": chamber, "legislature": legislature},
    }
```

`docs/API.md` — add the three params to the `/api/mps` row and `as_of` to `/api/persons/{id}`, including
the "invalid date ⇒ 422, omitted ⇒ current behaviour" contract.

#### 5.5.c New backend tests (`tests/test_scope_backend.py`)

Use the conftest `app` fixture and a plain `TestClient(app)` (no lifespan — see `tests/test_api.py:229`):

```python
from fastapi.testclient import TestClient
import pytest

@pytest.fixture()
def client(app):
    return TestClient(app)   # canonical read-only corpus; no seeding needed

def test_person_as_of_echoes_scope_and_filters_events(client):
    pid = client.get("/api/mps", params={"limit": 1}).json()["data"][0]["id"]
    full = client.get(f"/api/persons/{pid}").json()
    scoped = client.get(f"/api/persons/{pid}", params={"as_of": "2000-01-01"}).json()
    assert scoped["as_of"] == "2000-01-01" and full.get("as_of") is None
    assert all(e["event_date"] and e["event_date"] <= "2000-01-01" for e in scoped["events"])
    assert len(scoped["events"]) <= len(full["events"])

def test_person_invalid_as_of_is_422(client):
    pid = client.get("/api/mps", params={"limit": 1}).json()["data"][0]["id"]
    assert client.get(f"/api/persons/{pid}", params={"as_of": "yesterday"}).status_code == 422

def test_mps_scope_is_echoed_and_invalid_date_rejected(client):
    r = client.get("/api/mps", params={"as_of": "2024-06-30", "chamber": "deputies", "legislature": "2024"})
    assert r.status_code == 200
    body = r.json()
    assert body["scope"] == {"as_of": "2024-06-30", "chamber": "deputies", "legislature": "2024"}
    assert body["total"] >= len(body["data"])
    assert client.get("/api/mps", params={"as_of": "not-a-date"}).status_code == 422

def test_export_report_still_advertises_no_scope(client):
    params = client.app.openapi()["paths"]["/api/export/report"]["get"].get("parameters", [])
    assert not ({"chamber", "legislature", "as_of"} & {p["name"] for p in params})
```

**CHECKPOINT CP-3** —
```
cd /home/nedaktov/parlament-deschis && .venv/bin/ruff check backend/ && \
.venv/bin/pytest -q tests/test_scope_backend.py tests/test_api.py tests/test_committee_scoping.py \
  tests/test_analytics.py tests/test_export_report.py tests/test_api_exports.py
```
Expected: ruff `All checks passed!`; pytest `… passed` with **0 failed, 0 errors** (capture the exact
`N passed` as gate evidence). `test_report_*` and `test_scoped_params_are_ignored_not_honored` must still pass.
Exit **0**.

---

### 5.6 Step 6 — Page migration (files 10–32)

#### 5.6.1 Migration order (do not parallelise across waves — later waves consume earlier hooks)

| Wave | Pages | Why this order |
|---|---|---|
| 0 | Router, hook, controls, API client, backend extensions (§5.1–5.5) | foundation; gates before any page |
| 1 | InstitutionalView, LegislatureDetail, PartyProfile, LiveDashboard, Traseism, SwitchLeaderboard, Coalitions | already wired — adopt hook only, proves no regression |
| 2 | Committees, PartyComparison, Demographics | *audit's named starting point* (FRONTEND-AUDIT:98); all backed by existing `as_of` params |
| 3 | PersonDeepDive, Mps, MpComparison | depend on the §5.5 backend extensions |
| 4 | Voturi, Radar, Grafice, Topuri | vote-scope mapping + honest relabel; depend on `votesForScope` |
| 5 | CoverageView, SenateHistory, Report, Parties, PartyTimeline, Ideology | relabel-only; no data shape change |
| 6 | i18n keys, gates, URL-persistence browser probe | last, so key-diff is complete |

#### 5.6.2 Per-page checklist

Legend: **A** = add `<ScopeControls/>`; **K** = add `...scopeKey` to every scope-dependent query key;
**P** = pass supported params to the API; **N** = render an explicit honest scope note; **U** = move a
local filter into the URL. Each row cites the current evidence from §2.6.

| # | Page (current evidence) | Supported scope → action | Checklist |
|---|---|---|---|
| 1 | `InstitutionalView.tsx:9-21,32-43` | `/chamber?as_of`, `/analytics/cross-chamber?as_of` | adopt: replace local `useSearch/navigate` with `useScope()`; keep `replace:true` on the date input; **K,P** already correct — no behaviour change |
| 2 | `LegislatureDetail.tsx:14-37` | `/chamber?as_of&chamber`, `/movements?from&to` | adopt `useScope()`; **keep** clamp `:20-29` on `scope.date`; pass `scope.chamber ?? "deputies"` explicitly (backend defaults to deputies — do not let `undefined` masquerade as "all"); **K,P** |
| 3 | `PartyProfile.tsx:18-32` | `/party/{short}?as_of`, `/party/{short}/movements?as_of` | adopt `useScope()`; **A** (date only) if no visible control exists; **K,P** already correct |
| 4 | `LiveDashboard.tsx:26-36,49-77` | `/dashboard/stats?as_of`, committee-control, cross-chamber | adopt `useScope()`; use `scope.searchFor()` for all `navigate()` calls at `:61,69,171,198,205`; **K,P** |
| 5 | `Traseism.tsx:667-696,316,602` | `/traseism/summary\|switches`, `/analytics/switch-waves` (chamber/legislature, **no as_of**) | adopt `useScope()`; **K,P** for chamber/legislature; **N**: "switch statistics are per chamber/legislature, not point-in-time"; keep date in URL for nav continuity |
| 6 | `SwitchLeaderboard.tsx:34` | `/analytics/switch-leaderboard?chamber&legislature` | adopt; add chamber control + scope to key/call; **U** `limit` |
| 7 | `Coalitions.tsx:31` | `/analytics/switch-waves?chamber&legislature` | adopt; pass scope to `switchWaves(chamber, legislature)` (currently `switchWaves()` at `:31`); **K,P**; **N** that waves are observed bursts, not coalition facts (out of scope to rewrite the copy) |
| 8 | `Committees.tsx:159-171,31,323` | `/committees?as_of` (no chamber); `/analytics/committee-control?legislature&as_of` (no chamber) | **A** date + legislature; **K,P**: `committeeControl(scope.legislature, scope.date)`, `committees(scope.date)`, `committeeMembers(id, scope.date)` (card `CommitteeCard` needs the date passed down); chamber stays a **client-side filter of the returned list** — persist it in URL via `setScope` and **N** "chamber filter applies to the returned committee list, the endpoint returns all chambers"; replace `localISODate()` links at `:31,:323` with `scope.searchFor()` |
| 9 | `PartyComparison.tsx:36-54` | `generationalShift(legislature, asOf)`; `committeeControl(legislature, asOf)`; `/parties` unscoped | **A** date + legislature; **K,P** for the two analytics calls with `...scopeKey`; **N** for the `/parties` size/switches columns ("corpus-wide, not filtered"); **U** `partyA`,`partyB` (currently `useState` `:38-39`); replace `localISODate()` at `:138` with `scope.searchFor()` |
| 10 | `Demographics.tsx:24-29` | `/analytics/generational-shift?legislature&as_of` | **A** date + legislature; **K,P**: `generationalShift(scope.legislature, scope.date)`; **N**: "chamber not filterable for this endpoint"; **U** `legislature` (replace `useState` `:24` with `scope.legislature`) |
| 11 | `PersonDeepDive.tsx:33-40` | extended `/persons/{id}?as_of` (§5.5.a) | **A** date; **K,P**: `api.person(personId, scope.date)`, key `["person", personId, ...scopeKey]`; **N**: "events and tenures are limited to the selected date"; all hooks stay before the early return (`:48-50`) |
| 12 | `Mps.tsx:31-62` | extended `/mps?as_of&chamber&legislature` (§5.5.b) | **A** date/chamber/legislature; **P**: `mpsCards({q:submitted, sort, offset, limit:PAGE_SIZE, asOf:scope.date, chamber:scope.chamber, legislature:scope.legislature})`; **K** `["mps", ...scopeKey, submitted, sort, offset]`; **U** `q`,`sort`,`offset` (currently `useState` `:53-56`); headline count from `data.total`, not `rows.length` (also serves X1/FN-3 — do not add new labels); replace `:178` link with `scope.searchFor()` |
| 13 | `MpComparison.tsx:31-50` | same as Mps | **A** + `mpsCards({limit:200, …scope})`; **K** `["mps-pool", ...scopeKey]`; **U** selection/search arrays if cheap, else log under §12; **N** "200-row pool is not the corpus total" (existing copy at `:333` already says so — do not duplicate) |
| 14 | `Voturi.tsx:11-24` | `/votes?chamber&legislature&to` | **A** date/chamber/legislature; **K,P**: `api.votes(votesForScope(scope, {limit:100}))`; **N**: "votes up to <date>"; **U** `query`, `selectedVoteId` (`:11-12`) — vote detail deep link is explicitly required by FN-7; replace local client-only filtering note at `:14-15` accordingly |
| 15 | `Radar.tsx:22-39` | `/votes?chamber&legislature&to`; positions keyed by vote id | **A** + **K,P** same as Voturi (`limit:30`); position queries keep `["radar-positions", v.native_vote_id]` (they depend on the id, not on scope); **N** for `positions_incomplete` (do not fix the flag itself — FN-8, other recipe) |
| 16 | `Grafice.tsx:11-19` | `traseismSummary(legislature, chamber)` (no as_of); `voteCohesion(chamber, legislature)` (no as_of) | **A chamber/legislature only**; **K,P**: `traseismSummary(scope.legislature ?? "2024", scope.chamber ?? "deputies")`, `api.voteCohesion(scope.chamber, scope.legislature)`; **N**: "cohesion and switch statistics are computed over all recorded votes/events in scope; there is no point-in-time filter for these endpoints" — do **not** render a date control here |
| 17 | `Topuri.tsx:18-24` | `/votes/scorecard?legislature&chamber` (no as_of) | **A chamber/legislature only**; **K,P**: `api.scorecard(scope.legislature, scope.chamber, 100, 0, minVotes)`; **N**: "scorecard covers all recorded votes in scope; no as_of"; **U** `minVotes` (`:18`) |
| 18 | `CoverageView.tsx:28-31` | `/coverage/detailed` takes **no** scope (api.py:424-427) | **no date control**; **N**: "coverage is a data-availability matrix by chamber × legislature, not a point-in-time snapshot"; chamber/legislature become **client-side row filters** persisted via `setScope`; keep `["coverage-detailed", ...scopeKey]` so the key is uniform, and disclose that only chamber/legislature affect the rows |
| 19 | `SenateHistory.tsx:37-40` | same; chamber already fixed to `senate` (`:46`) | **no date control**; **N** + client-side legislature row filter persisted in URL; keep uniform key; do not relabel the "%" stat here (X1/FN-9 — other recipe) |
| 20 | `Report.tsx:62-72` | `/api/export/report` **deliberately unscoped** (exports.py:162-187; tests/test_export_report.py:195-232) | **documented exception**: keep `queryKey: ["transparency-report"]` unchanged and add **N** "whole-corpus snapshot, generated at <generated_at>; date/chamber/legislature do not apply". Add no controls. Do not touch the endpoint or its tests. |
| 21 | `Parties.tsx:14-22` | `/parties` unscoped (api.py:602-666) | **no date control**; **N**: "corpus-wide list; not filtered by date/chamber/legislature"; **U** `q` (`:17`); replace `localISODate()`-style propagation at `:40` with `scope.searchFor()` so the party profile inherits date |
| 22 | `PartyTimeline.tsx:50-54,108` | `/analytics/party-timeline` unscoped (api.py:955-959) | **no date control**; **N**: "observed party spans from dated joins; not a point-in-time view"; adopt `useScope()` and use `scope.searchFor()` at `:108` for nav continuity; keep `["party-timeline", ...scopeKey]` uniform |
| 23 | `Ideology.tsx:47-52` | `/analytics/ideology?year` = **CHES survey year** (api.py:1566) | **no date control**; rename state to `chesYear`, URL param `chesYear`, key `["ideology", chesYear, ...scopeKey]`; **N**: "CHES expert-survey year, not a legislature or as-of date"; do **not** map `date`→`year` |

**Universal rules for wave 1–6:** no page-local `useSearch({strict:false})` casts remain; no page-local
`new URLSearchParams(location.href…)` scope reads remain; `<Link search={...}>` everywhere uses
`scope.searchFor(extra)`; no query key for a scope-dependent query lacks `...scopeKey` (Report is the only
documented exception, §5.6.2 row 20).

**CHECKPOINT CP-4** — after each wave:
```
cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build && \
grep -R "new URLSearchParams(location.href" -n src/pages src/router.tsx || true
```
Expected: lint 0 errors / ≤7 known warnings; build `✓ built`; final `grep` prints **nothing**.
Exit **0**.

---

### 5.7 Step 7 — Gates (final wave)

Run in this order; stop on the first failure.

**CHECKPOINT CP-5 (backend full suite)** —
```
cd /home/nedaktov/parlament-deschis && .venv/bin/pytest -q tests/
```
Expected: `… passed` (capture N), 0 failed / 0 errors / 0 xpass-strict. Exit **0**.
Known pre-existing skips/xfails are fine; **new** ones are a failure.

**CHECKPOINT CP-6 (API probes — proof that scope changes results)** —
```
cd /home/nedaktov/parlament-deschis
curl -fsS 'http://127.0.0.1:8000/api/chamber?as_of=2024-06-30&chamber=deputies' \
 | .venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); assert d["as_of"]=="2024-06-30" and d["chamber"]=="deputies"; print("chamber scope OK")'
PID=$(curl -fsS 'http://127.0.0.1:8000/api/mps?limit=1' | .venv/bin/python -c 'import json,sys; print(json.load(sys.stdin)["data"][0]["id"])')
curl -fsS "http://127.0.0.1:8000/api/persons/$PID?as_of=2000-01-01" \
 | .venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); assert d["as_of"]=="2000-01-01"; print("person as_of OK", len(d["events"]))'
curl -fsS 'http://127.0.0.1:8000/api/mps?as_of=2024-06-30&chamber=deputies&legislature=2024&limit=1' \
 | .venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); assert d["scope"]["as_of"]=="2024-06-30"; print("mps scope OK", d["total"])'
curl -fsS -o /dev/null -w 'report schema probe %{http_code}\n' 'http://127.0.0.1:8000/api/export/report'
```
Expected: `chamber scope OK`; `person as_of OK <n>`; `mps scope OK <n>`; `report schema probe 200`; exit **0**.
Also assert the negative contract: `curl -sS -o /dev/null -w '%{http_code}\n'
'http://127.0.0.1:8000/api/mps?as_of=nope'` → `422`.

**CHECKPOINT CP-7 (UI gate)** —
```
cd /home/nedaktov/parlament-deschis && test -s /tmp/axe.min.js && \
python3 scripts/ui_validate.py http://127.0.0.1:5173
```
Expected: 24-row per-route table; `0` JS errors; `0` axe violations; exit **0**.
`scripts/ui_validate.py:47-75` contains no query-string routes and is **not** in the §3 file list — do
not edit it. Scoped deep links are covered by the standalone browser probe in CP-8 instead.

**CHECKPOINT CP-8 (URL persistence / deep-link browser probe)** — create a temp script outside the repo
(allowed; do not track it), then run it:

```
cat > /tmp/opencode/r03_url_probe.py <<'PY'
import asyncio
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:5173"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page()
        # 1) deep link restores inputs
        await page.goto(BASE + "/committees?date=2024-06-30&chamber=senate&legislature=2024")
        await page.wait_for_load_state("networkidle")
        assert await page.input_value("#scope-date") == "2024-06-30"
        assert await page.input_value("#scope-chamber") == "senate"
        assert await page.input_value("#scope-legislature") == "2024"
        # 2) changing a filter persists to URL
        await page.select_option("#scope-chamber", "deputies")
        await page.wait_for_url("**chamber=deputies**")
        # 3) back/forward restores it (FN-7)
        await page.go_back(); await page.wait_for_load_state("networkidle")
        assert "chamber=senate" in page.url, page.url
        print("URL persistence OK")
        await b.close()

asyncio.run(main())
PY
python3 /tmp/opencode/r03_url_probe.py
```
Expected: `URL persistence OK`; exit **0**. If inputs lack those ids, add `id="scope-chamber"` /
`id="scope-legislature"` to `ScopeControls` (§5.3) and rerun.

**CHECKPOINT CP-9 (static acceptance grep)** —
```
cd /home/nedaktov/parlament-deschis/frontend/src && \
grep -R "useSearch({ strict: false })" -n pages router.tsx | grep -v hooks || true
```
Expected: **no output** (only `useScope.ts` may use `strict:false`). Exit **0**.

---

## 6. Decision table — what to do when the backend lacks `as_of`

Apply top-down; record the chosen row in the page checklist (§5.6.2).

| # | Condition | Decision | Applies to |
|---|---|---|---|
| 1 | Endpoint accepts `as_of` | Wire it; `date` in key + param + date control | chamber, committees, committee-members, party profile/movements, cross-chamber, committee-control, generational-shift, dashboard-stats |
| 2 | Endpoint accepts `from`/`to` and the data is an event stream | Map `date`→`to`, label **"up to <date>"**, keep `from` if page has its own range | `/votes` (Voturi, Radar), `/timeline`, `/movements` |
| 3 | Endpoint accepts chamber/legislature but no temporal dimension | Wire those two; add chamber/legislature controls; **no date control**; show an explicit note | traseism, switch-leaderboard, switch-waves, vote-cohesion, vote-activity, scorecard |
| 4 | Endpoint is a coverage/data-availability matrix | Relabel as "coverage by scope, not point-in-time"; chamber/legislature as client-side row filters persisted in URL; no date control; no backend change | `/coverage*`, CoverageView, SenateHistory |
| 5 | Endpoint is deliberately whole-corpus and **test-enforced** | Relabel, no controls, keep query key unscoped (documented exception). **Never** add scope params or edit its tests | `/api/export/report` (exports.py:162-187; test_export_report.py:195-232), Report |
| 6 | Endpoint is inherently historical/point-in-time-unaware and the page's value depends on it | **Extend backend** additively (optional param, default = current behaviour, 422 on bad date, cache-safe) | `/persons/{id}` (PersonDeepDive), `/mps` (Mps, MpComparison) |
| 7 | `year`/`chesYear` is a *survey* year, not a date | Keep it as a distinct, separately labelled URL param; never map `date` to it | `/analytics/ideology` (api.py:1566) |
| 8 | Endpoint ignores chamber but returns a `chamber` field | Client-side filter, persisted, with a note that filtering happens on the returned rows | `/committees` (api.py:444-477) |

**Never** solve a missing param by sending an extra query string the backend ignores — that is the exact
FN-1 failure mode. **Never** change `/export/report`, `/coverage*`, or `tests/test_export_report.py` to
"make the date work". **Never** send `as_of` to `/votes/scorecard` or `/analytics/vote-cohesion` (they would
silently ignore it today).

---

## 7. URL persistence contract

- Canonical scope params: `date` (ISO), `chamber` (`deputies|senate`), `legislature` (`\d{4}`).
  Absent = "not requested"; `date` is always materialised to today by the validator, so every URL ends up
  with an explicit `date` (same as today's behaviour, router.tsx:37-43).
- `validateScopeSearch` spreads unknown keys, so page-local params (`q`, `sort`, `offset`, `minVotes`,
  `chesYear`, `partyA`, `partyB`, `selectedVoteId`) survive navigation. Move each from `useState` to the URL
  via `setScope`/`navigate` where the checklist says **U**.
- `setScope` uses a functional updater and `replace:false`; the date input may use `replace:true` to avoid
  one history entry per keystroke (match InstitutionalView.tsx:39).
- Links use `scope.searchFor(extra)`; `stringifySearch` (router.tsx:531-539) omits `undefined`, so cleared
  filters disappear from the URL rather than becoming empty strings.
- Deep-link test (CP-8) must prove: load with query → inputs reflect it → change → URL updates → back restores.

---

## 8. Verification gates summary

| Gate | Command | Pass condition |
|---|---|---|
| Lint | `npm --prefix frontend run lint` | 0 errors |
| Typecheck+build | `npm --prefix frontend run build` | `✓ built` |
| Backend style | `.venv/bin/ruff check backend/` | `All checks passed!` |
| Backend tests (focused) | CP-3 | all pass, incl. `test_export_report.py` |
| Backend tests (full) | CP-5 | all pass |
| API probes | CP-6 | scope echoed, invalid date 422, report 200 |
| UI gate | CP-7 | 24/24 routes, zero JavaScript errors, 0 axe violations |
| URL persistence | CP-8 | `URL persistence OK` |
| Static | CP-4, CP-9 | no legacy URL reads, uniform keys |

Evidence must be **pasted into the implementation hand-off note** with the exact `N passed` counts and
exit codes. A command that cannot run is reported as **NOT PROVEN**, never as a pass.

---

## 9. Backup + checksum (before any edit) and rollback

### 9.1 Backup

```
cd /home/nedaktov/parlament-deschis
BK=/tmp/opencode/R03-scope-$(git rev-parse --short HEAD)-$(date +%Y%m%dT%H%M%S)
mkdir -p "$BK"
printf '%s\n' "$BK" > /tmp/opencode/R03-BACKUP-PATH
git ls-files -z frontend/src backend tests docs/API.md \
  | xargs -0 -I{} install -D -m 0644 "{}" "$BK/{}"
( cd "$BK" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum ) > "$BK/SHA256SUMS"
sha256sum "$BK/SHA256SUMS"; echo "BACKUP=$BK"
```
Expected: `BACKUP=/tmp/opencode/R03-scope-…` and a non-empty `SHA256SUMS`. Exit **0**.

### 9.2 Rollback (any time; restores exactly the §3 subset)

```
cd /home/nedaktov/parlament-deschis
BK=$(cat /tmp/opencode/R03-BACKUP-PATH)
# 1) remove files created by this recipe
rm -f frontend/src/hooks/useScope.ts frontend/src/components/ScopeControls.tsx \
      tests/test_scope_backend.py
# 2) restore tracked files from backup
( cd "$BK" && find . -type f ! -name SHA256SUMS -print0 \
    | xargs -0 -I{} cp --parents "{}" /home/nedaktov/parlament-deschis/ )
# 3) verify byte-for-byte
( cd /home/nedaktov/parlament-deschis && sha256sum -c "$BK/SHA256SUMS" ) | tail -3
git status --porcelain -- frontend/src backend tests docs/API.md   # expect empty
```
Expected: `sha256sum -c` prints `OK` for every file (last 3 shown), no `FAILED`; final `git status`
empty for the §3 subset. Exit **0**. Alternative if the tree is otherwise clean:
`git checkout -- frontend/src backend tests docs/API.md` (backup remains the source of truth for
newly added files). Never use `git reset --hard` — it would destroy unrelated work such as `.nedcode/`.

---

## 10. Acceptance criteria

1. **AC-1 (single source):** `grep -R "useSearch\|location.href" -n frontend/src/pages` shows no scope
   reads; every page uses `useScope()`. `useScope.ts` is the only file using `strict:false`.
2. **AC-2 (keys):** every scope-dependent `useQuery` key contains `...scopeKey`; the only unscoped key
   left is `["transparency-report"]` (documented in §6 row 5).
3. **AC-3 (params):** every API call sends only params its endpoint actually supports (§2.4 table). No
   `as_of` sent to coverage/report/cohesion/scorecard/ideology; no ignored param sent anywhere.
4. **AC-4 (controls):** every rendered scope control maps to an applied backend param or a documented
   client-side filter + note. Report/CoverageView/SenateHistory/Ideology/Grafice/Topuri have **no** date
   control that implies a filter.
5. **AC-5 (URL):** CP-8 passes; all **U** filters are in the URL; back/forward and deep links work.
6. **AC-6 (backend):** CP-3 and CP-5 pass; `/api/persons/{id}?as_of=` and `/api/mps?as_of=&chamber=&legislature=`
   echo their scope, filter data, return 422 on invalid dates, and are byte-identical to baseline when
   omitted. `/api/export/report` OpenAPI still exposes zero scope params.
7. **AC-7 (gates):** CP-1…CP-9 all green with pasted evidence and exit codes.
8. **AC-8 (honesty):** every relabelled view from §6 rows 4/5/7/8 renders a visible `role="note"` with an
   i18n key present in **both** ro and en.
9. **AC-9 (hygiene):** no edits outside §3; `git diff --stat` matches the file list; backup checksum
   verified at hand-off.

---

## 11. Dependencies

- **Requires:** approved plan + this recipe; baseline `eb693b4` (or identical docs-only descendant); §4
  preconditions; API dev server and Vite dev server; axe file + Playwright/Chromium.
- **Consumes:** `utils/date.ts` (§2.2), `api.meta` for legislature options, `QueryClient` key contract
  (router.tsx:566-575), backend `_parse_date`/`_parse_vote_bound` and cache semantics.
- **Unblocks:** R-0X count/denominator labelling (needs `scopeKey` and `total` from `/mps`), the transparency
  copy fix for Report (needs the "whole corpus" note), and the README claim "any moment 1990–today"
  (only Claimable after AC-3/AC-5 for the pages that genuinely support as_of).
- **Coordinates with:** another agent editing i18n keys — take the `scope.*` namespace only; a QA agent
  running CP-7 (needs exclusive use of the dev servers).

---

## 12. Side-quest policy

Time-box any surprise discovery to **30 minutes**, then log it here and continue with the checklist:

```
SIDE-QUEST LOG (implementation fills in)
SQ-1: …
```

Do **not** fix during R-03: FN-1's remaining pages outside §3; FN-2 (switch definitions); FN-3/FN-9
(labels/denominators/caps); FN-4/FN-5 (null→0, state gating); FN-6 (provenance); FN-8 (vote corpus scope,
`positions_incomplete`, pagination); X1/X4/X5/X6/X7/X8; AP-1…AP-8; TA-1…TA-8. Do not add `npm test`/vitest,
do not add new dependencies, do not touch `/export/report` or `/coverage*`, do not "quick-fix" a backend
query beyond §5.5. If a gate fails for a pre-existing reason, record the failing assertion verbatim and
mark that gate **NOT PROVEN** rather than weakening it.

---

## 13. NOT PROVEN (at recipe time)

Everything below is **static-code inference**; no code in this recipe has been executed:

- No browser render, click, back/forward, deep link, focus, 320 px reflow, or visual check was performed
  (TRIAD:87-89; FRONTEND:109-114). CP-7/CP-8 are *proposed* proofs, not results.
- No axe/WCAG-AA measurement was run; `/tmp/axe.min.js` was **absent** in the planning environment. The
  UI gate is therefore **NOT PROVEN** until §4 prerequisites and CP-7 succeed.
- No live API payload was fetched. The endpoint parameter matrix (§2.4) is read from source signatures only;
  actual database behaviour of the new `as_of` filters against the pinned corpus is **NOT PROVEN** until
  CP-3/CP-6 run.
- Production parity is **NOT PROVEN** (the vault QA note records a live proxy 404 on `/ideology` and a
  local-vs-live bundle hash mismatch — `QA-AND-AXE.md:36-46`). All gates here are local-only.
- The exact `N passed` for pytest/lint warning counts is unknown; §8 requires capturing it, not guessing it.
- Whether moving page-local filters (`selectedVoteId`, MpComparison's selection arrays) into the URL is
  desirable UX is a product call; where omitted it is logged as a side-quest, not silently skipped.
- No claim is made that the `paths` in §5.5.b produce identical query plans or latency; the existing 300 s
  cache (`backend/cache.py:28`) and 1 h React Query staleTime (router.tsx:569) still bound freshness.
- The two backend extensions are additive and default-identical **by design**, but "default-identical" is a
  contract to be *verified* by CP-3/CP-5, not an observed fact.
