# The 11-step source onboarding recipe

*A newbie-safe guide to adding a new public data source to Parlament Deschis
without breaking the evidence, audit or licence culture.*

This project is a public record. People make decisions about politicians from
it. That means one thing above all: **every number must be traceable to the
page it came from**. This recipe is the checklist that guarantees it.

You do not need to be a data engineer. Work through the steps in order; each
one has a "done when" test you can run yourself. If a step is unclear, stop
there and ask — never guess.

---

## Step 1 — Check the licence first

**What to do.** Find the licence page of the source. Copy the exact wording
into the licence register. Decide one of three classes:

| Class | Meaning | Allowed? |
|---|---|---|
| **COPY** | CC0, CC BY 4.0, OGL-ROU-1.0 | Yes — the values may be stored and republished, with the attribution string |
| **CROSS-CHECK** | NonCommercial (NC), ShareAlike (SA), or unverified | No — the values may only be *displayed* as an external benchmark, never copied into our dataset or an export |
| **CONDITIONAL** | The licence depends on the file, the version or a permission that we do not have yet | Treat as CROSS-CHECK until the permission exists in writing |

**Why first.** If the licence forbids copying, everything else you build is
wasted work — and copying anyway would poison the whole dataset.

**Done when.** The source has a row in `tests/fixtures/votes/LICENSE-APPENDIX.md`
*and* in `pipeline/licenses.py` with its licence ID, URL, quote, verification
date and attribution string.

**Never.** Do not assume a source is free because it is public. Do not assume a
CC BY source is compatible with our AGPL-licensed code without reading §5.

---

## Step 2 — Check `robots.txt` and pace yourself

**What to do.** Fetch `https://<host>/robots.txt` and read it. Note the
disallowed paths. Then:

* use `pipeline.sources.client.PoliteClient` — it sends our identifying
  User-Agent, honours `robots.txt`, paces requests (≥ 1 per second) and
  **stops** on a CAPTCHA page instead of trying to bypass it;
* never request a disallowed path;
* keep a low request rate and cache everything.

**Why.** A blocked or overloaded official server is a real cost for a
public institution, and it can get our project blocked permanently.

**Done when.** The path you intend to fetch is not disallowed, and the fetch
goes through `PoliteClient`.

**Never.** Never solve or bypass a CAPTCHA. Never parallelise requests to the
same host. Never fetch `/declaratii/` on cdep.ro (explicitly disallowed).

---

## Step 3 — Fetch the raw page into a fragment

**What to do.** Store the **raw bytes** of the response, with the URL and a
SHA-256 checksum, using `pipeline.fragments.record_fragment`.

**Why.** The raw snapshot is the evidence. If the page changes tomorrow, we
can still prove what we saw today — and re-run every parser against it.

**Done when.** A fragment row exists with `source_url`, `checksum` and a
snapshot path.

**Never.** Never store a re-encoded string as the "raw" page. cdep.ro sends
UTF-8 bytes while its XML prolog claims ISO-8859-2; re-encoding changes the
bytes and breaks the checksum (this is a real trap — see
`tests/fixtures/votes/FIELD-MAP.md` §5).

---

## Step 4 — Write a parser and lock it with a fixture

**What to do.** Put the pure parsing logic in `pipeline/parse/<source>.py`
(no network calls inside a parser). Capture one real page as a fixture under
`tests/fixtures/` and write a unit test that asserts the exact parsed values.

**Why.** Parsers are where "looks right" becomes "is right". A fixture plus
an exact-value test means the next person cannot silently change the
interpretation of a field.

**Done when.** The test passes and asserts concrete values (counts, ids,
field names) — not just "it parsed something".

**Never.** Never write a parser that has no fixture. Never guess a field's
meaning: verify it against the raw bytes and, if you can, against a second
independent view of the same data.

---

## Step 5 — Write to the target table with provenance

**What to do.** Every row carries where it came from: `source_url`,
`confidence` (how sure we are), `precision` (day/month/year) and a
`dedup_key`.

**Why.** "Trustworthy" means a reader can click through to the official
page. A number without a URL is an opinion.

**Done when.** No row in the new table has a null `source_url`.

**Never.** Never overwrite a stronger value with a weaker one
(`official_ledger` beats `official_profile` beats `derived` beats
`community`). Never silently fill a gap with a guess.

---

## Step 6 — Use `dedup_key` for idempotency

**What to do.** Give every row a deterministic natural key — for example
`source:native_vote_id` — and use it to detect "already imported".

**Why.** The pipeline runs daily. Running it twice must not double the data.
It also makes the import safe to re-run after a failure.

**Done when.** Importing the same source twice produces the same row count
and the same keys. Test it.

**Never.** Never use a timestamp, a UUID or a random value inside a dedup
key — the key has to be reproducible.

---

## Step 7 — Add a CLI subcommand, dry-run first

**What to do.** Add `parlament <your-command>` in `pipeline/cli.py`, following
`cmd_enrich` / `cmd_assets`: it must support a **dry run** that prints what
it *would* do and writes nothing.

**Why.** A dry run turns "I hope this is safe" into "I can see exactly what
it will do, and nothing has changed yet".

**Done when.** Running the command without the write flag leaves the database
byte-identical, and the write flag has to be explicit.

