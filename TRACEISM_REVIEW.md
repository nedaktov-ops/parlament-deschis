# Traseism statistics layer — senior review

**Repository:** `/home/nedaktov/parlament-deschis/`
**Files reviewed (all read in full, committed state — not in `git diff`):**
- `pipeline/traseism.py` (448 lines)
- `pipeline/analytics.py` (530 lines)
- `pipeline/events.py` (412 lines) — for `derive_group_events`/`derive_party_events` context
**Also confirmed:** `git status` — none of the three reviewed files are among the 15 modified files; working tree is otherwise dirty in `backend/`, `frontend/`, `pipeline/poller.py`, `pipeline/queries.py`, `tests/test_api.py`.
**Tests read:** `tests/test_traseism.py` (282 lines), `tests/test_analytics.py` (62 lines).

---

## 1. Scope covered

The traseism product has two layers:
- **Group level** (`pipeline/traseism.py`): `traseism_summary`, `traseism_switches`, `traseism_overview`, plus party-level `party_switches` / `party_summary`. Events consumed are `switch_group` rows produced by `pipeline.events.derive_group_events`.
- **Wave / rate layer** (`pipeline/analytics.py`): `derive_switch_waves` / `derive_all_switch_waves` over `switch_party` events (from `derive_party_events`), `party_switching_rates`, `generational_shift`.

Unit of observation per the module docstring (traseism.py:1-16): a **group switch** = same person, same chamber, same legislature, previous tenure closed, next tenure starts on/after leave date. Enforced in `events.py:180-182` (`_HANDOFF_TOLERANCE = 1` day).

---

## 2. `traseism_summary` correctness (traseism.py:96-211)

### Denominator `members` — not double-counted (PASS)
`_member_query` (traseism.py:46-56):
```sql
SELECT count(DISTINCT Membership.person_id)
FROM Membership JOIN Organization ...
WHERE Organization.classification = 'group'
[+ chamber / legislature filters]
```
`DISTINCT person_id` means membership rows are never used as a head-count. A person with several group tenures (e.g. Carol with two rows in the seed data, test_traseism.py:183-206) counts once. Test asserts `members == 3` for 5 membership rows. Correct.

Scope nuance: memberships are filtered by `Membership.legislature` and `Membership.chamber` but **not by date** against the legislature period from `KeyEvent` (`_period`, traseism.py:59-71). So `members` = distinct persons with *any* group membership row in that legislature/chamber, even if the row's dates fall outside the legislature start/end. That's a defensible "at risk" definition but it mixes a date-unbounded denominator with date-bounded numerators (switches filtered only by legislature/chamber, not by period).

### `switchers` and `switch_rate` — guarded (PASS)
- `switchers = len({e.person_id for e in events})` — traseism.py:102. Distinct person_ids among switch events. Correct.
- `switch_rate = (switchers / members) if members else 0.0` — traseism.py:194. Division-by-zero guard present.
- `switches_per_100_members` same guard — traseism.py:195.

One minor inconsistency: `switch_rate` is switchers/members while `switches_per_100_members` is events/members*100. Both documented implicitly; fine as long as consumers know the difference.

### `by_party` merging (PASS)
Multiple group orgs sharing one party label are merged by label (traseism.py:126-150). `seats_start`/`seats_end` use `_seats_at` which again counts `DISTINCT person_id` per org at `start`/`end` (traseism.py:81-93) — no double counting. Seats use the scope's `start`/`end` from `_period` (defaults to `date.today()` when no end date — traseism.py:70).

---

## 3. `repeat_switchers` (traseism.py:157-160)

```python
per_person: dict[str, int] = {}
for e in events:
    per_person[e.person_id] = per_person.get(e.person_id, 0) + 1
repeat = [n for n in per_person.values() if n >= 2]
```
Reported: `people = len(repeat)`, `max_switches = max(repeat) if repeat else 0` (traseism.py:202-205). This counts **group switches**, so Alice's `PSD → NEAFILIATI → PRO` (2 group events, 1 party change) is a repeat switcher here but not in `party_switches`. Semantics differ between the two views; the docstring (traseism.py:1-16) scopes everything to observed group movement, so this is consistent within the module, but worth flagging for anyone comparing `repeat_switchers.people` with `party_summary.switchers`.

