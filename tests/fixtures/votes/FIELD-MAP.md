# FIELD-MAP — cdep.ro / vot-parlament.ro roll-call vote fixtures

Every row below was **verified against the live source on 2026-11-20** and
locked into the fixtures in this directory. The SHA-256 of every file is in
`manifest.json`; the importer aborts if a file and its manifest entry
disagree.

Capture tool: `scripts/capture_vote_fixtures.py` (byte-exact, `PoliteClient`,
robots.txt honoured, no CAPTCHA bypass). Capture date: 2026-11-20.

---

## 1. Files

| File | Source URL | Bytes | Content (verified) |
|---|---|---:|---|
| `cdep_evot2015_day_20261118.xml` | `https://www.cdep.ro/ords/pls/steno/evot2015.xml?par1=1&par2=20261118` | 5 174 | 16 `ROW` records, all `CAMERA=2` (deputies) |
| `cdep_evot2015_day_20261110.xml` | `…/evot2015.xml?par1=1&par2=20261110` | 5 466 | 13 `ROW` records, all `CAMERA=0` (joint sitting) |
| `cdep_evot2015_nominal_37526.xml` | `…/evot2015.xml?par1=2&par2=37526` | 37 040 | 246 `ROW` records, `VOT` = 245×`DA` + 1×`-` |
| `cdep_evot2015_nominal_37526.html` | `…/evot2015.nominal?idv=37526&idl=1` | 94 774 | 246 unique profile links `structura2015.mp?idm=N&cam=2&leg=2024` |
| `cdep_evot2015_nominal_37492.html` | `…/evot2015.nominal?idv=37492&idl=1` | 95 732 | 218 unique profile links: 161×`cam=2` + 57×`cam=1` (joint vote) |
| `vot_parlament_votes_export_head.csv` | `https://vot-parlament.ro/votes/export.csv` | 27 906 | first 50 lines of the full 1.7 MB export; 22-column header + 49 data rows |
| `vot_parlament_vote_37526.json` | `https://vot-parlament.ro/votes/37526.json` | 126 897 | 8 top-level keys, 246 `positions` |
| `vot_parlament_api_votes_37526_404.html` | `https://vot-parlament.ro/api/votes/37526` | 7 213 | HTTP **404** body — the `/api/votes/*` route does not exist |

---

## 2. cdep day index — `evot2015.xml?par1=1&par2=YYYYMMDD`

**VERIFIED** — exactly 9 text elements, **no attributes**:

`VOTID`, `TIME_VOT`, `DESCRIERE`, `CAMERA`, `PREZENTI`, `NU_AU_VOTAT`,
`AU_VOTAT_DA`, `AU_VOTAT_NU`, `AU_VOTAT_AB`

| Element | Meaning (verified) | Type |
|---|---|---|
| `VOTID` | the official vote id — identical to the `idv` parameter of the nominal page | text |
| `TIME_VOT` | `DD.MM.YYYY HH:MM` local time | text |
| `DESCRIERE` | the published title of the vote (e.g. `PL-x 594/2026 - Vot final adoptare`) | text |
| `CAMERA` | `2` = Camera Deputaților, `0` = joint sitting, `1` = Senat (**day-level `1` still UNVERIFIED**) | text |
| `PREZENTI` | members present | int |
| `NU_AU_VOTAT` | present but **did not vote** | int |
| `AU_VOTAT_DA` / `AU_VOTAT_NU` / `AU_VOTAT_AB` | yes / no / abstain | int |

### Reconciliation for vote 37526 (the anchor fixture)

```
day index (20261118)      nominal XML                 cross-check (vot-parlament CSV)
PREZENTI     = 246        246 rows                    official_present      = 246
NU_AU_VOTAT  =   1        1 × VOT = "-"               official_not_voted    =   1
AU_VOTAT_DA  = 245        245 × VOT = "DA"            official_yes          = 245
AU_VOTAT_NU  =   0        0 × VOT = "NU"              official_no           =   0
AU_VOTAT_AB  =   0        0 × VOT = "AB"              official_abstain      =   0
```

**VERIFIED consequence:** the nominal token `-` means *present but did not
vote*, **not** abstain. Abstain is `AU_VOTAT_AB`, which was `0` in this vote.
The literal tokens `NU` and `AB` have **not** been observed yet — see §6.

---

## 3. cdep nominal list — `evot2015.xml?par1=2&par2=VOTID`

**VERIFIED** — exactly 6 text elements, **no attributes**:

`VOTID`, `NUME`, `PRENUME`, `GRUP`, `CAMERA`, `VOT`

* `NUME` = surname, `PRENUME` = given name(s) — the XML prints **given first**
  in the human-readable form but stores them in separate elements.
* `GRUP` = parliamentary group label as published in the nominal list.
* `VOT` = the raw token (`DA`, `-`, and — not yet observed — `NU`, `AB`).

---

## 4. cdep nominal page — `evot2015.nominal?idv=VOTID&idl=1`

This HTML page is the **only** place the official per-person identifier
(`idm`) is published. Each voting row contains:

```html
<a href="/ords/pls/parlam/structura2015.mp?idm=1&cam=2&leg=2024">Adomnicăi Mirela Elena</a>
```

