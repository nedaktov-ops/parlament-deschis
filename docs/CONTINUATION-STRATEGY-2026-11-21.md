# Continuation Strategy — Parlament Deschis (2026-11-21)

**Mandate.** No guessing, no assumptions, no presumptions. Every claim is backed
by code, a command with printed output, a git fact, a live probe, or a cited
source. If evidence is absent, record `NOT PROVEN` with a named resolver.
Work is real, non-destructive, versioned on GitHub, and gated by evidence.

**Method.** Five read-only strategy agents worked in parallel: S1 (evidence
inventory), S2 (GitHub best practice), S3 (missing-data acquisition), S4
(wave/rollback design), S5 (QA/security gates). Their reports are distilled
here; every step below inherits their evidence.

## 0. Verified baseline (do not assume the vault's older numbers)

| Fact | Verified value | Source |
|---|---|---|
| Local HEAD | `96e6fdd`, branch `review/completion-20261121` | `git rev-parse HEAD` |
| Divergence | **8 ahead / 0 behind** `origin/main` (`6b848f1`) | `git rev-list --left-right --count origin/main...HEAD` |
| Unpushed commits | `3eb3c0a, 221cf78, 6fd6028, a311382, 537cef7, bf75556, bc4bee2, 96e6fdd` | `git log origin/main..HEAD` |
| Release pin | `data-20261117-T213500` | `data/latest-release.txt`, live `/api/health` |
| CI on main | `test` failure ×6 recent runs; `audit`/`evidence-guards` success; `docker` skipped | `gh api .../check-runs`, `gh run list` |
| Branch protection | **absent** (HTTP 404) | `gh api .../branches/main/protection` |
| Issue #14 | OPEN, 11 failed data runs, `ConnectTimeout` to `www.cdep.ro` | `gh issue view 14`, run `44729831051` log |
| Local gates | pytest 384, ruff clean, lint 0 errors, build 0, audit 275/0, doc-truth 0, UI 24/24 local / 23/24 live, vault lint + sync clean | `scripts/` gates, 2026-11-21 |
| Production | no vote data (`/api/votes total=0`), canonical ideology 404, live bundle `index-D61EXxHz.js` | live curl probes |

Vault notes still carry mixed `source_commit` values (`6fd6028` ×35, `bc4bee2`
×5) and "3 ahead" wording — W-DV-01 corrects this before planning continues.

## 1. Governing rules and authority

1. Evidence over assertion; `NOT PROVEN` beats a guessed PASS.
2. One fact, one home; hubs link, never duplicate status.
3. Never `git push --force`, `git reset --hard`, branch deletion, or tag moves.
   Rollback = `git revert <sha>` or a new pin commit; backups are additive tags.
4. Owner-only actions are marked 🔒: merge to main, branch protection, secret
   settings, releases, workflow_dispatch, deploys, product-policy decisions.
   Agents STOP and ask rather than presume authority.
5. An unavailable check reports `NOT PROVEN` and fails a required gate; no
   `|| true`, `continue-on-error`, silent skips, or auto-accepted baselines.
6. Licence/quarantine first: NC/SA/UNVERIFIED sources are display-only; every
   imported row carries `source_url` + SHA-256 + `dedup_key`; identity by exact
   ID → auto, name+DOB → propose, name alone → review; never name-only merges.
7. No attendance score; group-semantics reads always filter
   `Organization.classification == 'group'`.

## 2. Master gate table

| ID | Command | Expected | Waves | Waiver |
|---|---|---|---|---|
| G01 | `.venv/bin/python -m pytest -q` | 384 passed, 0 failed | all | owner, dated |
| G02 | `.venv/bin/ruff check backend pipeline scripts tests` | All checks passed | all | owner |
| G03 | `cd frontend && npm run lint` | 0 errors | 1+ | owner |
| G04 | `cd frontend && npm run build` | exit 0 | 1+ | owner |
| G05 | `bash scripts/check-doc-truth.sh` | false-claims: 0 | all | none |
| G06 | strict audit `--baseline data/reference/corpus-audit-baseline.json` | 275 known / 0 new | 2+ | none (reviewed change only) |
| G07 | `node scripts/check_livefeed_props.mjs` | exit 0 | all | owner |
| G08 | `python3 scripts/ui_validate.py <dev-server>` | 24/24, 0 JS, 0 axe | 1+ | owner (never waive a deliverable route) |
| G09 | `python3 scripts/vault_sync.py --check && python3 scripts/vault_lint.py` | clean | all | owner |
| G10 | `git diff --check` | empty | all | none |
| G11 | `sha256sum -c <backup manifest>` | all OK | all | none |
| G12 | live `gh pr checks <n>` | 4/4 SUCCESS | 1+ | owner |

No wave starts until the previous wave's gate is GREEN and its output is
printed. AMBER = blocked on an owner decision; RED = stop and revert.

## 3. Backups and rollback (mandatory before every mutation)

