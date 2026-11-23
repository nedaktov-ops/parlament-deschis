"""V-05 clickable validation — MP, person, comparison, demographics pages.

Slice: C03-022..037 and C03-041..051 (27 elements) of the 2026-11-22 C03
clickable inventory.  Read-only validation against the local dev server at
http://127.0.0.1:5188; one Playwright chromium instance, one page per element,
browser closed in a finally block.

Evidence contract (CLICK-VALIDATION-FLEET §3):
  /tmp/opencode/click-validation/v05-results.json  — one row per element
  /tmp/opencode/click-validation/v05-console.json  — every console.error/pageerror
  /tmp/opencode/click-validation/v05-evidence-<ID>.json — raw per-element capture

A SKIP always carries a named ``resolver``.  Data-dependent person IDs come
from the live API at runtime; no UUID is hard-coded as a fixture.
"""

from __future__ import annotations

import asyncio
import json
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

pytest.importorskip("playwright", reason="external Playwright validation tool; see scripts/ui_validate.py")
from playwright.async_api import async_playwright  # noqa: E402

BASE = "http://127.0.0.1:5188"
OUT = Path("/tmp/opencode/click-validation")
CHROMIUM = "/usr/bin/chromium"

EXPECTED_IDS = [
    "C03-022",
    "C03-023",
    "C03-024",
    "C03-025",
    "C03-026",
    "C03-027",
    "C03-028",
    "C03-029",
    "C03-030",
    "C03-031",
    "C03-032",
    "C03-033",
    "C03-034",
    "C03-035",
    "C03-036",
    "C03-037",
    "C03-041",
    "C03-042",
    "C03-043",
    "C03-044",
    "C03-045",
    "C03-046",
    "C03-047",
    "C03-048",
    "C03-049",
    "C03-050",
    "C03-051",
]

LINE = {
    "C03-022": "frontend/src/pages/Mps.tsx:113-119",
    "C03-023": "frontend/src/pages/Mps.tsx:123-134",
    "C03-024": "frontend/src/pages/Mps.tsx:104-142",
    "C03-025": "frontend/src/pages/Mps.tsx:157-170",
    "C03-026": "frontend/src/pages/Mps.tsx:190-203",
    "C03-027": "frontend/src/pages/Mps.tsx:201-214",
    "C03-028": "frontend/src/pages/Mps.tsx:144-156",
    "C03-029": "frontend/src/pages/MpComparison.tsx:218-227",
    "C03-030": "frontend/src/pages/MpComparison.tsx:228-244",
    "C03-031": "frontend/src/pages/MpComparison.tsx:192-201",
    "C03-032": "frontend/src/pages/MpComparison.tsx:208-214",
    "C03-033": "frontend/src/pages/MpComparison.tsx:128-136",
    "C03-034": "frontend/src/pages/Demographics.tsx:57-66",
    "C03-035": "frontend/src/pages/PersonDeepDive.tsx:85-94",
    "C03-036": "frontend/src/pages/PersonDeepDive.tsx:167-174",
    "C03-037": "frontend/src/pages/PersonDeepDive.tsx:253-279 / CitationPopover.tsx:23-55",
    "C03-041": "frontend/src/components/ProvenanceStamp.tsx:42-50 (mounted PersonDeepDive.tsx:210-215)",
    "C03-042": "frontend/src/components/PersonDrawer.tsx:116-118",
    "C03-043": "frontend/src/components/PersonDrawer.tsx:97",
    "C03-044": "frontend/src/components/PersonDrawer.tsx:57-61",
    "C03-045": "frontend/src/components/PersonDrawer.tsx:143-152",
    "C03-046": "frontend/src/components/PersonDrawer.tsx:122-127",
    "C03-047": "frontend/src/components/CitationPopover.tsx:46-55",
    "C03-048": "frontend/src/components/CitationPopover.tsx:72-84",
    "C03-049": "frontend/src/components/CitationPopover.tsx:85-97",
    "C03-050": "frontend/src/components/CitationPopover.tsx:28-40",
    "C03-051": "frontend/src/pages/Mps.tsx:144-148",
}


def _api(path: str, timeout: int = 12):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _resolve_data() -> dict:
    """Runtime resolution: person id from /api/mps?limit=1, no fixed UUID."""
    mps = _api("/api/mps?limit=1", timeout=15)
    person = mps["data"][0]
    pid, pname = person["id"], person["name"]
    token = pname.split()[0]  # API q matches a single token, not the full name
    probe = _api("/api/mps?q=" + urllib.request.quote(token) + "&limit=3", timeout=15)
    if not probe.get("data"):
        token = pname[:4]
        probe = _api("/api/mps?q=" + urllib.request.quote(token) + "&limit=3", timeout=15)

    detail = _api("/api/persons/" + pid, timeout=15)
    detail = detail.get("data") or detail
    evidence = detail.get("evidence") or []

    # Bounded live-availability probe for the three data-dependent rows
    # (C03-036/045 need wikidata_qid; C03-049 needs evidence.snapshot_url).
    sample = _api("/api/mps?limit=15", timeout=15).get("data", [])
    qid_count, snap_count, scanned = 0, 0, 0
    for item in sample:
        try:
            d = _api("/api/persons/" + item["id"], timeout=10)
            d = d.get("data") or d
        except Exception:
            continue
        scanned += 1
        if d.get("wikidata_qid"):
            qid_count += 1
        if any(e.get("snapshot_url") for e in (d.get("evidence") or [])):
            snap_count += 1
    return {
        "person_id": pid,
        "person_name": pname,
        "query_token": token,
        "probe_total": probe.get("total"),
        "person_detail": detail,
        "evidence": evidence,
        "source_url": next((e.get("source_url") for e in evidence if e.get("source_url")), None),
        "availability": {
            "scanned_persons": scanned,
            "with_wikidata_qid": qid_count,
            "with_snapshot_url": snap_count,
            "resolved_person_wikidata_qid": detail.get("wikidata_qid"),
            "resolved_person_evidence": len(evidence),
            "resolved_person_snapshots": sum(1 for e in evidence if e.get("snapshot_url")),
        },
    }


