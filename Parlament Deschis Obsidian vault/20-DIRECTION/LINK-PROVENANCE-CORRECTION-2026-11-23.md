---
id: LINK-PROVENANCE-CORRECTION
type: runbook
title: "L-26 corrective recipe — vote-detail provenance anchor (2026-11-23)"
description: "Supervisor verdict on the V-03 C04-012 FAIL and a minimal corrective recipe that unwraps the vote-detail response at the call site, consistent with every other detail consumer; planning note, not an execution."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/frontend]
source_paths: [60-EVIDENCE/CLICK-VALIDATION-V07-2026-11-23.md, 20-DIRECTION/CLICK-VALIDATION-FLEET-2026-11-23.md, 20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md, 50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md]
source_commit: 863b200e1adc70aadb289fdd4df52a7e5be2c483
created: 2026-11-23
updated: 2026-11-23
---

# L-26 — Vote-detail provenance anchor correction (2026-11-23)

## 1. Verdict on the validation FAIL

**This is a genuine product defect, not an environment or data condition.** It
is a client/runtime type mismatch: the backend returns a wrapper envelope, the
client declares the unwrapped payload type, and the only consumer reads the
wrapper as if it were the payload.

### Verified evidence

- `v07-evidence-C04-012.json`: `GET /api/votes/34551` returned HTTP 200; the
  payload's top-level keys are `['data','data_exists','status']`;
  `api_data_source_url = "https://www.cdep.ro/ords/pls/steno/evot2015.xml?par1=2&par2=34551"`
  is present **inside** the wrapper; `detail_top_level_source_url = null`;
  `provenance_anchor_count = 0`, `provenance_href = null`,
  `body_contains_label = false`. The screenshot `v07-shot-C04-012.png` is the
  raw companion artifact.
- `v07-results.json`: C04-012 is the **only** FAIL among the 14 V-03 IDs.
  C04-007 (vote-row source anchor), C04-013 (roll-call source anchors) and the
  retry/render items are PASS, so the API, the dev server and the data are
  healthy — this is isolated to the detail path.

### Response shape from backend code (checked directly)

`backend/routers/api.py:1344-1381` `vote_detail()` returns:

```
1351-1355: when missing → {"status":"ok", "data_exists":False, "data":None}
1359-1381: when found  → {"status":"ok", "data_exists":True,
                          "data": {… "source_url": vote.source_url (1375),
                                    "snapshot_hash": … (1376),
                                    "truth_contract_version": … (1377), …}}
```

So `source_url` is at `data.source_url`, never at the top level. The wrapper
matches the other endpoints' envelope (`status`/`data_exists`/`data`).

### Where the contract breaks

- `frontend/src/api/client.ts:351-369` declares `VoteDetail` with `source_url`
  at the **top level** (:364).
- `frontend/src/api/client.ts:572-573` `voteDetail: (voteId) => get<VoteDetail>(…)`.
- `get<T>` at `client.ts:489-507` returns `res.json()` **unchanged** — no client
  method unwraps envelopes.
- `frontend/src/pages/Voturi.tsx:65-67` stores that raw wrapper in
  `voteDetailQuery.data`; `:354-359` guards on the wrapper object (truthy) and
  reads `voteDetailQuery.data.source_url` / `.snapshot_hash` /
  `.truth_contract_version` — all `undefined` at runtime.
- `frontend/src/components/ProvenanceStamp.tsx:31` returns `null` when every
  prop is falsy; `:42-50` would render the "Vezi sursa originală ↗" anchor only
  when `sourceUrl` is truthy. Hence no anchor.

### Correct fix layer: the call site, not `api.voteDetail()`

The codebase convention is **raw client, consumer unwraps**: `RollCallTable.tsx:29-31`
reads `query.data?.data` and `query.data?.data_exists` from the same envelope;
`Radar.tsx:77` uses `q.data.data`; `PartyComparison.tsx:96` uses
`control.data?.data?.parties`; `Committees.tsx:196` uses `control.data.data`;
`Ideology.tsx:69` uses `ideologyQuery.data?.data_exists`. Making
`api.voteDetail()` unwrap would make it the **only** client method that hides an
envelope, would contradict `get<T>`'s pass-through contract, and would leave
`VoteDetail`'s wrong type silently unfixed. The minimal, consistent change is
therefore: correct the type to describe the envelope, then unwrap once in
`Voturi.tsx`. The agent's suggestion to unwrap *inside* `api.voteDetail()` is
rejected for that reason; unwrapping at the call site is accepted.

