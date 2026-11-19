# Methodology / Metodologie

> **Rezumat în română.** Parlament Deschis publică fapte extrase din publicațiile oficiale
> ale Camerei Deputaților și Senatului. Nu inventăm zile atunci când sursa publică doar o
> lună sau un an; fiecare interval are o precizie și o fereastră `[earliest, latest]`.
> Fiecare membru, mandat și eveniment are o sursă și un nivel de încredere. Acolo unde
> datele lipsesc, aplicația afișează `partial` sau `none`, nu o istorie completă fictivă.
> Codul este AGPL-3.0-or-later; datele generate sunt CC-BY-4.0, cu atribuire
> „Parlament Deschis”.

This document defines the rules that decide what counts as a fact, how uncertain dates are
represented, what the confidence levels mean, and how corrections and merges are handled.
It is normative for the pipeline and for anyone contributing data.

---

## 1. Civic and legal basis

Parlament Deschis exists to make already-public information usable. It does not obtain
non-public data, and it does not replace the official record.

The relevant Romanian framework includes:

- **Constitution of Romania, Article 1(3) and Article 1(5).** Romania is a democratic and
  social state governed by the rule of law; observance of the Constitution, its supremacy,
  and the laws is binding. The exact text of Article 1(5) is:
  *„În România, respectarea Constituției, a supremației sale și a legilor este
  obligatorie.”*
- **Constitution of Romania, Article 31.** Guarantees the right of access to information
  of public interest; public authorities must provide it in good faith.
- **Law no. 544/2001 on free access to information of public interest.** Implements the
  constitutional right of access to public information.

Within that framework, the **official publications of the two chambers are the source of
truth**:

- Camera Deputaților publishes parliamentary group composition and dated member ledgers at
  `cdep.ro` (`structura2015.gp`).
- Senat publishes member profiles and group/committee history at `senat.ro`
  (`FisaSenator.aspx`, `ComponentaGrupuri.aspx`).

Where this project and an official publication disagree, the publication wins. The
project's job is to transcribe, date, and link — not to adjudicate politics.

The tracker is **not** an official record. For legal, electoral, or disciplinary purposes,
consult the chambers' published decisions and the Official Gazette.

---

## 2. Fact rules

### 2.1 No invented days

Official pages state dates with different precision:

| Published form | Example | Stored as | Precision |
| --- | --- | --- | --- |
| Full day | `15 iun. 2026`, `15.06.2026` | `2026-06-15` | `2026-06-15` |
| Month and year | `iunie 2026`, `iun. 2026` | earliest `2026-06-01`, latest `2026-06-30` | `2026-06` |
| Year only | `2026` | earliest `2026-01-01`, latest `2026-12-31` | `2026` |

The database stores the **earliest** bound in `start_date` / `end_date` and the precision
tag in `start_precision` / `end_precision`. A month-only date is **never** rendered as the
15th of the month, and a year-only date is **never** rendered as 1 January as if the source
had said so. The window and precision travel with the fact into the API and exports.

### 2.2 Unknown endpoints stay unknown

- A missing start date is `NULL`, not the term start, unless the source or a documented
  inference rule supplies it.
- A missing end date is `NULL` (open tenure), not today and not the term end.
- An open tenure means “no closing date has been published or observed”, not “still in
  office forever”. The UI renders it as *prezent* / *present* with the observation
  timestamp available in the API.

### 2.3 Allowed inference — and how it is flagged

Two inferences are allowed, both narrow:

1. **Continuing/founding member start.** When a group ledger lists a member but publishes
   no individual join date, the start may be inferred from the group's published founding
   date, or from the legislature start when no founding date exists. The evidence row gets
   a note such as `start inferred (founding/continuing member)`, and the precision reflects
   the source of the inferred date.
2. **Interval between observations.** When a current-only roster is observed on date D1 in
   group A and on date D2 in group B, the derived interval for A ends before D2 begins.
   This is marked `confidence="derived"`; it is an interval boundary, not a claim that the
   switch happened on an unobserved day inside the gap.

Nothing else is inferred. In particular, the pipeline does not:

- infer a party from a group acronym when the source does not link them;
- infer a birth date from a namesake;
- infer a committee role from a member's seniority;
- fill a missing term with a neighboring term's roster.

### 2.4 End-exclusive intervals

`end_date` is the **first day the tenure is no longer active**:

