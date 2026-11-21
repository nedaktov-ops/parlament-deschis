# R-08 — Feature-proxy honesty (coalitions, bureau, ideology, senate, reporting, vote analytics)

**Role:** STRATEGY/RECIPE agent R-08 — senior frontend + API engineer, honesty/claims reviewer.
**Status:** recipe only. **No product file is edited by this task.** The only file written is this document.
**Baseline:** `main` / `origin/main` `eb693b4d9faf558b22925fdb07ba6d118d7f6cef` (task brief: `eb693b4`).
Working branch observed: `docs/triad-audit` @ `80d91a90…`; verified `git diff --name-only 80d91a9 eb693b4 -- frontend/src pipeline backend docs` is **empty**, so every `path:line` below is valid at the baseline.
**Authority inputs:** vault `TRIAD-AUDIT-2026-11-21.md` (FN-8, FN-9, AP-7), vault `FRONTEND-AUDIT-2026-11-21.md` (X8 and per-page rows), `docs/DECISION-PARTY-GENEALOGY.md`, `docs/SENATE-PROFILE-IMPACT.md`, `docs/LOAD-TEST-EVIDENCE.md`.
**Rule inherited from the audits:** static-code evidence only. Browser renders, axe runs and live API payloads are **NOT PROVEN** until an implementer runs the gates in §8. No estimate, proxy, cap or editor label may be presented as an observed corpus fact.

---

## 0. Objective

Make every page named in the brief state **what its number actually measures**, and remove the presentation-layer claims that are false or self-contradictory:

1. `Coalitions` — stop selling a switch-wave proxy with a hardcoded trigger lookup as coalition facts; either relabel + disclose the trigger source and matching rule, or remove the trigger labelling.
2. `InstitutionalView` — make Bureau composition an explicit declared gap, or remove the card.
3. `Ideology` — remove the "not yet ingested" note that contradicts a populated chart, remove the PopuList source misclaim, and stop plotting null CHES scores as `0.00`.
4. `SenateHistory` — disclose the HOLD decision, fix the licence claim, and scope/correct the headline stats.
5. `Report` — remove the fabricated `60%` for `partial`, fix the EN footer, fix the "deputies" label on an all-persons count, and label group-only switch counts.
6. `CoverageView` — wire the already-existing `/api/coverage/dimensions` endpoint and stop deriving an "overall %" from rounded/null values.
7. `LegislatureDetail` — guard unknown years and scope the movements query to the legislature.
8. Vote pages (`Voturi`, `Radar`, `Grafice`, `Topuri`) — use the legislature/chamber where data actually exists, paginate from backend `total`, and surface `positions_incomplete`.

Each work item has a **decision gate** (A = recommended, B = documented alternative). An implementer must record the selected branch in the evidence log before editing. Default to A unless an owner decision says otherwise.

---

## 1. Evidence (path:line, all verified at `eb693b4`)

### 1.1 Audit inputs

| ID | Finding | Source |
| --- | --- | --- |
| FN-8 | Vote analytics scoped to empty data; hardcodes `2024/deputies`; limit 30/100 caps; `positions_incomplete=true` on all 52 local votes never surfaced; yes counts diverge 11008 vs 6258 | `TRIAD-AUDIT…md:70` |
| FN-9 | Mislabelled headline metrics; SenateHistory `%` is an integer count; LegislatureDetail unknown year renders 1990 data; movements endpoint has no legislature filter | `TRIAD-AUDIT…md:71` |
| FN-4 | Unknown/null coerced to displayed 0 or fabricated values (Report 60%, Ideology `0.00`, CoverageView null→0) | `TRIAD-AUDIT…md:66` |
| FN-6 | Provenance exists in API, absent from DOM; EN report footer falsely calls derived metrics "observed" | `TRIAD-AUDIT…md:68` |
| X8 | Vision features only proxies/placeholders: Bureau placeholder, Coalition Stability switch-wave proxy with hardcoded triggers ±90 d, Ideology PopuList misclaim | `FRONTEND-AUDIT…md:46`, `:106-107` |
| AP-7 | Canvas charts theme-blind/small-typed, hardcoded axis colours (`Ideology.tsx:22-42`) — adjacent, not owned here | `TRIAD-AUDIT…md:32` |
| SENATE-HOLD | **HOLD**: no exact `senat_guid` crosswalk (0 rows), no DOB in profiles, name-only auto-merge prohibited | `docs/SENATE-PROFILE-IMPACT.md:102-114` |
| GENEALOGY | **DROP** party genealogy; identity by exact ID only; never assert undeclared mergers/splits | `docs/DECISION-PARTY-GENEALOGY.md:3-22`, `:88-95` |
| LOAD | Load evidence is local-only; staging/production NOT PROVEN — do not use it to justify new runtime work | `docs/LOAD-TEST-EVIDENCE.md:14-17`, `:266-275` |

### 1.2 Code evidence

