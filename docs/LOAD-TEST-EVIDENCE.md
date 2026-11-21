# Load-Test Evidence & Vercel Cron Watchdog Decision (W4.1 / W4.4)

**Date:** 2026-11-21 (UTC)
**Repo commit at time of run:** `afd19444900f1caacb71b6fd26c9cb9c7498ca3a` (`main`)
**Scope:** evidence only. No commits, pushes, deploys, or load against production/Render/Vercel.
**Mandate applied:** no guessing. Anything not provable offline is marked **NOT PROVEN** with owner/blocker.

---

## 0. Status summary

| Item | Status |
| --- | --- |
| Local load test (copied DB, loopback only) | **PROVEN** — 900 requests, 0 errors, exit 0 |
| Staging load test | **NOT PROVEN — no staging environment exists** (see §2) |
| Production / Render / Vercel load test | **NOT PROVEN — out of scope / explicitly banned** |
| Vercel Cron watchdog | **DEFERRED — do not implement** (dated decision, §4) |
| `vercel.json` changed | **No** — left byte-for-byte unchanged (§5) |

---

## 1. Staging status: NOT PROVEN

No staging environment is defined in this repository. Offline checks:

- `render.yaml` defines exactly one web service, `name: parlament-deschis`, `branch: main`,
  `plan: free` — a single production service, no staging service.
- `scripts/deploy-all.sh` states deployment is triggered by CI **on push to `main`**
  (Vercel Git integration + Render auto-deploy gated by `checksPass`). No staging target.
- `vercel.json` has one rewrite set pointing at
  `https://parlament-deschis.onrender.com` (production). No staging rewrite.
- `docs/CONTINUATION-STRATEGY-2026-11-21.md:159` lists "W4.1 staging load-test evidence"
  as the work item, confirming this is the requested evidence and that staging is not yet
  stood up.

**Therefore:** staging status is **NOT PROVEN**. The only load measurement in this document
is against a throwaway **local** instance started from a copied DB (§3). Provisioning a real
staging environment and re-running the same command there is **owner-only**.

---

## 2. Script contract (`scripts/load_test.py`)

`python3 scripts/load_test.py --help` is **not supported**. Raw output:

```
Traceback (most recent call last):
  File "/home/nedaktov/.local/lib/python3.12/site-packages/httpx/_transports/default.py", line 101, in map_httpcore_exceptions
    yield
  ...
httpcore.UnsupportedProtocol: Request URL is missing an 'http://' or 'https://' protocol.
...
httpx.UnsupportedProtocol: Request URL is missing an 'http://' or 'https://' protocol.
EXIT=1
```

Reading the script (lines 57–60, 118–119) gives the exact contract — **three positional
arguments, no flag parser**:

```
usage: python3 scripts/load_test.py [base_url] [workers] [rounds]
  base_url : default http://127.0.0.1:8931
  workers  : default 50
  rounds   : default 6
```

It warms up 3 endpoints once, then spawns `workers` threads, each doing `rounds` passes over:

- `GET /api/parties`
- `GET /api/persons/7ff93a68-a284-46a8-8571-3c2ab6f8aae3`
- `GET /api/analytics/switch-leaderboard?limit=20`

and reports p50/p95/p99/max per endpoint plus overall. Stated target in the script:
`p95 < 500 ms`.

---

## 3. Local load test — procedure, target, and raw output

### 3.1 Target isolation (proof it was local only)

The backend was started on loopback with `PARLAMENT_DB` pointing at a **throwaway copy** of
the DB under `/tmp`. Production DBs were never touched; no request left the host.

```
LT_DIR=$(mktemp -d /tmp/opencode/loadtest.XXXXXX)
# -> /tmp/opencode/loadtest.jKg4Aq

# consistent SQLite online-backup copy (never the live/production DB file):
python3 - <<'PY'   # source = data/parlament-real.db (read-only URI)
src_con = sqlite3.connect("file:/home/nedaktov/parlament-deschis/data/parlament-real.db?mode=ro", uri=True)
dst_con = sqlite3.connect("/tmp/opencode/loadtest.jKg4Aq/parlament-local.db")
src_con.backup(dst_con)
PY
# backup bytes: 43589632 ; table person: 3388 rows

PARLAMENT_DB=/tmp/opencode/loadtest.jKg4Aq/parlament-local.db \
  nohup .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8931 \
  > /tmp/opencode/uvicorn.log 2>&1 &
# INFO: Uvicorn running on http://127.0.0.1:8931
# confirmed listener pid=2553958; port 8931 was free beforehand
```

Pre-flight (all 200):

```
GET /api/health -> 200
GET /api/parties -> 200
GET /api/persons/7ff93a68-a284-46a8-8571-3c2ab6f8aae3 -> 200
GET /api/analytics/switch-leaderboard?limit=20 -> 200
```

