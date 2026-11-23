"""V-03 clickable validation — Traseism page (C02-021 ... C02-039).

Contract: CLICK-VALIDATION-FLEET-2026-11-23.md §2 (V-03), §3 (test contract),
CLICK-INV-C02-OVERVIEW-2026-11-22.md §1 inventory rows 021-039.

Every assigned ID is exercised in a real Chromium against the read-only local
dev server at http://127.0.0.1:5188. Data-driven values (legislature, ledger
source URL, sortable row data, pagination totals) are resolved from the live
API at runtime — no hard-coded UUIDs. One chromium instance per file, closed
in ``finally``. Each element writes a raw evidence JSON under the v03-* prefix.

A FAIL is a *finding*, not a harness error: the pytest test asserts that all 19
IDs were evaluated and that artifacts exist, so the fleet gate (pytest exit 0)
stays meaningful while FAIL/SKIP verdicts live in v03-results.json with evidence
and a named resolver for every SKIP.
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import time
import traceback
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import pytest

pytest.importorskip("playwright", reason="external Playwright validation tool; see scripts/ui_validate.py")
from playwright.async_api import async_playwright  # noqa: E402

BASE = "http://127.0.0.1:5188"
ROUTE = "/traseism"
CHROMIUM = "/usr/bin/chromium"
OUT = Path("/tmp/opencode/click-validation")
RESULTS = OUT / "v03-results.json"
CONSOLE = OUT / "v03-console.json"

# i18n ro labels (default locale) — used only where a structural locator is
# insufficient; structural locators (role/id/aria-*) are preferred.
RETRY_LABEL = "Reîncearcă"
LEDGER_HEADING = "Registrul schimbărilor"
PREV_LABEL = "Pagina anterioară"
NEXT_LABEL = "Pagina următoare"
SOURCE_LABEL = "sursa oficială"
ABOUT_LABEL = "Despre proiect și metodă"
ABOUT_TITLE = "Despre"
METHODOLOGY_URL = "https://github.com/nedaktov-ops/parlament-deschis/blob/main/docs/METHODOLOGY.md"

SORT_HEADERS = [
    ("C02-029", "Cameră", "Traseism.tsx:507"),
    ("C02-030", "Legislatura", "Traseism.tsx:508"),
    ("C02-031", "Membri în perimetrul de analiză (numitor)", "Traseism.tsx:509"),
    ("C02-032", "Schimbări de grup", "Traseism.tsx:510"),
    ("C02-033", "Parlamentari care au schimbat grupul", "Traseism.tsx:511"),
    ("C02-034", "Rata de traseism", "Traseism.tsx:512"),
    ("C02-035", "Schimbări la 100 de membri", "Traseism.tsx:513"),
]

# All 19 element IDs of this slice, in inventory order.
ALL_IDS = [f"C02-{n:03d}" for n in range(21, 40)]


class SkipElement(Exception):
    """A SKIP is only allowed with a named resolver (fleet contract §3.5)."""

    def __init__(self, message: str, resolver: str):
        super().__init__(message)
        self.resolver = resolver


class Ctx:
    """Shared browser/session state for the single pytest file."""

    def __init__(self) -> None:
        self.element = "SETUP"
        self.console: list[dict] = []
        self.requests: list[dict] = []
        self.rows: list[dict] = []
        self.forced_fail: str | None = None
        self.pages: list = []
        self.ledger_first_page0: str | None = None
        self.browser = None


CTX = Ctx()


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def api_get(path: str):
    """Read-only GET against the same local API the UI uses."""
    with urllib.request.urlopen(BASE + path, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def url_params(url: str) -> dict[str, str]:
    return {
        k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).items() if v
    }


def record(eid, line, action, expected, observed, verdict, details, evidence_path, resolver=None):
    """Write one result row plus its raw evidence artifact."""
    row = {
        "element_id": eid,
        "source_file_line": line,
        "action": action,
        "expected": expected,
        "observed": observed,
        "verdict": verdict,
        # fleet-contract schema (§3.4) — kept alongside the short task keys
        "expected_outcome": expected,
        "observed_outcome": observed,
        "status": verdict,
        "evidence_path": evidence_path,
    }
    if resolver:
        row["resolver"] = resolver
    CTX.rows.append(row)
    evidence = {
        "element_id": eid,
        "captured_at": now_iso(),
        "source_file_line": line,
        "action": action,
        "expected_outcome": expected,
        "observed_outcome": observed,
        "status": verdict,
        "details": details,
        "console_events": [c for c in CTX.console if c.get("element") == eid],
    }
    Path(evidence_path).write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[{verdict:4s}] {eid}  {action[:58]:58s}  {observed[:70]}")


async def guard(eid, line, action, expected, fn, screenshot=None):
    """Run one element check, capture FAIL/SKIP/PASS and never abort the fleet."""
    CTX.element = eid
    started = time.time()
    # Element ids containing '/' (e.g. the C02-027/second-next regression row)
    # are kept verbatim in results but flattened for on-disk artifact names.
    safe_eid = eid.replace("/", "-")
    path = str(OUT / f"v03-evidence-{safe_eid}.json")
    details: dict = {}
    try:
        result = await fn()
        verdict = result.get("verdict", "PASS")
        observed = result.get("observed", "")
        details = result.get("details", {})
        resolver = result.get("resolver")
        if verdict == "SKIP" and not resolver:
            resolver = "unspecified resolver — rerun this element on local dev"
        if screenshot and verdict in ("PASS", "FAIL"):
            try:
                shot = str(OUT / f"v03-shot-{safe_eid}.png")
                await screenshot(shot)
                details["screenshot"] = shot
            except Exception as exc:  # noqa: BLE001 - screenshot is supplementary
                details["screenshot_error"] = str(exc)[:200]
    except SkipElement as exc:
        verdict, observed, resolver = "SKIP", str(exc), exc.resolver
        details = {"resolver": resolver}
    except Exception as exc:  # noqa: BLE001 - a harness error is a FAIL finding
        verdict = "FAIL"
        observed = f"harness exception: {type(exc).__name__}: {exc}"
        details = {"traceback": traceback.format_exc()[-2500:]}
        resolver = None
    details["elapsed_ms"] = round((time.time() - started) * 1000)
    details["page_url"] = getattr(getattr(CTX, "page", None), "url", None)
    record(eid, line, action, expected, observed, verdict, details, path, resolver)


def attach_listeners(page):
    # Capture the owning element at page-creation time: retry pages keep
    # loading in the background after the action moves on, so tagging at
    # event time would misattribute their forced 500s to later elements.
    forced = CTX.forced_fail

    def on_console(msg):
        if msg.type == "error":
            CTX.console.append(
                {
                    "ts": now_iso(),
                    "element": forced or CTX.element,
                    "type": "console.error",
                    "text": msg.text[:500],
                    "page_url": page.url,
                    "induced": bool(forced),
                    "induced_reason": (
                        "validation harness forced HTTP 500 to exercise retry" if forced else None
                    ),
                }
            )

    def on_pageerror(exc):
        CTX.console.append(
            {
                "ts": now_iso(),
                "element": forced or CTX.element,
                "type": "pageerror",
                "text": str(exc)[:500],
                "page_url": page.url,
                "induced": bool(forced),
                "induced_reason": (
                    "validation harness forced HTTP 500 to exercise retry" if forced else None
                ),
            }
        )

    def on_request(req):
        CTX.requests.append(
            {
                "ts": now_iso(),
                "element": CTX.element,
                "method": req.method,
                "url": req.url,
            }
        )

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)
    page.on("request", on_request)
    CTX.pages.append(page)


async def click_external_and_capture(page, anchor, expected_url):
    """Click a target=_blank anchor and capture the popup's navigation target.

    A fresh popup starts at about:blank, so its URL must be polled rather than
    read immediately; the popup's requests are also logged as raw evidence.
    """
    popup = None
    popup_url = None
    try:
        async with page.expect_popup(timeout=12_000) as info:
            await anchor.click()
        popup = await info.value
        attach_listeners(popup)

        async def resolved():
            u = popup.url
            return u if u and u.startswith(expected_url) else None

        popup_url = await poll_until(resolved, timeout=10.0)
        if not popup_url:
            popup_url = popup.url or ""
    except Exception as exc:  # noqa: BLE001 - captured as a finding, never hidden
        popup_url = f"popup-capture-failed: {type(exc).__name__}: {exc}"
    finally:
        if popup is not None:
            try:
                await popup.close()
            except Exception:  # noqa: BLE001
                pass
    return popup_url


async def open_page(context, fail_pattern=None, url=None):
    """New page, listeners, optional single-endpoint failure, bounded settle.

    ``url`` allows a specific scope (legislature × chamber) to be loaded for a
    regression check; it defaults to the route root.
    """
    page = await context.new_page()
    attach_listeners(page)
    if fail_pattern is not None:

        async def fail(route):
            CTX.console.append(
                {
                    "ts": now_iso(),
                    "element": CTX.element,
                    "type": "harness-route",
                    "text": f"forced HTTP 500 on {route.request.url[:300]}",
                    "page_url": page.url,
                    "induced": True,
                    "induced_reason": "validation harness forced HTTP 500 to exercise retry",
                }
            )
            await route.fulfill(
                status=500, content_type="application/json", body='{"detail":"v03-forced-error"}'
            )

        await page.route(re.compile(fail_pattern), fail)
    await page.goto(url or (BASE + ROUTE), wait_until="load", timeout=45_000)
    try:
        await page.wait_for_load_state("networkidle", timeout=12_000)
    except Exception:  # noqa: BLE001 - bounded, then fixed settle (fleet §3.2)
        pass
    await page.wait_for_timeout(3_500)
    CTX.page = page
    return page


async def poll_until(predicate, timeout=10.0, interval=0.1):
    """Poll a sync *or* async predicate until truthy; return its value or None."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if asyncio.iscoroutine(value):
            value = await value
        if value:
            return value
        await asyncio.sleep(interval)
    return None