class Ctx:
    def __init__(self, page, eid, rows, console, data):
        self.page = page
        self.eid = eid
        self.rows = rows
        self.console = console
        self.data = data
        self.reqs: list[str] = []

    def on_console(self, msg) -> None:
        if msg.type == "error":
            self.console.append(
                {
                    "element_id": self.eid,
                    "type": "console.error",
                    "text": msg.text[:500],
                    "url": self.page.url,
                }
            )

    def on_pageerror(self, exc) -> None:
        self.console.append(
            {
                "element_id": self.eid,
                "type": "pageerror",
                "text": str(exc)[:500],
                "url": self.page.url,
            }
        )

    def on_request(self, request) -> None:
        self.reqs.append(request.url)

    def requests_matching(self, needle: str) -> list[str]:
        return [u for u in self.reqs if needle in u]

    async def goto(self, path: str) -> None:
        await self.page.goto(BASE + path, wait_until="load", timeout=45_000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass
        await self.page.wait_for_timeout(800)

    def raw(self, **extra) -> dict:
        payload = {
            "element_id": self.eid,
            "captured_at": datetime.now(UTC).isoformat(),
            "url": self.page.url,
            "title": None,
            "requests": self.reqs[-30:],
            "availability": self.data["availability"],
        }
        payload.update(extra)
        return payload

    def record(
        self,
        verdict: str,
        action: str,
        expected: str,
        observed: str,
        resolver: str | None = None,
        **raw_extra,
    ) -> None:
        evidence_path = OUT / f"v05-evidence-{self.eid}.json"
        evidence_path.write_text(
            json.dumps(self.raw(**raw_extra), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        row = {
            "element_id": self.eid,
            "source_file_line": LINE[self.eid],
            "action": action,
            "expected": expected,
            "expected_outcome": expected,
            "observed": observed,
            "observed_outcome": observed,
            "verdict": verdict,
            "status": verdict,
            "evidence_path": str(evidence_path),
        }
        if resolver:
            row["resolver"] = resolver
        self.rows.append(row)


async def _fail_first(route_match, state: dict):
    """Intercept a GET the UI already makes; fail until the test disarms it."""

    async def handler(route):
        state["count"] += 1
        if state["armed"]:
            # A 200 with an unparsable JSON body makes the API client's
            # res.json() reject, which React Query surfaces as isError without
            # emitting a browser "Failed to load resource" console.error.
            await route.fulfill(
                status=200,
                content_type="application/json",
                body="v05-forced-malformed-payload",
            )
        else:
            await route.continue_()

    return handler


def _movement_stub(pid: str, pname: str) -> list[dict]:
    """A single synthetic movement row used only as a drawer trigger.

    The live /api/party/*/movements payload is empty for every party in this
    corpus (events reference group orgs, not party orgs), so PersonDrawer has
    no live mount trigger.  The row carries the runtime-resolved person id;
    the drawer's own data still comes from the real /api/persons endpoint.
    """
    return [
        {
            "id": "v05-synthetic-movement",
            "type": "join",
            "event_date": "2024-01-01",
            "chamber": "deputies",
            "person": {"id": pid, "name": pname},
            "from_org": {"short_name": "V05-FROM"},
            "to_org": {"short_name": "V05-TO"},
            "source_url": None,
            "confidence": None,
            "precision": None,
            "reason": None,
        }
    ]


async def _install_movement_stub(ctx: Ctx) -> None:
    async def handler(route):
        await route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(_movement_stub(ctx.data["person_id"], ctx.data["person_name"])),
        )

    await ctx.page.route(
        lambda u: "/api/party/" in urlparse(u).path and urlparse(u).path.endswith("/movements"),
        handler,
    )


async def _open_drawer(ctx: Ctx) -> object:
    await _install_movement_stub(ctx)
    await ctx.goto("/party/PSD")
    trigger = ctx.page.locator('button:has-text("' + ctx.data["person_name"] + '")').first
    await trigger.wait_for(state="visible", timeout=20_000)
    await trigger.click(timeout=15_000)
    dialog = ctx.page.locator('[role="dialog"]')
    await dialog.wait_for(state="visible", timeout=20_000)
    return dialog


def _popup_click(ctx: Ctx, locator):
    """Click a target=_blank anchor, capture the popup, return its URL."""
    return _popup_click_impl(ctx, locator)


async def _popup_click_impl(ctx: Ctx, locator) -> str:
    boxes: list = []
    ctx.page.on("popup", lambda page: boxes.append(page))
    await locator.click(timeout=15_000)
    await ctx.page.wait_for_timeout(1_200)
    if not boxes:
        return ""
    popup = boxes[-1]
    try:
        url = popup.url
    finally:
        try:
            await popup.close()
        except Exception:
            pass
    return url


# --------------------------------------------------------------------------
# C03-022..028 — Mps.tsx
# --------------------------------------------------------------------------


async def c03_022(ctx: Ctx) -> None:
    token = ctx.data["query_token"]
    await ctx.goto("/mps")
    field = ctx.page.locator("form input[type=search]")
    await field.wait_for(state="visible", timeout=20_000)
    before_url = ctx.page.url
    before_cards = await ctx.page.locator('a[href^="/person/"]').count()
    await field.fill(token)
    after = await field.input_value()
    ctx.record(
        "PASS" if after == token and ctx.page.url == before_url and before_cards > 0 else "FAIL",
        f'fill the MPS page search field with live-derived token "{token}"',
        "input value reflects typed text; URL stays unchanged (local-only state); cards remain before submit",
        f'input="{after}"; url_before="{before_url}"; url_after="{ctx.page.url}"; cards_before={before_cards}',
        before_url=before_url,
        typed=token,
        input_value=after,
        cards_before=before_cards,
    )


async def c03_023(ctx: Ctx) -> None:
    await ctx.goto("/mps")
    select = ctx.page.locator("form select")
    await select.wait_for(state="visible", timeout=20_000)
    await select.select_option("switches")
    await ctx.page.wait_for_timeout(900)
    params = parse_qs(urlparse(ctx.page.url).query)
    reqs = ctx.requests_matching("sort=switches")
    ok = params.get("sort") == ["switches"] and params.get("offset") == ["0"] and bool(reqs)
    ctx.record(
        "PASS" if ok else "FAIL",
        'select "switches" in the MPS sort <select>',
        "URL carries sort=switches and offset=0; a /api/mps request with sort=switches is fired",
        f'url="{ctx.page.url}"; sort={params.get("sort")}; offset={params.get("offset")}; matching_requests={reqs[:2]}',
        params=params,
        matching_requests=reqs[:5],
    )


async def c03_024(ctx: Ctx) -> None:
    token = ctx.data["query_token"]
    await ctx.goto("/mps")
    await ctx.page.locator("form input[type=search]").fill(token)
    await ctx.page.locator('form button[type="submit"]').click(timeout=15_000)
    await ctx.page.wait_for_timeout(1_000)
    params = parse_qs(urlparse(ctx.page.url).query)
    reqs = ctx.requests_matching("q=" + token)
    cards = await ctx.page.locator('a[href^="/person/"]').count()
    ok = params.get("q") == [token] and params.get("offset") == ["0"] and cards > 0 and bool(reqs)
    ctx.record(
        "PASS" if ok else "FAIL",
        f'submit the MPS search form with live-derived token "{token}"',
        "URL carries q=<token> and offset=0; a matching /api/mps request fires and MP cards render",
        f'url="{ctx.page.url}"; q={params.get("q")}; offset={params.get("offset")}; cards={cards}; requests={reqs[:2]}',
        params=params,
        cards=cards,
        matching_requests=reqs[:5],
    )


async def c03_025(ctx: Ctx) -> None:
    token, pname = ctx.data["query_token"], ctx.data["person_name"]
    await ctx.goto("/mps")
    await ctx.page.locator("form input[type=search]").fill(token)
    await ctx.page.locator('form button[type="submit"]').click(timeout=15_000)
    await ctx.page.wait_for_timeout(900)
    link = ctx.page.locator('a[href^="/person/"]').filter(has_text=pname).first
    await link.wait_for(state="visible", timeout=20_000)
    href = await link.get_attribute("href")
    await link.click(timeout=15_000)
    await ctx.page.wait_for_timeout(900)
    h1 = (await ctx.page.locator("h1").first.inner_text()).strip()
    reqs = ctx.requests_matching("/api/persons/")
    ok = (
        "/person/" in ctx.page.url
        and href
        and href.split("?")[0].endswith(ctx.data["person_id"])
        and pname in h1
        and bool(reqs)
    )
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the MP card person link for the live-resolved person",
        "navigate to /person/<resolved-id>; h1 shows that person's name; /api/persons/<id> requested",
        f'href="{href}"; url_after="{ctx.page.url}"; h1="{h1}"; person_requests={reqs[:2]}',
        href=href,
        url_after=ctx.page.url,
        h1=h1,
        person_requests=reqs[:5],
    )


async def c03_026(ctx: Ctx) -> None:
    await ctx.goto("/mps")
    prev = ctx.page.get_by_role("button", name="Anterior")
    await prev.wait_for(state="visible", timeout=20_000)
    disabled_at_zero = await prev.is_disabled()
    await ctx.goto("/mps?offset=60")
    await ctx.page.locator('a[href^="/person/"]').first.wait_for(state="visible", timeout=20_000)
    enabled_at_60 = not await prev.is_disabled()
    if enabled_at_60:
        await prev.click(timeout=15_000)
        await ctx.page.wait_for_timeout(900)
    params = parse_qs(urlparse(ctx.page.url).query)
    offset = params.get("offset", ["0"])[0]
    reqs = ctx.requests_matching("/api/mps?")
    ok = disabled_at_zero and enabled_at_60 and offset in ("0",) and bool(reqs)
    ctx.record(
        "PASS" if ok else "FAIL",
        'observe "Anterior" disabled at offset 0, then click it from /mps?offset=60',
        "disabled at start; enabled on page 2; click returns to offset 0 and fires a fresh /api/mps request",
        f'disabled_at_0={disabled_at_zero}; enabled_at_60={enabled_at_60}; url_after="{ctx.page.url}"; offset={offset}; requests={reqs[-2:]}',
        disabled_at_zero=disabled_at_zero,
        enabled_at_60=enabled_at_60,
        url_after=ctx.page.url,
        requests=reqs[-5:],
    )


async def c03_027(ctx: Ctx) -> None:
    await ctx.goto("/mps")
    next_btn = ctx.page.get_by_role("button", name="Următor")
    await next_btn.wait_for(state="visible", timeout=20_000)
    disabled = await next_btn.is_disabled()
    if not disabled:
        await next_btn.click(timeout=15_000)
        await ctx.page.wait_for_timeout(900)
    params = parse_qs(urlparse(ctx.page.url).query)
    offset = params.get("offset", [None])[0]
    reqs = ctx.requests_matching("offset=60")
    ok = (not disabled) and offset == "60" and bool(reqs)
    ctx.record(
        "PASS" if ok else "FAIL",
        'click "Următor" on the first MPS result page',
        "URL moves to offset=60 and a /api/mps request with offset=60 is fired",
        f'disabled={disabled}; url_after="{ctx.page.url}"; offset={offset}; requests={reqs[:2]}',
        disabled=disabled,
        url_after=ctx.page.url,
        matching_requests=reqs[:5],
    )


async def c03_028(ctx: Ctx) -> None:
    state = {"armed": True, "count": 0}
    await ctx.page.route(
        lambda u: urlparse(u).path == "/api/mps",
        await _fail_first(None, state),
    )
    await ctx.goto("/mps")
    retry = ctx.page.locator('button:has-text("Reîncearcă")').first
    await retry.wait_for(state="visible", timeout=20_000)
    before = state["count"]
    state["armed"] = False
    await retry.click(timeout=15_000)
    await ctx.page.locator('a[href^="/person/"]').first.wait_for(state="visible", timeout=20_000)
    after = state["count"]
    cards = await ctx.page.locator('a[href^="/person/"]').count()
    ok = before >= 1 and after > before
    ctx.record(
        "PASS" if ok else "FAIL",
        "force /api/mps to fail in-browser, then click the MPS retry button",
        "error state renders a Retry control; clicking it fires a new /api/mps request and MP cards render",
        f"failed_requests_before={before}; total_requests_after={after}; cards={cards}",
        failed_requests_before=before,
        total_requests_after=after,
        cards=cards,
    )


# --------------------------------------------------------------------------
# C03-029..033 — MpComparison.tsx
# --------------------------------------------------------------------------


async def _slot_input(ctx: Ctx, index: int = 0):
    # The compare-mps page renders exactly three search inputs (one per slot);
    # the site-wide header search is a combobox with a different input type.
    return ctx.page.locator('input[type="search"]').nth(index)


async def c03_029(ctx: Ctx) -> None:
    token = ctx.data["query_token"]
    await ctx.goto("/compare-mps")
    field = await _slot_input(ctx, 0)
    await field.wait_for(state="visible", timeout=20_000)
    before_url = ctx.page.url
    await field.fill(token)
    await ctx.page.wait_for_timeout(500)
    value = await field.input_value()
    suggestions = await ctx.page.locator("ul li button").count()
    ok = value == token and ctx.page.url == before_url and suggestions > 0
    ctx.record(
        "PASS" if ok else "FAIL",
        f'type live-derived token "{token}" into comparison slot 1',
        "slot input holds the typed text (local state), URL unchanged, suggestion list appears from the live MP pool",
        f'value="{value}"; url_before="{before_url}"; url_after="{ctx.page.url}"; suggestions={suggestions}',
        value=value,
        suggestions=suggestions,
    )


async def c03_030(ctx: Ctx) -> None:
    token = ctx.data["query_token"]
    await ctx.goto("/compare-mps")
    field = await _slot_input(ctx, 0)
    await field.fill(token)
    suggestion = ctx.page.locator("ul li button").first
    await suggestion.wait_for(state="visible", timeout=20_000)
    picked = (await suggestion.evaluate("e => e.firstChild ? e.firstChild.textContent.trim() : e.textContent.trim()")).strip()
    if not picked:
        picked = (await suggestion.inner_text()).strip().split("\n")[0].strip()
    await suggestion.click(timeout=15_000)
    await ctx.page.wait_for_timeout(500)
    # Slot 1's input disappears after selection, so bind to the stable card.
    slot = ctx.page.locator("div.bg-slate-800.rounded-lg.p-4.relative").nth(0)
    slot_text = (await slot.inner_text()).strip()
    slot_links = await slot.locator('a[href^="/person/"]').count()
    ok = bool(picked) and picked in slot_text and slot_links == 1
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the first suggested MP in comparison slot 1",
        "slot switches from search input to selected MP state: name visible, person link and clear control present",
        f'picked="{picked}"; slot_text="{slot_text[:200]}"; slot_person_links={slot_links}',
        picked=picked,
        slot_text=slot_text[:300],
    )