* `idm` — the person's id in the chamber's structure page (the identity key).
* `cam` — `2` = deputies, `1` = senate (a joint vote lists both).
* `leg` — the legislature (`2024`).

The page also carries the group and the vote token in the same row, and links
to the machine-readable list: `…/evot2015.xml?par1=2&par2=<VOTID>` — which is
how `par1=2` was confirmed to mean *nominal list for one vote id*.

### Name join between the HTML page and the XML list

* HTML names are **surname first**: `Adomnicăi Mirela Elena`.
* XML names are **given first**: `PRENUME="Andrei"`, `NUME="Dolineaschi"`.
* Join key: `normalize_name(NUME + " " + PRENUME)` == `normalize_name(HTML name)`.
* **VERIFIED:** 246 / 246 rows of vote 37526 join on the normalized name.
* **VERIFIED trap:** the group label differs between the two views for 20 of
  the 246 rows (`neafiliat` vs `Neafiliati`, `PSD` vs `PSD(afiliat)`). The
  group is therefore **not** part of the join key; both raw values are kept.
* A name that matches more than one HTML row is **ambiguous → quarantined**,
  never guessed.

---

## 5. Encoding trap (verified 2026-11-20)

The XML prolog says `encoding="ISO-8859-2"` but the server sends
`Content-Type: text/xml; charset=UTF-8` and the **bytes are UTF-8**:

```
b"\xc4\x83" (UTF-8 "ă")  present in the file
b"\xe3"   (latin-2 "ă")  absent
```

Parsing the bytes with the prolog's declaration produces mojibake
(`DrÄ\x83goescu` instead of `Drăgoescu`). **Rule:** decode UTF-8 first, fall
back to ISO-8859-2, and never trust the prolog.

---

## 6. vot-parlament.ro contract

### CSV export (`/votes/export.csv`, HTTP header `x-truth-contract: votes-v1`)

22 columns, in this exact order:

```
platform_vote_id, native_vote_id, chamber, vote_time, native_title,
native_bill_code, native_bill_number, native_bill_year, native_bill_title,
outcome, official_present, official_yes, official_no, official_abstain,
official_not_voted, nominal_unknown_rows, official_vote_url, source_fetched_at,
native_bill_url, linked_bill_key, linked_bill_url, truth_contract_version
```

**VERIFIED trap:** the file starts with a UTF-8 **BOM** (`\ufeff`) — read it
as `utf-8-sig`, or the first column name becomes `\ufeffplatform_vote_id`.

### Vote JSON (`/votes/<id>.json`)

8 top-level keys: `bill`, `cache`, `group_breakdown`, `matter`,
`official_group_summary`, `party_breakdown`, `positions`, `vote`.

Each `positions[*]` object has 12 keys: `chamber`, `family_name`,
`given_name`, `is_duplicate_politician_in_vote`, `official_person_id`,
`party`, `party_normalized`, `politician_key`, `politician_name`,
`raw_vote_choice`, `row_number`, `vote_choice`.

**VERIFIED:** `/api/votes/<id>` returns **HTTP 404** — there is no stable JSON
API under `/api/`. The contract to assert is the CSV header + the JSON shape
above; on drift the importer reports `DATA_UNAVAILABLE` and writes nothing.

---

## 7. Identity resolution (no name matching, no fabrication)

Resolution is **identifier-only**, in this order:

1. `person_identifier(scheme='cdep_mandate', identifier='<chamber>:<leg>:<idm>')`
2. `person_identifier(scheme='cdep_idm', identifier='<idm>', legislature='<leg>')`
   — accepted **only** if that person has a `mandate` in the same chamber and
   legislature (this rejects stubs such as `idm=106`).
3. `person_identifier(scheme='cdep_person', identifier='cdep-person:<chamber>:<leg>:<idm>')`
   — same mandate check.
4. otherwise → **quarantine** (recorded in the import report, never guessed,
   never a new `person` row).

**VERIFIED against the shipped corpus** (vote 37526, 246 positions):

| Outcome | Count |
|---|---:|
| resolved via `cdep_mandate` | 146 |
| resolved via `cdep_idm` (mandate check passed) | 98 |
| resolved via `cdep_person` | 0 |
| rejected by the mandate check (quarantined) | 1 (`idm=106`) |
| unresolved (quarantined) | 2 (`idm=87`, and `idm=106` after the rejection) |

`idm=87` is not in the corpus at all — the deputy is missing from our
person table, so the position is quarantined instead of being fabricated.

---

## 8. Open items and their resolvers

| Item | Status | Resolver |
|---|---|---|
| Day-level `CAMERA=1` (senate-only sitting) | UNVERIFIED | capture `evot2015.xml?par1=1&par2=<senate-day>` |
| Literal nominal tokens `NU` and `AB` | UNVERIFIED | capture a vote whose `AU_VOTAT_NU`/`AU_VOTAT_AB` > 0 |
| Test vote `VOTID=37515` ("Vot test 1") | policy UNVERIFIED | written sign-off before a production backfill |
| `vot-parlament` "stable API" | does not exist (404) | contract test on CSV header + JSON keys; drift → `DATA_UNAVAILABLE` |
| `par1` values other than 1 and 2 | UNVERIFIED | they returned empty bodies in the 2026-11-20 probe |
