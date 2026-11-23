---
id: LINK-PAGINATION-CORRECTION
type: runbook
title: "L-25 corrective recipe — Traseism ledger pagination regression (2026-11-23)"
description: "Supervisor verdict on the V-03 C02-026/027 FAIL and a minimal corrective recipe that keeps the L-06 no-out-of-range-page goal while letting react-query pending/cached states advance the ledger; a planning note, not an execution."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/frontend]
source_paths: [60-EVIDENCE/CLICK-VALIDATION-V03-2026-11-23.md, 20-DIRECTION/CLICK-VALIDATION-FLEET-2026-11-23.md, 20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md, 50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md]
source_commit: 863b200e1adc70aadb289fdd4df52a7e5be2c483
created: 2026-11-23
updated: 2026-11-23
---

# L-25 — Traseism ledger pagination correction (2026-11-23)

## 1. Verdict on the validation FAIL

**This is a genuine product defect, and it is a regression introduced by
W2/L-06's clamp effect.** It is not a harness error and not a data-dependent
SKIP. The agent's hypothesis is **substantially correct but incomplete on one
point**, stated precisely below.

### Evidence actually observed

- `v03-evidence-C02-027.json`: clicking Next fired
  `GET /api/traseism/switches?legislature=2024&chamber=deputies&limit=25&offset=25`
  (HTTP 200, 20 rows), yet `'Pagina 2 din'` stayed `false`, Previous stayed
  disabled, the counter remained `Pagina 1 din 2`, the first row was unchanged
  (`Alexandrin MOISEEV …`), and no further request occurred — polled for
  **10,671 ms**.
- `v03-evidence-C02-026.json`: Previous is a *dependent* FAIL — it can never be
  enabled because page index 0 is never left (156 ms, same counter).
- `v03-runtime.json`: served HEAD `e82e01b9152266bf3fe862029946b24acc2032f8`
  (the code read for this verdict), `ledger_total=45`, `limit=25` → two pages
  exist, so Next should work.
- `v03-console.json`: 28 errors, all flagged `induced=true` from the harness's
  forced HTTP 500 on retry handlers; **non-induced errors = 0**. The failure is
  therefore not a JS exception.

### Root cause from code, checked independently

At `frontend/src/pages/Traseism.tsx:292-314`:

```
292: const [page, setPage] = useState(0);
298-307: useQuery({ queryKey: ["traseism-switches", legislature, chamber, page, ...scopeKey],
                    queryFn: … offset: page * PAGE_SIZE … });
309: const rows  = query.data?.rows ?? [];
310: const total = query.data?.total ?? 0;
311: const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
312-314: useEffect(() => { setPage((p) => Math.min(p, totalPages - 1)); }, [totalPages]);
```

Sequence on a Next click from page 0 with `total=45`:

1. `:424` `setPage(p => p + 1)` → `page=1` → **new query key** (`:299`).
2. There is no `placeholderData`/`keepPreviousData` on this query, so while the
   new key is pending `query.data` is `undefined` → `:310` `total=0` →
   `:311` `totalPages=1`.
3. The clamp effect's only dependency `totalPages` changed `2 → 1`, so it runs
   `:313` `setPage(p => Math.min(1, 0))` → **`page=0`**.
4. The query key returns to the page-0 key. `frontend/src/router.tsx:589`
   `staleTime: 60 * 60 * 1_000` makes the cached page-0 payload fresh, so
   react-query serves it with **no refetch** — rows, counter and Previous
   snap back to the initial state. The `offset=25` response (200) is discarded.

**Correction to the agent's hypothesis:** `staleTime=1h` is *not* the cause; it
only makes the snap-back silent (no second request). The root cause is the
unconditional clamp at `:312-314` firing on a transient `total=0` that comes
from a **pending, differently-keyed query**, not from a real shrink of the
corpus. The separate scope-reset effect at `:294-296` (`[legislature, chamber]`)
is not implicated: the scope did not change during the click.

### Why this is a W2/L-06 regression

[RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) L-06 step 2 prescribed exactly the
clamp now at `:312-314`; [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md)
W2 :640 records L-06 as `624e159… fix(pagination): L-06 correct next-page bounds`
and :737 records "L-06 bounds … PASS per gates and browser captures". Before
L-06 there was no clamp, so Next advanced normally. L-06 fixed the *out-of-range
page* problem by adding an effect that now prevents *any* forward page change
while a new query is pending — the fix traded one defect for another.

