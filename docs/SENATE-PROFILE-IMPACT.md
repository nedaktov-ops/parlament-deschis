# Senate Historical Profile Ingest — Copy-DB Impact Report

Task 5. **Read-only for code; the only repo file written is this report.** All measurements
ran against a copy at `/tmp/senate-impact/parlament-copy.db` (43,589,632 bytes, copied from
`data/parlament-real.db`; WAL was empty / integrity `ok`). No DB outside `/tmp` was written.

Evidence rule: measured values are marked **MEASURED**; the discovery counts supplied in the
task brief are marked **CONTEXT** (they cannot be re-derived here — no profile corpus is
archived in the DB: `senator_profile` fragments = 0). No success claim is made.

## 1. What an ingest writes and the identity schemes it needs

- `pipeline/sources/senat.py:240 ingest_profiles` fetches each `FisaSenator.aspx` page,
  archives a fragment (`model="senator_profile"`, `group_key=guid`), and calls
  `ingest_senator_profile`. Historical GUIDs come from
  `pipeline/sources/senat.py:105 fetch_historical_guids` (two-step POST flow, with the
  cross-legislature distinctness guard at `:220`). The CLI path
  `pipeline/cli.py:152-158 ingest --chamber senate` does **not** pass `legislatures=`, so it
  uses only the sitemap (current senators) — historical ingest is not a single CLI command today.
- `pipeline/ingest.py:461 ingest_senator_profile` resolves identity via
  `scheme="senat_guid"`, `identifier=guid`, `legislature=prof.legislature` (`:470-475`), then
  writes: one `PersonIdentifier(scheme="senat_guid")` (or a new `Person`+`PersonName`); one
  **group** `Membership` (`classification="group"`, `confidence="official_profile"`,
  `start=validation_date or legislature_start`, `on_behalf_of=party org`) at `:488-517`; one
  `Membership` per committee/bureau/friendship/delegation row at `:520-546` (class mapped by
  `_senate_org_class`, `:552`); `Evidence` rows via `_add_evidence`; plus a `PipelineRun`,
  a `Fragment`, and a snapshot. Ambiguous names add `MatchReview` rows
  (`pipeline/identity.py:138-147`).
- Group semantics are preserved: writes use `classification="group"` (`:491`) and all reads
  filter `Organization.classification == 'group'` (`pipeline/queries.py:20,23,35,91`;
  `pipeline/audit.py:188`; `pipeline/traseism.py:264` overview). Non-group org classes never
  count as party tenures.
- Identity schemes required: **exact ID** (`senat_guid`+legislature) → auto; **name+DOB** →
  propose; **name alone** → review, never merge. The Senate parser
  (`pipeline/parse/senat_profile.py:30-53,122-189`) has **no `birth_date` field at all**
  (**MEASURED**: fields = name,guid,profile_url,constituency_nr,constituency_name,election_date,
  validation_date,party,group,group_role,legislature,memberships), so the name+DOB tier is
  structurally unavailable for Senate profiles.

## 2. Baseline measurements (on the /tmp copy)

Raw counts (**MEASURED**, read-only sqlite):

```
person=3388  membership=7349  mandate=5273  person_identifier=7097
organization=120  coverage=20  fragment=184  match_review=0  merge_audit=0
senat_guid_identifiers=0  senator_profile_fragments=0
org_classification_group=57  membership_group_scoped=6614
```

`/api/coverage` (`backend/queries.py:613 get_coverage`) — **20 scopes**, summed
`persons=5282`, completeness `{"full":20}`. Senate scopes (chamber, legislature → persons):
`1990→128`, `1992→161`, `1996→154`, `2000→163`, `2004→163`, `2008→137`, `2012→179`,
`2016→141`, `2020→151`, `2024→132`. (Deputies: 1990→448, 1992→381, 1996→367, 2000→393,
2004→378, 2008→339, 2012→416, 2016→361, 2020→354, 2024→336. Full raw JSON:
`/tmp/senate-impact/coverage.raw.json`; captured output `/tmp/senate-impact/baseline.out`.)

`/api/traseism/overview` (`pipeline/traseism.py:264`, POST body via Starlette
`json.dumps(..., ensure_ascii=False, allow_nan=False, indent=None, separators=(",",":"))`):