```text
active(D) = start_date <= D AND (end_date IS NULL OR end_date > D)
```

Consequences:

- A member who switches on 15 June 2026 is counted in the old group through 14 June and in
  the new group from 15 June.
- A published “până în 15.06.2026” closing date is stored as `end_date = 2026-06-15`; the
  switch date is not double-counted.
- A same-day switch resolves to the new group.

This convention is applied by `pipeline/queries.py` everywhere: API composition, timeline,
person detail, and tests.

### 2.5 What is never done

- No synthetic person rows to make a chamber look full.
- No guessed dates to make a Gantt chart continuous.
- No merging of two people based only on a similar name when both carry different official
  identifiers in the same term.
- No deletion of a closed tenure to “fix” history. Corrections add evidence and, where
  needed, a new audited operation.
- No scraping behind a CAPTCHA or an anti-bot challenge.

---

## 3. Confidence levels

Every membership and event carries one of four values. Lower rank is stronger.

| Value | Rank | Meaning | Typical source |
| --- | --- | --- | --- |
| `official_ledger` | 0 | The chamber publishes the fact in a dated ledger: member, group, join/leave date, role. | Camera group ledger tables. |
| `official_profile` | 1 | The chamber publishes the fact on an official member profile, possibly with history sections. | Senat `FisaSenator` profile. |
| `derived` | 2 | The interval is derived from observations or from an allowed inference rule; no explicit dated statement for this endpoint. | Current-only roster collapse; inferred founding-member start. |
| `community` | 3 | A human-reviewed contribution or correction that is not itself an official publication. Reserved; never used to override an official ledger. | Reviewed issue/PR with citation. |

Rules:

- A write may **improve** confidence (for example, `derived` → `official_ledger`) but does
  not downgrade a stronger row.
- Events inherit the confidence of the membership interval they are derived from.
- Coverage does not use confidence to inflate counts. A derived membership still counts as
  an ingested person, but the row's confidence is visible in the API and UI.
- The UI translates the values as *registru oficial*, *profil oficial*, *dedus*,
  *comunitate*.

---

## 4. Coverage badges

Coverage answers a narrower question than “is history complete?”: **how many distinct
people has the pipeline actually ingested for this chamber and term?**

The calculation (`pipeline/coverage.py`):

1. Read the legislature key events for the chamber.
2. Count distinct `person_id` values in memberships for that chamber and legislature.
3. Compare with modern constitutional chamber sizes: **330 deputies**, **136 senators**.
4. Assign:

| Badge | Rule | What the reader should conclude |
| --- | --- | --- |
| `full` | count ≥ 90% of the modern size | The term is substantially complete at member level. |
| `partial` | 0 < count < threshold | Real data, but visibly incomplete. Do not read the hemicycle as the full chamber. |
| `none` | count = 0 | Nothing ingested for that term/chamber. The UI says so. |

Why 90% and not 100%? Vacancies, deaths, replacements, and source quirks mean a term may
never have exactly 330/136 simultaneous members. The threshold is a conservative “clearly
complete” bar, not an exact seat audit.

Why the modern sizes for old terms? Legislatures before 2004 had different chamber sizes
(1990–1992, for example, had 396 deputies and 119 senators). Using the modern size as the
`full` bar means an old term will show `partial` rather than a false `full`. This is
intentional. A future term-specific threshold would be a methodology change and must be
documented here.

Coverage is **not** inferred from the existence of a legislature's dates. A term with key
events but no memberships is `none`.

The API returns the same matrix as the About modal. The `coverage` step persists the
derived rows; if the table is empty, the API falls back to a `partial`/`none` derivation
from membership presence. (`pipeline.coverage` is implemented; the `parlament coverage`
subcommand is not wired in this checkout.)

---

## 5. Corrections, merges, and history

### 5.1 Corrections

- A correction must cite an official URL. A screenshot or a news article may explain the
  issue, but the official publication is the evidence.
- If the official page changed, fetch and archive a new snapshot; the fragment checksum
  changes and the new evidence points at the new snapshot. The old snapshot remains in the
  archive, so it is possible to see what the pipeline saw before.
- Closed tenures are immutable. A date correction is applied as an explicit update with
  evidence, not by deleting and recreating history silently.
- Corrections that would create an inverted interval are rejected or clamped; `parlament
  verify` reports inverted intervals and orphan rows.

### 5.2 Merges

