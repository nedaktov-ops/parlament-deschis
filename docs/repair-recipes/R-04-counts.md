# R-04 — Count / definition honesty & no null→0

**Status:** strategy + implementation-ready recipe (NOT implementation).
**Author role:** STRATEGY/RECIPE AGENT R-04 (read-only on product code).
**Written:** 2026-11-21.
**Brief baseline:** main `eb693b4`.
**Verified baseline:** `eb693b4` = `origin/main` (merge PR #69, 2026-11-21 19:40:49 +0200). Local `HEAD` = `80d91a9` on branch `docs/triad-audit`; `git rev-parse eb693b4^{tree} HEAD^{tree}` returns the **same tree** `02ac065d7…` and `git diff --quiet eb693b4 HEAD` exits `0`. All `path:line` citations below are therefore against the intended baseline content even though the local branch pointer differs. **Do not "fix" this by checking out a different commit** — see Preconditions P0.

---

## 1. Objective

Establish a single source of truth for what every headline number in this project means, so that:

1. **One canonical labelled switch definition** exists. Both constituent counts are published with explicit labels: **group switches** (`switch_group`) and **party switches** (`switch_party`), plus their disjoint exact sum **all observed affiliation-change events**. Bare "Switches", "Party switches" and "Total MPs" disappear from the UI.
2. **API-level `total` / aggregates back every headline figure.** No page computes a corpus total from a rendered, capped or paginated array (`rows.length`, `top-N` sums, `slice(0,100)`, expanded-card sums).
3. **Null is displayed as "unknown"/"—", never 0.** Any API field that is `null` for "no data / unavailable" stays `null` through the client and renders as `—` (or the localised "unknown" string).
4. **No approximated percentages.** Percentages are computed from raw integer counts at the API, with `null` when the denominator is zero; the UI never back-computes counts from rounded percentages, never invents a percentage from an ordinal state (`partial → 60`), and never does a mean-of-means.
5. **Correct denominators** for demographics, switch-leaderboard loyalty, scorecard rebellion, coverage and derived per-person metrics; each derived percentage carries its denominator name and raw numerator/denominator in the payload.
6. **Per-page label changes** on all affected pages, in both locales (ro + en).

This recipe does **not** fix date/as-of scoping, i18n key gaps unrelated to counts, visual primitives, keyboard access, or the coalition proxy. Those belong to other recipes; see §12 Side-quest policy.

---

## 2. Evidence (path:line)

All citations are static-code evidence from the baseline tree. Runtime/browser claims are NOT PROVEN (§14).

### 2.1 Audit inputs

| Source | Finding | Reference |
| --- | --- | --- |
| `Parlament Deschis Obsidian vault/40-FRONTEND/TRIAD-AUDIT-2026-11-21.md:64` | FN-2: ≥3 incompatible switch definitions under one label | group-only `traseism.py:39`, leaderboard, exports; group+party `api.py:1061-1066`; dated joins "Total switches" (PartyTimeline); merged group+party under "Group switches" (PersonDeepDive) |
| same `:65` | FN-3: page-local slices labelled corpus totals | Mps 60-row, MpComparison 200-row, SwitchLeaderboard top-N sums, Topuri 100-row cap, CoverageView overall % from rounded %, committee-card sums, all-chamber count as "Senate Members" |
| same `:66` | FN-4: null→0 and fabricated values | PartyProfile missing switch data → 0, PartyComparison unavailable chairs → 0, CoverageView null `dated_pct` → 0, Report `"partial"` → fabricated 60% ring, Ideology null CHES → `0.00`, Topuri rebellion counts abstain/not-voting |
| same `:71` | FN-9: mislabelled headline metrics | Report "Party switches"=group-only, "deputies in corpus"=all persons, SenateHistory "%" is a count, Demographics "Total MPs"=birth-dated only + mean-of-means + 100% coverage by construction |
| same `:80` | Enhancement 3: "One canonical switch definition — return both counts with labels from the backend; ... use API `total`/aggregates, never rendered arrays, for headline figures." | — |
| `…/FRONTEND-AUDIT-2026-11-21.md:39` | X1: unlabelled/mislabelled counts (1,217 vs 2,002 vs 60/200 vs 3,388 vs 5,282) | LiveDashboard A04, Traseism A2, Mps 1, MpComparison A01, SenateHistory S1, Report A2, LegislatureDetail LD-2, Grafice G5 |
| same `:94-96` | Recommended order #1: label every count and denominator; derive totals from API `total` | — |
| `docs/AUDIT-RESOLUTIONS-2026-11-21.md:26` | R1: 2,002 vs 1,217 is **definitional, not a defect**; residual = UI/docs do not label the definitions | `switch_group=1217`, `switch_party=785` in pinned release; local DBs have `switch_party=0` |
| same `:27` | R2: 7,358 raw asset vs 7,349 prepared runtime DB; current truth = 7,349 | — |
| `docs/API.md:404-454` | Count definitions section already states the labels; implementation must make code match | `api.py:1047-1049`, `exports.py:72` |

### 2.2 Backend evidence

| Location | Defect |
| --- | --- |
| `backend/routers/api.py:1060-1066` | `/dashboard/stats` `switches` counts both types; **no label, no split** |
| `backend/routers/api.py:1091-1097` | `coverage_score` = rounded share of coverage rows; denominator unnamed |
| `backend/routers/api.py:277-375` | `/mps` returns `status/data/offset/limit`, **no `total`** (line 375) |
| `backend/routers/exports.py:68-82` | report `totals.switches` = group-only (`:72`), unlabelled |
| `backend/queries.py:694-705, 733-744` | coverage `dated_pct`/`sourced_pct` are `null` when denominator 0 (correct) but there is **no corpus-level aggregate** |
| `backend/routers/api.py:1684-1827` | leaderboard loyalty: `tenure_weight = min(1, tenure_years/4)`; single switch + zero observed span → `loyalty=100` (`:1794-1800`); no denominator labelled |
| `backend/routers/api.py:1455-1526` | scorecard: `else: rebel_votes += 1` at `:1498-1499` counts abstain/not-voting as rebellion; pcts coerce to `0` when denominator 0 (`:1521-1525`) |
| `backend/routers/api.py:1562-1632` | ideology already returns `null` fields honestly — backend is correct, frontend fabricates |
| `pipeline/traseism.py:38-44, 185-212` | group-only definition, no explicit `definitions` field in payload |
| `pipeline/analytics.py:354-415` | `generational_shift` uses `Person.birth_date.is_not(None)` (`:380`) so "Total MPs" excludes unknown birth dates; per-party mean is not population mean (`:404-413`) |
| `pipeline/analytics.py:435-514` | `derive_committee_control` returns `share_pct`, denominator = chairs; `"unknown"` party bucket at `:487` |
| `backend/queries.py:798-842` | party profile already returns `null` switch fields when no dated data — backend is correct, frontend coerces |

### 2.3 Frontend evidence

| Location | Defect |
| --- | --- |
| `frontend/src/api/client.ts:124-134` | `DashboardStats` has only bare `switches`, `coverage_score` |
| `frontend/src/api/client.ts:245-275` | `MpsResponse` interfaces lack `total`; `:735-742` `PartyListEntry` has only `switches_in` |
| `frontend/src/api/client.ts:673-688, 706-717, 884-907` | leaderboard/generational/scorecard types lack denominator metadata; pcts typed `number` (not nullable) |
| `frontend/src/pages/LiveDashboard.tsx:119-126` | card title `"Switches"`, value `stats?.switches` (2,002) unlabelled |
| `frontend/src/pages/Traseism.tsx:740, 764, 852-865` | `scope.switches` labelled "total switches in corpus" but is group-only |
| `frontend/src/pages/SwitchLeaderboard.tsx:40-42, 66-67, 184-196, 233-234` | hero = top-N sum; methodology claims "100 means no observed switch" while 1-switch MPs score 100 |
| `frontend/src/pages/Mps.tsx:64-66, 84-107` | `value={rows.length}` (60) labelled "Total MPs"; `canNext = rows.length === PAGE_SIZE` |
| `frontend/src/pages/MpComparison.tsx:96-103, 157-158` | 200-row pool labelled "Total MPs" |
| `frontend/src/pages/SenateHistory.tsx:66-85` | all-chamber `persons` sum labelled "Senate Members"; "Full Coverage %" renders an integer count |
| `frontend/src/pages/Report.tsx:94-95, 255-258, 266-269` | `completenessValue("partial") = 60` fabricated ring; "Party switches"=group-only; "deputies in corpus"=all persons |
| `frontend/src/pages/Report.tsx:451-454` | uses the fabricated 60 ring in the coverage table |
| `frontend/src/pages/CoverageView.tsx:34-52, 63-66, 127-130` | `?? 0` coerces null pcts; `overallPct` reconstructed from rounded per-row pcts |
| `frontend/src/pages/Demographics.tsx:34, 43-60, 90-94` | `totalMPs = birthDated`; mean-of-means at `:44-48`; `coveragePct` = parties-with-data / parties (100% by construction) |
| `frontend/src/pages/Ideology.tsx:76-85, 118-122` | `d.lrgen ?? 0`, `d.galtan ?? 0`, `d.eu_position ?? 0` fabricate plotted points and tooltip values |
| `frontend/src/pages/Topuri.tsx:79-81, 146-154` | `{entries.length} MPs shown` hides API `total`; pcts rendered with `%` with no denominator; null would render `%` after coercion upstream |
| `frontend/src/pages/PartyProfile.tsx:78, 119-122` | `(p.switches_in ?? 0) + (p.switches_out ?? 0)` fabricates 0 from backend `null` |
| `frontend/src/pages/PartyComparison.tsx:104-107` | unavailable chairs render literal `"0"` instead of `—` |
| `frontend/src/pages/PartyTimeline.tsx:119-124` | dated joins labelled "Total switches" |
| `frontend/src/pages/PersonDeepDive.tsx:96-99, 122-125` | merges group+party events under `personStatSwitches` "Group switches" |
| `frontend/src/pages/Committees.tsx:188-196, 241-244` | "Total members" sums only expanded committee cards |
| `frontend/src/pages/LegislatureDetail.tsx:80-83` | group-only filter on a 1,000-row movements array labelled "Switches" |
| `frontend/src/pages/Grafice.tsx:144-148` | group-only summary labelled "Switches" |
| `frontend/src/pages/Parties.tsx:103, 135` | "Switches in" = group-only, unlabelled |
| `frontend/src/i18n.ts` (both `ro` and `en` blocks) | keys `dashboardStatSwitches`, `report.switches`, `mpsTotalMps`, `leaderboard.methodology.loyalty`, etc. encode the wrong definitions |

### 2.4 Measured local baseline (command output, 2026-11-21)

```
TestClient GET /api/dashboard/stats  → persons=3388 memberships=7349 switches=1217 committees=26
TestClient GET /api/health           → memberships=7349
TestClient GET /api/export/report    → totals.switches=1217 (group only)
SQL count Event.type: switch_group=1217, switch_party=0  (data/parlament-real.db)
```

**Critical:** the **local** DB has `switch_party=0`. The **1,217 / 785 / 2,002** triple is a *pinned-release* fact (R1). After this recipe, the local probe must show `1217 / 0 / 1217` and the release probe `1217 / 785 / 2002`. A probe that hard-codes 2,002 against the local DB is itself a false claim. Both triples satisfy the invariant `group + party == all`.

Baseline gates observed before any edit:
```
.venv/bin/python -m pytest tests/test_api.py tests/test_traseism.py \
  tests/test_export_report.py tests/test_analytics_transparency.py -q
→ 63 passed, 1 warning, exit 0
.venv/bin/ruff check .                       → All checks passed!, exit 0
cd frontend && npm run build                 → ✓ built in ~16s, exit 0 (chunk-size warning only)
.venv/bin/python scripts/ui_validate.py --help → ModuleNotFoundError: playwright  (see §8.4)
```

---

## 3. Exclusive file list

The implementer may modify **only** these files. Anything not listed is out of scope for R-04 and must be left untouched.

**Backend / pipeline**
1. `backend/routers/api.py`
2. `backend/routers/exports.py`
3. `pipeline/analytics.py`
4. `pipeline/traseism.py`

**Frontend**
5. `frontend/src/api/client.ts`
6. `frontend/src/i18n.ts`
7. `frontend/src/pages/LiveDashboard.tsx`
8. `frontend/src/pages/Traseism.tsx`
9. `frontend/src/pages/SwitchLeaderboard.tsx`
10. `frontend/src/pages/Mps.tsx`
11. `frontend/src/pages/MpComparison.tsx`
12. `frontend/src/pages/SenateHistory.tsx`
13. `frontend/src/pages/Report.tsx`
14. `frontend/src/pages/LegislatureDetail.tsx`
15. `frontend/src/pages/Grafice.tsx`
16. `frontend/src/pages/Parties.tsx`
17. `frontend/src/pages/PartyProfile.tsx`
18. `frontend/src/pages/PartyTimeline.tsx`
19. `frontend/src/pages/PersonDeepDive.tsx`
20. `frontend/src/pages/PartyComparison.tsx`
21. `frontend/src/pages/CoverageView.tsx`
22. `frontend/src/pages/Demographics.tsx`
23. `frontend/src/pages/Topuri.tsx`
24. `frontend/src/pages/Ideology.tsx`
25. `frontend/src/pages/Committees.tsx`

**Tests (additive / signature updates only)**
26. `tests/test_api.py`
27. `tests/test_analytics.py`
28. `tests/test_export_report.py`
29. `tests/test_analytics_transparency.py`
30. `tests/test_count_definitions.py` (new — preferred home for R-04 regression tests)

**Docs**
31. `docs/API.md`
32. `docs/repair-recipes/R-04-counts.md` (this file; status/checkpoint notes only, never product code)

Explicitly **forbidden**: `backend/queries.py`, `backend/graphql/schema.py`, `pipeline/export.py`, `backend/config.py`, `pipeline/db.py`, `frontend/src/router.tsx`, `frontend/src/components/*`, `data/*`, any CI/workflow file, any vault file. If a step appears to require one of these, **stop and report a blocker** (§12).

---

## 4. Preconditions

| ID | Precondition | Verify with | Exit |
| --- | --- | --- | --- |
| P0 | Baseline tree matches the brief. `eb693b4` is a commit in this clone and its tree equals local `HEAD`'s tree. | `git cat-file -t eb693b4 && git diff --quiet eb693b4 HEAD; echo $?` | prints `commit`, `0` |
| P1 | Working tree clean for the exclusive file list (only this recipe doc and pre-existing untracked `.nedcode/` + vault backlink may be present). | `git status --short` | no tracked modifications to files in §3 |
| P2 | Python env and linter present. | `.venv/bin/python -V && .venv/bin/ruff --version` | `Python 3.12.x`, `ruff 0.x` |
| P3 | Node deps installed. | `test -d frontend/node_modules && echo ok` | `ok` |
| P4 | Baseline gates green (outputs in §2.4). | commands in §2.4 | all exit `0` |
| P5 | DB is **read-only** for this work. Nothing in R-04 writes to `data/*.db`. | `git status --short data/` | empty |
| P6 | Owner decision recorded: switch definitions are **definitional, not a data bug** (R1). Do not "fix" 1,217 → 2,002 or dedupe/merge event types. | this document §5 | — |
| P7 | UI gate tooling is available *before* claiming UI verification. Local `.venv` lacks playwright (§2.4). Install/use system python3 with playwright + Chromium, or record NOT PROVEN. | `python3 -c 'import playwright; print("ok")'` | `ok` or explicit NOT PROVEN |
| P8 | A local API can be started on a free port for probes. | `ss -ltn \| grep -q ':8017' \|\| echo free` | `free` |

If P0 fails, **stop**: do not rebase or checkout; report the mismatch to the orchestrator with both commit IDs.

---

## 5. Canonical definition contract (the single source of truth)

This table is authoritative. Every payload field and every label added below must match it verbatim.

| Canonical field | Label (en) | Label (ro) | Definition | Pinned-release value | Local-DB value |
| --- | --- | --- | --- | ---: | ---: |
| `switches_group` | Group switches | Schimbări de grup | `Event.type == "switch_group"`: same person changes parliamentary group within the **same chamber and same legislature**, prior tenure has a published leave date, next tenure starts on/after it (`pipeline/traseism.py:3-7,38-44`) | 1,217 | 1,217 |
| `switches_party` | Party switches | Schimbări de partid | `Event.type == "switch_party"`: change of the party behind the group; unaffiliated bucket skipped, so `PSD→unaffiliated→PRO` is one switch (`pipeline/traseism.py:296-301,340-401`) | 785 | 0 |
| `switches_all` | All observed affiliation changes | Toate schimbările observate de afiliere | Exact sum of the two disjoint event types; never an estimate | 2,002 | 1,217 |
| `memberships` | Memberships (prepared corpus) | Mandate (corpus preparat) | All `Membership` rows served at runtime after `prepare_db.py` dedupe | 7,349 | 7,349 |
| `memberships_raw_asset` | Memberships (raw release asset) | Mandate (fișier brut) | Same corpus before dedupe; historical/asset figure only | 7,358 | n/a |
| `persons` | Persons in corpus | Persoane în corpus | All `Person` rows; **not** "deputies" | 3,388 | 3,388 |
| `mps_total` | MPs matching query (corpus-wide) | Parlamentari care corespund căutării | `/api/mps` `total`, independent of `offset`/`limit` | 3,388 | 3,388 |
| `dated_pct` | Members with a start date | Membri cu dată de început | `null` when `total_memberships == 0`; computed from raw integer counts | — | — |
| `coverage_pct` (demographics) | MPs with known birth date | Parlamentari cu dată de naștere cunoscută | `mps_with_birth_date / mps_in_scope`; `null` when denominator 0. **Never** parties-with-data / parties | — | — |
| `loyalty_score` | Loyalty proxy | Indicator de loialitate | `100 × (1 − switches/total_events × min(1, tenure_years/4))`, clipped to [0,100]; `null` when no observed event span; capped `<100` whenever ≥1 switch observed. Denominator = observed events **in the reported scope** | — | — |
| `rebellion_pct` | Rebellion (yes/no positions against party majority) | Rebeliune (poziții da/nu contra majorității partidului) | `no_against_majority / alignment_denominator`; `alignment_denominator` includes only positions with a group majority and choice `yes`/`no`. Abstain/not-voting excluded. `null` when denominator 0 | — | — |
| `participation_pct` | Participation | Participare | `positions_cast / votes_in_scope`; `null` when denominator 0 | — | — |

**Naming rule for the UI:** a number is always rendered with its canonical label. Never "Switches", never "Party switches" for `switches_group`, never "Total MPs" for a page-local array length or a birth-dated subset, never "Full Coverage %" for an integer count.

---

## 6. Backup + checksum

Run once before the first edit. Record the output in the implementation PR.

```bash
cd /home/nedaktov/parlament-deschis
BACKUP=/tmp/opencode/R-04-$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$BACKUP"
cat > "$BACKUP/file-list.txt" <<'EOF'
backend/routers/api.py
backend/routers/exports.py
pipeline/analytics.py
pipeline/traseism.py
frontend/src/api/client.ts
frontend/src/i18n.ts
frontend/src/pages/LiveDashboard.tsx
frontend/src/pages/Traseism.tsx
frontend/src/pages/SwitchLeaderboard.tsx
frontend/src/pages/Mps.tsx
frontend/src/pages/MpComparison.tsx
frontend/src/pages/SenateHistory.tsx
frontend/src/pages/Report.tsx
frontend/src/pages/LegislatureDetail.tsx
frontend/src/pages/Grafice.tsx
frontend/src/pages/Parties.tsx
frontend/src/pages/PartyProfile.tsx
frontend/src/pages/PartyTimeline.tsx
frontend/src/pages/PersonDeepDive.tsx
frontend/src/pages/PartyComparison.tsx
frontend/src/pages/CoverageView.tsx
frontend/src/pages/Demographics.tsx
frontend/src/pages/Topuri.tsx
frontend/src/pages/Ideology.tsx
frontend/src/pages/Committees.tsx
tests/test_api.py
tests/test_analytics.py
tests/test_export_report.py
tests/test_analytics_transparency.py
docs/API.md
EOF
while read -r f; do
  mkdir -p "$BACKUP/$(dirname "$f")"
  cp -p "$f" "$BACKUP/$f"
done < "$BACKUP/file-list.txt"
( cd "$BACKUP" && find . -type f -not -name file-list.txt -print0 | sort -z | xargs -0 sha256sum ) > "$BACKUP/SHA256SUMS"
echo "BACKUP=$BACKUP"
sha256sum "$BACKUP/SHA256SUMS"
```

**CHECKPOINT B0**
```bash
test -s "$BACKUP/SHA256SUMS" && wc -l "$BACKUP/SHA256SUMS"
```
Expected: `30 $BACKUP/SHA256SUMS` (one checksum per backed-up file), exit `0`.

To verify the backup later:
```bash
( cd "$BACKUP" && sha256sum -c SHA256SUMS )
```
Expected: every line `OK`, exit `0`.

---

## 7. Implementation steps

Each step uses a deterministic Python replacement so the exact old text is asserted before writing. If `assert count == 1` fails, **stop** — the baseline has drifted; re-check §4 P0 and the cited lines.

### Step 1 — `/api/dashboard/stats`: publish both switch counts with definitions

**File:** `backend/routers/api.py`

**1a.** Replace the switch-count block (`:1060-1066`):

```bash
cd /home/nedaktov/parlament-deschis
.venv/bin/python - <<'PY'
from pathlib import Path
p = Path("backend/routers/api.py"); s = p.read_text()
old = '''    # Get total switch events
    total_switches = (
        db.scalar(
            select(func.count(Event.id)).where(Event.type.in_(["switch_group", "switch_party"]))
        )
        or 0
    )
'''
new = '''    # R-04: publish both switch definitions separately. The two event types
    # are disjoint, so their sum is exact — never an approximation. Keep
    # ``switches`` as a deprecated alias of ``switches_all`` for old clients.
    switch_group = (
        db.scalar(select(func.count(Event.id)).where(Event.type == "switch_group")) or 0
    )
    switch_party = (
        db.scalar(select(func.count(Event.id)).where(Event.type == "switch_party")) or 0
    )
    total_switches = switch_group + switch_party
'''
assert s.count(old) == 1, s.count(old)
p.write_text(s.replace(old, new))
PY
```

**1b.** Replace the coverage-score block (`:1091-1097`) with raw counts + labelled score:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
p = Path("backend/routers/api.py"); s = p.read_text()
old = '''    # Get coverage completeness score
    coverage_scores = db.scalars(select(Coverage.completeness)).all()
    if coverage_scores:
        full_count = sum(1 for s in coverage_scores if s == "full")
        completeness_score = round((full_count / len(coverage_scores)) * 100)
    else:
        completeness_score = 0
'''
new = '''    # R-04: expose the denominator. The score is an exact share of coverage
    # ROWS, not a share of memberships/events, and is null when there are no rows.
    coverage_scores = db.scalars(select(Coverage.completeness)).all()
    coverage_rows_total = len(coverage_scores)
    coverage_full_rows = sum(1 for s in coverage_scores if s == "full")
    completeness_score = (
        round((coverage_full_rows / coverage_rows_total) * 100) if coverage_rows_total else None
    )
'''
assert s.count(old) == 1, s.count(old)
p.write_text(s.replace(old, new))
PY
```

**1c.** Extend the returned `data` dict (`:1099-1112`):

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
p = Path("backend/routers/api.py"); s = p.read_text()
old = '''            "switches": total_switches,
            "committees": total_committees,'''
new = '''            "switches": total_switches,  # deprecated alias of switches_all
            "switches_all": total_switches,
            "switches_group": switch_group,
            "switches_party": switch_party,
            "committees": total_committees,'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
old2 = '''            "coverage_score": completeness_score,
            "computed_at": datetime.now(UTC).isoformat(),'''
new2 = '''            "coverage_score": completeness_score,
            "coverage_full_rows": coverage_full_rows,
            "coverage_rows_total": coverage_rows_total,
            "computed_at": datetime.now(UTC).isoformat(),
            "definitions": {
                "switches_group": "Observed parliamentary-group changes within the same chamber and legislature (Event.type='switch_group').",
                "switches_party": "Observed changes of the party behind the group, unaffiliated bucket skipped (Event.type='switch_party').",
                "switches_all": "switches_group + switches_party; disjoint event types, exact sum. Previously published bare as 'switches'.",
                "memberships": "All Membership rows in the prepared runtime corpus (7,349); the raw release asset has 7,358 before dedupe.",
                "coverage_score": "Share of coverage ROWS with completeness='full'; null when there are no rows.",
            },'''
assert s.count(old2) == 1, s.count(old2)
p.write_text(s.replace(old2, new2))
PY
```

**CHECKPOINT 1**
```bash
.venv/bin/ruff check backend/routers/api.py && .venv/bin/python -m pytest tests/test_api.py -q -k "dashboard or health"
```
Expected: `All checks passed!`; pytest `N passed, 0 failed` (was `1 passed` for `test_dashboard_stats_rejects_invalid_as_of`), exit `0`.

---

### Step 2 — `/api/export/report`: label group-only switches

**File:** `backend/routers/exports.py`

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
p = Path("backend/routers/exports.py"); s = p.read_text()
old = '''    totals = {
        "persons": db.scalar(select(func.count(Person.id))) or 0,
        "memberships": db.scalar(select(func.count(Membership.id))) or 0,
        "events": db.scalar(select(func.count(Event.id))) or 0,
        "switches": db.scalar(select(func.count(Event.id)).where(Event.type == "switch_group"))
        or 0,
'''
new = '''    # R-04: this report has always counted group switches only (docs/API.md
    # count definitions, resolution R1). Publish that definition explicitly
    # and add the party count so the dashboard's all-events total is derivable
    # without changing the meaning of any existing field.
    switches_group = (
        db.scalar(select(func.count(Event.id)).where(Event.type == "switch_group")) or 0
    )
    switches_party = (
        db.scalar(select(func.count(Event.id)).where(Event.type == "switch_party")) or 0
    )
    totals = {
        "persons": db.scalar(select(func.count(Person.id))) or 0,
        "memberships": db.scalar(select(func.count(Membership.id))) or 0,
        "events": db.scalar(select(func.count(Event.id))) or 0,
        "switches": switches_group,  # deprecated alias of switches_group
        "switches_group": switches_group,
        "switches_party": switches_party,
        "switches_all": switches_group + switches_party,
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
old2 = '''        "report": "parlament-deschis transparency report",
        "scope": "all",
        "totals": totals,'''
new2 = '''        "report": "parlament-deschis transparency report",
        "scope": "all",
        "definitions": {
            "switches": "Group switches only (Event.type='switch_group'); legacy field name.",
            "switches_all": "Exact sum of group and party switch events; equals /api/dashboard/stats switches_all for the same corpus.",
            "persons": "All Person rows in the corpus, not 'deputies currently serving'.",
            "memberships": "Prepared runtime corpus (7,349); raw release asset is 7,358.",
        },
        "totals": totals,'''
assert s.count(old2) == 1, s.count(old2)
p.write_text(s.replace(old2, new2))
PY
```

**CHECKPOINT 2**
```bash
.venv/bin/ruff check backend/routers/exports.py && .venv/bin/python -m pytest tests/test_export_report.py -q
```
Expected: `All checks passed!`; all report tests pass (existing `_unfiltered_totals` compares the **subset** of keys it constructs, so adding keys is safe — verify with output), exit `0`.

---

### Step 3 — `/api/mps`: publish the corpus `total`

**File:** `backend/routers/api.py`

**3a.** Insert the count after `base` is built (immediately after the `if q: base = ...` line, before the subqueries):

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
p = Path("backend/routers/api.py"); s = p.read_text()
old = '''    base = select(Person.id, Person.canonical_name, Person.birth_date)
    if q:
        base = base.where(Person.normalized_name.like(f"%{q.lower()}%"))
'''
new = '''    base = select(Person.id, Person.canonical_name, Person.birth_date)
    if q:
        base = base.where(Person.normalized_name.like(f"%{q.lower()}%"))
    # R-04: corpus-wide denominator, independent of offset/limit. A 60-row
    # page is a page, not a total.
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
old2 = '''    return {"status": "ok", "data": cards, "offset": offset, "limit": limit}
'''
new2 = '''    return {
        "status": "ok",
        "data": cards,
        "total": total,
        "offset": offset,
        "limit": limit,
        "definition": "total = persons matching q across the whole corpus, independent of offset/limit.",
    }
'''
assert s.count(old2) == 1, s.count(old2)
p.write_text(s.replace(old2, new2))
PY
```

**CHECKPOINT 3**
```bash
.venv/bin/python -m pytest tests/test_api.py -q -k "mps or persons" && .venv/bin/ruff check backend/routers/api.py
```
Expected: all selected tests pass, `All checks passed!`, exit `0`.

---

### Step 4 — Add `/api/coverage/summary` with raw counts and honest denominators

**File:** `backend/routers/api.py` — insert after the `/coverage/dimensions` handler (currently ends at `:441`).

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
p = Path("backend/routers/api.py"); s = p.read_text()
anchor = '''    from pipeline.coverage import coverage_dimensions as _coverage_dimensions

    return _coverage_dimensions(db)
'''
addition = anchor + '''

@router.get("/coverage/summary")
def coverage_summary(db: Session = Depends(get_db)):
    """Corpus-wide coverage aggregates from raw counts, never rounded pcts.

    A percentage is ``null`` when its denominator is zero. This endpoint is
    additive: ``/coverage/detailed`` keeps its list shape for existing clients.
    """
    from sqlalchemy import and_, case, func, select

    from pipeline.db import Event, Membership, Organization
    from pipeline.queries import is_group

    mem = db.execute(
        select(
            func.count(Membership.id),
            func.sum(case((Membership.start_date.is_not(None), 1), else_=0)),
            func.sum(case((Membership.source_url.is_not(None), 1), else_=0)),
        )
        .join(Organization, Organization.id == Membership.org_id)
        .where(is_group())
    ).one()
    memberships = int(mem[0] or 0)
    dated = int(mem[1] or 0)
    sourced = int(mem[2] or 0)

    is_switch = Event.type.in_(("switch_group", "switch_party"))
    ev = db.execute(
        select(
            func.sum(case((Event.type == "switch_group", 1), else_=0)),
            func.sum(case((Event.type == "switch_party", 1), else_=0)),
            func.sum(case((is_switch, 1), else_=0)),
            func.sum(case((and_(is_switch, Event.source_url.is_not(None)), 1), else_=0)),
        )
    ).one()
    group = int(ev[0] or 0)
    party = int(ev[1] or 0)
    all_switches = int(ev[2] or 0)
    switches_sourced = int(ev[3] or 0)
    assert all_switches == group + party  # disjoint event types; fail loudly

    def pct(numerator: int, denominator: int) -> float | None:
        return round(100 * numerator / denominator, 1) if denominator else None

    return {
        "status": "ok",
        "totals": {
            "memberships": memberships,
            "memberships_dated": dated,
            "memberships_sourced": sourced,
            "switches_group": group,
            "switches_party": party,
            "switches_all": all_switches,
            "switches_sourced": switches_sourced,
        },
        "percentages": {
            "dated": pct(dated, memberships),
            "sourced": pct(sourced, memberships),
            "switches_sourced": pct(switches_sourced, all_switches),
        },
        "definitions": {
            "memberships_dated": "Group membership rows with a published start_date.",
            "dated": "memberships_dated / memberships; null when memberships == 0.",
            "switches_all": "switch_group + switch_party events; exact sum.",
            "switches_sourced": "Switch events with a source_url.",
        },
    }
'''
assert s.count(anchor) == 1, s.count(anchor)
p.write_text(s.replace(anchor, addition))
PY
```

**CHECKPOINT 4**
```bash
.venv/bin/ruff check backend/routers/api.py && .venv/bin/python -m pytest tests/test_api.py -q -k "coverage"
```
Expected: `All checks passed!`; all coverage tests pass; exit `0`. New endpoint is additive so legacy shape tests remain green.

---

### Step 5 — `generational_shift`: population denominators, not mean-of-means

**File:** `pipeline/analytics.py`

**5a.** Add the population age dict and the "unknown birth date" denominator. Replace the result-building block (`:393-415`):

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
p = Path("pipeline/analytics.py"); s = p.read_text()
old = '''    ages_by_party: dict[str, dict[str, int]] = {}
    party_names: dict[str, str] = {}
    for person_id, birth_date, party_id, short_name, party_name in session.execute(stmt):
        age = evaluation_date.year - birth_date.year
        if (evaluation_date.month, evaluation_date.day) < (birth_date.month, birth_date.day):
            age -= 1
        if age < 0:
            continue
        ages_by_party.setdefault(party_id, {})[person_id] = age
        party_names[party_id] = short_name or party_name

    results = [
        {
            "party": party_names[party_id],
            "mps_with_birth_dates": len(ages),
            "avg_age": round(sum(ages.values()) / len(ages), 1),
            "median_age": median(ages.values()),
        }
        for party_id, ages in ages_by_party.items()
        if ages
    ]
    results.sort(key=lambda result: result["party"])
    return evaluation_date, results
'''
new = '''    ages_by_party: dict[str, dict[str, int]] = {}
    party_names: dict[str, str] = {}
    population_ages: dict[str, int] = {}  # R-04: dedupe by person, not by party
    for person_id, birth_date, party_id, short_name, party_name in session.execute(stmt):
        age = evaluation_date.year - birth_date.year
        if (evaluation_date.month, evaluation_date.day) < (birth_date.month, birth_date.day):
            age -= 1
        if age < 0:
            continue
        ages_by_party.setdefault(party_id, {})[person_id] = age
        population_ages[person_id] = age
        party_names[party_id] = short_name or party_name

    results = [
        {
            "party": party_names[party_id],
            "mps_with_birth_dates": len(ages),
            "avg_age": round(sum(ages.values()) / len(ages), 1),
            "median_age": median(ages.values()),
        }
        for party_id, ages in ages_by_party.items()
        if ages
    ]
    results.sort(key=lambda result: result["party"])

    # R-04: the denominator is every MP active in scope at the evaluation
    # date, including those with no published birth date. Identical joins and
    # active-window predicates as the main query, minus the birth-date filter.
    scope = (
        select(func.count(func.distinct(Membership.person_id)))
        .join(Person, Person.id == Membership.person_id)
        .join(group, group.id == Membership.org_id)
        .join(party, party.id == Membership.on_behalf_of_id)
        .where(
            is_group(group),
            party.classification == "party",
            Membership.start_date <= evaluation_date,
            or_(Membership.end_date.is_(None), Membership.end_date > evaluation_date),
        )
    )
    if legislature:
        scope = scope.where(Membership.legislature == legislature)
    mps_in_scope = int(session.scalar(scope) or 0)
    mps_with_birth_date = len(population_ages)
    mps_unknown_birth_date = mps_in_scope - mps_with_birth_date
    if mps_unknown_birth_date < 0:
        raise ValueError("demographic scope counts disagree: known > total")

    all_ages = list(population_ages.values())
    totals = {
        "mps_in_scope": mps_in_scope,
        "mps_with_birth_date": mps_with_birth_date,
        "mps_unknown_birth_date": mps_unknown_birth_date,
        "population_avg_age": round(sum(all_ages) / len(all_ages), 1) if all_ages else None,
        "population_median_age": median(all_ages) if all_ages else None,
        "coverage_pct": round(100 * mps_with_birth_date / mps_in_scope, 1)
        if mps_in_scope
        else None,
        "definition": "coverage_pct = mps_with_birth_date / mps_in_scope; population_avg_age is computed over all persons with a known birth date, not a mean of per-party means.",
    }
    return evaluation_date, results, totals
'''
assert s.count(old) == 1, s.count(old)
p.write_text(s.replace(old, new))
PY
```

**5b.** Update the three callers of the now-3-tuple return:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
# pipeline/analytics.py derive_generational_shift
p = Path("pipeline/analytics.py"); s = p.read_text()
old = '''    evaluation_date, results = generational_shift(session, legislature)
'''
new = '''    evaluation_date, results, totals = generational_shift(session, legislature)
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
old2 = '''    if not results:
        print("No party memberships with birth-date data are available.")
    return len(results)
'''
new2 = '''    print(
        f"Population: {totals['mps_with_birth_date']}/{totals['mps_in_scope']} MPs with birth dates "
        f"({totals['coverage_pct']}%); mean age {totals['population_avg_age']}"
    )
    if not results:
        print("No party memberships with birth-date data are available.")
    return len(results)
'''
assert s.count(old2) == 1, s.count(old2)
p.write_text(s.replace(old2, new2))

# backend/routers/api.py
p = Path("backend/routers/api.py"); s = p.read_text()
old = '''        evaluation_date, results = generational_shift(
'''
new = '''        evaluation_date, results, totals = generational_shift(
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
old2 = '''    return {"status": "ok", "as_of": evaluation_date.isoformat(), "data": results}
'''
new2 = '''    return {
        "status": "ok",
        "as_of": evaluation_date.isoformat(),
        "totals": totals,
        "data": results,
    }
'''
assert s.count(old2) == 1, s.count(old2)
p.write_text(s.replace(old2, new2))

# backend/routers/exports.py
p = Path("backend/routers/exports.py"); s = p.read_text()
old = '''        _, ages = generational_shift(db)
'''
new = '''        _, ages, _ = generational_shift(db)
'''
assert s.count(old) == 1, s.count(old)
p.write_text(s.replace(old, new))

# tests/test_analytics.py
p = Path("tests/test_analytics.py"); s = p.read_text()
old = '''        evaluated, results = generational_shift(session, legislature="2024")
'''
new = '''        evaluated, results, totals = generational_shift(session, legislature="2024")
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
old2 = '''        assert results[0]["avg_age"] == 45
'''
new2 = '''        assert results[0]["avg_age"] == 45
        assert totals["mps_with_birth_date"] == 1
        assert totals["mps_in_scope"] == 1
        assert totals["mps_unknown_birth_date"] == 0
        assert totals["coverage_pct"] == 100.0
'''
assert s.count(old2) == 1, s.count(old2)
p.write_text(s.replace(old2, new2))
PY
```

> `backend/graphql/schema.py:507` has its **own** implementation of `generational_shift` and does not call `pipeline.analytics.generational_shift` — it is intentionally untouched (§3).

**CHECKPOINT 5**
```bash
.venv/bin/ruff check pipeline/analytics.py backend/routers/api.py backend/routers/exports.py tests/test_analytics.py && \
.venv/bin/python -m pytest tests/test_analytics.py tests/test_api.py tests/test_export_report.py -q
```
Expected: `All checks passed!`; all tests pass including the new totals assertions; exit `0`.

---

### Step 6 — Leaderboard loyalty: real denominator, no fabricated 100

**File:** `backend/routers/api.py` (`switch_leaderboard`, `:1791-1813`)

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
p = Path("backend/routers/api.py"); s = p.read_text()
old = '''        total_events = totals_by_person.get(person_id, 0)
        span = span_by_person.get(person_id)
        tenure_years = 0.0
        if span and span[0] and span[1]:
            tenure_years = max((span[1] - span[0]).days / 365.25, 0.0)
        tenure_weight = min(1.0, tenure_years / 4.0)
        switch_ratio = (count / total_events) if total_events else 0.0
        volatility = switch_ratio * tenure_weight
        loyalty = round(max(0.0, min(100.0, 100.0 * (1.0 - volatility))), 1)

        leaderboard.append(
            {
                "person_id": person_id,
                "name": name,
                "switch_count": count,
                "first_switch": first_switch.isoformat() if first_switch else None,
                "last_switch": last_switch.isoformat() if last_switch else None,
                "parties": parties_by_person.get(person_id, []),
                "total_events": total_events,
                "tenure_years": round(tenure_years, 1),
                "loyalty_score": loyalty,
            }
        )
'''
new = '''        total_events = totals_by_person.get(person_id, 0)
        span = span_by_person.get(person_id)
        tenure_years = 0.0
        if span and span[0] and span[1]:
            tenure_years = max((span[1] - span[0]).days / 365.25, 0.0)
        tenure_weight = min(1.0, tenure_years / 4.0) if tenure_years > 0 else None
        # R-04: with a zero observed span a single switch produced exactly 100,
        # contradicted by the UI's "100 = never switched". Undefined means null.
        if not total_events or tenure_weight is None:
            loyalty = None
            loyalty_status = "undefined: no observed event span in scope"
        else:
            volatility = (count / total_events) * tenure_weight
            loyalty = round(max(0.0, min(100.0, 100.0 * (1.0 - volatility))), 1)
            if count > 0:
                loyalty = min(loyalty, 99.9)  # never present an observed switcher as 100
            loyalty_status = "ok"

        leaderboard.append(
            {
                "person_id": person_id,
                "name": name,
                "switch_count": count,
                "first_switch": first_switch.isoformat() if first_switch else None,
                "last_switch": last_switch.isoformat() if last_switch else None,
                "parties": parties_by_person.get(person_id, []),
                "total_events": total_events,
                "tenure_years": round(tenure_years, 1),
                "loyalty_score": loyalty,
                "loyalty_status": loyalty_status,
                "loyalty_inputs": {
                    "switch_count": count,
                    "total_events_in_scope": total_events,
                    "tenure_years": round(tenure_years, 1),
                    "tenure_weight": round(tenure_weight, 3) if tenure_weight is not None else None,
                },
            }
        )
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
old2 = '''    return {"status": "ok", "score_scope": score_scope, "data": leaderboard}
'''
new2 = '''    return {
        "status": "ok",
        "score_scope": score_scope,
        "definitions": {
            "switches": "switch_group events only, scoped as score_scope.",
            "loyalty_score": "100*(1 - switch_count/total_events_in_scope * min(1, tenure_years/4)); null when tenure_years <= 0; capped below 100 when a switch is observed.",
        },
        "data": leaderboard,
    }
'''
assert s.count(old2) == 1, s.count(old2)
p.write_text(s.replace(old2, new2))
PY
```

**CHECKPOINT 6**
```bash
.venv/bin/ruff check backend/routers/api.py && \
.venv/bin/python -m pytest tests/test_api.py -q -k "leaderboard"
```
Expected: `All checks passed!`; `test_switch_leaderboard_scope_covers_all_loyalty_ingredients` still passes (it asserts ingredient scoping, not the 100 value); exit `0`.

---

### Step 7 — Scorecard rebellion: exclude abstain/not-voting, publish denominators

**File:** `backend/routers/api.py` (`vote_scorecard`, `:1470-1527`)

**7a.** Add the alignment denominator to the per-person stats init and replace the second pass:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
p = Path("backend/routers/api.py"); s = p.read_text()
old = '''                "loyal_votes": 0,
                "rebel_votes": 0,
            }