| Work item | Path:line | Observed fact |
| --- | --- | --- |
| W1 | `pipeline/analytics.py:24-73` | `TRIGGER_DATES` is a hardcoded editor lookup (elections/governments/congresses/breakups) with **no per-event source URL**. |
| W1 | `pipeline/analytics.py:76-87` | `_find_trigger` matches a date inside the wave window **or up to 90 days before** `wave_start`. |
| W1 | `pipeline/analytics.py:198-207` | That label is persisted into `SwitchWave.trigger_type` / `trigger_event`. |
| W1 | `api.py:829-859` | `GET /analytics/switch-waves` returns trigger fields with no provenance field. |
| W1 | `Coalitions.tsx:62-69`, `:252-262`, i18n `:292`, `:285`, `:288`, `:849`, `:842`, `:845` | Page titled "Coalition Stability" / "Stabilitatea coalițiilor"; intro says the corpus "links" events to named moments; methodology claims a link "when the corpus records that trigger" — false for a hardcoded dict. |
| W2 | `InstitutionalView.tsx:71-74` | Bureau card is a permanent `bureauDataUnavailable` text div, no data path. |
| W2 | i18n `:80-81`, `:643-644` | Copy says "not included in the current dataset" — honest, but presented as a content card, not a declared gap. |
| W3 | `Ideology.tsx:77-85`, `:118-122`, `:305-311` | `d.lrgen ?? 0`, `d.galtan ?? 0`, `d.eu_position ?? 0` → missing axes plotted/printed as `0.00`. |
| W3 | `Ideology.tsx:212`, `:232`, i18n `:448`, `:1020` | Intro claims "based on CHES and PopuList data". |
| W3 | `Ideology.tsx:205-223`, `:320-336` | Empty-state note "Ideological data not yet ingested. No figures or invented axes shown." rendered in the main branch **on top of a populated chart**; footer lists "Planned sources: CHES, Party Facts". |
| W3 | `api.py:1592` | Query filters `PartyIdeology.source == "ches"` only — no PopuList read path exists. |
| W3 | `pipeline/licenses.py:196-201` | PopuList licence **UNVERIFIED**, external cross-check only — cannot be claimed as a source. |
| W3 | `pipeline/licenses.py:124-131` | CHES is CC-BY-4.0 with attribution string. |
| W4 | `SenateHistory.tsx:68`, `:92` | "Senate Members" sums `coverage.data` (all chambers) = **5282**, while table filters `chamber==="senate"` (`:46`) = **1509**. |
| W4 | `SenateHistory.tsx:76-88`, i18n `:550`, `:1113` | "Full Coverage %" value is an integer count of rows (`rows.filter(...).length`), accent `rose`. |
| W4 | `SenateHistory.tsx:112-115`, i18n `:533`, `:1096` | "Current legislature (2024): Only sitemap data available (134 GUIDs)" — discovery CONTEXT, not archived data (`senator_profile` fragments = 0, `SENATE-PROFILE-IMPACT.md:4-9`). |
| W4 | `SenateHistory.tsx:202-207`, i18n `:541`, `:1104` | Claims `CC-BY 4.0`; licence register says `senat_facts` = **OGL-ROU-1.0** (`pipeline/licenses.py:71-76`). |
| W5 | `Report.tsx:94-102` | `completenessValue`: `full→100`, `partial→60`, else `0` — pure fabrication. |
| W5 | `Report.tsx:128-133`, i18n `:523`, `:1086` | `d.totals.persons` (all persons, both chambers) labelled "deputies in the corpus". |
| W5 | `Report.tsx:255-259`, i18n `:524`, `:1087` | "Party switches" = `totals.switches` = `Event.type == "switch_group"` only (`exports.py:72-73`). |
| W5 | `Report.tsx:466-468`, i18n `:1078` | EN footer: "Every figure above is an observed count" — contradicts derived loyalty score and mean/median age (RO footer at `:515` is already honest). |
| W6 | `CoverageView.tsx:33-66`, `:100-136` | `datedMemberships` uses `r.dated_pct ?? 0`; `overallPct` derived from rounded percentages — new number with no backend field. |
| W6 | `api.py:430-441`, `pipeline/coverage.py:192-259` | `/api/coverage/dimensions` already returns per-scope `mandates` / `votes` / `biographies` status+count+note. |
| W6 | `client.ts:445-446` | Client exposes `coverage` and `coverage_detailed` only — **no `coverageDimensions` method**. |
| W6 | i18n `:175-193`, `:734-751` | Missing keys: `coverageStatChambers`, `coverageStatLegislatures`, `coverageStatFullCoverage`, `coverageStatPartialCoverage`, `coverageOverallLabel`, `coverageStatEntries` → English defaults leak to RO. |
| W7 | `LegislatureDetail.tsx:21-37` | Unknown `params.year` → `leg` undefined → `start="1990-01-01"`, `end=today`; queries still run and render 1990 data under the unknown year. |
| W7 | `LegislatureDetail.tsx:34-37`, `:80-84` | Movements query has no `legislature`/`chamber` filter; headline "Switches" counts a 1000-row page. |
| W7 | `api.py:395-406`, `queries.py:526-544` | `/api/movements` accepts `chamber`, not `legislature`; `Event.legislature` exists (used at `queries.py:559`). |
| W8 | `Voturi.tsx:16-24`, `:64-72` | Query has no chamber/legislature, `limit:100` cap; copy claims "Chamber of Deputies and the Senate". |
| W8 | `Voturi.tsx:89-91`, `:102-201` | `filtered.length / votes.length` uses the capped page, not `total`. |
| W8 | `api.py:1155-1183`, `client.ts:284-291` | Backend already returns `total`/`offset`/`limit` and per-row `positions_incomplete` (`:1172`). |
| W9 | `Radar.tsx:25-39` | `api.votes({limit:30})`, positions `limit:500`. |
| W9 | `Radar.tsx:98-105` | **Any** failed positions query blanks the whole matrix with "Failed to load votes." — error conflated with empty. |
| W10 | `Grafice.tsx:11-19`, `:168-170` | Hardcodes `traseismSummary("2024","deputies")`, `voteCohesion("deputies","2024")`, `<VoteActivityChart legislature="2024">`. |
| W10 | `Grafice.tsx:25-41`, `:57-62`, `:131-163` | One cohesion error/empty hides the independent switch-statistics block. |
| W10 | `Topuri.tsx:20-24`, `:79-81` | `api.scorecard(undefined, undefined, 100, 0, minVotes)` — no scope, hard cap ignoring `total`. |
| W10 | `api.py:1494-1499`, `:1521-1523` | Rebellion increments for **any** non-majority choice, including `abstain` and `not_voting`. |

### 1.3 Measured corpus facts (read-only, for expected checkpoint outputs)

Commands were run against a **read-only SQLite URI**; no DB was written.

```
data/parlament.db        votes: ('deputies','2020') 52, all positions_incomplete=1
                         vote-level yes/no/abstain/not_voting: 11008 / 439 / 516 / 105
                         position-level yes/no/abstain/not_voting: 6258 / 391 / 426 / 52
                         senate scopes 10 / senate persons 1509 / all persons 5282 / full scopes 14
                         CHES rows 44
data/parlament-real.db   votes: ('',None) 12 (8 incomplete), ('deputies','2020') 120,
                         ('deputies','2024') 45 ; all but 4 of 177 incomplete
                         vote-level yes 38186 ; position-level yes 24585
                         senate scopes 10 / senate persons 1509 / all persons 5282 / full scopes 14
                         CHES rows 38
```

**Honest consequence:** the audit's "corpus is entirely 2020" statement is true for `data/parlament.db` (the dev/fixture corpus) but **not** for the default `data/parlament-real.db`, which also has 2024 votes. The fix must therefore **derive scope from data**, never hardcode `2020` either.

---

## 2. Exclusive file list

**The implementer may write only these paths.** Everything else is a side-quest (§11).

### Frontend
- `frontend/src/pages/Coalitions.tsx`
- `frontend/src/pages/InstitutionalView.tsx`
- `frontend/src/pages/Ideology.tsx`
- `frontend/src/pages/SenateHistory.tsx`
- `frontend/src/pages/Report.tsx`
- `frontend/src/pages/CoverageView.tsx`
- `frontend/src/pages/LegislatureDetail.tsx`
- `frontend/src/pages/Voturi.tsx`
- `frontend/src/pages/Radar.tsx`
- `frontend/src/pages/Grafice.tsx`
- `frontend/src/pages/Topuri.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/i18n.ts`

### Backend (only the additive changes named in W1, W7, W8, W10)
- `backend/routers/api.py`
- `backend/queries.py`

### Tests (new files allowed; existing files only if adding tests, never weakening one)
- `tests/test_r08_feature_honesty.py` (new — preferred single home for all new regression tests)
- `tests/test_api.py`, `tests/test_export_report.py`, `tests/test_vote_ideology_convergence.py`, `tests/test_analytics_transparency.py` (additive-only)

### Documentation (this recipe is already written; implementer may update)
- `docs/API.md` (only for the additive response fields in W1/W7/W8)

**Do NOT touch:** `backend/routers/exports.py`, `pipeline/analytics.py` (W1 gate B is the only exception, and only the deletion of the trigger lookup call), `pipeline/coverage.py`, `pipeline/licenses.py`, `frontend/src/components/*`, `frontend/src/router.tsx`, `frontend/src/index.css`, any DB/data file, any baseline JSON, `vercel.json`, any audit/vault document, `docs/DECISION-PARTY-GENEALOGY.md`, `docs/SENATE-PROFILE-IMPACT.md`, `docs/LOAD-TEST-EVIDENCE.md`.
**Never** add a genealogy ingestion path, a `PopuList` claim, or a licence entry that contradicts `pipeline/licenses.py`.

---

## 3. Preconditions

1. Repo at baseline: `git -C /home/nedaktov/parlament-deschis rev-parse HEAD` → `eb693b4d9faf558b22925fdb07ba6d118d7f6cef…` (or a clean worktree based on it).
2. `git status --short` has no unexpected modifications to the exclusive file list. Untracked `.nedcode/` and vault backlink files are pre-existing and unrelated — leave them alone.
3. `.venv/bin/python -m pytest --collect-only -q` → `408 tests collected` (record actual value; a different count means the baseline moved — stop).
4. `cd frontend && npm run lint` and `npm run build` both exit 0 **before** edits (green baseline). If red, report `NOT PROVEN` and stop; do not mix pre-existing failures with this work.
5. Read `docs/SENATE-PROFILE-IMPACT.md:102-114` and `docs/DECISION-PARTY-GENEALOGY.md:3-22` in full. The HOLD and DROP decisions are **inputs**, not work items.
6. No network calls, no deploy, no secrets, no production DB writes. All DB probes use `file:…?mode=ro`.

---

## 4. Backup + checksum (mandatory, before any edit)