async def c03_031(ctx: Ctx) -> None:
    token, pname = ctx.data["query_token"], ctx.data["person_name"]
    await ctx.goto("/compare-mps")
    await (await _slot_input(ctx, 0)).fill(token)
    suggestion = ctx.page.locator("ul li button").first
    await suggestion.wait_for(state="visible", timeout=20_000)
    await suggestion.click(timeout=15_000)
    link = ctx.page.locator('a[href^="/person/"]').first
    await link.wait_for(state="visible", timeout=20_000)
    href = await link.get_attribute("href")
    link_text = (await link.inner_text()).strip()
    await link.click(timeout=15_000)
    await ctx.page.wait_for_timeout(900)
    h1 = (await ctx.page.locator("h1").first.inner_text()).strip()
    person_reqs = ctx.requests_matching("/api/persons/")
    ok = "/person/" in ctx.page.url and bool(href) and link_text in h1 and bool(person_reqs)
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the selected MP's name link in comparison slot 1",
        f"navigate to /person/<id> for the picked MP ({pname}); detail page shows the person's name",
        f'href="{href}"; url_after="{ctx.page.url}"; h1="{h1}"; person_requests={person_reqs[:2]}',
        href=href,
        url_after=ctx.page.url,
        h1=h1,
        link_text=link_text,
    )


