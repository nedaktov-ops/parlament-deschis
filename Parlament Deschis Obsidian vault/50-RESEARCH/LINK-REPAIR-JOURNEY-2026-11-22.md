---
id: LINK-REPAIR-JOURNEY
type: research
title: "Link and button repair — journey log (2026-11-22)"
description: "Running record of the repair programme: wave entry state, backups, checkpoint SHAs, gate output, supervisor verdicts and vault write-backs for each wave."
status: in-progress
authority: canonical
tags: [type/research, lifecycle/active, domain/frontend]
source_paths: [frontend/src, scripts, .github/workflows/ci.yml]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Link and button repair — journey log

Strategy: [LINK-REPAIR-STRATEGY](../20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md) ·
Recipes: [LINK-REPAIR-RECIPES](../20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md) ·
Supervision: [LINK-REPAIR-SUPERVISION](../20-DIRECTION/LINK-REPAIR-SUPERVISION-2026-11-22.md) ·
Investigation: [CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md).

**Programme state: W0 safety baseline executed; W1 (first code-editing wave) next.**

## Phase S — strategy design (this phase)

Grounded at HEAD `8811216`, `origin/main` identical, product tree clean, with the
investigation vault notes uncommitted (exact paths enumerated at run time by
L-00; an early draft of this note said "11", which was an unproven count).
Gates and CI were read from
`frontend/package.json:6-12` and `.github/workflows/ci.yml:17-154`. A live
`curl -L` probe upgraded one investigation item: `https://github.com/parlament-deschis`
returns HTTP 404 while `https://github.com/nedaktov-ops/parlament-deschis`
returns HTTP 200, so the `About.tsx:6` literal is BROKEN, not merely inconsistent.

Authored in the vault before any repair action:

- [LINK-REPAIR-STRATEGY](../20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md) — principles, scope, eight waves, backup/rollback, gates, supervisor contract, GitHub policy.
- [LINK-REPAIR-RECIPES](../20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md) — 18 bespoke recipes L-00…L-17 with exclusive file lists, exact anchors, checkpoints and rollbacks.
- This journey note — one section added per wave as it runs.

**Gate S:** `python3 scripts/vault_lint.py`, `python3 scripts/vault_sync.py --check`,
`bash scripts/check-doc-truth.sh` and `git diff --check` were run after authoring;
output recorded in the final session report.

### Supervisor audit and corrections (same phase)

The [supervisor protocol](../20-DIRECTION/LINK-REPAIR-SUPERVISION-2026-11-22.md)
audited the draft strategy and recipes and produced 16 findings (S-01…S-16).
Before W0, the lead accepted and applied every blocking correction:

| Finding | Correction applied |
|---|---|
| S-01 (two owners of `LiveDashboard.tsx` in W2) | L-04 and L-05 are one agent, two atomic commits with one shared gate; the wave table names one owner |
| S-02 (i18n.ts multi-owner) | Single i18n owner per wave: W2 L-03, W3 L-07 (all three keys), W4 L-13 (all three keys), W5 none; published in strategy §4.1 |
| S-03 (L-02 delete-keys branch) | Branch deleted; L-02 always renders the link, L-15 keeps the keys |
| S-05 (W3 lacks `LiveDashboard.tsx`) | Added explicitly with L-09 as sole W3 owner |
| S-06 (placeholder file lists) | W4/W5 files enumerated by full repo-relative path in strategy §4 and recipes L-14/L-15 |
| S-07 (broken i18n gate path) | All checkpoints use `cd …/frontend && npm run i18n:check` |
| S-08 ("11 notes" count) | L-00 enumerates exact paths at run time and decides disposition of modified `START-HERE.md` |
| S-09 (`git branch -D`) | `git branch -d` first; `-D` only under verified-bundle conditions |
| S-12 (evidence separation) | Every wave note requires titled **Code evidence** / **Browser evidence** sections |
| S-13 (L-16 anchor pattern) | Third pattern `href="/…"` added, with pre/post count and exit-code contract |
| S-14 (ellipses in commands) | Fully expanded absolute paths required; L-00 checkpoint rewritten |
| S-15 (`wave.start_date` unguarded) | Changed to `wave?.start_date ?? clamped` |
| S-04, S-10, S-11, S-16 | Accepted as written / ADEQUATE; retained |

The four ownership contradictions S-01/S-02/S-05/S-06 are resolved in the
corrected register at strategy §4.1. No code file has been edited in this phase.

## Wave W0 — safety baseline

Reference: [LINK-REPAIR-STRATEGY](../20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md) §5 · [LINK-REPAIR-RECIPES](../20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md) L-00.

### Entry identity (captured before any branch creation or backup)

```console
$ git branch --show-current
main
$ git rev-parse HEAD
88112168237e5c37841b785dccd2375f6cc40115
$ git rev-parse origin/main
88112168237e5c37841b785dccd2375f6cc40115
$ git status --short
 M "Parlament Deschis Obsidian vault/00-START/START-HERE.md"
?? "Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md"
?? "Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md"
?? "Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-SUPERVISION-2026-11-22.md"
?? "Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C01-SHELL-2026-11-22.md"
?? "Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C02-OVERVIEW-2026-11-22.md"
?? "Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C03-ENTITIES-2026-11-22.md"
?? "Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C04-VOTES-2026-11-22.md"
?? "Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md"
?? "Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C06-DESTINATIONS-2026-11-22.md"
?? "Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C07-HARNESS-2026-11-22.md"
?? "Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md"
?? "Parlament Deschis Obsidian vault/50-RESEARCH/CLICK-INVESTIGATION-JOURNEY-2026-11-22.md"
?? "Parlament Deschis Obsidian vault/50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md"
?? "Parlament Deschis Obsidian vault/60-EVIDENCE/CLICK-BROWSER-OBSERVATIONS-2026-11-22.md"
```

`HEAD` equals `origin/main` exactly. Every working-tree entry is under `Parlament Deschis Obsidian vault/`; **no product-code path** (`frontend/`, `backend/`, `data/`, `pipeline/`, `scripts/`, `.github/workflows/`) is modified. The single modified tracked file, `Parlament Deschis Obsidian vault/00-START/START-HERE.md`, was explicitly decided to be committed with the baseline (supervisor S-08). Enumerated by exact path (status code from `git status --short` above):

- `Parlament Deschis Obsidian vault/00-START/START-HERE.md`
- `Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md`
- `Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md`
- `Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-SUPERVISION-2026-11-22.md`
- `Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C01-SHELL-2026-11-22.md`
- `Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C02-OVERVIEW-2026-11-22.md`
- `Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C03-ENTITIES-2026-11-22.md`
- `Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C04-VOTES-2026-11-22.md`
- `Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md`
- `Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C06-DESTINATIONS-2026-11-22.md`
- `Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C07-HARNESS-2026-11-22.md`
- `Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md`
- `Parlament Deschis Obsidian vault/50-RESEARCH/CLICK-INVESTIGATION-JOURNEY-2026-11-22.md`
- `Parlament Deschis Obsidian vault/50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md`
- `Parlament Deschis Obsidian vault/60-EVIDENCE/CLICK-BROWSER-OBSERVATIONS-2026-11-22.md`

### Backup — created BEFORE the branch

ROOT: `/tmp/opencode/backups/link-repair/W0`. Full commands, with expanded absolute paths (supervisor S-14):

```bash
mkdir -p /tmp/opencode/backups/link-repair/W0
git bundle create /tmp/opencode/backups/link-repair/W0/pre.bundle --all
git rev-parse HEAD > /tmp/opencode/backups/link-repair/W0/pre.sha
git status --porcelain > /tmp/opencode/backups/link-repair/W0/pre.status
tar -czf /tmp/opencode/backups/link-repair/W0/worktree.tgz -C /home/nedaktov/parlament-deschis --exclude=.git --exclude=node_modules --exclude=.venv --exclude=.next --exclude=dist .
(cd /tmp/opencode/backups/link-repair/W0 && sha256sum pre.bundle pre.sha pre.status worktree.tgz > SHA256SUMS)
git bundle verify /tmp/opencode/backups/link-repair/W0/pre.bundle
tar -tzf /tmp/opencode/backups/link-repair/W0/worktree.tgz >/dev/null
(cd /tmp/opencode/backups/link-repair/W0 && sha256sum -c SHA256SUMS)
```

Manifest `SHA256SUMS` (verbatim):

```text
cbc26418f17f9b981fe6af2adeb5806b4245c69bc203e8820f3149225b10c93d  pre.bundle
11f0f7c2f884fc218a36a6dba8e8c388ee0ebb385bb623912a2364d7987bcbd7  pre.sha
db5e52faee4e5679b07d88b8ad421685cdfb117c6cb6df3b3131ca38494f1321  pre.status
c948fd249c8c10ec3cdc84591a5fe43419af4076918001770a7cb804b0d44bbe  worktree.tgz
```

Verification outputs — all three commands exited 0, recorded verbatim before the first edit:

`git bundle verify /tmp/opencode/backups/link-repair/W0/pre.bundle` → exit 0:

