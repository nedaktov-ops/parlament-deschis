# Parlament Deschis

> **Unde stau aleșii tăi, în orice moment din 1990 până azi.**
> Open, source-cited tracker for the Romanian Parliament — Camera Deputaților and Senat.

[![Code license: AGPL-3.0-or-later](https://img.shields.io/badge/code-AGPL--3.0--or--later-blue.svg)](LICENSE)

**Parlament Deschis** measures **traseism**: parliamentary-group and party switching by Romanian MPs, both chambers (Camera Deputaților ~330 seats, Senat ~136 seats), across all 10 legislatures 1990–2024.

Every fact is **dated**, carries a **confidence level**, links to the **official publication** (`cdep.ro`), and points to an **archived snapshot** of the exact page it came from (SHA-256 manifest). Where the official record is incomplete, the corpus audit reports the gap rather than silently filling it.

This is a transparency tool, not a news outlet. It reports what the chambers themselves publish.

---

## What it measures

A **group switch** = the same person changes parliamentary group inside the **same chamber and the same legislature**, where the previous tenure has a published leave date and the next tenure starts on or after it. A chamber or legislature change is **not** a switch.

Two views are published:

| View | What counts | Unaffiliated bucket |
|------|-------------|---------------------|
| **Group switches** | Every change of parliamentary group | Counts as a move (in or out) |
| **Party switches** | A change of the party behind the group | Skipped — `PSD → unaffiliated → PRO` = **one** party switch |

The denominator is **members at risk**: distinct people who held a group seat in the scope — never membership rows. Switch rate = switchers ÷ members at risk.

---

## Data: real, source-cited, with known limitations

- **3,388 persons**, **7,358 memberships** (100% carry source URL + SHA-256 evidence), **7,429 events**, **1,217 switches** across all 20 scopes. Counts are from the release pinned in `data/latest-release.txt`; read that file for the current tag — do not hard-code a tag in documentation.
- Primary source: `cdep.ro` — group ledgers (`structura2015.gp`) publish dated membership intervals ("Membru din" / "până în"); MP profiles (`structura2015.mp`) link every mandate a person ever held (`idm` is per-mandate, so identity is resolved via the mandate graph, never by name).
- The group index **omits** groups that no longer exist (e.g. the 2016–2020 Deputies ALDE group). The collector probes the id space to find them: **15 hidden groups across 10 scopes**.
- The alphabetical roster (`structura2015.de?par=A`) is a second view of the same data; the three views are reconciled against each other (group page vs. index count vs. roster). **141 of 143 groups reconcile exactly**; the 2 exceptions are documented source inconsistencies.
- Cross-checked against the independent tracker `parlament.openpolitics.ro`: Ponta PSD→independent 5 Sep 2017, Sitterli 9 Oct 2017, Balint independent→PSD 1 Sep 2017, ALDE split 8 May / 20 Jun 2017 — all match cdep's dates.

---

## Run it locally

```bash
# 1. Environment
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'

# 2. Build the real corpus from cdep.ro (cached on disk; a re-run is free)
.venv/bin/python -m pipeline.cli --db data/parlament-real.db build-corpus --chamber both --cache data/cache/cdep --strict

# 3. Audit it (the gate — proves completeness and consistency)
.venv/bin/python -m pipeline.cli --db data/parlament-real.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json

# 4. Serve
.venv/bin/python -m pipeline.cli --db data/parlament-real.db serve
```

The audit runs 10 checks: mandate coverage, no overlap, every membership evidenced, switch events backed by dated tenures, scope totals, roster reconciliation, index reconciliation, interval order, no missing starts, and batched-date smells.

---

## Verify the data

```bash
.venv/bin/python -m pipeline.cli --db data/parlament-real.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json --json data/verification-report.json
```

See `docs/VERIFICATION.md` for what each check proves and the full reconciliation table.

---

## Deploy

The service is **read-only at runtime**: the SQLite database is rebuilt from the official sources and **baked into the Docker image** (free hosts have no persistent disk, and a WAL database cannot even open on a read-only filesystem).

- **Render** (free, no card): `render.yaml` — Docker runtime, `/api/health/ready` healthcheck.
- **Vercel** (SPA): `vercel.json` — static frontend, `/api/*` rewritten to the Render API host.
- **CI**: `.github/workflows/ci.yml` (pytest + ruff + frontend build + image test) and `.github/workflows/data.yml` (daily corpus rebuild, audit, publish as a GitHub release).

```bash
docker build -t parlament-deschis .
docker run -p 8000:8000 parlament-deschis
curl http://localhost:8000/api/health
```

The Docker build downloads the exact public release pinned in
`data/latest-release.txt` and verifies the GitHub asset SHA-256 before preparing
the read-only database. The data workflow revalidates current-legislature
pages daily and historical pages every 30 days by default; HTTP validators
avoid redownloading unchanged pages. New releases are published only after
source collection, database integrity, and strict audit gates pass. Updating
the pinned release marker does **not** by itself start CI or Render's Git
deployment: the push uses `GITHUB_TOKEN` (which starts neither), so the data
workflow triggers Render explicitly through its API and then verifies the
expected `dataset.release_tag` (see `.github/workflows/data.yml`). The API reports liveness at
`/api/health/live`, database readiness at `/api/health/ready`, and dataset
identity/publication metadata at `/api/health`.

---

## Licence

Code: AGPL-3.0-or-later. The scraped data is a factual record of official publications.