# --------------------------------------------------------------------------- #
# element checks
# --------------------------------------------------------------------------- #


async def check_chamber(page, index, expected_chamber):
    buttons = page.locator('div[role="group"][aria-labelledby="traseism-chamber-label"] button')
    if await buttons.count() != 2:
        return {
            "verdict": "FAIL",
            "observed": f"expected 2 chamber buttons, found {await buttons.count()}",
        }
    btn = buttons.nth(index)
    label = (await btn.inner_text()).strip()
    before = url_params(page.url)
    await btn.click()
    after = await poll_until(
        lambda: (
            url_params(page.url).get("chamber") == expected_chamber
            and urllib.parse.urlsplit(page.url).path == ROUTE
        ),
        timeout=8.0,
    )
    after_p = url_params(page.url)
    pressed = [await buttons.nth(i).get_attribute("aria-pressed") for i in range(2)]
    ok = (
        bool(after)
        and after_p.get("chamber") == expected_chamber
        and pressed[index] == "true"
        and urllib.parse.urlsplit(page.url).path == ROUTE
    )
    return {
        "verdict": "PASS" if ok else "FAIL",
        "observed": (
            f"clicked '{label}': URL chamber={after_p.get('chamber')!r} "
            f"(was {before.get('chamber')!r}), path={urllib.parse.urlsplit(page.url).path}, "
            f"aria-pressed={pressed}, still-on-route={after}"
        ),
        "details": {
            "label": label,
            "before_params": before,
            "after_params": after_p,
            "aria_pressed": pressed,
            "path": urllib.parse.urlsplit(page.url).path,
        },
    }