```text
The bundle contains these 203 refs:
479f5511a8351dbe225298af35f9226b5c08b5e9 refs/agents/80aa5903-4dbc-426b-a11f-e12fa2f4b8a2/checkpoints/turn/0
7fa58a6bef4667bb2d2161e665b01448e8752c42 refs/agents/9960f273-0c86-466d-9e54-452df0ba330e/checkpoints/turn/0
83df24ddff336f6b58fe60c8a3584a8d96c7e244 refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/0
fae3a16b39c6ba6dd50de79972b946c443b90e7d refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/1
193d911a3e917b616f4a5e2f043244066dcffb8d refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/10
7a0e6475cc6e55497040cfa65255247a94f959b9 refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/11
94c3109efce17edd45634c7fb461bcedf2c43626 refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/12
b4cb0ea0b48a2a70b2f77c619035d9e6bee5d47a refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/13
a514c7177939d109f0b5b3702ad0af5895ebecdf refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/14
945ecc4f8a1213265ea67708b52af68e2c1a5f98 refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/15
5a0e7fa73834f4dec4f1ae8b1658fdc0ef1e3758 refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/16
5552d73d8b5412bbac2aa177fbe665f5808b1252 refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/17
d5f495f9856c77ddf5186366a72234b1877a9016 refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/18
ad77b5e2ace255a652722f347f62030b293809c6 refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/19
6e1f0810d2a064cba4d9a4150caa6c94f6af1737 refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/2
6eebecf0374a7db455029f2de8f20e29eae20233 refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/20
a41f1dcbe4ba47885fe7dd428bd7b92ad330cb0c refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/21
5924ab665676512049ed0a018732ca291df1aef4 refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/3
93b2719997a2ba427d9712ef171568261e30217f refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/4
e59df9b32c5d3ed505ec9446664d6887e42e3cb1 refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/5
065f4dc074b4746926dc84089656e44c80f164ca refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/6
12215e2706aff1546cb2d4c628625e45a2456ac7 refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/7
3a8348f2950d7ff39dd5bb7ff7c996bd9d0f1e71 refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/8
57918e410fb858c50acda7fa06991ecc7bae91df refs/agents/a2e73f7a-fd88-4db8-b9e7-b4525b7df6bf/checkpoints/turn/9
20040a3f190b14287b316eec097b839867746a32 refs/heads/baseline
81198d63d7d4b56205cba9529ca4750afa351294 refs/heads/chore/platform-ops
2a092dcea481ccb46638be65bff66102ad59b5dc refs/heads/chore/vault-resync
b34d519a53a1f98de5a7f16476a2741900b21780 refs/heads/chore/vault-resync2
e2669205c24971b63e0c3480635a76c15846ad05 refs/heads/chore/vault-resync3
e74337f20bf90791c908ae9aff37acd1769e48a6 refs/heads/chore/vault-resync4
91e283a1d6290a6f562f5d84b7b67ef4fc5ed851 refs/heads/design/hero-brand-mark
6cdff5385fdb987036d68c504a7b36ae592aa36a refs/heads/docs/action-plan
7a6bcb47bdbb935a58bcb1a9781d9488d9101f7f refs/heads/docs/data-refresh-decision
00f5c9d19222c3de7675f2531d233dba7c347c80 refs/heads/docs/docker-fix-record
5ecbd0753d7b130187084deebfc02498a312fde8 refs/heads/docs/execution-log
849c05e8ce41276c3075c1060f558d0b35638f46 refs/heads/docs/frontend-audit
93ade75ce5b67ebb1ed1a580b0428ae1ed4cf391 refs/heads/docs/next-actions
71a14d6a931a7c26a99abecd8eb3b36b5042e12c refs/heads/docs/production-release-evidence
600f0b67bba9627f50640611e61d5eb9717b5b4e refs/heads/docs/repair-recipes
b94ed9e51f9cbdb45b33838461f26c475bcc595e refs/heads/docs/research-fleet
80d91a90eb332e8affc74e740de38c1fb65aab78 refs/heads/docs/triad-audit
b488a66f6c6c4e8c0b66cb906ab9aaf9124c6dfb refs/heads/docs/vercel-mcp-proof
b672b158def315b1f7dea175d693d3e7d25d073b refs/heads/feat/next-actions-wave
73ec7f9974f2bf0cb5cabe3a84d7dbbe52af3c59 refs/heads/fix/data-cache-seed
67e6176aa6e2b92592d0444387703e755062eca0 refs/heads/fix/data-completeness-recovery
23b6ef3921d63667e5859651889cbce947fffb42 refs/heads/fix/data-release-completeness
b731ac3ceeb43e11b75a3a5447e42a9f2e52dc3c refs/heads/fix/deploy-dispatch
f7223fca5dceadb4aa82446cb57533a0c1e80cf2 refs/heads/fix/deploy-sync
fb6bb0d139cedf8ac5e67f4fb8a9b77c19f96f60 refs/heads/fix/deploy-sync-v2
33fab41d49209bb2e99c7934570e58acd1a9bde3 refs/heads/fix/deploy-verify-skip-vercel
58a9752ef4f1a995bb38c8fbfa8c922bd5c28b5d refs/heads/fix/docker-authenticated-download
af80b559a20b875141c5cb1a56a5c32973a7edfa refs/heads/fix/pin-release-20261117
bef18e1a501a757fe5b423cc367ac8d7d3954b3a refs/heads/fix/ui-gate-settle
0f9d88c231585724287cf0f3b35372434ef98adf refs/heads/fix/ui-vote-states
7568a38547817f17c06d5476d5b266b75ea237a2 refs/heads/fix/vault-sync-stable
56c3be575881488bb28d127f789f1ff53159be39 refs/heads/fix/wal-startup-guard
4576126263e86a7a45e91390168dcd44817f5e51 refs/heads/ingest/committee-events
5f66fc2182b9191340dd8f98c053fda701b355f0 refs/heads/ingest/senate-historical-discovery
20dbf8f88c742055d6c6426c98bd7349f89a110a refs/heads/ingest/senate-post-support
88112168237e5c37841b785dccd2375f6cc40115 refs/heads/main
20040a3f190b14287b316eec097b839867746a32 refs/heads/master
1e26d9afb8feb8b94af7fb3cc3bf8e07385d6b90 refs/heads/policy/w28-release-prep
fa83b62f10eea3e6ee62f67f4fc788779e797794 refs/heads/release/pin-votes-001
dd463d18e830c3881e2a02ee0513952493f4ed26 refs/heads/remediation/D0.1
23b5b81b8c133ef7648acbccdb1106b15e40aba1 refs/heads/remediation/D0.2
1d72d06f9ee18ddec1cc3aada796ff03f7a74772 refs/heads/remediation/D0.3
eb069d2b1de953a89489245ef6418a66a7b652ba refs/heads/remediation/D0.4
75da6eb39a6e8bb8bb3431bf1735fe53cd0957ae refs/heads/remediation/D2.1
eb069d2b1de953a89489245ef6418a66a7b652ba refs/heads/remediation/D3.1
1005060cdccd7061a9a9656614117086121f6fee refs/heads/remediation/D4.1
e042961409f4d9b83e6c6dd08d20a974de457b00 refs/heads/remediation/D4.2
eb069d2b1de953a89489245ef6418a66a7b652ba refs/heads/remediation/D4.3
58ec23fc4662d21215c3966ba624b5e0d39f4f94 refs/heads/remediation/INTEGRATION-SUP
587307de0dd742af145828ba7dbdf4c7ebbf15e0 refs/heads/remediation/INTEGRATION-SUP2
0a42bea7f5052b7cf3f6a4074e325d8976959968 refs/heads/remediation/INTEGRATION-SUP3
1fcd577e8aa08e42e4fb4b8bfd614a024e04a526 refs/heads/remediation/P0-1
d7fb3c77336050402968353afe3cc36d2425b6ec refs/heads/remediation/P0-2
74f20f7a05cfcc4d1199633c8e476cc81db4c548 refs/heads/remediation/P0-3
d56456c8ff543e31d975fa62ae7b7d48d287aad4 refs/heads/remediation/P0-4
f46c660ef5142e20fab4eeb430c77d444e1158ff refs/heads/remediation/P0-5
76ed2754477023a31cd6268b2d28acb1e490835b refs/heads/remediation/P0-6
2aa54014ae3aabd23650d1ba9603cb22cbc552a5 refs/heads/remediation/P0-7
d43bd3546cb51c82d4f66d1135f62edce6bcf6a8 refs/heads/remediation/W2-A
3f7a17ed25c5cff53347551c13d946cccea18c5e refs/heads/remediation/W2-B
c97573568cc860558560178c89ff9ef6ca62abec refs/heads/remediation/W2-C
2bbb85e4175b3ef1cf7358d872c0fcefd5e9aaca refs/heads/remediation/W2-D
7444c7b0fc267e21be80516860a7f0ec004d64cd refs/heads/remediation/W2-E
427a77c57a53933751ff8b5e55a91432cf7fc00b refs/heads/remediation/W5
eb069d2b1de953a89489245ef6418a66a7b652ba refs/heads/remediation/base
f1a45083c4e14ba50883ed7bc681ced1f4087978 refs/heads/remediation/wave2-base
3615ba083a0baf57ca904c07ec86db62313eafc6 refs/heads/repair/w0-safety
841617707250df78b3ff37d61fc89a15869553cf refs/heads/review/completion-20261121
43b2796362f1793f761838065095606d5c6149aa refs/heads/w5-deployment-squash
12ca8965d8401f3091ea94617b21bf280d47a9a9 refs/heads/wip/week-1-data
7bcf551aa8a788e53c318ee0c129c52d709817be refs/heads/wip/week-2-ui
52e054c8654d323f72fbd1e461884ec4f1bc3e65 refs/heads/wip/week-3-analytics
e5709106d7b540a529e7bc5a8fe0fec023e4d84d refs/heads/wip/week-4-polish
f47f9df25d587885f67121d15846f30d15f68273 refs/remotes/origin/add-deploy-job
20040a3f190b14287b316eec097b839867746a32 refs/remotes/origin/baseline
81198d63d7d4b56205cba9529ca4750afa351294 refs/remotes/origin/chore/platform-ops
2a092dcea481ccb46638be65bff66102ad59b5dc refs/remotes/origin/chore/vault-resync
b34d519a53a1f98de5a7f16476a2741900b21780 refs/remotes/origin/chore/vault-resync2
e2669205c24971b63e0c3480635a76c15846ad05 refs/remotes/origin/chore/vault-resync3
e74337f20bf90791c908ae9aff37acd1769e48a6 refs/remotes/origin/chore/vault-resync4
4fcaaea551d2ac60c09559145fc43e02938273e0 refs/remotes/origin/dependabot/docker/node-25-alpine
d35caa1f665cfdf44efdea39282f11e696886c71 refs/remotes/origin/dependabot/docker/python-3.15-slim
9c17d39929ce2765076256c29466cf26650ef7ea refs/remotes/origin/dependabot/github_actions/actions-7a048e5329
d43d0bb21f0f3dc84bf17a694e8238cf9506221b refs/remotes/origin/dependabot/npm_and_yarn/frontend/frontend-minor-patch-b91de917a0
36b7105d41e9a6f8639a62bfcfb55820d5b3bfcd refs/remotes/origin/dependabot/npm_and_yarn/frontend/i18next-27.0.1
472076cb1936114a2545c4fc7c6fe2157bc06156 refs/remotes/origin/dependabot/npm_and_yarn/frontend/react-i18next-18.0.0
dc020aef8799f602560bd8a34bc91d17e4713e79 refs/remotes/origin/dependabot/npm_and_yarn/frontend/tailwindcss-4.3.5
91e283a1d6290a6f562f5d84b7b67ef4fc5ed851 refs/remotes/origin/design/hero-brand-mark
6cdff5385fdb987036d68c504a7b36ae592aa36a refs/remotes/origin/docs/action-plan
7a6bcb47bdbb935a58bcb1a9781d9488d9101f7f refs/remotes/origin/docs/data-refresh-decision
00f5c9d19222c3de7675f2531d233dba7c347c80 refs/remotes/origin/docs/docker-fix-record
5ecbd0753d7b130187084deebfc02498a312fde8 refs/remotes/origin/docs/execution-log
849c05e8ce41276c3075c1060f558d0b35638f46 refs/remotes/origin/docs/frontend-audit
93ade75ce5b67ebb1ed1a580b0428ae1ed4cf391 refs/remotes/origin/docs/next-actions
71a14d6a931a7c26a99abecd8eb3b36b5042e12c refs/remotes/origin/docs/production-release-evidence
600f0b67bba9627f50640611e61d5eb9717b5b4e refs/remotes/origin/docs/repair-recipes
b94ed9e51f9cbdb45b33838461f26c475bcc595e refs/remotes/origin/docs/research-fleet
80d91a90eb332e8affc74e740de38c1fb65aab78 refs/remotes/origin/docs/triad-audit
b488a66f6c6c4e8c0b66cb906ab9aaf9124c6dfb refs/remotes/origin/docs/vercel-mcp-proof
b672b158def315b1f7dea175d693d3e7d25d073b refs/remotes/origin/feat/next-actions-wave
73ec7f9974f2bf0cb5cabe3a84d7dbbe52af3c59 refs/remotes/origin/fix/data-cache-seed
67e6176aa6e2b92592d0444387703e755062eca0 refs/remotes/origin/fix/data-completeness-recovery
23b6ef3921d63667e5859651889cbce947fffb42 refs/remotes/origin/fix/data-release-completeness
b731ac3ceeb43e11b75a3a5447e42a9f2e52dc3c refs/remotes/origin/fix/deploy-dispatch
f7223fca5dceadb4aa82446cb57533a0c1e80cf2 refs/remotes/origin/fix/deploy-sync
fb6bb0d139cedf8ac5e67f4fb8a9b77c19f96f60 refs/remotes/origin/fix/deploy-sync-v2
33fab41d49209bb2e99c7934570e58acd1a9bde3 refs/remotes/origin/fix/deploy-verify-skip-vercel
58a9752ef4f1a995bb38c8fbfa8c922bd5c28b5d refs/remotes/origin/fix/docker-authenticated-download
8bce18e3cf7940939b2304ab30c9c2e24a822166 refs/remotes/origin/fix/frontend-ux-h1-fix
af80b559a20b875141c5cb1a56a5c32973a7edfa refs/remotes/origin/fix/pin-release-20261117
bef18e1a501a757fe5b423cc367ac8d7d3954b3a refs/remotes/origin/fix/ui-gate-settle
0f9d88c231585724287cf0f3b35372434ef98adf refs/remotes/origin/fix/ui-vote-states
7568a38547817f17c06d5476d5b266b75ea237a2 refs/remotes/origin/fix/vault-sync-stable
56c3be575881488bb28d127f789f1ff53159be39 refs/remotes/origin/fix/wal-startup-guard
4576126263e86a7a45e91390168dcd44817f5e51 refs/remotes/origin/ingest/committee-events
5f66fc2182b9191340dd8f98c053fda701b355f0 refs/remotes/origin/ingest/senate-historical-discovery
20dbf8f88c742055d6c6426c98bd7349f89a110a refs/remotes/origin/ingest/senate-post-support
88112168237e5c37841b785dccd2375f6cc40115 refs/remotes/origin/main
20040a3f190b14287b316eec097b839867746a32 refs/remotes/origin/master
1e26d9afb8feb8b94af7fb3cc3bf8e07385d6b90 refs/remotes/origin/policy/w28-release-prep
fa83b62f10eea3e6ee62f67f4fc788779e797794 refs/remotes/origin/release/pin-votes-001
841617707250df78b3ff37d61fc89a15869553cf refs/remotes/origin/review/completion-20261121
43b2796362f1793f761838065095606d5c6149aa refs/remotes/origin/w5-deployment-squash
3615ba083a0baf57ca904c07ec86db62313eafc6 refs/remotes/origin/w5-owner-merged
12ca8965d8401f3091ea94617b21bf280d47a9a9 refs/remotes/origin/wip/week-1-data
7bcf551aa8a788e53c318ee0c129c52d709817be refs/remotes/origin/wip/week-2-ui
52e054c8654d323f72fbd1e461884ec4f1bc3e65 refs/remotes/origin/wip/week-3-analytics
e5709106d7b540a529e7bc5a8fe0fec023e4d84d refs/remotes/origin/wip/week-4-polish
6da38deb2c6a79c58263fac161dc7eba5623d46e refs/tags/dashboard-for-deployment-1795041320
7649438839f9a19ab140399de75b634292c97772 refs/tags/dashboard-v1.0-20261119-002049
7649438839f9a19ab140399de75b634292c97772 refs/tags/dashboard-v1.0-complete-20261119-001943
3dcc890d53edea48a85176ed65eb35fe3fc1f9c3 refs/tags/dashboard-v1.0-staging-ready-20261119-001539
3dcc890d53edea48a85176ed65eb35fe3fc1f9c3 refs/tags/dashboard-v1.0-staging-ready-20261119-001543
cda4e5e58e26003538635c129ba0e05bf194798d refs/tags/data-20261115-T203142
b4a85ff95e7cabedea2d7d35f9dabe97cb3135b3 refs/tags/data-20261117-T[superseded-tag]
76b49452f9c6f9d321cbdbe8701c112e4ce8b42d refs/tags/data-20261117-T213500
4bfcea089db4766f5dc5569fc221cf17a2bb8d5f refs/tags/data-20261121-votes-001
e115a06b864e4ec82a570cda3aded22cdcd24410 refs/tags/data-44909412878-1
e5f4bea8f13d5c8045641bc134ebfddaf8860a0e refs/tags/data-initial-2026-11-14
70365c3fcc8fe0f8d8ddda1dcd4e6313b9a2a986 refs/tags/perf-baseline-20261114
f62738b5d6f1c2469bdaae578fb9755d7d109c34 refs/tags/phase1-data-contract-20261114
e1f25c8ad8416c85ebbd20848047c7dbefd4f4ac refs/tags/phase2-sankey-20261114
0a9d8db8a8b992547a4936a5d9c1484c9e92ccdd refs/tags/phase3-complete-20261114
bd5bd900f2a2517f4590d1e040448298187925e2 refs/tags/phase3-coverage-20261114
5acf5b374a787e42358b9ac63dc454df51884948 refs/tags/phase4-complete-20261114
fe263f980f36ca475a67bdd0bde600d9bea0475a refs/tags/pre-github-20261113-115113
346fcbd514c033499b71f84143fb53f5befb2552 refs/tags/pre-remediation-2026-11-19
a26cdf01fb80bf09c53f291bbb08d6bb05dd5b3f refs/tags/pre-wave2-2026-11-19
ce2fe2427905a32923db160fa6b1cea7fabfcfe2 refs/tags/v0.2.0
6da38deb2c6a79c58263fac161dc7eba5623d46e refs/tags/v1.0-full-dashboard-20261119
6b848f1d1a68ebdb21c70e06d369072704413694 refs/tags/w1-before-merge
88112168237e5c37841b785dccd2375f6cc40115 HEAD
eb069d2b1de953a89489245ef6418a66a7b652ba worktrees/wt-D4.3/HEAD
1005060cdccd7061a9a9656614117086121f6fee worktrees/wt-D4.1/HEAD
dd463d18e830c3881e2a02ee0513952493f4ed26 worktrees/wt-D0.1/HEAD
d43bd3546cb51c82d4f66d1135f62edce6bcf6a8 worktrees/wt-W2-A/HEAD
2aa54014ae3aabd23650d1ba9603cb22cbc552a5 worktrees/wt-P0-7/HEAD
7444c7b0fc267e21be80516860a7f0ec004d64cd worktrees/wt-W2-E/HEAD
23b5b81b8c133ef7648acbccdb1106b15e40aba1 worktrees/wt-D0.2/HEAD
1fcd577e8aa08e42e4fb4b8bfd614a024e04a526 worktrees/wt-P0-1/HEAD
58ec23fc4662d21215c3966ba624b5e0d39f4f94 worktrees/wt-INTEGRATE/HEAD
427a77c57a53933751ff8b5e55a91432cf7fc00b worktrees/wt-W5/HEAD
2bbb85e4175b3ef1cf7358d872c0fcefd5e9aaca worktrees/wt-W2-D/HEAD
76ed2754477023a31cd6268b2d28acb1e490835b worktrees/wt-P0-6/HEAD
74f20f7a05cfcc4d1199633c8e476cc81db4c548 worktrees/wt-P0-3/HEAD
e042961409f4d9b83e6c6dd08d20a974de457b00 worktrees/wt-D4.2/HEAD
587307de0dd742af145828ba7dbdf4c7ebbf15e0 worktrees/wt-INTEGRATE2/HEAD
f46c660ef5142e20fab4eeb430c77d444e1158ff worktrees/wt-P0-5/HEAD
eb069d2b1de953a89489245ef6418a66a7b652ba worktrees/wt-SUP-BASE/HEAD
d56456c8ff543e31d975fa62ae7b7d48d287aad4 worktrees/wt-P0-4/HEAD
1d72d06f9ee18ddec1cc3aada796ff03f7a74772 worktrees/wt-D0.3/HEAD
eb069d2b1de953a89489245ef6418a66a7b652ba worktrees/wt-D3.1/HEAD
75da6eb39a6e8bb8bb3431bf1735fe53cd0957ae worktrees/wt-D2.1/HEAD
0a42bea7f5052b7cf3f6a4074e325d8976959968 worktrees/wt-INTEGRATE3/HEAD
d7fb3c77336050402968353afe3cc36d2425b6ec worktrees/wt-P0-2/HEAD
c97573568cc860558560178c89ff9ef6ca62abec worktrees/wt-W2-C/HEAD
1b45bfc6fb86eb74d2bbe5f15bfc976522380103 worktrees/baseline/HEAD
3f7a17ed25c5cff53347551c13d946cccea18c5e worktrees/wt-W2-B/HEAD
eb069d2b1de953a89489245ef6418a66a7b652ba worktrees/wt-D0.4/HEAD
The bundle records a complete history.
The bundle uses this hash algorithm: sha1
/tmp/opencode/backups/link-repair/W0/pre.bundle is okay
```