```bash
cd /home/nedaktov/parlament-deschis
R08_BASE=$(git rev-parse eb693b4)
test "$R08_BASE" = "$(git rev-parse HEAD)" || { echo "STOP: HEAD != baseline"; exit 2; }

BACKUP_DIR=/tmp/opencode/R-08-backup-$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$BACKUP_DIR"

git diff --binary "$R08_BASE" -- \
  frontend/src/pages frontend/src/api/client.ts frontend/src/i18n.ts \
  backend/routers/api.py backend/queries.py tests docs/API.md \
  > "$BACKUP_DIR/r08-baseline.patch"

sha256sum \
  frontend/src/pages/{Coalitions,InstitutionalView,Ideology,SenateHistory,Report,CoverageView,LegislatureDetail,Voturi,Radar,Grafice,Topuri}.tsx \
  frontend/src/api/client.ts frontend/src/i18n.ts \
  backend/routers/api.py backend/queries.py \
  | tee "$BACKUP_DIR/SHA256SUMS"

printf '%s\n' "$R08_BASE" > "$BACKUP_DIR/BASELINE_SHA"
sha256sum "$BACKUP_DIR/r08-baseline.patch" >> "$BACKUP_DIR/SHA256SUMS"
echo "BACKUP_DIR=$BACKUP_DIR"
```

Expected: the patch is empty (baseline == HEAD); `SHA256SUMS` has 15 file lines + 1 patch line; exit 0. **Record `BACKUP_DIR` in the evidence log** — rollback (§13) depends on it.

---

## 5. Decision-gate protocol

For each W-item the implementer writes one line to the evidence log **before** editing:

```
W<n> GATE=<A|B> RATIONALE=<one sentence> OWNER=<name/date>
```

- **A** is the recommended branch in every item — it keeps the feature but makes the copy true.
- **B** is the documented removal/label-only branch where keeping the data would require inference or new unsourced data.
- Mixing branches without recording both lines is a REJECT.
- If a gate's precondition cannot be proven offline, choose B and mark the A branch `NOT PROVEN`.

---

## 6. Work items

### W1 — Coalition Stability → switch-wave proxy with trigger disclosure

**Gate A (recommended):** keep waves and events, relabel the page, disclose that named triggers come from a **hardcoded editor lookup** matched by ±90-day proximity, and add a provenance field to the API response.
**Gate B:** remove trigger labelling: stop calling `_find_trigger` in `pipeline/analytics.py:199`, set `trigger_type`/`trigger_event` to `None`, drop all three event sections from `Coalitions.tsx`; page becomes "Switch-wave timeline" with wave counts only. B is required if the owner refuses editor-curated labels.

**Honest copy (A), both locales:**
- EN title: `Switch-wave timeline (proxy)`. RO: `Cronologia valurilor de schimbare (proxy)`.
- EN intro: `Detected bursts of group-switch events. Named political moments are editor-curated labels — not coalition facts asserted by the corpus — matched to a wave inside its window or up to 90 days before it.`
- EN methodology: `A wave is a 30-day cluster of 3+ switch_group events. Trigger labels come from the editor-maintained TRIGGER_DATES lookup in pipeline/analytics.py; there is no per-event source URL in the dataset. "Since prior formation" is the interval between two labelled waves, not an official government duration.`
- EN disclosure panel: `Trigger disclosure — each label below is an editor-curated name from a hardcoded lookup (pipeline/analytics.py:24-73), matched within the wave window or 90 days before it. No source URL is attached to the trigger; do not read these as coalition records.`

**Steps (A):**
1. `Coalitions.tsx:62-69` — change title/intro `t()` defaults and add `t("coalitions.triggerDisclosure", "<copy above>")`.
2. `Coalitions.tsx:252-262` — replace the methodology `t()` default with the honest paragraph above; delete the clause "when the corpus records that trigger".
3. `Coalitions.tsx:40-53` — keep `spans`, but add a comment `// Editor labels only; "days" is a wave-to-wave interval, not a government lifetime.` and change the column header at `:163` to `t("coalitions.col.since", "Interval from prior labelled wave")`.
4. Add a disclosure `<section className="…" data-enter>` immediately before the methodology block, rendering `t("coalitions.triggerDisclosure")` plus counts of `formations/breakups/congresses`.
5. `api.py:848-859` — add one field to each wave dict (additive; keep every existing field):
   ```python
   "trigger_provenance": (
       "editor-curated lookup (pipeline/analytics.py:TRIGGER_DATES); "
       "matched within wave window or 90 days before; no per-event source URL"
       if w.trigger_event else None
   ),
   ```
6. `i18n.ts` — update `coalitions.title`, `coalitions.intro`, `coalitions.methodology.desc`, `coalitions.col.since` and add `coalitions.triggerDisclosure` in **both** `ro` and `en` objects (keys currently at `:276-292` and `:833-849`). Romanian copy must use diacritics; no English fallback.
7. `tests/test_r08_feature_honesty.py` — add a test asserting: (a) `/api/analytics/switch-waves` rows with a trigger carry non-null `trigger_provenance`; (b) rows without a trigger carry `None`; (c) no existing field removed.

**Checkpoint W1:** `git grep -n 'Coalition Stability\|Stabilitatea coalițiilor\|corpus records that trigger' -- frontend/src/pages/Coalitions.tsx frontend/src/i18n.ts` → **no output, exit 1 from grep** (wrap as `test -z "$(git grep …)"`). Plus `grep -c 'trigger_provenance' backend/routers/api.py` → `1`.

**Rollback W1:** `git checkout eb693b4 -- frontend/src/pages/Coalitions.tsx backend/routers/api.py frontend/src/i18n.ts` then drop the W1 test lines.

---

### W2 — Bureau composition → explicit gap or removal

**Gate A (recommended):** keep the card but convert it from a data-looking placeholder into a labelled **declared gap** with no number, no progress bar and no hover affordance.
**Gate B:** delete the whole `<div className="card p-4">` block at `InstitutionalView.tsx:71-74` and remove the two i18n keys in both locales.

**Honest copy (A):**
- EN heading: `Bureau composition — not in scope`. Body: `Declared data gap. This corpus has no bureau-membership rows; no composition, count or chart is shown and none is inferred. See FRONTEND-AUDIT-2026-11-21 X8.`
- RO heading: `Compoziția birourilor — nu este în sferă`. Body: `Lacună declarată. Corpusul nu conține înregistrări de membri ai birourilor; nu afișăm nicio compoziție, număr sau grafic și nu le inferăm.`

**Steps (A):**
1. `InstitutionalView.tsx:71-74` — replace the div with:
   ```tsx
   <div className="card p-4">
     <h2 className="font-semibold mb-3">{t("bureauComposition")}</h2>
     <p className="text-sm text-slate-400" role="note">{t("bureauGap")}</p>
   </div>
   ```
2. `i18n.ts:80-81` and `:643-644` — keep `bureauComposition`, replace `bureauDataUnavailable` with `bureauGap` (both locales); delete the old key rather than leaving dead copy.
3. No backend change: the corpus genuinely has no bureau rows, and inventing them is forbidden by `docs/DECISION-PARTY-GENEALOGY.md:8-11`.

**Checkpoint W2:** `test -z "$(git grep -n 'bureauDataUnavailable' -- frontend/src)"` → exit 0; `grep -n 'bureauGap' frontend/src/i18n.ts` → exactly 2 lines (ro+en), exit 0.

**Rollback W2:** `git checkout eb693b4 -- frontend/src/pages/InstitutionalView.tsx frontend/src/i18n.ts`.

---

### W3 — Ideology: contradictory note, PopuList misclaim, null→0 points

**Gate A (recommended):** keep the CHES chart; plot only complete points and disclose omissions; remove PopuList from all copy; condition the "not yet ingested" note on `dataExists === false`.
**Gate B:** if any CHES axis is missing in >50% of rows for a year, hide the scatter for that year and render the table with `—` placeholders only. Gate B is a copy-only fallback; it **must not** say data is absent when CHES rows exist (44 in `parlament.db`, 38 in `parlament-real.db`).

