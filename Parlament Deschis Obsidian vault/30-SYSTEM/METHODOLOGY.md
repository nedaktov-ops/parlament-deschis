---
id: METHODOLOGY
type: reference
title: "Methodology — fact rules, intervals, confidence, coverage and licensing"
description: "Normative distilled reference for how facts are dated and qualified: no invented days, end-exclusive intervals, confidence ranks, switch definitions, coverage badges and licence policy."
status: active
authority: canonical
tags: [type/reference, lifecycle/active, domain/research]
source_paths: [docs/METHODOLOGY.md, pipeline/traseism.py, pipeline/coverage.py, pipeline/licenses.py]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Methodology

This is the normative reference for what counts as a fact. Official publications of the two chambers outrank every enrichment source; where they disagree, the publication wins. The tracker is not an official record.

State context: [CURRENT-STATE](../10-STATE/CURRENT-STATE.md). Storage of these fields: [DATA-MODEL](DATA-MODEL.md).

## Dating rules

- **No invented days.** A full date is stored as-is (precision `YYYY-MM-DD`); a month-only source becomes the window `[YYYY-MM-01, YYYY-MM-30]` with precision `YYYY-MM`; a year-only source becomes `[YYYY-01-01, YYYY-12-31]` with precision `YYYY`. The earliest bound is stored in `start_date`/`end_date`; the window and precision travel into the API and exports. A month-only date is never rendered as the 15th.
- **Unknown endpoints stay unknown.** Missing start/end is `NULL`, not the term boundary or today. An open tenure means "no closing date published or observed".
- **Only two narrow inferences**, both flagged: a continuing/founding member's start from the group's founding date (noted in evidence), and the interval boundary between two dated roster observations (`derived`). No inferred party from an acronym, no birth date from a namesake, no synthetic persons, no filling gaps with neighbouring rosters.
- **End-exclusive intervals.** `active(D) = start_date <= D AND (end_date IS NULL OR end_date > D)`. A switch dated 15 June counts in the old group through 14 June and the new group from 15 June; same-day transitions resolve to the new group. A published "până în 15.06.2026" is stored as `end_date = 2026-06-15`.

## Confidence and correction

Four ranks, lower is stronger: `official_ledger` (0), `official_profile` (1), `derived` (2), `community` (3, reserved). A write may **improve** confidence but never downgrades a stronger row; events inherit their tenure's confidence. Corrections must cite an official URL and archive a fresh snapshot; closed tenures are immutable, and merges are audited (`merge_audit`) and reversible (`revert_merge`). The loser row is never deleted. Wikidata may corroborate a birth date or QID but never creates or dates a tenure.

## Switch definitions and denominators

- A **group switch** (`switch_group`) is the same person changing parliamentary group within the **same chamber and same legislature**, where the previous tenure has a published leave date and the next starts on or after it. This is the observed-movement event counted in traseism statistics.
- A **party switch** (`switch_party`) is a lower-confidence view derived from a change in a membership's `on_behalf_of_id` party. The two are different measures: the pinned release has 1,217 group switches + 785 party switches = **2,002 total switch events**. Labelling the 2,002 figure as "group switches" is the labelling gap, not a data bug.
- The traseism denominator is **members at risk**: distinct people who held a parliamentary-group seat in scope, never membership rows (one member contributes several rows). Movement counts say nothing about motives; a move to "unaffiliated" is a loss for the old party, not a gain for a rival.

## Coverage

Coverage counts **distinct ingested `person_id` values** per chamber and legislature, compared with modern chamber sizes **330 deputies / 136 senators**. `full` = at least **90%**; `partial` = between zero and the threshold; `none` = zero. The 90% bar is deliberately conservative (vacancies and replacements mean a term rarely has exactly 330/136 simultaneous members), and using modern sizes for pre-2004 terms makes old terms show `partial` rather than a false `full`. Coverage is not inferred from the existence of a legislature's dates; there is no separate "dimension gap" score to inflate it, and derived memberships still count as ingested people.

## Licensing

Source code is **AGPL-3.0-or-later**; generated data and exports are **CC-BY-4.0** with attribution "Parlament Deschis" plus retained source URLs. Wikidata facts are CC0; archived chamber pages remain the chambers' copyright and exist only to substantiate cited facts. The external Romanian civic source (ro_281) is CC-BY-4.0 and redistributable. NC- or SA-licensed sources (e.g. IPU CC BY-NC-SA, V-Dem CC BY-SA, OpenSanctions CC BY-NC) and unverified sources such as PopuList are **cross-check-only** and never reposited as redistributable. The `source_license` register's redistributable flag is constrained by a DB check to compatible licences, but the register itself is currently latent (see [DATA-MODEL](DATA-MODEL.md)). Source precedence: official chamber publication → committed reference data → Wikidata → reviewed community correction.

## Corrected routes

The older doc text names `/analytics/waves` for switch-wave access. The actual registered route is **`/api/analytics/waves`** (read alias `GET /api/analytics/switch-waves`); vote/ideology canonical paths and their live lag are catalogued in [API](API.md). The vot-parlament source is **cross-check-only** — its vote data is not redistributed in the published corpus.
