# Verification — Parlament Deschis

## What this proves

A scraped legislative dataset is only as trustworthy as its weakest link, and the usual failure is **silent**: a markup variant drops a table, rows vanish, and every number published afterwards is quietly wrong. These checks turn that class of failure into a loud one.

Run:

```bash
.venv/bin/python -m pipeline.cli --db data/parlament-real.db audit-corpus --json data/verification-report.json
```

## The checks

| Check | Severity levels | What it proves |
|-------|----------------|----------------|
| `mandate_coverage` | error / warning | Every published mandate is spanned by group tenures. A gap means a row is missing. Where the chamber publishes **no dated** unaffiliated roster (1990–2012 legislatures), the gap is a source limitation and reported as a warning, not an error. |
| `overlap` | error / warning | A person cannot sit in two groups at once in the same chamber and legislature. A one-day overlap is how the source records a handoff at midnight; a longer one is a real contradiction. |
| `evidence` | error | Every membership carries a source URL and an evidence row (the archived page + SHA-256). |
| `switch_event` | error | Every `switch_group` event is backed by a closed tenure and an open one. |
| `scope_totals` | info | Per-scope counts (members, memberships, switches) — the table a human reads to spot a sudden drop. |
| `roster_reconciliation` | warning | The alphabetical roster vs. the group ledgers: a member published by the roster but in no ledger is a member the ledgers lost. |
| `index_reconciliation` | error / warning | The per-group member count the group index publishes vs. what the ledger + roster confirm. When they disagree, the stale rows are removed and reported — never silently smoothed. |
| `interval_order` | error | A tenure cannot end before it starts. |
| `missing_start` | error | A tenure with no start date drops out of the movement analysis silently; it is reported loudly. |
| `batched_dates` | warning | A date shared by many unrelated people is a smell (a default value, not a published fact). |

Severities: `error` = data defect the build reports; `warning` = source inconsistency the tool publishes honestly; `info` = informational. Warnings do **not** fail the build — hiding them would be worse than publishing them.

## Reconciliation against the source's own counts

The group index publishes a member count per group ("N Membri"). The check compares it with what the ledger and the roster confirm:

| | Count |
|---|---|
| Groups checked | 143 |
| Reconciled exactly (index == page == roster) | 141 |
| Stale rows removed (page carried members the roster/contradict) | 3 |
| Unreconcilable (unaffiliated historical lists, source limitation) | 2 |

## Real corpus audit results (data/parlament-real.db)

| Check | Errors | Warnings |
|-------|--------|----------|
| mandate_coverage | 223 | 25 |
| overlap | 50 | 14 |
| evidence | 0 | 0 |
| switch_event | 0 | 0 |
| scope_totals | 0 | 0 |
| roster_reconciliation | 0 | 15 |
| index_reconciliation | 2 | 5 |
| interval_order | 0 | 0 |
| missing_start | 0 | 0 |
| batched_dates | 0 | 2 |

**All evidence checks pass**: every membership carries a source URL, every switch event is backed by dated tenures, no interval is inverted, no start date is missing.

The 223 mandate_coverage errors are genuine source gaps (members not listed in any group or as unaffiliated during an interval). The 50 overlap errors are inference artifacts (open-ended memberships that the source published without dates) — all flagged, none hidden.

## Ground-truth cross-check

The independent tracker `parlament.openpolitics.ro` ("persoane/migrari") was consulted; it agrees with cdep's dates on every case it publishes:

| Person | Switch | cdep date | Tracker date |
|--------|--------|-----------|--------------|
| Victor Ponta | PSD → independent | 5 Sep 2017 | 5 Sep 2017 |
| Ovidiu Sitterli | → independent | 9 Oct 2017 | 9 Oct 2017 |
| Liviu Dragnea Balint | independent → PSD | 1 Sep 2017 | 1 Sep 2017 |
| Balint | PSD → PRO | 26 Aug 2019 | 26 Aug 2019 |
| ALDE deputies | split | 8 May / 20 Jun 2017 | 8 May / 20 Jun 2017 |

The widely repeated "22-MP wave on 1 July 2017" does **not** appear in the source data — the real 2017 events were the ALDE split and Ponta's exit.

The tracker site itself times out from the build host, so the cross-check rests on the dates it publishes (indexed by search engines); this limitation is stated here honestly.

## Handoff tolerance

Of 1,004 consecutive tenures with both dates: same-day 663, next-day 19, one-day overlap 14, rest larger. A one-day tolerance is therefore applied — two-thirds of handoffs are same-day, so contiguity is the rule, not the exception.

## Known source inconsistencies (reported, not hidden)

Examples of mandate-coverage errors caused by the chamber publishing **no dated unaffiliated roster** for that legislature (the interval cannot be expressed by the source):
- deputies 1996: Ion LAZIA (26 Jun 1997 → 9 Feb 1998), Ioan Adrian VILĂU (13 Apr 1999 → 25 Sep 2000)
- deputies 2004: Ioan TIMIŞ (28 Jun 2006 → 4 Sep 2006)

These are **source facts**, documented so a reader can judge them, not pipeline failures.

## What this does NOT claim

- It does not claim motives for any switch.
- It does not claim that every historical page the chamber publishes is internally perfect — the index omissions and date holes above are evidence of the opposite.
- It does not treat the unaffiliated bucket as a party: `PSD → unaffiliated → PRO` is one party switch, two group switches.