**Honest copy:**
- EN intro: `Party positions from CHES expert-survey scores (0–10 axes: left-right, GAL-TAN, EU). PopuList is NOT ingested in this corpus and is not used here.`
- EN provenance footer (replaces `view.ideology.note`/`sources` on the populated branch): `Source: CHES, EUI archive (hdl.handle.net/1814/69975), CC BY 4.0. Parties are matched by Party Facts ID; PopuList is excluded (licence UNVERIFIED).`
- EN empty copy: `No CHES wave is available for the selected year.` (only when `dataExists` is true but the filtered list is empty). `Ideological data not yet available.` is used **only** when `dataExists === false`.
- EN omission line: `{{n}} party-wave(s) omitted from the plot: at least one CHES axis is missing. Missing values are shown as — in the table, never as 0.`

**Steps (A):**
1. `Ideology.tsx:76-85` — replace axis construction with a completeness filter; do **not** use `?? 0`:
   ```tsx
   const AXIS_KEYS = ["lrgen", "galtan", "eu_position"] as const;
   const hasAxes = (d: IdeologyEntry) =>
     AXIS_KEYS.every((k) => typeof d[k] === "number" && Number.isFinite(d[k] as number));
   const plottedData = filteredData.filter(hasAxes);
   const omittedCount = filteredData.length - plottedData.length;

   const scatterData = plottedData.map((d: IdeologyEntry) => ({
     value: [d.lrgen, d.galtan, d.eu_position],
     name: d.party_name,
     survey_year: d.survey_year,
     // ...unchanged auxiliary fields
   }));
   ```
   (Keep the auxiliary fields at `:80-85`; only the three axis values change.)
2. `Ideology.tsx:112-124` — tooltip: use `d.value[0].toFixed(2)` etc. directly (values are now guaranteed finite); drop `?? 0`.
3. `Ideology.tsx:293-313` — table cells: render `d.lrgen == null ? "—" : d.lrgen.toFixed(2)` (same for `galtan`, `eu_position`).
4. `Ideology.tsx:205-223` — split the branch:
   - `if (!dataExists) { … empty.ideology … }` — this is the only place the "not yet ingested" copy may appear.
   - `if (filteredData.length === 0) { … view.ideology.noYear … }`.
5. `Ideology.tsx:212` and `:232` — remove `and PopuList data` / `și PopuList`; keep CHES only.
6. `Ideology.tsx:320-336` — replace the bottom note block with the provenance copy and the omission line (`{t("view.ideology.omitted", { n: omittedCount })}`). Remove the literal strings "Planned sources:" / "Ideological data not yet ingested" from this branch.
7. `i18n.ts:447-449`, `:1019-1024` — update `view.ideology.intro`, `view.ideology.note` (rename to `view.ideology.provenance`), add `view.ideology.omitted` and `view.ideology.noYear`; ro+en. Remove any copy claiming PopuList as a source. The `Licence-gated: CC BY 4.0 (CHES), CC0 (Party Facts)` line may stay **only** if reworded as `CHES: CC BY 4.0` — Party Facts supplies IDs here, not licensed scores.
8. `tests/test_r08_feature_honesty.py` — add a source-scan test: `Ideology.tsx` must not contain `PopuList data` or `?? 0` on `lrgen|galtan|eu_position`; `api.py` ideology handler must still filter `source == "ches"`.

**Optional within W3, own gate W3b:** `Ideology.tsx:47`, `:67`, `:242-255` — "All years" is a no-op because `selectedYear` falls back to the latest year (`TRIAD FN-7`). Gate W3b-A: use a sentinel `year: string | "all" | undefined` where `"all"` disables the `selectedYear` fallback; W3b-B: remove the `<option value="">All years</option>` and relabel the default `Latest available year`. Record the gate separately.

**Checkpoint W3:** `test -z "$(git grep -n 'PopuList data\|d.lrgen ?? 0\|d.galtan ?? 0\|d.eu_position ?? 0' -- frontend/src/pages/Ideology.tsx frontend/src/i18n.ts)"` → exit 0. `.venv/bin/python -m pytest tests/test_vote_ideology_convergence.py -q` → exit 0.

**Rollback W3:** `git checkout eb693b4 -- frontend/src/pages/Ideology.tsx frontend/src/i18n.ts`.

---

### W4 — SenateHistory: HOLD disclosure, licence fix, honest stats

**Gate A (recommended):** keep the page; add HOLD notice, correct stats to senate-only, relabel the "%" stat as a scope count, fix licence; keep the per-scope note column.
**Gate B:** replace the whole page body with a single HOLD notice (still under the existing route) — used only if an owner decides the page must not render figures at all.

**Honest copy (A):**
- EN HOLD: `HOLD (2026-11-21) — historical Senate profiles are NOT ingested. There is no exact senat_guid crosswalk (0 rows) and profiles carry no date of birth, so ingest would require name-only auto-matching, which the project prohibits. Decision: docs/SENATE-PROFILE-IMPACT.md §4.`
- EN licence: `Source: senat.ro public data — Open Government Licence (Romania), OGL-ROU-1.0, per the project licence register (pipeline/licenses.py). The derived corpus is CC-BY 4.0.`
- EN gap line: `Current legislature (2024): GUID discovery only. No senator profiles are archived in this dataset (0 senator_profile fragments); the GUID count from discovery notes is not a corpus count.` (RO mirror required.)
- EN stat labels: `Senate members (this corpus)`, `Full-coverage scopes (of 10)`.

**Steps (A):**
1. `SenateHistory.tsx:46` — keep `allRows = rows.filter(r => r.chamber === "senate")`.
2. `SenateHistory.tsx:65-89` — replace every `coverage.data?.reduce(...)` and `rows` used for headline stats with `allRows`:
   ```tsx
   value={allRows.reduce((acc, r) => acc + r.persons, 0)}   // 1509 in both corpora
   ...
   value={allRows.length}                                    // legislatures = 10
   ...
   label={t("senateStatCoverage", "Full-coverage scopes (of {{n}})", { n: allRows.length })}
   value={allRows.filter((r) => r.completeness === "full").length}
   accent="emerald"
   ```
   (Check `InfoStat` accepts a `label: string`; it does at all other call sites. If interpolation in `label` is not supported by `InfoStat`, precompute the string with `t()` before the JSX.)
3. `SenateHistory.tsx:90-97` — moment figure must also use `allRows`.
4. `SenateHistory.tsx:100-124` — add the HOLD notice as the first `<li>` in Known Gaps and replace the 134-GUID claim with the honest gap line above.
5. `SenateHistory.tsx:202-207` — replace the licence `t()` default with the OGL text; do not claim CC-BY 4.0 for senat.ro itself.
6. `i18n.ts:533-541`, `:548-551`, `:1094-1114` — update ro+en: `senate.history.hold` (new), `senate.history.gap.current`, `senateStatMembers`, `senateStatCoverage`, `senate.history.methodology.source`. `senateStatLegislatures` must be added in both locales (currently a raw key — FRONTEND-AUDIT X4).
7. `tests/test_r08_feature_honesty.py` — add a static test: `SenateHistory.tsx` must not contain `coverage.data?.reduce` or `CC-BY 4.0` in the licence line, and must contain the HOLD key.

**Checkpoint W4:**
```bash
test -z "$(git grep -n 'CC-BY 4.0' -- frontend/src/pages/SenateHistory.tsx)"   # exit 0
test -z "$(git grep -n 'coverage.data?.reduce' -- frontend/src/pages/SenateHistory.tsx)" # exit 0
```
Read-only corpus corroboration (no UI claim): the python probe in §1.3 must print `senate persons 1509` and `all persons 5282`.

**Rollback W4:** `git checkout eb693b4 -- frontend/src/pages/SenateHistory.tsx frontend/src/i18n.ts`.

---

### W5 — Report: fabricated 60%, EN footer, deputy label, group-switch label

**Gate A (recommended):** keep the ring for `full` scopes only; show status text for every other scope; correct all copy.
**Gate B:** remove `ProgressRing` and `Sparkline` from the coverage table entirely and render only a text badge `full | partial | none — no percentage published`. B is required if the team wants zero numeric affordance on non-quantified states.

