# R-07 — Provenance rendering, i18n sweep, navigation cleanup

| Field | Value |
| --- | --- |
| Agent | STRATEGY/RECIPE R-07 (read-only product code; this document is the only write) |
| Project | `/home/nedaktov/parlament-deschis` |
| Baseline declared by the parent session | `main` at `eb693b4` |
| Observed `HEAD` at authoring time | `80d91a9` (ancestor of `eb693b4`; see Preconditions) |
| Audit inputs | `TRIAD-AUDIT-2026-11-21.md` FN-6; `FRONTEND-AUDIT-2026-11-21.md` X4/X5/X6 |
| Status | **Design / implementation-ready recipe — NOT implementation** |
| Scope | Frontend rendering, i18n dictionaries + CI gate, nav/route reachability, dead-component disposition |
| Out of scope | X1/X2/X3/X7/X8, visual redesign, backend schema changes (one optional, explicitly gated exception) |

> **Naming collision (honesty note).** `R-07` is already used as a *risk ID* in
> `docs/MASTER-INTEGRATION-BLUEPRINT-WAVE2.md:330` ("i18n missing key → undefined
> label"). This recipe is the repair recipe, not that risk row. Do not merge the two.

---

## 1. Objective

1. **FN-6 / X6 — provenance at the table layer:** render `source_url`, `confidence`,
   `date/event precision`, `snapshot_hash`/`snapshot_url` and backend `note`/`reason`
   on every page whose API response already supplies them. Never invent a value; render
   only when supplied, and render nothing when absent.
2. **X4 — i18n sweep:** add all missing `ro`/`en` pairs found by the audit (69 distinct
   keys, 132 per-locale insertions) and add a **zero-dependency key-diff CI gate** that
   fails on any literal key missing in either locale, any ro↔en asymmetry, or any
   duplicate definition.
3. **X5 — nav/route cleanup:** link or formally deprecate the 6 orphan routes
   (`/compare-mps`, `/Voturi`, `/radar`, `/grafice`, `/topuri`, `/ideology`), and wire
   or delete the dead components (`LiveFeed`, `About`, `ui/Modal`, `ui/Drawer`,
   `TimelineStrip`). Document each decision in this file; no silent choices.
4. **Evidence over assertion:** every claim in this recipe is traceable to `path:line`
   below; every implementation step ends in a checkpoint with an exact command,
   expected output and exit code.

---

## 2. Evidence (`path:line`)

### 2.1 Audit findings

| ID | Claim | Evidence |
| --- | --- | --- |
| FN-6 | "Provenance exists in API, absent from DOM" — `source_url`, `confidence`, `date_precision`, `snapshot_hash`, `CoverageRow.note`, committee source/precision, movement reason dropped | `Parlament Deschis Obsidian vault/40-FRONTEND/TRIAD-AUDIT-2026-11-21.md:68`; enhancement order `:83` |
| X4 | Dozens of `t(key, "English…")` calls have no ro/en entry; `nav.parties`, `senateStatLegislatures` resolve to raw keys | `.../FRONTEND-AUDIT-2026-11-21.md:42`; recommended order `:101` |
| X5 | 6 routes with no nav link; `About.tsx`, `LiveFeed.tsx` have no reachable importer; `Modal`/`Drawer`/`TimelineStrip` unused; Traseism About never opens | `.../FRONTEND-AUDIT-2026-11-21.md:43`; `:102-103` |
| X6 | API rows carry provenance; pages discard it on Traseism, Committees, PartyProfile, PersonDeepDive, CoverageView, SenateHistory, PartyTimeline, Ideology | `.../FRONTEND-AUDIT-2026-11-21.md:44`; `:104` |

### 2.2 API contract already supplies the fields (no new data needed for 8 of 9 pages)

| Field | Serializer evidence | Frontend type evidence |
| --- | --- | --- |
| membership `start_precision`, `end_precision`, `source_url` | `backend/queries.py:79-93`; `backend/routers/api.py:518-530` | `frontend/src/api/client.ts:31-44` |
| event `precision`, `reason`, `confidence`, `source_url` | `backend/queries.py:96-114`; party movements reuse it at `backend/queries.py:857-880` | `frontend/src/api/client.ts:46-62`; **party movement type is truncated** at `frontend/src/api/client.ts:226-236` |
| evidence `source_url`, `snapshot_hash`, `snapshot_url`, `note` | `backend/routers/api.py:547-561`; `backend/queries.py:360-371` | `frontend/src/api/client.ts:64-73` |
| `CoverageRow.note` | `backend/queries.py:643-744` (`:663`, `:731`) | `frontend/src/api/client.ts:105-122` |
| committee member `start_precision`, `end_precision`, `source_url` | `backend/routers/api.py:518-530` | `frontend/src/api/client.ts:751-762` |
| vote `source_url` (list), `snapshot_hash`, `truth_contract_version` (detail) | `backend/routers/api.py:1158-1175`, `:1201-1223` | `frontend/src/api/client.ts:268-282`, `:293-311` |
| party-facts `gaps.note` | `backend/routers/api.py:1004-1016` | declared locally in `frontend/src/pages/PartyTimeline.tsx:23-27` |
| ideology `meta.generated_at`, `meta.count` | `frontend/src/api/client.ts:343-347`, `:923-928` | page ignores it: `frontend/src/pages/Ideology.tsx:300-338` |
| **traseism ledger** supplies **only** `source_url` + `precision` | `pipeline/traseism.py:215-256` (rows `:240-253`); route `backend/routers/api.py:1661-1679` | `frontend/src/api/client.ts:613-623` |

### 2.3 Where the DOM drops it (per page)

| Page | Currently rendered | Dropped | Evidence |
| --- | --- | --- | --- |
| Traseism | `coverage.note`, `row.precision`, `row.source_url` | backend `confidence`/`snapshot_hash` **not supplied** by this endpoint (see §2.2) | `frontend/src/pages/Traseism.tsx:159-160`, `:385-402` |
| Committees | member name/group/role/dates/status | `start_precision`, `end_precision`, `source_url` | `frontend/src/pages/Committees.tsx:23-52` (no provenance cell), header `:120-138` |
| PartyProfile | raw `m.type`, date, chambers, names | **all** event provenance (backend supplies it) | `frontend/src/pages/PartyProfile.tsx:150-190`; type gap `frontend/src/api/client.ts:226-236` |
| PersonDeepDive | membership `source_url`, evidence popover (note/source/snapshot) | **event** `precision`, `confidence`, `reason`, `source_url`; committee-member precision | `frontend/src/pages/PersonDeepDive.tsx:186-214`, `:254-285`; `frontend/src/components/CitationPopover.tsx:64-90` |
| CoverageView | completeness, counts, percentages, date | `row.note` | `frontend/src/pages/CoverageView.tsx:190-245` |
| SenateHistory | `row.note` **already rendered** | no provenance field supplied by `CoverageItem` beyond note | `frontend/src/pages/SenateHistory.tsx:140-158`; `frontend/src/api/client.ts:105-112` → **no edit expected** |
| PartyTimeline | hardcoded methodology + gap counts | backend `gaps.note` | `frontend/src/pages/PartyTimeline.tsx:166-181`; `backend/routers/api.py:1004-1016` |
| Ideology | "not yet ingested" note + planned sources | `meta.generated_at`, `meta.count` | `frontend/src/pages/Ideology.tsx:300-338` |
| Voturi / RollCallTable | vote-row `source_url`, position `source_url` | `voteDetail.snapshot_hash`, `truth_contract_version` (never fetched) | `frontend/src/pages/Voturi.tsx:183-190`, `:204-216`; `frontend/src/components/RollCallTable.tsx:126-133` |

### 2.4 i18n gaps — measured, not remembered

Static extraction (`t("literal")` call sites vs both dictionary blocks in
`frontend/src/i18n.ts`, with nested `confidence: { … }` flattened to
`confidence.<key>`) on the baseline tree:

| Measure | Value |
| --- | ---: |
| Literal `t()` keys used in `frontend/src/**/*.{ts,tsx}` (excluding `i18n.ts`) | 538 |
| Keys defined in `ro` | 535 |
| Keys defined in `en` | 536 |
| Used but missing in `ro` | 66 |
| Used but missing in `en` | 66 |
| Defined only in `ro` | 2 (`nav.committees`, `nav.compare`) |
| Defined only in `en` | 3 (`view.ideology.licence`, `.sources`, `.status`) |
| Distinct keys needing action (union) | **69** |
| Duplicate definitions in either locale | 0 |

Dictionaries: `frontend/src/i18n.ts:4-567` (`ro`), `:568-1130` (`en`), init `:1133-1138`.
Raw-key call sites: `frontend/src/router.tsx:203` (`nav.parties`),
`frontend/src/pages/Parties.tsx` (`nav.parties`),
`frontend/src/pages/SenateHistory.tsx` (`senateStatLegislatures`).

Dynamic (non-literal) call sites that a naive key-diff would falsely flag:
`Traseism.tsx:76,156,577,797`; `CoverageView.tsx:220`; `ChamberView.tsx:25`;
`MembershipGantt.tsx:54`; `CitationPopover.tsx:64`; `About.tsx:230,290`;
`LiveFeed.tsx:124`; `TimelineChart.tsx:199`. Their resolved values are all already
defined; the gate in §4 Step 1 carries an explicit, commented allowlist.

### 2.5 Routing / dead component evidence

* 24 routes registered: `frontend/src/router.tsx:500-525`; 16 `NavLink`s: `:247-294`.
* 6 orphans (no `NavLink` target): `/compare-mps` (`:437-442`), `/Voturi` (`:465-470`),
  `/radar` (`:472-477`), `/grafice` (`:479-484`), `/topuri` (`:486-491`),
  `/ideology` (`:493-498`). `/person/$id` is reached via global Search (`:227-231`);
  `/electoral` is redirect-only (`:322-336`) — both are allowlisted, not orphans.
* `mps.compareLink` is defined in both locales (`i18n.ts:397`, `:954`) but has **zero**
  call sites → the `/mps` → `/compare-mps` link promised by the audit is absent.
* `/person/$id` is not nav-linked but is search-reachable; do not "fix" it.
* `components/LiveFeed.tsx` (221 lines): no importer; only self-references plus a
  comment in `Footer.tsx:7`. **A CI guard compiles and renders it**:
  `scripts/check_livefeed_props.mjs` (invoked by `.github/workflows/ci.yml:95-105`).
* `components/About.tsx` (370 lines): imported at `Traseism.tsx:14`, rendered at `:945`,
  but `setAboutOpen(true)` is **never called** (`:668` declares the state; only the
  close setter appears at `:945`). The header's separate `AboutModal` at
  `router.tsx:112-173` **is** wired (`:232-236`, `:303`) — do not confuse the two.
* `components/ui/Modal.tsx` (70 lines), `components/ui/Drawer.tsx` (65 lines),
  `components/TimelineStrip.tsx` (152 lines): zero importers anywhere in `frontend/src`.
  `TimelineStrip` also has an empty TODO handler (TA-1 in triad audit `:46`).
* `scripts/ui_validate.py:47-77` hard-codes all 24 route paths, including the 6
  orphans. Deleting/redirecting routes **requires** editing that list; linking them
  keeps the UI gate unchanged.
* `.github/workflows/ci.yml`: `test` job `:30-42` (ruff, pytest, frontend lint/build);
  `evidence-guards` job `:95-122` (LiveFeed props guard + Playwright probe).

---

## 3. Exclusive file list (what the implementer may touch)

**Edit**

1. `frontend/src/i18n.ts`
2. `frontend/src/api/client.ts` (extend `PartyMovementResponse` only)
3. `frontend/src/router.tsx` (nav links + document-title labels only)
4. `frontend/src/pages/Traseism.tsx`
5. `frontend/src/pages/Committees.tsx`
6. `frontend/src/pages/PartyProfile.tsx`
7. `frontend/src/pages/PersonDeepDive.tsx`
8. `frontend/src/pages/CoverageView.tsx`
9. `frontend/src/pages/PartyTimeline.tsx`
10. `frontend/src/pages/Ideology.tsx`
11. `frontend/src/pages/Voturi.tsx`
12. `frontend/src/pages/LiveDashboard.tsx`
13. `frontend/src/components/ProvenanceStamp.tsx` (**new**)
14. `scripts/check_i18n_keys.mjs` (**new**)
15. `scripts/check_routes_nav.mjs` (**new**)
16. `frontend/package.json` (add `i18n:check` script)
17. `.github/workflows/ci.yml` (add two guard steps)

**Delete with `git rm`**

18. `frontend/src/components/ui/Modal.tsx`
19. `frontend/src/components/ui/Drawer.tsx`
20. `frontend/src/components/TimelineStrip.tsx`

**Optional, separately gated (default: NOT applied)**

21. `backend/queries.py` — extend `get_party_movements` ledger rows (Step 3B only)

**Explicitly NOT touched**

`components/About.tsx` (wired, not edited), `components/LiveFeed.tsx` (wired, not
edited — its props/query contract is guarded by CI), `components/CitationPopover.tsx`,
`components/RollCallTable.tsx`, `components/PersonDrawer.tsx`, `components/LoadingState.tsx`,
`scripts/check_livefeed_props.mjs`, `scripts/ui_validate.py`, `scripts/check-hook-order.mjs`,
all Python backend/pipeline files except optional #21, all vault notes, `.nedcode/`,
`docs/*.md` other than this file, dependencies/lockfiles.

> Do **not** run `git add -A`: the working tree has pre-existing untracked
> `.nedcode/` and a vault `backlink.json` that are not ours (see Preconditions).

---

## 4. Preconditions

```bash
cd /home/nedaktov/parlament-deschis
git rev-parse HEAD                    # observed: 80d91a90eb332e8affc74e740de38c1fb65aab78
git cat-file -t eb693b4               # must print: commit
git merge-base --is-ancestor HEAD eb693b4 && echo ANCESTOR_OK
git diff --name-status HEAD eb693b4 -- frontend/src docs scripts .github
# expected: NO OUTPUT (product files at HEAD == declared baseline eb693b4)
git status --short
# expected only: ?? .nedcode/
#               ?? "Parlament Deschis Obsidian vault/.obsidian/backlink.json"
node --version                        # observed v24.22.3; >=18 required for .mjs guards
cd frontend && npm ci && npm run lint && npm run build
# expected: exit 0 on the untouched baseline (known-good starting point)
```

* If `git diff HEAD..eb693b4` is non-empty for the listed paths, **stop** and rebase the
  recipe's line numbers against the actual baseline before editing.
* If `npm run lint`/`build` fail before any edit, the tree is not a valid R-07 starting
  point; report the pre-existing failure and stop (side-quest policy, §13).
* The declared baseline `eb693b4` is a *merge commit on `main`*; the audit vault notes
  were committed after the observed `HEAD` but describe the same product source, so the
  product-code evidence above is valid for both commits.

---

## 5. Decisions (recorded before implementation)

| # | Decision | Rationale | Alternative rejected |
| --- | --- | --- | --- |
| D1 | Create one shared `ProvenanceStamp` component; each page passes only the fields its API supplies. | One render path, one label set, no per-page string drift; absent fields render nothing. | Copy/paste a provenance block into 9 pages (drift risk). |
| D2 | Extend `PartyMovementResponse` in TypeScript only — backend already returns the fields via `serialize_event`. | No API change needed; evidence `backend/queries.py:857-880`. | Backend serializer change (unnecessary). |
| D3 | Traseism ledger confidence/snapshot: **deferred by default**, optional Step 3B included. | `pipeline/traseism.py:240-253` does not supply those fields; rendering them is impossible without a backend change. Claiming otherwise would fabricate provenance. | Pretend the fields exist. |
| D4 | Link all 6 orphan routes in a secondary "Vote analytics" nav row; keep the literal `/Voturi` path. | `scripts/ui_validate.py:47-77` hard-codes the paths; linking keeps the UI gate valid. The capital `V` is a recorded wart, deferred to a coordinated rename recipe. | Delete routes (breaks UI gate + features the vision calls first-class). |
| D5 | Wire `LiveFeed` into `LiveDashboard`; do **not** change its props or query signature. | No importer today, but CI guard compiles it and asserts `[40,"senate","2024"]`/`["recent","2024","senate"]`; wiring preserves the guard and restores recent activity. | Delete it requires editing the guard and CI (§2.5). |
| D6 | Wire the existing `About` modal in Traseism using the already-defined `traseismAboutButton` key. | Component and copy exist; only the trigger is missing. The router's `AboutModal` is a different, already-wired dialog — keep both. | Delete 370 lines of source-cited project info. |
| D7 | `git rm` `ui/Modal.tsx`, `ui/Drawer.tsx`, `TimelineStrip.tsx`. | Zero importers, no CI guard references, and the audit flags them as incomplete/inert (TA-7/TA-1). Keep the working exemplars `About.tsx`/`PersonDrawer.tsx`. | Keep dead code and claim a design system exists. |
| D8 | Add two zero-dependency Node guards (`check_i18n_keys.mjs`, `check_routes_nav.mjs`) to the `test` CI job. | Existing CI already runs root-level Node guards; no new dependency, deterministic exit codes. | A Python gate needing a new requirements entry. |

> If the parent session prefers "formally deprecate" over "link" for any orphan, use
> **Step 5B** instead of 5A for that route. Do not mix silently: record the choice in
> the `DEPRECATED_ROUTES` map with a reason and keep the route/nav gate green.

---

## 6. Numbered steps (implementation-ready)

### Step 0 — Backup + checksum (mandatory, before any edit)

```bash
cd /home/nedaktov/parlament-deschis
BK="/tmp/opencode/R-07-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BK"
git diff HEAD > "$BK/unstaged.patch"                    # may be empty; keep the file
git diff --cached HEAD > "$BK/staged.patch"             # may be empty; keep the file
tar -czf "$BK/product.tar.gz" \
  frontend/src frontend/package.json scripts .github/workflows/ci.yml docs/repair-recipes \
  2>/dev/null || true
( cd "$BK" && sha256sum unstaged.patch staged.patch product.tar.gz > SHA256SUMS )
cat "$BK/SHA256SUMS"
printf '%s\n' "$BK" > /tmp/opencode/R-07-last-backup-path
```

Keep `$BK` until acceptance is signed off; it is the rollback source (§9).

---

### Step 1 — Add the key-diff gate (write the failing test first)

Create `scripts/check_i18n_keys.mjs` with **exactly** this content (zero dependencies):

```js
#!/usr/bin/env node
/**
 * i18n key-diff gate. Fails (exit 1) when:
 *   - a literal t("key") call site is missing from ro or en;
 *   - a key is defined in only one locale;
 *   - a dynamic allowlist key is missing from either locale;
 *   - any key is defined twice in one locale.
 * Nested objects (confidence: { … }) are flattened to confidence.<key>.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "..");
const I18N = path.join(repo, "frontend/src/i18n.ts");
const SRC = path.join(repo, "frontend/src");

// Dynamic t() call sites (verified at audit time; keep this list commented with
// its source so a future refactor can update it deliberately):
//  Traseism.tsx:76,797 t(chamber|"deputies"|"senate"), :156,577 t("full"|"partial"|"none")
//  CoverageView.tsx:220 t("full"|"partial"|"none"), ChamberView.tsx:25 t(chamber)
//  MembershipGantt.tsx:54 / About.tsx:230 t(`confidence.${...}`)
//  CitationPopover.tsx:64 TYPE_LABEL map -> confidence.*
//  About.tsx:290 t(row.completeness), LiveFeed.tsx:124 event-label map
//  TimelineChart.tsx:199 t(chamber)
const DYNAMIC_ALLOWLIST = [
  "deputies", "senate", "full", "partial", "none",
  "confidence.official_ledger", "confidence.official_profile",
  "confidence.derived", "confidence.community",
  "joined", "left", "switchGroup", "switchParty", "groupFounded", "groupRenamed",
  "committeeJoined", "committeeLeft", "roleChanged", "mandateStarted",
  "mandateEnded", "event",
];

const fail = (m) => { console.error(`FAIL: ${m}`); process.exit(1); };

function localeBlock(text, open, close) {
  const a = text.indexOf(open);
  if (a < 0) fail(`cannot find ${open} in i18n.ts`);
  const b = text.indexOf(close, a + open.length);
  if (b < 0) fail(`cannot find ${close} after ${open} in i18n.ts`);
  return text.slice(a + open.length, b);
}

function definitions(block) {
  const counts = new Map();
  let nest = null;
  for (const raw of block.split(/\r?\n/)) {
    const line = raw.trim();
    if (/^confidence\s*:\s*\{/.test(line)) { nest = "confidence"; continue; }
    if (nest && /^\},?$/.test(line)) { nest = null; continue; }
    const m = line.match(/^["']([^"']+)["']\s*:/) || line.match(/^([A-Za-z_$][\w$]*)\s*:/);
    if (!m) continue;
    const key = nest ? `${nest}.${m[1]}` : m[1];
    if (key === "translation" || key === "confidence") continue;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return counts;
}

function walk(dir, out = []) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (/\.(ts|tsx)$/.test(e.name) && e.name !== "i18n.ts") out.push(p);
  }
  return out;
}

try {
  const text = readFileSync(I18N, "utf8");
  const ro = definitions(localeBlock(text, "ro: {", "\n  en: {"));
  const en = definitions(localeBlock(text, "\n  en: {", "\n};"));

  const used = new Map();
  for (const file of walk(SRC)) {
    const body = readFileSync(file, "utf8");
    const re = /\bt\(\s*(["'])([^"']+)\1/g;
    let m;
    while ((m = re.exec(body))) {
      if (!used.has(m[2])) used.set(m[2], new Set());
      used.get(m[2]).add(path.relative(repo, file));
    }
  }

  const wanted = new Set([...used.keys(), ...DYNAMIC_ALLOWLIST]);
  const missingRo = [...wanted].filter((k) => !ro.has(k)).sort();
  const missingEn = [...wanted].filter((k) => !en.has(k)).sort();
  const asymmetric = [...new Set([...ro.keys(), ...en.keys()])]
    .filter((k) => ro.has(k) !== en.has(k)).sort();
  const duplicates = [...new Set([...ro.keys(), ...en.keys()])]
    .filter((k) => (ro.get(k) ?? 0) > 1 || (en.get(k) ?? 0) > 1).sort();

  console.log(`I18N KEY DIFF ro=${ro.size} en=${en.size} used=${used.size} dynamic=${DYNAMIC_ALLOWLIST.length}`);
  for (const [name, list] of [
    ["MISSING_IN_RO", missingRo], ["MISSING_IN_EN", missingEn],
    ["ASYMMETRIC_DEFINITIONS", asymmetric], ["DUPLICATE_DEFINITIONS", duplicates],
  ]) {
    console.log(`${name} ${list.length}`);
    for (const k of list.slice(0, 20)) console.log(`  - ${k}`);
    if (list.length > 20) console.log(`  … and ${list.length - 20} more`);
  }
  if (missingRo.length || missingEn.length || asymmetric.length || duplicates.length) {
    fail("i18n key diff is not clean");
  }
  console.log("PASS: i18n key diff clean (0 missing, 0 asymmetric, 0 duplicate)");
  process.exit(0);
} catch (err) {
  fail(err && err.message ? err.message : String(err));
}
```

Wire it into CI and npm:

```bash
python3 - <<'PY'
from pathlib import Path
p = Path('.github/workflows/ci.yml')
s = p.read_text()
anchor = "      - name: Frontend lint, type-check and build\n"
assert anchor in s
add = ("      - name: i18n key diff\n"
       "        run: node scripts/check_i18n_keys.mjs\n\n"
       "      - name: Route/nav reachability guard\n"
       "        run: node scripts/check_routes_nav.mjs\n")
s = s.replace(anchor, add + anchor, 1)
p.write_text(s)

p = Path('frontend/package.json')
s = p.read_text()
assert '"lint":' in s
s = s.replace('"lint": "tsc --noEmit && eslint src --ext .ts,.tsx"',
              '"lint": "tsc --noEmit && eslint src --ext .ts,.tsx",\n    "i18n:check": "node ../scripts/check_i18n_keys.mjs"')
p.write_text(s)
PY
node scripts/check_i18n_keys.mjs; echo "exit=$?"
```

**CHECKPOINT CP1 (red) — expected on the untouched dictionaries:**

```
I18N KEY DIFF ro=535 en=536 used=538 dynamic=21
MISSING_IN_RO 66
MISSING_IN_EN 66
ASYMMETRIC_DEFINITIONS 5
DUPLICATE_DEFINITIONS 0
FAIL: i18n key diff is not clean
exit=1
```

(`dynamic=21` is the allowlist length; `ASYMMETRIC_DEFINITIONS 5` =
`nav.committees`, `nav.compare` + the three `view.ideology.*` keys. Counts are from
the baseline extraction in §2.4 and must be confirmed by the actual run.)

> If the gate prints a different `used=` count, your `t()` regex is catching a
> non-translation helper or missing a call site; investigate before Step 2.

---

### Step 2 — Fill the 69 i18n gaps (132 per-locale insertions)

Add the following entries to `frontend/src/i18n.ts`. Quoted dotted keys must be
**quoted**, exactly as the surrounding P1-A block (`i18n.ts:274-...` / `:831-...`).
Insert the flat camelCase keys next to their existing siblings (e.g. `coverage*`
near `i18n.ts:175-193`, `dashboardStat*` near `:32-36`) so the file remains readable.
**Do not add a key to a locale that already defines it** — the three
`view.ideology.*` keys exist only in `en`; `nav.committees`/`nav.compare` exist only in `ro`.

#### 2a. Keys missing in BOTH locales (add to `ro` and `en`)

| Key | ro | en |
| --- | --- | --- |
| `coalitions.statBreakups` | `Ruperi` | `Breakups` |
| `coalitions.statCongresses` | `Congrese` | `Congresses` |
| `coalitions.statFormations` | `Formări` | `Formations` |
| `coalitions.statWaves` | `Total valuri` | `Total waves` |
| `coalitions.waveTimeline` | `Cronologia valurilor — schimbări per val detectat` | `Wave timeline — switches per detected wave` |
| `coalitions.wavesInCorpus` | `valuri de schimbări în corpus` | `switch waves in the corpus` |
| `compare.viewAllParties` | `Vezi toate partidele →` | `View all parties →` |
| `coverageOverallLabel` | `Acoperire generală` | `Overall coverage` |
| `coverageStatChambers` | `Camere` | `Chambers` |
| `coverageStatEntries` | `înregistrări de acoperire` | `coverage entries` |
| `coverageStatFullCoverage` | `Acoperire completă` | `Full coverage` |
| `coverageStatLegislatures` | `Legislaturi` | `Legislatures` |
| `coverageStatPartialCoverage` | `Acoperire parțială` | `Partial coverage` |
| `dashboardStatCommittees` | `Comisii` | `Committees` |
| `dashboardStatMemberships` | `Mandate` | `Memberships` |
| `dashboardStatPersons` | `Parlamentari` | `Members of Parliament` |
| `dashboardStatSwitches` | `Schimbări` | `Switches` |
| `deepDiveViews` | `Vederi detaliate` | `Deep Dive Views` |
| `demographics.moment.totalMPs` | `membri cu dată de naștere` | `members with birth dates` |
| `demographics.sparkline.label` | `Distribuția vârstelor pe partid` | `Age distribution by party` |
| `demographics.stat.avgAge` | `Vârsta medie` | `Average age` |
| `demographics.stat.legislatures` | `Legislaturi acoperite` | `Legislatures covered` |
| `demographics.stat.medianAge` | `Vârsta mediană` | `Median age` |
| `demographics.stat.totalMPs` | `Total parlamentari` | `Total MPs` |
| `filter.year` | `An` | `Year` |
| `filter.year_all` | `Toți anii` | `All years` |
| `footer.datasetRelease` | `Versiune date: {{tag}}` | `Dataset release: {{tag}}` |
| `leaderboard.stat.top_switcher` | `Cel mai traseist` | `Top switcher` |
| `leaderboard.stat.total_switches` | `Total schimbări` | `Total switches` |
| `leaderboard.stat.unique_switchers` | `Traseiști unici` | `Unique switchers` |
| `mpcTotalMpsLabel` | `parlamentari în corp` | `members of parliament in corpus` |
| `nav.parties` | `Partide` | `Parties` |
| `navigateTo` | `Navighează către` | `Navigate to` |
| `parties.col.members` | `Membri` | `Members` |
| `parties.col.shortName` | `Acronim` | `Acronym` |
| `parties.col.switchesIn` | `Schimbări în` | `Switches in` |
| `parties.empty` | `Niciun partid nu corespunde acestei căutări.` | `No parties match this search.` |
| `parties.intro` | `Toate partidele din corpus (din setul public). Apasă un partid pentru profilul la data selectată.` | `All parties in the corpus (from the public dataset). Click a party to open its profile for the selected date.` |
| `parties.loadError` | `Nu s-au putut încărca partidele.` | `Failed to load parties.` |
| `parties.scopeNote` | `Această listă este la nivel de corpus (nu este filtrată pe legislatură/cameră în această vizualizare).` | `This list is corpus-wide (not filtered by legislature/chamber in this view).` |
| `parties.search.placeholder` | `nume sau acronim…` | `name or acronym…` |
| `partyEcosystem` | `Ecosistemul partidelor` | `Party Ecosystem` |
| `personDeepDive.title` | `Profil parlamentar` | `Parliamentary profile` |
| `pp.activeMembers` | `Membri activi` | `Active members` |
| `pp.switchTimeline` | `Cronologia schimbărilor` | `Switch timeline` |
| `pp.switchTimelineNote` | `Evenimente de schimbare pe zi, din mișcările înregistrate` | `Switch events per day across recorded movements` |
| `pp.totalMembers` | `Total membri` | `Total members` |
| `pp.totalSwitches` | `Total schimbări` | `Total switches` |
| `ptimeline.parties` | `partide în corpus` | `parties in the corpus` |
| `ptimeline.statGaps` | `Evenimente de lacună` | `Gap events` |
| `ptimeline.statLegislatures` | `Legislaturi acoperite` | `Legislatures covered` |
| `ptimeline.statParties` | `Total partide` | `Total parties` |
| `ptimeline.statSwitches` | `Total schimbări` | `Total switches` |
| `ptimeline.viewAllParties` | `Vezi toate partidele →` | `View all parties →` |
| `report.errorDesc` | `Nu am putut încărca raportul de transparență.` | `We couldn't load the transparency report.` |
| `report.errorTitle` | `Nu s-a putut încărca raportul` | `Failed to load report` |
| `report.loadingDesc` | `Compilăm corpusul de transparență. Poate dura un moment.` | `Compiling the transparency corpus. This may take a moment.` |
| `report.loadingTitle` | `Se încarcă raportul…` | `Loading report…` |
| `report.refresh` | `Reîmprospătează` | `Refresh` |
| `report.retry` | `Reîncearcă` | `Retry` |
| `senateStatLegislatures` | `Legislaturi` | `Legislatures` |
| `view.ideology.axis_gal_tan` | `Autoritar ← → Libertarian` | `Authoritarian ← → Libertarian` |
| `view.ideology.axis_left_right` | `Stânga economică ← → Dreapta` | `Economic Left ← → Right` |
| `view.ideology.legend_title` | `Pozițiile partidelor` | `Party positions` |

#### 2b. Asymmetric — add only where missing

| Key | ro | en | Add to |
| --- | --- | --- | --- |
| `nav.committees` | already `Comisii` (`i18n.ts:476`) | `Committees` | en only |
| `nav.compare` | already `Compară` (`i18n.ts:477`) | `Compare` | en only |
| `view.ideology.licence` | `Restricții de licență:` | already present (`i18n.ts:1023`) | ro only |
| `view.ideology.sources` | `Surse planificate:` | already present (`i18n.ts:1022`) | ro only |
| `view.ideology.status` | `Stare:` | already present (`i18n.ts:1024`) | ro only |

#### 2c. Provenance labels (new, both locales — needed by Step 3)

| Key | ro | en |
| --- | --- | --- |
| `prov.confidence` | `Încredere` | `Confidence` |
| `prov.precision` | `Precizie` | `Precision` |
| `prov.snapshot` | `Copie instantanee` | `Snapshot` |
| `prov.note` | `Notă` | `Note` |

> Reuse the existing `source` (`i18n.ts:195`/`:753`) and `viewOriginal`
> (`:23`/`:586`) keys for the link label; do not create `prov.source`.
> Preserve `{{tag}}` in `footer.datasetRelease` verbatim — interpolation must survive.

**CHECKPOINT CP2 (two-stage — count arithmetic derived from §2.4):**

```bash
# Stage 1 — immediately after Step 2a (64 both-locale keys added):
node scripts/check_i18n_keys.mjs; echo "exit=$?"
# expected:
# I18N KEY DIFF ro=599 en=600 used=538 dynamic=21
# MISSING_IN_RO 2        <- view.ideology.licence, view.ideology.sources
# MISSING_IN_EN 2        <- nav.committees, nav.compare
# ASYMMETRIC_DEFINITIONS 5
# DUPLICATE_DEFINITIONS 0
# FAIL: i18n key diff is not clean
# exit=1

# Stage 2 — after Step 2b (3 ro-only + 2 en-only insertions):
node scripts/check_i18n_keys.mjs; echo "exit=$?"
# expected:
# I18N KEY DIFF ro=602 en=602 used=538 dynamic=21
# MISSING_IN_RO 0
# MISSING_IN_EN 0
# ASYMMETRIC_DEFINITIONS 0
# DUPLICATE_DEFINITIONS 0
# PASS: i18n key diff clean (0 missing, 0 asymmetric, 0 duplicate)
# exit=0
```

After Stage 2, Step 2c adds 4 provenance keys per locale (→ `ro=606 en=606`) and
Step 5A adds 7 nav keys per locale (→ `ro=613 en=613`), which is the expected
final count at CP7. If any printed number differs, re-check §2b **before** proceeding;
do not weaken the gate to make a wrong count pass.

---

### Step 3 — Provenance rendering

#### 3a. Shared component (new file)

Create `frontend/src/components/ProvenanceStamp.tsx`:

```tsx
import { useTranslation } from "react-i18next";

export interface ProvenanceStampProps {
  sourceUrl?: string | null;
  confidence?: string | null;
  precision?: string | null;
  snapshotHash?: string | null;
  snapshotUrl?: string | null;
  note?: string | null;
  className?: string;
}

const CONFIDENCE_KEYS: Record<string, string> = {
  official_ledger: "confidence.official_ledger",
  official_profile: "confidence.official_profile",
  derived: "confidence.derived",
  community: "confidence.community",
};

/** Renders provenance only for fields the API actually supplied. */
export default function ProvenanceStamp({
  sourceUrl,
  confidence,
  precision,
  snapshotHash,
  snapshotUrl,
  note,
  className = "",
}: ProvenanceStampProps) {
  const { t } = useTranslation();
  if (!sourceUrl && !confidence && !precision && !snapshotHash && !snapshotUrl && !note) {
    return null;
  }
  const confidenceLabel = confidence
    ? CONFIDENCE_KEYS[confidence]
      ? t(CONFIDENCE_KEYS[confidence])
      : confidence
    : null;

  return (
    <dl className={`flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-500 ${className}`}>
      {sourceUrl && (
        <div className="flex gap-1">
          <dt className="sr-only">{t("source")}</dt>
          <dd>
            <a href={sourceUrl} target="_blank" rel="noopener noreferrer"
               className="text-sky-400 hover:underline">{t("viewOriginal")} ↗</a>
          </dd>
        </div>
      )}
      {confidenceLabel && (
        <div className="flex gap-1">
          <dt>{t("prov.confidence")}:</dt><dd className="text-slate-400">{confidenceLabel}</dd>
        </div>
      )}
      {precision && (
        <div className="flex gap-1">
          <dt>{t("prov.precision")}:</dt><dd className="text-slate-400">{precision}</dd>
        </div>
      )}
      {(snapshotHash || snapshotUrl) && (
        <div className="flex gap-1">
          <dt>{t("prov.snapshot")}:</dt>
          <dd className="font-mono text-slate-400">
            {snapshotUrl ? (
              <a href={snapshotUrl} target="_blank" rel="noopener noreferrer"
                 className="text-sky-400 hover:underline" title={snapshotHash ?? undefined}>
                {(snapshotHash ?? "link").slice(0, 12)} ↗
              </a>
            ) : (
              <span title={snapshotHash ?? undefined}>{(snapshotHash ?? "").slice(0, 12)}</span>
            )}
          </dd>
        </div>
      )}
      {note && (
        <div className="flex gap-1 max-w-full">
          <dt>{t("prov.note")}:</dt><dd className="text-amber-300/90 break-words">{note}</dd>
        </div>
      )}
    </dl>
  );
}
```

Design constraints: no link without `rel="noopener noreferrer"`; `dl/dt/dd` keeps a
data/definition semantic; `sr-only` label avoids repeating "Source:" before an icon link;
the component returns `null` when every field is absent (zero visual noise on empty data).

#### 3b. Per-page edits (exact insertion points)

1. **Committees** — `frontend/src/pages/Committees.tsx`
   * Add `import ProvenanceStamp from "../components/ProvenanceStamp";`
   * In `MemberRow` (`__:23-52`), append a cell after the Status `<td>`:
     ```tsx
     <td className="px-3 py-2">
       <ProvenanceStamp
         sourceUrl={member.source_url}
         precision={[member.start_precision, member.end_precision].filter(Boolean).join(" / ") || null}
       />
     </td>
     ```
   * Add the matching 7th header in the table (`__:120-138`):
     ```tsx
     <th scope="col" className="px-3 py-2 text-left text-slate-300 font-medium">{t("source")}</th>
     ```

2. **PartyProfile** — `frontend/src/pages/PartyProfile.tsx`
   * First fix the truncated type in `frontend/src/api/client.ts:226-236` — add
     `precision: string | null; reason: string | null; confidence: string; source_url: string | null;`
     (all already returned by `serialize_event`, evidence §2.2).
   * Inside the recent-movements button (`:163-188`), after the from→to `<div>`:
     ```tsx
     <ProvenanceStamp
       sourceUrl={m.source_url}
       confidence={m.confidence}
       precision={m.precision}
       note={m.reason}
     />
     ```

3. **PersonDeepDive** — `frontend/src/pages/PersonDeepDive.tsx`
   * In the events list (`:191-214`), after the from→org `<div>`:
     ```tsx
     <ProvenanceStamp
       sourceUrl={e.source_url}
       confidence={e.confidence}
       precision={e.precision}
       note={e.reason}
     />
     ```
   * In the committee-membership list (`:242-285`), replace the bare source `<a>`
     block with `<ProvenanceStamp sourceUrl={m.source_url} precision={[m.start_precision, m.end_precision].filter(Boolean).join(" / ") || null} />`.
   * Leave the existing `CitationPopover` (evidence note/source/snapshot) as-is — it already renders those fields.

4. **CoverageView** — `frontend/src/pages/CoverageView.tsx`
   * Add a "Note" `<th>` after the last header in the table (`:~185-196`) using
     `t("prov.note")`, and in each `<tr>` (`:~200-242`) add:
     ```tsx
     <td className="py-1.5 pr-3 text-xs text-slate-400">{row.note ?? "—"}</td>
     ```
     (No new key needed for the cell body — it is backend-authored text, not UI copy.)

5. **PartyTimeline** — `frontend/src/pages/PartyTimeline.tsx`
   * In the gap panel (`:166-181`), after the `ptimeline.gapBody` paragraph:
     ```tsx
     {gaps.note && (
       <p className="mt-2 text-xs text-amber-200/80">
         <span className="font-semibold">{t("prov.note")}: </span>{gaps.note}
       </p>
     )}
     ```
     The declared local `gaps.note` type at `:23-27` already exists; no type change.

6. **Ideology** — `frontend/src/pages/Ideology.tsx`
   * The API response exposes `meta: AnalyticsMeta` (`frontend/src/api/client.ts:923-928`).
     Guard the existing "not yet ingested" note on real data instead of showing it over
     a populated chart (this is also the honest X8 presentation fix):
     ```tsx
     {!ideology.data?.data_exists && (
       <p>{t("view.ideology.note", "Ideological data not yet ingested. No figures or invented axes shown.")}</p>
     )}
     {ideology.data?.meta && (
       <p className="mt-1 text-xs text-slate-600">
         {t("datasetPublished", "Published: {{date}}", { date: ideology.data.meta.generated_at })}
         {" · "}{ideology.data.meta.count}
       </p>
     )}
     ```
     Keep the planned-sources/licence paragraphs unchanged. If the local query variable
     is named differently in this file, use that identifier — do not introduce a second fetch.

7. **Voturi** — `frontend/src/pages/Voturi.tsx`
   * In the detail panel (`:204-216`) fetch detail once and show its provenance:
     ```tsx
     const voteDetailQuery = useQuery({
       queryKey: ["vote-detail", selectedVoteId],
       queryFn: () => api.voteDetail(selectedVoteId!),
       enabled: Boolean(selectedVoteId),
     });
     ```
     (add `useQuery` import and `api` import if absent), then inside the panel:
     ```tsx
     {voteDetailQuery.data?.data && (
       <ProvenanceStamp
         sourceUrl={voteDetailQuery.data.data.source_url}
         snapshotHash={voteDetailQuery.data.data.snapshot_hash}
         note={voteDetailQuery.data.data.truth_contract_version}
       />
     )}
     ```
     `truth_contract_version` is shown as the "note" value only because it is the only
     backend-authored qualifier on that payload; if a reviewer prefers a dedicated
     label, add `prov.truthContract` to both locales before merging.

8. **Traseism** — no change. It already renders `coverage.note`, `row.precision` and
   `row.source_url` (`:159-160`, `:385-402`); the endpoint does **not** supply
   confidence/snapshot (§2.2). Option B below is the only way to add them.

9. **SenateHistory** — no change: `row.note` is already rendered at `:158`.

#### 3B. OPTIONAL backend extension — **default: NOT applied**

To close the ledger half of FN-6, add to the row dict in `pipeline/traseism.py:240-253`:

```python
"confidence": e.confidence,
"snapshot_hash": e.snapshot_hash,
"snapshot_url": queries._snapshot_url(session, e.snapshot_hash, e.source_url),
"reason": e.reason,
```

and mirror the four fields in `frontend/src/api/client.ts:613-623`, then render them
inside the ledger rows at `frontend/src/pages/Traseism.tsx:385-410` via
`<ProvenanceStamp ... />`. `pipeline/traseism.py` already imports `Event`; add a local
`from backend.queries import _snapshot_url` import **inside the function** to avoid a
module-import cycle, or omit `snapshot_url` and derive it client-side from
`source_url`. Existing tests assert key *subsets* (`tests/test_traseism.py:252-263`),
so additive fields are safe. Apply only after `uv run pytest -q tests/test_traseism.py`
is green on the untouched baseline and record the decision in §5 D3.

**CHECKPOINT CP3:**

```bash
cd frontend && npm run lint && npm run build; echo "exit=$?"
# expected: tsc --noEmit + eslint clean; vite build completes; exit=0
cd .. && node scripts/check_i18n_keys.mjs; echo "exit=$?"
# expected: MISSING_IN_RO 0 / MISSING_IN_EN 0 / ASYMMETRIC 0 / DUP 0; exit=0
grep -R "ProvenanceStamp" frontend/src/pages | wc -l   # expected >= 8 (imports + usages)
```

---

### Step 4 — Wire or delete the dead components (decisions D5–D7)

**D5 — wire `LiveFeed` into `LiveDashboard`** (`frontend/src/pages/LiveDashboard.tsx`):

```tsx
import LiveFeed from "../components/LiveFeed";
```

Insert a section after the "Deep Dive Views" section (`:189-...`), before the closing
`</div>`:

```tsx
<section className="px-4 pb-8 sm:pb-10" data-enter>
  <h2 className="text-xl font-semibold mb-3">{t("liveFeed", "Recent activity")}</h2>
  <LiveFeed
    onSelect={(id) => navigate({
      to: "/person/$id",
      params: { id },
      search: { date: clamped },
    })}
    legislature="2024"
    chamber="deputies"
  />
</section>
```

**Do not** change `LiveFeed`'s props interface, `queryKey` or `api.recentEvents` call:
`scripts/check_livefeed_props.mjs` asserts the exact two-argument call
`[40, "senate", "2024"]` and key `["recent","2024","senate"]` when it renders the
component with `{ legislature:"2024", chamber:"senate" }`.

**D6 — wire Traseism's About modal** (`frontend/src/pages/Traseism.tsx`): add a button
next to the methodology link/section using the already-defined key:

```tsx
<button type="button" className="btn btn-hover bg-slate-700 hover:bg-slate-600"
        onClick={() => setAboutOpen(true)}>
  {t("traseismAboutButton")}
</button>
```

`About` is already imported (`:14`) and rendered (`:945`); only the trigger was missing.

**D7 — delete the three inert components:**

```bash
cd /home/nedaktov/parlament-deschis
git rm frontend/src/components/ui/Modal.tsx \
       frontend/src/components/ui/Drawer.tsx \
       frontend/src/components/TimelineStrip.tsx
grep -R "TimelineStrip\|ui/Modal\|ui/Drawer" frontend/src scripts --include='*.ts' --include='*.tsx' --include='*.mjs' || echo "NO_REFERENCES"
# expected: NO_REFERENCES (Footer.tsx:7 mentions LiveFeed only)
```

**CHECKPOINT CP4:**

```bash
node scripts/check_livefeed_props.mjs; echo "exit=$?"
# expected: PASS: LiveFeed props (legislature=2024, chamber=senate) reach queryFn and queryKey
# exit=0
grep -n "setAboutOpen(true)" frontend/src/pages/Traseism.tsx   # expected: 1 match
test ! -e frontend/src/components/TimelineStrip.tsx && echo DELETED_OK
```

---

### Step 5A — Link the 6 orphan routes (default)

Edit `frontend/src/router.tsx`:

1. Add a second nav row inside `<header>` after the existing `<nav>` block (`:246-297`),
   so the primary nav is not lengthened past the viewport:

```tsx
<nav className="flex flex-wrap gap-1 border-b border-slate-700/60 px-4 py-1"
     aria-label={t("nav.analytics", "Vote analytics")}>
  <NavLink to="/compare-mps" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">{t("nav.compareMps", "Compare MPs")}</NavLink>
  <NavLink to="/Voturi"      activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">{t("nav.voturi", "Votes")}</NavLink>
  <NavLink to="/radar"       activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">{t("nav.radar", "Vote radar")}</NavLink>
  <NavLink to="/grafice"     activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">{t("nav.grafice", "Charts")}</NavLink>
  <NavLink to="/topuri"      activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">{t("nav.topuri", "Vote rankings")}</NavLink>
  <NavLink to="/ideology"    activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">{t("nav.ideology", "Ideology")}</NavLink>
</nav>
```

2. Add the 7 new keys (`nav.analytics`, `nav.compareMps`, `nav.voturi`, `nav.radar`,
   `nav.grafice`, `nav.topuri`, `nav.ideology`) to **both** locales in `i18n.ts` using
   the values in the `t()` fallbacks above (ro: "Analiză voturi", "Compară
   parlamentari", "Voturi", "Radar voturi", "Grafice", "Clasamente vot",
   "Ideologie").

3. Extend the document-title `if/else` chain (`:194-211`) so the newly linked routes
   get a real label rather than the generic `t("title")`:

```tsx
else if (path === "/compare-mps") label = t("nav.compareMps");
else if (path === "/Voturi") label = t("nav.voturi");
else if (path === "/radar") label = t("nav.radar");
else if (path === "/grafice") label = t("nav.grafice");
else if (path === "/topuri") label = t("nav.topuri");
else if (path === "/ideology") label = t("nav.ideology");
```

4. Also fix the two raw keys already in that chain: `t("nav.parties", "Parties")` →
   `t("nav.parties")` and `t("senateStatLegislatures")` now resolves because Step 2
   added it (no call-site change needed).

**Keep `/Voturi` capitalised.** Renaming it to `/voturi` requires coordinated edits to
`router.tsx`, `scripts/ui_validate.py:70`, every link and the vault docs — deferred, not
silently changed here.

### Step 5B — ALTERNATIVE: formally deprecate an orphan (use only per-route with D-record)

For each route the parent chooses to deprecate, replace its `component:` with a redirect
and record the reason in `scripts/check_routes_nav.mjs`'s `DEPRECATED_ROUTES` map:

```tsx
const ideologyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/ideology",
  beforeLoad: () => { throw redirect({ to: "/", search: { date: localISODate() } }); },
  validateSearch: validateDateSearch,
});
```

Then remove its lazy import and its `NavLink`, and **remove its row from**
`scripts/ui_validate.py:47-77` (otherwise the UI gate navigates to a redirect and still
passes for the wrong reason — record that explicitly). A deprecated route must keep a
`reason` string in the guard; an unlinked route with no reason is a gate failure.

**CHECKPOINT CP5:**

```bash
node scripts/check_routes_nav.mjs; echo "exit=$?"
# expected (Step 5A): ROUTES total=24 nav_links=22 unlinked=0 deprecated=0
#                     PASS: every route is nav-reachable or formally deprecated
# exit=0
```

Guard source for `scripts/check_routes_nav.mjs`:

```js
#!/usr/bin/env node
/** Every registered route must be nav-reachable, search-reachable, redirect-only, or formally deprecated. */
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "..");
const text = readFileSync(path.join(repo, "frontend/src/router.tsx"), "utf8");
const routes = [...text.matchAll(/path:\s*"([^"]+)"/g)].map((m) => m[1]);
const navTargets = [...text.matchAll(/<NavLink\s+to="([^"]+)"/g)].map((m) => m[1]);
const REACHABLE_OTHERWISE = new Map([
  ["/person/$id", "reachable via global Search (router.tsx:227-231)"],
  ["/electoral", "redirect-only route (router.tsx:322-336)"],
]);
const DEPRECATED_ROUTES = new Map([
  // ["<path>", "<reason + redirect target>"],  // Step 5B entries go here
]);
const normalize = (r) => r.replace(/\/\$[^/]+/g, "");
const linked = routes.filter((r) => {
  const n = normalize(r);
  return navTargets.some((t) => t === n || n === "/" || t.startsWith(`${n}/`));
});
const unlinked = routes.filter((r) => !linked.includes(r)
  && !REACHABLE_OTHERWISE.has(r) && !DEPRECATED_ROUTES.has(r));
console.log(`ROUTES total=${routes.length} nav_links=${navTargets.length} unlinked=${unlinked.length} deprecated=${DEPRECATED_ROUTES.size}`);
for (const r of unlinked) console.log(`  UNLINKED ${r}`);
for (const [r, why] of DEPRECATED_ROUTES) console.log(`  DEPRECATED ${r}: ${why}`);
if (unlinked.length) { console.error("FAIL: routes have no nav link and no deprecation entry"); process.exit(1); }
console.log("PASS: every route is nav-reachable or formally deprecated");
process.exit(0);
```

Baseline (before Step 5A) prints `unlinked=6` and exits 1 — expected red state.
Add both guards to CI in Step 1 (already included in the CI snippet).

---

### Step 6 — Full verification gates

```bash
cd /home/nedaktov/parlament-deschis
# G1: static + type + build
cd frontend && npm run lint && npm run build && npm run i18n:check; cd ..
# G2: Python/lint/test (unchanged product areas must stay green)
uv run ruff check pipeline backend scripts tests
uv run pytest -q
# G3: existing evidence guards
node scripts/check_livefeed_props.mjs
node scripts/check-hook-order.mjs
node scripts/check_i18n_keys.mjs
node scripts/check_routes_nav.mjs
# G4: live UI gate (requires a dev server and the local axe asset)
python3 -c "import playwright; print('playwright OK')"
test -x /usr/bin/chromium && echo "chromium OK"
test -f /tmp/axe.min.js || echo "AXE_MISSING - UI gate cannot pass until provided"
# start dev server (separate terminal): cd frontend && npm run dev -- --port 5174
python3 scripts/ui_validate.py http://127.0.0.1:5174
```

`git status --short` at the end must show only the files in §3 plus the two pre-existing
untracked entries; no `.env`, no lockfile rewrite, no vault changes.

---

## 7. CHECKPOINTS (exact command → expected output → exit)

| CP | When | Command | Expected output (essential lines) | Exit |
| --- | --- | --- | --- | ---: |
| CP0 | Before backup | `git merge-base --is-ancestor HEAD eb693b4 && git diff --quiet HEAD eb693b4 -- frontend/src scripts .github` | no output | 0 |
| CP1 | After Step 1 | `node scripts/check_i18n_keys.mjs` | `MISSING_IN_RO 66`, `MISSING_IN_EN 66`, `FAIL: i18n key diff is not clean` | **1 (intended red)** |
| CP2 | After Step 2b | `node scripts/check_i18n_keys.mjs` | `MISSING_IN_RO 0`, `MISSING_IN_EN 0`, `ASYMMETRIC_DEFINITIONS 0`, `PASS: …` | 0 |
| CP3 | After Step 3 | `cd frontend && npm run lint && npm run build` | tsc+eslint silent; `dist/` built | 0 |
| CP4 | After Step 4 | `node scripts/check_livefeed_props.mjs` | `PASS: LiveFeed props (legislature=2024, chamber=senate) reach queryFn and queryKey` | 0 |
| CP5 | After Step 5A | `node scripts/check_routes_nav.mjs` | `ROUTES total=24 nav_links=29 unlinked=0 deprecated=0` → `PASS: every route…` | 0 |
| CP6 | After Step 6 G2 | `uv run pytest -q` | same pass count as the untouched baseline (no regressions) | 0 |
| CP7 | Final | `node scripts/check_i18n_keys.mjs && node scripts/check_routes_nav.mjs && (cd frontend && npm run lint && npm run build)` | all PASS lines | 0 |
| CP8 | UI (conditional) | `python3 scripts/ui_validate.py http://127.0.0.1:5174` | `UI VALIDATION PASS: 24 routes, 0 JS errors, 0 axe violations` | 0, or **NOT PROVEN** if axe/asset/server unavailable |

`nav_links=22` = 16 existing `NavLink`s (`router.tsx:247-294`) + 6 new analytics
links. Deprecated routes (if Step 5B is used) are counted separately in
`deprecated=`. If the printed number differs, inspect the guard's `normalize()`
output rather than weakening the assertion.

---

## 8. Rollback

```bash
cd /home/nedaktov/parlament-deschis
BK="$(cat /tmp/opencode/R-07-last-backup-path)"
# Verify the backup before using it
( cd "$BK" && sha256sum -c SHA256SUMS )   # expected: all OK

# Full file-level rollback of everything this recipe owns
git checkout -- frontend/src frontend/package.json scripts .github/workflows/ci.yml
git checkout -- $(git diff --cached --name-only --diff-filter=D | grep '^frontend/src/' || true)
git reset HEAD -- frontend/src scripts .github/workflows/ci.yml frontend/package.json
rm -f frontend/src/components/ProvenanceStamp.tsx \
      scripts/check_i18n_keys.mjs scripts/check_routes_nav.mjs

# Partial rollback options
git apply -R "$BK/unstaged.patch"      # restore pre-edit unstaged state, if any
git apply -R "$BK/staged.patch"        # restore pre-edit staged state, if any
tar -tzf "$BK/product.tar.gz" | head   # inspect before any manual restore from tar

# Confirm
git status --short                     # only the two pre-existing untracked entries
node scripts/check_i18n_keys.mjs       # expected: exit 1 (red baseline restored)
```

`git rm`-deleted components are restored by the first `git checkout --` line because
the deletions are staged; verify with `git status --short` that no `D` lines remain.
Never use `git checkout -- .` or `git reset --hard`: that would touch `.nedcode/` and
the vault note the parent session owns.

---

## 9. Backup + checksum (policy)

* Location: `/tmp/opencode/R-07-backup-<UTCstamp>/` (pre-created approved temp root).
* Contents: `unstaged.patch`, `staged.patch`, `product.tar.gz`, `SHA256SUMS`.
* `SHA256SUMS` is generated **inside** the backup dir with relative names so
  `sha256sum -c SHA256SUMS` works from anywhere after `cd "$BK"`.
* The path is persisted to `/tmp/opencode/R-07-last-backup-path`.
* Checksums are **not** copied into this document (they are run-specific); CP0 of the
  rollback section re-verifies them before use.
* No secret values, `.env` files or vault notes are captured in the tar (explicit
  path list in Step 0).

---

## 10. Verification gates (summary)

| Gate | Command | Pass condition | Enforced in CI today? |
| --- | --- | --- | --- |
| i18n key diff | `node scripts/check_i18n_keys.mjs` | 0 missing / 0 asymmetric / 0 duplicate | **After Step 1 wiring** (`.github/workflows/ci.yml` `test` job) |
| Route/nav reachability | `node scripts/check_routes_nav.mjs` | 0 unlinked without deprecation | **After Step 1 wiring** |
| Typecheck + lint | `cd frontend && npm run lint` | exit 0 | Yes (`ci.yml:36-42`) |
| Build | `cd frontend && npm run build` | exit 0 | Yes (`ci.yml:36-42`) |
| Python lint/tests | `uv run ruff check … && uv run pytest -q` | no regressions | Yes (`ci.yml:30-35`) |
| LiveFeed props regression | `node scripts/check_livefeed_props.mjs` | PASS line, exit 0 | Yes (`ci.yml:95-105`) |
| Hook-order regression | `node scripts/check-hook-order.mjs` | existing metric unchanged | Local checkpoint (not currently in CI) |
| UI (browser + axe) | `python3 scripts/ui_validate.py …` | `UI VALIDATION PASS: 24 routes…` | **Probe-only** in CI (`ci.yml:106-122`); runner lacks chromium per probe |

---

## 11. Acceptance criteria

- [ ] `node scripts/check_i18n_keys.mjs` prints `MISSING_IN_RO 0`, `MISSING_IN_EN 0`,
      `ASYMMETRIC_DEFINITIONS 0`, `DUPLICATE_DEFINITIONS 0` and exits 0.
- [ ] All 69 audited keys resolve in both locales; `nav.parties` and
      `senateStatLegislatures` no longer render as raw keys (verified by gate + code review).
- [ ] `prov.confidence`/`precision`/`snapshot`/`note` exist in both locales and all
      8 edited pages import/use `ProvenanceStamp` (or are explicitly marked no-change:
      Traseism, SenateHistory).
- [ ] Provenance appears on Committees member rows, PartyProfile movements,
      PersonDeepDive events + committee service, CoverageView rows, PartyTimeline gap
      panel, Ideology meta footer, Voturi vote detail — **only where the field is supplied**.
- [ ] `PartyMovementResponse` includes the four fields `serialize_event` already returns.
- [ ] `node scripts/check_routes_nav.mjs` exits 0 with `unlinked=0`; every deprecation
      (if any) carries a written reason and a matching `ui_validate.py` edit.
- [ ] `LiveFeed` is reachable from `/` and the LiveFeed props guard still passes;
      Traseism's About button calls `setAboutOpen(true)` at least once.
- [ ] `ui/Modal.tsx`, `ui/Drawer.tsx`, `TimelineStrip.tsx` are gone and no references remain.
- [ ] `npm run lint`, `npm run build`, `uv run pytest -q` green with no new skips.
- [ ] Backup+checksum exists and rollback was verified (checksum `-c` OK) before sign-off.
- [ ] This recipe's §5 decisions are copied unchanged into the implementation PR/ADR;
      no silent substitution of "delete" for "wire" or vice versa.

---

## 12. Dependencies

* **Parent session / sibling agents:** R-07 consumes audit docs only. X1 (count labels),
  X2 (`useAsOf`), X3 (state system), X7 (chart/a11y), X8 (vision proxies) are other
  recipes — do not absorb their edits here. D3's optional backend step must not be
  applied by an agent that owns a backend/recipes conflict without a new decision row.
* **CI:** `.github/workflows/ci.yml` must remain the single source of truth; no shadow
  workflow files. Adding the two Node steps to the existing `test` job is sufficient;
  they need no npm install (zero deps).
* **Tooling:** Node ≥18 (observed v24.22.3), `frontend/node_modules` via `npm ci`,
  `uv` for Python gates, `playwright` + `/usr/bin/chromium` + `/tmp/axe.min.js` for CP8.
  `/tmp/i18n-extract.mjs` referenced by the parent session **does not exist** on this
  machine; the equivalent extraction is embedded in Step 1's gate.
* **Upstream data:** no dataset release change is required; provenance fields are
  already in the API contract (§2.2). Step 3B would touch `pipeline/traseism.py`.

---

## 13. Side-quest policy

Authorised side effects are only those needed to make §6 compile and pass. Explicitly
**forbidden** in this recipe:

* Visual/design-system fixes (AP-1…AP-8, X7): HeroGraphic colours, DataBar paint,
  ProgressRing, `.wrap`, contrast, motion — another recipe owns them.
* X1/X2/X3: relabelling headline counts, `useAsOf()`, loading/error/empty gating.
  Where a provenance edit touches a stat card, leave the number logic untouched.
* X8: coalition stability honesty, bureau placeholder, PopuList claim — except the
  narrowly scoped Ideology "not yet ingested" guard in Step 3b(6), which is required
  so provenance is not printed under a false empty-state message.
* Backend/DB/pipeline changes except the gated Step 3B.
* Vault regeneration (`scripts/vault_sync.py`), lockfile updates, dependency bumps,
  commits, or touching `.nedcode/`.
* "Fixing" the capital `/Voturi` path or the duplicate-looking `mpsTotalMps` entries
  (they are distinct keys: `mpcTotalMps` vs `mpsTotalMps`).

If a step cannot be completed because of an out-of-scope defect, **stop at the next
checkpoint and report it as blocked** — do not widen the file list.

---

## 14. NOT PROVEN (must be stated in the implementation PR)

1. **No browser render, axe scan, contrast measurement, 320 px reflow or touch test was
   performed by this recipe agent.** CP8 is conditional on a local dev server, Playwright,
  Chromium and `/tmp/axe.min.js`; on this machine the first two are present and
  `/tmp/axe.min.js` is **missing** (verified), so the UI gate cannot pass until that
  asset is supplied. CI deliberately only probes for it (`ci.yml:106-122`).
2. Static type/serializer evidence proves the API *contract* supplies provenance; it
   does **not** prove the live production payload contains non-null values for every
   row. Verify with `curl /api/coverage/detailed`, `/api/committees/<id>/members`,
   `/api/persons/<id>`, `/api/party/<short>/movements` against the deployment before
   claiming "provenance visible".
3. The 69-key list comes from a regex extraction of literal `t("…")` call sites plus a
   hand-reviewed dynamic allowlist. A truly dynamic key constructed outside the
   allowlisted sites would evade the gate; the allowlist must be reviewed at each audit.
4. Romanian translations in §Step 2 are authored, not native-speaker reviewed; English
   fallbacks are taken verbatim from the source call sites. A language review is still
   required before claiming the app is "bilingual Romanian-first".
5. Wiring `LiveFeed` and the 6 orphan nav links is expected to improve reachability, but
   no usage/analytics data proves users want those routes; the decision is an audit-driven
   presentation fix, not a measured UX outcome.
6. Deleting `ui/Modal`, `ui/Drawer`, `TimelineStrip` is based on static grep (zero
   importers) and CI-guard inspection. A runtime plugin or future dynamic import outside
   `frontend/src` is not covered by that search.
7. `check_routes_nav.mjs`'s `normalize()` treats `/legislature/2024` as satisfying
   `/legislature/$year`. If a future route uses a different param shape, review the
   normaliser rather than adding an allowlist entry blindly.
8. Step 3B (traseism ledger provenance) is **not applied by default**; its tests and
   import-cycle avoidance are designed but unexecuted. Do not claim the ledger shows
   confidence/snapshot unless that step is explicitly applied and CP6 repeated.
9. The declared parent baseline `eb693b4` was not the observed `HEAD` (`80d91a9`) at
   authoring time; the two are ancestor-related and product files are identical, but the
   implementer must re-run CP0 before relying on the line numbers in §2.

---

## 15. Report line for the parent session

`docs/repair-recipes/R-07-provenance-i18n-nav.md` — designed (not implemented):
provenance component + 9-page render map (backend fields already present; ledger
confidence/snapshot deferred), 69-key ro/en gap table (132 insertions) with a
zero-dependency key-diff CI gate, 6-route nav/deprecation decision with a route guard,
and wire/delete decisions for all 5 dead components; every step carries a checkpoint,
backup/checksum, rollback and NOT PROVEN section. No product file was edited.
