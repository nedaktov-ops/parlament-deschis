# Contributing

Mulțumim că vrei să contribui. / Thank you for contributing.

Parlament Deschis is a civic data project. The most valuable contributions are **accurate
facts with an official source**, **captured fixtures for pages the parsers do not yet
handle**, and **tests that make temporal or identity behavior safer**. Hype, unsourced
claims, and “helpful” date guessing are not accepted.

---

## 1. Development setup

### Requirements

- Python **3.12+**
- Node.js **18+** and npm (frontend)
- Git
- No live network access is needed to run the test suite

### Python environment

The repository ships a working `.venv`. To use it directly:

```bash
source .venv/bin/activate
pytest
ruff check .
```

To create a fresh environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e '.[dev]'
```

If `uv` is available, the equivalent is:

```bash
uv sync --extra dev --locked
```

Do not commit `.venv/`, `__pycache__/`, `.pytest_cache/`, or `.ruff_cache/` — they are
gitignored.

### Initialize a development database

```bash
.venv/bin/parlament init
.venv/bin/parlament ingest-fixtures
.venv/bin/parlament stats
```

Use a separate database for experiments:

```bash
.venv/bin/parlament --db /tmp/parlament-dev.db init
```

### Run the backend and frontend

The API uses `data/parlament-real.db` by default. Build that corpus first (see the README)
or set `PARLAMENT_DB` to another database explicitly.

```bash
# terminal 1
PARLAMENT_DB=data/parlament-real.db .venv/bin/parlament serve --host 127.0.0.1 --port 8000
# (if `serve` is not wired in your checkout)
PARLAMENT_DB=data/parlament-real.db .venv/bin/uvicorn backend.main:app --reload --port 8000