### Dedup collapse risk — NOT a real collapse for A→B→A (PASS, with caveat)
`derive_group_events` dedup key (events.py:186-189): `switch:{pid}:{prev.org_id}:{m.org_id}:{ch}:{leg}:{start_date}`. Because both `from` and `to` org ids are in the key, `A→B` and `B→A` on the same date are distinct keys, so rapid A→B→A moves are **not** collapsed even if dates collide. Only a genuine duplicate (same person, same pair, same date, same chamber/legislature) dedupes — correct idempotent behaviour.

Residual caveat: `derive_party_events` (events.py:377) requires `m.start_date >= prev.end_date` with **no** 1-day handoff tolerance, whereas `derive_group_events` allows `m.start_date >= prev.end_date - 1` (events.py:180-182). A same-day handoff yields a `switch_group` but may not yield a `switch_party`; the two event sets can therefore differ by a handful of rows. Cross-layer inconsistency, not a double-count.

---

## 4. `NO_PARTY` completeness and case/diacritic handling (traseism.py:34, 303-309)

`NO_PARTY = {"NEAFILIATI", "NEAFILIAȚI", "NEAFILIAŢI", "INDEPENDENT", "NEAFILIAT"}` (traseism.py:34). Code points verified: includes both Ț (U+021A comma-below) and Ţ (U+0162 cedilla), plus ASCII T and plain "NEAFILIAT". `_party_label` (traseism.py:303-309): `raw.strip()` then `label.upper()` then membership test against already-uppercase literals. Verified on Python 3.12.3: `ț.upper() → Ț`, `ţ.upper() → Ţ`, so Romanian diacritics survive and match both set entries.

**Gaps:**
1. **Missing feminine variants:** "NEAFILIATĂ" (U+0102 Ă) and "NEAFILIATE" are not in the set. A feminine unaffiliated member (`NEAFILIATĂ`) would be treated as a real party and break the "one party switch" collapsing (party_switches traseism.py:339-400).
2. **NFD decomposition:** if raw input arrives as `T` + combining comma-below (U+0326) rather than precomposed Ț/Ţ, `.upper()` yields `T` + U+0326, which equals neither literal. Depends on upstream normalization; worth a `.strip().upper()` + `unicodedata.normalize("NFC", ...)` guard if ledger text is not NFC.
3. Case is fully handled (`.upper()` on both sides). No issue there.

---

## 5. `party_switches` unaffiliated collapsing (traseism.py:339-400)

The episode loop (traseism.py:363-381): for each membership row (sorted by start), compute `_party_label(party_short_name)`; `None` (unaffiliated) rows are `continue`d — dropped from the episode list. Consecutive rows with the same party extend the episode; otherwise a new episode starts.

`PSD → unaffiliated → PRO`: episodes = `[PSD, PRO]`; the unaffiliated stretch never becomes an episode. `zip(episodes, episodes[1:], strict=False)` (traseism.py:382) emits exactly one switch `PSD → PRO`, dated `nxt["start_date"]` = PRO join date (traseism.py:392). Covered by `test_party_view_collapses_unaffiliated_passage_to_one_switch` (test_traseism.py:229-241) — asserts exactly 1 switch for Alice, dated 2024-08-01, from_party PSD, to_party PRO.

Edge cases:
- `zip` with 0 or 1 episode yields nothing — safe. `strict=False` requires Python ≥3.10; runtime is 3.12.3, fine.
- `PSD → unaffiliated → PSD`: both rows collapse into one extended PSD episode (same party extends, traseism.py:368-371) → **no switch emitted**. Correct: returning to the same party is not a party change.
- `unaffiliated → PSD → unaffiliated`: one episode `[PSD]` → no switch. Correct (entry without exit within scope).

Subtle: `from_date` = `prev["end_date"]` (traseism.py:393) is the last membership end date of the *from* episode, which for an extended episode is the last row's end_date. Reasonable.

---

## 6. `party_summary` entries/exits (traseism.py:403-448)