async def check_legislature(page):
    sel = page.locator("#traseism-legislature")
    if await sel.count() != 1:
        return {"verdict": "FAIL", "observed": "legislature select #traseism-legislature not found"}
    current = await sel.input_value()
    options = [
        o
        for o in await sel.locator("option").evaluate_all("(els) => els.map(e => e.value)")
        if o and o != current
    ]
    if not options:
        raise SkipElement(
            "no alternative legislature option in the live selector",
            "data-dependent — rerun when /api/meta exposes >1 legislature",
        )
    target = options[0]
    before = url_params(page.url).get("legislature")
    await sel.select_option(value=target)
    ok = await poll_until(lambda: url_params(page.url).get("legislature") == target, timeout=8.0)
    after = url_params(page.url).get("legislature")
    sel_value = await sel.input_value()
    requests = [
        r["url"]
        for r in CTX.requests
        if "/api/traseism/" in r["url"] and f"legislature={target}" in r["url"]
    ]
    passed = (
        bool(ok)
        and after == target
        and sel_value == target
        and urllib.parse.urlsplit(page.url).path == ROUTE
    )
    return {
        "verdict": "PASS" if passed else "FAIL",
        "observed": (
            f"selected {target}: URL legislature={after!r} (was {before!r}), "
            f"select value={sel_value!r}, refetched endpoints={len(requests)}"
        ),
        "details": {
            "before": before,
            "target": target,
            "after": after,
            "select_value": sel_value,
            "refetch_urls": requests[:6],
        },
    }


async def check_source_anchor(context, page, legislature):
    path = f"/api/traseism/switches?legislature={legislature}&chamber=deputies&limit=25&offset=0"
    payload = api_get(path)
    rows = payload.get("rows", [])
    sourced = [r for r in rows if r.get("source_url")]
    if not sourced:
        raise SkipElement(
            "no ledger row in the live payload exposes source_url",
            "data-dependent — rerun with a scope whose /api/traseism/switches rows carry source_url",
        )
    expected_url = sourced[0]["source_url"]
    anchors = page.locator(f'a[href="{expected_url}"]')
    if await anchors.count() == 0:
        return {
            "verdict": "FAIL",
            "observed": f"API row source_url {expected_url!r} has no matching ledger anchor",
        }
    anchor = anchors.first
    attrs = {
        "href": await anchor.get_attribute("href"),
        "target": await anchor.get_attribute("target"),
        "rel": await anchor.get_attribute("rel"),
        "text": (await anchor.inner_text()).strip(),
    }
    host = urllib.parse.urlsplit(expected_url).netloc

    async def stub(route):
        await route.fulfill(
            status=200,
            content_type="text/html",
            body="<html><title>v03-captured</title></html>",
        )

    await context.route(re.compile(re.escape(host)), stub)
    popup_url = await click_external_and_capture(page, anchor, expected_url)
    ok = (
        attrs["href"] == expected_url
        and attrs["target"] == "_blank"
        and "noopener" in (attrs["rel"] or "")
        and "noreferrer" in (attrs["rel"] or "")
        and SOURCE_LABEL in attrs["text"]
        and bool(popup_url)
        and popup_url.startswith(expected_url)
    )
    return {
        "verdict": "PASS" if ok else "FAIL",
        "observed": (
            f"anchor href={attrs['href']!r} (API source_url={expected_url!r}), "
            f"target={attrs['target']!r}, rel={attrs['rel']!r}, text={attrs['text']!r}, "
            f"popup navigated to {popup_url!r}"
        ),
        "details": {
            "api_source_url": expected_url,
            "attributes": attrs,
            "popup_url": popup_url,
            "sourced_rows": len(sourced),
        },
    }