`tar -tzf /tmp/opencode/backups/link-repair/W0/worktree.tgz >/dev/null` → exit 0, no stdout/stderr output.

`(cd /tmp/opencode/backups/link-repair/W0 && sha256sum -c SHA256SUMS)` → exit 0:

```text
pre.bundle: OK
pre.sha: OK
pre.status: OK
worktree.tgz: OK
```

Raw captures: `/tmp/opencode/backups/link-repair/W0/verify-bundle.stdout`, `/tmp/opencode/backups/link-repair/W0/verify-bundle.stderr`, `/tmp/opencode/backups/link-repair/W0/verify-sums.out`, plus `/tmp/opencode/backups/link-repair/W0/SHA256SUMS`. The `is okay` line is emitted by `git bundle verify` on stderr; it appears after the stdout in the terminal capture above.

### Branch and baseline commit

```console
$ git checkout -b repair/links-base
Switched to a new branch 'repair/links-base'
$ git add -- "Parlament Deschis Obsidian vault/"
$ git diff --cached --name-only
Parlament Deschis Obsidian vault/00-START/START-HERE.md
Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md
Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md
Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-SUPERVISION-2026-11-22.md
Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C01-SHELL-2026-11-22.md
Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C02-OVERVIEW-2026-11-22.md
Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C03-ENTITIES-2026-11-22.md
Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C04-VOTES-2026-11-22.md
Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md
Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C06-DESTINATIONS-2026-11-22.md
Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C07-HARNESS-2026-11-22.md
Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md
Parlament Deschis Obsidian vault/50-RESEARCH/CLICK-INVESTIGATION-JOURNEY-2026-11-22.md
Parlament Deschis Obsidian vault/50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md
Parlament Deschis Obsidian vault/60-EVIDENCE/CLICK-BROWSER-OBSERVATIONS-2026-11-22.md
$ git commit -m "docs(vault): commit clickable investigation baseline (C-01..C-07)"
[repair/links-base dbc5eaf] docs(vault): commit clickable investigation baseline (C-01..C-07)
 15 files changed, 3235 insertions(+), 3 deletions(-)
 create mode 100644 Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md
 create mode 100644 Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md
 create mode 100644 Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-SUPERVISION-2026-11-22.md
 create mode 100644 Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C01-SHELL-2026-11-22.md
 create mode 100644 Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C02-OVERVIEW-2026-11-22.md
 create mode 100644 Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C03-ENTITIES-2026-11-22.md
 create mode 100644 Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C04-VOTES-2026-11-22.md
 create mode 100644 Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md
 create mode 100644 Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C06-DESTINATIONS-2026-11-22.md
 create mode 100644 Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C07-HARNESS-2026-11-22.md
 create mode 100644 Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md
 create mode 100644 Parlament Deschis Obsidian vault/50-RESEARCH/CLICK-INVESTIGATION-JOURNEY-2026-11-22.md
 create mode 100644 Parlament Deschis Obsidian vault/50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md
 create mode 100644 Parlament Deschis Obsidian vault/60-EVIDENCE/CLICK-BROWSER-OBSERVATIONS-2026-11-22.md
$ git rev-parse HEAD
dbc5eafcbcf5412fc883a78d5870b44c3021f71d
$ git branch --show-current
repair/links-base
```

