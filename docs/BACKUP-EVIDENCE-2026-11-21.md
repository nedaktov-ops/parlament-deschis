# Backup evidence — Wave 0 steps W0.1–W0.3 (2026-11-21)

## Purpose

Produce a verifiable, non-destructive safety net before any Wave 1 mutation of
`parlament-deschis`, per `docs/CONTINUATION-STRATEGY-2026-11-21.md` §3 and §4:
freeze the baseline (W0.1), make an additive full backup (W0.2), and prove the
backup can be restored in a sandbox (W0.3). No repository file was mutated by
W0.1–W0.3; the only repo write is this evidence file.

- **Project root:** `/home/nedaktov/parlament-deschis`
- **Backup dir (`BK`):** `/tmp/opencode/pd-backups/w0/`
- **Sandbox restore:** `/tmp/opencode/pd-restore-w0/` (never the working repo)
- **Recorded at:** `2026-11-21T09:47:48Z` (`2026-11-21 11:47:48 EET`)
- **Authority:** read-only freeze, additive backup, sandbox-only restore. No
  commit, push, merge, deploy, branch change, `git add -A`, or destructive
  command was executed.

## Status — no unqualified success claim

The mechanical checks for W0.1–W0.3 completed with printed exit codes
(baseline SHA/divergence/pin match §0; bundle verify OK; manifest all `OK`;
restored HEAD matches). **However three anomalies are recorded and must be
acknowledged by the owner before W0 is declared GREEN.** This document is an
evidence record, not a "success" claim.

| Flag | Severity | Detail |
| --- | --- | --- |
| F1 — dirty tracked files at baseline | AMBER / STOP-condition | `git status --porcelain` showed 2 modified **tracked** files (Obsidian auto-save reformatting). See §2.1. |
| F2 — first manifest self-reference FAILED | AMBER (corrected) | First `sha256sum -c` returned `FAILED` on the live command log; regenerated manifest over backup artifacts only → all `OK`. See §3.3. |
| F3 — broken `sqlite3` CLI shim | INFO (worked around) | mise shim has no version set; used `.venv/bin/python` `sqlite3` module as the strategy's fallback. See §3.1. |

No checksum mismatch remains in the final manifest, restored HEAD equals the
recorded HEAD, and the only dirty tracked files are pre-existing and confined
to the backed-up vault. F1 is reported rather than silently accepted.

---

## 1. Raw command outputs (trimmed to relevant lines, with exit codes)

### 1.1 W0.1 Freeze — `BK/VERSIONS.txt`

Full raw transcript: `/tmp/opencode/pd-backups/w0/VERSIONS.txt`
(sha256 `cbc414dee3a4976e2c4950991ea0985e0d7ec10c26f366b1a76684c34175288b`,
verified `VERSIONS.txt: OK`, exit `0`).

```
$ git rev-parse HEAD
96e6fdd5d75c3f7f51a6888a693eeca40e954674
[exit=0]

$ git rev-list --left-right --count origin/main...HEAD
0	8
[exit=0]

$ cat data/latest-release.txt
data-20261117-T213500
[exit=0]

$ git status --porcelain
 M "Parlament Deschis Obsidian vault/.obsidian/app.json"
 M "Parlament Deschis Obsidian vault/.obsidian/core-plugins.json"
?? .nedcode/
?? docs/CONTINUATION-STRATEGY-2026-11-21.md
[exit=0]

$ git log --oneline origin/main..HEAD
96e6fdd chore(vault): regenerate notes after style fix
bc4bee2 style(vault-sync): satisfy ruff UP022 (capture_output)
bf75556 chore(vault): regenerate generated notes at stable source commit
537cef7 fix(vault-sync): anchor generated notes on last non-vault commit
a311382 feat(vault): build Obsidian state mirror with idempotent sync and lint
6fd6028 docs: exhaustive post-initial audit with contradiction resolutions
221cf78 docs: add docs-vs-live gap analysis from coordinated six-agent review
3eb3c0a fix(review): complete CI, vote API, a11y and docs gaps (2026-11-21 review)
[exit=0]

$ gh run list --branch main --limit 6
completed	skipped	Deploy verify	Deploy verify	main	workflow_run	44879971117	1s	2026-11-21T07:22:43Z
completed	failure	feat(frontend): wire vote API into statistical views	CI	main	push	44879894155	55s	2026-11-21T07:21:47Z
completed	skipped	Deploy verify	Deploy verify	main	workflow_run	44839779288	4s	2026-11-20T23:51:10Z
completed	failure	fix(votes): handle empty XML responses from cdep.ro	CI	main	push	44839683042	45s	2026-11-20T23:50:22Z
completed	skipped	Deploy verify	Deploy verify	main	workflow_run	44822037700	9s	2026-11-20T21:37:57Z
completed	failure	feat(votes): add SHA-256 snapshot_hash to vote import	CI	main	push	44821911844	49s	2026-11-20T21:37:05Z
[exit=0]

$ gh api repos/nedaktov-ops/parlament-deschis/branches/main/protection
{"message":"Branch not protected",...,"status":"404"}
gh: Branch not protected (HTTP 404)
[exit=1]   <-- EXPECTED (404)

$ gh issue view 14 --json state,number
{"number":14,"state":"OPEN"}
[exit=0]
```

