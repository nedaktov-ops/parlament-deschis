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