```
traseism_overview_rows=20
traseism_overview_body_bytes=48419
traseism_overview_sha256=7b5358641d29762ffd355dedfd2ee085d93ffcf34b8576af995f5ed574845857
```

Raw body at `/tmp/senate-impact/traseism_overview.raw.json`. Strict audit gate on copy
(**MEASURED**): `275 errors, 234 warnings` → `275 known errors, 0 new errors`, exit 0.

## 3. Identity risk

Discovery (**CONTEXT**): 128 GUIDs for 1990, 134 for 2024; 127/128 names overlap existing
names. Structural facts (**MEASURED**): `senat_guid` rows = 0; name pool = 3349 distinct
normalized names, 3310 held by one person, 39 ambiguous.

A rolled-back probe on a throwaway copy proved resolver behaviour
(`pipeline/identity.py:82-148`):

```
probe_unique_name='acsinte gaspar' person_id=54d99c8e-1418-49c6-98b2-2638b24ba768
resolve_created=False
resolve_linked_to_existing=True
EXACT_ID_AVAILABLE_TODAY=0 ; NAME_ONLY_AUTO_LINKED=True
senator_profile_has_birth_date_field=False
probe_rolled_back=True
```

| Scheme | Rule | Senate profile supplies? | State today | Outcome |
| --- | --- | --- | --- | --- |
| Exact `senat_guid`+legislature | auto | GUID yes | **0 rows → 0 / 128, 0 / 134 matchable** | none |
| Name + DOB | propose | **NO DOB field** | impossible | unavailable |
| Name alone, unique | review (never merge) | yes | current code **auto-links** | **VIOLATION** |
| Name alone, ambiguous | review | yes | new `Person` + `MatchReview` | needs approval |

Precise answer: **0** candidate profiles can be matched by exact ID today. **127 of 128**
(1990) and effectively all 2024 candidates fall to name handling. Of those, any name that is
unique in the DB (3310 of 3349 names are unique) is **auto-merged on name alone** by current
code (prohibited); ambiguous names (39) create new persons + review flags. Name-only matching
would be *required* for every profile, so the identity risk **cannot be resolved** with
today's data.

## 4. Recommendation — HOLD (named blocker)

**Do not ingest Senate historical profiles.** Blocker: there is no exact identifier source
(0 `senat_guid`; Senate profiles carry no DOB), so ingest would require name-only matching,
and the resolver auto-merges unique name-only matches in violation of project rules.
Lift only when an exact crosswalk exists (e.g. `senat_guid` ↔ `cdep_person`/`wikidata_qid`)
**and** the unique-name path is gated to review-only for `senat_guid`.

Safe staged plan once the blocker is lifted: (1) dry-run on a `/tmp` copy → per-GUID identity
report; (2) assert **0** name-only auto-links; (3) human approval of the review queue;
(4) apply on the copy, run strict audit (275/0 must hold) and re-measure coverage + traseism
SHA against §2; (5) only then publish via the immutable-release pipeline — `render.yaml:5,27`
makes the runtime read-only and the corpus image-baked, so there is no runtime ingest.

## 5. Verification commands

```
# baseline counts (read-only, /tmp copy)
python3 -c "import sqlite3;c=sqlite3.connect('file:/tmp/senate-impact/parlament-copy.db?mode=ro',uri=True);print([c.execute('select count(*) from '+t).fetchone()[0] for t in ('person','membership','mandate','person_identifier')])"
# API outputs on copy
PYTHONPATH=. python3 /tmp/senate-impact/baseline.py
# identity probe (throwaway copy, rolled back)
PYTHONPATH=. python3 /tmp/senate-impact/identity_probe.py
# strict audit gate (read-only)
.venv/bin/python -m pipeline.cli --db /tmp/senate-impact/parlament-copy.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json
# report hygiene
git diff --check
bash scripts/check-doc-truth.sh
```

## 6. Rollback

No code or tracked DB was changed. To unwind any future staged apply: (a) revert the ingest
code change (`git revert`); (b) restore the pristine DB by re-copying
`data/parlament-real.db` to the working path and verify its SHA manifest; (c) the strict audit
gate stays unchanged — re-run §5 and require `275 known / 0 new`, exit 0; (d) require the
traseism overview SHA to return to `7b535864…57845857` and coverage scope totals to §2.