**Honest copy:**
- EN footer: `Source: parlament-deschis corpus — cdep.ro and senat.ro dated parliamentary ledgers. Counts are observed; the loyalty score and mean/median age are derived. Gaps are stated, never filled with estimates. CC-BY 4.0.` (mirrors the already-honest RO string at `i18n.ts:515`).
- EN hero label: `people in the corpus` (RO `persoane în corpus`) — `totals.persons` includes both chambers.
- EN stat label: `Group switches (switch_group events)` (RO `Schimbări de grup (evenimente switch_group)`).
- EN coverage cell note: `Partial — no completeness percentage is published.`

**Steps (A):**
1. `Report.tsx:94-102` — **delete** `completenessValue` and `completenessRingColor`; add
   ```tsx
   const completenessText = (c: string): string =>
     c === "full" ? "full" : c === "partial" ? "partial — no % published" : "none — no % published";
   ```
   (`completenessColor` at `:87-92` may stay for the text colour.)
2. `Report.tsx:441-459` — render the ring only for `full`, and always render the honest status:
   ```tsx
   <span className={`font-medium text-xs text-nowrap ${completenessColor(c.completeness)}`}>
     {completenessText(c.completeness)}
   </span>
   {c.completeness === "full" && (
     <ProgressRing value={100} max={100} size={22} color="stroke-emerald-400" />
   )}
   ```
   Because `tsconfig` has `noUnusedLocals`, deleting the two helpers is mandatory, not cosmetic.
3. `Report.tsx:128-133` — change `t("report.deputiesCount", …)` to `t("report.peopleCount", "people in the corpus")`.
4. `Report.tsx:255-259` — change `t("report.switches", "Party switches")` to `t("report.groupSwitches", "Group switches (switch_group events)")`.
5. `Report.tsx:466-468` — no code change needed; the footer text lives in i18n.
6. `i18n.ts:515`, `:523-524`, `:1078`, `:1086-1087` — update EN footer; replace `report.deputiesCount` with `report.peopleCount` in ro+en; add `report.groupSwitches` and `report.coverageNoPct` in ro+en. Do not leave a string stating every figure is observed.
7. `tests/test_r08_feature_honesty.py` (or additively in `tests/test_export_report.py`) — assert the EN footer key text contains `derived` and does not contain `Every figure above is an observed count`.

**Checkpoint W5:** `test -z "$(git grep -n 'c === \"partial\" ? 60\|Every figure above is an observed count\|deputies in the corpus' -- frontend/src/pages/Report.tsx frontend/src/i18n.ts)"` → exit 0. `.venv/bin/python -m pytest tests/test_export_report.py tests/test_api_exports.py -q` → exit 0.

**Rollback W5:** `git checkout eb693b4 -- frontend/src/pages/Report.tsx frontend/src/i18n.ts`.

---

### W6 — CoverageView: wire `/api/coverage/dimensions`

**Gate A (recommended):** render the dimensions endpoint as the primary view; keep the existing detailed mandate table below it under an explicit `Mandate detail` heading. Remove the derived `overallPct`.
**Gate B:** replace the page with the dimensions table only (delete `coverage_detailed` usage from this page; keep the API endpoint).

**Honest copy:** EN `Dimensions are reported separately. A scope with full mandates is not claimed to have full votes or biographies. Counts and notes come from /api/coverage/dimensions; no overall percentage is averaged or inferred.` (RO mirror.) Column labels: `Mandates`, `Votes`, `Biographies`; each cell shows `status — count` plus the backend `note`.

**Steps (A):**
1. `client.ts` next to `:445-446` — add:
   ```ts
   export interface CoverageDimension { status: string; count: number; total?: number; note: string | null }
   export interface CoverageDimensionRow {
     chamber: string; legislature: string | null;
     period_start: string | null; period_end: string | null;
     mandates: CoverageDimension; votes: CoverageDimension; biographies: CoverageDimension;
   }
   // inside `api`:
   coverageDimensions: () => get<CoverageDimensionRow[]>("/coverage/dimensions"),
   ```
2. `CoverageView.tsx:28-33` — add a second query:
   ```tsx
   const dimensions = useQuery({
     queryKey: ["coverage-dimensions"],
     queryFn: api.coverageDimensions,
   });
   ```
3. `CoverageView.tsx:33-66` — delete `overallPct`, `fullPct`, `partialPct` and the `datedMemberships` / `sourcedSwitches` rounding maths. Headline cards become **data-derived counts only**: `scopes = dimensions.data?.length`, chambers `new Set(...)`, legislatures `new Set(...)`, and a count of scopes whose `votes.status !== "none"`. Never invent a percentage.
4. `CoverageView.tsx:125-136` — remove the `ProgressRing value={overallPct}` block; replace with the honest copy paragraph above. Note: `ProgressRing` import at `:7` becomes unused → remove it or the build fails under `noUnusedLocals`.
5. `CoverageView.tsx:155-253` — insert the dimensions table **before** the existing detailed table; wrap the old table in `<h2>{t("coverageMandateDetail")}</h2>`. Each dimension cell:
   ```tsx
   <td>
     <span className={`rounded px-2 py-0.5 ${completenessClass(d.status)}`}>{t(d.status)}</span>
     <span className="ml-2 tabular-nums">
       {d.count}{d.total != null ? ` / ${d.total}` : ""}
     </span>
     <div className="text-slate-500 text-xs">{d.note ?? "—"}</div>
   </td>
   ```
6. Gate both queries: `isLoading` → one loading state; `isError` → error + single RetryButton calling both `refetch()`; never render zeros while loading.
7. `i18n.ts:175-193` and `:734-751` — add the six missing keys (`coverageStatChambers`, `coverageStatLegislatures`, `coverageStatFullCoverage`, `coverageStatPartialCoverage`, `coverageOverallLabel`, `coverageStatEntries` — replace `coverageOverallLabel` with `coverageDimensionsNote`), plus `coverageMandateDetail`, `coverageDimMandates`, `coverageDimVotes`, `coverageDimBiographies`, in **ro and en**.
8. `tests/test_r08_feature_honesty.py` — assert `CoverageView.tsx` calls `api.coverageDimensions()` and does not contain `overallPct`; existing `tests/test_api.py:1289,1371,1391,1408` already cover the endpoint — keep them green.

**Checkpoint W6:**
```bash
test -z "$(git grep -n 'overallPct\|datedMemberships' -- frontend/src/pages/CoverageView.tsx)"  # exit 0
grep -n 'coverageDimensions' frontend/src/pages/CoverageView.tsx frontend/src/api/client.ts  # >=2 lines, exit 0
```
API proof (existing test): `.venv/bin/python -m pytest tests/test_api.py -q -k coverage_dimensions` → exit 0.

**Rollback W6:** `git checkout eb693b4 -- frontend/src/pages/CoverageView.tsx frontend/src/api/client.ts frontend/src/i18n.ts`.

---

### W7 — LegislatureDetail: unknown-year guard + scoped movements

**Gate A (recommended):** add an optional `legislature` parameter to `/api/movements` and scope the page to `{chamber:"deputies", legislature:year}`; guard unknown years before any data query.
**Gate B:** no backend change; relabel the card `Recent switch events in the 1990→selected window (all legislatures, first 1000)` and drop the "Switches" headline stat. Use B if an API-shape change is not authorised in this wave.

**Honest copy:** EN unknown-year: `Unknown legislature "{{year}}". This corpus has no metadata for that year, so no figures are shown. Known years: {{years}}.` EN scoped label: `Group switches in this legislature (within scope, first 1000 events)`.

**Steps (A):**
1. `queries.py:526-544` — extend the signature and predicate:
   ```python
   def get_movements(session, person_id, chamber, start, end, limit=200,
                     legislature: str | None = None) -> list[dict]:
       stmt = select(Event).where(Event.type.in_(["switch_group", "switch_party"]))
       ...
       if legislature:
           stmt = stmt.where(Event.legislature == legislature)
   ```
2. `api.py:395-406` — add the query parameter and pass through:
   ```python
   legislature: str | None = Query(None, pattern=r"^\d{4}$"),
   ...
   return queries.get_movements(db, person_id, chamber, s, e, limit, legislature)
   ```