'''
new = '''                "loyal_votes": 0,
                "rebel_votes": 0,
                "alignment_denominator": 0,
            }
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
old2 = '''        if pos.group_raw:
            majority = vote_party_majority.get((vote.id, pos.group_raw))
            if majority == pos.choice:
                stats["loyal_votes"] += 1
            else:
                stats["rebel_votes"] += 1
'''
new2 = '''        if pos.group_raw:
            majority = vote_party_majority.get((vote.id, pos.group_raw))
            # R-04: rebellion is only a yes/no position against the party
            # majority. Abstain/not-voting are not rebellion and must not
            # inflate the denominator.
            if majority is not None and pos.choice in ("yes", "no"):
                stats["alignment_denominator"] += 1
                if majority == pos.choice:
                    stats["loyal_votes"] += 1
                else:
                    stats["rebel_votes"] += 1
'''
assert s.count(old2) == 1, s.count(old2)
p.write_text(s.replace(old2, new2))
PY
```

**7b.** Replace the response row construction (`:1509-1527`):

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
p = Path("backend/routers/api.py"); s = p.read_text()
old = '''                "loyalty_pct": round(stats["loyal_votes"] / total * 100, 1) if total else 0,
                "rebellion_pct": round(stats["rebel_votes"] / total * 100, 1) if total else 0,
                "participation_pct": round(total / total_votes_in_scope * 100, 1)
                if total_votes_in_scope
                else 0,
'''
new = '''                "loyalty_pct": round(
                    stats["loyal_votes"] / stats["alignment_denominator"] * 100, 1
                )
                if stats["alignment_denominator"]
                else None,
                "rebellion_pct": round(
                    stats["rebel_votes"] / stats["alignment_denominator"] * 100, 1
                )
                if stats["alignment_denominator"]
                else None,
                "participation_pct": round(total / total_votes_in_scope * 100, 1)
                if total_votes_in_scope
                else None,
                "denominators": {
                    "alignment": stats["alignment_denominator"],
                    "participation": total_votes_in_scope,
                    "definition": "alignment = positions with a party majority and an observed yes/no choice; abstain and not_voting excluded; participation = all votes in scope.",
                },
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
old2 = '''    return {
        "status": "ok",
        "data_exists": data_exists,
        "data": paged,
        "total": total,
        "offset": offset,
        "limit": limit,
    }
'''
# there are several such returns; anchor on the one following scorecard sort
idx = s.index('    data.sort(key=lambda d: d["total_votes"], reverse=True)')
pos = s.index(old2, idx)
s = s[:pos] + s[pos:].replace(old2, '''    return {
        "status": "ok",
        "data_exists": data_exists,
        "data": paged,
        "total": total,
        "offset": offset,
        "limit": limit,
        "definitions": {
            "rebellion_pct": "no-votes against the party's majority choice / alignment denominator; null when denominator is 0.",
            "participation_pct": "positions cast / votes in scope; null when denominator is 0.",
        },
    }
''', 1)
p.write_text(s)
PY
```