Branch: `repair/links-base`. Baseline commit SHA: `dbc5eafcbcf5412fc883a78d5870b44c3021f71d`. `git diff --cached --name-only` contained only paths under `Parlament Deschis Obsidian vault/`; the exact committed paths are the same enumerated list above. `main` was not modified by W0.

### Gate results (re-run after the baseline commit, from repo root)

| Command | Exit | Output excerpt |
|---|---:|---|
| `python3 scripts/vault_lint.py` | 0 | `VAULT LINT PASS: 66 notes, all links/frontmatter/vocabularies clean` |
| `python3 scripts/vault_sync.py --check` | 0 | `vault_sync --check: clean — 5 generated notes match the source commit` |
| `bash scripts/check-doc-truth.sh` | 0 | `false-claims: 0` |
| `git diff --check` | 0 | `(no output)` |

Raw gate captures: `/tmp/opencode/backups/link-repair/W0/gate-vault-lint.out`, `gate-vault-sync.out`, `gate-doc-truth.out`, `gate-diff-check.out`.

### Code evidence

Scope: git identity/branch/commit operations, backup artifact creation and verification, and the four vault-gate scripts, all from repository root `/home/nedaktov/parlament-deschis`. No product-code file was edited in W0; no `_generated/*`, data, release-pin, workflow or config file was touched. Raw capture paths are the ROOT files listed above plus the four gate captures. Result: entry identity matched the expected `main` / `88112168237e5c37841b785dccd2375f6cc40115`; the three backup verifications all exited 0; the baseline commit contains only vault paths; all four gates exited 0. Limits: W0 ran only the four vault gates; frontend `lint` / `build` / `i18n:check` gates belong to later waves and were not run here, so no claim is made about them. This section records no wave sign-off verdict — that is supervisor-only, and no integration SHA exists yet.

### Browser evidence

No browser action in W0 — not applicable. No browser capture exists and no browser observation is claimed.

### Supervisor sign-off (§F template)

```text
WAVE SIGN-OFF
Wave ID:            W0
Recipes:            L-00 (agent: git-master)
Entry HEAD/branch:  main / 88112168237e5c37841b785dccd2375f6cc40115 (W0 §Entry identity :74-101; backup pre.sha)
Backup ROOT:        /tmp/opencode/backups/link-repair/W0
Manifest evidence:  bundle verify exit 0 (W0 :355-356; raw verify-bundle.stdout/stderr) | tar -tzf exit 0 (W0 :358) | sha256sum -c exit 0 (W0 :360-367) — committed in vault commit baa972a; supervisor re-ran all three read-only: four OK lines, "The bundle records a complete history", tar exit 0
Diff (name-only):   baseline dbc5eaf changed 15 files, all under "Parlament Deschis Obsidian vault/" (W0 :377-409); supervisor re-ran git diff --name-only main..HEAD — 15 vault paths, zero product-code paths
Checkpoint SHAs:    baseline dbc5eafcbcf5412fc883a78d5870b44c3021f71d; evidence baa972ae211182fa2259efaf499b8f8690680901; main and origin/main still 88112168237e5c37841b785dccd2375f6cc40115 (supervisor re-check)
Gates (cmd/exit):   vault_lint 0 (66 notes); vault_sync --check 0 (5 generated notes clean); check-doc-truth.sh 0 (false-claims: 0); git diff --check 0 (no output) — W0 :420-425, raw captures :427; supervisor independently re-ran check-doc-truth.sh -> false-claims: 0, exit 0
Browser evidence:   N/A — no browser action in W0 (W0 :433-435); no browser-dependent acceptance item
Code evidence:      W0 :429-431 (separate titled section: scope, result, limits)
Acceptance items:   5/5 PASS — L-00 :66-67 (branch exists; baseline commit exists; manifest verifies; main untouched; no product code changed)
Verdict:            GREEN

Citations (exact note/section or file:line for every judgement):
  - This note, W0 §Entry identity :74-101, §Backup :119-369, §Branch and baseline commit :371-416, §Gate results :418-427, §Code evidence :429-431, §Browser evidence :433-435.
  - Recipes L-00 :39-67 (steps, checkpoint, rollback, acceptance); strategy §4 W0 row :74, §5 :104-127, §6 :129-156; supervision protocol §C G1-G8 and §F.
  - Supervisor read-only re-verification (2026-11-22): branch repair/links-base; HEAD baa972a; main/origin/main 8811216; clean worktree; SHA256SUMS four OK; git bundle verify complete history; tar -tzf exit 0; doc-truth false-claims 0; banned tag literal absent from this note and the [superseded-tag] alias present at :308; no "W0 NOT STARTED" or "one checkpoint" lines remain.
  - This sign-off is supervisor-authored and appended after commit baa972a; the lead commits the verdict block with the wave record.

Required remediations (owner: lead; each must be closed before next verdict):
  - none

Authorisation (GREEN only — reproduce verbatim, filling the braces):
  "Integration authorised: wave W0 is GREEN on the evidence cited above; the lead may merge repair/links-base into repair/links-base with git merge --ff-only."
```

## Wave W1 — confirmed BROKEN fixes

Recipes L-01 (Ideology "All years") and L-02 (dead Compare MPs link).

### Code evidence — entry and backup (recorded before the first edit)

```console
$ git branch --show-current
repair/links-base
$ git rev-parse HEAD
baa972ae211182fa2259efaf499b8f8690680901
$ git status --short
(empty)
```

Backup ROOT: `/tmp/opencode/backups/link-repair/W1`. Exact commands (fully
expanded paths, no ellipses):

```bash
mkdir -p /tmp/opencode/backups/link-repair/W1
git bundle create /tmp/opencode/backups/link-repair/W1/pre.bundle --all
git rev-parse HEAD > /tmp/opencode/backups/link-repair/W1/pre.sha
git status --porcelain > /tmp/opencode/backups/link-repair/W1/pre.status
tar -czf /tmp/opencode/backups/link-repair/W1/worktree.tgz -C /home/nedaktov/parlament-deschis --exclude=.git --exclude=node_modules --exclude=.venv --exclude=.next --exclude=dist .
(cd /tmp/opencode/backups/link-repair/W1 && sha256sum pre.bundle pre.sha pre.status worktree.tgz > SHA256SUMS)
git bundle verify /tmp/opencode/backups/link-repair/W1/pre.bundle
tar -tzf /tmp/opencode/backups/link-repair/W1/worktree.tgz >/dev/null
(cd /tmp/opencode/backups/link-repair/W1 && sha256sum -c SHA256SUMS)
```

