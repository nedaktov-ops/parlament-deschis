# Project audit — 2026-11-13

Scope: every tracked file in `backend/`, `pipeline/`, `frontend/src/`, `tests/`, `docs/`, `data/reference/`,
plus configuration, CI and deployment. Each finding is backed by a reproduction taken from the live
sources or from the repository itself. Severity is judged by one question only: **does this defect make
the published statistics about traseism wrong?**

## Status update — 2026-11-14

This document records the initial audit baseline; its historical “open” labels below are not a current
issue tracker. Subsequent implementation changed the state materially:

- The real corpus is now the API default, the corpus build/audit commands and CI workflows exist, and
  `pipeline/traseism.py` supplies the group-switch statistics and coverage used by the public UI.
- Group-event derivation is chamber/legislature scoped, uses logical-event upserts, and does not invent
  group-rename dates. The active corpus ingester classifies departures; the older ledger ingester now
  uses `UNKNOWN` rather than asserting every departure was a party change.
- Database uniqueness/integrity fixes and regression tests were added. Analytics-wave writes now use
  token-protected `POST` routes with explicit commits; GET attempts return 405.
- The Institutional page now reads cross-chamber careers from dated `Mandate` records and applies the
  selected date. Committee and bureau panels explicitly report that those source data are absent.
- Party switching and generational summaries now use the group-to-party `on_behalf_of` relationship,
  dated memberships, and historical ages. The party-switch endpoint reports unavailable data rather
  than presenting an empty result as zero switching.

Remaining data/product limits: committee and bureau composition cannot be calculated until the project
ingests official membership/chair records. The legacy `derive_committee_control` helper returns
`None` for that unsupported analysis. Party-switching rates are not a statistical “cohesion index” and
should be interpreted only when dated, attributable party-switch events exist.

---

## 0. Verdict against the product goal

The product goal is: *help the public understand traseism in the Romanian Parliament, statistically, in
both chambers, across all legislatures.*

**As of this audit the project does not achieve that goal.** The code is a sound temporal-model
implementation (as-of queries, provenance, confidence, exports, bilingual UI), but the three things that
make it a *traseism* tool were missing or wrong:

| Requirement | State before this audit | Evidence |
| --- | --- | --- |
| Real membership data | **Fabricated.** `data/parlament.db` holds 444 synthetic people named `PSD MP 1…444`, 0 evidence rows, 0 identifiers, 888 `join` events, no source URLs. | `sqlite3 data/parlament.db` row dump |
| Both chambers, all legislatures | **Senate historical data could not exist.** The pipeline read `senat.ro` profiles, which carry mandates and committees but **no dated group intervals** (verified on live captures). | `senat-probe/REPORT.md`: "NO dated group-membership intervals" |
| Statistical traseism | **Absent.** No switch rate, denominator, per-party net, from→to matrix or repeat-switcher analysis exists. The UI has a sankey of movements, not statistics. | no `traseism` module, no `/api/traseism`, no `/traseism` route |

Everything below is the evidence for what had to change to reach the goal.

---

## 1. P0 — defects that corrupt the statistics

### 1.1 The collection target was the wrong site for the Senate — **fixed**
`senat.ro` publishes no dated group history, so a Senate traseism series was impossible from it.
`cdep.ro` serves **both chambers** from the same application (`structura2015`):
`cam=2` = Chamber of Deputies, `cam=1` = Senate, `leg` = legislature, `idg` = group id.
Verified live for every legislature 1990–2024, both chambers, with dated `Membru din` / `Membru până`
columns. The Senate ledgers are the same template as the Chamber's.

### 1.2 `idm` is per-mandate, so the same MP was a different person in every legislature — **fixed**
`Marcel Ciolacu Ion` is `idm=71` in the 2016 Chamber ledger and `idm=70` in the 2020 one. The profile
page's *Mandate parlamentar* block links every mandate of a person (`idm`, `leg`, `cam`). That graph is
the authoritative identity source and now drives person resolution
(`pipeline/parse/cdep_profile.py`, `pipeline/collect.py::cluster_mandates`).

### 1.3 The parser silently dropped members — **fixed**
Header-driven column mapping replaced cell-count guessing. Confirmed drops:

| Page | Symptom | Fix |
| --- | --- | --- |
| 1990 / 2020 former tables (`Nume \| Membru până`) | all 55 former members of the 1990 FSN group lost | 2-column shape supported |
| current roster with no party column (USR 2016 deputies, UDMR senate) | 0 of 5 / 0 of 9 members | `Functia \| Nume \| Membru din` supported |
| current roster with no dates at all (1990 UNR, minorities) | 0 of 12 members | `Functia \| Nume \| Partid` supported |
| Senate `Functia \| Nume` roster (current *and* former bureau share the shape) | only the first member kept | resolved by document order + `până în` |

Reconciliation after the fix (index count vs ledger rows):

```
senate    1990: index=106 ledger=106   senate    2016: index=135 ledger=135
senate    2020: index=133 ledger=135   deputies 1990: index=380 ledger=380
deputies  2016: index=293 ledger=294   deputies 2020: index=319 ledger=321
```

The residual `+1/+2` are **not** errors: the group index is a start-of-term snapshot, the ledger is the
end-of-term roster (AUR grew from 23 to 25 deputies during 2020–2024). The difference is itself a finding.