**CHECKPOINT 7**
```bash
.venv/bin/ruff check backend/routers/api.py && .venv/bin/python -m pytest tests/test_api.py -q -k "scorecard or vote or cohesion"
```
Expected: `All checks passed!`; selected tests pass; exit `0`.

---

### Step 8 — Traseism payloads carry their definition

**File:** `pipeline/traseism.py`

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
p = Path("pipeline/traseism.py"); s = p.read_text()
old = '''        "coverage": {"completeness": completeness, "note": note},
    }
'''
new = '''        "coverage": {"completeness": completeness, "note": note},
        "definitions": {
            "switches": "Group switches only (Event.type='switch_group'); this is NOT the dashboard all-events total.",
            "party.switches": "Party changes with the unaffiliated bucket skipped, derived from dated group memberships.",
            "members": "Distinct persons holding a parliamentary-group seat in scope.",
            "switch_rate": "switchers / members (distinct people, not events).",
            "switches_per_100_members": "switches / members * 100.",
        },
    }
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
old2 = '''                "coverage": summary["coverage"],
            }
'''
new2 = '''                "coverage": summary["coverage"],
                "definitions": summary["definitions"],
            }
'''
assert s.count(old2) == 1, s.count(old2)
p.write_text(s.replace(old2, new2))
PY
```

**CHECKPOINT 8**
```bash
.venv/bin/ruff check pipeline/traseism.py && .venv/bin/python -m pytest tests/test_traseism.py -q
```
Expected: `All checks passed!`; all 20+ traseism tests pass; exit `0`.

---

### Step 9 — Client types and API methods

**File:** `frontend/src/api/client.ts`

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
p = Path("frontend/src/api/client.ts"); s = p.read_text()

old = '''export interface DashboardStats {
  persons: number;
  memberships: number;
  switches: number;
  committees: number;
  legislatures: number;
  parties: number;
  cross_chamber: number;
  coverage_score: number;
  computed_at: string;
}
'''
new = '''export interface DashboardStats {
  persons: number;
  memberships: number;
  switches: number; // deprecated alias of switches_all
  switches_all: number;
  switches_group: number;
  switches_party: number;
  committees: number;
  legislatures: number;
  parties: number;
  cross_chamber: number;
  coverage_score: number | null;
  coverage_full_rows: number;
  coverage_rows_total: number;
  definitions: Record<string, string>;
  computed_at: string;
}