async def check_pagination_next(page, total):
    if total <= 25:
        raise SkipElement(
            f"live ledger total={total} <= PAGE_SIZE=25 — Next is correctly disabled",
            "data-dependent — rerun with a scope whose /api/traseism/switches total > 25",
        )
    nxt = page.get_by_role("button", name=NEXT_LABEL, exact=True)
    prev = page.get_by_role("button", name=PREV_LABEL, exact=True)
    assert await nxt.count() == 1 and await prev.count() == 1, "pagination buttons missing"
    assert await prev.is_disabled(), "Previous must start disabled at page 0"
    sec = page.locator('section:has(h2:text-is("Registrul schimbărilor"))')
    ledger_rows = sec.locator("tbody tr")

    def counters(text):
        return [line for line in text.split("\n") if "Pagina " in line]

    before_counter = counters(await sec.inner_text())
    before_first = (
        (await ledger_rows.first.inner_text()).split("\n")[0][:80]
        if await ledger_rows.count()
        else None
    )
    since = len(CTX.requests)
    await nxt.click()
    hit = await poll_until(
        lambda: next(
            (
                r
                for r in CTX.requests[since:]
                if "/api/traseism/switches" in r["url"] and "offset=25" in r["url"]
            ),
            None,
        ),
        timeout=12.0,
    )

    async def page2_ready():
        text = await page.locator("body").inner_text()
        return ("Pagina 2 din" in text) and (not await prev.is_disabled())

    # React needs a render tick after the request fires: poll the UI state.
    ready = await poll_until(page2_ready, timeout=10.0)
    text = await page.locator("body").inner_text()
    page2 = "Pagina 2 din" in text
    prev_enabled = not await prev.is_disabled()
    after_counter = counters(await sec.inner_text())
    after_first = (
        (await ledger_rows.first.inner_text()).split("\n")[0][:80]
        if await ledger_rows.count()
        else None
    )
    requests_after = [
        r["url"] for r in CTX.requests[since:] if "/api/traseism/switches" in r["url"]
    ]
    shot = str(OUT / "v03-shot-C02-027.png")
    try:
        await page.screenshot(path=shot, full_page=False)
    except Exception:  # noqa: BLE001 - screenshot is supplementary
        shot = None
    # L-25 regression: the ledger must not only say "Pagina 2" — the rendered
    # rows must actually be a different page's rows.
    row_changed = bool(before_first and after_first and before_first != after_first)
    CTX.ledger_first_page0 = before_first  # consumed by check_pagination_prev
    ok = bool(hit) and bool(ready) and page2 and prev_enabled and row_changed
    return {
        "verdict": "PASS" if ok else "FAIL",
        "observed": (
            f"Next click fired {hit['url'] if hit else 'NO offset=25 request'}; "
            f"'Pagina 2 din' visible={page2}; Previous enabled={prev_enabled}; "
            f"first row changed={row_changed}; "
            f"counter {before_counter} -> {after_counter}; first row "
            f"{before_first!r} -> {after_first!r}; switches requests after click={requests_after}"
        ),
        "details": {
            "request": hit,
            "page2_visible": page2,
            "previous_enabled": prev_enabled,
            "first_row_changed": row_changed,
            "total": total,
            "ui_polled_ready": bool(ready),
            "counter_before": before_counter,
            "counter_after": after_counter,
            "first_row_before": before_first,
            "first_row_after": after_first,
            "switches_requests_after_click": requests_after,
            "screenshot": shot,
            "finding_note": (
                "offset=25 request returns HTTP 200 with 20 rows, but the page counter "
                "and rows never advance; Traseism.tsx:312-314 clamp effect recomputes "
                "totalPages=1 while the newly-keyed query has no data (total=0), "
                "resetting page to 0; router.tsx:589 staleTime=1h then serves cached "
                "page-0 rows without a new request (confirmed by manual probe)."
            )
            if not ok
            else None,
        },
    }


async def check_pagination_prev(page):
    nxt = page.get_by_role("button", name=NEXT_LABEL, exact=True)
    prev = page.get_by_role("button", name=PREV_LABEL, exact=True)
    if await prev.is_disabled():
        sec = page.locator('section:has(h2:text-is("Registrul schimbărilor"))')
        counter = [line for line in (await sec.inner_text()).split("\n") if "Pagina " in line]
        shot = str(OUT / "v03-shot-C02-026.png")
        try:
            await page.screenshot(path=shot, full_page=False)
        except Exception:  # noqa: BLE001
            shot = None
        return {
            "verdict": "FAIL",
            "observed": (
                "Previous remains disabled after the Next click; ledger counter is still "
                f"{counter}; page never left index 0 (see C02-027 evidence)"
            ),
            "details": {
                "counter": counter,
                "previous_disabled": True,
                "screenshot": shot,
                "finding_note": (
                    "dependent on C02-027: Next fires offset=25 successfully but the clamp "
                    "effect resets page to 0, so Previous can never be enabled in practice."
                ),
            },
        }
    since = len(CTX.requests)
    await prev.click()
    hit = await poll_until(
        lambda: next(
            (
                r
                for r in CTX.requests[since:]
                if "/api/traseism/switches" in r["url"] and "offset=0" in r["url"]
            ),
            None,
        ),
        timeout=12.0,
    )

    async def page1_ready():
        text = await page.locator("body").inner_text()
        return ("Pagina 1 din" in text) and (not await nxt.is_disabled())

    ready = await poll_until(page1_ready, timeout=10.0)
    text = await page.locator("body").inner_text()
    page1 = "Pagina 1 din" in text
    next_enabled = not await nxt.is_disabled()
    sec = page.locator('section:has(h2:text-is("Registrul schimbărilor"))')
    ledger_rows = sec.locator("tbody tr")
    after_first = (
        (await ledger_rows.first.inner_text()).split("\n")[0][:80]
        if await ledger_rows.count()
        else None
    )
    first_page0 = getattr(CTX, "ledger_first_page0", None)
    restored = bool(first_page0 and after_first and after_first == first_page0)
    # router.tsx staleTime=1h means page 0 may be served from react-query's
    # cache (no fresh offset=0 request). The settled UI — counter back to
    # "Pagina 1 din N", Next enabled, original rows rendered — is the proof.
    ok = bool(ready) and page1 and next_enabled and restored
    screenshot = None
    if ok:
        screenshot = str(OUT / "v03-shot-C02-026.png")
        try:
            await page.screenshot(path=screenshot, full_page=False)
        except Exception:  # noqa: BLE001 - screenshot is supplementary
            screenshot = None
    return {
        "verdict": "PASS" if ok else "FAIL",
        "observed": (
            f"Previous click {'fired ' + hit['url'] if hit else 'served from cache (no offset=0 request)'}; "
            f"'Pagina 1 din' visible={page1}; Next enabled={next_enabled}; "
            f"first row restored to page 1={restored} ({first_page0!r} -> {after_first!r})"
        ),
        "details": {
            "request": hit,
            "page1_visible": page1,
            "next_enabled": next_enabled,
            "first_row_restored": restored,
            "first_row_page0": first_page0,
            "first_row_after": after_first,
            "ui_polled_ready": bool(ready),
            "screenshot": screenshot,
        },
    }