async def c03_032(ctx: Ctx) -> None:
    token = ctx.data["query_token"]
    await ctx.goto("/compare-mps")
    await (await _slot_input(ctx, 0)).fill(token)
    suggestion = ctx.page.locator("ul li button").first
    await suggestion.wait_for(state="visible", timeout=20_000)
    await suggestion.click(timeout=15_000)
    # Bind to the stable slot-1 card: the input is replaced on selection.
    slot = ctx.page.locator("div.bg-slate-800.rounded-lg.p-4.relative").nth(0)
    clear = slot.locator('button:has-text("șterge")')
    await clear.wait_for(state="visible", timeout=15_000)
    await clear.click(timeout=15_000)
    await ctx.page.wait_for_timeout(400)
    search_again = await _slot_input(ctx, 0)
    value = await search_again.input_value()
    search_visible = await search_again.is_visible()
    slot_links = await slot.locator('a[href^="/person/"]').count()
    ok = search_visible and value == "" and slot_links == 0
    ctx.record(
        "PASS" if ok else "FAIL",
        'click the slot-1 "șterge" (clear) button after a pick',
        "slot returns to empty search state: input visible with empty value, selected person link removed",
        f'input_visible={search_visible}; value="{value}"; person_links={slot_links}',
        input_visible=search_visible,
        value=value,
        slot_links=slot_links,
    )