# terminal 2
cd frontend
npm install
npm run dev
```

The Vite dev server runs at <http://localhost:5173> and proxies `/api` and `/snapshots` to
port 8000 by default. To use a backend on another port, set
`PARLAMENT_API_PROXY_TARGET`, for example:

```bash
PARLAMENT_API_PROXY_TARGET=http://127.0.0.1:8001 npm run dev
```

---

## 2. Test-first expectations

- **Write or update a test before changing behavior.** This is especially important for
  parsers, date handling, identity resolution, reconciliation, and event derivation.
- A bug fix should include a regression test that fails on the old code and passes on the
  new code.
- A parser change should include a **real captured fixture** (see §3) and a test that
  exercises the changed structure.
- A schema change should include tests for the affected queries and an update to
  [`docs/DATA-MODEL.md`](DATA-MODEL.md).
- A methodology change (fact rule, confidence, coverage threshold, merge rule) requires an
  update to [`docs/METHODOLOGY.md`](METHODOLOGY.md) and a note in the PR.

Run the full suite before opening a PR:

```bash
.venv/bin/pytest
.venv/bin/ruff check .
```

Targeted runs while developing:

```bash
.venv/bin/pytest tests/test_cdep_group.py -q
.venv/bin/pytest tests/test_reconcile.py tests/test_identity.py -q
.venv/bin/pytest tests/test_ingest_integration.py -q
```

### Test rules

- **No live network calls in tests.** Tests must run offline and deterministically.
- Prefer in-memory SQLite (`get_session(":memory:")`) or `tmp_path` databases.
- Do not assert on today's date or on wall-clock timestamps; use fixed dates.
- Do not weaken an assertion to make a test pass. If the expected behavior is unclear, open
  an issue or ask in the PR.
- Keep tests focused: one behavior per test, with a name that states the behavior.

---

## 3. Parser fixture policy

Parsers are only as good as the HTML they have seen. The fixture directory is
`tests/fixtures/`.

When adding a fixture:

1. **Capture the real official page** (Camera Deputaților group ledger, Senat profile,
   Senat group roster, etc.). Do not hand-edit the HTML to make the parser pass.
2. Save it with a descriptive name:
   `tests/fixtures/cdep_group_<acronym>.html`,
   `tests/fixtures/senat_fisa_<name>.html`,
   `tests/fixtures/senat_grup.html`.
3. Record the source URL and capture date in the test docstring or a short `README` next to
   the fixture. The fixture itself should remain byte-faithful to the capture where
   possible.
4. Add a parser test that asserts the **meaningful** fields: names, identifiers, dates,
   precision, roles, and organization classification. Do not assert on incidental
   whitespace or on a whole-page snapshot unless that is the point of the test.
5. If the page contains personal data that is not already public on the official page,
   stop and raise it in the PR. The project only republishes what the chamber publishes.

Fixture capture is a manual, polite operation:

- Use a normal browser or a single `curl` request; do not run a crawler.
- Respect `robots.txt` and the site's terms.
- Do not capture pages behind a CAPTCHA or a login.
- Keep the capture small: one group ledger, one profile, one roster.

The test suite must not fetch the fixture URL at runtime. The committed HTML is the input.

---

## 4. Style

### Python

- Ruff is configured in `pyproject.toml`: line length **100**, target **py312**, rules
  `E`, `F`, `I`, `UP`, `B`, with `E501` ignored.
- Run `ruff check .` before committing. `ruff check --fix .` is acceptable for import
  order and safe autofixes; review the diff.
- Use type hints on public functions and dataclasses.
- Keep parser functions pure: HTML in, dataclasses out, no database or network access.
- Use `ApproxDate` for anything date-like from a source. Do not pass raw date strings
  through the pipeline.
- Preserve Romanian diacritics in user-facing strings and source labels. Normalize only
  for matching keys.
- Comments should explain *why* a rule exists (especially temporal or identity rules), not
  restate the code.

### TypeScript / frontend

- TypeScript is `strict`, with `noUnusedLocals` and `noUnusedParameters`. `npm run lint`
  runs `tsc --noEmit`; fix the types rather than casting to `any`.
- `npm run build` must pass before a frontend PR is merged.
- Keep API types in `frontend/src/api/client.ts` in sync with the backend response shapes.
- UI strings belong in `frontend/src/i18n.ts`, with both `ro` and `en` entries. Romanian is
  the default; English is a full translation, not a partial fallback.
- Do not query the chamber websites from the browser. The frontend reads only the local
  API.

### Documentation

- Update the relevant document when behavior changes: `docs/ARCHITECTURE.md` for data
  flow, `docs/API.md` for endpoints, `docs/DATA-MODEL.md` for schema, `docs/METHODOLOGY.md`
  for fact rules, and `README.md` for commands or setup.
- Code examples in docs must be runnable. If a command changes, change the docs in the
  same PR.
- Keep Romanian diacritics in Romanian text and examples.

---

## 5. Responsible scraping rules

These are non-negotiable. A PR that weakens them will not be merged.

- **Honor `robots.txt`.** The client checks it per host and raises when a URL is
  disallowed. Do not add a bypass.
- **Keep at least one second between requests per host.** The default client pause is
  **2.5 s**. Do not lower it below 1 s, and do not parallelize requests to the same host.
- **Identify the project** in the `User-Agent`. Do not impersonate a browser to evade
  anti-bot measures.
- **Use conditional GET** (`ETag`, `Last-Modified`) and skip unchanged content.
- **Respect `429`** and `Retry-After`; do not hammer a source after a rate limit.
- **Stop on a CAPTCHA or challenge page.** Never solve, outsource, or bypass it. Record the
  failure in `pipeline_run` and let the health indicator show it.
- **Do not use a headless browser** to defeat a challenge or to render around an access
  control.
- **Do not scrape personal data** that is not already published on the official page.
- **Do not commit** the database, snapshots, or exports. They are generated and
  gitignored.
- **Use `--limit`** for a first live run against a source, and prefer `--force` only when
  you intend to re-parse unchanged pages.

If a source changes its terms or asks the project to stop, stop that source and document
it in the methodology and PR.

---

## 6. Commits and pull requests

### Commits

- Keep commits focused: one logical change, with tests and docs where applicable.
- Use a short, scoped subject. Examples:
  - `parser: handle Senat profile history table without a header`
  - `reconcile: keep closed tenure immutable on re-ingest`
  - `api: add evidence snapshot URL fallback`
  - `docs: document end-exclusive intervals`
- Explain *why* in the body when the change is not obvious. Link the official source or
  issue when the change is data-related.
- Do not mix formatting-only changes with behavior changes.

### Pull requests

A good PR description answers:

1. **What changed?** The behavior, not just the files.
2. **Why?** The bug, the source page change, or the civic use case.
3. **Evidence.** The official URL, the captured fixture, and the test that proves it.
4. **Impact.** Any schema, API, export, or methodology change.
5. **Verification.** The commands you ran and their result.

Before requesting review:

```bash
.venv/bin/pytest
.venv/bin/ruff check .
cd frontend && npm run lint && npm run build
```

For a data correction, include:

- the official page URL;
- the exact old and new values;
- the snapshot hash if you captured one;
- a note on whether the correction affects a closed tenure, a merge, or coverage.

### Review expectations

- Reviewers check correctness against the official source, not only code style.
- A parser change without a fixture is incomplete.
- A temporal change without a test is incomplete.
- A schema change without a `docs/DATA-MODEL.md` update is incomplete.
- A methodology change without a `docs/METHODOLOGY.md` update is incomplete.

---

## 7. Licensing of contributions

By contributing code, you agree that your contribution is licensed under
**AGPL-3.0-or-later**. By contributing data or fixtures, you agree that the generated data
is licensed under **CC-BY-4.0** and that the fixture may be committed for testing.

Do not paste large excerpts from non-official sources. Official chamber pages are cited and
archived for verification; their copyright remains with the respective chamber. If you are
unsure whether a capture is permissible, ask before committing it.

See:

- [`LICENSE`](../LICENSE)
- [`data/licenses/README.md`](../data/licenses/README.md)
- [`docs/METHODOLOGY.md`](METHODOLOGY.md)

---

## 8. Where to start

Good first contributions:

- Add a captured fixture for a page that currently fails to parse.
- Add a parser test for a role or date format that is not covered.
- Improve an error message when a source page changes shape.
- Add a coverage note for a term where the badge is `partial`.
- Fix a documentation command that no longer matches the CLI.
- Translate a missing RO/EN string in `frontend/src/i18n.ts`.

If you are unsure where a change belongs, open an issue with the official URL and a short
description. A precise question with evidence is more useful than a large speculative PR.