async def check_second_next(context, pages):
    """L-25 regression: two consecutive Next clicks advance 1 -> 2 -> 3.

    A single Next click is not enough to prove the clamp guard survives a
    second re-keying of the query. Discover (at runtime, from /api/meta) the
    legislature × chamber scope with the largest ledger total > 50, then
    exercise Next twice and assert request offsets, counters, distinct first
    rows and that Previous stays enabled.
    """
    meta = api_get("/api/meta")
    best = None
    for leg in sorted(meta.get("legislatures", {}).keys()):
        for chamber in ("deputies", "senate"):
            payload = api_get(
                f"/api/traseism/switches?legislature={leg}&chamber={chamber}&limit=25&offset=0"
            )
            total = int(payload.get("total", 0))
            if total > 50 and (best is None or total > best[2]):
                best = (leg, chamber, total)
    if best is None:
        raise SkipElement(
            "no /api/meta legislature × chamber scope exposes a ledger total > 50 "
            "(two pages) — a second Next cannot be exercised on the live data",
            "rerun with a ledger scope whose total exceeds two pages",
        )
    leg, chamber, total = best
    url = f"{BASE}{ROUTE}?date=2026-11-23&legislature={leg}&chamber={chamber}"
    page = await open_page(context, url=url)
    pages.append(page)

    nxt = page.get_by_role("button", name=NEXT_LABEL, exact=True)
    prev = page.get_by_role("button", name=PREV_LABEL, exact=True)
    sec = page.locator('section:has(h2:text-is("Registrul schimbărilor"))')
    ledger_rows = sec.locator("tbody tr")

    def counters(text):
        return [line for line in text.split("\n") if "Pagina " in line]

    async def first_row_text():
        return (
            (await ledger_rows.first.inner_text()).split("\n")[0][:80]
            if await ledger_rows.count()
            else None
        )

    counter0 = counters(await sec.inner_text())
    first0 = await first_row_text()
    since1 = len(CTX.requests)
    await nxt.click()
    hit1 = await poll_until(
        lambda: next(
            (
                r
                for r in CTX.requests[since1:]
                if "/api/traseism/switches" in r["url"] and "offset=25" in r["url"]
            ),
            None,
        ),
        timeout=12.0,
    )

    async def page2_ready():
        return ("Pagina 2 din" in await page.locator("body").inner_text()) and (
            not await prev.is_disabled()
        )

    ready1 = await poll_until(page2_ready, timeout=10.0)
    counter1 = counters(await sec.inner_text())
    first1 = await first_row_text()

    since2 = len(CTX.requests)
    await nxt.click()
    hit2 = await poll_until(
        lambda: next(
            (
                r
                for r in CTX.requests[since2:]
                if "/api/traseism/switches" in r["url"] and "offset=50" in r["url"]
            ),
            None,
        ),
        timeout=12.0,
    )

    async def page3_ready():
        return ("Pagina 3 din" in await page.locator("body").inner_text()) and (
            not await prev.is_disabled()
        )

    ready2 = await poll_until(page3_ready, timeout=10.0)
    counter2 = counters(await sec.inner_text())
    first2 = await first_row_text()
    prev_enabled = not await prev.is_disabled()

    shot = str(OUT / "v03-shot-C02-027-second-next.png")
    try:
        await page.screenshot(path=shot, full_page=False)
    except Exception:  # noqa: BLE001 - screenshot is supplementary
        shot = None

    page2_ok = "Pagina 2 din" in " ".join(counter1)
    page3_ok = "Pagina 3 din" in " ".join(counter2)
    rows_distinct = bool(first0 and first1 and first2 and len({first0, first1, first2}) == 3)
    ok = bool(
        hit1
        and hit2
        and ready1
        and ready2
        and page2_ok
        and page3_ok
        and rows_distinct
        and prev_enabled
        and total > 50
    )
    return {
        "verdict": "PASS" if ok else "FAIL",
        "observed": (
            f"scope legislature={leg} chamber={chamber} total={total}; "
            f"Next#1 {hit1['url'] if hit1 else 'NO offset=25 request'} counter={counter1} "
            f"first row {first0!r} -> {first1!r}; "
            f"Next#2 {hit2['url'] if hit2 else 'NO offset=50 request'} counter={counter2} "
            f"first row -> {first2!r}; three distinct rows={rows_distinct}; "
            f"Previous enabled at page 3={prev_enabled}"
        ),
        "details": {
            "scope": {"legislature": leg, "chamber": chamber, "total": total},
            "initial_counter": counter0,
            "first_row_page1": first0,
            "request_1": hit1,
            "counter_after_next1": counter1,
            "first_row_page2": first1,
            "request_2": hit2,
            "counter_after_next2": counter2,
            "first_row_page3": first2,
            "three_distinct_first_rows": rows_distinct,
            "previous_enabled_at_page3": prev_enabled,
            "ui_polled_ready": [bool(ready1), bool(ready2)],
            "screenshot": shot,
        },
    }