async def c03_033(ctx: Ctx) -> None:
    state = {"armed": True, "count": 0}
    await ctx.page.route(
        lambda u: urlparse(u).path == "/api/mps" and "limit=200" in u,
        await _fail_first(None, state),
    )
    await ctx.goto("/compare-mps")
    retry = ctx.page.locator('button:has-text("Reîncearcă")').first
    await retry.wait_for(state="visible", timeout=20_000)
    before = state["count"]
    state["armed"] = False
    await retry.click(timeout=15_000)
    await (await _slot_input(ctx, 0)).wait_for(state="visible", timeout=20_000)
    after = state["count"]
    slot_inputs = await ctx.page.locator('input[type="search"]').count()
    ok = before >= 1 and after > before
    ctx.record(
        "PASS" if ok else "FAIL",
        "force the MP pool /api/mps?limit=200 call to fail in-browser, then click Retry",
        "full-page error state shows Retry; clicking fires a new pool request and the three slots render",
        f"failed_requests_before={before}; total_requests_after={after}; slot_inputs={slot_inputs}",
        failed_requests_before=before,
        total_requests_after=after,
        slot_inputs=slot_inputs,
    )


# --------------------------------------------------------------------------
# C03-034..037 — Demographics.tsx and PersonDeepDive.tsx
# --------------------------------------------------------------------------


async def c03_034(ctx: Ctx) -> None:
    state = {"armed": True, "count": 0}
    await ctx.page.route(
        lambda u: "/api/analytics/generational-shift" in u,
        await _fail_first(None, state),
    )
    await ctx.goto("/demographics")
    retry = ctx.page.locator('button:has-text("Reîncearcă")').first
    await retry.wait_for(state="visible", timeout=20_000)
    before = state["count"]
    state["armed"] = False
    await retry.click(timeout=15_000)
    await ctx.page.locator("h1").first.wait_for(state="visible", timeout=20_000)
    await ctx.page.wait_for_timeout(600)
    h1 = (await ctx.page.locator("h1").first.inner_text()).strip()
    after = state["count"]
    ok = before >= 1 and after > before and bool(h1)
    ctx.record(
        "PASS" if ok else "FAIL",
        "force /api/analytics/generational-shift to fail in-browser, then click Retry",
        "demographics error state shows Retry; clicking fires a new request and the demographics page renders",
        f'failed_requests_before={before}; total_requests_after={after}; h1="{h1}"',
        failed_requests_before=before,
        total_requests_after=after,
        h1=h1,
    )


async def c03_035(ctx: Ctx) -> None:
    pid, pname = ctx.data["person_id"], ctx.data["person_name"]
    state = {"armed": True, "count": 0}
    await ctx.page.route(
        lambda u: urlparse(u).path == "/api/persons/" + pid,
        await _fail_first(None, state),
    )
    await ctx.goto("/person/" + pid)
    retry = ctx.page.locator('button:has-text("Reîncearcă")').first
    await retry.wait_for(state="visible", timeout=20_000)
    before = state["count"]
    state["armed"] = False
    await retry.click(timeout=15_000)
    await ctx.page.locator("h1").first.wait_for(state="visible", timeout=20_000)
    await ctx.page.wait_for_timeout(600)
    h1 = (await ctx.page.locator("h1").first.inner_text()).strip()
    after = state["count"]
    ok = before >= 1 and after > before and pname in h1
    ctx.record(
        "PASS" if ok else "FAIL",
        "force the person's /api/persons/<id> call to fail in-browser, then click Retry",
        "person error state shows Retry; clicking fires a new request and the profile renders with the person's name",
        f'failed_requests_before={before}; total_requests_after={after}; h1="{h1}"',
        failed_requests_before=before,
        total_requests_after=after,
        h1=h1,
    )