**Evidence-discipline note:** the W2 browser section (:652-670) records footer,
dashboard-card and wave-click captures, **not** a Next-click capture on
`/traseism`. The "PASS per … browser captures" claim at :737 is therefore
supported by gates and code review, not by an actual pagination click. This is
why the regression escaped W2 and why the fleet's click-level test (V-03) was
needed. It does not change the W2 verdict; it records how the gap slipped through.

## 2. Corrective recipe L-25 (wave W14)

- **Objective.** Make Next/Previous advance and retreat correctly with
  react-query's pending/cached states, while **keeping** L-06's original goal
  (no out-of-range page after the total shrinks). Minimal change only.
- **Evidence anchor.** `v03-evidence-C02-027.json`, `v03-evidence-C02-026.json`,
  `v03-runtime.json`, `v03-console.json`; `frontend/src/pages/Traseism.tsx:292-314,414-426`;
  `frontend/src/router.tsx:589`; [C-02](../40-FRONTEND/CLICK-INV-C02-OVERVIEW-2026-11-22.md)
  rows C02-026/027; [W2 record](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md)
  :640, :737; [RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) L-06 step 2.
- **Exclusive files (exact, repo-relative).**
  - `frontend/src/pages/Traseism.tsx`
  - `tests/frontend_click/test_v03_traseism.py`
  Nothing else — in particular `frontend/src/router.tsx`, `frontend/src/i18n.ts`,
  data, config, workflows, other agents' test files and `_generated/*` are
  **out of scope**.
- **Steps (exact commands and code intent).**
  1. Re-read the anchors:
     ```bash
     cd /home/nedaktov/parlament-deschis
     grep -n "totalPages\|setPage\|queryKey\|staleTime" frontend/src/pages/Traseism.tsx frontend/src/router.tsx
     cat /tmp/opencode/click-validation/v03-evidence-C02-027.json
     ```
  2. Verify the W14 backup before the first edit: bundle, `pre.sha`,
     `pre.status`, worktree archive and `SHA256SUMS` under
     `/tmp/opencode/backups/link-repair/W14` with fully expanded paths per
     [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §5; `git bundle verify`,
     `tar -tzf` and `sha256sum -c` must all exit 0 and their output must be
     committed in the W14 vault section before the edit (G2/R3, S-14).
  3. **Minimal source change** in `frontend/src/pages/Traseism.tsx` — replace
     only the clamp effect at `:312-314`:

     ```tsx
     // before
     useEffect(() => {
       setPage((p) => Math.min(p, totalPages - 1));
     }, [totalPages]);

     // after
     useEffect(() => {
       if (!query.isSuccess) return; // a newly-keyed, pending query has total=0
       setPage((p) => Math.min(p, totalPages - 1));
     }, [query.isSuccess, totalPages]);
     ```

     **Justification from code:** `total`, hence `totalPages`, is derived from
     `query.data` (`:309-311`) and is `0` while a new key is pending. Guarding
     on `query.isSuccess` means the clamp only reacts to a **known** total —
     exactly the L-06 case (a successful query whose corpus shrank) — and never
     to a loading placeholder. The dependency list changes from `[totalPages]`
     to `[query.isSuccess, totalPages]` so the effect re-arms when the query
     first succeeds. No new import, no new dependency, no change to rendering.

  4. **Do not change:** the scope-reset effect at `:294-296`; the query key or
     `offset` at `:298-307`; `PAGE_SIZE`; `router.tsx:589` `staleTime`; the
     `disabled` predicates at `:418`/`:425`. These are outside the defect, and
     changing `staleTime` would alter global cache policy for every query
     (a side quest). A brief transient in which Next reads disabled while the
     page-1 query is pending is accepted; the regression test asserts the
     settled state after the data arrives.
  5. **Regression test change** in `tests/frontend_click/test_v03_traseism.py`:
     in `check_pagination_next` / `run_all`, after the C02-027 assertion for
     page 2, add a second-Next check. Discover at runtime a scope
     (`legislature` × `chamber`) from `/api/meta` whose
     `/api/traseism/switches?...&limit=25&offset=0` `total > 50`; navigate
     there, click Next once (assert `offset=25`, counter `Pagina 2 din N`, a
     distinct first row), then click Next again (assert `offset=50`, counter
     `Pagina 3 din N`, another distinct first row and Previous enabled). Write
     the result as an additional row with an `element_id` such as
     `C02-027/second-next` in the same v03 result JSON, with a raw artifact.
     If no scope has `total > 50`, record SKIP with the named resolver "rerun
     with a ledger scope whose total exceeds two pages" — never PASS. Keep all
     19 inventory IDs exactly once; the extra row is a regression assertion,
     not a new inventory element.
  6. Re-run gates and the V-03 test (§3), then write W14 vault records and
     request the supervisor verdict.
- **Checkpoint.**
  ```bash
  cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build && npm run i18n:check
  cd /home/nedaktov/parlament-deschis && node scripts/check_routes_nav.mjs
  cd /home/nedaktov/parlament-deschis && python3 scripts/vault_lint.py && python3 scripts/vault_sync.py --check && bash scripts/check-doc-truth.sh && git diff --check
  ```
  plus the V-03 pytest re-run below. All commands must exit 0 with working
  directory, command, exit code and output excerpt recorded.
- **Rollback.** `git revert <L-25-commit-sha>` (additive); verified bundle at
  `/tmp/opencode/backups/link-repair/W14/pre.bundle`. No reset, force-push or
  tag move. If the test change must also be withdrawn, both files revert in the
  single atomic L-25 commit.
- **Acceptance criteria.**
  1. `C02-027` and `C02-026` in `tests/frontend_click/test_v03_traseism.py`
     turn **PASS** with raw artifacts (counter advances to page 2, Previous
     becomes enabled, first row changes, Previous then returns to page 1).
  2. The second-Next check is PASS where a >2-page scope exists, or SKIP with
     the named resolver; it is never silently absent and never converted to PASS.
  3. L-06's original property still holds: after a scope change that shrinks
     the total, `page` is clamped to the last valid page with no empty page.
  4. Non-induced console errors remain zero (induced retry errors are recorded
     and labelled, not counted).
  5. Diff is exactly the two exclusive files; all gates exit 0; four vault
     gates clean; `_generated/*` regenerated, not hand-edited.
- **Side-quest policy.** No data, release-pin, config, workflow, backend,
  i18n, global cache-policy or deployment edit; no change to another agent's
  test file; no FAIL/SKIP suppressed to obtain a PASS; a new defect found during
  the fix becomes a new finding/recipe after supervisor approval, not a fix here.

## 3. Regression test requirement

Run after the source fix, on the same read-only local dev server (`5188`) and
serving HEAD recorded in the W14 note:

```bash
cd /home/nedaktov/parlament-deschis
python3 -m pytest tests/frontend_click/test_v03_traseism.py -q
```

- **PASS condition:** `C02-026` and `C02-027` flip from FAIL to PASS in the
  regenerated `/tmp/opencode/click-validation/v03-results.json`, each with an
  existing raw `v03-evidence-*.json` and screenshot; the second-Next assertion
  is PASS (or SKIP with its resolver); element reconciliation still has exactly
  the 19 V-03 IDs.
- The test file deliberately records findings as rows and keeps pytest exit 0;
  therefore the verdict must be read from the result JSON statuses, **not** from
  pytest's exit code alone (fleet contract §3 and the test's own docstring).
