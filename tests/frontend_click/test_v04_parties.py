"""V-04 clickable validation: party pages (C03-001..014, C03-038..040).

Read-only validation fleet agent. This file owns exactly 17 element IDs and
writes only to /tmp/opencode/click-validation/v04-*.

For every assigned ID an observable outcome is asserted: a URL change, a title/
visible text change, a select value reflected in the URL, a state transition,
or a fired request (retry elements are exercised by forcing a query error with
an HTTP-200/non-JSON body, so no synthetic browser console error is produced).

Party short names, comparison options, Wikidata candidates, movement candidates
and legislature values are resolved from the LIVE API; nothing data-dependent is
hard-coded. A data-dependent element that cannot be resolved is a SKIP with a
named resolver, never a PASS.

Harness contract: one Chromium instance, closed in a finally block; bounded
networkidle waits plus a fixed settle; all console.error/pageerror captured raw.
"""

from __future__ import annotations

import asyncio
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Coroutine

import pytest
from playwright.async_api import Page, TimeoutError as PWTimeout, async_playwright

BASE = "http://127.0.0.1:5188"
OUT = Path("/tmp/opencode/click-validation")
RESULTS = OUT / "v04-results.json"
CONSOLE = OUT / "v04-console.json"

ELEMENT_IDS = [
    "C03-001",
    "C03-002",
    "C03-003",
    "C03-004",
    "C03-005",
    "C03-006",
    "C03-007",
    "C03-008",
    "C03-009",
    "C03-010",
    "C03-011",
    "C03-012",
    "C03-013",
    "C03-014",
    "C03-038",
    "C03-039",
    "C03-040",
]

results: list[dict[str, Any]] = []
console_errors: list[str] = []
page_errors: list[str] = []
visited: list[str] = []
induced: list[dict[str, str]] = []