### 1.2 W0.2 Backup — `BK/w02-commands.log`

Full raw transcript: `/tmp/opencode/pd-backups/w0/w02-commands.log`.

```
$ sha256sum data/parlament-real.db data/parlament.db        [before checkpoint]
0ea8c911ec302eb5d230e1bc08eaa4755928385fef4bf59aa924a6a8409e1b2d  data/parlament-real.db
29c15c305c5b58d0ee3f543d80bd6fdf0248a0b81b330abb7a80a7f92bbfbb46  data/parlament.db
[exit=0]

$ .venv/bin/python -c '... wal_checkpoint(TRUNCATE) ...'    parlament-real.db
journal_mode: [('wal',)]
wal_checkpoint(TRUNCATE): [(0, 0, 0)]
closed
[exit=0]

$ .venv/bin/python -c '... wal_checkpoint(TRUNCATE) ...'    parlament.db
journal_mode: [('wal',)]
wal_checkpoint(TRUNCATE): [(0, 0, 0)]
closed
[exit=0]

$ sha256sum data/parlament-real.db data/parlament.db        [after checkpoint]
0ea8c911ec302eb5d230e1bc08eaa4755928385fef4bf59aa924a6a8409e1b2d  data/parlament-real.db
29c15c305c5b58d0ee3f543d80bd6fdf0248a0b81b330abb7a80a7f92bbfbb46  data/parlament.db
[exit=0]

$ ls -l data/parlament-real.db data/parlament-real.db-wal data/parlament.db data/parlament.db-wal
ls: cannot access 'data/parlament.db-wal': No such file or directory
-rw-r--r-- ... data/parlament.db
-rw-r--r-- ... data/parlament-real.db
-rw-r--r-- 1 nedaktov nedaktov 0 Nov 21 11:46 data/parlament-real.db-wal
[exit=2]   <-- evidence-only `ls`; the -wal file was removed by TRUNCATE; harmless

$ git bundle create /tmp/opencode/pd-backups/w0/pre-w0.bundle --all
[exit=0]

$ cp -a data/parlament-real.db data/parlament.db data/latest-release.txt BK/
[exit=0]
$ cp -a "Parlament Deschis Obsidian vault" BK/vault
[exit=0]
$ cp -a .nedcode/qa BK/qa
[exit=0]
```

### 1.3 W0.3 Restore drill — `BK/w03-commands.log`

Full raw transcript: `/tmp/opencode/pd-backups/w0/w03-commands.log`.

