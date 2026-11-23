"""V-07 clickable validation — Voturi list and roll-call detail.

Slice: C04-001..014 (14 elements) of the 2026-11-22 C04 clickable inventory.
Read-only validation against the local dev server at http://127.0.0.1:5188;
one Playwright chromium instance, one page per element, browser closed in a
``finally`` block.

Evidence contract (CLICK-VALIDATION-FLEET §3):
  /tmp/opencode/click-validation/v07-results.json          — one row per element
  /tmp/opencode/click-validation/v07-console.json          — every console.error/pageerror
  /tmp/opencode/click-validation/v07-evidence-<ID>.json    — raw per-element capture
  /tmp/opencode/click-validation/v07-shot-<ID>.png         — viewport screenshot

A SKIP always carries a named ``resolver``.  Vote IDs and source URLs are
resolved from the live API at runtime; no UUID/ID is hard-coded as a fixture.
The two retry checks (C04-011/014) deliberately induce a React Query error by
serving a malformed JSON body for a GET the UI already makes; the interception
is disarmed before the retry is clicked and the induced condition is labelled
in both the evidence and the console capture.
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

EXPECTED_IDS = [f"C04-{n:03d}" for n in range(1, 15)]

# Localised (ro) strings observed on the live page; selectors are kept structural
# where possible and the exact text is captured as evidence on every row.
LABEL_SCOPE_SELECT = "Domeniu de vot (din corpus)"
LABEL_SEARCH_HINT = "Căutarea filtrează doar pagina curentă."
LABEL_ERROR = "Nu s-au putut încărca voturile."
LABEL_RETRY = "Reîncearcă"
LABEL_BACK = "← Înapoi la lista de voturi"
LABEL_POSITIONS_REGION = "Tabel derulabil cu pozițiile la vot"
LABEL_PROVENANCE = "Vezi sursa originală"
LABEL_TRUNCATION = "Sunt afișate doar primele"

LINE = {
    "C04-001": "frontend/src/components/ScopeControls.tsx:32-34 (rendered by Voturi.tsx:111-114)",
    "C04-002": "frontend/src/components/ScopeControls.tsx:40-45",
    "C04-003": "frontend/src/components/ScopeControls.tsx:51-56",
    "C04-004": "frontend/src/pages/Voturi.tsx:134-159",
    "C04-005": "frontend/src/pages/Voturi.tsx:161-175 (page-local hint :172-174; note :176-183)",
    "C04-006": "frontend/src/pages/Voturi.tsx:240-256 (goToVote :85-87)",
    "C04-007": "frontend/src/pages/Voturi.tsx:277-289",
    "C04-008": "frontend/src/pages/Voturi.tsx:318-326",
    "C04-009": "frontend/src/pages/Voturi.tsx:330-337",
    "C04-010": "frontend/src/pages/Voturi.tsx:342-353",
    "C04-011": "frontend/src/pages/Voturi.tsx:93-107 (AsyncState/ErrorState/RetryButton)",
    "C04-012": "frontend/src/pages/Voturi.tsx:354-359 -> ProvenanceStamp.tsx:42-50",
    "C04-013": "frontend/src/components/RollCallTable.tsx:109-149 (truncation note :81-85)",
    "C04-014": "frontend/src/components/RollCallTable.tsx:57-63",
}

INDUCED = {"C04-011", "C04-014"}


def _api(path: str, timeout: int = 15):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _resolve_data(date: str) -> dict:
    """Runtime resolution: scope probe + a data-bearing vote, no hard-coded ID."""
    probe = _api("/api/votes?limit=1", timeout=15)
    scopes = probe.get("scopes") or []
    # The page picks the highest-total scope; mirror that so the resolved vote
    # is actually rendered on page 1 of the default view.
    active = sorted(scopes, key=lambda s: s.get("total") or 0, reverse=True)[0]
    chamber, legislature = active.get("chamber"), active.get("legislature")
    q = f"/api/votes?chamber={chamber}&legislature={legislature}&to={date}&limit=100&offset=0"
    listing = _api(q, timeout=15)
    rows = listing.get("data") or []
    first = rows[0]
    native_id = str(first["native_vote_id"])
    detail = _api("/api/votes/" + native_id, timeout=15)
    positions = _api(f"/api/votes/{native_id}/positions?limit=500", timeout=15)
    pos_rows = positions.get("data") or []
    return {
        "date": date,
        "scopes": scopes,
        "active": {"chamber": chamber, "legislature": legislature},
        "votes_total": listing.get("total"),
        "native_vote_id": native_id,
        "first_title": first.get("title_raw") or native_id,
        "first_source_url": first.get("source_url"),
        "all_source_urls": [v.get("source_url") for v in rows if v.get("source_url")],
        "detail_payload": detail,
        "positions_total": positions.get("total"),
        "positions_len": len(pos_rows),
        "positions_source_urls": [p.get("source_url") for p in pos_rows if p.get("source_url")],
        "availability": {
            "scopes": len(scopes),
            "votes_total": listing.get("total"),
            "resolved_native_vote_id": native_id,
            "detail_source_url": (detail.get("data") or {}).get("source_url"),
            "detail_wrapper_keys": sorted(detail.keys()),
            "positions_total": positions.get("total"),
            "positions_rendered_capable": len(pos_rows),
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
        self.resps: list[tuple[str, int]] = []

    def on_console(self, msg) -> None:
        if msg.type == "error":
            self.console.append(
                {
                    "element_id": self.eid,
                    "type": "console.error",
                    "text": msg.text[:500],
                    "url": self.page.url,
                    "label": (
                        "induced-by-v07-interception (malformed JSON for a UI GET)"
                        if self.eid in INDUCED
                        else "uninduced-observation"
                    ),
                }
            )

    def on_pageerror(self, exc) -> None:
        self.console.append(
            {
                "element_id": self.eid,
                "type": "pageerror",
                "text": str(exc)[:500],
                "url": self.page.url,
                "label": (
                    "induced-by-v07-interception (malformed JSON for a UI GET)"
                    if self.eid in INDUCED
                    else "uninduced-observation"
                ),
            }
        )

    def on_request(self, request) -> None:
        self.reqs.append(request.url)

    def on_response(self, response) -> None:
        self.resps.append((response.url, response.status))

    def requests_matching(self, needle: str) -> list[str]:
        return [u for u in self.reqs if needle in u]

    async def goto(self, path: str = "/Voturi") -> None:
        await self.page.goto(BASE + path, wait_until="load", timeout=45_000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass
        await self.page.wait_for_timeout(900)

    async def record(
        self,
        verdict: str,
        action: str,
        expected: str,
        observed: str,
        resolver: str | None = None,
        **raw_extra,
    ) -> None:
        shot = OUT / f"v07-shot-{self.eid}.png"
        try:
            await self.page.screenshot(path=str(shot), timeout=10_000)
        except Exception:
            shot = None
        evidence_path = OUT / f"v07-evidence-{self.eid}.json"
        payload = {
            "element_id": self.eid,
            "captured_at": datetime.now(UTC).isoformat(),
            "url": self.page.url,
            "title": None,
            "requests": self.reqs[-40:],
            "responses": self.resps[-40:],
            "availability": self.data["availability"],
            "screenshot_path": str(shot) if shot else None,
        }
        if self.eid in INDUCED:
            payload["induced_error"] = (
                "Playwright route fulfilled a GET the UI already makes with an "
                "unparsable JSON body to drive React Query into isError; "
                "interception was disarmed before the retry click."
            )
        payload.update(raw_extra)
        evidence_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
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
        if shot:
            row["screenshot_path"] = str(shot)
        if resolver:
            row["resolver"] = resolver
        self.rows.append(row)


async def _malformed(route, state: dict, label: str) -> None:
    """Fail a UI GET with an unparsable 200 body; count every interception."""
    state["count"] += 1
    state.setdefault("labels", []).append(label)
    if state["armed"]:
        await route.fulfill(
            status=200, content_type="application/json", body="v07-forced-malformed-payload"
        )
    else:
        await route.continue_()


async def _popup_url(page, locator) -> str:
    boxes: list = []
    page.on("popup", lambda popup: boxes.append(popup))
    await locator.click(timeout=15_000)
    await page.wait_for_timeout(1_200)
    if not boxes:
        return ""
    popup = boxes[-1]
    try:
        return popup.url
    finally:
        try:
            await popup.close()
        except Exception:
            pass


# --------------------------------------------------------------------------
# C04-001..003 — ScopeControls on /Voturi
# --------------------------------------------------------------------------


async def c04_001(ctx: Ctx) -> None:
    await ctx.goto()
    field = ctx.page.locator("#scope-date")
    await field.wait_for(state="visible", timeout=20_000)
    before = await field.input_value()
    target = "2025-01-01"
    await field.fill(target)
    await ctx.page.wait_for_timeout(1_000)
    params = parse_qs(urlparse(ctx.page.url).query)
    reqs = ctx.requests_matching("to=" + target)
    scope_note = await ctx.page.get_by_text("Voturi până la " + target + ".").count()
    ok = params.get("date") == [target] and bool(reqs) and scope_note > 0
    await ctx.record(
        "PASS" if ok else "FAIL",
        f'fill the scope date input (#scope-date) with "{target}"',
        "URL carries date=<new date>; a /api/votes request with to=<new date> is fired; the scope note shows the new cutoff",
        f'url="{ctx.page.url}"; date={params.get("date")}; before="{before}"; to_requests={reqs[:2]}; scope_note_count={scope_note}',
        date_before=before,
        date_after=await field.input_value(),
        params=params,
        matching_requests=reqs[:5],
        scope_note_count=scope_note,
    )


async def c04_002(ctx: Ctx) -> None:
    await ctx.goto()
    select = ctx.page.locator("#scope-chamber")
    await select.wait_for(state="visible", timeout=20_000)
    note_before = (await ctx.page.locator("[aria-live=polite]").first.inner_text()).strip()
    reqs_before = len(ctx.requests_matching("/api/votes?"))
    await select.select_option("senate")
    await ctx.page.wait_for_timeout(1_100)
    params = parse_qs(urlparse(ctx.page.url).query)
    note_after = (await ctx.page.locator("[aria-live=polite]").first.inner_text()).strip()
    reqs_after = ctx.requests_matching("/api/votes?")
    ok = (
        params.get("chamber") == ["senate"]
        and note_after != note_before
        and len(reqs_after) > reqs_before
    )
    await ctx.record(
        "PASS" if ok else "FAIL",
        'select "senate" in the chamber scope select (#scope-chamber)',
        "URL carries chamber=senate; the scope note changes; a new /api/votes query fires",
        f'url="{ctx.page.url}"; chamber={params.get("chamber")}; note_before="{note_before}"; note_after="{note_after}"; votes_requests_before={reqs_before} after={len(reqs_after)}',
        params=params,
        note_before=note_before,
        note_after=note_after,
        votes_requests=reqs_after[-5:],
    )


async def c04_003(ctx: Ctx) -> None:
    await ctx.goto()
    select = ctx.page.locator("#scope-legislature")
    await select.wait_for(state="visible", timeout=20_000)
    await select.select_option("2024")
    await ctx.page.wait_for_timeout(1_100)
    params = parse_qs(urlparse(ctx.page.url).query)
    reqs = ctx.requests_matching("legislature=2024")
    note = (await ctx.page.locator("[aria-live=polite]").first.inner_text()).strip()
    ok = params.get("legislature") == ["2024"] and bool(reqs) and "2024" in note
    await ctx.record(
        "PASS" if ok else "FAIL",
        'select "2024" in the legislature scope select (#scope-legislature)',
        "URL carries legislature=2024; a /api/votes request with legislature=2024 is fired; scope note reflects 2024",
        f'url="{ctx.page.url}"; legislature={params.get("legislature")}; matching_requests={reqs[:2]}; scope_note="{note}"',
        params=params,
        matching_requests=reqs[:5],
        scope_note=note,
    )


# --------------------------------------------------------------------------
# C04-004..010 — Voturi.tsx controls
# --------------------------------------------------------------------------


async def c04_004(ctx: Ctx) -> None:
    await ctx.goto()
    select = ctx.page.locator('select:has(option[value*="|"])')
    await select.wait_for(state="visible", timeout=20_000)
    before = await select.input_value()
    options = await select.locator("option").evaluate_all(
        "es => es.map(e => ({value: e.value, text: e.textContent.trim()}))"
    )
    # Prefer a different *named* chamber scope; the "unknown" probe bucket maps
    # to "deputies" in the UI, so asserting its literal value would be wrong.
    target = next(
        (
            o
            for o in options
            if o["value"]
            and o["value"] != before
            and o["value"].startswith(("deputies|", "senate|"))
        ),
        None,
    )
    if not target:
        await ctx.record(
            "SKIP",
            "change the data-derived vote-scope <select>",
            "URL/scope note and paged query follow the chosen data-bearing scope",
            "the probe exposed no alternative scope option",
            resolver="data-dependent options — rerun with a corpus exposing >1 vote scope",
            options=options,
        )
        return
    await select.select_option(target["value"])
    await ctx.page.wait_for_timeout(1_100)
    params = parse_qs(urlparse(ctx.page.url).query)
    chamber, _, legislature = target["value"].partition("|")
    reqs = (
        ctx.requests_matching("legislature=" + legislature)
        if legislature
        else ctx.requests_matching("/api/votes?")
    )
    note = (await ctx.page.locator("[aria-live=polite]").first.inner_text()).strip()
    want_note = target["text"].replace("—", "/", 1) if "/" not in target["text"] else target["text"]
    ok = (
        await select.input_value() == target["value"]
        and params.get("chamber") == [chamber]
        and (
            params.get("legislature") == [legislature]
            if legislature
            else "legislature" not in params
        )
        and bool(reqs)
        and chamber in note
        and (legislature in note if legislature else True)
    )
    await ctx.record(
        "PASS" if ok else "FAIL",
        f'choose data-derived vote scope "{target["value"]}" in the scope <select>',
        "the select value, URL chamber/legislature, scope note and paged /api/votes query all follow the chosen scope",
        f'url="{ctx.page.url}"; selected="{await select.input_value()}"; chamber={params.get("chamber")}; legislature={params.get("legislature")}; note="{note}"; matching_requests={reqs[:2]}',
        before=before,
        target=target,
        options=options,
        params=params,
        matching_requests=reqs[:5],
        want_note=want_note,
    )


async def c04_005(ctx: Ctx) -> None:
    await ctx.goto()
    rows = ctx.page.locator("table.data-table tbody tr")
    await rows.first.wait_for(state="visible", timeout=20_000)
    rows_before = await rows.count()
    note_before = (await ctx.page.locator("[aria-live=polite]").nth(1).inner_text()).strip()
    token = ctx.data["first_title"][:12]
    field = ctx.page.locator('input[placeholder="Caută după titlu…"]')
    await field.wait_for(state="visible", timeout=20_000)
    await field.fill(token)
    await ctx.page.wait_for_timeout(900)
    params = parse_qs(urlparse(ctx.page.url).query)
    hint = await ctx.page.get_by_text(LABEL_SEARCH_HINT).count()
    rows_after = await rows.count()
    note_after = (await ctx.page.locator("[aria-live=polite]").nth(1).inner_text()).strip()
    ok = (
        params.get("query") == [token]
        and hint > 0
        and 0 < rows_after <= rows_before
        and note_after != note_before
    )
    await ctx.record(
        "PASS" if ok else "FAIL",
        f'fill the page-local title search with a live-derived token "{token}"',
        "URL carries query=<token>; the page-local hint is visible; rendered row count and page note narrow while scope/corpus totals stay unchanged",
        f'url="{ctx.page.url}"; query={params.get("query")}; hint_count={hint}; rows {rows_before}->{rows_after}; note_before="{note_before}"; note_after="{note_after}"',
        token=token,
        params=params,
        hint_count=hint,
        rows_before=rows_before,
        rows_after=rows_after,
        note_before=note_before,
        note_after=note_after,
    )


async def c04_006(ctx: Ctx) -> None:
    await ctx.goto()
    title = ctx.data["first_title"]
    btn = ctx.page.get_by_role("button", name="Poziții la vot — " + title)
    await btn.first.wait_for(state="visible", timeout=20_000)
    await btn.first.click(timeout=15_000)
    await ctx.page.wait_for_timeout(1_800)
    params = parse_qs(urlparse(ctx.page.url).query)
    heading = (await ctx.page.locator("h2").first.inner_text()).strip()
    pos_reqs = ctx.requests_matching("/positions")
    ok = (
        params.get("selectedVoteId") == [ctx.data["native_vote_id"]]
        and ctx.data["native_vote_id"] in heading
        and bool(pos_reqs)
    )
    await ctx.record(
        "PASS" if ok else "FAIL",
        "click the live-resolved vote row title button",
        "URL carries selectedVoteId=<native id>; detail heading shows that id; a /api/votes/<id>/positions request fires",
        f'url="{ctx.page.url}"; selectedVoteId={params.get("selectedVoteId")}; heading="{heading}"; position_requests={pos_reqs[:2]}',
        native_vote_id=ctx.data["native_vote_id"],
        params=params,
        heading=heading,
        position_requests=pos_reqs[:5],
    )


async def c04_007(ctx: Ctx) -> None:
    await ctx.goto()
    anchor = ctx.page.locator("table.data-table tbody tr td a[href]").first
    await anchor.wait_for(state="visible", timeout=20_000)
    href = await anchor.get_attribute("href")
    text = (await anchor.inner_text()).strip()
    target = await anchor.get_attribute("target")
    rel = await anchor.get_attribute("rel")
    popup = await _popup_url(ctx.page, anchor)
    ok = (
        href == ctx.data["first_source_url"]
        and href in ctx.data["all_source_urls"]
        and target == "_blank"
        and bool(rel)
        and "noopener" in rel
        and popup == href
    )
    await ctx.record(
        "PASS" if ok else "FAIL",
        "click the first vote-row source anchor (target=_blank)",
        "href equals a live /api/votes source_url; target=_blank and rel=noopener; the opened popup commits that exact URL and stays off production",
        f'text="{text}"; href="{href}"; api_first_source="{ctx.data["first_source_url"]}"; target={target}; rel={rel}; popup="{popup}"',
        href=href,
        text=text,
        target=target,
        rel=rel,
        popup_url=popup,
        api_source_in_listing=ctx.data["first_source_url"] in ctx.data["all_source_urls"],
    )


async def c04_008(ctx: Ctx) -> None:
    await ctx.goto()
    prev = ctx.page.get_by_role("button", name="Anterioare")
    nxt = ctx.page.get_by_role("button", name="Următoarele")
    await prev.wait_for(state="visible", timeout=20_000)
    disabled_at_zero = await prev.is_disabled()
    await nxt.click(timeout=15_000)
    await ctx.page.wait_for_timeout(1_200)
    range_at_100 = (await ctx.page.locator("[aria-live=polite]").nth(2).inner_text()).strip()
    enabled_at_100 = not await prev.is_disabled()
    reqs_before = len(ctx.requests_matching("/api/votes?"))
    if enabled_at_100:
        await prev.click(timeout=15_000)
        await ctx.page.wait_for_timeout(1_100)
    range_after = (await ctx.page.locator("[aria-live=polite]").nth(2).inner_text()).strip()
    votes_reqs_after = len(ctx.requests_matching("/api/votes?"))
    offset_zero_reqs = ctx.requests_matching("offset=0")
    # The offset=0 page was already fetched on first load, so React Query may
    # legitimately serve Previous from cache: the observable contract is the
    # disabled->enabled->disabled transition plus the range going back to 1-100.
    ok = (
        disabled_at_zero
        and enabled_at_100
        and "101" in range_at_100
        and "1–100" in range_after
        and bool(offset_zero_reqs)
    )
    await ctx.record(
        "PASS" if ok else "FAIL",
        "click Next then Previous in the vote-list pagination",
        "Previous is disabled at offset 0, enabled after Next, and returns the range to 1–100 (an offset=0 query is in the captured requests; it may be cached rather than refetched)",
        f'disabled_at_zero={disabled_at_zero}; range_after_next="{range_at_100}"; enabled_at_100={enabled_at_100}; range_after_prev="{range_after}"; offset0_requests={offset_zero_reqs[-3:]}; votes_reqs {reqs_before}->{votes_reqs_after} (cached OK)',
        disabled_at_zero=disabled_at_zero,
        range_at_100=range_at_100,
        enabled_at_100=enabled_at_100,
        range_after_prev=range_after,
        offset_zero_requests=offset_zero_reqs[-5:],
    )


async def c04_009(ctx: Ctx) -> None:
    await ctx.goto()
    nxt = ctx.page.get_by_role("button", name="Următoarele")
    await nxt.wait_for(state="visible", timeout=20_000)
    enabled_at_start = not await nxt.is_disabled()
    range_before = (await ctx.page.locator("[aria-live=polite]").nth(2).inner_text()).strip()
    reqs_before = len(ctx.requests_matching("/api/votes?"))
    await nxt.click(timeout=15_000)
    await ctx.page.wait_for_timeout(1_200)
    range_after = (await ctx.page.locator("[aria-live=polite]").nth(2).inner_text()).strip()
    offset_reqs = ctx.requests_matching("offset=100")
    disabled_at_end = await nxt.is_disabled()
    ok = (
        enabled_at_start
        and "1–100" in range_before
        and "101" in range_after
        and len(ctx.requests_matching("/api/votes?")) > reqs_before
        and bool(offset_reqs)
    )
    await ctx.record(
        "PASS" if ok else "FAIL",
        "click Next in the vote-list pagination",
        "range advances past row 100; an /api/votes request with offset=100 fires; Next becomes disabled at the corpus end",
        f'enabled_at_start={enabled_at_start}; range "{range_before}" -> "{range_after}"; offset100_requests={offset_reqs[:2]}; disabled_at_end={disabled_at_end}; votes_reqs {reqs_before}->{len(ctx.requests_matching("/api/votes?"))}',
        range_before=range_before,
        range_after=range_after,
        offset_100_requests=offset_reqs[:5],
        disabled_at_end=disabled_at_end,
    )


async def c04_010(ctx: Ctx) -> None:
    await ctx.goto("/Voturi?selectedVoteId=" + ctx.data["native_vote_id"])
    heading = ctx.page.locator("h2").first
    await heading.wait_for(state="visible", timeout=20_000)
    assert ctx.data["native_vote_id"] in (await heading.inner_text()).strip()
    back = ctx.page.get_by_role("button", name=LABEL_BACK)
    await back.wait_for(state="visible", timeout=20_000)
    await back.click(timeout=15_000)
    await ctx.page.wait_for_timeout(1_000)
    params = parse_qs(urlparse(ctx.page.url).query)
    detail_headings = (
        await ctx.page.locator("h2")
        .filter(has_text="Poziții la vot — " + ctx.data["native_vote_id"])
        .count()
    )
    rows = await ctx.page.locator("table.data-table tbody tr").count()
    ok = "selectedVoteId" not in params and detail_headings == 0 and rows > 0
    await ctx.record(
        "PASS" if ok else "FAIL",
        "click “← Back to votes list” in the open vote detail",
        "selectedVoteId is removed from the URL; the detail heading is gone; the vote list renders again",
        f'url="{ctx.page.url}"; params={params}; detail_heading_count={detail_headings}; rows={rows}',
        params=params,
        detail_heading_count=detail_headings,
        rows=rows,
    )


# --------------------------------------------------------------------------
# C04-011/012 — Voturi page-level retry and detail provenance
# --------------------------------------------------------------------------


async def c04_011(ctx: Ctx) -> None:
    state = {"armed": True, "count": 0, "labels": []}

    async def handler(route):
        await _malformed(route, state, "GET /api/votes?...limit=100 (paged vote query)")

    await ctx.page.route(
        lambda u: urlparse(u).path == "/api/votes" and "limit=100" in urlparse(u).query,
        handler,
    )
    await ctx.goto()
    retry = ctx.page.get_by_role("button", name=LABEL_RETRY)
    await retry.wait_for(state="visible", timeout=25_000)
    error_text = await ctx.page.get_by_text(LABEL_ERROR).count()
    intercepted_before = state["count"]
    state["armed"] = False
    await retry.click(timeout=15_000)
    try:
        await ctx.page.locator("table.data-table tbody tr").first.wait_for(
            state="visible", timeout=25_000
        )
        recovered = await ctx.page.locator("table.data-table tbody tr").count()
    except Exception:
        recovered = 0
    ok = (
        error_text > 0
        and intercepted_before > 0
        and state["count"] > intercepted_before
        and recovered > 0
    )
    await ctx.record(
        "PASS" if ok else "FAIL",
        "induce a paged /api/votes error, then click the page-level Retry",
        "error state shows the load-error text and a Retry button; after disarming the interception, Retry refetches and the vote table returns",
        f"error_text_count={error_text}; intercepts before={intercepted_before} after={state['count']}; rows_after_retry={recovered}; intercepted={state['labels'][:2]}",
        induced_intercepts=state["count"],
        error_text_count=error_text,
        rows_after_retry=recovered,
    )


async def c04_012(ctx: Ctx) -> None:
    vid = ctx.data["native_vote_id"]
    await ctx.goto("/Voturi?selectedVoteId=" + vid)
    heading = ctx.page.locator("h2").first
    await heading.wait_for(state="visible", timeout=20_000)
    try:
        await ctx.page.wait_for_response(
            lambda r: urlparse(r.url).path == "/api/votes/" + vid and r.status == 200,
            timeout=20_000,
        )
    except Exception:
        pass
    await ctx.page.wait_for_timeout(1_800)
    anchors = ctx.page.locator("a[href]").filter(has_text=LABEL_PROVENANCE)
    count = await anchors.count()
    href = await anchors.first.get_attribute("href") if count else None
    target = await anchors.first.get_attribute("target") if count else None
    rel = await anchors.first.get_attribute("rel") if count else None
    detail = ctx.data["detail_payload"]
    # The backend wraps the payload in {status, data_exists, data}; source_url
    # lives at data.source_url, never at the top level (api.py:1359-1381).
    api_source = (detail.get("data") or {}).get("source_url")
    detail_ok = any(
        urlparse(u).path == "/api/votes/" + vid and status == 200 for u, status in ctx.resps
    )
    body_has = LABEL_PROVENANCE in (await ctx.page.inner_text("body"))
    rel_ok = bool(rel) and "noopener" in rel and "noreferrer" in rel
    ok = (
        count == 1
        and bool(api_source)
        and href == api_source
        and target == "_blank"
        and rel_ok
        and body_has
        and detail_ok
    )
    await ctx.record(
        "PASS" if ok else "FAIL",
        "open the live-resolved vote detail and inspect the provenance “View original source” anchor",
        "exactly one “Vezi sursa originală ↗” anchor whose href equals the live /api/votes/{id} wrapper's data.source_url, with target=_blank and rel containing noopener and noreferrer; the translated label is visible",
        f'detail_http_ok={detail_ok}; api_data_source_url="{api_source}"; provenance_anchor_count={count}; href="{href}"; target={target}; rel={rel}; rel_ok={rel_ok}; body_contains_label={body_has}; detail_wrapper_keys={sorted(detail.keys())}',
        detail_http_ok=detail_ok,
        api_data_source_url=api_source,
        detail_top_level_source_url=detail.get("source_url"),
        detail_wrapper_keys=sorted(detail.keys()),
        provenance_anchor_count=count,
        provenance_href=href,
        provenance_target=target,
        provenance_rel=rel,
        provenance_rel_ok=rel_ok,
        body_contains_label=body_has,
    )


# --------------------------------------------------------------------------
# C04-013/014 — RollCallTable anchors, truncation note, retry
# --------------------------------------------------------------------------


async def c04_013(ctx: Ctx) -> None:
    await ctx.goto("/Voturi?selectedVoteId=" + ctx.data["native_vote_id"])
    region = ctx.page.locator('[role="region"][aria-label="' + LABEL_POSITIONS_REGION + '"]')
    await region.wait_for(state="visible", timeout=25_000)
    anchors = region.locator("a[href]")
    try:
        await anchors.first.wait_for(state="visible", timeout=20_000)
    except Exception:
        pass
    rendered = await anchors.count()
    hrefs = await anchors.evaluate_all("es => es.slice(0, 8).map(e => e.getAttribute('href'))")
    targets = await anchors.evaluate_all("es => es.slice(0, 5).map(e => e.getAttribute('target'))")
    rels = await anchors.evaluate_all("es => es.slice(0, 5).map(e => e.getAttribute('rel'))")
    api_urls = set(ctx.data["positions_source_urls"])
    hrefs_match = rendered > 0 and all(h in api_urls for h in hrefs if h)
    safe = (
        bool(targets)
        and all(t == "_blank" for t in targets)
        and all(r and "noopener" in r for r in rels)
    )
    notes = await ctx.page.locator("[role=note]").all_inner_texts()
    trunc_present = any(LABEL_TRUNCATION in n for n in notes)
    expect_trunc = ctx.data["positions_total"] > rendered
    ok = rendered > 0 and hrefs_match and safe and trunc_present == expect_trunc
    await ctx.record(
        "PASS" if ok else "FAIL",
        "open the roll-call positions table and inspect its source anchors and truncation disclosure",
        "one target=_blank/noopener source anchor per rendered position, each href matching a live /api/votes/{id}/positions source_url; the truncation note appears iff the API total exceeds the rendered rows",
        f"rendered={rendered}; api_total={ctx.data['positions_total']}; first_hrefs={hrefs[:3]}; all_hrefs_in_api={hrefs_match}; safe={safe}; truncation_note_present={trunc_present}; expected_truncation={expect_trunc}",
        rendered_anchors=rendered,
        api_total=ctx.data["positions_total"],
        first_hrefs=hrefs[:8],
        targets=targets[:5],
        rels=rels[:5],
        all_hrefs_in_api=hrefs_match,
        truncation_note_present=trunc_present,
        expected_truncation=expect_trunc,
    )


async def c04_014(ctx: Ctx) -> None:
    vid = ctx.data["native_vote_id"]
    state = {"armed": True, "count": 0, "labels": []}

    async def handler(route):
        await _malformed(
            route, state, f"GET /api/votes/{vid}/positions?limit=500 (roll-call positions)"
        )

    await ctx.page.route(lambda u: urlparse(u).path == f"/api/votes/{vid}/positions", handler)
    await ctx.goto("/Voturi?selectedVoteId=" + vid)
    retry = ctx.page.get_by_role("button", name=LABEL_RETRY)
    await retry.wait_for(state="visible", timeout=25_000)
    error_text = await ctx.page.get_by_text(LABEL_ERROR).count()
    intercepted_before = state["count"]
    state["armed"] = False
    await retry.click(timeout=15_000)
    region = ctx.page.locator('[role="region"][aria-label="' + LABEL_POSITIONS_REGION + '"]')
    try:
        await region.wait_for(state="visible", timeout=25_000)
        recovered = await region.locator("a[href]").count()
    except Exception:
        recovered = 0
    ok = (
        error_text > 0
        and intercepted_before > 0
        and state["count"] > intercepted_before
        and recovered > 0
    )
    await ctx.record(
        "PASS" if ok else "FAIL",
        "induce a roll-call positions error, then click the RollCallTable Retry",
        "error state shows the load-error text and a Retry button; after disarming, Retry refetches positions and the source-anchor table returns",
        f"error_text_count={error_text}; intercepts before={intercepted_before} after={state['count']}; anchors_after_retry={recovered}; intercepted={state['labels'][:2]}",
        induced_intercepts=state["count"],
        error_text_count=error_text,
        anchors_after_retry=recovered,
    )


CHECKS = [
    c04_001,
    c04_002,
    c04_003,
    c04_004,
    c04_005,
    c04_006,
    c04_007,
    c04_008,
    c04_009,
    c04_010,
    c04_011,
    c04_012,
    c04_013,
    c04_014,
]


async def _run(rows: list, console: list) -> dict:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path=CHROMIUM, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1440, "height": 900})

        # target=_blank anchors are real external links; stub only the external
        # navigation so the browser never leaves localhost while the popup URL
        # still commits the exact href under test.
        async def external(route):
            host = urlparse(route.request.url).hostname
            if host in (None, "127.0.0.1", "localhost"):
                await route.continue_()
            else:
                await route.fulfill(
                    status=200,
                    content_type="text/html",
                    body="<!doctype html><title>v07 stubbed external destination</title>",
                )

        await context.route("**/*", external)
        try:
            # Bootstrap: read the browser's own scope date, then resolve the
            # data-bearing vote IDs/URLs from the live API (no hard-coded ID).
            boot = await context.new_page()
            await boot.goto(BASE + "/Voturi", wait_until="load", timeout=45_000)
            try:
                await boot.wait_for_load_state("networkidle", timeout=8_000)
            except Exception:
                pass
            await boot.locator("#scope-date").wait_for(state="visible", timeout=20_000)
            date = await boot.locator("#scope-date").input_value()
            await boot.close()
            data = _resolve_data(date)

            for check in CHECKS:
                eid = "C04-" + check.__name__.split("_")[1]
                page = await context.new_page()
                ctx = Ctx(page, eid, rows, console, data)
                page.on("console", ctx.on_console)
                page.on("pageerror", ctx.on_pageerror)
                page.on("request", ctx.on_request)
                page.on("response", ctx.on_response)
                started = time.monotonic()
                try:
                    await check(ctx)
                except Exception as exc:  # harness error is a FAIL finding, never a PASS
                    try:
                        await ctx.record(
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
                status = next((r["status"] for r in rows if r["element_id"] == eid), "?")
                print(f"[v07] {eid} {status} {time.monotonic() - started:.1f}s", flush=True)
        finally:
            await browser.close()
    return data


def test_v07_clickable_validation() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list = []
    console: list = []
    data = asyncio.run(_run(rows, console))

    (OUT / "v07-results.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "v07-console.json").write_text(
        json.dumps(console, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "v07-meta.json").write_text(
        json.dumps(
            {
                "base": BASE,
                "chromium": CHROMIUM,
                "runtime_resolution": {
                    "date": data["date"],
                    "active_scope": data["active"],
                    "native_vote_id": data["native_vote_id"],
                    "first_title": data["first_title"],
                    "first_source_url": data["first_source_url"],
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
    assert len(rows) == 14, f"expected 14 result rows, got {len(rows)}"
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
        ),
        flush=True,
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q", "-s"]))