### 1.4 `derive_group_events` fabricated switches — **open**
It sorted every membership of a person across **all chambers and all legislatures** and emitted a
`switch_group` whenever the organisation changed, without requiring the previous tenure to be closed.
Consequences: a deputy who became a senator was counted as a switch; overlapping ledger dates produced
a switch; a new legislature's first membership was a "switch" from the previous term.

### 1.5 Every departure was labelled `CHANGED_PARTY` — **open**
`ingest_cdep_group_ledger` set `end_reason="CHANGED_PARTY"` for every former member, including members
who left Parliament or whose term ended. That inflates any "party changers" count.

### 1.6 SQLite uniqueness constraints are ineffective — **open**
`NULL != NULL` in SQLite, so three constraints do not constrain:

- `membership.uq_stint (org_id, person_id, post_id, end_date)` — duplicate **open** tenures allowed.
- `organization.uq_org (classification, normalized_name, founding_date)` — duplicate organisations allowed
  (two `POT` rows exist in the shipped DB).
- `person_identifier.uq_identifier (scheme, identifier, legislature)` — duplicate global identifiers allowed.

### 1.7 Events carry no source — **open**
`Event` has no `source_url`, `legislature` or `snapshot_hash`. For a tool whose entire promise is
"every claim is traceable to the official publication", every derived event is uncitable.

### 1.8 Corrected dates create duplicate events — **open**
`Event.dedup_key` embeds the event date. When a tenure date is corrected, the old event is not
invalidated and a second event is created for the same move.

---

## 2. P1 — defects that make the product wrong or misleading

### 2.1 The documentation contradicts the code and the data
- `docs/METHODOLOGY.md:492` — "Senate historical (1990–2020): no ledger publications discoverable …
  Senate coverage `none` pre-2024." **False**: cdep.ro `cam=1` serves the Senate for every legislature.
- `docs/RESEARCH.md:18` — "Senate pre-2024 requires manual discovery or alternative sources." **False**
  for the same reason.
- `docs/RESEARCH.md` — states cdep's robots.txt disallows `/ords/`. The live file disallows only
  `/declaratii/`.
- `README.md` advertises a "time-slider dashboard (1990 → present)" while the only ingestable data is a
  two-ledger fixture sample.

### 2.2 `data/parlament.db` is fabricated but looks authoritative
It is gitignored, but it is the file the API serves by default, and it contains 444 fake MPs with no
evidence. Any screenshot or demo of the current app shows invented data.

### 2.3 No statistical module exists
There is no switch rate, no denominator ("MPs at risk"), no per-party gain/loss/net, no from→to matrix,
no repeat-switcher count, no coverage-weighted confidence. The analytics endpoints that do exist
(`party-cohesion`, `generational-shift`) are computed from `switch_party` events, which are derived from
the **undated** `Partid` column — the tech evaluation concluded group switches must be the primary metric.

### 2.4 State-changing operations are exposed as GET
`GET /api/analytics/waves/recompute` recomputes waves and `GET /api/admin/poll` triggers collection.
Both mutate state, are not idempotent and can be triggered by a crawler.

### 2.5 `derive_committee_control` is a stub returning `0`
It is exposed as if it were an analysis.

### 2.6 `derive_org_events` dates group renames to the founding date
`group_renamed` events get `founding_date`, which is not the rename date.

---

## 3. P1 — operational gaps (the project cannot be shipped)

| Gap | Detail |
| --- | --- |
| No CI | `.github/workflows/` does not exist; nothing runs tests on push |
| No container | no `Dockerfile`, no `render.yaml`, no `vercel.json`, no compose file |
| `scripts/` is empty | the verification entry point referenced in the docs does not exist |
| `frontend/dist` is gitignored | a fresh clone has no SPA; the backend serves `FRONTEND_DIST`, so the UI 404s unless a build step is defined |
| No data build step | there is no command that produces the production database from the live sources |
| `GET /api/committees` returns `[]` | honest, but the endpoint advertises a capability that does not exist |

---

## 4. What is already sound

- The temporal model (`start_date`/`end_date` exclusive, `ApproxDate` with an `[earliest, latest]`
  window and precision, closed tenures immutable) is correct and well tested.
- `parse_ro_date` correctly refuses to invent a day the source did not publish.
- Provenance plumbing (`Fragment`, `Evidence`, `source_url`, `snapshot_hash`) exists and is usable.
- The API surface, GraphQL schema, Popolo/CSV exports, bilingual UI and the time-slider concept are
  good building blocks — they were waiting for real data and real statistics.

---

## 5. Fix order (implemented in this order)

1. **Collection correctness** — parser header mapping, cdep both chambers, disk cache + SHA-256
   manifest, mandate-graph identity. *(done)*
2. **Database integrity** — event provenance columns, partial unique indexes, overlap guard, correct
   `end_reason`, chamber/legislature-scoped event derivation.
3. **Corpus ingest** — persons, organisations, memberships, evidence, coverage, from the real corpus.
4. **Statistics** — `pipeline/traseism.py`: switch counts, switchers, switch rate, per-party net,
   from→to matrix, timing, repeat switchers, coverage.
5. **Public surface** — `/api/traseism/*`, a `/traseism` page, methodology and coverage in the UI.
6. **Ship** — Dockerfile, `render.yaml`, CI, a production database built from the live sources, and a
   verification document with the raw evidence.