```
$ git bundle verify /tmp/opencode/pd-backups/w0/pre-w0.bundle
The bundle contains these 148 refs:
  ... 96e6fdd5d75c3f7f51a6888a693eeca40e954674 HEAD
The bundle records a complete history.
The bundle uses this hash algorithm: sha1
/tmp/opencode/pd-backups/w0/pre-w0.bundle is okay
[exit=0]

$ git clone --no-local /tmp/opencode/pd-backups/w0/pre-w0.bundle /tmp/opencode/pd-restore-w0
Cloning into '/tmp/opencode/pd-restore-w0'...
[exit=0]

$ git -C /tmp/opencode/pd-restore-w0 rev-parse HEAD
96e6fdd5d75c3f7f51a6888a693eeca40e954674
[exit=0]

$ git -C /tmp/opencode/pd-restore-w0 status --short
[exit=0]   <-- empty output = clean sandbox tree

HEAD equality assertion: MATCH (restored == recorded ==
96e6fdd5d75c3f7f51a6888a693eeca40e954674)
```

---

## 2. Baseline values (W0.1) vs strategy §0

| Fact | Recorded value | §0 expectation | Match |
| --- | --- | --- | --- |
| Local HEAD | `96e6fdd5d75c3f7f51a6888a693eeca40e954674` | `96e6fdd` | YES |
| Branch | `review/completion-20261121` | same | YES |
| Divergence | `0  8` (behind ahead) | 8 ahead / 0 behind | YES |
| `origin/main` | `6b848f1d1a68ebdb21c70e06d369072704413694` | `6b848f1` | YES |
| Release pin | `data-20261117-T213500` | same | YES |
| Unpushed commits | 8 (list in §1.1) | 8 commits | YES |
| Branch protection | HTTP 404, `Branch not protected` | absent | YES |
| Issue #14 | `OPEN` | OPEN | YES |
| CI on main | 3 `failure` / 3 `skipped` in latest 6 runs | `test` failures present | YES |

### 2.1 F1 — dirty tracked files at baseline (STOP-condition anomaly)

`git status --porcelain` (exit `0`) reported two modified **tracked** files:

```
 M "Parlament Deschis Obsidian vault/.obsidian/app.json"
 M "Parlament Deschis Obsidian vault/.obsidian/core-plugins.json"
```

Evidence gathered (`git diff` exit `0`; `stat` exit `0`):

- `app.json`: only JSON array reformatting (`["_generated/", ".obsidian/"]`
  expanded to multi-line) and removal of trailing newline. No semantic change.
- `core-plugins.json`: only removal of trailing newline. No semantic change.
- Both mtimes `2026-11-21 11:14:37 +0200`; HEAD commit time
  `2026-11-21 11:06:59 +0200`. They predate this W0 session and are consistent
  with Obsidian auto-saving settings after the last vault-regeneration commit.
- Untracked entries (`.nedcode/`, `docs/CONTINUATION-STRATEGY-2026-11-21.md`)
  are the strategy/QA working files, expected for this session.

These files are inside the vault that W0.2 copied verbatim (`cp -a`), so the
backup preserves the exact working state. No file was reverted, staged, or
cleaned by this agent. **Owner must confirm these Obsidian auto-save changes are
expected** before W0 is declared GREEN; this agent does not assume it.

A concurrent process was observed holding `parlament-real.db` during preflight
(PID 2484323, `pipeline.cli ... audit-corpus --strict --baseline ...`, likely a
sibling agent). It had exited before the checkpoint ran; only the long-running
idle uvicorn server (PID 2370354) remained. No lock prevented the backup.

---

## 3. Backup artifacts (W0.2)

`BK = /tmp/opencode/pd-backups/w0/`. Generated with
`git bundle create "$BK/pre-w0.bundle" --all` and `cp -a`.

### 3.1 WAL checkpoint

`sqlite3` CLI is a **broken mise shim** (`mise ERROR No version is set for shim:
sqlite3`, exit `1`). Per strategy fallback, `.venv/bin/python` (Python 3.12.3,
SQLite 3.45.1) `sqlite3.connect(...).execute("PRAGMA
wal_checkpoint(TRUNCATE);")` was used for both DBs (both exit `0`, result
`[(0, 0, 0)]` = not busy). `parlament-real.db-wal` was 7,045,232 bytes before
preflight and 0 bytes after; `parlament.db-wal` was removed by TRUNCATE. DB
hashes before and after checkpoint are identical, so the copied DBs are
consistent and complete.