Two rows can represent the same person when a source changes identifiers or a name is
spelled differently across terms. Merging is deliberately conservative:

1. Prefer an exact official identifier match.
2. Otherwise require a unique name candidate, filtered by birth date and by conflicting
   official identifiers in the same term.
3. If the match is ambiguous, leave two people and record a `match_review` proposal. Do not
   guess.
4. A merge is performed by `merge_persons`, which writes a `merge_audit` row listing every
   operation.
5. A merge can be reversed with `revert_merge`; the audit row is marked `reverted`.

The loser row is not deleted. This keeps the audit meaningful and makes reversal possible.
`match_status` becomes `merged` on the winner.

### 5.3 What “change history” means

The database records both valid time (`start_date`, `end_date`) and observation time
(`first_seen_at`, `last_seen_at`, `event.detected_at`, `evidence.observed_at`). The person
history is the record of what the pipeline observed and when, not a claim that the
underlying real-world fact changed on the observation date. A page edit can change the
observation timestamp without changing the historical tenure.

---

## 6. Sources, enrichment, and precedence

| Priority | Source | Role |
| --- | --- | --- |
| 1 | Official chamber publication (`cdep.ro`, `senat.ro`) | Source of truth for membership, group, role, and dates. |
| 2 | Committed reference data (`data/reference/*.json`) | Term boundaries, group display names/colors. Not a substitute for a membership source. |
| 3 | Wikidata | Cross-check/enrichment of birth dates and QIDs. Never creates or dates a tenure. |
| 4 | Community correction | Human-reviewed, citation-backed; can fix a transcription but does not override an official ledger. |

Wikidata enrichment is conservative:

- It fills a birth date or QID only when the match is supported; otherwise it leaves the
  field empty and may report a candidate for review.
- A different Wikidata QID is a strong signal against a merge.
- `parlament enrich --dry-run` reports proposed changes without writing. Enrichment is
  implemented in the pipeline; the CLI subcommand is not wired in this checkout.

Every fact in an export keeps its `source_url` and `confidence` where the schema has those
fields. A consumer can therefore re-check the claim at the source.

---

## 7. Licensing and attribution

| Material | License | Attribution |
| --- | --- | --- |
| Source code | AGPL-3.0-or-later | Keep the license and source availability obligations. |
| Generated data and exports | CC-BY-4.0 | Attribute **“Parlament Deschis”**, link to the project and the license, and retain source URLs. |
| Archived source pages | Copyright remains with the respective chamber | Stored solely to substantiate cited facts; do not redistribute full pages beyond what the source site permits. |
| Wikidata facts | CC0 (Wikidata) | No attribution required by CC0; the project still records the QID. |

The canonical license texts are committed:

- [`LICENSE`](../LICENSE) — GNU AGPL-3.0.
- [`data/licenses/CC-BY-4.0.txt`](../data/licenses/CC-BY-4.0.txt) — CC-BY-4.0 legal code.
- [`data/licenses/README.md`](../data/licenses/README.md) — licensing notes, source-site
  terms, and the archive/snapshot legal note.

Attribution example for a reused dataset or chart:

> Sursă: Parlament Deschis (https://github.com/parlament-deschis), date sub CC-BY-4.0.
> Faptele provin din publicațiile oficiale ale Camerei Deputaților și Senatului.

### Source-site terms and archives

- The pipeline honors `robots.txt`, identifies itself, paces requests, and stops on a
  CAPTCHA/challenge. It does not attempt to bypass access controls.
- Snapshots are archived to make a cited fact verifiable after the live page changes. They
  are not a redistribution of the chamber's website.
- Copyright in the original pages remains with the respective chamber. If a rights holder
  asks for a snapshot to be removed, the project should remove the archived copy and keep
  the source URL as the citation, rather than silently altering the historical record.
- If a source's terms change and prohibit archival, ingestion for that source should stop
  and the methodology note should be updated.

---

## 8. Methodology changes

A change to any of the following is a methodology change and must be documented in this
file, reflected in tests, and called out in the PR:

- a fact rule (what may be inferred, or how precision is stored);
- a confidence level or its rank;
- a coverage threshold or the seat counts;
- an identity/merge rule;
- the end-exclusive convention;
- a source's precedence;
- licensing or attribution.

Silent changes to these rules are bugs, even if the code still runs.

---

## 9. Party genealogy

Romanian political parties undergo frequent mergers, splits, and renamings. To enable longitudinal analysis, Parlament Deschis records party genealogy as explicit relationships between organizations.

### 9.1 Relationship model

Each `Organization` with `classification="party"` may have:

- `previous_party_id`: the party that preceded it (predecessor).
- `successor_party_id`: the party that followed it (successor).

Both are nullable foreign keys to `organization.id`, creating a directed graph.
**Current status (verified 2026-11-19 by a read-only count on the shipped
database): both columns hold 0 non-null values.** Sections 9.2–9.3 describe the
intended data model, not ingested genealogy data; this is a declared gap.

### 9.2 Genealogy rules

1. **Linear succession** — A party B that continues party A sets `previous_party_id = A.id`. A sets `successor_party_id = B.id`. Example: `PSD.previous = FDSN`, `FDSN.successor = PSD`.

2. **Split** — One party divides into multiple successors. The parent has no single successor; each child records the parent in `previous_party_id`. Example: `PNL` splits → `PNTCD.previous = PNL`, `PNL-CD.previous = PNL`. `PNL` keeps `successor = NULL` (multiple children).

3. **Merger** — Multiple parties merge into one. The merged party records one predecessor in `previous_party_id` (the dominant legal successor). Others are linked via evidence notes. Example: `ALDE` merged into `USR` → `USR.previous = ALDE`, `ALDE.successor = USR`.

4. **Continuity** — A party with no predecessor or successor (e.g., `UDMR`) has both fields `NULL`. It signals an unbroken legal identity.

### 9.3 Source precedence for genealogy

1. Official party statutes / founding documents published by the party.
2. Court of Accounts / AEP decisions on party registration / dissolution.
3. Parliamentary records of group renaming or succession declarations.
4. Academic histories with specific legal citations (used only for verification).

Wikidata QIDs are recorded for cross-referencing but do not establish genealogy.

### 9.4 Querying genealogy

**The GraphQL API does not expose party genealogy.** Live introspection of
`PartyType` on 2026-11-19 returned only `id`, `name`, `shortName`,
`classification`, `color`, `wikidataQid`, `foundingDate`, `dissolutionDate` and
`chamber`. Selecting `previous` or `successor` fails with `Cannot query field
'previous' on type 'PartyType'`. Party genealogy is a declared data gap, not a
queryable feature. The supported party query is:

```graphql
query {
  parties(classification: "party", limit: 5) {
    shortName
    name
    wikidataQid
    foundingDate
    dissolutionDate
  }
}
```

---

## 10. Switch wave detection

Party switching is a salient feature of Romanian parliamentary life. To move beyond isolated events, the pipeline detects **switch waves** — clusters of `switch_party` events in time.

### 10.1 Algorithm

1. Collect all `switch_party` events (optionally filtered by chamber / legislature).
2. Sort by `event_date`.
3. Slide a fixed window (default 30 days, configurable) over the sorted events.
4. If the window contains ≥ N switches (default 3, configurable), emit a `SwitchWave`.
5. Label the wave with the closest known trigger event within ±90 days:
   - Election dates
   - Government formation dates
   - Party congresses (major)
   - Coalition breakups
5. Deduplicate via signature `(start_date, end_date, chamber, legislature)`.

### 10.2 Wave properties

| Field | Meaning |
| --- | --- |
| `label` | Human-readable description |
| `start_date`, `end_date` | Inclusive window bounds |
| `switch_count` | Number of switches in the window |
| `trigger_type` | `election`, `government_formation`, `party_congress`, `coalition_breakup`, `other` |
| `trigger_event` | Human-readable description of the trigger |
| `legislature` | Legislature label (e.g., `2024`) |
| `chamber` | `deputies` or `senate` |

### 10.3 Access

- REST: `GET /api/analytics/switch-waves`, `GET /analytics/waves`
- GraphQL: `switchWaves(chamber, legislature, limit)`

---

## 11. Analytics methodology

### 11.1 Party Cohesion Index

Measures how tightly a party's MPs move together.

**Formula**:  
`switch_rate = total_switches / (member_count * avg_tenure_years)`

- `total_switches`: sum of `switch_party` events where the party is the destination (`to_org_id`).
- `member_count`: distinct MPs with a current membership in the party.
- `avg_tenure_years`: mean tenure duration (days/365.25) for all memberships in that party.

The cohesion index is `1 - (std_dev(switch_rate) / mean(switch_rate))` across parties in a legislature. Higher = more cohesive.

**Access**: `GET /api/analytics/party-cohesion`, GraphQL `partyCohesion(legislature)`.

### 11.2 Cross-chamber careers

Identifies MPs who have served in both the Chamber of Deputies and the Senate.

**Algorithm**: For each person, collect distinct `chamber` values from their memberships. If both `deputies` and `senate` present, record as cross-chamber.

**Access**: `GET /api/analytics/cross-chamber`, GraphQL `crossChamber`.

### 11.3 Generational shift

Computes average and median age per party per legislature, using Wikidata birth dates.

**Algorithm**: For each person with a birth date and a party membership in the legislature, compute age at reference date (today, or legislature end). Aggregate per party.

**Access**: `GET /api/analytics/generational-shift`, GraphQL `generationalShift(legislature)`.

---

## 12. GraphQL API

The `/graphql` endpoint (Strawberry) provides a single flexible query surface.

### 12.1 Root queries

| Query | Arguments | Returns |
| --- | --- | --- |
| `person(id)` | `id: ID!` | `PersonType` |
| `persons` | `q: String`, `chamber: String`, `limit: Int` | `[PersonType!]!` |
| `party(shortName)` | `shortName: String!` | `PartyType` |
| `parties` | `classification: String`, `limit: Int` | `[PartyType!]!` |
| `memberships` | `person_id, org_id, chamber, limit` | `[MembershipType!]!` |
| `events` | `person_id, event_type, chamber, start, end, limit` | `[EventType!]!` |
| `switchWaves` | `chamber, legislature, limit` | `[SwitchWaveType!]!` |
| `partyCohesion` | `legislature, limit` | `[AnalyticsPartyCohesionType!]!` |
| `crossChamber` | — | `[AnalyticsCrossChamberType!]!` |
| `generationalShift` | `legislature, limit` | `[AnalyticsGenerationalShiftType!]!` |

### 12.2 Type definitions (excerpt)

```graphql
type PartyType {
  id: ID!
  name: String
  shortName: String
  classification: String!
  color: String
  wikidataQid: String
  foundingDate: Date
  dissolutionDate: Date
  chamber: String
}

type SwitchWaveType {
  id: ID!
  label: String
  startDate: Date!
  endDate: Date!
  switchCount: Int!
  triggerType: String
  triggerEvent: String
  legislature: String
  chamber: String
}

type AnalyticsPartyCohesionType {
  partyId: ID!
  partyName: String!
  members: Int!
  switches: Int!
  switchers: Int!
  avgTenureYears: Float!
  switchRatePerMpPerYear: Float!
}
```

### 12.3 Playground

Interactive schema explorer available at `GET /graphql` (Strawberry default).

---

## 13. Known gaps (honest coverage)

| Domain | Gap | Reason | Impact |
| --- | --- | --- | --- |
| **Senate historical ingest (1990–2020)** | Discovery is fixed and guarded: 128 GUIDs for 1990, 134 for 2024 — but profile ingest is not wired into `build-corpus`. | Deferred on **identity risk**, not source unavailability: 127/128 name overlap for 1990 and 0 existing `senat_guid` identifiers. | Name overlap is not a verified identity match; do not badge pre-2024 profiles as ingested. See `docs/DATA-COMPLETENESS-RECOVERY.md`. |
| **Voting records** | No roll-call or vote publications found. | Source unavailable. | No whip compliance / voting alignment analysis. |
| **Asset declarations pre-2020** | PDFs not published / not discoverable. | Source unavailable. | Asset extraction only for 2020, 2024. |
| **Committee chairs** | Resolved: dated chair roles are ingested from cdep.ro committee ledgers. | 26 committees / 26 `role='presedinte'` rows in the shipped release. | Committee control is now computed by `derive_committee_control`; 142 switch waves stored. Former gap, not current. |
| **Birth-date coverage** | 3,113 of 3,388 persons (92%) have `birth_date`. | Sourced from cdep.ro committee ledgers 1990–2024, not the ~4% Wikidata reconciliation rate of the earlier spec. | Generational shift is available across parties; ~275 persons still lack a sourced date. |
| **Party genealogy pre-1990** | Pre-1990 parties not in scope. | Scope boundary. | Genealogy starts at 1990. |

---

*End of Methodology.*
