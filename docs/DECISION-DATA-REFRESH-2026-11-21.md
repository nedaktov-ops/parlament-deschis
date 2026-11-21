# Decision — automated data refresh (2026-11-21)

**Status:** OPEN, owner decision required. Not a silent skips or false green.

## What was proven by the dispatched run

`gh workflow run data.yml` → run `44909412878`. Compared with the previous
run `44908121895`:

1. The cache-seed fix worked: the previously empty runner cache was restored
   from the `pd-cdep-cache.tar.gz` asset on the pinned release.
2. `Collect and ingest (strict, with cached fallback)` **succeeded** — the
   cdep.ro `ConnectTimeout` and the "no cached source page" failure are gone.
3. Strict audit and `prepare_db.py` succeeded.
4. A new immutable release **`data-44909412878-1`** was published with
   `parlament.db`, `manifest.jsonl` and `audit-report.json`.
5. The step `Pin the release and trigger Render` then **failed**:
   `GH006: Protected branch update failed ... Changes must be made through a
   pull request ... 4 of 4 required status checks are expected`. The workflow
   retries 3 times and exits 1. Issue #14 was updated by the failure reporter
   and remains OPEN.

## Why the new release was NOT pinned

The workflow does not ingest roll-call votes; its `parlament.db` is ~22 MB and
has no vote tables. The currently pinned release
`data-20261121-votes-001` contains 189 votes / 24,682 positions and is serving
them live (`GET /api/votes total=189`). Pinning the workflow release would
silently remove the 10× centrepiece from production. That is a regression, not
a refresh.

## Decision

Keep `data-20261121-votes-001` pinned. Do not pin `data-44909412878-1`.
Issue #14 stays OPEN with this precise, evidence-backed root cause. The
supported release path remains: local rebuild → vote ingest → strict audit →
prepare → publish immutable release → pin via reviewed PR → Render deploy
(the path actually executed earlier on 2026-11-21).

## Owner options (choose one; no guessing)

| Option | What it changes | Consequence |
|---|---|---|
| A — PR-based pin | data.yml creates a branch + PR for the marker; a human/App merges after checks | Keeps protection intact; daily refresh needs a human merge step |
| B — bot bypass | ruleset allows the workflow App to bypass PR + required checks | Fully automatic; weakens protection for that actor only |
| C — vote-aware workflow | workflow also ingests votes (needs a runner-reachable source or a vote-bearing asset) | Fully automatic and no regression; largest change |
| D — keep manual path | document that scheduled refresh is best-effort; local ingest + release is canonical | No code change; issue #14 remains open by design |

## Verification of the current state

```
origin/main pin file: data-20261121-votes-001
live /api/health release_tag: data-20261121-votes-001
live /api/votes total: 189
latest GitHub release: data-44909412878-1 (NOT pinned, no vote tables)
run 44909412878 conclusion: failure (pin step only)
```

## Rollback

None needed (no pin or data change made). Pin overrides are reverted with a new
commit changing `data/latest-release.txt`; immutable release tags are never
moved or deleted.