/** R-04: canonical coverage aggregates; percentages are null when denominator is 0. */
export interface CoverageSummaryResponse {
  status: string;
  totals: {
    memberships: number;
    memberships_dated: number;
    memberships_sourced: number;
    switches_group: number;
    switches_party: number;
    switches_all: number;
    switches_sourced: number;
  };
  percentages: {
    dated: number | null;
    sourced: number | null;
    switches_sourced: number | null;
  };
  definitions: Record<string, string>;
}
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old = '''  coverage: () => get<CoverageItem[]>("/coverage"),
  coverage_detailed: () => get<CoverageRow[]>("/coverage/detailed"),
'''
new = '''  coverage: () => get<CoverageItem[]>("/coverage"),
  coverage_detailed: () => get<CoverageRow[]>("/coverage/detailed"),
  coverageSummary: () => get<CoverageSummaryResponse>("/coverage/summary"),
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old = '''export interface SwitchLeaderboardEntry {
  person_id: string;
  name: string;
  switch_count: number;
  first_switch: string | null;
  last_switch: string | null;
  parties: string[];
  total_events: number;
  tenure_years: number;
  loyalty_score: number;
}

export interface SwitchLeaderboardResponse {
  status: string;
  data: SwitchLeaderboardEntry[];
}
'''
new = '''export interface SwitchLeaderboardEntry {
  person_id: string;
  name: string;
  switch_count: number;
  first_switch: string | null;
  last_switch: string | null;
  parties: string[];
  total_events: number;
  tenure_years: number;
  loyalty_score: number | null;
  loyalty_status: string;
  loyalty_inputs: {
    switch_count: number;
    total_events_in_scope: number;
    tenure_years: number;
    tenure_weight: number | null;
  };
}