3. `client.ts` `movements(...)` at `:437-440` — accept and forward `legislature`.
4. `LegislatureDetail.tsx:20-37` — compute the guard **before** the queries:
   ```tsx
   const knownYears = Object.keys(meta.data?.legislatures ?? {});
   const leg = meta.data?.legislatures?.[year];
   const yearUnknown = meta.isSuccess && !leg;
   const scoped = !!leg && !yearUnknown;
   const movements = useQuery({
     queryKey: ["leg-movements", year, start, selectedDate],
     queryFn: () => api.movements({ from: start, to: selectedDate, limit: 1000,
                                    chamber: "deputies", legislature: year }),
     enabled: scoped,
   });
   ```
   Gate `chamber` (`api.chamber("deputies", selectedDate)`) with `enabled: scoped` too.
5. `LegislatureDetail.tsx:39-52` — after the `meta.isError` branch, add:
   ```tsx
   if (yearUnknown) return (
     <div className="wrap p-6" role="alert">
       <h1 className="text-xl font-semibold">{t("legislatureUnknown", { year })}</h1>
       <p className="text-sm text-slate-400">{t("legislatureKnownYears", { years: knownYears.join(", ") || "—" })}</p>
     </div>
   );
   ```
   No fallback `1990-01-01` render is allowed once meta has loaded.
6. `LegislatureDetail.tsx:80-84` — relabel the stat `legislatureStatSwitches` to `Group switches in this legislature (first 1000)`; keep the `=== 1000` cap warning at `:150-152`.
7. `i18n.ts` — add `legislatureUnknown`, `legislatureKnownYears`, update `legislatureStatSwitches` in ro+en.
8. `tests/test_r08_feature_honesty.py` — add a test using the existing API fixture: `/api/movements?legislature=1990&limit=1000` must return only events whose `legislature == "1990"`; unknown year page guard is a static source assertion.

**Checkpoint W7:**
```bash
grep -n 'legislature' backend/queries.py | grep -n 'Event.legislature'   # >=1 new line, exit 0
test -z "$(git grep -n 'queryFn: () => api.movements({ from: start' -- frontend/src/pages/LegislatureDetail.tsx)" # exit 0
```
`.venv/bin/python -m pytest tests/test_api.py -q -k movements` → exit 0.

**Rollback W7:** `git checkout eb693b4 -- frontend/src/pages/LegislatureDetail.tsx frontend/src/api/client.ts backend/routers/api.py backend/queries.py frontend/src/i18n.ts`.

---

### W8 — Voturi: real scope, pagination, positions disclosure

**Gate A (recommended):** add a data-derived `scopes` array to `/api/votes` and drive the page from it (default = largest data-bearing scope, currently 2020 deputies in `parlament.db`); paginate with `total`/`offset`/`limit`.
**Gate B:** no API change — hardcode the visible default `deputies/2020` with a scope selector built from a one-off `api.votes({limit:1})` probe, and label it `local corpus default`. Use B only if the additive API field is rejected.

**Honest copy:** EN intro: `Roll-call votes in the scope selected below. Every published row comes from the official cdep.ro feed and carries its source URL.` (drops the false "and the Senate" claim). EN scope note: `Scope: {{chamber}} / {{legislature}} — {{total}} votes in this corpus. Showing {{from}}–{{to}}.` EN position note: `{{n}} of {{m}} votes in this corpus have positions_incomplete=true: official yes/no/abstain totals can exceed the number of recorded individual positions. The flag is shown per row.`

**Steps (A):**
1. `api.py:1132` — change local import to `from sqlalchemy import func, select`. After `total = len(rows)` at `:1155`, add:
   ```python
   scopes = [
       {"chamber": r[0] or "unknown", "legislature": r[1], "total": r[2]}
       for r in db.execute(
           select(Vote.chamber, Vote.legislature, func.count(Vote.id))
           .group_by(Vote.chamber, Vote.legislature)
           .order_by(func.count(Vote.id).desc())
       ).all()
   ]
   ```
   and add `"scopes": scopes,` to the return at `:1176-1183`. Keep all existing fields.
2. `client.ts:268-291` — add `export interface VoteScope { chamber: string; legislature: string | null; total: number }` and `scopes: VoteScope[]` to `VotesResponse`.
3. `Voturi.tsx:11-24` — add `const [offset, setOffset] = useState(0); const [scope, setScope] = useState<string | null>(null);` and query with `chamber`, `legislature`, `limit: 100`, `offset`. Derive the default from `votesQuery.data?.scopes` once loaded (largest total; in `parlament.db` that is `deputies/2020`, 52 votes).
4. `Voturi.tsx:64-72` — replace intro/scopeNote defaults with the honest copy above; `${scope}` values interpolated from data, never hardcoded.
5. `Voturi.tsx:89-91` — replace `filtered.length / votes.length` with `filtered.length` of `total` plus the `Showing from–to` note; disable Next when `offset + limit >= total`.
6. `Voturi.tsx:144-197` — add a visible `positions_incomplete` badge in an extra `<th scope="col">Positions</th>` cell:
   ```tsx
   <td className="…">{v.positions_incomplete ? t("vote.positionsIncomplete", "incomplete") : "complete"}</td>
   ```
7. Under the table, render the position note with counts derived from the scope's rows where possible; if the API does not expose an aggregate, state the per-row flag only and **do not** print 11008/6258 as a live UI number (those are measured facts from §1.3, not an endpoint field).
8. `i18n.ts` — add `view.voturi.intro` update, `view.voturi.scopeNote`, `vote.positionsIncomplete`, `view.voturi.positionsNote`, `view.voturi.page`, `view.voturi.next`, `view.voturi.prev` in ro+en.
9. `tests/test_r08_feature_honesty.py` — assert `/api/votes` returns `scopes` and that `scopes` sums to `total`; assert each returned row has a boolean `positions_incomplete`.

**Checkpoint W8:**
```bash
grep -n '"scopes": scopes' backend/routers/api.py                 # 1 line, exit 0
test -z "$(git grep -n 'Chamber of Deputies and the Senate' -- frontend/src/pages/Voturi.tsx frontend/src/i18n.ts)" # exit 0
```
Corpus proof: `.venv/bin/python - <<'PY' … PY` probe from §1.3 prints `votes: [('deputies','2020') 52]` for `data/parlament.db`.

**Rollback W8:** `git checkout eb693b4 -- frontend/src/pages/Voturi.tsx frontend/src/api/client.ts frontend/src/i18n.ts backend/routers/api.py`.

---

### W9 — Radar: scope, error isolation, cap disclosure

**Gate A (recommended):** derive scope from `VotesResponse.scopes` (W8), show `Showing first 30 of N votes`, and treat a failed **positions** query as an excluded column with disclosure — not as a blank page.
**Gate B:** keep the 30-vote sample but relabel the page `Sample roll-call alignment (first 30 votes in scope)` and add the same positions disclosure. B is acceptable only with pagination explicitly declared out of scope.

**Honest copy:** EN `Sample of {{shown}} of {{total}} votes in scope {{legislature}}. Colour = dominant party choice; number = count of MPs with that choice. {{failed}} vote(s) had positions that could not be loaded and are excluded from the matrix — this is an error, not an empty result.` Plus the W8 `positions_incomplete` note.

**Steps (A):**
1. `Radar.tsx:25-28` — query with scope from W8 (`chamber`, `legislature`, `limit: 30`, `offset: 0`).
2. `Radar.tsx:33-39` — keep `useQueries`, but add `retry: 1`.
3. `Radar.tsx:87-105` — change the loading branch to only `votesQuery.isLoading || positionQueries.some(q => q.isLoading && q.fetchStatus !== "idle")`; **delete** the `positionQueries.some(q => q.isError)` whole-page error branch. Keep only `votesQuery.isError` as a page-level error.
4. `Radar.tsx:41-50` — build `positionsData` only from successful queries; count failures:
   ```tsx
   const failedPositions = positionQueries.reduce((n, q) => n + (q.isError ? 1 : 0), 0);
   ```