## 2. Corrective recipe L-26 (wave W15)

- **Objective.** Render the vote-detail provenance anchor from the live
  `data.source_url` without changing labels, provenance semantics or any other
  endpoint.
- **Evidence anchor.** `v07-evidence-C04-012.json`, `v07-shot-C04-012.png`,
  `v07-results.json`; `backend/routers/api.py:1344-1381`;
  `frontend/src/api/client.ts:351-369,489-507,572-573`;
  `frontend/src/pages/Voturi.tsx:65-67,354-359`;
  `frontend/src/components/ProvenanceStamp.tsx:31,42-50`;
  [C-04](../40-FRONTEND/CLICK-INV-C04-VOTES-2026-11-22.md) C04-012;
  [V-03/V-07 fleet plan](CLICK-VALIDATION-FLEET-2026-11-23.md) §3/§5.
- **Exclusive files (exact, repo-relative).**
  - `frontend/src/api/client.ts` — type/return-type correction only (no runtime
    change).
  - `frontend/src/pages/Voturi.tsx` — call-site unwrapping only.
  - `tests/frontend_click/test_v07_votes.py` — regression assertion only.
  These are disjoint from L-25's `frontend/src/pages/Traseism.tsx` and
  `tests/frontend_click/test_v03_traseism.py`.