export interface SwitchLeaderboardResponse {
  status: string;
  score_scope: string;
  definitions: Record<string, string>;
  data: SwitchLeaderboardEntry[];
}
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old = '''export interface GenerationalShiftResponse {
  status: string;
  as_of: string;
  data: GenerationalShiftEntry[];
}
'''
new = '''export interface GenerationalShiftResponse {
  status: string;
  as_of: string;
  totals: {
    mps_in_scope: number;
    mps_with_birth_date: number;
    mps_unknown_birth_date: number;
    population_avg_age: number | null;
    population_median_age: number | null;
    coverage_pct: number | null;
    definition: string;
  };
  data: GenerationalShiftEntry[];
}
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old = '''  loyalty_pct: number;
  rebellion_pct: number;
  participation_pct: number;
}
'''
new = '''  loyalty_pct: number | null;
  rebellion_pct: number | null;
  participation_pct: number | null;
  denominators: {
    alignment: number;
    participation: number;
    definition: string;
  };
}
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old = '''  matrix: TraseismMatrixCell[];
  repeat_switchers: TraseismRepeatSwitchers;
  timing: TraseismTiming;
  coverage: TraseismCoverage;
}
'''
new = '''  matrix: TraseismMatrixCell[];
  repeat_switchers: TraseismRepeatSwitchers;
  timing: TraseismTiming;
  coverage: TraseismCoverage;
  definitions: Record<string, string>;
}
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

# Add typed /mps client method and response with total (after dashboardStats method)
old = '''  dashboardStats: (asOf?: string) =>
    get<DashboardStatsResponse>(asOf ? `/dashboard/stats?as_of=${asOf}` : "/dashboard/stats"),
