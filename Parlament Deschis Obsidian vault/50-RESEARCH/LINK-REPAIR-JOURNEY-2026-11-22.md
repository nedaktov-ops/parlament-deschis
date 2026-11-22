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

## Wave W1 — confirmed BROKEN fixes

_Recipes L-01, L-02. Entry/exit, checkpoint SHAs, gate output, browser result, verdict._

## Wave W2 — navigation and scope integrity

_Recipes L-03…L-06._

## Wave W3 — honest controls

_Recipes L-07…L-11._

## Wave W4 — accessibility, labels, URLs

_Recipes L-12…L-14._

## Wave W5 — dead controls

_Recipe L-15._

## Wave W6 — regression guards

_Recipe L-16._

## Wave W7 — integration and owner hand-off

_Recipe L-17. No merge to main and no deploy without explicit owner decision._

## See also

[CLICK-INVESTIGATION-JOURNEY](CLICK-INVESTIGATION-JOURNEY-2026-11-22.md) ·
[START-HERE](../00-START/START-HERE.md)