- **Steps (exact code intent).**
  1. Re-read the anchors:
     ```bash
     cd /home/nedaktov/parlament-deschis
     sed -n '1344,1381p' backend/routers/api.py
     sed -n '351,369p;489,507p;572,573p' frontend/src/api/client.ts
     sed -n '65,67p;354,359p' frontend/src/pages/Voturi.tsx
     cat /tmp/opencode/click-validation/v07-evidence-C04-012.json
     ```
  2. Verify the W15 backup before the first edit: bundle, `pre.sha`,
     `pre.status`, worktree archive and `SHA256SUMS` under
     `/tmp/opencode/backups/link-repair/W15` with fully expanded paths per
     [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §5; `git bundle verify`,
     `tar -tzf` and `sha256sum -c` must all exit 0, recorded in the W15 vault
     section before the edit (G2/R3, S-14).
  3. **Type correction in `client.ts`** — add next to `VoteDetail` (:369):

     ```ts
     /** Wire envelope returned by GET /votes/{vote_id} (api.py:1359-1381). */
     export interface VoteDetailResponse {
       status: string;
       data_exists: boolean;
       data: VoteDetail | null;
     }
     ```

     and change `:572-573` to
     `voteDetail: (voteId: string) => get<VoteDetailResponse>(\`/votes/${encodeURIComponent(voteId)}\`),`.
     This changes no runtime behaviour (`get` still returns raw JSON) and makes
     the declared type match the backend envelope.
  4. **Call-site unwrap in `Voturi.tsx`** — after `voteDetailQuery` (:65-67),
     derive `const detail = voteDetailQuery.data?.data;` and replace `:354-359` with:

     ```tsx
     {detail && (
       <ProvenanceStamp
         sourceUrl={detail.source_url}
         snapshotHash={detail.snapshot_hash}
         note={detail.truth_contract_version}
       />
     )}
     ```

     Keep the `ProvenanceStamp` component, its labels, `target`, `rel` and the
     `RollCallTable` mount unchanged. When `data` is null (backend
     :1351-1355), nothing renders — the correct honest behaviour.
  5. **Regression assertion in `tests/frontend_click/test_v07_votes.py`**
     (§3 below). Preserve the existing 14-ID reconciliation.
  6. Re-run gates and the V-07 test, then write W15 vault records and request
     the supervisor verdict.
- **Checkpoint.**
  ```bash
  cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build && npm run i18n:check
  cd /home/nedaktov/parlament-deschis && node scripts/check_routes_nav.mjs
  cd /home/nedaktov/parlament-deschis && python3 -m pytest tests/frontend_click/test_v07_votes.py -q
  cd /home/nedaktov/parlament-deschis && python3 scripts/vault_lint.py && python3 scripts/vault_sync.py --check && bash scripts/check-doc-truth.sh && git diff --check
  ```
  All must exit 0 with working directory, command, exit code and output excerpt
  recorded.
- **Rollback.** `git revert <L-26-commit-sha>` (additive); verified bundle at
  `/tmp/opencode/backups/link-repair/W15/pre.bundle`. No reset, force-push or
  tag move.
- **Acceptance criteria.**
  1. `C04-012` in `tests/frontend_click/test_v07_votes.py` turns **PASS** with a
     raw artifact: one "Vezi sursa originală ↗" anchor, `href` exactly equal to
     the live `/api/votes/{id}` wrapper's `data.source_url`, `target=_blank`,
     `rel` containing `noopener` and `noreferrer`.
  2. All other V-07 IDs keep their prior PASS/SKIP status; reconciliation still
     has exactly the 14 inventory IDs.
  3. Type check passes: no `any` cast added, `VoteDetailResponse` matches the
     backend envelope, and no other client method is changed.
  4. Labels, provenance semantics, `ProvenanceStamp`, backend and all other
     endpoints are byte-identical; diff is exactly the three exclusive files.
  5. All gates exit 0; four vault gates clean; `_generated/*` regenerated, not
     hand-edited.
- **Side-quest policy.** No backend edit, no envelope change, no label/i18n
  change, no `get<T>` change, no change to L-25's files or other agents' tests,
  no data/config/workflow/deployment edit; a FAIL/SKIP is never suppressed to
  obtain a PASS; new findings become new recipes after supervisor approval.

## 3. Regression test requirement

```bash
cd /home/nedaktov/parlament-deschis
python3 -m pytest tests/frontend_click/test_v07_votes.py -q
```

In `tests/frontend_click/test_v07_votes.py`, the C04-012 check must:

- fetch the live detail payload and take the source URL from the **wrapper**,
  `payload["data"]["source_url"]` (not `payload["source_url"]`);
- open a vote detail and assert `provenance_anchor_count >= 1`, the anchor's
  `href == payload["data"]["source_url"]`, `target == "_blank"`, `rel`
  contains both `noopener` and `noreferrer`, and the translated label is visible;
- write the fresh result and raw artifact under the `v07-*` prefix; the status
  in `v07-results.json` for C04-012 must be PASS.

The test records findings as rows and keeps pytest exit 0, so the verdict must
come from the result JSON status, not pytest's exit code alone (fleet §3). If no
live vote detail with `data.source_url` exists, mark the item SKIP/AMBER with a
named resolver — never PASS.

## 4. Wave placement and authority

- **W15**, branch `repair/links-w15`, from the current integration branch after
  the fleet (W13) and after W14/L-25; it is a **separate wave with disjoint
  files** from L-25 (see §2). One shared backup at
  `/tmp/opencode/backups/link-repair/W15` verified before the edit, one atomic
  commit, W15 section in
  [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) with backup
  evidence, diff, checkpoint SHA, gate table, before/after result statuses and
  the §F supervisor sign-off. The supervisor issues one GREEN/AMBER/RED verdict
  for L-26 using §C/§D/§E.
- **No merge to `main`, PR merge, push to `main`, deploy or branch-protection
  change.** The earlier programme was owner-merged to `main@863b200e…`; any
  further rollout is a separate owner gate recorded in the vault
  ([STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §9). Integration is `--ff-only`
  into the integration branch only, and only on GREEN.

## See also

[LINK-PAGINATION-CORRECTION](LINK-PAGINATION-CORRECTION-2026-11-23.md) (W14, disjoint files) ·
[CLICK-VALIDATION-FLEET](CLICK-VALIDATION-FLEET-2026-11-23.md) §5–§6 ·
[CONSISTENCY-STEPS](LINK-REPAIR-CONSISTENCY-STEPS-2026-11-22.md) §2–§3 ·
[RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) ·
[SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §C/§D/§E ·
[JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) ·
[C-04](../40-FRONTEND/CLICK-INV-C04-VOTES-2026-11-22.md)