'''
new = '''  dashboardStats: (asOf?: string) =>
    get<DashboardStatsResponse>(asOf ? `/dashboard/stats?as_of=${asOf}` : "/dashboard/stats"),

  /** R-04: corpus-wide MP cards; `total` is independent of offset/limit. */
  mps: (q: string, sort: string, limit: number, offset: number) => {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset), sort });
    if (q) params.set("q", q);
    return get<MpsCardsResponse>(`/mps?${params.toString()}`);
  },
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old = '''export interface DashboardStatsResponse {
  status: string;
  data: DashboardStats;
}
'''
new = old + '''
export interface MpCard {
  id: string;
  name: string;
  birth_date: string | null;
  age: number | null;
  party: string | null;
  switches: number;
  committees: number;
}

export interface MpsCardsResponse {
  status: string;
  data: MpCard[];
  total: number;
  offset: number;
  limit: number;
  definition: string;
}
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
p.write_text(s)
PY
```

**CHECKPOINT 9**
```bash
cd frontend && npx tsc --noEmit 2>&1 | head -40
```
Expected at this intermediate point: type errors only in the pages listed in Step 10 that still read fields as non-null / don't yet use new fields. **No errors from `client.ts` itself.** Exit of `head` is `0`; treat as a review checkpoint, not a gate. The final gate is §8.2.

---

### Step 10 — Per-page label and denominator changes

Apply each row with the same deterministic replacement pattern. `en` fallback strings are updated here; Step 11 adds the matching ro/en i18n keys.

| # | File:line | Exact old → new |
| --- | --- | --- |
| 10.1 | `frontend/src/pages/LiveDashboard.tsx:119,126` | `title={t("dashboardStatSwitches", "Switches")}` → `title={t("dashboardStatSwitches", "All observed affiliation changes")}`; `value={stats?.switches ?? "--"}` → `value={stats?.switches_all ?? "--"}` |
| 10.2 | `frontend/src/pages/Traseism.tsx:764` | `{t("traseismTotalSwitches", "total switches in corpus")}` → `{t("traseismTotalSwitches", "group switches in scope")}`; at `:740` add `title={scope?.definitions?.switches}` to the switches `InfoStat` if the component accepts `title` (else add a `<p className="text-xs text-slate-400">…</p>` beneath); at `:852` keep `scope.switches` but label "Group switches" |
| 10.3 | `frontend/src/pages/SwitchLeaderboard.tsx:40,66,60,190-196,233-234` | `const totalSwitches = rows.reduce((sum, row) => sum + row.switch_count, 0);` → `const totalSwitches = rows.reduce(...); // top-N sum, NOT a corpus total` and change label to `t("leaderboard.stat.total_switches", "Group switches in top N")`. Intro text: "MPs ranked by observed **group** switch count (`switch_group`) within the reported scope." Loyalty cell: `row.loyalty_score === null ? "—" : \`\${row.loyalty_score}\``; `title` shows `row.loyalty_inputs` denominators. Methodology text: replace `"100 means no observed switch in the record."` with `"100 is the maximum proxy value; any MP with an observed group switch is capped below 100; — means no observed event span in scope."` |
| 10.4 | `frontend/src/pages/Mps.tsx:20-37,64,84-107` | Local `MpsResponse`/`fetchMps` → import `api, { type MpCard }` and call `api.mps(submitted, sort, PAGE_SIZE, offset)`. `value={rows.length}` at `:86` → `value={cards.data?.total ?? "--"}`; `:100-101` "Total switches" → "Group switches in page" with `rows.reduce(...)` kept but explicitly page-scoped; moment `:107` → `cards.data?.total ?? "--"`; `canNext = rows.length === PAGE_SIZE` → `canNext = offset + rows.length < (cards.data?.total ?? 0)` |
| 10.5 | `frontend/src/pages/MpComparison.tsx:25-38,157-158,174` | Local `MpsResponse`/`fetchMps` → `api.mps("", "name", 200, 0)`. `value={poolList.length}` labelled "Total MPs" → `value={pool.data?.total ?? "--"}` labelled "MPs in corpus (search pool capped at 200)"; at `:174` show `pool.data?.total ?? "--"` |
| 10.6 | `frontend/src/pages/SenateHistory.tsx:67-68,82-85` | `"Senate Members"` → `"Persons in coverage rows (all chambers)"`; `"Full Coverage %"` with integer count value → `"Full coverage rows"` with same value (integer count, no `%`) |
| 10.7 | `frontend/src/pages/Report.tsx:94-95,132,255-258,266-269,451-454` | Delete `completenessValue` (`:94-95`) and replace `value={completenessValue(c.completeness)}` with `value={c.completeness === "full" ? 100 : null}` so `partial`/`none` render as `—`, never 60. `label "Party switches"` → `"Group switches"`; `label "deputies in corpus"` → `"persons in corpus"`; add a line under the totals grid: `"Switches = group switches only; see /api/dashboard/stats for group + party."` |
| 10.8 | `frontend/src/pages/LegislatureDetail.tsx:80-83` | `label "Switches"` → `"Group switches in loaded movements"`; keep group filter but change `?? "--"` to `?? "--"` only when `isLoading/isError` (no fabricated 0) |
| 10.9 | `frontend/src/pages/Grafice.tsx:144-148` | `<div>Switches</div>` → `<div>Group switches</div>` |
| 10.10 | `frontend/src/pages/Parties.tsx:103,135` | `"Switches in"` → `"Group switches in"` for header and i18n fallback |
| 10.11 | `frontend/src/pages/PartyProfile.tsx:78,119-122` | `const totalSwitches = (p.switches_in ?? 0) + (p.switches_out ?? 0);` → `const totalSwitches = p.switches_in === null \|\| p.switches_out === null ? null : p.switches_in + p.switches_out;`; `value={totalSwitches}` stays, label → `"Party switches (in + out)"`; if `null`, render `"—"` |
| 10.12 | `frontend/src/pages/PartyComparison.tsx:104-107` | `a: chairsA ? ... : "0"` → `a: chairsA ? ... : "—"` (same for `b`); add `title` = "No dated chair data in corpus → unavailable, not zero" |
| 10.13 | `frontend/src/pages/PartyTimeline.tsx:123` | `label="Total switches"` → `label="Dated joins in range"` (the value is `datedJoins`, not switch events) |
| 10.14 | `frontend/src/pages/PersonDeepDive.tsx:96-99,124` | either filter `p.events.filter(e => e.type === "switch_group")` so the label stays "Group switches", or relabel to `"Observed switch events (group + party)"`; **choose one and document it** — recommended: filter to group-only to match `personStatSwitches` |
| 10.15 | `frontend/src/pages/Committees.tsx:241-244` | `label "Total members"` → `"Members in expanded committees"`; when no committee expanded, value `"—"` |
| 10.16 | `frontend/src/pages/CoverageView.tsx:34-66,127-130,227-233` | Replace the `totals` `useMemo` with `api.coverageSummary()` query; `datedMemberships` from `summary.totals.memberships_dated`, `sourcedSwitches` from `summary.totals.switches_sourced`; `overallPct` from `summary.percentages.dated` (raw counts), and if `null` render `ProgressRing` with no value + `"—"`. Keep `fmtPct` for per-row nulls (it already returns `—`). Remove `?? 0` from both reducers. |
| 10.17 | `frontend/src/pages/Demographics.tsx:34,43-60,90-94` | `totalMPs = birthDated` → `totalMPs = shift.data?.totals?.mps_in_scope ?? null`; `avgAge` → `shift.data?.totals?.population_avg_age ?? null`; `coveragePct` → `shift.data?.totals?.coverage_pct ?? null`; moment label → `"MPs in scope"`; stat label `"Total MPs"` → `"MPs in scope"`; add a stat/line `"Birth date known: {{n}} / {{m}} ({{pct}}%)"` using totals, rendering `—` when null |
| 10.18 | `frontend/src/pages/Topuri.tsx:79-81,146-154` | `{entries.length} MPs shown` → `{entries.length} of {scorecardQuery.data?.total ?? "—"} MPs shown`; pct cells → `{e.loyalty_pct === null ? "—" : \`\${e.loyalty_pct}%\`}` etc.; add a caption under the table: `"Loyalty/rebellion denominator: {{alignment}} yes/no positions with a party majority (abstain/not-voting excluded). Participation denominator: {{participation}} votes in scope."` from `scorecardQuery.data?.data[0]?.denominators` |
| 10.19 | `frontend/src/pages/Ideology.tsx:76-85,118-122` | Filter scatter data: `const scatterData = filteredData.filter(d => d.lrgen !== null && d.galtan !== null && d.eu_position !== null).map(...)` (remove `?? 0`); tooltip `(d.value[0] ?? 0).toFixed(2)` → `d.value[0] == null ? "—" : d.value[0].toFixed(2)` (same for indices 1/2 and the two salience fields); add a note: `"Parties without a published CHES score are omitted, not plotted at zero."` |
| 10.20 | `frontend/src/pages/Report.tsx` coverage table caption | add `"'partial' means incomplete data, not a numeric percentage."` |

**CHECKPOINT 10**
```bash
cd frontend && npx tsc --noEmit && npm run lint
```
Expected: no type errors; `eslint` exits `0` (existing rules only). This is an intermediate checkpoint; final build is §8.2.

---

### Step 11 — i18n keys (both locales)

**File:** `frontend/src/i18n.ts`

Add to the `ro.translation` object (near `dashboardStatSwitches`) and the corresponding `en.translation` block. Exact keys/strings:

```ts
// RO
"dashboardStatSwitches": "Toate schimbările observate de afiliere",
"leaderboard.stat.total_switches": "Schimbări de grup în primii N",
"groupSwitchesOnly": "Doar schimbări de grup (switch_group); totalul general este în /api/dashboard/stats.",
"report.personsInCorpus": "persoane în corpus",
"report.switches": "Schimbări de grup",
"senateStatMembers": "Persoane în rândurile de acoperire (toate camerele)",
"senateStatCoverage": "Rânduri de acoperire complete",
"senateStatLegislatures": "Legislaturi cu rânduri de acoperire",
"unknown": "necunoscut",
"noDataDenominator": "— (numitor zero)",
// EN
"dashboardStatSwitches": "All observed affiliation changes",
"leaderboard.stat.total_switches": "Group switches in top N",
"groupSwitchesOnly": "Group switches only (switch_group); see /api/dashboard/stats for all events.",
"report.personsInCorpus": "persons in corpus",
"report.switches": "Group switches",
"senateStatMembers": "Persons in coverage rows (all chambers)",
"senateStatCoverage": "Full coverage rows",
"senateStatLegislatures": "Legislatures with coverage rows",
"unknown": "unknown",
"noDataDenominator": "— (zero denominator)",
```

Also **edit** the existing methodology strings in both locales (they currently claim "100 means no observed switch"):
- `leaderboard.methodology.loyalty`: replace the trailing sentence with the canonical definition from §5 (`loyalty_score`).
- `leaderboard.loyalty.hint`: replace `100 = niciodată schimbat` / `100 = never switched` with `100 = maximum proxy value; a person with an observed switch is capped below 100; — = no observed event span`.

**CHECKPOINT 11**
```bash
cd frontend && npx tsc --noEmit && grep -c '"unknown"' src/i18n.ts && grep -c 'maximum proxy value' src/i18n.ts
```
Expected: tsc exit `0`; grep counts ≥1 each (ro+en where applicable), exit `0`.

---

### Step 12 — `docs/API.md` alignment

**File:** `docs/API.md`

In `## Count definitions` (`:404-454`), add a short paragraph under `### Switch counts`:

```md
The API now publishes both definitions as separate labelled fields:
`GET /api/dashboard/stats` → `data.switches_group`, `data.switches_party`,
`data.switches_all` (with a `data.definitions` map); `GET /api/export/report`
→ `totals.switches_group`, `totals.switches_party`, `totals.switches_all`
(`totals.switches` is a deprecated alias of `switches_group`).
`GET /api/traseism/summary` and `/overview` carry a `definitions` map stating
that their `switches` field is group-only. The bare `switches` field on
`/dashboard/stats` is a deprecated alias of `switches_all`.
```

Add to the endpoint list (`:383-403`): `GET /api/coverage/summary` — raw corpus-wide coverage totals; percentages derived from integer counts and `null` at a zero denominator.

Add to `/api/mps` entry: response now includes `total` (corpus-wide, independent of `limit`/`offset`).

**CHECKPOINT 12**
```bash
grep -n 'switches_all\|coverage/summary' docs/API.md
```
Expected: ≥3 matches, exit `0`.

---

### Step 13 — Regression tests (new file)

**File:** `tests/test_count_definitions.py` (new). These are read-only API probes against the DB configured by `PARLAMENT_DB` (default `data/parlament-real.db`); for a hermetic run set `PARLAMENT_DB` to a copy **before** importing `backend.main`, exactly as the other API tests do via `conftest.py`.

```python
"""R-04 regressions: labelled counts, honest denominators, no null→0."""

from fastapi.testclient import TestClient

from backend.main import app


def test_dashboard_stats_publishes_labelled_switch_split():
    client = TestClient(app)
    data = client.get("/api/dashboard/stats").json()["data"]
    assert data["switches_all"] == data["switches_group"] + data["switches_party"]
    assert data["switches"] == data["switches_all"]
    assert set(data["definitions"]) >= {"switches_group", "switches_party", "switches_all"}
    assert data["coverage_score"] is None or isinstance(data["coverage_score"], int)


def test_report_and_dashboard_agree_on_group_switches():
    client = TestClient(app)
    report = client.get("/api/export/report").json()["totals"]
    stats = client.get("/api/dashboard/stats").json()["data"]
    assert report["switches_group"] == stats["switches_group"]
    assert report["switches_all"] == stats["switches_all"]


def test_mps_total_is_not_the_page_length():
    client = TestClient(app)
    body = client.get("/api/mps?limit=3&offset=0").json()
    assert len(body["data"]) <= 3
    assert body["total"] >= len(body["data"])
    assert body["definition"].startswith("total = persons matching q")


def test_coverage_summary_uses_raw_counts_and_null_denominators():
    client = TestClient(app)
    body = client.get("/api/coverage/summary").json()
    t = body["totals"]
    assert t["switches_all"] == t["switches_group"] + t["switches_party"]
    p = body["percentages"]
    assert p["dated"] is None if t["memberships"] == 0 else 0 <= p["dated"] <= 100


def test_generational_shift_totals_do_not_count_unknowns_as_known():
    client = TestClient(app)
    body = client.get("/api/analytics/generational-shift").json()
    t = body["totals"]
    assert t["mps_in_scope"] == t["mps_with_birth_date"] + t["mps_unknown_birth_date"]
    assert t["coverage_pct"] is None or 0 <= t["coverage_pct"] <= 100


def test_scorecard_percentages_are_null_when_denominator_is_zero():
    client = TestClient(app)
    body = client.get("/api/votes/scorecard?min_votes=1&limit=5").json()
    for row in body["data"]:
        d = row["denominators"]["alignment"]
        assert (row["rebellion_pct"] is None) == (d == 0)
        assert (row["loyalty_pct"] is None) == (d == 0)


def test_traseism_payload_declares_group_only_definition():
    client = TestClient(app)
    body = client.get("/api/traseism/summary").json()
    assert body["definitions"]["switches"].startswith("Group switches only")
```

**CHECKPOINT 13**
```bash
.venv/bin/python -m pytest tests/test_count_definitions.py -q
```
Expected: `7 passed`, exit `0`. If the local DB has no vote positions, `test_scorecard_*` still passes because the response has `data: []` (vacuous loop) — see NOT PROVEN.

---

## 8. Verification gates (run ALL before claiming done)

### 8.1 Pytest (full suite)

```bash
cd /home/nedaktov/parlament-deschis
.venv/bin/python -m pytest -q
```
Expected: `0 failed`, `0 errors`, exit `0`. Baseline for the four R-04-touched modules was `63 passed`; after Step 13 expect `70 passed` (63 + 7) plus any other tests in the repo — record the exact number in the PR. A single failure is a blocker; do not waive it.

### 8.2 Lint + build

```bash
.venv/bin/ruff check .
cd frontend && npm run lint && npm run build
```
Expected: `All checks passed!`; `tsc --noEmit`/eslint exit `0`; `✓ built in …s` exit `0` (the pre-existing chunk-size warning is acceptable and unrelated).

### 8.3 API probes (live local server, read-only)

Start in one terminal:
```bash
cd /home/nedaktov/parlament-deschis
PARLAMENT_DB=data/parlament-real.db .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8017
```
Probe (second terminal):
```bash
cd /home/nedaktov/parlament-deschis
.venv/bin/python - <<'PY'
import json, urllib.request
base = "http://127.0.0.1:8017/api"
def get(p):
    return json.load(urllib.request.urlopen(base + p))

s = get("/dashboard/stats")["data"]
print("stats:", s["switches_group"], s["switches_party"], s["switches_all"])
assert s["switches_all"] == s["switches_group"] + s["switches_party"]
assert {"switches_group", "switches_party", "switches_all"} <= set(s["definitions"])

r = get("/export/report")["totals"]
print("report:", r["switches_group"], r["switches_party"], r["switches_all"])
assert r["switches_group"] == s["switches_group"]
assert r["switches_all"] == s["switches_all"]

m = get("/mps?limit=1&offset=0")
print("mps page/total:", len(m["data"]), m["total"])
assert m["total"] >= len(m["data"])

c = get("/coverage/summary")
print("coverage:", c["totals"], c["percentages"])
assert c["totals"]["switches_all"] == c["totals"]["switches_group"] + c["totals"]["switches_party"]

g = get("/analytics/generational-shift")
t = g["totals"]
print("demographics:", t)
assert t["mps_in_scope"] == t["mps_with_birth_date"] + t["mps_unknown_birth_date"]

lb = get("/analytics/switch-leaderboard?limit=20")
print("leaderboard entries:", len(lb["data"]), "null-loyalty:",
      sum(1 for x in lb["data"] if x["loyalty_score"] is None))
assert all(x["loyalty_score"] is None or x["loyalty_score"] < 100 or x["switch_count"] == 0
           for x in lb["data"])

tr = get("/traseism/summary")
assert tr["definitions"]["switches"].startswith("Group switches only")
print("ALL API PROBES OK")
PY
```
Expected: prints the local triple `1217 0 1217` (NOT `2,002` — see §2.4), `report: 1217 0 1217`, `mps page/total: 1 3388`, a coverage dict, a demographics dict, leaderboard summary, `ALL API PROBES OK`, exit `0`.

**Release-DB probe (if the pinned asset is available):** repeat with `PARLAMENT_DB=<pinned parlament.db>`; expect `1217 785 2002`. If the pinned asset is not available, write `NOT PROVEN — pinned-release triple not re-measured; R1 evidence only` in the PR. Never substitute the local number for the release number or vice versa.

### 8.4 UI gate

```bash
cd /home/nedaktov/parlament-deschis
# In terminal A: frontend dev/preview server
cd frontend && npm run dev -- --port 5174
# In terminal B (system python3 with playwright + Chromium, NOT .venv):
python3 scripts/ui_validate.py http://127.0.0.1:5174
```
Expected: `24/24 routes rendered, 0 JavaScript errors, 0 axe violations` (per resolution R8 baseline), exit `0`. Additionally **manually** verify (or record NOT PROVEN) on the affected pages:
- `/` — switch card reads "All observed affiliation changes", value equals `switches_all`.
- `/mps` — "Total MPs" card equals API `total` (3,388), not 60.
- `/compare-mps` — "Total MPs" equals API `total`, with 200-pool note.
- `/traseism`, `/grafice`, `/parties`, `/legislature/:year` — every "Switches" label now says "Group switches".
- `/report` — no 60% ring; `partial` rows show `—`; "persons in corpus".
- `/coverage` — no `0%` where API is `null`; overall % is derived from raw counts.
- `/demographics` — "MPs in scope" with `known/total` and `—` when unknown.
- `/ideology` — no point at (0,0) for missing CHES scores.
- `/topuri` — `—` for null pcts; denominators caption.
- `/leaderboard` — no `100` for a 1-switch MP; `—` when span undefined.

If playwright is unavailable (baseline P7 fails), the UI gate is **NOT PROVEN** — say so explicitly; do not claim 24/24.

### 8.5 Definition grep gate (fast static check)

```bash
cd /home/nedaktov/parlament-deschis
grep -rn 'switches_all' backend frontend/src | wc -l
grep -rn '?? 0' frontend/src/pages/CoverageView.tsx frontend/src/pages/Ideology.tsx \
  frontend/src/pages/PartyProfile.tsx | wc -l
```
Expected: first count ≥ 10; second count `0` for the three named files (any remaining `?? 0` on a count/pct is a defect). Exit `0`.

---

## 9. Rollback

Rollback is per-file from the backup in §6; no DB changes were made.

```bash
cd /home/nedaktov/parlament-deschis
BACKUP=/tmp/opencode/R-04-<the-stamp-from-section-6>
( cd "$BACKUP" && sha256sum -c SHA256SUMS ) || echo "WARN: backup drift — inspect before restore"
while read -r f; do cp -p "$BACKUP/$f" "$f"; done < "$BACKUP/file-list.txt"
# New file created by Step 13 must be removed explicitly:
rm -f tests/test_count_definitions.py
git status --short
git diff --stat
```
Expected after rollback: `git diff --stat` empty for all files in §3; only pre-existing untracked `.nedcode/` and vault backlink remain. Exit `0`.

If a partial rollback is needed (one step only), restore just that step's files from `$BACKUP` and re-run that step's CHECKPOINT plus §8.1.

---

## 10. Acceptance criteria

1. **Definitions exist in code and payload.** `/api/dashboard/stats` exposes `switches_group`, `switches_party`, `switches_all` and a `definitions` map; `/api/export/report` exposes the same three; traseism summary/overview declare `switches` = group-only. `docs/API.md` matches.
2. **Invariants hold:** `switches_group + switches_party == switches_all` on both dashboard and report and coverage summary. `report.switches_group == dashboard.switches_group`.
3. **No page-local totals.** `/mps`, `/compare-mps`, `/leaderboard`, `/topuri` use API `total` for any headline "total" figure. No `rows.length`, `slice(0,N)`, `top-N` sum or expanded-card sum is labelled as a corpus total.
4. **No null→0.** PartyProfile, PartyComparison, CoverageView, Ideology, Report, Topuri, leaderboard, demographics all render `—` (or localised "unknown") when the source is `null`. `grep` gate §8.5 is clean.
5. **No fabricated percentages.** Report `partial` is not 60; CoverageView overall % comes from raw integer counts; Demographics `avg_age` is population-level and coverage uses persons.
6. **Denominators are published** for loyalty, rebellion, participation, coverage and demographics (`denominators`/`loyalty_inputs`/`totals` fields), and every derived `%` is `null` at a zero denominator.
7. **Labels are correct in both locales** on all 20 pages in Step 10; bare "Switches", "Party switches" (for group-only), "Total MPs" (for a subset/page), "Full Coverage %" (for a count) are gone.
8. **All gates green:** §8.1 pytest, §8.2 lint/build, §8.3 API probes, §8.4 UI gate (or explicit NOT PROVEN), §8.5 grep gate.
9. **No out-of-scope file changed** (compare `git diff --name-only` against §3).
10. **Evidence recorded:** the PR contains the exact probe output for both local and (if available) release DB, and the UI-gate result or its NOT PROVEN statement.

---

## 11. Dependencies

| Dependency | Needed for | Blocking? |
| --- | --- | --- |
| `eb693b4` tree == local `HEAD` tree (P0) | all line-number citations | **Yes** — stop if false |
| `.venv` with pytest/ruff/httpx | §8.1, §8.2 | Yes |
| `frontend/node_modules` + npm | §8.2, §8.4 | Yes |
| `data/parlament-real.db` (read-only) | API probes | Yes; use a copy if the live file is locked |
| Pinned release asset from `data/latest-release.txt` | release-DB probe (1,217/785/2,002) | No — record NOT PROVEN if absent |
| System python3 + playwright + Chromium | §8.4 UI gate | No — record NOT PROVEN if absent (baseline lacks it) |
| `docs/AUDIT-RESOLUTIONS-2026-11-21.md` R1/R2 | definition authority | Yes (already present) |
| Other recipes (date/as-of, i18n sweep, state system, visual primitives, coalition proxy) | not required here | No — R-04 must not absorb them (§12) |

R-04 is **independent** of the other repair recipes at the file level except for shared i18n keys and `client.ts`; if another agent edits those files concurrently, merge in this order: definitions/payload first, then types, then labels.

---

## 12. Side-quest policy

The following are **explicitly out of scope** and must not be "fixed while I'm in here":

- FN-1 / X2 `date` / `as_of` wiring on pages that ignore it — separate recipe.
- FN-5 / X3 loading/error/empty state system and retry buttons — separate recipe. (R-04 only ensures `null` renders as `—`; it does not redesign state components.)
- X4 i18n keys **other than** the count/denominator keys in Step 11 — separate recipe.
- X5 orphan routes, unreachable `About`/`LiveFeed` — separate recipe.
- X6 provenance rendering (source URL/confidence/precision) — separate recipe.
- X7 `DataBar` hex-in-className, canvas theme, radial clipping — separate recipe (visual primitives).
- X8 coalition stability proxy, Bureau placeholder, PopuList misclaim — separate recipe.
- FN-8 vote scope (hardcoded 2024 vs local 2020 corpus, `positions_incomplete` surfacing) — separate recipe; R-04 only fixes the rebellion denominator and null rendering on `/topuri`.
- Any DB write, dedupe change, event-type merge, or attempt to make the local DB's `switch_party` non-zero — **forbidden** (R1: definitional, not a data bug).
- Adding new dependencies, changing CI, touching `data/*`, or moving files.

If an implemented step needs one of these, **stop, leave the file unchanged, and report the blocker with the path:line** to the orchestrator. Do not ask the user mid-flight; report at the checkpoint.

---

## 13. Rollout / commit points

- **Commit 1 (backend):** Steps 1–8. Verify §8.1 (backend tests only) + §8.3 probes. Payloads are additive, so frontend still builds.
- **Commit 2 (frontend types + labels):** Steps 9–11. Verify §8.2.
- **Commit 3 (docs + tests):** Steps 12–13. Verify full §8.
- Final PR: include §8 outputs, backup checksum from §6, and the rollback command. Reviewers should re-run §8.5.

---

## 14. NOT PROVEN

Everything below is a **static-code + local-DB** conclusion. It has not been observed in a browser or against the live deployment by this agent:

- **Browser rendering** of any label, ring, tooltip, chart point or `—` placeholder. The UI-gate expectations in §8.4 are from resolution R8's earlier run, not from this recipe's execution.
- **axe/WCAG-AA, 320 px reflow, keyboard/touch, print preview** — not tested.
- **Live/production API payload** — the live host is documented as lagging on `/api/votes/scorecard` and `/api/analytics/ideology` (docs/API.md:265-277, 300-303); do not assume the new canonical/legacy alias behaviour is deployed. R-04 does not change those routes.
- **The pinned-release 1,217 / 785 / 2,002 triple** was *not* re-measured by this agent. The local DB measured `1,217 / 0 / 1,217`. The release triple comes from R1 and `docs/API.md:414-432`. Re-measure with the pinned asset before quoting it as observed.
- **Scorecard tests on real votes** — the local corpus has 52 votes with positions; the seeded test fixtures may not exercise the abstain/not-voting exclusion end-to-end. `test_scorecard_percentages_are_null_when_denominator_is_zero` can pass vacuously if `data == []`.
- **Whether `ProgressRing` with a null/undefined `value` renders an empty ring without a JS error** — depends on the component; if it throws, fall back to rendering `"—"` text instead of the ring (Step 10.16).
- **Whether any `InfoStat` accepts a `title` prop** (Step 10.2) — inspect `frontend/src/components/InfoStat.tsx` before applying; if absent, use the sibling `<p>` approach.
- **Performance** of the two extra aggregate queries and the population-scope query on the full corpus — not profiled; if slow, add caching consistent with the existing `@cache_result` pattern, but only after measuring.
- **No claim is made that the old numbers were "wrong"** — they were correct for their own artifacts and definitions (R1/R2). R-04 fixes labels, denominators and null handling, not the data.