### 3.2 Top-level artifacts with checksums

| Artifact | SHA-256 |
| --- | --- |
| `pre-w0.bundle` | `89c9c175ccf074c3b2458f78c60ee9de282bdedbee3c91da2ed5d9da25ec0455` |
| `parlament-real.db` | `0ea8c911ec302eb5d230e1bc08eaa4755928385fef4bf59aa924a6a8409e1b2d` |
| `parlament.db` | `29c15c305c5b58d0ee3f543d80bd6fdf0248a0b81b330abb7a80a7f92bbfbb46` |
| `latest-release.txt` | `48e69a382a1587bd5ae2d7ecc739f3698e540aa874e987ac6c0249d5036f8fcb` |
| `VERSIONS.txt` | `cbc414dee3a4976e2c4950991ea0985e0d7ec10c26f366b1a76684c34175288b` |
| `VERSIONS.txt.sha256` | `39d37e379c5d3d92744ff16a5dbb5dfd42b4093df0989df7749d74de0e926b4f` |
| `MANIFEST.sha256` | `1a2b9bb5e3213f339d1481509943f1d12f8a1624b519324b1eb757f115a58b3d` |

Source-vs-backup DB hashes match byte-for-byte (both pairs shown in §1.2).
Bundle `git bundle list-heads` includes `96e6fdd... HEAD`, all `refs/heads/*`,
`refs/remotes/*`, `refs/tags/*` (incl. `data-20261117-T213500`), and worktree
HEADs.

### 3.3 Manifest (55 files) — F2 corrected

The **first** manifest was generated with `sha256sum "$BK"/*`-style globbing and
included the live log `w02-commands.log`. Because that log was still being
appended to during verification, `sha256sum -c` produced:

```
./w02-commands.log: FAILED
sha256sum: WARNING: 1 computed checksum did NOT match
[exit=1]
```

This is a self-referential logging artifact, **not** a corrupted backup file.
The manifest was regenerated over backup artifacts only, excluding the manifest
itself, `*.log`, and `*.sh`:

```
$ find . -type f ! -name MANIFEST.sha256 ! -name '*.log' ! -name '*.sh' -print0 \
    | sort -z | xargs -0 sha256sum > MANIFEST.sha256
MANIFEST_GEN_EXIT:0

$ sha256sum -c MANIFEST.sha256
./latest-release.txt: OK
./parlament.db: OK
./parlament-real.db: OK
./pre-w0.bundle: OK
... (all 55 lines OK: 2 qa files, 52 vault files, VERSIONS.txt,
     VERSIONS.txt.sha256) ...
[exit=0]
```

Full manifest (verbatim) is `/tmp/opencode/pd-backups/w0/MANIFEST.sha256`:

```
48e69a382a1587bd5ae2d7ecc739f3698e540aa874e987ac6c0249d5036f8fcb  ./latest-release.txt
29c15c305c5b58d0ee3f543d80bd6fdf0248a0b81b330abb7a80a7f92bbfbb46  ./parlament.db
0ea8c911ec302eb5d230e1bc08eaa4755928385fef4bf59aa924a6a8409e1b2d  ./parlament-real.db
89c9c175ccf074c3b2458f78c60ee9de282bdedbee3c91da2ed5d9da25ec0455  ./pre-w0.bundle
0a95f1c805318a24a569af2c36650e2b1064e2b29d6938fbff3b21cb944d5213  ./qa/taste-report.md
f658ac6d3d764e0d9c030980a96666bf343b969e1069736b15c287fad23fd71a  ./qa/verification-matrix.md
48d310e58146357810867669680d4b36a44e408c48849925c3d281c09a4153f3  ./vault/00-START/AGENTS.md
8c294146fd946eaeff2f1bfbf9f1441cefdbc108fe936d3137aadcc83bf1549b  ./vault/00-START/MAINTENANCE-PROTOCOL.md
c46bd5c0715a4d45e22d24c33153fac162bb3763a332c52a6f49cc4ad531ef62  ./vault/00-START/SOURCE-MAP.md
cfd18a2d9de21d9a7b59db79d363edd1bd53166cf6862b02a8432b705c054ddd  ./vault/00-START/START-HERE.md
477c8c7d029dbc2e4ebed81e447fff889ab2ce72c567c000c8614492b19d06e4  ./vault/10-STATE/CONTRADICTIONS.md
0fabcbf3cf47c7a4c169122ce074373e5daa08a69b0e79e39819c00a60885dfc  ./vault/10-STATE/CURRENT-STATE.md
23aa08336b334ec4434b84502a0a26e59abe2d438ccfab1ca86a9b0b64f4a5f6  ./vault/10-STATE/GAP-REGISTER.md
4afd09ea0f455f1d5ebc8ee8c6484332f69133ecb2736b2bcd298c64f8be001a  ./vault/10-STATE/GIT-POSITION.md
a9b1aa328c01399ae731b3872fe3afbc0c2edc356be4c05e15e77492d8f0b030  ./vault/10-STATE/RELEASE-AND-VERIFICATION.md
4d6bc9b6e485316c4ad0b4bbdac8cb27d6a527356f61d769e5f73f018e3cff75  ./vault/20-DIRECTION/CONTINUATION-STRATEGY.md
bd45ba8188a64c956eb2fcdce81829db57af066566b9163f3e56aab01bf4ed47  ./vault/20-DIRECTION/DECISIONS.md
35bb88fdd64ece57224ae05997d475e96246bc699370d813f4c512648734d27b  ./vault/20-DIRECTION/TASK-REGISTER.md
25c640bcbdf643631a6ee2189c9e648cc103249e3ee2c02e50a6e32b5228715d  ./vault/20-DIRECTION/VISION.md
1c0ef76359149856eb391e8fc0b5744804b608060c87039ed111ded22807f947  ./vault/20-DIRECTION/WAVE-STATUS.md
2960b218f061583130880c489a2306c4172804625d9e8b416771eb8922ff08d5  ./vault/30-SYSTEM/API.md
b5c3360f1df902529965be01cbfb5a2aea4dacac0e1b078d280215bd7d4389ff  ./vault/30-SYSTEM/ARCHITECTURE.md
3222d0b4df0c0d69fdafa6b56e16324f81ab483e18b9053ed46743c5fef900eb  ./vault/30-SYSTEM/DATA-MODEL.md
6a449261b695472c08ba907498790d52a6cdea984abe671e8ff633c5e63086fa  ./vault/30-SYSTEM/DATA-RELEASE-PROCEDURE.md
3aa930adb9ec2ce3abf47408b4828676aefb86da5a2efbf129b6c4998ecd99a2  ./vault/30-SYSTEM/DEPLOYMENT.md
b0123bdaf50e6dc83639b20f932c53bf2439edd86474a47074cd5701cd74b2a2  ./vault/30-SYSTEM/METHODOLOGY.md
5b5f6e9261b6e6e0ca5db3888a43a158cf73153d1bfbb4a4c533fe962a38c3fb  ./vault/40-FRONTEND/DESIGN-CONTRACT.md
fd30ec791ec5fc1b62ea3865eb17c52c3b037098d2ffabc03d35af5019561784  ./vault/40-FRONTEND/QA-AND-AXE.md
5e82066e996311000ccefc617984e1fe7aad3300911655af615f31ac47ea140e  ./vault/40-FRONTEND/STACK-AND-TOKENS.md
9f022a4dba121a1662826ebda8ec83562cf2d042b2d972440806c4676a850224  ./vault/50-RESEARCH/DATA-ENRICHMENT.md
f8f98bd199be7a52157cee50c9675c97623d3ad4a10901d80f34d1bd2bf5337b  ./vault/50-RESEARCH/RESEARCH-LOG.md
0052a9e0a4520756ebca3f230bedd3a97cd8bf34e04b2a12dc5ba2e5b1ceeafc  ./vault/50-RESEARCH/SOURCE-RESEARCH.md
9c6cf0e74ca60bc139e7c19e012c5f28a931de5b8d77f4df583529a9c4279150  ./vault/60-EVIDENCE/AUDIT-2026-11-21.md
5472104308b89cb1f6d0035367f504ea55186cbe79ff5b05769bbf37aa878fe8  ./vault/60-EVIDENCE/COMPREHENSIVE-REVIEW-2026-11-21.md
82cd395f7dc0c93b1a6efc5bb68ae84962e9c818f36fe93798f9462bba365e19  ./vault/60-EVIDENCE/DASHBOARD-VERIFICATION-2026-11-19.md
b8344f7d3492e0fb7dc99208174dc69e401c580bc4a8092a8f06db048ff4be32  ./vault/60-EVIDENCE/GAP-ANALYSIS-2026-11-21.md
6a5d9b593ec6fa34e1422b3054ab264508d7052ab1f091c52692ef79cb8d118d  ./vault/70-ARCHIVE/COMPLETION-CERTIFICATE.md
5485a0c61ae83547a0db3c1074c4bb032677b1a8d6faf9c1c81b7e841bc43d95  ./vault/70-ARCHIVE/STRATEGY-BLUEPRINTS-HISTORICAL.md
6f94577e88c7e4451980624a4c03e0f54029083b95a0dd9f8e48d622281af1a0  ./vault/_generated/releases.md
12168a27e0d2596c2a03f74791ec632ef58e260117c4106cee2d7c5e4c63d589  ./vault/_generated/routes.md
4eefdc6117490046a6048e3e779cfde1957519d6d0ce9c45e0c8c6a661f574f5  ./vault/_generated/source-map.md
a95370d53c25c995e67bd8ca2f4bdd9a492b8908b622a4f49bcbf77faedd7bf2  ./vault/_generated/status.md
af9f260a582a02ae63568c27d7492ab084505c615cea65f34856ba13315498bf  ./vault/_generated/tests.md
a5f9b276bc28dfabf018b0cb53044b65c5e099585af766a66d495919675822bd  ./vault/.obsidian/appearance.json
2f24025494349e05945fd64cfc876d0f2ca58c16f45bebf520323c6180a2c72a  ./vault/.obsidian/app.json
0343639fac1511a32a4c9a92c7655a6e9f9ad3a600fc6f30b5bdad6806160a97  ./vault/.obsidian/bookmarks.json
1479c5f06ac4061db3c5e4fb8934c521d321c5394501ac688a50b9150521b0be  ./vault/.obsidian/core-plugins.json
59e40291073cc35d83000681159addef084981c9e99d345378e139053f611115  ./vault/.obsidian/daily-notes.json
291c110034b39179680eeffef2620a0693d82d506609a7d5c30e772ae8e3e464  ./vault/.obsidian/graph.json
393f96d6332dfc05f25eb19dc0cb3c75f8c924696b1b35349e4c6672e3c3a712  ./vault/.obsidian/templates.json
593efaf5cf298c2d109221555727517c66a5672e1184f2bdf648932f970b40b5  ./vault/.obsidian/workspace.json
fab17e7b08509c570284aed5a081693b8f3db0412e6d80249578bf46dadfed99  ./vault/Templates/Daily.md
ad2efe9dfb1305997cf1ded18f08f86fb044df48a1951ed5b2115b20e68a1305  ./vault/Templates/Decision.md
faabd2d7ca8146492fc2e77e196c7e0eef26778e38bdc4c652ea1944ed04aaaf  ./vault/Templates/State-Note.md
11d983c0075b42dba8b18db602101a90aa37d47fe54e2596221169d4e9a28671  ./vault/Templates/Task.md
39f5d5028b47d67a7615e26a8c7c72c09d34aebd23f064572c6821081de80f07  ./vault/vault.json
cbc414dee3a4976e2c4950991ea0985e0d7ec10c26f366b1a76684c34175288b  ./VERSIONS.txt
39d37e379c5d3d92744ff16a5dbb5dfd42b4093df0989df7749d74de0e926b4f  ./VERSIONS.txt.sha256
```