**Target:** `http://127.0.0.1:8931` (local). Not Render, not Vercel, not production.

### 3.2 Exact run command and environment

```
Start (UTC): 2026-11-21T13:18:15Z
End   (UTC): 2026-11-21T13:18:36Z
CWD: /home/nedaktov/parlament-deschis
Python: 3.12.3 ; httpx 0.28.1 ; fastapi 0.136.3 ; uvicorn 0.48.0

timeout 300 python3 scripts/load_test.py http://127.0.0.1:8931 50 6
Process exit code: 0
```

### 3.3 Complete raw output (verbatim)

```
Load test: 50 workers x 6 rounds x 3 endpoints
Target: p95 < 500 ms | http://127.0.0.1:8931

Completed 900 requests in 4.8s (189 req/s), errors: 0
     parties: n= 300 p50=  179.9 p95=  370.7 p99=  505.4 max=  535.9 ms [PASS]
      person: n= 300 p50=  175.3 p95=  283.1 p99=  300.3 max=  341.7 ms [PASS]
 leaderboard: n= 300 p50=  170.6 p95=  282.8 p99=  298.1 max=  390.1 ms [PASS]
     OVERALL: n= 900 p50=  175.3 p95=  297.6 p99=  423.0 max=  535.9 ms [PASS]

LOAD TEST PASS
```

### 3.4 Measurements (p50 / p95 / p99 in ms)

| Endpoint | n | p50 | p95 | p99 | max | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `/api/parties` | 300 | 179.9 | 370.7 | **505.4** | 535.9 | PASS (p95 < 500) |
| `/api/persons/{id}` | 300 | 175.3 | 283.1 | 300.3 | 341.7 | PASS |
| `/api/analytics/switch-leaderboard?limit=20` | 300 | 170.6 | 282.8 | 298.1 | 390.1 | PASS |
| **OVERALL** | **900** | **175.3** | **297.6** | **423.0** | **535.9** | **PASS** |

- Total: 900 requests in 4.8 s ≈ 189 req/s.
- **Errors: 0** (script counter), corroborated by the uvicorn log:
  `non-200 response lines: 0`, `ERROR/Traceback/Exception lines: 0`, `907 request log lines`
  (900 measured + 3 warm-up + 4 pre-flight curls).
- **Honest caveat:** the script's gate is p95 < 500 ms, which all endpoints pass. However the
  `/api/parties` **p99 = 505.4 ms and max = 535.9 ms exceed 500 ms**. The unweighted tail is
  above 500 ms on that one endpoint; this is reported, not hidden by the PASS label.
- Server was shut down afterwards; `ss -ltnp | grep :8931` confirmed the port was released.

### 3.5 What was and was not measured

- **Measured:** warm in-process latency of three hot read endpoints on a single uvicorn
  worker with a local SQLite copy of the corpus (3,388 persons), 50 concurrent client threads.
- **Not measured:** multi-worker/concurrency limits, CDN/rewrite behaviour, Render cold
  starts, network latency, DB write contention, or any staging/production condition.
  This is a **local baseline only**; it does not prove staging or production performance.

---

## 4. Vercel Cron watchdog — decision (dated 2026-11-21): **DEFER / DO NOT IMPLEMENT**

### 4.1 Decision

**Do not add a `crons` key to `vercel.json`.** `vercel.json` is left unchanged. Rationale:
there is no Vercel-runnable endpoint in this repo, so any configured cron path would either
404 or proxy to Render with no offline proof of a 200 + useful action. Per the mandate, that
is **NOT PROVEN**, so no cron is added.

### 4.2 Local verification — no function / API route exists (raw output)

```
root-level function dirs (Vercel convention):
  absent: api
  absent: functions
  absent: pages/api
  absent: .vercel/output/functions
  absent: frontend/api
  absent: frontend/pages/api
  absent: frontend/src/pages/api
  absent: frontend/app/api

vercel/serverless keywords in tracked config/source: (none found)
frontend/dist contents: index.html, favicon.svg, assets/*.js, assets/*.css  (static only)
grep -n 'cron' vercel.json  ->  no 'cron' key in vercel.json
```

`vercel.json` is a Vite SPA build (`outputDirectory: frontend/dist`) whose only `/api`
behaviour is a **rewrite** to `https://parlament-deschis.onrender.com`. A rewrite is a
proxy, not a Vercel Function. There is no build output directory
(`.vercel/output/functions`) and no API route handler anywhere in the tracked tree.

### 4.3 Official documentation research (sources)

1. **https://vercel.com/docs/cron-jobs** (canonical `/docs/schedules/cron-jobs`,
   last updated 2026-09-16):
   > "Vercel supports cron jobs for **Vercel Functions**. Cron jobs can be added through
   > `vercel.json` or the Build Output API."
   >
   > "To trigger a cron job, Vercel makes an HTTP GET request to your project's **production
   > deployment URL**, using the `path` provided in your project's `vercel.json` file."