async def check_retry(context, eid, fail_pattern, endpoint, scope_selector=None):
    CTX.forced_fail = eid
    try:
        page = await open_page(context, fail_pattern=fail_pattern)
    finally:
        CTX.forced_fail = None
    if scope_selector:
        err = page.locator(scope_selector).locator(
            '[data-state="error"] button[aria-label="Reîncearcă"]'
        )
    else:
        err = page.locator('[data-state="error"] button[aria-label="Reîncearcă"]')

    async def retry_visible():
        return await err.count() > 0 and await err.first.is_visible()

    appeared = await poll_until(retry_visible, timeout=30.0)
    if not appeared:
        await page.close()
        return {
            "verdict": "FAIL",
            "observed": f"no retry button appeared for forced failure of {endpoint}",
        }
    error_text = (await err.first.locator('xpath=ancestor::div[@data-state="error"]').inner_text())[
        :200
    ]
    since = len(CTX.requests)
    await err.first.click()
    hit = await poll_until(
        lambda: next((r for r in CTX.requests[since:] if endpoint in r["url"]), None), timeout=15.0
    )
    ok = bool(hit)
    result = {
        "verdict": "PASS" if ok else "FAIL",
        "observed": (
            f"forced 500 on {endpoint}; error UI showed {error_text[:80]!r}; "
            f"Retry click fired {hit['url'] if hit else 'NO new request'}"
        ),
        "details": {
            "endpoint": endpoint,
            "error_text": error_text,
            "request_after_click": hit,
            "requests_before": since,
            "requests_total": len(CTX.requests),
        },
    }
    # Close promptly: react-query keeps retrying the forced-failure endpoint in
    # the background, which would otherwise bleed into later element captures.
    await page.close()
    return result


async def check_sort(page, eid, label, line):
    btn = page.get_by_role("button", name=label, exact=True)
    if await btn.count() == 0:
        return {"verdict": "FAIL", "observed": f"sortable header {label!r} not found"}
    btn = btn.first
    th = btn.locator("xpath=..")
    read_rows = """() => {
        const th = document.querySelector('th[aria-sort]');
        if (!th) return [];
        const table = th.closest('table');
        return [...table.querySelectorAll('tbody tr')].map(
            tr => (tr.querySelector('td')?.textContent || '').trim());
    }"""
    before_sort = await th.get_attribute("aria-sort")
    before_rows = await page.evaluate(read_rows)
    await btn.click()

    async def sort_changed():
        return (await th.get_attribute("aria-sort")) != before_sort

    changed = await poll_until(sort_changed, timeout=8.0)
    after_sort = await th.get_attribute("aria-sort")
    after_rows = await page.evaluate(read_rows)
    ok = bool(changed) and after_sort in ("ascending", "descending")
    return {
        "verdict": "PASS" if ok else "FAIL",
        "observed": (
            f"header '{label}': aria-sort {before_sort!r} -> {after_sort!r}; "
            f"row order changed={before_rows != after_rows} "
            f"({len(before_rows)} rows)"
        ),
        "details": {
            "label": label,
            "aria_sort_before": before_sort,
            "aria_sort_after": after_sort,
            "rows_before": before_rows[:20],
            "rows_after": after_rows[:20],
            "row_order_changed": before_rows != after_rows,
        },
    }


async def check_methodology(context, page):
    anchor = page.locator(f'a[href="{METHODOLOGY_URL}"]')
    if await anchor.count() == 0:
        return {
            "verdict": "FAIL",
            "observed": f"methodology anchor href={METHODOLOGY_URL!r} not found",
        }

    async def stub(route):
        await route.fulfill(
            status=200,
            content_type="text/html",
            body="<html><title>v03-captured</title></html>",
        )

    await context.route(re.compile(r"github\.com"), stub)
    attrs = {
        "href": await anchor.get_attribute("href"),
        "target": await anchor.get_attribute("target"),
        "rel": await anchor.get_attribute("rel"),
        "text": (await anchor.inner_text()).strip(),
    }
    popup_url = await click_external_and_capture(page, anchor, METHODOLOGY_URL)
    ok = (
        attrs["href"] == METHODOLOGY_URL
        and attrs["target"] == "_blank"
        and "noopener" in (attrs["rel"] or "")
        and "noreferrer" in (attrs["rel"] or "")
        and "metodolog" in attrs["text"].lower()
        and bool(popup_url)
        and popup_url.startswith(METHODOLOGY_URL)
    )
    return {
        "verdict": "PASS" if ok else "FAIL",
        "observed": (
            f"href={attrs['href']!r}, target={attrs['target']!r}, rel={attrs['rel']!r}, "
            f"text={attrs['text']!r}, popup={popup_url!r}"
        ),
        "details": {"expected_url": METHODOLOGY_URL, "attributes": attrs, "popup_url": popup_url},
    }