Verification outputs: `git bundle verify` exit 0 ("The bundle records a complete
history", 203 refs); `tar -tzf` exit 0; `sha256sum -c` exit 0 with
`pre.bundle: OK`, `pre.sha: OK`, `pre.status: OK`, `worktree.tgz: OK`.
Full raw outputs are in `/tmp/opencode/backups/link-repair/W1/`.

### Code evidence — implementation and gates

Implementation agent: `minimal-change-engineer`, two atomic commits on
`repair/links-w1`:

| Recipe | SHA | Subject |
|---|---|---|
| L-01 | `12cab48cf6c3c095850275a9d642666dca727fea` | `fix(ideology): L-01 make "All years" persistent …` |
| L-02 | `943f4bf00fe191a1d60542676d9f5029bc00a672` | `fix(mps): L-02 render Compare MPs link …` |

Diff from entry `e919b677..HEAD` is exactly two paths:
`frontend/src/pages/Ideology.tsx`, `frontend/src/pages/Mps.tsx`.
`git diff --name-only` and `git status --short` were empty after the commits.

Code verification by lead: `ALL_YEARS` declared in `Ideology.tsx:49`;
query function at `:65` passes `undefined` for `all` (the mandatory S-10 step,
so `year=all` never reaches `api.py:1747`'s `^\d{4}$` validator); `selectedYear`
at `:81-85` and the `value`/`onChange`/option at `:253-257` use the sentinel;
query key unchanged at `:64`. `Mps.tsx:144-148` renders `<Link to="/compare-mps"
search={scope.searchFor()}>` with `t("mps.compareLink", …)`; `i18n.ts` unchanged.

Gate outputs (all exit 0):

```console
$ cd /home/nedaktov/parlament-deschis/frontend && npm run lint
> tsc --noEmit && eslint src --ext .ts,.tsx        [no errors]
$ cd /home/nedaktov/parlament-deschis/frontend && npm run build
✓ 940 modules transformed … ✓ built in 8.75s       [exit 0]
$ node scripts/check_routes_nav.mjs
ROUTES total=24 nav_links=22 unlinked=0 deprecated=0
PASS: every route is nav-reachable or formally deprecated   [exit 0]
$ node scripts/check_i18n_keys.mjs
PASS: i18n key diff clean (0 missing, 0 asymmetric, 0 duplicate) [exit 0]
$ python3 scripts/vault_lint.py
VAULT LINT PASS: 66 notes, all links/frontmatter/vocabularies clean  [exit 0]
$ python3 scripts/vault_sync.py --check
clean — 5 generated notes match the source commit          [exit 0, after regeneration]
$ bash scripts/check-doc-truth.sh
false-claims: 0                                             [exit 0]
$ git diff --check                                          [exit 0, no output]
```

`vault_sync.py` regenerated the five `_generated/*` notes against source commit
`943f4bf…`; this was a regeneration, never a hand-edit.

### Browser evidence (supplementary, local dev server)

Raw captures: `/tmp/opencode/w1-browser-ideology.json`,
`/tmp/opencode/w1-browser-mps.json`, `/tmp/opencode/w1-browser-mps-specific.json`.
Scope: Chrome DevTools on `http://127.0.0.1:5188` only; no production or axe claims.

- `/ideology?date=2026-11-22`: options were `all / 2024 / 2019 / 2014 / 2010 /
  2006 / 2002`; after selecting `all`, URL became `…&chesYear=all`, select value
  stayed `all`, and the table rendered **38 rows across 6 distinct years**
  (2019, 2024, 2006, 2010, 2014, 2002). This is the B1 defect fixed.
- `/mps?date=2026-11-22`: two anchors target `/compare-mps` — the pre-existing
  nav link ("Compară parlamentari") and the **new** card link
  ("Compară parlamentarii →"). Clicking the new one reached
  `/compare-mps?date=2026-11-22`, title "Compară parlamentari — Parlament
  Deschis", with `window.__w1marker` surviving → SPA navigation. The first
  attempt accidentally clicked the nav link; it was repeated with a link-text
  discriminator and the false lead is recorded here, not claimed as a defect.
- `list_console_messages` (error/warn) after the clicks: **no console messages found**.

### Acceptance table

| Criterion | Evidence | Result |
|---|---|---|
| "All years" persists in URL and renders all waves | browser ideology capture | PASS |
| API receives no `year=all` | `Ideology.tsx:65` code + 200 OK render with 6 years | PASS |
| Compare MPs link visible and navigates with scope | browser MPS specific capture | PASS |
| i18n parity unchanged | `check_i18n_keys.mjs` exit 0 | PASS |
| Diff ⊆ exclusive file list | `{Ideology.tsx, Mps.tsx}` | PASS |
| No new console errors | console capture | PASS |

### Supervisor sign-off (§F template)

```text
WAVE SIGN-OFF
Wave ID:            W1
Recipes:            L-01, L-02 (agent: minimal-change-engineer)
Entry HEAD/branch:  e919b6771267866682946f842b9a770d49e02e2a / repair/links-base (W1 :473-480; backup pre.sha re-read)
Backup ROOT:        /tmp/opencode/backups/link-repair/W1
Manifest evidence:  bundle verify exit 0 (W1 :497-500; raw bundle-verify.txt) | tar -tzf exit 0 (W1 :498; tar-list.txt) | sha256sum -c exit 0 (W1 :498-499; manifest-check.txt) — entry/evidence commit e919b67; supervisor re-ran all three: four OK lines, "The bundle records a complete history", tar exit 0
Diff (name-only):   code commits 12cab48..943f4bf = exactly frontend/src/pages/Ideology.tsx + frontend/src/pages/Mps.tsx (W1 :512-514; supervisor re-ran git diff --name-only e919b677..943f4bf = 2 paths). Full e919b677..HEAD additionally has the journey note and five regenerated _generated/* notes from evidence commit eab926a (W1 :544-545) — mandated vault write-back (STRAT §10) and regeneration (AGENTS NEVER hand-edit generated files), not a code-scope breach under R1; vault_sync --check clean confirms.
Checkpoint SHAs:    L-01 12cab48cf6c3c095850275a9d642666dca727fea; L-02 943f4bf00fe191a1d60542676d9f5029bc00a672; evidence eab926a233b38a3d18cb14ce703ddb8f4ce0d3e2; entry e919b6771267866682946f842b9a770d49e02e2a. Code commit messages carry recipe ID, evidence anchor, gate output and rollback SHA (W1 :507-510; supervisor git log). The "brownser" typo is only in the vault evidence-commit subject: no gate reads commit-subject text, so no gate or checkpoint is affected.
Gates (cmd/exit):   lint 0; build 0; routes total=24 nav_links=22 unlinked=0 exit 0; i18n parity 0; vault_lint 66 notes 0; vault_sync --check 0; doc-truth false-claims: 0; git diff --check 0 — W1 :523-542, raw captures :544-545 and /tmp/opencode/w1-{lint,build}.txt. Supervisor re-ran routes (24/22/0), i18n (ro=724 en=724 used=651 dynamic=21; 0 missing/asymmetric/duplicate), vault_lint, sync --check, doc-truth and diff --check: all exit 0. Build not re-run by supervisor (it writes dist); recorded build log examined instead.
Browser evidence:   separate titled section W1 :547-564. Raw captures /tmp/opencode/w1-browser-ideology.json (chesYear=all persists, 38 rows / 6 distinct years), /tmp/opencode/w1-browser-mps-specific.json (new "Compară parlamentarii →" link clicked, marker "spa", /compare-mps?date=2026-11-22, correct title), /tmp/opencode/w1-browser-mps.json (first-click false lead recorded and discarded, not claimed). No console error/warn observed (:564). Local dev server 127.0.0.1:5188 only; no production or axe claim.
Code evidence:      separate title W1 :471-545. Ideology.tsx:49 ALL_YEARS; :65 mandatory S-10 step `chesYear === ALL_YEARS ? undefined : chesYear` so year=all never reaches api.py:1747's ^\d{4}$; :81-84 selectedYear; :253-257 value/onChange/option sentinel; :64 query key unchanged. Mps.tsx:144-148 <Link to="/compare-mps" search={scope.searchFor()}> with t("mps.compareLink"); i18n.ts unchanged (2-path code diff). Supervisor re-read all cited lines.
Acceptance items:   6/6 PASS — W1 :568-575; each corroborated by code, gate or browser capture above.
Verdict:            GREEN

Citations (exact note/section or file:line for every judgement):
  - This note, W1 §Code evidence :471-545, §Browser evidence :547-564, §Acceptance table :566-575.
  - Recipes L-01 :51-105, L-02 :109-138; strategy §2.5 :48-49, §6 :129-156, §10 :191-197; supervision protocol §C (G1-G8, R1, R2), §D, §E, finding S-10.
  - Supervisor read-only re-verification (2026-11-22): branch repair/links-w1; HEAD eab926a; clean worktree; code diff entry..943f4bf = 2 files; six checks re-run with exit 0; backup SHA256SUMS and bundle re-verified; browser JSON captures read.
  - Commit-subject typo in eab926a is cosmetic and affects no gate (STRAT §2.5 applies to code checkpoint messages, which are correct).
  - Non-blocking evidence note for future waves: W1 :564 records an empty error/warn console list with tool name but no separate raw capture file; no console error was observed, so R2 is not triggered.

Required remediations (owner: lead; each must be closed before next verdict):
  - none

Authorisation (GREEN only — reproduce verbatim, filling the braces):
  "Integration authorised: wave W1 is GREEN on the evidence cited above; the lead may merge repair/links-w1 into repair/links-base with git merge --ff-only."
```

## Wave W2 — navigation and scope integrity

Recipes L-03 (footer navigation + shared project URL), L-04+L-05 (dashboard card
scope + wave click, one agent / two commits), L-06 (pagination bounds).

### Code evidence — entry and backup (before first edit)

```console
$ git branch --show-current
repair/links-base
$ git rev-parse HEAD
1fa34b127ced496778a0c60caf110fd32e62953d
$ git status --short
(empty)
```

Backup ROOT `/tmp/opencode/backups/link-repair/W2`. Commands are identical to W1
with `W1` replaced by `W2` (fully expanded absolute paths, no ellipses):
`git bundle create …/W2/pre.bundle --all`, `git rev-parse HEAD > …/W2/pre.sha`,
`git status --porcelain > …/W2/pre.status`, `tar -czf …/W2/worktree.tgz -C
/home/nedaktov/parlament-deschis --exclude=.git --exclude=node_modules
--exclude=.venv --exclude=.next --exclude=dist .`, `sha256sum … > SHA256SUMS`,
then `git bundle verify`, `tar -tzf` and `sha256sum -c`. All three verifications
exited 0: `pre.bundle: OK`, `pre.sha: OK`, `pre.status: OK`, `worktree.tgz: OK`.

### Code evidence — implementation (W2)

| Recipe | SHA | Subject |
|---|---|---|
| L-03 | `11538c857acd7216c4d6ca20521a6d7f641cd59e` | `fix(footer): L-03 router links, honest label, single project URL …` |
| L-04 | `b739c958eef2a27afce64e07b8af94233ff0e8d5` | `fix(dashboard): L-04 preserve scope on four stat cards …` |
| L-05 | `9e22d94ee0afe9e1f56a4788e4776f396719ea02` | `fix(dashboard): L-05 wave click carries wave date …` |
| L-06 | `624e15982ade695fca46f7649b4dcdfdf729d4e4` | `fix(pagination): L-06 correct next-page bounds …` |

Diff from W2 entry `0613198f..624e159` is exactly eight paths:
`About.tsx`, `Footer.tsx`, `config/links.ts` (new), `i18n.ts`, `LiveDashboard.tsx`,
`Mps.tsx`, `Traseism.tsx`, `router.tsx`. Gate outputs: `npm run lint` exit 0,
`npm run build` exit 0 (941 modules, pre-existing chunk-size warning),
`npm run i18n:check` exit 0 (ro=725/en=725, 0 missing/asymmetric/duplicate),
`check_routes_nav.mjs` 24 routes / 22 nav links / 0 unlinked exit 0, vault lint
PASS 66, sync check clean after regeneration, doc-truth 0, `git diff --check` 0.
`grep -R "github.com/parlament-deschis" frontend/src` returned no match; the
footer now shows "Cod sursă" pointing at the 200 URL.

### Browser evidence — W2 (supplementary, local dev)

Raw captures: `/tmp/opencode/w2-browser-footer.json`,
`w2-browser-footer-retest.json`, `w2-browser-footer-trace.json`,
`w2-browser-card.json`, `w2-browser-card-click.json`, `w2-browser-wave.json`.

- Footer links now carry scope in `href` (e.g. `/traseism?date=2024-06-01`,
  `/report?date=2024-06-01`) and the click is an SPA navigation (marker survived).
- Dashboard card `/mps?date=2024-06-01` click reached "Parlamentari" with the
  scope retained and marker survived — L-04 PASS.
- Wave click carried the wave date (`date=2016-02-01`) — L-05's own logic works.
- **FAIL (pre-existing, escalated):** a browser history trace showed
  `push /traseism?date=2024-06-01` followed by
  `push /?date=2024-06-01&legislature=2020`, ending on the overview page; the
  wave click likewise ended on `/` with `?date=2016-02-01…`. Direct navigation
  to `/traseism?date=2024-06-01` also settled on `/`, proving the defect is not
  a W2 regression. Cause: `useScope.ts:38` `useNavigate({ from: "/" })` plus
  `:51-65` `navigate({ search })` with no `to`, triggered by
  `Traseism.tsx:678-682`.

### Supervisor ruling — RED for W2, emergency wave W2B

The supervisor classified the failed browser check as **R2 (broken route)** —
the check ran and failed, so it cannot be downgraded to NOT PROVEN. No W2
checkpoint revert is warranted because a direct-navigation control proves the
defect pre-existed L-03, but W2 cannot be signed GREEN. Ruling: add emergency
recipe **L-18** in wave **W2B**, exclusive file `frontend/src/hooks/useScope.ts`,
with explicit `to: location.pathname` via `useLocation()`, preserving the
functional search updater and `replace: false`; re-test footer link, wave click,
dashboard card and another scope control. Details in the supervision note §I.

### W2B entry, backup and L-18 result

Entry branch `repair/links-w2`, HEAD `1167d8a7de21d0e6e699dc5a1ef36727db365f8e`,
clean tree. Backup ROOT `/tmp/opencode/backups/link-repair/W2B`, created with the
same expanded-path bundle/archive/manifest procedure as W1/W2; `git bundle
verify` exit 0, `tar -tzf` exit 0, `sha256sum -c` exit 0 (`pre.bundle: OK`,
`pre.sha: OK`, `pre.status: OK`, `worktree.tgz: OK`). Raw outputs in that folder.

L-18 agent: `frontend-developer`, branch `repair/links-w2b`, one commit
`3a49f25a949bb9b292c6188fe4bb1c35d065d42b`. Diff from W2B entry is exactly
`frontend/src/hooks/useScope.ts`: `useLocation` imported (`:2`), `location`
captured (`:39`), `to: location.pathname` added to the `navigate` call (`:52-66`)
with the functional search updater and `replace: false` preserved, dependency
array `[navigate, location.pathname]`, and the false "no `to` = stay in place"
comment corrected.

Gates (all exit 0): `npm run lint`, `npm run build` (941 modules, pre-existing
chunk warning), `npm run i18n:check` (ro=725/en=725, 0 missing/asymmetric/
duplicate), `node scripts/check_routes_nav.mjs` (24/22/0), vault lint 66, sync
check clean after regeneration against `3a49f25`, doc-truth 0, `git diff --check` 0.

Browser re-test captures (local dev, supplementary):

- `/tmp/opencode/w2b-browser-footer.json` — footer click from
  `/?date=2024-06-01` now lands on `/traseism?date=2024-06-01&legislature=2020`,
  title "Traseism — Parlament Deschis", marker survived (SPA), `aria-current`
  on Traseism. **V5 footer item PASS.**
- `/tmp/opencode/w2b-browser-wave.json` — wave `2016-02-01` click lands on
  `/traseism?date=2016-02-01&chamber=deputies&legislature=2012`, title
  "Traseism — Parlament Deschis", marker survived. **V5 wave item PASS.**
- `/tmp/opencode/w2b-browser-scope-control.json` + a subsequent `fill` of the
  "Camera" select — dashboard card still SPA (`/mps?date=2024-06-01`), and
  changing chamber stayed on `/mps?date=2024-06-01&chamber=deputies` with title
  "Parlamentari — Parlament Deschis". **V5 card + other-control items PASS.**
- `list_console_messages` (error/warn): no console messages found. **V5 console item PASS.**

The two W2 acceptance items that were FAIL are now PASS on the V5 captures
(footer → `/traseism`, wave click → `/traseism` with wave date). W2B is integrated
into `repair/links-w2` by fast-forward; supervisor sign-off follows.

### Supervisor sign-off (§F template)

```text
WAVE SIGN-OFF
Wave ID:            W2 (including emergency sub-wave W2B / recipe L-18)
Recipes:            L-03; L-04+L-05 (one agent, two commits); L-06; L-18 in W2B (frontend-developer)
Entry HEAD/branch:  W2: 1fa34b127ced496778a0c60caf110fd32e62953d / repair/links-base (W2 :615-622; W2 pre.sha re-read). W2B: 1167d8a7de21d0e6e699dc5a1ef36727db365f8e / repair/links-w2 (W2 :685; W2B pre.sha re-read)
Backup ROOT:        /tmp/opencode/backups/link-repair/W2 and /tmp/opencode/backups/link-repair/W2B
Manifest evidence:  both bundles: git bundle verify exit 0, tar -tzf exit 0, sha256sum -c exit 0 (W2 :624-631; W2B :685-689) — supervisor re-ran all six: four OK lines per manifest, "complete history" for both bundles, tar exit 0 both; pre.sha values match the two entry HEADs
Diff (name-only):   W2 entry..624e159 = exactly 8 code paths (W2 :642-644); W2B entry..3a49f25 = useScope.ts only (W2 :692-697); full 0613198..HEAD = 9 code paths (supervisor re-ran) plus the mandated journey note and five regenerated _generated/* notes (STRAT §10; AGENTS regenerate-only) — no R1 code-scope breach. i18n.ts owner in W2 is L-03 only, as registered.
Checkpoint SHAs:    L-03 11538c8; L-04 b739c95; L-05 9e22d94; L-06 624e159; L-18 3a49f25; evidence commits 1167d8a (W2 RED finding), ed20fa9 (supervisor escalation), 8c6ad8e (W2B result). W2B ff-only integration confirmed by linear git log (no merge commit); main and origin/main still 88112168237e5c37841b785dccd2375f6cc40115; worktree clean.
Gates (cmd/exit):   all exit 0 — npm run lint, npm run build, npm run i18n:check (ro=725/en=725, 0 missing/asymmetric/duplicate), check_routes_nav.mjs 24/22/0, vault lint 66, vault_sync --check clean, doc-truth false-claims: 0, git diff --check (W2 :644-648; W2B :699-702; logs w2-*.txt / w2b-*.txt). Supervisor re-ran routes (24/22/0), i18n, vault lint, sync --check, doc-truth and diff --check: all exit 0. Build not re-run by supervisor (writes dist); recorded build logs examined.
Browser evidence:   separate titled sections W2 :652-670 and W2B :704-717. V5 captures verified by supervisor: /tmp/opencode/w2b-browser-footer.json ends on /traseism?date=2024-06-01&legislature=2020, title "Traseism", marker "spa", aria-current on Traseism; /tmp/opencode/w2b-browser-wave.json ends on /traseism?date=2016-02-01&chamber=deputies&legislature=2012, title "Traseism", marker "spa"; /tmp/opencode/w2b-browser-scope-control.json shows card SPA to /mps?date=2024-06-01 and that the subsequent scope interaction stayed on /mps (chamber-fill result "…&chamber=deputies" recorded at W2 :713-716); console error/warn list empty (:717). Local dev only; no production or axe claim.
Code evidence:      V2/V3 verified by supervisor re-read: useScope.ts:2 useLocation import; :38-39 `from:"/"` type anchor retained plus `location` captured; :53 `to: location.pathname`; :57-65 functional search updater preserved; :66 replace:false preserved; :69 deps [navigate, location.pathname]; :36-37 false comment corrected. Root cause at old :38/:51-65 and Traseism.tsx:678-682.
Acceptance items:   all PASS. Formerly-FAIL item 1 "footer link reaches /traseism with scope" → PASS on w2b-browser-footer.json (previously FAIL at :663-670); formerly-FAIL item 2 "wave click reaches /traseism with wave date" → PASS on w2b-browser-wave.json (previously FAIL at :663-670). L-03 label/URL, L-04 card, L-06 bounds and i18n parity PASS per gates and browser captures.
Verdict:            GREEN

Citations (exact note/section or file:line for every judgement):
  - This note, W2 §Code evidence :613-650, §Browser evidence W2 :652-670, §Supervisor ruling :672-681, §W2B entry/backup/L-18 :683-720.
  - Recipes L-03/L-04/L-05/L-06 and emergency L-18; strategy §2.5 :48-49, §4 :83-84, §5, §6, §9 :183-189, §10; supervision protocol §C (G1-G8, R1, R2, A2), §D, §E, §I (V1-V6).
  - Supervisor read-only re-verification (2026-11-22): branch/HEAD, linear ff-only history, 9-path code diff, both pre.sha files, both manifests/bundles/tars, six re-run gates, useScope.ts:1-76, all three W2B browser JSON captures, main/origin/main unchanged, clean worktree.
  - Non-blocking evidence note: the chamber-fill URL at W2 :715 is recorded in the wave note without a separate raw file; the route-preservation property is corroborated by afterScope.url in w2b-browser-scope-control.json. Future waves should attach a dedicated raw capture for each scope-control assertion.

Required remediations (owner: lead; each must be closed before next verdict):
  - none

Authorisation (GREEN only — reproduce verbatim, filling the braces):
  "Integration authorised: wave W2 is GREEN on the evidence cited above; the lead may merge repair/links-w2 into repair/links-base with git merge --ff-only."
```

## Wave W3 — honest controls

Recipes L-07 (Voturi page-local search), L-08 (vote position source links),
L-09 (chair button), L-10 (PartyProfile nested interactive), L-11 (party
comparison defaults). Sole W3 i18n owner: L-07 (three keys).

**Code evidence — entry:** branch `repair/links-base`, HEAD
`bab425db28618df46eff08f2245ce89b231ee88d`, clean tree. Backup ROOT
`/tmp/opencode/backups/link-repair/W3`; `git bundle verify`, `tar -tzf` and
`sha256sum -c` all exit 0 (`pre.bundle: OK`, `pre.sha: OK`, `pre.status: OK`,
`worktree.tgz: OK`). Commands are the expanded-path procedure from W1/W2.

### Code evidence — implementation and gates

Two agents, six commits on `repair/links-w3`:

| Recipe | SHA | Files |
|---|---|---|
| L-07 | `85bdd81514b90c05e360170bd14a931cee836a86` | `Voturi.tsx`, `i18n.ts` |
| L-08 | `3f965aa87621caca47ea675e92ede33afd91492b` | `RollCallTable.tsx` |
| L-11 | `1f2cdc80219de266a2fc409bb2b1c2d0621eab24` | `PartyComparison.tsx` |
| L-09 | `74e7997fd28452395e0c1118dc5dc797360f3bc3` | `CommitteeControl.tsx` |
| L-10 | `7ccfd26fe7f3f860c099e02da7254ace59a6fbd8` | `PartyProfile.tsx` |
| L-09 follow-up | `944e67dd8c2a075c20dad252e4dd28d74e81def2` | `CommitteeControl.tsx` |

The follow-up closed a regression the L-09 agent itself detected: its first
patch set `aria-label={canOpenChair ? undefined : t("committee.noChair")}`,
removing the accessible name of enabled chair buttons (WCAG 4.1.2). It now
restores `t("a11y.committeeChair", { party })` in the true branch. Diff from
W3 entry `037934b2..HEAD` is exactly the six authorized paths above.

Gates all exit 0: `npm run lint`, `npm run build` (941 modules, pre-existing
chunk warning), `npm run i18n:check` (ro=728/en=728, 0 missing/asymmetric/
duplicate, `used=655` after the follow-up), `check_routes_nav.mjs` PASS, vault
lint PASS 66, sync check clean after regeneration against `944e67dd`, doc-truth
0, `git diff --check` 0. Exactly three i18n keys were added (both locales):
`view.voturi.searchHint`, `vote.positionsTruncated`, `committee.noChair`.

### Browser evidence (supplementary, local dev)

- `/tmp/opencode/w3-browser-voturi.json` — `/Voturi?date=2026-11-22` renders the
  new page-local search hint in Romanian. PASS.
- `/tmp/opencode/w3-browser-partyprofile.json` — `/party/PSD?date=2026-11-22`:
  `document.querySelectorAll('button a')` returned an empty list, so the
  provenance link is no longer nested inside a button. PASS.

Not browser-verified in this wave: `POSITION_LIMIT=500` truncation note
(needs a vote with >100 positions — resolver: live payload), party-default
correction (data-dependent), chair disabled label (component-level). These are
code-verified only and remain AMBER/NOT PROVEN for runtime.

### Supervisor sign-off (§F template)

```text
WAVE SIGN-OFF
Wave ID:            W3
Recipes:            L-07, L-08, L-09 (+ self-detected follow-up 944e67d), L-10, L-11 (two agents, six commits)
Entry HEAD/branch:  bab425db28618df46eff08f2245ce89b231ee88d / repair/links-base (W3 :759-763; W3 backup pre.sha re-read)
Backup ROOT:        /tmp/opencode/backups/link-repair/W3
Manifest evidence:  git bundle verify exit 0, tar -tzf exit 0, sha256sum -c exit 0 (W3 :761-763) — supervisor re-ran all three: four OK lines, "The bundle records a complete history", tar exit 0; pre.sha matches entry HEAD
Diff (name-only):   exactly six authorized code paths (W3 :769-782; supervisor re-ran git diff --name-only 037934b2..HEAD -- frontend/): Voturi.tsx, RollCallTable.tsx, i18n.ts, CommitteeControl.tsx, PartyProfile.tsx, PartyComparison.tsx. i18n.ts touched by L-07 ONLY (git log on that path returns 85bdd81 alone), matching strategy §4.1 sole-owner register. Extra journey/_generated paths are mandated vault write-back and regeneration (STRAT §10), not an R1 breach.
Checkpoint SHAs:    85bdd81 (L-07), 3f965aa (L-08), 1f2cdc8 (L-11), 74e7997 (L-09), 7ccfd26 (L-10), 944e67d (L-09 a11y follow-up), c12ada1 (evidence). Code messages carry recipe ID, evidence anchor, gates and rollback SHA. The L-09 agent self-detected an accessible-name regression from its first patch and closed it in 944e67d; final CommitteeControl.tsx:100-101 has disabled={!canOpenChair} and both aria-label branches named (a11y.committeeChair / committee.noChair) — verified by supervisor re-read.
Gates (cmd/exit):   all exit 0 — npm run lint, npm run build, npm run i18n:check (ro=728/en=728, used=655, 0 missing/asymmetric/duplicate; exactly 3 keys added in both locales: view.voturi.searchHint, vote.positionsTruncated, committee.noChair), check_routes_nav.mjs 24/22/0, vault lint 66, sync clean after regeneration against 944e67d, doc-truth 0, git diff --check (W3 :784-789; logs w3-*.txt). Supervisor re-ran routes, i18n, vault lint, sync --check, doc-truth and diff --check: all exit 0. Build not re-run (writes dist); recorded log examined. main/origin/main still 88112168237e5c37841b785dccd2375f6cc40115; worktree clean.
Browser evidence:   separate titled section W3 :791-802. Supervisor read both raw captures: /tmp/opencode/w3-browser-voturi.json (hasHint true, URL /Voturi?date=2026-11-22) → page-local hint rendered; /tmp/opencode/w3-browser-partyprofile.json (nestedAnchorsInButtons [] on /party/PSD?date=2026-11-22) → no nested interactive markup. Local dev only; no production or axe claim. No new console error or broken route observed.
Code evidence:      W3 :765-789 plus supervisor re-read of final CommitteeControl.tsx:94-117 and i18n key diff.
Acceptance items:   9/12 PASS · 3/12 AMBER/NOT PROVEN — per §C A2/A5 the AMBER items are acceptance-item-scoped, not wave-level, because every required gate ran and passed and no defect was observed:
  - AMBER 1: L-08 truncation note runtime rendering needs a vote with >100 positions; resolver = live payload (W3 :799-800). Code path bounded to POSITION_LIMIT=500 and note condition code-verified.
  - AMBER 2: L-11 party-default correction is data-dependent; resolver = live /api/parties (W3 :800-801; C03 F5).
  - AMBER 3: L-09 chair disabled label at runtime is component-level only; resolver = browser check with a chairless party (W3 :801-802).
Verdict:            GREEN

Citations (exact note/section or file:line for every judgement):
  - This note, W3 §Code evidence :759-789, §Browser evidence :791-802.
  - Recipes L-07 :257-278, L-08 :282-300, L-09 :304-317, L-10 :321-339, L-11 :343-357; strategy §2.2, §2.5, §4.1 :93-99, §5, §6 :129-156, §10; supervision protocol §C (G1-G8, A2, A5), §D, §E, §I.
  - AMBER scope ruling: my §C A2/A5 explicitly make a non-runnable or data-dependent item "AMBER for that acceptance item only"; STRAT §6 :134 requires naming the missing check and its resolver — done for all three at W3 :799-802. No R1/R2 condition is present, so the wave is GREEN; the three items remain NOT PROVEN and must never be restated as PASS.
  - Non-blocking note: the W3 browser section does not state console error/warn status explicitly; future waves should record it, as done in W1/W2.

Required remediations (owner: lead; each must be closed before next verdict):
  - none (three AMBER items carry named resolvers and are explicitly NOT PROVEN, not remediations of a defect)

Authorisation (GREEN only — reproduce verbatim, filling the braces):
  "Integration authorised: wave W3 is GREEN on the evidence cited above; the lead may merge repair/links-w3 into repair/links-base with git merge --ff-only."
```

## Wave W4 — accessibility, labels, URLs

Recipes L-12 (Hemicycle seat semantics — decision procedure), L-13 (Topuri
label, sole W4 i18n owner), L-14 (three live "View all →" literals).

**Code evidence — entry:** branch `repair/links-base`, HEAD
`129986e4bdbfd512fb4aebdcb66cffaecb379cf5`, clean tree. Backup ROOT
`/tmp/opencode/backups/link-repair/W4`; `git bundle verify`, `tar -tzf` and
`sha256sum -c` all exited 0 (`pre.bundle / pre.sha / pre.status / worktree.tgz: OK`).

### Code evidence — implementation and gates

| Recipe | SHA / outcome |
|---|---|
| L-12 | **NO-CHANGE** with one explanatory comment; committed as `docs(a11y): L-12 hemicycle NO-CHANGE decision comment …` (code evidence: every clickable seat has an equivalent native button in `Hemicycle.tsx:129-153`, same callback as `:118`) |
| L-13 | `aa5a358225291800a19383d93f53a601a396f4e0` — `Topuri.tsx` + sole W4 `i18n.ts` edit |
| L-14 | `258186fc2551a74c856415cf0f1c50016b06de64` — `SwitchTimeline.tsx`, `PartyNetwork.tsx`, `PartyListTable.tsx` |

Diff from W4 entry `4510d9ce..HEAD` is exactly the six authorized paths.
Gates all exit 0: lint, build (941 modules, pre-existing chunk advisory),
`i18n:check` (ro=731/en=731, 0 missing/asymmetric/duplicate), routes PASS,
vault lint PASS 66, sync check clean, doc-truth 0, `git diff --check` 0.
Exactly three keys added symmetrically: `filter.minVotes`,
`filter.minVotesPlaceholder`, `common.viewAll`.

### Browser evidence

`/tmp/opencode/w4-browser-labels.json`: `/topuri?date=2026-11-22` renders the
Romanian "Voturi minime" label and contains no stray "Minimum votes" / "View
all" English strings. The three localized "Vezi toate →" buttons were verified
in source only (no raw capture for them) — code evidence, not a browser claim.

### Supervisor sign-off (§F template)

```text
WAVE SIGN-OFF
Wave ID:            W4
Recipes:            L-12 (NO-CHANGE), L-13, L-14
Entry HEAD/branch:  129986e4bdbfd512fb4aebdcb66cffaecb379cf5 / repair/links-base (W4 :842-845; W4 backup pre.sha re-read)
Backup ROOT:        /tmp/opencode/backups/link-repair/W4
Manifest evidence:  git bundle verify exit 0, tar -tzf exit 0, sha256sum -c exit 0 (W4 :843-845) — supervisor re-ran all three: four OK lines, "The bundle records a complete history", tar exit 0; pre.sha matches entry HEAD
Diff (name-only):   exactly six authorized code paths (W4 :849-855; supervisor re-ran git diff --name-only 4510d9ce..HEAD -- frontend/): Hemicycle.tsx, Topuri.tsx, SwitchTimeline.tsx, PartyNetwork.tsx, PartyListTable.tsx, i18n.ts. i18n.ts touched by L-13 alone (git log on that path returns aa5a358 only), matching strategy §4.1 sole-owner register. Extra journey/_generated paths are mandated vault write-back and regeneration (STRAT §10), not an R1 breach.
Checkpoint SHAs:    e494c89 (L-12 NO-CHANGE comment), aa5a358 (L-13), 258186f (L-14), 7411f80 (evidence). Code commit messages carry recipe ID, evidence anchor, gates and rollback SHA. L-12 followed the decision procedure at REC L-12 :368-380: the one-line comment cites the equivalent native <button> path; supervisor verified the committed comment and that no seat semantics were changed.
Gates (cmd/exit):   all exit 0 — lint, build, npm run i18n:check (ro=731/en=731, 0 missing/asymmetric/duplicate; exactly 3 symmetric keys: filter.minVotes, filter.minVotesPlaceholder, common.viewAll — verified in the i18n diff by supervisor), check_routes_nav.mjs 24/22/0, vault lint 66, sync clean, doc-truth 0, git diff --check (W4 :856-860). Supervisor re-ran routes, i18n, vault lint, sync --check, doc-truth and diff --check: all exit 0. Build not re-run (writes dist); recorded log examined. main/origin/main still 88112168237e5c37841b785dccd2375f6cc40115; worktree clean.
Browser evidence:   separate titled section W4 :862-867. Supervisor read the raw capture /tmp/opencode/w4-browser-labels.json: /topuri?date=2026-11-22 has hasRoMinVotes true, strayEnglish false. The three "Vezi toate →" buttons are explicitly source-verified only, not claimed as browser evidence (W4 :866-867) — honest per §E; no new console error or broken route observed. Local dev only; no production or axe claim.
Code evidence:      W4 :842-860 plus supervisor re-read of the i18n key diff and the L-12 comment commit.
Acceptance items:   all PASS · 0 AMBER/NOT PROVEN — L-12 documented NO-CHANGE with code citations and no keyboard trap; L-13 zero hardcoded English labels (browser capture PASS); L-14 no remaining literal in the three component files (source/grep verified). No runtime-only claim is made for the three View-all buttons.
Verdict:            GREEN

Citations (exact note/section or file:line for every judgement):
  - This note, W4 §Code evidence :842-860, §Browser evidence :862-867.
  - Recipes L-12 :361-380 (decision procedure), L-13 :384-398, L-14 :402-417; strategy §2.8 :55-57 (honest no-change), §2.2, §4.1 :93-99, §5, §6 :129-156, §10; supervision protocol §C (G1-G8), §D, §E.
  - Supervisor read-only re-verification (2026-11-22): branch/HEAD, 6-path code diff, sole i18n owner, three symmetric keys, NO-CHANGE comment commit, backup manifest/bundle/tar, six re-run gates, browser JSON capture, main/origin/main unchanged, clean worktree.
  - Non-blocking note: the W4 browser section does not state console error/warn status explicitly; future waves should record it, as done in W1/W2.

Required remediations (owner: lead; each must be closed before next verdict):
  - none

Authorisation (GREEN only — reproduce verbatim, filling the braces):
  "Integration authorised: wave W4 is GREEN on the evidence cited above; the lead may merge repair/links-w4 into repair/links-base with git merge --ff-only."
```

## Wave W5 — dead controls

Recipe L-15. **Code evidence — entry:** branch `repair/links-base`, HEAD
`24984e23d9ddcc584025068b1fcc89a9b5da5020`, clean tree. Backup ROOT
`/tmp/opencode/backups/link-repair/W5`; `git bundle verify`, `tar -tzf` and
`sha256sum -c` all exited 0 (`pre.bundle / pre.sha / pre.status / worktree.tgz: OK`).

Implementation: commit `3e3cd99efa6999f81369304c918cfb043eb583fc`
(`refactor(dead): L-15 remove unreachable controls`). Re-run importer greps
proved zero source importers for `PartyComparisonMatrix` and `TimeSlider`, so
both files were deleted; `LoadingState`'s unused retry and `DashboardCard`'s
unreachable button branch were removed. The agent correctly **declined** two
parts of the recipe as unsafe: `EmptyState`'s CTA is still passed by
`AsyncState.tsx:89-90` (outside its exclusive list), and the dead arc plumbing
lives in `AgeDistributionRadial.tsx` (also outside its list); changing them
would either break the type gate or exceed scope. Both are recorded as
follow-ups, not claimed as fixed. `i18n.ts` read-only; `mps.compareLink` kept.

Diff from W5 entry `ccf01a44..HEAD` is exactly four paths (5 insertions,
232 deletions). Gates all exit 0: lint, build, i18n:check (ro=731/en=731),
routes PASS, vault lint PASS 66, sync clean, doc-truth 0, `git diff --check` 0.

**Browser evidence:** no browser pass — this wave removes only unreachable
code, so there is no clickable control whose runtime behaviour could change.
No browser claim is made.

### Supervisor sign-off (§F template)

```text
WAVE SIGN-OFF
Wave ID:            W5
Recipes:            L-15 (dead-control cleanup; two sub-items explicitly declined as out-of-scope and recorded as follow-ups)
Entry HEAD/branch:  24984e23d9ddcc584025068b1fcc89a9b5da5020 / repair/links-base (W5 :901-904; W5 backup pre.sha re-read)
Backup ROOT:        /tmp/opencode/backups/link-repair/W5
Manifest evidence:  git bundle verify exit 0, tar -tzf exit 0, sha256sum -c exit 0 (W5 :902-904) — supervisor re-ran all three: four OK lines, "The bundle records a complete history", tar exit 0; pre.sha matches entry HEAD
Diff (name-only):   exactly four authorized paths (W5 :906-919; supervisor re-ran git diff --name-status ccf01a44..HEAD -- frontend/): M DashboardCard.tsx, M LoadingState.tsx, D PartyComparisonMatrix.tsx, D TimeSlider.tsx. No i18n change (i18n.ts read-only in W5 as registered); mps.compareLink keys retained at i18n.ts:521 and :1274 (supervisor grep). EmptyState.tsx and AgeDistributionSection.tsx were left untouched within the agent's exclusive list; AgeDistributionRadial.tsx is outside it. Extra journey/_generated paths are mandated vault write-back (STRAT §10), not an R1 breach.
Checkpoint SHAs:    3e3cd99efa6999f81369304c918cfb043eb583fc (L-15), b157055faa0a8f90ff1513f05664d049fb80b6b8 (evidence). Message carries recipe ID, evidence anchor, gates and rollback SHA ccf01a44.
Gates (cmd/exit):   all exit 0 — lint, build, npm run i18n:check (ro=731/en=731, 0 missing/asymmetric/duplicate), check_routes_nav.mjs 24/22/0, vault lint 66, sync clean, doc-truth 0, git diff --check (W5 :917-919). Supervisor re-ran routes, i18n, vault lint, sync --check, doc-truth and diff --check: all exit 0. Build not re-run (writes dist); recorded log examined. main/origin/main still 88112168237e5c37841b785dccd2375f6cc40115; worktree clean.
Browser evidence:   no browser pass claimed (W5 :921-923). G6 permits this because the wave has no browser-dependent criterion: only unreachable code was removed, so no clickable control's runtime behaviour could change. Supervisor re-ran importer greps: PartyComparisonMatrix and TimeSlider have zero source importers (safe deletion); DashboardCard still imported by LiveDashboard; EmptyState still imported by Committees/Parties/AsyncState; AgeDistributionRadial imported by AgeDistributionSection — no importer broken.
Code evidence:      W5 :901-919; supervisor re-read of the diff and importer greps. Scope discipline (§E) is good: the agent declined EmptyState CTA (AsyncState.tsx:89-90 forwarding is outside its exclusive list) and the AgeDistributionRadial arc plumbing (file outside its exclusive list), recording both as follow-ups rather than exceeding scope or breaking the type gate.
Acceptance items:   all PASS · 0 AMBER/NOT PROVEN — L-15 "no importer broken" (zero-importer greps + build + routes gates) and "no live control removed" (only dead branches removed; declined items untouched and recorded). The two declined sub-items are NOT claimed as fixed.
Verdict:            GREEN

Citations (exact note/section or file:line for every judgement):
  - This note, W5 §Code evidence/implementation :901-919, §Browser evidence :921-923.
  - Recipe L-15 :421-446 (exclusive list, importer-grep step, read-only i18n, acceptance); strategy §2.8 :55-57 (honest no-change), §4 W5 row :79 (i18n read-only), §5, §6, §10; supervision protocol §C (G1-G8, G6), §D, §E.
  - Supervisor read-only re-verification (2026-11-22): branch/HEAD, 4-path diff, importer greps for all five symbols, i18n key retention, backup manifest/bundle/tar, six re-run gates, main/origin/main unchanged, clean worktree.
  - Non-blocking note: future browser sections should state console error/warn status explicitly; W5 legitimately claims no browser pass.

Required remediations (owner: lead; each must be closed before next verdict):
  - none (the declined EmptyState and AgeDistributionRadial sub-items are recorded follow-ups, not defects in this wave)

Authorisation (GREEN only — reproduce verbatim, filling the braces):
  "Integration authorised: wave W5 is GREEN on the evidence cited above; the lead may merge repair/links-w5 into repair/links-base with git merge --ff-only."
```

## Wave W6 — regression guards

_Recipe L-16._

## Wave W7 — integration and owner hand-off

_Recipe L-17. No merge to main and no deploy without explicit owner decision._

## See also

[CLICK-INVESTIGATION-JOURNEY](CLICK-INVESTIGATION-JOURNEY-2026-11-22.md) ·
[START-HERE](../00-START/START-HERE.md)