Entries/exits derived from raw parties per person (not from the collapsed switch list):
- `parties = [_party_label(...) for r in items]` (traseism.py:419), `real = [p for p in parties if p]` (traseism.py:420).
- `if not real: continue` (traseism.py:421-422) — a member who is *always* unaffiliated is skipped. Correct per spec.
- Entry: `parties[0] is None and real[0] is not None` + `first_party_idx > 0` (traseism.py:424-427) — unaffiliated prefix then a party → +1 entry. Note `first_party_idx > 0` is redundant given `parties[0] is None`, harmless.
- Exit: `parties[-1] is None and real[-1] is not None` (traseism.py:429-430) — last real party followed only by unaffiliated → +1 exit.

Edge cases:
- Always-unaffiliated → skipped (covered by `if not real`). **Not tested** (seed data starts every member at a real party).
- Party → unaffiliated → party: neither entry nor exit (middle unaffiliated ignored) — consistent with "one switch" philosophy.
- Entry counted even if the first real party appears after multiple unaffiliated stretches — fine.

Denominator `members` reuses `_member_query` (traseism.py:432) with the same guards at traseism.py:440-441.

---

## 7. `derive_switch_waves` / `derive_all_switch_waves` (analytics.py:97-230)

Sliding 30-day window over `switch_party` events (`Event.type == "switch_party"` — note: **not** `switch_group`), ordered by date (analytics.py:118-123). Per chamber:

- `window_start = evs[i].event_date`, `window_end = start + 30 days` (analytics.py:159-160).
- `window_events` = all events in `[window_start, window_end]` (analytics.py:163-165).
- If `>= min_switches (3)`: attribute legislature via `KeyEvent` scan over **all** legislature key events (analytics.py:174-184 — no chamber filter on the KeyEvent query, first date-match wins), build signature `start:end:chamber:legislature` (analytics.py:89-94), skip if already in `seen_signatures` (pre-loaded from existing `SwitchWave` rows, analytics.py:148-151), else insert and `i += len(window_events)` (analytics.py:210) to avoid re-detecting the same cluster.

**Risks (confirmed, not hypothetical):**
1. **Skip-ahead skips a legitimate second wave.** After a wave is detected at index `i`, `i` jumps past *all* events in that window. A second wave whose first event falls inside the previous window is never evaluated as a window start. Only waves starting *after* the previous window's last event can be detected. Under-counting of waves is possible in dense switch periods.
2. **Signature dedup is boundary-sensitive.** Re-running with identical dates is idempotent (signature in `seen_signatures`), but changing `window_days` or shifting boundaries creates new signatures → duplicate waves for the same cluster. Dedup key should probably be content-based (e.g. sorted set of event ids) rather than window-boundary-based.
3. Legislature attribution scans all `KeyEvent` rows labelled "legislature"; if multiple KeyEvents share a label (different chambers/rows), the first chronological match wins — non-deterministic ordering if the table has duplicates (analytics.py:174-184).
4. `derive_all_switch_waves` hardcodes chambers `("deputies", "senate")` (analytics.py:226) — any other chamber value is silently skipped.

Test coverage: `test_derive_all_switch_waves_includes_open_legislature` (test_analytics.py:15-61) covers idempotency (second call returns 0) and legislature attribution, but not the skip-ahead or boundary-duplicate risks.

---

## 8. `party_switching_rates` and `generational_shift` (analytics.py:246-417)

### `party_switching_rates` (analytics.py:246-353)
- Numerator: `switch_party` events within `[period_start, period_end]`; for each switch, affected parties = from-party and to-party (resolved via `Organization.classification` and, for groups, `Membership.on_behalf_of_id` at event date, analytics.py:271-295). `party_switches[party_id][person_id] += 1` for **each** affected party → a switch between two parties increments the person's counter twice (once per party) and `total_switches` (sum over person_switches) counts the switch twice. Denominator and numerator are therefore on different counting bases (per-party-person incidences vs person-years). Whether that's intended ("switch rate per MP per year per party") is unclear; it reads like a double count of the same event.
- Denominator: memberships (`on_behalf_of_id == party_id`, group orgs) overlapping the period, tenure clipped to `[period_start, period_end]` (analytics.py:329-332):
  ```python
  clipped_start = max(start, period_start)
  clipped_end = min(end or period_end, period_end)
  if clipped_end >= clipped_start:
      tenure_days[person_id] += (clipped_end - clipped_start).days
  ```
  Tenure clipping is correct and inclusive of both endpoints. `member_ids` (analytics.py:323) is populated even when `start` is None or the clip is empty, while `total_person_years` and `avg_tenure_years` (dividing by `len(tenure_days)`, analytics.py:345-347) only include clipped tenures → `members` can exceed the population underlying the rate. Guard `if not member_ids or total_person_years <= 0: continue` (analytics.py:335-336) protects division by zero.