async def check_about(page):
    dialog = page.locator('div[role="dialog"][aria-modal="true"]')
    before = await dialog.count()
    btn = page.get_by_role("button", name=ABOUT_LABEL, exact=True)
    if await btn.count() == 0:
        return {"verdict": "FAIL", "observed": "About button not found"}
    await btn.click()

    async def dialog_open():
        return await dialog.count() > 0 and await dialog.first.is_visible()

    opened = await poll_until(dialog_open, timeout=8.0)
    aria_modal = await dialog.first.get_attribute("aria-modal") if opened else None
    title = await dialog.first.get_by_role("heading", name=ABOUT_TITLE).count() if opened else 0

    async def shot(path):
        await page.screenshot(path=path, full_page=False)

    if opened:
        try:
            await shot(str(OUT / "v03-shot-C02-039-dialog.png"))
        except Exception:  # noqa: BLE001
            pass
    await page.keyboard.press("Escape")

    async def dialog_closed():
        return await dialog.count() == 0

    closed = await poll_until(dialog_closed, timeout=8.0)
    ok = bool(before == 0 and opened and aria_modal == "true" and closed)
    return {
        "verdict": "PASS" if ok else "FAIL",
        "observed": (
            f"dialog before={before}, opened={bool(opened)}, aria-modal={aria_modal!r}, "
            f"about heading count={title}, closed after Escape={bool(closed)}"
        ),
        "details": {
            "dialog_before": before,
            "opened": bool(opened),
            "aria_modal": aria_modal,
            "about_heading": title,
            "closed_after_escape": bool(closed),
            "screenshot": str(OUT / "v03-shot-C02-039-dialog.png"),
        },
    }


# --------------------------------------------------------------------------- #
# orchestration
# --------------------------------------------------------------------------- #