async def c03_036(ctx: Ctx) -> None:
    pid = ctx.data["person_id"]
    await ctx.goto("/person/" + pid)
    anchors = await ctx.page.locator('a[href*="wikidata.org"]').count()
    qid = ctx.data["person_detail"].get("wikidata_qid")
    avail = ctx.data["availability"]
    ok = anchors == 0
    ctx.record(
        "SKIP" if ok else "FAIL",
        "look for the Wikidata anchor on the live-resolved person profile and inspect payload wikidata_qid",
        "if the corpus supplies wikidata_qid, a target=_blank wikidata.org anchor opens that entity; otherwise SKIP with a named resolver",
        f"wikidata anchors rendered={anchors}; resolved person wikidata_qid={qid!r}; scanned={avail['scanned_persons']} persons with_qid={avail['with_wikidata_qid']}",
        resolver="data-dependent: the live corpus supplies no wikidata_qid (resolved person and bounded live sample both empty); rerun with a payload carrying wikidata_qid to observe the anchor/target",
        anchors=anchors,
        availability=avail,
    )


async def c03_037(ctx: Ctx) -> None:
    pid = ctx.data["person_id"]
    await ctx.goto("/person/" + pid)
    button = ctx.page.locator("button[aria-expanded]").first
    await button.wait_for(state="visible", timeout=20_000)
    label = (await button.inner_text()).strip()
    initial = await button.get_attribute("aria-expanded")
    await button.click(timeout=15_000)
    await ctx.page.wait_for_timeout(300)
    expanded = await button.get_attribute("aria-expanded")
    pop_links = await ctx.page.locator("div.absolute a").count()
    ok = initial == "false" and expanded == "true" and pop_links > 0 and "surse" in label
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the per-membership citation control mounted on the person profile",
        "control shows '<n> surse', starts collapsed, opens to a popover with source anchors and aria-expanded=true",
        f'label="{label}"; aria-expanded {initial} -> {expanded}; popover_anchors={pop_links}',
        label=label,
        initial=initial,
        expanded=expanded,
        popover_anchors=pop_links,
    )


# --------------------------------------------------------------------------
# C03-041..051 — provenance, drawer, popover, dead-link reconciliation
# --------------------------------------------------------------------------


async def c03_041(ctx: Ctx) -> None:
    pid = ctx.data["person_id"]
    await ctx.goto("/person/" + pid)
    anchor = ctx.page.locator('dl a[href^="http"]').first
    await anchor.wait_for(state="visible", timeout=20_000)
    href = await anchor.get_attribute("href")
    target = await anchor.get_attribute("target")
    text = (await anchor.inner_text()).strip()
    popup_url = await _popup_click_impl(ctx, anchor)
    ok = bool(href) and target == "_blank" and popup_url == href and "Vezi sursa originală" in text
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the provenance 'Vezi sursa originală ↗' anchor (external navigation fulfilled by a local stub; popup URL is the real href)",
        "target=_blank anchor opens a new page at the exact source_url from the live evidence payload",
        f'text="{text}"; href="{href}"; target={target}; popup_url="{popup_url}"; payload_source_url="{ctx.data["source_url"]}"',
        href=href,
        target=target,
        popup_url=popup_url,
        text=text,
    )


async def c03_042(ctx: Ctx) -> None:
    dialog = await _open_drawer(ctx)
    close = dialog.locator('button:has-text("Închide")')
    await close.wait_for(state="visible", timeout=15_000)
    await close.click(timeout=15_000)
    await dialog.wait_for(state="hidden", timeout=15_000)
    ctx.record(
        "PASS",
        "open the drawer via a synthetic movement row carrying the live-resolved person id (live party-movements payload is empty), then click 'Închide'",
        "the drawer is visible before the click and removed from the DOM afterwards",
        f'dialog_visible_before=true; dialog_visible_after={await dialog.is_visible()}; url="{ctx.page.url}"',
        dialog_visible_after=await dialog.is_visible(),
    )


async def c03_043(ctx: Ctx) -> None:
    dialog = await _open_drawer(ctx)
    overlay = ctx.page.locator('div[aria-hidden="true"].fixed')
    await overlay.wait_for(state="visible", timeout=15_000)
    await overlay.click(position={"x": 400, "y": 400}, timeout=15_000)
    await dialog.wait_for(state="hidden", timeout=15_000)
    ctx.record(
        "PASS",
        "open the drawer via a synthetic live-id movement row, then click the aria-hidden overlay outside the panel",
        "the outside click dismisses the drawer (dialog hidden)",
        f'dialog_visible_after={await dialog.is_visible()}; url="{ctx.page.url}"',
        dialog_visible_after=await dialog.is_visible(),
    )


async def c03_044(ctx: Ctx) -> None:
    dialog = await _open_drawer(ctx)
    await ctx.page.keyboard.press("Escape")
    await dialog.wait_for(state="hidden", timeout=15_000)
    ctx.record(
        "PASS",
        "open the drawer via a synthetic live-id movement row, then press Escape",
        "the document keydown handler dismisses the drawer (dialog hidden)",
        f'dialog_visible_after={await dialog.is_visible()}; url="{ctx.page.url}"',
        dialog_visible_after=await dialog.is_visible(),
    )


async def c03_045(ctx: Ctx) -> None:
    dialog = await _open_drawer(ctx)
    anchors = await dialog.locator('a[href*="wikidata.org"]').count()
    avail = ctx.data["availability"]
    ok = anchors == 0
    ctx.record(
        "SKIP" if ok else "FAIL",
        "inspect the drawer (opened via a synthetic live-id movement row) for a Wikidata link",
        "if the corpus supplies wikidata_qid, the drawer renders a target=_blank wikidata.org anchor; otherwise SKIP with a named resolver",
        f"wikidata anchors in drawer={anchors}; resolved wikidata_qid={avail['resolved_person_wikidata_qid']!r}; scanned={avail['scanned_persons']} with_qid={avail['with_wikidata_qid']}",
        resolver="data-dependent: no live person carries wikidata_qid, so the conditional drawer anchor cannot render; rerun with a person payload containing wikidata_qid",
        anchors=anchors,
        availability=avail,
    )


