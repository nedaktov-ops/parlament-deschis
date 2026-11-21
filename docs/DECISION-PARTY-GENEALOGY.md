# Decision report — party genealogy (`previous_party_id` / `successor_party_id`)

- **Decision:** **DROP** party genealogy from active scope. Do not ingest any
  predecessor/successor links. Keep the two columns as unused legacy schema.
- **Date:** 2026-11-21
- **Owner:** master agent (spawning session). This report is read-only research;
  no code, schema, data, or config was changed by this task.
- **Rule applied:** identity by exact ID, never by name; NC/SA/unverified sources
  never enter the CC-BY 4.0 output; never assert undeclared mergers or splits;
  if a source's licence or coverage is not proven, mark NOT PROVEN and do not
  ingest. No new audit failures.

## Decision in one paragraph

No candidate source declares a **complete, referenced, ID-addressable**
predecessor/successor relation that can be redistributed into our CC-BY 4.0
dataset. The two licence-complete sources (Wikidata, Party Facts) either publish
unsourced and ambiguous relations or explicitly declare the coding incomplete and
ship no genealogy columns in the licensed archive. The two sources that do
declare split/merge semantics are licence-blocked (ShareAlike) or have no proven
licence at all. Ingesting any of them would require inferring links, which is
forbidden. DROP is therefore the only evidence-consistent option.

## Evidence table

| Source | URL | Licence | Declared relation | Redistributable? | Verdict |
| --- | --- | --- | --- | --- | --- |
| Wikidata Q752435 (PSD) | `https://www.wikidata.org/wiki/Q752435` and `https://www.wikidata.org/wiki/Special:EntityData/Q752435.json` | CC0 for structured data (`https://www.wikidata.org/wiki/Wikidata:Licensing`) | `P1365` "replaces" ×4: Q14923612, Q2917689, Q3827065 (point in time 2003), Q18549616 — **every statement has 0 references**; `P1366`/`P155`/`P156` = 0 | Licence yes; relations unsourced and ambiguous | **Do not ingest** |
| Party Facts Core Parties (2023 archive) | DOI `https://doi.org/10.7910/DVN/TJINLQ`; files API `https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/TJINLQ` | CC0 1.0 confirmed by Dataverse metadata (`"rightsIdentifier":"CC0-1.0"`) | Codebook: "Relations between parties are shown on the core party's page, containing successor and predecessor parties"; "**Note — Coding of party changes and party names incomplete.**" Archived `core-parties.csv` columns: `country, partyfacts_id, technical, name_short, name, name_english, name_other, year_first, year_last, share, share_year, new, wikipedia, description, comment, created, modified` — **no predecessor/successor column** | Licence yes; genealogy absent from licensed archive and coverage self-declared incomplete | **Do not ingest** |
| PolPaL (Political Party Links) | `https://polpal.org/index.html`; `https://www.medem.eu/polpal-connecting-political-party-data` | **NOT PROVEN** (no licence published) | Records "splits and mergers" and time-sensitive links; site states "PolPaL Coming Autumn 2026", "under construction" — no released dataset | No — licence not proven, no data | **NOT PROVEN; excluded** |
| SER-PROM | `https://serprom.eu/` | CC BY-SA 4.0 (project register, `pipeline/licenses.py:203-211`) | Party-change material, cross-check only | No — ShareAlike is barred by project rule | **Excluded** |
| External Romanian civic source (ro_281) | licence register `pipeline/licenses.py:80-90` (source name `ro_281`) | CC-BY-4.0, self-declared | Not a party-genealogy source | Licence yes but irrelevant to genealogy | **Not used for genealogy** |

## Raw evidence (quotes and counts)

- Wikidata `Special:EntityData/Q752435.json` (lastrevid 2568018839, modified
  2026-11-11): `P1365` has 4 statements; reference counts are `0, 0, 0, 0`.
  Rendered page lists them under "replaces" — all marked "0 references". Four
  different predecessor parties for one organization is not a single legal
  succession and cannot populate a one-valued `previous_party_id` without a
  human decision (i.e. inference).
- Party Facts codebook (`https://partyfacts.herokuapp.com/documentation/codebook`):
  "Party changes — _Note — Coding of party changes and party names incomplete._
  Relations between parties are shown on the core party's page, containing
  successor and predecessor parties." News 2015-12-22: "We include a few party
  changes but for most of the core parties this information has yet to be added
  in the future." The live relations pages were on the decommissioned
  `partyfacts.herokuapp.com` API (`pipeline/sources/party_facts.py:3-4`).