async def run_all() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=CHROMIUM, args=["--no-sandbox"])
        CTX.browser = browser
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        pages: list = []
        try:
            # Resolve runtime data from the live API (no hard-coded IDs).
            meta = api_get("/api/meta")
            overview = api_get("/api/traseism/overview")
            page = await open_page(context)
            pages.append(page)
            legislature = await page.locator("#traseism-legislature").input_value()
            switches = api_get(
                f"/api/traseism/switches?legislature={legislature}"
                f"&chamber=deputies&limit=25&offset=0"
            )
            total = int(switches.get("total", 0))
            runtime = {
                "served_head": subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd="/home/nedaktov/parlament-deschis",
                ).stdout.strip(),
                "api_legislatures": sorted(meta.get("legislatures", {}).keys()),
                "runtime_legislature": legislature,
                "overview_rows": len(overview),
                "ledger_total": total,
                "source_url_sample": (
                    switches["rows"][0].get("source_url") if switches.get("rows") else None
                ),
            }
            (OUT / "v03-runtime.json").write_text(
                json.dumps(runtime, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            # C02-021 — summary retry (summary.asyncState onRetry)
            await guard(
                "C02-021",
                "Traseism.tsx:839",
                "force 500 on /api/traseism/summary, click error Retry",
                "Retry refetches /api/traseism/summary (new request observed)",
                lambda: check_retry(
                    context, "C02-021", r"/api/traseism/summary", "/api/traseism/summary"
                ),
            )

            # C02-022 / C02-023 — chamber buttons (orange deputies / senate)
            await guard(
                "C02-022",
                "Traseism.tsx:789-803",
                "click 'Camera Deputaților' chamber toggle",
                "URL chamber=deputies, aria-pressed=true, stays on /traseism",
                lambda: check_chamber(page, 0, "deputies"),
            )
            await guard(
                "C02-023",
                "Traseism.tsx:789-803",
                "click 'Senat' chamber toggle",
                "URL chamber=senate, aria-pressed flips, stays on /traseism",
                lambda: check_chamber(page, 1, "senate"),
            )

            # C02-024 — legislature select
            await guard(
                "C02-024",
                "Traseism.tsx:813-824",
                "change #traseism-legislature to another live year",
                "URL legislature=<selected year>, select value follows, refetch fires",
                lambda: check_legislature(page),
            )

            # C02-025 — per-row external source URL (data-driven).
            # Use a FRESH page: C02-022/023/024 intentionally mutated the scope
            # of `page`, so its ledger no longer matches the default-scope API.
            src_page = await open_page(context)
            pages.append(src_page)
            src_legislature = await src_page.locator("#traseism-legislature").input_value()
            await guard(
                "C02-025",
                "Traseism.tsx:391-398",
                "click ledger row 'sursa oficială' anchor (URL from live API)",
                "href equals API source_url, target=_blank/rel noopener noreferrer, popup navigates to it",
                lambda: check_source_anchor(context, src_page, src_legislature),
            )

            # C02-026 / C02-027 — pagination on the SAME clean page (fresh state)
            page2 = await open_page(context)
            pages.append(page2)
            legislature2 = await page2.locator("#traseism-legislature").input_value()
            total2 = int(
                api_get(
                    f"/api/traseism/switches?legislature={legislature2}"
                    f"&chamber=deputies&limit=25&offset=0"
                ).get("total", 0)
            )
            await guard(
                "C02-027",
                "Traseism.tsx:421-426",
                "click Next page on the switch ledger",
                "request offset=25, 'Pagina 2 din N' visible, Previous enabled, first row changes",
                lambda: check_pagination_next(page2, total2),
            )
            await guard(
                "C02-026",
                "Traseism.tsx:414-419",
                "click Previous page on the switch ledger",
                "'Pagina 1 din N' visible, Next enabled, first row restored to original page-1 rows",
                lambda: check_pagination_prev(page2),
            )
            # L-25 regression row (not a new inventory element): two Next clicks
            # on a runtime-discovered >2-page scope must advance 1 -> 2 -> 3.
            await guard(
                "C02-027/second-next",
                "Traseism.tsx:312-314 (L-25 clamp guard)",
                "click Next twice on a runtime-discovered >2-page ledger scope",
                "offset=25 then offset=50, counters 'Pagina 2 din N' and "
                "'Pagina 3 din N', three distinct first rows, Previous enabled",
                lambda: check_second_next(context, pages),
            )

            # C02-028 — ledger retry
            await guard(
                "C02-028",
                "Traseism.tsx:331",
                "force 500 on /api/traseism/switches, click ledger Retry",
                "Retry refetches /api/traseism/switches (new request observed)",
                lambda: check_retry(
                    context,
                    "C02-028",
                    r"/api/traseism/switches",
                    "/api/traseism/switches",
                    scope_selector='section:has(h2:text-is("Registrul schimbărilor"))',
                ),
            )

            # C02-029 ... C02-035 — seven sortable headers (sequential state)
            for eid, label, line in SORT_HEADERS:
                await guard(
                    eid,
                    line,
                    f"click sortable header '{label}'",
                    "th aria-sort changes to ascending/descending and row order updates",
                    lambda lbl=label, e=eid, line=line: check_sort(page, e, lbl, line),
                    screenshot=None,
                )

            # C02-036 — switch waves retry
            await guard(
                "C02-036",
                "Traseism.tsx:617",
                "force 500 on /api/analytics/switch-waves, click Retry",
                "Retry refetches /api/analytics/switch-waves (new request observed)",
                lambda: check_retry(
                    context,
                    "C02-036",
                    r"/api/analytics/switch-waves",
                    "/api/analytics/switch-waves",
                ),
            )

            # C02-037 — scopes overview retry
            await guard(
                "C02-037",
                "Traseism.tsx:928",
                "force 500 on /api/traseism/overview, click Retry",
                "Retry refetches /api/traseism/overview (new request observed)",
                lambda: check_retry(
                    context, "C02-037", r"/api/traseism/overview", "/api/traseism/overview"
                ),
            )

            # C02-038 — methodology external anchor
            await guard(
                "C02-038",
                "Traseism.tsx:942-949",
                "click 'Citește metodologia completă' external anchor",
                "href=docs/METHODOLOGY.md GitHub URL, target=_blank, popup navigates to it",
                lambda: check_methodology(context, page),
            )

            # C02-039 — About button / modal open + Escape close
            await guard(
                "C02-039",
                "Traseism.tsx:950-956",
                "click About button, press Escape",
                "role=dialog aria-modal=true appears, then unmounts on Escape",
                lambda: check_about(page),
            )

        finally:
            for p in pages:
                try:
                    await p.close()
                except Exception:  # noqa: BLE001
                    pass
            try:
                await context.close()
            except Exception:  # noqa: BLE001
                pass
            await browser.close()


def test_v03_traseism_clickables():
    """Execute the fleet slice and persist artifacts; findings are rows, not raises."""
    _run_summary = asyncio.run(run_all())

    OUT.mkdir(parents=True, exist_ok=True)
    # Deterministic inventory order: exactly one row per assigned ID, plus the
    # single L-25 regression row (a check, not a new inventory element).
    by_id = {r["element_id"]: r for r in CTX.rows}
    assert len(by_id) == len(CTX.rows), "duplicate element_id in results"
    missing = sorted(set(ALL_IDS) - set(by_id))
    assert not missing, f"element reconciliation failed: missing={missing}"
    extras = sorted(set(by_id) - set(ALL_IDS))
    assert set(extras) <= {"C02-027/second-next"}, (
        f"element reconciliation failed: unexpected extra rows={extras}"
    )
    rows = [by_id[eid] for eid in ALL_IDS]
    rows += [by_id[eid] for eid in extras]
    RESULTS.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    induced = sum(1 for c in CTX.console if c.get("induced"))
    console_doc = {
        "captured_at": now_iso(),
        "base": BASE,
        "route": ROUTE,
        "element_count": len(rows),
        "console_error_count": len(CTX.console),
        "induced_error_count": induced,
        "non_induced_error_count": len(CTX.console) - induced,
        "note": (
            "events flagged induced=true were caused by the harness forcing HTTP 500 "
            "to exercise retry handlers; they are recorded, not suppressed"
        ),
        "events": CTX.console,
    }
    CONSOLE.write_text(json.dumps(console_doc, indent=2, ensure_ascii=False), encoding="utf-8")

    for p in [Path(r["evidence_path"]) for r in rows]:
        assert p.exists(), f"missing evidence artifact: {p}"

    counts = {s: sum(1 for r in rows if r["status"] == s) for s in ("PASS", "FAIL", "SKIP")}
    print("\n" + "=" * 78)
    print(
        f"V-03: {len(rows)} elements | PASS={counts['PASS']} "
        f"FAIL={counts['FAIL']} SKIP={counts['SKIP']} | "
        f"console errors={len(CTX.console)} (induced={induced}, "
        f"non-induced={len(CTX.console) - induced})"
    )
    print(f"results: {RESULTS}")
    print(f"console: {CONSOLE}")
    print("=" * 78)