**Never.** Never default a destructive command to writing. Never let a
command ignore its `--db` argument.

---

## Step 8 — Update the audit

**What to do.** Register a new check in the `CHECKS` map in `pipeline/audit.py`.
The check must fail when the new data is missing or inconsistent — for
example a row without a source URL, or counts that do not reconcile.

**Why.** The audit is the project's safety net. A source that silently
produces garbage must stop the release, not decorate it.

**Done when.**

```bash
uv run python -m pipeline.cli audit-corpus --strict
```

reports the expected baseline (currently **275 known errors, 0 new errors**)
and your new check appears in the check list.

**Never.** Never weaken an existing check to make a new source pass. If a
genuine defect appears, baseline it deliberately in the same commit, with a
written reason.

---

## Step 9 — Only then wire it into the daily workflow

**What to do.** Add the step to `.github/workflows/data.yml`, with its **own
cache key**, and make it fail soft (`continue-on-error`) if the source is
third-party.

**Why.** If a third-party site is down at 03:17 UTC, the official corpus
must still ship. One broken source must never block the daily dataset.

**Done when.** The official build still succeeds when the new source returns
HTTP 500, and the workflow reports the source as unavailable rather than
crashing.

**Never.** Never let a new source sit in the critical path of the official
build without a fallback.

---

## Step 10 — Update the documentation in the same commit

**What to do.** Update `docs/DATA-MODEL.md`, `docs/RESEARCH.md`,
`docs/VERIFICATION.md` (and the licence appendix) in the **same commit** as
the code.

**Why.** Documentation that lags the code is worse than no documentation:
readers will trust a number whose meaning has already changed.

**Done when.** A newcomer reading only the docs can tell where a field came
from, what it means and how fresh it is.

**Never.** Never ship a code change and explain it "later".

---

## Step 11 — Publish a release and let the pipeline prove it

**What to do.** Publish a new dataset release, pin it in
`data/latest-release.txt`, let the deploy pipeline run, and verify the live
API serves the new tag.

**Why.** The release pipeline is the only thing that proves the change works
in production, not just on your laptop.

**Done when.** The live health endpoint reports the new dataset tag and the
new numbers are visible on the site.

**Never.** Never edit a published release. Releases are immutable; a mistake
is fixed by publishing a new one.

---

## The one-page checklist

```
[ ] 1  licence checked and registered      → row in LICENSE-APPENDIX.md + pipeline/licenses.py
[ ] 2  robots.txt checked, PoliteClient    → path allowed, requests paced
[ ] 3  raw bytes stored as a fragment      → source_url + sha256
[ ] 4  parser + fixture + exact-value test → test asserts real values
[ ] 5  provenance on every row             → source_url / confidence / precision / dedup_key
[ ] 6  deterministic dedup_key             → re-running does not duplicate
[ ] 7  CLI subcommand, dry-run default     → dry run writes nothing
[ ] 8  audit check registered              → audit-corpus --strict still 275/0
[ ] 9  daily workflow, own cache key       → third-party failure cannot block the build
[ ] 10 docs updated in the same commit     → no stale field meanings
[ ] 11 release published and verified      → live API serves the new tag
```

## Rollback for every step

| Step | Rollback |
|---|---|
| 1 | remove the licence row; nothing was ingested yet |
| 2 | stop the fetcher; nothing was stored |
| 3 | delete the fragment rows and the snapshot files (`data/snapshots/<source>/`) |
| 4 | `git revert <commit>` — fixtures and test go together |
| 5 | delete the rows by `source_name`; re-run the importer from the last good release |
| 6 | rebuild the table from the fragments (the raw snapshots are still there) |
| 7 | `git revert <commit>` |
| 8 | `git revert <commit>` (never leave a check unregistered) |
| 9 | remove the workflow step; the corpus build is independent |
| 10 | `git revert <commit>` |
| 11 | re-pin `data/latest-release.txt` to the previous tag and re-run the release verification |

## A worked example: the roll-call votes (Wave 1)

| Step | What it looked like |
|---|---|
| 1 | cdep.ro facts = OGL-ROU-1.0 (COPY); vot-parlament.ro = CC BY but `ai-train=no` → CROSS-CHECK only |
| 2 | `www.cdep.ro/robots.txt` disallows `/declaratii/` only; vote feeds are allowed |
| 3 | fixtures captured byte-exact by `scripts/capture_vote_fixtures.py`, SHA-256 in `manifest.json` |
| 4 | `pipeline/parse/cdep_votes.py` + `tests/test_votes_cdep_parser.py` (exact counts, exact tags) |
| 5 | `vote.source_url` + `vote_position.source_url` + `dedup_key` on every row |
| 6 | `vote.dedup_key = "<source>:<native_vote_id>"`, `vote_position.dedup_key = "<vote_key>:<person_id>"` |
| 7 | `parlament votes-import --fixtures …` — dry run by default, `--apply` writes |
| 8 | `check_vote_evidence` registered in `pipeline/audit.py` |
| 9 | **not in Wave 1** — no workflow wiring yet; the build-isolation test proves the corpus build never touches votes |
| 10 | `docs/MASTER-INTEGRATION-BLUEPRINT.md` §5, `FIELD-MAP.md`, `LICENSE-APPENDIX.md` |
| 11 | **deferred to Wave 2**, after the production backfill has been reviewed |