5. `Radar.tsx:121-126` — the "no data" branch must require `votesQuery.isSuccess && votes.length === 0` (a failed positions query must not produce "Roll-call data not yet available").
6. `Radar.tsx:199-203` — append the disclosure copy; add the `positions_incomplete` note from W8.
7. `i18n.ts` — add `view.radar.sampleNote`, `view.radar.failedPositions`, `view.radar.positionsNote` in ro+en.

**Checkpoint W9:** `test -z "$(git grep -n 'positionQueries.some((q) => q.isError)' -- frontend/src/pages/Radar.tsx)"` → exit 0; `grep -n 'failedPositions' frontend/src/pages/Radar.tsx` → exit 0.

**Rollback W9:** `git checkout eb693b4 -- frontend/src/pages/Radar.tsx frontend/src/i18n.ts`.

---

### W10 — Grafice / Topuri: scope, pagination, rebellion definition

**Gate A (recommended):** derive scope from W8 `scopes` for all four vote pages; use backend `total` for Topuri pagination; fix rebellion in the backend to exclude `abstain`/`not_voting` from "against majority".
**Gate B:** keep the definitions but relabel: `Rebellion = any choice other than the party majority, including abstain and not-voting`, keep the 100-row cap with an explicit `Showing first 100 of N` note. Use B if changing the metric definition is not authorised (it changes published numbers — requires an owner decision and a changelog note).

**Honest copy:** EN Grafice intro: `Party cohesion from observed roll-call positions and switch_group events in the selected scope. "Cohesion" here is the share of recorded positions by choice, not a party-discipline score.` EN Topuri note (A): `Loyalty = share of yes/no votes with the party majority. Rebellion = share of yes/no votes against it. Abstain and not-voting are excluded from both and reported separately. Participation = share of votes in scope with a recorded position.` EN scope note: `Scope: deputies / {{legislature}} — {{total}} votes. Showing {{from}}–{{to}} of {{n}} MPs.`

**Steps (A):**
1. **Grafice** `Grafice.tsx:11-19` — add a scope query `api.votes({limit:1})`, derive `legislature` from `scopes` (largest total), then:
   ```tsx
   queryFn: () => traseismSummary(legislature, "deputies")
   queryFn: () => api.voteCohesion("deputies", legislature)
   ```
   `Grafice.tsx:168-170` — `<VoteActivityChart chamber="deputies" legislature={legislature} />`.
2. **Grafice** `:25-41`, `:57-62`, `:131-163` — split the gates: summary block renders when `summary` exists and `summaryQuery.isSuccess`, independent of cohesion; cohesion block renders only when `cohesionExists && cohesion.length`; each failed/empty block gets its own honest message (`empty.rollcall` only for `data_exists === false`, `cohesionLoadError` for `isError`). Remove the hardcoded `2024` string from the whole file.
3. **Topuri** `:20-24` — `api.scorecard(legislature, "deputies", limit, offset, minVotes)`; add `const [offset, setOffset] = useState(0)`, `total = scorecardQuery.data?.total ?? 0`, `limit = 100`; render `Showing {{from}}–{{to}} of {{total}} MPs` and Next/Prev buttons.
4. **Backend rebellion** `api.py:1494-1499` — replace the unconditional `else`:
   ```python
   if majority == pos.choice:
       stats["loyal_votes"] += 1
   elif pos.choice in ("yes", "no") and majority in ("yes", "no"):
       stats["rebel_votes"] += 1
   # abstain / not_voting are neither loyal nor rebellious; they remain in
   # *_votes counters and in total_votes (participation).
   ```
   `:1521-1523` — keep denominators as `total` (participation semantics unchanged) and document the new definition in the docstring at `:1421-1427`.
5. `tests/test_r08_feature_honesty.py` — add a regression test with seeded votes/positions: an MP who abstains against the party majority must have `rebellion_pct == 0`, `loyalty_pct == 0`, and `participation_pct > 0`; existing scorecard route tests stay green.
6. `i18n.ts` — add/update `view.grafice.intro`, `view.grafice.note`, `view.grafice.scopeNote`, `view.topuri.note`, `view.topuri.scopeNote`, `view.topuri.page` in ro+en.

**Checkpoint W10:**
```bash
test -z "$(git grep -n 'traseismSummary(\"2024\"\|voteCohesion(\"deputies\", \"2024\"\|legislature=\"2024\"' -- frontend/src/pages/Grafice.tsx)" # exit 0
grep -n 'elif pos.choice in ("yes", "no")' backend/routers/api.py                    # exit 0
```
`.venv/bin/python -m pytest tests/test_analytics.py tests/test_analytics_transparency.py -q` → exit 0.

**Rollback W10:** `git checkout eb693b4 -- frontend/src/pages/Grafice.tsx frontend/src/pages/Topuri.tsx frontend/src/i18n.ts backend/routers/api.py`.

---

## 7. Consolidated CHECKPOINTS (exact command → expected output → exit)

Run from `/home/nedaktov/parlament-deschis` unless noted. Capture raw output into the evidence log.

| # | Command | Expected output | Exit |
| --- | --- | --- | --- |
| CP-0 | `test "$(git rev-parse HEAD)" = "$(git rev-parse eb693b4)" && echo BASELINE_OK` | `BASELINE_OK` | 0 |
| CP-1 | `bash scripts/check-doc-truth.sh` | no false-claim hits (empty hit section) | 0 |
| CP-2 | `git diff --check` | no output | 0 |
| CP-3 | `.venv/bin/python -m pytest tests/test_r08_feature_honesty.py -q` | all new regression tests pass; count recorded | 0 |
| CP-4 | `.venv/bin/python -m pytest -q` | every test passes (baseline 408 + new); count recorded | 0 |
| CP-5 | `.venv/bin/ruff check .` | `All checks passed!` | 0 |
| CP-6 | `cd frontend && npm run lint` | no TS/ESLint errors | 0 |
| CP-7 | `cd frontend && npm run build` | Vite build succeeds | 0 |
| CP-8 | `git grep -n 'Coalition Stability\|PopuList data\|Every figure above is an observed count\|c === "partial" ? 60' -- frontend/src` | no output | 1 (grep) / 0 when wrapped in `test -z` |
| CP-9 | `git grep -n 'positions_incomplete' -- frontend/src/pages/Voturi.tsx frontend/src/pages/Radar.tsx backend/routers/api.py` | ≥3 hits | 0 |
| CP-10 | `git grep -n 'coverageDimensions' -- frontend/src/api/client.ts frontend/src/pages/CoverageView.tsx` | ≥2 hits | 0 |
| CP-11 | read-only corpus probe from §1.3 (both DBs) | `senate persons 1509 / all persons 5282`; dev `52` votes all incomplete; real `177` with `('deputies','2024') 45` | 0 |
| CP-12 | `python3 scripts/ui_validate.py http://127.0.0.1:5174` (only if a local server + Playwright/axe exist) | per-route table, no JS errors, no axe violations | 0 — otherwise **NOT PROVEN**, never claimed |

> CP-12 is explicitly conditional. `docs/LOAD-TEST-EVIDENCE.md:14-17,266-275` forbids treating staging/production as proven. Do not start a server against production to satisfy a checkpoint.

---

## 8. Verification gates (ordered; all must be green before acceptance)

1. **Baseline gate** — CP-0; backup manifest from §4 exists and checksums still match before edits.
2. **Red/green gate** — for every new regression test, demonstrate it fails at baseline (run against the `/tmp` backup copy or before the edit) and passes after. Evidence log must contain both outputs.
3. **Static honesty gate** — CP-8/9/10 and every per-W checkpoint. A clean static check is necessary but **not sufficient**: it proves the string is gone, not that the page is correct.
4. **API shape gate** — CP-3; additive fields (`trigger_provenance`, `scopes`, `legislature` filter) must not remove or rename any existing field.
5. **Full backend gate** — CP-4 + CP-5.
6. **Frontend gate** — CP-6 + CP-7 (`noUnusedLocals` is the safety net for deleted helpers/imports).
7. **Doc-truth gate** — CP-1 + CP-2; if `docs/API.md` was updated for new fields, ensure commands in it remain runnable.
8. **Browser gate** — CP-12 if and only if the local environment exists; otherwise log `NOT PROVEN — no browser/axe run` and keep the final verdict at `PROVEN (static/backend only)`.
9. **No-new-claim gate** — final `git diff` review: no new "observed", "complete", "official", "full coverage", "PopuList", or "genealogy" claim unverified by an endpoint field or an explicit source line.