```
BK=/tmp/opencode/pd-backups/<wave>
mkdir -p "$BK"
sqlite3 data/parlament-real.db "PRAGMA wal_checkpoint(TRUNCATE);"
sqlite3 data/parlament.db "PRAGMA wal_checkpoint(TRUNCATE);"
git bundle create "$BK/pre-<wave>.bundle" --all
cp -a data/parlament-real.db data/parlament.db data/latest-release.txt "$BK/"
cp -a "Parlament Deschis Obsidian vault" "$BK/vault"
sha256sum "$BK"/* > "$BK/MANIFEST.sha256"
sha256sum -c "$BK/MANIFEST.sha256"          # every line OK
git clone --no-local "$BK/pre-<wave>.bundle" /tmp/opencode/pd-restore-<wave>
git -C /tmp/opencode/pd-restore-<wave> rev-parse HEAD   # exact SHA
```
Rollback of a code commit: `git revert <sha>` (never rewrite history). Rollback
of a dataset release: new commit restoring the previous value of
`data/latest-release.txt`, never editing/deleting an immutable tag.

## 4. Wave 0 — Safety, versioning, backups (must be GREEN first)

| Step | Action | Checkpoint | Rollback / backup |
|---|---|---|---|
| W0.1 | Freeze baseline: HEAD, divergence, pin, CI, PR list into `BK/VERSIONS.txt` | exact values match §0; `sha256sum` recorded | read-only |
| W0.2 | Full backup bundle + DB copies + vault copy + manifest | `git bundle verify` OK; `sha256sum -c` all OK | additive only |
| W0.3 | Restore drill into `/tmp/opencode/pd-restore-w0` | restored HEAD = `96e6fdd` | sandbox clone |
| W0.4 | Replace destructive rollback recipe in `docs/DASHBOARD-STRATEGY.md` with `git revert` / `git checkout <tag> -- <path>`; drop nonexistent `npm test` gate; align WCAG AA and approved palette | `grep -nE 'reset --hard|origin --force|origin --delete|npm test|WCAG AAA|violet' docs/DASHBOARD-STRATEGY.md` → 0; G05 green | `git revert <sha>` |
| W0.5 | Resolve the four-way Vite version conflict (`WAVE-4-RECIPES.md`, `WAVE-4-STRATEGY.md`) against shipped `^6.0.0`; cite `fb95e56` | `grep -rn 'Vite 8\|\^5\.0\.0' docs/remediation` → historical only | `git revert <sha>` |
| W0.6 | Re-anchor vault notes to real HEAD/8-ahead; add this strategy note | `grep -rn '3 ahead\|6fd6028' vault` → historical only; G09 green | `git revert <sha>`; regenerate vault |

**Wave 0 GREEN** = backup + restore drill + G05/G09/G11.

## 5. Wave 1 — Land the already-made local fixes

| Step | Action | Owner? | Checkpoint | Rollback |
|---|---|---|---|---|
| W1.1 | Full local gate sweep G01–G10 + UI 24/24 | no | all exit 0, printed | none |
| W1.2 | Push `review/completion-20261121`; open PR to `main` (8 commits) | **authorized this session** | `gh pr list --head ...` → PR | close PR, retain remote branch |
| W1.3 | Watch PR checks; fix RED with new normal commits only | no | `gh pr checks` 4/4 SUCCESS | `git revert <fix-sha>` |
| W1.4 | Merge PR to `main` (pre-tag `w1-before-merge`) | 🔒 owner, **not in this session** | main SHA changes; checks green | `git revert -m 1 <merge-sha>` |
| W1.5 | Enable branch protection with required `test/audit/docker/evidence-guards` | 🔒 owner | protection API 200 | owner reverses setting |
| W1.6 | Verify Render (backend) first: no `/api/api`, ideology 200 with `meta` | 🔒 deploy | curl/jq assertions | platform rollback dry-run then real |
| W1.7 | Verify Vercel (frontend) second: new bundle hash, 24/24 live | 🔒 deploy | hash ≠ `index-D61EXxHz.js`; UI 24/24 | platform rollback |
| W1.8 | Record evidence (bundle hashes, PR SHA, check list, hashes) | no | G05 + `git diff --check` green | `git revert <sha>` |

**Session outcome:** W0.1–W0.6, W1.1–W1.3 and W1.8 were executed. The branch was
pushed and PR #48 opened; all four required checks passed (`test`, `audit`,
`docker`, `evidence-guards`). W1.4–W1.7 are prepared as owner/deploy runbooks
and deliberately NOT performed — production still serves the pre-fix bundle
and backend. Evidence: `docs/GATE-EVIDENCE-2026-11-21.md`,
`docs/BACKUP-EVIDENCE-2026-11-21.md`.

## 6. Wave 2 — Data completeness and release (recipe specs; next session)

Ordered by dependency (S3 evidence):

1. **W2.1 Licence register** — wire `ensure_source_licenses()` into a tested CLI
   path; seed 15 rows before `prepare_db.py`; add `check_license_quarantine`.
   Gate: `select count(*) from source_license` → 15; `tests/test_source_licenses.py`
   green; forged SA row rejected. Ownership: `pipeline/licenses.py`, `pipeline/cli.py`,
   `tests/test_source_licenses.py`, `pipeline/audit.py`.