2. **https://vercel.com/docs/cron-jobs/quickstart** (canonical
   `/docs/schedules/cron-jobs/quickstart`, last updated 2026-08-11):
   - Prerequisites include "A project … with a **Vercel Function**."
   - "You will learn how to create a cron job … by **creating a Vercel Function** and
     configuring it in your `vercel.json` file."
   - The cron's `path` targets a function file such as `api/hello.js` (framework: other) or
     `app/api/hello/route.ts` (Next.js) — none of which exist here.

3. **https://vercel.com/docs/cron-jobs/manage-cron-jobs** (canonical
   `/docs/schedules/cron-jobs/manage-cron-jobs`, last updated 2026-08-11):
   - "Handling nonexistent paths — **If you create a cron job for a path that doesn't exist,
     it generates a 404 error. However, Vercel still executes your cron job.**"
   - "Cron jobs are API routes."
   - "Vercel will not retry an invocation if a cron job fails."
   - "Cron jobs run only on production deployments."
   - Troubleshooting: run `vercel build --prod` and confirm `.vercel/output/config.json`
     contains a `crons` array with the job.

**Conclusion from sources:** a Vercel Cron requires a real Vercel Function/route handler at
the configured `path`. Pointing it at a non-existent path produces a 404 on every invocation
while still consuming the scheduled run — exactly the "cron that would 404" the task warns
against.

### 4.4 Why implementation was rejected

- No function source exists → a cron `path` cannot resolve to a Vercel Function.
- A `/api/...` cron path would be caught by the rewrite and forwarded to Render. Whether
  that remote endpoint returns 200 **and performs useful watchdog work** cannot be proven
  offline without hitting production (banned by the task) → **NOT PROVEN**.
- The repo's own design already classifies this as optional and owner-gated:
  - `docs/SELF-SUSTAINABILITY-ARCHITECTURE.md:135` — "Evaluate a daily Vercel Hobby Cron
    watchdog **only if** inactivity-related schedule suspension becomes a practical risk;
    it requires a narrowly scoped GitHub App credential stored in Vercel …"
  - `:176-179` — "Vercel: use it for the static frontend and API rewrite, not as the source
    of truth … A Vercel Hobby Cron may be a watchdog, but its once-per-day limit and timing
    jitter make it a fallback trigger, not a reliability guarantee."
  - `:204-206` — "Phase 4: GitHub scheduling remains best-effort. **The optional Vercel
    Cron watchdog is not configured** …"
  - `:278-281` — "Decide whether the optional Vercel Cron watchdog is warranted. If enabled,
    install a GitHub App with workflow-dispatch permission and store its private key/IDs as
    Vercel environment secrets …"

**Alternative already in place:** `.github/workflows/data.yml` already opens/updates a
deduplicated GitHub issue titled **"Automated dataset refresh/deployment failure"** on
failure and closes it on success (steps "Report refresh or deployment failure" /
"Close failure issue on success"). `/api/health/ready` and the frontend stale-data warning
also report status. Status reporting therefore exists without adding a 404-prone cron.

**Dated decision (2026-11-21):** DROP for now / DEFER to owner — implement only after a real
Vercel Function endpoint exists, an owner decision authorizes the watchdog, and the required
GitHub App credential is provisioned. No `vercel.json` edit made.

---

## 5. Owner-only / NOT PROVEN register

| Item | Status | Owner / blocker |
| --- | --- | --- |
| Staging load test | **NOT PROVEN** | No staging env exists; owner must provision one and re-run §3.2 command against it. |
| Production / Render / Vercel load test | **NOT PROVEN** | Out of scope / banned in this task. |
| Render endpoint returning 200 + doing useful watchdog work | **NOT PROVEN** | Requires production verification (banned here) + owner decision. |
| Vercel Cron `crons` registration in `.vercel/output/config.json` | **NOT PROVEN** | Requires a real function + `vercel build --prod`; no function exists. |
| Watchdog activation (GitHub App credential in Vercel) | **NOT PROVEN** | Owner-only, per strategy doc §4.4. |

---

## 6. Verification performed on this change set

- Only new file: `docs/LOAD-TEST-EVIDENCE.md`. `vercel.json` and all source files untouched.
- `git diff --check` → clean (see raw output below).
- `python3 -m json.tool vercel.json >/dev/null` → *(see raw result below)* — run as a sanity
  check even though the file was not modified.
- Banned-literal scan of this document for the false-claim markers listed in the task
  (a "zero JS errors" phrase, the phone-number-style domain, and the fake data-release tag)
  → none present.

### Raw verification output

```
$ git diff --check
(no output — clean)

$ python3 -m json.tool vercel.json >/dev/null && echo VALID_JSON
VALID_JSON
```