---

## 4. Restore-drill result (W0.3)

- `git bundle verify` → **exit 0**: "The bundle records a complete history",
  "pre-w0.bundle is okay", 148 refs, sha1.
- `git clone --no-local ... /tmp/opencode/pd-restore-w0` → **exit 0**.
- Restored `HEAD` = `96e6fdd5d75c3f7f51a6888a693eeca40e954674` → **exit 0**,
  equals recorded HEAD (§2). `HEAD_MATCH=YES`.
- `git -C /tmp/opencode/pd-restore-w0 status --short` → **exit 0**, empty output.
- The working repo at `/home/nedaktov/parlament-deschis` was not touched by the
  clone (separate path; `--no-local` used).

---

## 5. Rollback instructions

**Never** use `git reset --hard`, `git push --force`, branch deletion, or tag
moves (strategy §1 rule 3).

1. **Revert a committed code change** (after W0.2 the pre-W0 HEAD is
   `96e6fdd5d75c3f7f51a6888a693eeca40e954674`):
   ```
   cd /home/nedaktov/parlament-deschis
   git revert <sha>          # one normal commit per bad commit; no history rewrite
   ```
   For a merge commit use `git revert -m 1 <merge-sha>`.

2. **Restore from the W0 bundle into a fresh sandbox / recover a ref:**
   ```
   BK=/tmp/opencode/pd-backups/w0
   git bundle verify "$BK/pre-w0.bundle"
   git clone --no-local "$BK/pre-w0.bundle" /tmp/opencode/pd-restore-<wave>
   git -C /tmp/opencode/pd-restore-<wave> rev-parse HEAD   # expect 96e6fdd...
   git -C /tmp/opencode/pd-restore-<wave> status --short   # expect empty
   ```
   To recover a single ref into the working repo without overwriting HEAD:
   ```
   git -C /home/nedaktov/parlament-deschis update-ref \
       refs/heads/recovery-w0 96e6fdd5d75c3f7f51a6888a693eeca40e954674
   ```

