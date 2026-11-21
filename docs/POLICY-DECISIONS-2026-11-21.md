# Policy decisions — 2026-11-21

Three open product/security decisions from the continuation program are closed
here with evidence, implementation, verification and rollback. Rule: no guessing
— each decision cites the observed state that forced it.

## P-1 — Polling / "real-time" alerts

**Decision:** remove all 60-second client polls; switch alerts now mean
"new in this data release", not "real-time".

**Evidence:** `render.yaml:28` sets `PARLAMENT_POLL_INTERVAL_MIN: ""` (poller
disabled); the API is read-only and the dataset is baked into the image; the
live `/api/health` reports `sources.cdep/senat: "never_run"`. A 60 s poll
against immutable data cannot produce new events and contradicts
`docs/REMEDIATION-STRATEGY.md:76` ("Do not keep a 60 s poll against immutable
data").

**Implementation:** `refetchInterval: 60_000` removed from
`frontend/src/components/LiveFeed.tsx` (events + health) and
`frontend/src/components/Footer.tsx` (health). Queries still refresh on mount
and window focus. ro/en `switchAlerts.title` now says "in this data release".

**Verification:** `grep -rn '60_000' frontend/src` → 0; `npm run lint`, build,
24-route UI gate green. **Rollback:** revert the commit; no data or schema change.

## P-2 — Content Security Policy

**Decision:** enforce CSP (change `Content-Security-Policy-Report-Only` to
`Content-Security-Policy`) with the **same byte-identical value** in
`backend/main.py` and `vercel.json`.

**Evidence:** report-only headers block nothing, so claiming protection from
them is a false green (QA gate research, SLSA verification principle). The
policy is intentionally permissive (`'unsafe-inline'`, `'unsafe-eval'`, data:
images/fonts) because the current SPA needs those permissions; the security
gain is `default-src 'self'`, `base-uri 'self'`, `object-src 'none'` and
`frame-ancestors 'none'`. Both layers previously matched byte-for-byte, so the
swap is symmetric and verifiable.

**Implementation:** header key renamed in both files; value unchanged.

**Verification:** programmatic byte-equality check of both values; live
`curl -sI` must show an enforcing `Content-Security-Policy` header on Vercel
static assets and Render `/api/*`; 24-route browser gate must stay green after
deploy. **Rollback:** revert the two-file commit (report-only restored).
Residual: `'unsafe-inline'`/`'unsafe-eval'` remain necessary — tightening them
needs a separate frontend hardening recipe with staging evidence.

## P-3 — Blog / SEO / donations

**Decision:** **drop from active scope**; keep `docs/BLOG-SEO-AND-HOSTING-STRATEGY.md`
as historical strategy only. No blog routes, no donation UI.

**Evidence:** the document itself says "strategy only; implementation has not
started" and requires owner inputs (donation recipient/checkout) that were
never supplied; no blog/article directories or routes exist in the tree
(master verification: `find` + `grep` on `frontend/src/router.tsx`). Building a
donation path without a verified recipient would be guessing.

**Implementation:** none (decision recorded, no code). Revisit only when an
owner supplies a recipient and a scoped editorial plan.

**Verification:** `grep -RIl 'donation' frontend/src` → no product code;
decision note committed. **Rollback:** none (no code changed).

## Implementation order and ownership

P-1 and P-2 are code changes on a branch + PR (branch protection requires
required checks to pass). P-3 is documentation only. All three are recorded in
the Obsidian vault's `ACTION-LOG` and `DECISIONS` notes.