- If the dev server or a >2-page dataset is unavailable, mark the affected item
  AMBER/NOT PROVEN with a resolver (§C A2/A5) — never infer a pass from code
  review.

## 4. Wave placement and authority

- **W14**, branch `repair/links-w14`, from the current integration branch after
  the ten-agent fleet (W13) has completed and been signed off. One shared backup
  at `/tmp/opencode/backups/link-repair/W14` verified before the edit; one
  atomic commit; W14 section in
  [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) with backup
  evidence, diff, checkpoint SHA, gate table, before/after result statuses and
  the §F supervisor sign-off. The supervisor issues one GREEN/AMBER/RED verdict
  for L-25 using §C/§D/§E.
- **No merge to `main`, PR merge, push to `main`, deploy or branch-protection
  change.** The owner rollout already merged the earlier programme to
  `main@863b200e…`; any further rollout of this correction is a separate owner
  gate recorded in the vault ([STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §9;
  W7 owner-decision section of the journey). Integration is `--ff-only` into
  the integration branch only, and only on GREEN.

## See also

[CLICK-VALIDATION-FLEET](CLICK-VALIDATION-FLEET-2026-11-23.md) §5–§6 ·
[CONSISTENCY-STEPS](LINK-REPAIR-CONSISTENCY-STEPS-2026-11-22.md) §2–§3 ·
[RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) L-06, L-12 ·
[SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §C/§D/§E ·
[JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) W2 ·
[C-02](../40-FRONTEND/CLICK-INV-C02-OVERVIEW-2026-11-22.md)