3. **Restore DB / pin / vault / QA files** (additive copy back, preserving the
   backup originals):
   ```
   cd /home/nedaktov/parlament-deschis
   cp -a "$BK/parlament-real.db" data/parlament-real.db
   cp -a "$BK/parlament.db"      data/parlament.db
   cp -a "$BK/latest-release.txt" data/latest-release.txt
   cp -a "$BK/vault/."           "Parlament Deschis Obsidian vault/"
   cp -a "$BK/qa/."              .nedcode/qa/
   ```
   Verify with `sha256sum -c "$BK/MANIFEST.sha256"` (after copying, the restored
   paths equal the backed-up files; re-hash at destination if needed).

4. **Revert a dataset release pin** (strategy §3): create a new commit restoring
   the previous `data/latest-release.txt` value; never edit/delete an immutable
   tag such as `data-20261117-T213500`.

---

## 6. Residual / next owner action

- Owner must acknowledge F1 (the two Obsidian auto-save config diffs) before
  W0 is declared GREEN; W0.4–W0.6 were not executed by this agent.
- F2 is documented and corrected; the final manifest verifies all 55 artifacts
  `OK` with exit `0`.
- F3 is a tooling environment issue (mise `sqlite3` shim unset) — any future
  wave must use the `.venv/bin/python` fallback or set a mise version.
- No git state was changed: no commit, no ref update, no staging, no push by
  this agent.
- **Concurrent sibling agents:** after the W0.1 freeze, `git status --porcelain`
  showed additional tracked modifications (`docs/DASHBOARD-STRATEGY.md`,
  `docs/remediation/WAVE-4-RECIPES.md`, `docs/remediation/WAVE-4-STRATEGY.md`,
  several vault notes) and new untracked vault notes. These correspond to
  W0.4–W0.6 being executed in parallel and are **not** from W0.1–W0.3. The W0.2
  bundle (committed refs) and the `cp -a` vault/DB copies are a point-in-time
  snapshot taken before those edits; restoring from this backup will revert
  those sibling changes. Re-run a fresh backup before any later destructive
  step if those changes must be preserved.