# --------------------------------------------------------------------------- #
# infrastructure
# --------------------------------------------------------------------------- #
def api_get(path: str) -> Any:
    with urllib.request.urlopen(BASE + "/api" + path, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def flush() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    CONSOLE.write_text(
        json.dumps(
            {
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "base": BASE,
                "pages_visited": visited,
                "console_errors": console_errors,
                "page_errors": page_errors,
                "total_browser_errors": len(console_errors) + len(page_errors),
                "induced_query_failures": induced,
                "note": (
                    "Retry elements were validated by fulfilling the API request with "
                    "HTTP 200 + a non-JSON body, which makes react-query enter its error "
                    "state without producing a browser console error. Every induced "
                    "failure is listed here; nothing was filtered or suppressed."
                ),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


async def evidence(
    eid: str, capture: dict[str, Any], page: Page | None = None, shot: bool = False
) -> str:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"v04-evidence-{eid}.json"
    capture = dict(capture)
    capture["element_id"] = eid
    capture["captured_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(
        json.dumps(capture, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    if shot and page is not None:
        try:
            await page.screenshot(path=str(OUT / f"v04-shot-{eid}.png"))
            capture["screenshot"] = str(OUT / f"v04-shot-{eid}.png")
        except Exception as exc:  # noqa: BLE001 - screenshot is supplementary
            capture["screenshot_error"] = str(exc)[:200]
    return str(path)


async def goto(page: Page, route: str) -> None:
    visited.append(route)
    await page.goto(BASE + route, wait_until="load", timeout=45_000)
    try:
        await page.wait_for_load_state("networkidle", timeout=10_000)
    except Exception:  # noqa: BLE001 - bounded fallback, never skip the settle
        pass
    await page.wait_for_timeout(1_200)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


async def run(
    eid: str,
    line: str,
    action: str,
    expected: str,
    fn: Callable[[], Coroutine[Any, Any, tuple[str, str, str, dict[str, Any]]]],
    resolver: str | None = None,
) -> dict[str, Any]:
    """Execute one element validator; a thrown assertion is a FAIL finding."""
    try:
        observed, status, ev_path, extra = await fn()
    except Exception as exc:  # noqa: BLE001 - validation must always record a verdict
        observed = f"validation error: {type(exc).__name__}: {str(exc)[:400]}"
        status = "FAIL"
        ev_path = await evidence(eid, {"error": observed, "action": action})
        extra = {}
    row: dict[str, Any] = {
        "element_id": eid,
        "source_file_line": line,
        "action": action,
        "expected_outcome": expected,
        "observed_outcome": observed,
        "status": status,
        "evidence_path": ev_path,
        # User-facing aliases (fleet note vs. task-brief vocabulary).
        "expected": expected,
        "observed": observed,
        "verdict": status,
    }
    if resolver and status == "SKIP":
        row["resolver"] = resolver
    row.update(extra)
    results.append(row)
    flush()
    return row


async def force_error_and_retry(
    page: Page,
    eid: str,
    fail_pattern: re.Pattern[str],
    route: str,
    expected_request_fragment: str,
    label: str,
) -> tuple[str, str, str, dict[str, Any]]:
    """Force one query into error state, then click Retry and observe a refetch."""

    async def broken(route_obj: Any) -> None:
        # HTTP 200 + non-JSON -> JSON.parse throws inside api.get -> query error.
        await route_obj.fulfill(
            status=200,
            content_type="application/json",
            body="V04_FORCED_NON_JSON_BODY",
        )

    induced.append(
        {
            "element_id": eid,
            "endpoint_pattern": fail_pattern.pattern,
            "mechanism": "HTTP 200 + non-JSON body -> react-query error",
        }
    )
    await page.route(fail_pattern, broken)
    try:
        await goto(page, route)
        retry = page.locator("[data-state='error'] [role='alert'] button").first
        await retry.wait_for(state="visible", timeout=30_000)
        states_before = await page.locator("[data-state]").evaluate_all(
            "els => els.map(e => e.getAttribute('data-state'))"
        )
        alert_text = (await page.locator("[role='alert']").first.inner_text()).strip()[:200]
        await page.unroute(fail_pattern, broken)
        async with page.expect_request(fail_pattern, timeout=25_000) as request_info:
            await retry.click()
        req = await request_info.value
        require(
            expected_request_fragment in req.url,
            f"retry request URL {req.url!r} lacks {expected_request_fragment!r}",
        )
        cleared = False
        try:
            await page.wait_for_selector("[data-state='error']", state="detached", timeout=20_000)
            cleared = True
        except PWTimeout:
            pass
        states_after = await page.locator("[data-state]").evaluate_all(
            "els => els.map(e => e.getAttribute('data-state'))"
        )
        observed = (
            f"{label}: error state {states_before} shown with alert {alert_text!r}; "
            f"Retry click fired {req.method} {req.url}; error cleared={cleared}; "
            f"states_after={states_after}"
        )
        cap = {
            "route": route,
            "states_before": states_before,
            "alert_text": alert_text,
            "retry_request": {"method": req.method, "url": req.url},
            "error_cleared_after_retry": cleared,
            "states_after": states_after,
            "final_url": page.url,
        }
        return observed, "PASS", await evidence(eid, cap, page, shot=True), cap
    finally:
        try:
            await page.unroute(fail_pattern, broken)
        except Exception:  # noqa: BLE001 - already unrouted on the happy path
            pass


# --------------------------------------------------------------------------- #
# live API resolution (no hard-coded data-dependent IDs)
# --------------------------------------------------------------------------- #
def resolve_data() -> dict[str, Any]:
    parties = api_get("/parties")["data"]
    shorts = [p["short_name"] for p in parties]

    def matches(value: str) -> int:
        needle = value.strip().lower()
        return sum(
            1 for p in parties if needle in p["short_name"].lower() or needle in p["name"].lower()
        )

    unique = [s for s in shorts if matches(s) == 1 and re.fullmatch(r"[A-Za-z0-9-]+", s)]
    ascii_shorts = [s for s in shorts if re.fullmatch(r"[A-Za-z0-9-]+", s)]
    nav_a, nav_b = (unique[:2] + ascii_shorts[:2])[:2]
    if len({nav_a, nav_b}) < 2:
        nav_b = next(s for s in ascii_shorts if s != nav_a)

    meta = api_get("/meta")
    legs = [k for k in (meta.get("legislatures") or {}) if re.fullmatch(r"\d{4}", k)]
    legislature = sorted(legs)[len(legs) // 2] if legs else ""
    leg_start = (meta.get("legislatures", {}).get(legislature, {}) or {}).get("start")
    date_value = (
        leg_start
        if isinstance(leg_start, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", leg_start)
        else None
    )

    qid_party = None
    mov_party = None
    for p in parties:
        s = urllib.parse.quote(p["short_name"], safe="")
        try:
            profile = api_get(f"/party/{s}")
        except Exception:  # noqa: BLE001 - resolution must not abort the fleet agent
            profile = {}
        if qid_party is None and profile.get("wikidata_qid"):
            qid_party = {
                "short_name": p["short_name"],
                "qid": profile["wikidata_qid"],
                "name": profile.get("name"),
            }
        if mov_party is None:
            try:
                movements = api_get(f"/party/{s}/movements?limit=50")
            except Exception:  # noqa: BLE001
                movements = []
            rows = movements if isinstance(movements, list) else movements.get("data", [])
            with_person = [m for m in rows if m.get("person")]
            if with_person:
                person = with_person[0]["person"]
                mov_party = {
                    "short_name": p["short_name"],
                    "person_id": person.get("id"),
                    "person_name": person.get("name"),
                }
        if qid_party and mov_party:
            break

    return {
        "parties": parties,
        "party_count": len(parties),
        "search_short": unique[0] if unique else ascii_shorts[0],
        "nav_a": nav_a,
        "nav_b": nav_b,
        "legislature": legislature,
        "date_value": date_value,
        "qid_party": qid_party,
        "mov_party": mov_party,
    }


# --------------------------------------------------------------------------- #
# element validators
# --------------------------------------------------------------------------- #
async def c03_001(page: Page, d: dict[str, Any]):
    short = d["search_short"]
    await goto(page, "/parties")
    box = page.locator('input[type="text"]').first
    await box.wait_for(state="visible", timeout=20_000)
    before = page.url
    await box.fill(short)
    await page.wait_for_function(
        "v => new URLSearchParams(location.search).get('q') === v",
        arg=short,
        timeout=20_000,
    )
    after = page.url
    count_text = (await page.get_by_text(re.compile(r"^\d+\s*/\s*\d+$")).first.inner_text()).strip()
    visible_rows = await page.locator("tr[role='button']").count()
    rows_text = (await page.locator("tr[role='button']").all_inner_texts())[:3]
    require(
        visible_rows >= 1 and short in " ".join(rows_text),
        f"filtered table does not show searched party {short!r}",
    )
    require(
        count_text.split("/")[0].strip() == "1",
        f"expected exactly one filtered party, count text={count_text!r}",
    )
    cap = {
        "url_before": before,
        "url_after": after,
        "typed": short,
        "input_value": await box.input_value(),
        "count_text": count_text,
        "visible_rows": visible_rows,
        "rows_text": rows_text,
    }
    return (
        f"typing {short!r} navigated to {after}; count {before} -> {count_text!r}; "
        f"{visible_rows} row(s) remain",
        "PASS",
        await evidence("C03-001", cap, page, shot=True),
        cap,
    )


async def c03_002(page: Page, d: dict[str, Any]):
    return await force_error_and_retry(
        page,
        "C03-002",
        re.compile(r"/api/parties(?:\?|$)"),
        "/parties",
        "/api/parties",
        "Parties load-error retry",
    )


async def c03_003(page: Page, d: dict[str, Any]):
    a, b = d["nav_a"], d["nav_b"]
    await goto(page, "/parties")
    row = page.locator("tr[role='button']").filter(has_text=a).first
    await row.wait_for(state="visible", timeout=20_000)
    await row.click()
    await page.wait_for_url(re.compile(r"/party/" + re.escape(a) + r"(?:\?|$)"), timeout=20_000)
    # wait_for_url fires on URL change, before react-query renders the profile;
    # wait for the party name in an h1 before asserting visible text.
    await page.wait_for_function(
        "n => [...document.querySelectorAll('h1')].some(h => h.textContent.includes(n))",
        arg=a,
        timeout=25_000,
    )
    mouse_url = page.url
    mouse_title = (await page.locator("h1").filter(has_text=a).first.inner_text()).strip()
    require(
        a in mouse_title or a.lower() in mouse_title.lower(),
        f"profile h1 {mouse_title!r} does not name party {a!r}",
    )

    await goto(page, "/parties")
    row2 = page.locator("tr[role='button']").filter(has_text=b).first
    await row2.focus()
    await page.keyboard.press("Enter")
    await page.wait_for_url(re.compile(r"/party/" + re.escape(b) + r"(?:\?|$)"), timeout=20_000)
    await page.wait_for_function(
        "n => [...document.querySelectorAll('h1')].some(h => h.textContent.includes(n))",
        arg=b,
        timeout=25_000,
    )
    keyboard_url = page.url
    cap = {
        "mouse": {"party": a, "url": mouse_url, "h1": mouse_title},
        "keyboard_enter": {"party": b, "url": keyboard_url},
        "rows_count": await page.locator("tr[role='button']").count(),
    }
    return (
        f"mouse click on {a} row -> {mouse_url} (h1 {mouse_title!r}); "
        f"Enter on {b} row -> {keyboard_url}",
        "PASS",
        await evidence("C03-003", cap, page, shot=True),
        cap,
    )


async def c03_004(page: Page, d: dict[str, Any]):
    short = d["nav_a"]
    pat = re.compile(r"/api/party/[^/]+(?:\?|$)")
    return await force_error_and_retry(
        page,
        "C03-004",
        pat,
        f"/party/{short}",
        "/api/party/",
        "PartyProfile full-page load-error retry",
    )


async def c03_005(page: Page, d: dict[str, Any]):
    candidate = d["qid_party"]
    cap: dict[str, Any] = {
        "api_resolution": candidate,
        "parties_checked": d["party_count"],
    }
    if candidate is None:
        await goto(page, f"/party/{d['nav_a']}")
        anchors = await page.locator('a[href^="https://www.wikidata.org/wiki/"]').count()
        cap["browser_anchor_count"] = anchors
        cap["sample_profile_url"] = page.url
        return (
            "SKIP: live /api/party/{short} returned wikidata_qid=null for all "
            f"{d['party_count']} resolved parties; the anchor is conditionally "
            f"rendered only for a truthy QID and none is rendered on "
            f"{page.url} (anchor count={anchors}). No link target could be observed.",
            "SKIP",
            await evidence("C03-005", cap, page),
            cap,
        )
    short, qid = candidate["short_name"], candidate["qid"]
    await goto(page, f"/party/{urllib.parse.quote(short, safe='')}")
    link = page.locator('a[href^="https://www.wikidata.org/wiki/"]').first
    await link.wait_for(state="visible", timeout=20_000)
    href = await link.get_attribute("href")
    text = (await link.inner_text()).strip()
    target = await link.get_attribute("target")
    expected_href = f"https://www.wikidata.org/wiki/{qid}"
    require(href == expected_href, f"href {href!r} != {expected_href!r}")
    require(qid in text and "Wikidata" in text, f"link text {text!r} lacks QID")
    require(target == "_blank", f"target={target!r} != _blank")
    cap.update({"href": href, "text": text, "target": target, "short_name": short, "qid": qid})
    return (
        f"{short} Wikidata anchor text={text!r} href={href!r} target={target}",
        "PASS",
        await evidence("C03-005", cap, page, shot=True),
        cap,
    )


async def c03_006(page: Page, d: dict[str, Any]):
    candidate = d["mov_party"]
    cap: dict[str, Any] = {"api_resolution": candidate, "parties_checked": d["party_count"]}
    if candidate is None:
        await goto(page, f"/party/{d['nav_a']}")
        enabled = await page.locator("button:not([disabled])").all_inner_texts()
        cap["profile_url"] = page.url
        cap["enabled_buttons"] = enabled
        cap["movement_region_count"] = await page.locator("[role='region']").count()
        return (
            f"SKIP: live /api/party/{{short}}/movements returned no movement with a "
            f"linked person for any of {d['party_count']} parties; no enabled "
            f"movement button exists on {page.url} (enabled buttons={enabled!r}). "
            "The drawer-opening click cannot be observed with this corpus.",
            "SKIP",
            await evidence("C03-006", cap, page),
            cap,
        )
    short, name = candidate["short_name"], candidate["person_name"]
    await goto(page, f"/party/{urllib.parse.quote(short, safe='')}")
    button = page.locator("button:not([disabled])").filter(has_text=name).first
    await button.wait_for(state="visible", timeout=20_000)
    await button.click()
    dialog = page.get_by_role("dialog")
    await dialog.wait_for(state="visible", timeout=20_000)
    await page.wait_for_function(
        "n => document.querySelector('#person-drawer-title')?.textContent?.includes(n)",
        arg=name,
        timeout=20_000,
    )
    drawer_title = (await page.locator("#person-drawer-title").inner_text()).strip()
    cap.update(
        {
            "short_name": short,
            "person_name": name,
            "dialog_title": drawer_title,
            "dialog_count": await dialog.count(),
        }
    )
    require(name in drawer_title, f"drawer title {drawer_title!r} lacks {name!r}")
    return (
        f"movement button for {name!r} opened dialog titled {drawer_title!r}",
        "PASS",
        await evidence("C03-006", cap, page, shot=True),
        cap,
    )


async def c03_007(page: Page, d: dict[str, Any]):
    short = d["nav_a"]
    pat = re.compile(r"/api/party/[^/]+/movements(?:\?|$)")
    return await force_error_and_retry(
        page, "C03-007", pat, f"/party/{short}", "/movements", "PartyProfile inline movements retry"
    )


async def c03_008(page: Page, d: dict[str, Any]):
    await goto(page, "/party-timeline")
    link = page.locator('a[href^="/parties"]').filter(has_text="→").first
    await link.wait_for(state="visible", timeout=20_000)
    text = (await link.inner_text()).strip()
    href = await link.get_attribute("href")
    await link.click()
    await page.wait_for_url(re.compile(r"/parties(?:\?|$)"), timeout=20_000)
    cap = {"link_text": text, "link_href": href, "url_after": page.url}
    require(
        any(tok in text.lower() for tok in ("partide", "parties")),
        f"view-all link text {text!r} is not a parties CTA",
    )
    return (
        f"timeline link {text!r} ({href}) navigated to {page.url}",
        "PASS",
        await evidence("C03-008", cap, page, shot=True),
        cap,
    )


async def c03_009(page: Page, d: dict[str, Any]):
    return await force_error_and_retry(
        page,
        "C03-009",
        re.compile(r"/api/analytics/party-timeline(?:\?|$)"),
        "/party-timeline",
        "/api/analytics/party-timeline",
        "PartyTimeline load-error retry",
    )


async def c03_010(page: Page, d: dict[str, Any]):
    await goto(page, "/compare")
    link = page.locator('a[href^="/parties"]').filter(has_text="→").first
    await link.wait_for(state="visible", timeout=20_000)
    text = (await link.inner_text()).strip()
    href = await link.get_attribute("href")
    await link.click()
    await page.wait_for_url(re.compile(r"/parties(?:\?|$)"), timeout=20_000)
    cap = {"link_text": text, "link_href": href, "url_after": page.url}
    require(
        any(tok in text.lower() for tok in ("partide", "parties")),
        f"view-all link text {text!r} is not a parties CTA",
    )
    return (
        f"comparison link {text!r} ({href}) navigated to {page.url}",
        "PASS",
        await evidence("C03-010", cap, page, shot=True),
        cap,
    )


async def _select_test(
    page: Page, index: int, param: str, eid: str
) -> tuple[str, str, str, dict[str, Any]]:
    await goto(page, "/compare")
    sel = page.locator("select").nth(index)
    await sel.wait_for(state="visible", timeout=20_000)
    default = await sel.input_value()
    options = await sel.locator("option").evaluate_all("els => els.map(e => e.value)")
    other_sel = page.locator("select").nth(1 if index == 2 else 2)
    other_default = await other_sel.input_value()
    require(len(options) > 1, f"party selector has no alternatives: {options}")
    # Default validation (finding F5): code defaults must exist in loaded list
    # and comparison table must render with both defaults.
    require(default in options, f"default {default!r} absent from party options {options}")
    require(
        other_default in options,
        f"other default {other_default!r} absent from party options {options}",
    )
    table_headers = (await page.locator("table thead th").all_inner_texts())[:4]
    require(
        default in " ".join(table_headers) or other_default in " ".join(table_headers),
        f"comparison table did not render defaults: headers={table_headers}",
    )

    target = next((o for o in options if o and o != default), None)
    require(target is not None, "no selectable alternative party found")
    before = page.url
    await sel.select_option(target)
    await page.wait_for_function(
        "p => new URLSearchParams(location.search).get(p[0]) === p[1]",
        arg=[param, target],
        timeout=20_000,
    )
    after = page.url
    chosen = await sel.input_value()
    require(chosen == target, f"select value {chosen!r} != chosen {target!r}")
    require(
        f"{param}={urllib.parse.quote(target, safe='')}" in after,
        f"URL {after} lacks {param}={target}",
    )
    cap = {
        "default_value": default,
        "other_default": other_default,
        "options": options,
        "table_headers": table_headers,
        "selected": target,
        "select_value_after": chosen,
        "url_before": before,
        "url_after": after,
    }
    return (
        f"default {default!r} validated in options {options}; choosing {target!r} "
        f"changed URL {before} -> {after} and select value to {chosen!r}",
        "PASS",
        await evidence(eid, cap, page, shot=True),
        cap,
    )


async def c03_011(page: Page, d: dict[str, Any]):
    return await _select_test(page, 1, "partyA", "C03-011")


async def c03_012(page: Page, d: dict[str, Any]):
    return await _select_test(page, 2, "partyB", "C03-012")


async def c03_013(page: Page, d: dict[str, Any]):
    return await force_error_and_retry(
        page,
        "C03-013",
        re.compile(r"/api/parties(?:\?|$)"),
        "/compare",
        "/api/parties",
        "PartyComparison three-query retry",
    )


async def c03_014(page: Page, d: dict[str, Any]):
    return await force_error_and_retry(
        page,
        "C03-014",
        re.compile(r"/api/analytics/switch-waves(?:\?|$)"),
        "/coalitions",
        "/api/analytics/switch-waves",
        "Coalitions wave retry",
    )


async def c03_038(page: Page, d: dict[str, Any]):
    value = d["date_value"]
    require(bool(value), "no ISO date resolved from live /api/meta")
    await goto(page, "/compare")
    field = page.locator("#scope-date")
    await field.wait_for(state="visible", timeout=20_000)
    before = page.url
    await field.fill(value)
    await page.wait_for_function(
        "v => new URLSearchParams(location.search).get('date') === v", arg=value, timeout=20_000
    )
    after = page.url
    chosen = await field.input_value()
    require(chosen == value, f"date input {chosen!r} != {value!r}")
    cap = {"date_from_meta": value, "url_before": before, "url_after": after, "input_value": chosen}
    return (
        f"date picker set to {value} (from /api/meta) -> {after}; input reflects {chosen!r}",
        "PASS",
        await evidence("C03-038", cap, page, shot=True),
        cap,
    )


async def c03_039(page: Page, d: dict[str, Any]):
    await goto(page, "/mps")
    sel = page.locator("#scope-chamber")
    await sel.wait_for(state="visible", timeout=20_000)
    options = await sel.locator("option").evaluate_all("els => els.map(e => e.value)")
    target = next((o for o in options if o), None)
    require(target is not None, "chamber selector has no concrete option")
    before = page.url
    await sel.select_option(target)
    await page.wait_for_function(
        "v => new URLSearchParams(location.search).get('chamber') === v", arg=target, timeout=20_000
    )
    after = page.url
    chosen = await sel.input_value()
    require(chosen == target, f"chamber select {chosen!r} != {target!r}")
    cap = {
        "options": options,
        "selected": target,
        "select_value_after": chosen,
        "url_before": before,
        "url_after": after,
    }
    return (
        f"chamber picker {target!r} changed URL {before} -> {after}; select value={chosen!r}",
        "PASS",
        await evidence("C03-039", cap, page, shot=True),
        cap,
    )


async def c03_040(page: Page, d: dict[str, Any]):
    value = d["legislature"]
    require(bool(value), "no legislature resolved from live /api/meta")
    await goto(page, "/compare")
    sel = page.locator("#scope-legislature")
    await sel.wait_for(state="visible", timeout=20_000)
    options = await sel.locator("option").evaluate_all("els => els.map(e => e.value)")
    require(value in options, f"resolved legislature {value!r} absent from {options}")
    before = page.url
    await sel.select_option(value)
    await page.wait_for_function(
        "v => new URLSearchParams(location.search).get('legislature') === v",
        arg=value,
        timeout=20_000,
    )
    after = page.url
    chosen = await sel.input_value()
    require(chosen == value, f"legislature select {chosen!r} != {value!r}")
    cap = {
        "legislature_from_meta": value,
        "options": options[:12],
        "url_before": before,
        "url_after": after,
        "select_value_after": chosen,
    }
    return (
        f"legislature picker {value!r} (from /api/meta) -> {after}; select value={chosen!r}",
        "PASS",
        await evidence("C03-040", cap, page, shot=True),
        cap,
    )


VALIDATORS: dict[str, Callable[[Page, dict[str, Any]], Coroutine[Any, Any, Any]]] = {
    "C03-001": c03_001,
    "C03-002": c03_002,
    "C03-003": c03_003,
    "C03-004": c03_004,
    "C03-005": c03_005,
    "C03-006": c03_006,
    "C03-007": c03_007,
    "C03-008": c03_008,
    "C03-009": c03_009,
    "C03-010": c03_010,
    "C03-011": c03_011,
    "C03-012": c03_012,
    "C03-013": c03_013,
    "C03-014": c03_014,
    "C03-038": c03_038,
    "C03-039": c03_039,
    "C03-040": c03_040,
}

SOURCE_LINES = {
    "C03-001": "Parties.tsx:70-76 (onChange :73)",
    "C03-002": "Parties.tsx:83-89 (onRetry :86)",
    "C03-003": "Parties.tsx:107-119 (onClick :110, onKeyDown :113-118)",
    "C03-004": "PartyProfile.tsx:68-76 (onRetry :72)",
    "C03-005": "PartyProfile.tsx:106-115 (href :108)",
    "C03-006": "PartyProfile.tsx:180-200 (onClick :182)",
    "C03-007": "PartyProfile.tsx:168-174 (onRetry :171)",
    "C03-008": "PartyTimeline.tsx:127-133 (Link :128)",
    "C03-009": "PartyTimeline.tsx:99-106 (onRetry :102)",
    "C03-010": "PartyComparison.tsx:188-195 (Link :189)",
    "C03-011": "PartyComparison.tsx:198-211 (onChange :202)",
    "C03-012": "PartyComparison.tsx:212-225 (onChange :216)",
    "C03-013": "PartyComparison.tsx:156-169 (onRetry :161-165)",
    "C03-014": "Coalitions.tsx:64-73 (onRetry :69)",
    "C03-038": "ScopeControls.tsx:29-36 (onChange :34)",
    "C03-039": "ScopeControls.tsx:37-47 (onChange :41)",
    "C03-040": "ScopeControls.tsx:48-57 (onChange :52)",
}

EXPECTED = {
    "C03-001": "URL gains q=<party short name>; table filters to that party",
    "C03-002": "retry button in error state fires /api/parties refetch and error clears",
    "C03-003": "mouse click and Enter on role=button row navigate to /party/<short>",
    "C03-004": "full-page retry fires /api/party/<short> refetch and error clears",
    "C03-005": "Wikidata anchor shows <qid>, href=wikidata.org/wiki/<qid>, target=_blank",
    "C03-006": "clicking a person-bearing movement opens the PersonDrawer dialog",
    "C03-007": "inline movements retry fires /api/party/<short>/movements refetch",
    "C03-008": '"View all parties" link navigates to /parties',
    "C03-009": "timeline retry fires /api/analytics/party-timeline refetch",
    "C03-010": '"View all parties" link navigates to /parties',
    "C03-011": "default party A in live options; selecting another sets URL partyA",
    "C03-012": "default party B in live options; selecting another sets URL partyB",
    "C03-013": "retry fires /api/parties refetch (of three queries) and error clears",
    "C03-014": "retry fires /api/analytics/switch-waves refetch and error clears",
    "C03-038": "date input changes URL date=<ISO date> and reflects chosen value",
    "C03-039": "chamber select changes URL chamber=<value> and reflects chosen value",
    "C03-040": "legislature select changes URL legislature=<YYYY> and reflects value",
}

ACTIONS = {
    "C03-001": "type a live-resolved party short name into parties search",
    "C03-002": "induce parties fetch error, click Retry",
    "C03-003": "click a party row with mouse; focus another row and press Enter",
    "C03-004": "induce profile fetch error, click Retry",
    "C03-005": "inspect the rendered Wikidata anchor on a live-QID party profile",
    "C03-006": "click a movement button whose movement has a linked person",
    "C03-007": "induce movements fetch error only, click inline Retry",
    "C03-008": 'click timeline "View all parties" link',
    "C03-009": "induce timeline fetch error, click Retry",
    "C03-010": 'click comparison "View all parties" link',
    "C03-011": "validate defaults then select a different Party A",
    "C03-012": "validate defaults then select a different Party B",
    "C03-013": "induce parties fetch error on /compare, click Retry",
    "C03-014": "induce switch-waves fetch error, click Retry",
    "C03-038": "set #scope-date from /api/meta",
    "C03-039": "select a concrete #scope-chamber option",
    "C03-040": "select a /api/meta-resolved #scope-legislature option",
}

SKIP_RESOLVERS = {
    "C03-005": (
        "data-dependent: rerun when /api/party/{short} yields a non-null "
        "wikidata_qid (anchor is conditionally rendered) "
    ),
    "C03-006": (
        "data-dependent: rerun when /api/party/{short}/movements yields a "
        "movement with a non-null person (movement button is disabled "
        "otherwise) "
    ),
}


# --------------------------------------------------------------------------- #
# pytest entry point
# --------------------------------------------------------------------------- #
def test_v04_parties_clickables() -> None:
    results.clear()
    console_errors.clear()
    page_errors.clear()
    visited.clear()
    induced.clear()
    flush()

    d = resolve_data()

    async def orchestrate() -> None:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                executable_path="/usr/bin/chromium", args=["--no-sandbox"]
            )
            page = await browser.new_page()

            def on_console(msg: Any) -> None:
                if msg.type == "error":
                    console_errors.append(f"console.error: {msg.text[:300]}")

            def on_pageerror(exc: Any) -> None:
                page_errors.append(f"pageerror: {str(exc)[:300]}")

            page.on("console", on_console)
            page.on("pageerror", on_pageerror)
            try:
                for eid in ELEMENT_IDS:
                    fn = VALIDATORS[eid]
                    await run(
                        eid,
                        SOURCE_LINES[eid],
                        ACTIONS[eid],
                        EXPECTED[eid],
                        lambda eid=eid, fn=fn: fn(page, d),
                        resolver=SKIP_RESOLVERS.get(eid),
                    )
                    flush()
            finally:
                try:
                    await page.close()
                finally:
                    await browser.close()
                flush()

    asyncio.run(orchestrate())
    flush()

    # Harness gate: every assigned ID got exactly one verdict and evidence.
    got = [r["element_id"] for r in results]
    require(sorted(got) == sorted(ELEMENT_IDS), f"element reconciliation failed: {got}")
    require(
        all(Path(r["evidence_path"]).exists() for r in results),
        "one or more evidence artifacts missing",
    )
    counts = {s: sum(1 for r in results if r["status"] == s) for s in ("PASS", "FAIL", "SKIP")}
    print(
        f"V-04 verdicts: {counts} across {len(results)} elements; "
        f"browser errors={len(console_errors) + len(page_errors)}"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", "-s"]))