---

## 9. Acceptance criteria

- [ ] Every W1–W10 item has a recorded gate (`A` or `B`) and the honest copy in both `ro` and `en`.
- [ ] "Coalition Stability" / "Stabilitatea coalițiilor" no longer appears in product copy; trigger labels carry a visible provenance disclosure or are removed.
- [ ] Bureau card is a declared gap or absent; no implied composition figure remains.
- [ ] Ideology chart contains **zero** `0.00` points produced from null scores; no PopuList claim; the "not yet ingested" note appears only when `data_exists === false`.
- [ ] SenateHistory headlines use senate rows only (1509, 10 scopes, full = count not `%`); HOLD notice present; licence says OGL-ROU-1.0 for senat.ro.
- [ ] Report has no `60` for `partial`; EN footer distinguishes observed counts from derived scores; "people in the corpus" and "group switches" labels used.
- [ ] CoverageView calls `/api/coverage/dimensions`; no `overallPct` or rounded/null-derived percentage rendered.
- [ ] LegislatureDetail returns an honest unknown-year message instead of 1990 fallback data; movements query is scoped and its cap disclosed.
- [ ] Vote pages never hardcode `2024`/`2020`; scope comes from data; pagination uses backend `total`; `positions_incomplete` is visible on Voturi and disclosed on Radar/Grafice/Topuri.
- [ ] A failed positions request on Radar no longer produces "no data" or a blank page.
- [ ] All CP-0…CP-11 gates exit 0; CP-12 is either 0 or explicitly `NOT PROVEN`.
- [ ] Only files from §2 changed; `git diff --stat` reviewed; no DB/data/baseline file touched.

---

## 10. Dependencies

- **W8 before W9/W10** — `VotesResponse.scopes` is the scope source for Radar, Grafice and Topuri. If W8 gate B is chosen, W9/W10 must use the one-off probe variant and say so.
- **W6 depends on** existing backend `api.py:430-441` + `pipeline/coverage.py:192-259` (already present — no new endpoint work).
- **W7 gate A depends on** `Event.legislature` existing (`queries.py:559`) — verified.
- **W4 depends on** `docs/SENATE-PROFILE-IMPACT.md` HOLD decision (already present); do **not** re-open the ingest.
- **W2/W3 depend on** `docs/DECISION-PARTY-GENEALOGY.md` and `pipeline/licenses.py` for the "never infer / never claim unverified licence" rule.
- **No dependency** on staging, Vercel, deployment, or live-network evidence (`docs/LOAD-TEST-EVIDENCE.md`).
- Blocking condition for any Gate A that changes published numbers (W10 rebellion): owner sign-off + changelog note; otherwise choose Gate B.

---

## 11. Side-quest policy

Everything not in §2 is a side-quest and **REJECTED** in this wave, even if the audits list it:

- FN-1 / X2 (single `useAsOf()` hook across all pages), FN-2 (one canonical switch definition), X3 (shared state components), X4 (full i18n key sweep beyond the keys named here), X5 (nav/orphan routes), X6 (provenance on every table), X7 (design system / DataBar paint / contrast) — **other recipes**, not R-08.
- AP-1/AP-2/AP-3/AP-4/AP-7 visual repairs (HeroGraphic colours, DataBar hex-in-className, ProgressRing SVG paint, `.wrap`, canvas theme) — visual skill/recipe, not R-08. W5 only removes the fabricated *value*, it does not repaint the ring.
- Party genealogy ingestion, `previous_party_id`/`successor_party_id` population — **forbidden** by `docs/DECISION-PARTY-GENEALOGY.md`.
- Senate profile ingest — **HOLD**, forbidden by `docs/SENATE-PROFILE-IMPACT.md`.
- Adding a Vercel Cron, editing `vercel.json`, staging load tests, production requests — forbidden/deferred by `docs/LOAD-TEST-EVIDENCE.md`.
- Changing the strict audit baseline, weakening a test, touching `pipeline/analytics.py` except W1 gate B, or editing any vault document — forbidden.

If a step in §6 requires touching a forbidden file, stop, mark that step `NOT PROVEN / BLOCKED`, choose the documented Gate B, and report — do not improvise.

---

## 12. NOT PROVEN (must be copied verbatim into the implementer's evidence log)

- **No browser render, screenshot, computed-style/contrast measurement, axe/WCAG-AA run, keyboard walk, touch test or print-preview** was performed by this recipe agent. Every visual/UX claim in the audits remains static-code evidence until CP-12 is run.
- **No live API payload** from Render/Vercel/production was inspected. All corpus numbers in §1.3 were measured locally from `data/parlament.db` and `data/parlament-real.db` via read-only SQLite URI; the two corpora disagree on 2024 vote presence, which is exactly why scope must be derived from data.
- **Staging and production performance** are NOT PROVEN (`docs/LOAD-TEST-EVIDENCE.md:14-17`); the local load test is not evidence for these changes.
- **The 134-GUID figure** on SenateHistory is CONTEXT from discovery notes, not an archived dataset count (`docs/SENATE-PROFILE-IMPACT.md:7-9`); the recipe removes the claim rather than sourcing it.
- **Trigger dates/labels** in `pipeline/analytics.py:24-73` have no source URL in the repository. Gate A discloses them; it does **not** claim they are sourced.
- **PopuList licence** is UNVERIFIED (`pipeline/licenses.py:196-201`); no amount of copy editing makes it an ingestible source.
- **The 60% completeness figure** in `Report.tsx:95` has no backend field behind it and cannot be proven; it is removed, not replaced with another estimate.
- This document is a **strategy/recipe only**. No product file was edited and no test was run by R-08; all commands above are to be executed by the implementer.

---

## 13. Rollback (global)

```bash
cd /home/nedaktov/parlament-deschis
# 1. Restore every owned file to baseline
git checkout eb693b4 -- \
  frontend/src/pages/{Coalitions,InstitutionalView,Ideology,SenateHistory,Report,CoverageView,LegislatureDetail,Voturi,Radar,Grafice,Topuri}.tsx \
  frontend/src/api/client.ts frontend/src/i18n.ts \
  backend/routers/api.py backend/queries.py \
  docs/API.md tests/test_r08_feature_honesty.py
# 2. Confirm pristine
git diff --check
sha256sum -c "$BACKUP_DIR/SHA256SUMS"    # all OK (the patch line included)
# 3. Re-run the gates to confirm the baseline is healthy again
.venv/bin/python -m pytest -q
cd frontend && npm run lint && npm run build
```

If a commit was already made, use `git revert <sha>` instead of `git checkout`, then re-run §8. Never `git push`, never delete a tag, never touch the data directory.

---

## 14. Evidence log template (implementer fills this in)

| Command | Raw output (verbatim) | Exit | PASS / FAIL / NOT PROVEN |
| --- | --- | --- | --- |
| `test "$(git rev-parse HEAD)" = "$(git rev-parse eb693b4)"` | | | |
| `sha256sum -c $BACKUP_DIR/SHA256SUMS` | | | |
| W1 gate line (`W1 GATE=…`) | | | |
| … W10 gate lines … | | | |
| CP-1 … CP-12 | | | |
| `git diff --stat` | | | |

**Output contract:** commit SHA (if committed), diff stat, per-checkpoint table, per-W gate decisions, and a self-verdict of `PASS`, `PASS (static/backend only)`, or `REJECT`. A missing checkpoint output is `NOT PROVEN`, never a pass.