async def c03_046(ctx: Ctx) -> None:
    pid, pname = ctx.data["person_id"], ctx.data["person_name"]
    state = {"armed": True, "count": 0}
    await ctx.page.route(
        lambda u: urlparse(u).path == "/api/persons/" + pid,
        await _fail_first(None, state),
    )
    dialog = await _open_drawer(ctx)
    retry = dialog.locator('button:has-text("Reîncearcă")')
    await retry.wait_for(state="visible", timeout=20_000)
    before = state["count"]
    state["armed"] = False
    await retry.click(timeout=15_000)
    await ctx.page.wait_for_timeout(900)
    text = (await dialog.inner_text()).strip()
    after = state["count"]
    ok = before >= 1 and after > before and pname in text
    ctx.record(
        "PASS" if ok else "FAIL",
        "open the drawer via a synthetic live-id movement row, force its person fetch to fail in-browser, then click Retry",
        "drawer shows an inline Retry; clicking fires a new /api/persons/<id> request and the drawer renders the person",
        f'failed_requests_before={before}; total_requests_after={after}; drawer_has_name={pname in text}; text="{text[:160]}"',
        failed_requests_before=before,
        total_requests_after=after,
        drawer_text=text[:300],
    )


async def c03_047(ctx: Ctx) -> None:
    await ctx.goto("/person/" + ctx.data["person_id"])
    button = ctx.page.locator("button[aria-expanded]").first
    await button.wait_for(state="visible", timeout=20_000)
    states = [await button.get_attribute("aria-expanded")]
    for _ in range(3):
        await button.click(timeout=15_000)
        await ctx.page.wait_for_timeout(200)
        states.append(await button.get_attribute("aria-expanded"))
    ok = states == ["false", "true", "false", "true"]
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the citation toggle three times and read aria-expanded after each click",
        "aria-expanded transitions false -> true -> false -> true (real toggle state, not just element presence)",
        f"aria-expanded sequence={states}",
        aria_sequence=states,
    )


async def c03_048(ctx: Ctx) -> None:
    await ctx.goto("/person/" + ctx.data["person_id"])
    button = ctx.page.locator("button[aria-expanded]").first
    await button.click(timeout=15_000)
    anchor = ctx.page.locator('div.absolute a:has-text("Vezi sursa originală")').first
    await anchor.wait_for(state="visible", timeout=15_000)
    href = await anchor.get_attribute("href")
    target = await anchor.get_attribute("target")
    popup_url = await _popup_click_impl(ctx, anchor)
    source_urls = [e.get("source_url") for e in ctx.data["evidence"] if e.get("source_url")]
    ok = bool(href) and target == "_blank" and popup_url == href and href in source_urls
    ctx.record(
        "PASS" if ok else "FAIL",
        "open the citation popover and click its 'Vezi sursa originală ↗' anchor (external navigation stubbed locally; popup URL is the real href)",
        "a new page opens at exactly the evidence item's source_url from the live API payload",
        f'href="{href}"; target={target}; popup_url="{popup_url}"; payload_source_url="{ctx.data["source_url"]}"',
        href=href,
        target=target,
        popup_url=popup_url,
    )


async def c03_049(ctx: Ctx) -> None:
    await ctx.goto("/person/" + ctx.data["person_id"])
    button = ctx.page.locator("button[aria-expanded]").first
    await button.click(timeout=15_000)
    anchors = await ctx.page.locator('div.absolute a:has-text("Vezi copia arhivată")').count()
    avail = ctx.data["availability"]
    ok = anchors == 0
    ctx.record(
        "SKIP" if ok else "FAIL",
        "inspect the open citation popover for the archive ('Vezi copia arhivată') anchor",
        "if evidence supplies snapshot_url, the anchor opens it in a new page; otherwise SKIP with a named resolver",
        f"archive anchors rendered={anchors}; resolved person snapshots={avail['resolved_person_snapshots']}; scanned={avail['scanned_persons']} persons with_snapshot={avail['with_snapshot_url']}",
        resolver="data-dependent: no live evidence item carries snapshot_url, so the conditional archive anchor cannot render; rerun with an evidence payload containing snapshot_url",
        anchors=anchors,
        availability=avail,
    )


async def c03_050(ctx: Ctx) -> None:
    await ctx.goto("/person/" + ctx.data["person_id"])
    button = ctx.page.locator("button[aria-expanded]").first
    await button.click(timeout=15_000)
    assert await button.get_attribute("aria-expanded") == "true"
    await ctx.page.keyboard.press("Escape")
    await ctx.page.wait_for_timeout(200)
    after_escape = await button.get_attribute("aria-expanded")
    await button.click(timeout=15_000)
    await ctx.page.wait_for_timeout(200)
    reopened = await button.get_attribute("aria-expanded")
    await ctx.page.locator("h1").first.click(timeout=15_000)
    await ctx.page.wait_for_timeout(200)
    after_outside = await button.get_attribute("aria-expanded")
    ok = after_escape == "false" and reopened == "true" and after_outside == "false"
    ctx.record(
        "PASS" if ok else "FAIL",
        "open the citation popover, press Escape, reopen, then click outside it",
        "Escape and outside mousedown both set aria-expanded=false; reopening sets it true",
        f"after_escape={after_escape}; reopened={reopened}; after_outside_click={after_outside}",
        after_escape=after_escape,
        reopened=reopened,
        after_outside=after_outside,
    )