2. **W2.2 Honest coverage dimensions** — add `dimension` to coverage so votes and
   biographies show `none`/`partial` before data exists. Gate: `/api/coverage`
   contains all dimensions. Ownership: `pipeline/coverage.py`, `backend/routers/api.py`, tests.
3. **W2.3 cdep acquisition reliability** — retry/backoff at `PoliteClient`, warm
   action cache, offline rebuild fallback; keep `--strict`. Gate: offline
   build exit 0 on a copy; issue #14 closes after a green run. Ownership:
   `pipeline/sources/client.py`, `.github/workflows/data.yml`.
4. **W2.4 Vote release** — dry-run `ingest-votes` on a copy, `--apply` after
   approval, repair 4 NULL snapshot hashes, strict audit 0 new, publish immutable
   release, pin marker, 🔒 trigger Render, live `/api/votes total>0`.
5. **W2.5 Label discrepancies** — 1,217 group-only / 785 party / 2,002 total and
   7,358 raw vs 7,349 prepared in `docs/API.md`, `README.md`, UI wording.
6. **W2.6 CHES/Party Facts** — fix `ChesSource.ingest_ches` committing inside dry
   run first; then `--apply`; verify `party_ideology` rows >0.
7. **W2.7 Senate profiles / genealogy** — 🔒 identity-risk and source decisions;
   no name-only identity; no undeclared mergers.

Each step gets a standalone recipe: ID, exclusive file list, precondition,
exact commands, printed checkpoint, `git revert` rollback, backup path, and a
`NOT PROVEN` clause. No step touches another step's files.

## 7. Wave 3 — Vision gaps (recipe specs; later)

W3.1 genealogy (source decision first); W3.2 Senate profiles (copy-DB bit-identity
gate); W3.3 multi-dimensional coverage; W3.4 frontend H3-D/H4-A + dead code +
7 lint warnings + one missing `type="button"`; W3.5 docs/vault truth pass;
W3.6 decide the 60 s poll vs "on release" alert semantics (🔒 product call);
W3.7 resolve GraphQL 404 (diagnose locally, then 🔒 deploy).

## 8. Wave 4 — Hardening (recipe specs; later)

W4.1 staging load-test evidence; W4.2 CSP enforcement decision (report-only is
not protection); W4.3 blog/donations drop-or-scope decision (🔒 recipient);
W4.4 Vercel Cron watchdog; W4.5 end-to-end `verify-deploy.sh` + freshness gate.

## 9. GitHub hardening sequence (owner-only where marked)

Safe order (S2): (1) backup refs; (2) push branch/PR [done this session];
(3) get CI green; (4) triage 9 PRs without bulk-close; (5) 🔒 block force-push
and deletion, no required checks yet; (6) 🔒 require PR + 1 approval; (7) 🔒 add
required checks "loose" after 7 green days; (8) 🔒 strict + include admins;
(9) 🔒 secret scanning/push protection/Dependabot alerts; (10) 🔒 release
immutability for future tags. Keep SHA-pinned actions; `permissions: {}` by
default; never require `data.yml` checks on PRs (scheduled/dispatch-only).

## 10. Missing-data acquisition rules (S3)

- Official cdep facts only (`OGL-ROU-1.0`); hash raw bytes (prolog lies about
  encoding); unresolved vote positions quarantined, never name-matched.
- External civic source, Party Facts, CHES, Wikidata = licensed cross-check or
  CC0/CC-BY sources; NC/SA (IPU, V-Dem, SER-PROM, V-Party, OpenSanctions)
  display-only. PolPaL licence NOT PROVEN — do not ingest.
- Dry-run on copies; verify group outputs bit-identical; `prepare_db.py` must
  yield `journal_mode=DELETE`; never weaken `--strict`.
- If no licence-complete genealogy source exists, DROP the feature from the
  vision rather than infer links.

## 11. Agent recipe template (for every step of every wave)

```
ID / ROLE         stable step id + specialist agent type
INPUTS            project root, vault path, baseline SHA, backup path
PRECONDITION      previous wave/step gate GREEN (print evidence)
EXCLUSIVE FILES   exact list; everything else is a side-quest -> REJECT
STEPS             numbered, each with exact command
CHECKPOINT        raw output + exit code; NOT PROVEN if unavailable
ROLLBACK          git revert <sha> / pin revert; never reset or force-push
BACKUP            BK path + sha256 manifest, verified before first edit
NO-FALSE-GREEN    no || true, no skip; missing tool = NOT PROVEN
SIDE-QUESTS       none; report any anomaly instead
REPORT            command output, changed files, residual, next owner action
```

## 12. Sources

S1–S5 raw reports were delivered in-session; key external references:
[GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule),
[required status checks troubleshooting](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks),
[immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases),
[secure use of Actions](https://docs.github.com/en/actions/reference/security/secure-use),
[Playwright accessibility testing](https://playwright.dev/docs/accessibility-testing),
[SLSA verifying artifacts](https://slsa.dev/spec/v1.2/verifying-artifacts),
[test pyramid](https://martinfowler.com/articles/practical-test-pyramid.html).