- `switch_rate_per_mp_per_year = total_switches / total_person_years` (analytics.py:348-350) — given the double-count note above, interpret as "party-attributed switch incidences per person-year".

### `generational_shift` (analytics.py:356-417)
- `evaluation_date = as_of or (legislature period end)` (analytics.py:364-366). With a legislature and no `as_of`, ages are computed as of the legislature end date — a "historical age at legislature close" choice, stated implicitly.
- Age calc: year difference minus 1 if month/day hasn't occurred yet (analytics.py:398-400) — correct Western age.
- Denominator per party: persons with `birth_date`, a group membership with `on_behalf_of` party, `start_date <= evaluation_date`; without a legislature filter, also `end_date >= evaluation_date` (currently serving, analytics.py:391-393). With a legislature filter there is **no end-date constraint** — anyone who ever held a group seat in that legislature is included, even if long gone by `evaluation_date`. Documented as "dated group memberships"; consistent but the two branches answer slightly different questions.
- `avg_age = round(sum/len, 1)` (analytics.py:410), `median_age` via `statistics.median` (analytics.py:411). A person with memberships in two parties appears in both parties' averages (one age per party dict, analytics.py:403) — intended for "by party" view.

---

## 9. Test coverage gaps

| Invariant / behaviour | Status | Where it should be tested |
|---|---|---|
| `members == 0` → `switch_rate == 0.0`, no crash | ❌ not tested | `traseism_summary` with empty scope |
| Distinct-person denominator (multiple rows per person) | ✅ | `test_summary_counts_switches_and_distinct_person_denominator` (test_traseism.py:210) |
| Unaffiliated collapsing `PSD → unaffiliated → PRO` = 1 switch dated at PRO join | ✅ | `test_party_view_collapses_unaffiliated_passage_to_one_switch` (test_traseism.py:229) |
| Unaffiliated variants with cedilla/comma-below/feminine (`NEAFILIAŢI`, `NEAFILIATĂ`) | ❌ not tested | `party_switches` / `_party_label` |
| Always-unaffiliated member skipped in entries/exits | ❌ not tested | `party_summary` |
| Entry (unaffiliated → party) and exit (party → unaffiliated) counters | ❌ not tested (assertions only on switches/switchers/matrix) | `party_summary` |
| Repeat switchers with 3+ switches; `max_switches` boundary | ⚠️ partial (max=2, people=2 in seed) | `traseism_summary` |
| `derive_switch_waves` skip-ahead missing a 2nd wave inside previous window | ❌ not tested | `derive_switch_waves` |
| Window-boundary changes produce duplicate signatures (non-idempotent across configs) | ❌ not tested | `derive_switch_waves` |
| `party_switching_rates` denominator = clipped tenure, guard when no tenure | ❌ not tested | `party_switching_rates` |
| `generational_shift` age boundary (birthday not yet occurred), legislature vs current-serving denominator | ❌ not tested (test_api.py:698 tests group/party join and historical age at API level only) | `generational_shift` |

### Recommendations (priority order)
1. Add tests for members=0 guard and entries/exits edge cases (always-unaffiliated skipped).
2. Extend `NO_PARTY` with feminine variants (`NEAFILIATĂ`, `NEAFILIATE`) or normalize lemmas; add NFC normalization before `.upper()` if ledger text isn't NFC.
3. Make wave dedup content-based (event id set) instead of window-boundary-based, and reconsider the `i += len(window_events)` skip-ahead (e.g. advance only to `window_end + 1`, or allow overlapping window starts) to avoid missing a second wave inside the first window.
4. Clarify `party_switching_rates` counting base: decide whether one switch between two parties counts once or twice, and align `members` with `tenure_days` population.
5. Derive `switch_party` events with the same 1-day handoff tolerance as `switch_group` (events.py:377 vs events.py:180-182) to keep the two event sets aligned.