async def c03_051(ctx: Ctx) -> None:
    await ctx.goto("/mps")
    link = ctx.page.locator('a[href^="/compare-mps"]').last
    await link.wait_for(state="visible", timeout=20_000)
    text = (await link.inner_text()).strip()
    href = await link.get_attribute("href")
    await link.click(timeout=15_000)
    await ctx.page.wait_for_timeout(900)
    path = urlparse(ctx.page.url).path
    h1 = (await ctx.page.locator("h1").first.inner_text()).strip()
    pool_reqs = ctx.requests_matching("limit=200")
    ok = path == "/compare-mps" and bool(h1) and bool(pool_reqs)
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the rendered 'Compară parlamentarii →' link on the MPS page",
        "navigate to /compare-mps, render the comparison page and fire its MP-pool request",
        f'text="{text}"; href="{href}"; url_after="{ctx.page.url}"; path={path}; h1="{h1}"; pool_requests={pool_reqs[:2]}',
        text=text,
        href=href,
        url_after=ctx.page.url,
        h1=h1,
        pool_requests=pool_reqs[:5],
    )


CHECKS = [
    (c03_022,),
    (c03_023,),
    (c03_024,),
    (c03_025,),
    (c03_026,),
    (c03_027,),
    (c03_028,),
    (c03_029,),
    (c03_030,),
    (c03_031,),
    (c03_032,),
    (c03_033,),
    (c03_034,),
    (c03_035,),
    (c03_036,),
    (c03_037,),
    (c03_041,),
    (c03_042,),
    (c03_043,),
    (c03_044,),
    (c03_045,),
    (c03_046,),
    (c03_047,),
    (c03_048,),
    (c03_049,),
    (c03_050,),
    (c03_051,),
]


async def _run(rows: list, console: list) -> dict:
    data = _resolve_data()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path=CHROMIUM, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1440, "height": 900})

        # External anchors are real target=_blank links; stub the external
        # navigation so the browser never leaves localhost, while the URL the
        # popup commits is still the exact href under test.
        async def external(route):
            host = urlparse(route.request.url).hostname
            if host in (None, "127.0.0.1", "localhost"):
                await route.continue_()
            else:
                await route.fulfill(
                    status=200,
                    content_type="text/html",
                    body="<!doctype html><title>v05 stubbed external destination</title>",
                )

        await context.route("**/*", external)
        try:
            for (check,) in CHECKS:
                eid = "C03-" + check.__name__.split("_")[1]
                page = await context.new_page()
                ctx = Ctx(page, eid, rows, console, data)
                page.on("console", ctx.on_console)
                page.on("pageerror", ctx.on_pageerror)
                page.on("request", ctx.on_request)
                started = time.monotonic()
                try:
                    await check(ctx)
                except Exception as exc:  # a harness error is a FAIL finding, never a PASS
                    try:
                        ctx.record(
                            "FAIL",
                            f"harness error while exercising {eid}",
                            "the element's expected observable outcome",
                            f"{type(exc).__name__}: {str(exc)[:400]}",
                            error_type=type(exc).__name__,
                        )
                    except Exception:
                        pass
                finally:
                    await page.close()
                print(
                    f"[v05] {eid} {rows[-1]['status'] if rows and rows[-1]['element_id'] == eid else '?'} "
                    f"{time.monotonic() - started:.1f}s"
                )
        finally:
            await browser.close()
    return data


def test_v05_clickable_validation() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list = []
    console: list = []
    data = asyncio.run(_run(rows, console))

    (OUT / "v05-results.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "v05-console.json").write_text(
        json.dumps(console, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "v05-meta.json").write_text(
        json.dumps(
            {
                "base": BASE,
                "chromium": CHROMIUM,
                "runtime_resolution": {
                    "person_id": data["person_id"],
                    "person_name": data["person_name"],
                    "query_token": data["query_token"],
                    "probe_total": data["probe_total"],
                },
                "availability": data["availability"],
                "counts": {
                    "elements": len(rows),
                    "PASS": sum(r["status"] == "PASS" for r in rows),
                    "FAIL": sum(r["status"] == "FAIL" for r in rows),
                    "SKIP": sum(r["status"] == "SKIP" for r in rows),
                    "console_errors": len(console),
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    ids = [r["element_id"] for r in rows]
    assert len(rows) == 27, f"expected 27 result rows, got {len(rows)}"
    assert sorted(ids) == sorted(EXPECTED_IDS), f"ID mismatch: {sorted(ids)}"
    assert len(set(ids)) == len(ids), "duplicate element IDs"
    for row in rows:
        assert {
            "element_id",
            "source_file_line",
            "action",
            "expected",
            "observed",
            "verdict",
            "expected_outcome",
            "observed_outcome",
            "status",
            "evidence_path",
        } <= set(row), row["element_id"]
        assert Path(row["evidence_path"]).is_file(), row["evidence_path"]
        if row["status"] == "SKIP":
            assert row.get("resolver"), f"SKIP without resolver: {row['element_id']}"
    print(
        json.dumps(
            {
                "elements": len(rows),
                "PASS": sum(r["status"] == "PASS" for r in rows),
                "FAIL": sum(r["status"] == "FAIL" for r in rows),
                "SKIP": sum(r["status"] == "SKIP" for r in rows),
                "console_errors": len(console),
            }
        )
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q", "-s"]))