- The licensed Dataverse `core-parties.tab` header contains no genealogy field;
  the only free-text fields are `description` and `comment`, which the codebook
  says "may also include party relations" but are unstructured and incomplete.
- Four distinct Party Facts IDs are confirmed in the project adapter
  (`pipeline/sources/party_facts.py:14`): FSN=958, FDSN=276, PDSR=1034, PSD=120.
  A name-based "PSD replaces PDSR" mapping would conflate distinct identities;
  this is explicitly disallowed. QIDs are a different identifier system again.

## Current schema / audit / API state (read-only)

- `pipeline/db.py:175-181` — both columns declared `ForeignKey("organization.id"),
  nullable=True`; `pipeline/db.py:709-710, 757-758` — listed as FKs excluded from
  the ordinary identity/merge machinery.
- Read-only count on `data/parlament.db` and `data/parlament-real.db`:
  `select count(*) from organization where previous_party_id is not null or
  successor_party_id is not null` → **0** (120 organizations in each).
- `pipeline/audit.py` — no genealogy audit check exists. The only "merge" logic
  is interval merging (`:126, :246`) and the identity warning "never to merge two
  identities" (`:575`); neither concerns party genealogy.
- `backend/graphql/schema.py` — no genealogy field is exposed (confirmed by
  `docs/METHODOLOGY.md:341-346`: selecting `previous`/`successor` fails).
- `backend/routers/api.py:1004-1006` — party-timeline `gaps` hardcodes
  `"predecessor_links": 0, "successor_links": 0`.

## Removal steps (documentation-only; no code required)

1. `docs/METHODOLOGY.md:304-346` — retitle §9 "Party genealogy — retired
   (historical design, not active scope)". Add a one-line pointer to this
   decision. Keep §9.1–§9.4 as **historical design notes, not implemented**;
   strike the implication in `:306` that the project "records" genealogy.
2. `docs/DATA-MODEL.md:71-72` and `:330` — mark `previous_party_id` /
   `successor_party_id` as legacy, always NULL, retained for schema
   compatibility; no ingestion planned.
3. `docs/GAP-ANALYSIS-2026-11-21.md:44, 94, 101, 133` — remove genealogy from the
   open P1 gap list and from recommended work; record it as decided-and-dropped
   on 2026-11-21. This also resolves the "15 features all complete"
   self-contradiction noted at `:101`.
4. `docs/DATA-ENRICHMENT-RESEARCH.md:74, 330` — keep as historical research; add
   a note that the suggested genealogy enrichment was rejected by this decision.
5. UI text (already honest, no false claim to retract): `frontend/src/pages/
   PartyTimeline.tsx:177-178` and the ro/en `ptimeline.gapBody` strings at
   `frontend/src/i18n.ts:492, 1055` already say "Mergers and splits are NOT
   machine-declared in this corpus ... never asserted". Optionally append that
   genealogy ingestion is retired; do not add any succession claim.
6. Do **not** add an ingestion adapter, a new licence entry, a schema migration,
   or a GraphQL/API field. Do not populate the columns from name similarity.

## Verification

- Re-run the read-only count after the doc edits; it must remain `0`:
  `sqlite3 data/parlament.db "select count(*) from organization where
  previous_party_id is not null or successor_party_id is not null;"` → `0`.
- `grep -rn "previous_party_id\|successor_party_id" pipeline/sources
  pipeline/parse backend/routers` → no new write path; only the existing
  `pipeline/db.py` FK declarations remain.
- `git diff --check` clean; only this report file added by this task.
- No audit gate changes: the project's existing verification suite stays as-is
  because no runtime code changed. No new audit failures are introduced because
  no checks or code are added.

## Rollback

No runtime change to roll back. If a future owner supplies an official,
licence-complete and referenced genealogy source, revert the documentation
labels above and reopen the feature through a new decision report with its own
evidence table; do not re-enable it from the sources rejected here.

## NOT PROVEN / excluded

- **PolPaL licence** — NOT PROVEN; no licence text and no released data.
- **Party Facts genealogy coverage** — NOT PROVEN as complete; source states it
  is incomplete and the licensed archive has no genealogy columns.
- **Wikidata Q752435 relations** — declared but **without any reference**; not
  evidence of an undeclared merger/split and not usable for identity mapping.
- **SER-PROM CC-BY permission** — NOT PROVEN; CC BY-SA only, cross-check only.
- Any claim that FSN/FDSN/PDSR/PSD are one party — contradicted by four distinct
  Party Facts IDs; identity is by exact ID only.
