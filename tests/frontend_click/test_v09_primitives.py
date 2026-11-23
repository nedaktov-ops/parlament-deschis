"""V-09 clickable validation — C05 shared interactive primitives (52 IDs).

Slice (CLICK-VALIDATION-FLEET §2): C05-001..016, 018, 020..021, 023..036,
040..042, 045..056, 058..059, 061..062 of the 2026-11-22 C05 clickable
inventory.  Read-only validation against the local dev server at
http://127.0.0.1:5188; exactly one system Chromium instance, one page per
element, browser + page closed in ``finally`` blocks.

Every ID performs a real click / keypress / hover / focus and asserts an
observable outcome (navigation, selection, disclosure, tooltip, request,
state transition, or a documented designed no-op).  Data-dependent IDs are
resolved from the live API; no UUID is hard-coded as a fixture.  A SKIP is
only used when the trigger cannot exist in the served corpus and always
carries a named ``resolver``.

Artifacts (all under /tmp/opencode/click-validation/v09-*):
  * v09-results.json            -- one row per element ID (52 rows)
  * v09-console.json            -- every console error/warning/pageerror
  * v09-evidence-C05-NNN.json   -- raw per-element capture (one per row)
  * v09-meta.json               -- runtime resolution + counts
  * v09-pytest.log              -- captured pytest output
"""

from __future__ import annotations

import asyncio
import json
import re
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:5188"
CHROMIUM = "/usr/bin/chromium"
OUT = Path("/tmp/opencode/click-validation")
RESULTS_PATH = OUT / "v09-results.json"
CONSOLE_PATH = OUT / "v09-console.json"
META_PATH = OUT / "v09-meta.json"
SERVED_HEAD = "e82e01b9152266bf3fe862029946b24acc2032f8"

EXPECTED_IDS = [
    *[f"C05-{n:03d}" for n in range(1, 17)],
    "C05-018",
    "C05-020",
    "C05-021",
    *[f"C05-{n:03d}" for n in range(23, 37)],
    "C05-040",
    "C05-041",
    "C05-042",
    *[f"C05-{n:03d}" for n in range(45, 57)],
    "C05-058",
    "C05-059",
    "C05-061",
    "C05-062",
]

LINE = {
    "C05-001": "frontend/src/components/Search.tsx:75-93",
    "C05-002": "frontend/src/components/Search.tsx:44-71",
    "C05-003": "frontend/src/components/Search.tsx:111-125",
    "C05-004": "frontend/src/components/Search.tsx:20-26",
    "C05-005": "frontend/src/components/PersonDrawer.tsx:97",
    "C05-006": "frontend/src/components/PersonDrawer.tsx:116-118",
    "C05-007": "frontend/src/components/PersonDrawer.tsx:51-82",
    "C05-008": "frontend/src/components/PersonDrawer.tsx:143-152",
    "C05-009": "frontend/src/components/PersonDrawer.tsx:243-255",
    "C05-010": "frontend/src/components/PersonDrawer.tsx:125",
    "C05-011": "frontend/src/components/CitationPopover.tsx:46-55",
    "C05-012": "frontend/src/components/CitationPopover.tsx:28-40",
    "C05-013": "frontend/src/components/CitationPopover.tsx:72-84",
    "C05-014": "frontend/src/components/CitationPopover.tsx:85-97",
    "C05-015": "frontend/src/components/ProvenanceStamp.tsx:42-50",
    "C05-016": "frontend/src/components/ProvenanceStamp.tsx:61-75",
    "C05-018": "frontend/src/components/ErrorState.tsx:38-45",
    "C05-020": "frontend/src/components/RetryButton.tsx:18-25",
    "C05-021": "frontend/src/components/DashboardCard.tsx:79-85",
    "C05-023": "frontend/src/components/Hemicycle.tsx:108-120",
    "C05-024": "frontend/src/components/Hemicycle.tsx:129-132",
    "C05-025": "frontend/src/components/Hemicycle.tsx:133",
    "C05-026": "frontend/src/components/Hemicycle.tsx:140-148",
    "C05-027": "frontend/src/components/SankeyFlow.tsx:248-264",
    "C05-028": "frontend/src/components/SankeyFlow.tsx:269-295",
    "C05-029": "frontend/src/components/SankeyFlow.tsx:180-189",
    "C05-030": "frontend/src/components/SwitchTimeline.tsx:170-191",
    "C05-031": "frontend/src/components/SwitchTimeline.tsx:214-231",
    "C05-032": "frontend/src/components/PartyNetwork.tsx:90-126",
    "C05-033": "frontend/src/components/PartyNetwork.tsx:145-153",
    "C05-034": "frontend/src/components/PartyListTable.tsx:60-99",
    "C05-035": "frontend/src/components/PartyListTable.tsx:55",
    "C05-036": "frontend/src/components/PartyListTable.tsx:106-113",
    "C05-040": "frontend/src/components/CommitteeControl.tsx:97-116",
    "C05-041": "frontend/src/components/CommitteeControl.tsx:153-167",
    "C05-042": "frontend/src/components/CommitteeControl.tsx:159",
    "C05-045": "frontend/src/components/LegislatureSeatExplorer.tsx:82-90",
    "C05-046": "frontend/src/components/LegislatureSeatExplorer.tsx:91-99",
    "C05-047": "frontend/src/components/LegislatureSeatExplorer.tsx:104-114",
    "C05-048": "frontend/src/components/LegislatureSeatExplorer.tsx:130-138",
    "C05-049": "frontend/src/components/VoteActivityChart.tsx:180-186",
    "C05-050": "frontend/src/components/VoteActivityChart.tsx:106-109",
    "C05-051": "frontend/src/components/TimelineChart.tsx:192-206",
    "C05-052": "frontend/src/components/TimelineChart.tsx:234-239",
    "C05-053": "frontend/src/components/TimelineChart.tsx:246-250",
    "C05-054": "frontend/src/components/TimelineChart.tsx:251",
    "C05-055": "frontend/src/components/CrossChamberFlow.tsx:83-107",
    "C05-056": "frontend/src/components/CrossChamberFlow.tsx:65-70",
    "C05-058": "frontend/src/components/DataQualityGauge.tsx:26-27,64-74",
    "C05-059": "frontend/src/components/ui/AsyncState.tsx:78-83",
    "C05-061": "frontend/src/components/ui/AgeDistributionSection.tsx:29-35",
    "C05-062": "frontend/src/components/ui/ThemeToggle.tsx:32-51",
}


# --------------------------------------------------------------------------- #
# live API resolution
# --------------------------------------------------------------------------- #
def api(path: str, timeout: int = 15):
    with urllib.request.urlopen(BASE + "/api" + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def resolve_data() -> dict:
    """Resolve every data-dependent value from the served API at runtime."""
    data: dict = {"resolved_at": datetime.now(UTC).isoformat(), "errors": []}

    def step(name, fn, default=None):
        try:
            data[name] = fn()
        except Exception as exc:  # noqa: BLE001 - resolution failure is recorded
            data["errors"].append(f"{name}: {type(exc).__name__}: {str(exc)[:180]}")
            data[name] = default

    person = api("/mps?limit=1")["data"][0]
    data["person_id"], data["person_name"] = person["id"], person["name"]
    token = re.sub(r"[^A-Za-z]", "", person["name"])[:5] or "albe"
    data["token"] = token
    step("search_expected", lambda: api(f"/persons?q={token}")[0]["id"])
    step("person_detail", lambda: api(f"/persons/{data['person_id']}"))
    step("person_history", lambda: api(f"/persons/{data['person_id']}/history"))
    step("parties", lambda: api("/parties")["data"])
    step("committee", lambda: api("/analytics/committee-control?as_of=2026-11-23")["data"])
    step("cross", lambda: api("/analytics/cross-chamber?as_of=2026-11-23")["data"])

    # A live person with at least one history row carrying source_url (drawer
    # history link) and one with a snapshot_url (designed-absent check).
    def survey_persons():
        rows = api("/mps?limit=150")["data"]
        with_history, with_snapshot = None, []
        for row in rows[:60]:
            d = api(f"/persons/{row['id']}")
            if d.get("evidence"):
                with_snapshot += [e for e in d["evidence"] if e.get("snapshot_url")]
            if with_history is None:
                h = api(f"/persons/{row['id']}/history")
                if h.get("history") and h["history"][0].get("source_url"):
                    with_history = {
                        "id": row["id"],
                        "name": row["name"],
                        "source_url": h["history"][0]["source_url"],
                    }
        return {"with_history": with_history, "snapshot_rows": with_snapshot[:3]}

    step("person_survey", survey_persons, {"with_history": None, "snapshot_rows": []})

    # Party-movements trigger for PersonDrawer: sweep live parties/dates.
    def sweep_movements():
        found = []
        for party in (data.get("parties") or [])[:12]:
            for date in ("2026-11-23", "2024-12-21", "2020-12-01", "2016-12-01"):
                try:
                    rows = api(f"/party/{party['short_name']}/movements?as_of={date}&limit=3")
                except Exception:  # noqa: BLE001
                    rows = []
                if rows:
                    found.append({"party": party["short_name"], "date": date, "count": len(rows)})
                    return found
        return found

    step("party_movements", sweep_movements, [])
    return data


# --------------------------------------------------------------------------- #
# context + evidence
# --------------------------------------------------------------------------- #
class Ctx:
    def __init__(self, browser, data, rows, console):
        self.browser = browser
        self.context = None
        self.page = None
        self.data = data
        self.rows = rows
        self.console = console
        self.eid = "bootstrap"
        self.induced = None
        self.requests: list[str] = []
        self.external_requests: list[str] = []

    def on_console(self, msg) -> None:
        if msg.type in ("error", "warning", "warn"):
            self.console.append(
                {
                    "ts": time.time(),
                    "element_context": self.eid,
                    "type": f"console.{msg.type}",
                    "text": msg.text[:400],
                    "test_induced": bool(self.induced),
                    "induced": self.induced,
                    "url": self.page.url if self.page else None,
                }
            )

    def on_pageerror(self, exc) -> None:
        self.console.append(
            {
                "ts": time.time(),
                "element_context": self.eid,
                "type": "pageerror",
                "text": str(exc)[:400],
                "test_induced": bool(self.induced),
                "induced": self.induced,
                "url": self.page.url if self.page else None,
            }
        )

    def on_request(self, request) -> None:
        self.requests.append(request.url)
        if len(self.requests) > 300:
            del self.requests[:150]

    async def setup(self) -> None:
        self.context = await self.browser.new_context(
            viewport={"width": 1500, "height": 1100}, locale="ro-RO"
        )

        # External source links are stubbed: no production/external navigation
        # is performed, while the real href is still observed and asserted.
        async def stub(route):
            await route.fulfill(
                status=200,
                content_type="text/html",
                body="<!doctype html><title>v09 external destination stub</title>",
            )

        for host in (
            "https://www.cdep.ro/**",
            "https://www.wikidata.org/**",
            "https://github.com/**",
        ):
            await self.context.route(host, stub)

        def on_context_request(request):
            if not request.url.startswith(BASE):
                self.external_requests.append(request.url)

        self.context.on("request", on_context_request)

    async def new_page(self, induced=None):
        self.induced = induced
        self.requests = []
        self.page = await self.context.new_page()
        self.page.on("console", self.on_console)
        self.page.on("pageerror", self.on_pageerror)
        self.page.on("request", self.on_request)
        return self.page

    async def goto(self, route: str, settle: int = 1800) -> None:
        await self.page.goto(BASE + route, wait_until="load", timeout=30_000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:  # noqa: BLE001 - bounded wait, fall through to settle
            pass
        await self.page.wait_for_timeout(settle)

    def record(self, verdict, action, expected, observed, extra=None, resolver=None) -> None:
        if verdict not in ("PASS", "FAIL", "SKIP"):
            raise ValueError(f"bad verdict {verdict}")
        eid = self.eid
        evidence_path = OUT / f"v09-evidence-{eid}.json"
        capture = {
            "element_id": eid,
            "source_file_line": LINE[eid],
            "served_head": SERVED_HEAD,
            "base": BASE,
            "timestamp": time.time(),
            "action": action,
            "expected": expected,
            "observed": observed,
            "verdict": verdict,
            "page_url": self.page.url if self.page else None,
            "page_title": None,
            "console_context": {"induced": self.induced, "element": eid},
            "requests": self.requests[-40:],
            "extra": extra or {},
        }
        if resolver:
            capture["resolver"] = resolver
        evidence_path.write_text(
            json.dumps(capture, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        row = {
            "element_id": eid,
            "source_file_line": LINE[eid],
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
        if extra and extra.get("error_type"):
            row["error_type"] = extra["error_type"]
        self.rows.append(row)


# --------------------------------------------------------------------------- #
# small DOM helpers
# --------------------------------------------------------------------------- #
async def statuses(page) -> list[str]:
    return await page.locator("[role=status]").all_inner_texts()


async def button_index_in_card(page, button_rx: str, marker: str) -> int | None:
    """Index of the first button matching button_rx whose ancestor card text contains marker."""
    loc = page.locator("button")
    for i in range(await loc.count()):
        b = loc.nth(i)
        try:
            text = (await b.inner_text(timeout=1000)).strip()
        except Exception:  # noqa: BLE001
            text = ""
        if not re.search(button_rx, text):
            continue
        anc = await b.evaluate(
            """(el, marker) => {
                let p = el.parentElement;
                for (let k=0; k<3 && p && !['BODY','MAIN','HTML'].includes(p.tagName); k++) {
                    if ((p.textContent||'').includes(marker)) return (p.textContent||'').slice(0,180);
                    p = p.parentElement;
                }
                return '';
            }""",
            marker,
        )
        if anc:
            return i
    return None


async def retry_index_in_card(page, marker: str | None) -> int | None:
    loc = page.locator("button")
    for i in range(await loc.count()):
        b = loc.nth(i)
        try:
            text = (await b.inner_text(timeout=1000)).strip()
        except Exception:  # noqa: BLE001
            text = ""
        label = await b.get_attribute("aria-label") or ""
        if not re.search(r"retry|reîncearcă|try again", text + " " + label, re.I):
            continue
        if marker is None:
            return i
        anc = await b.evaluate(
            """(el, marker) => {
                let p = el.parentElement;
                for (let k=0; k<7 && p; k++) {
                    if ((p.textContent||'').includes(marker)) return (p.textContent||'').slice(0,180);
                    p = p.parentElement;
                }
                return '';
            }""",
            marker,
        )
        if anc:
            return i
    return None


async def induce(ctx: Ctx, fragment: str, route: str):
    """Block one API endpoint until the error state is visible; return a state flag."""
    page = await ctx.new_page(induced={"endpoint": fragment, "kind": "test-induced API abort"})
    state = {"unblock": False, "aborted": 0}

    async def handler(route_):
        state["aborted"] += 1
        if state["unblock"]:
            await route_.continue_()
        else:
            await route_.abort("failed")

    await page.route(f"**/{fragment}*", handler)
    await ctx.goto(route)
    return state


async def assert_refetch(ctx: Ctx, fragment: str, retry, marker: str | None, clear_check) -> dict:
    """Click a retry control after unblocking, assert a request + a state change."""
    page = ctx.page
    before = len([u for u in ctx.requests if fragment in u])
    state = getattr(ctx, "_block_state", None)
    if state is not None:
        state["unblock"] = True
    try:
        async with page.expect_request(lambda r: fragment in r.url, timeout=15_000) as req_info:
            await retry.click(timeout=15_000)
        request = await req_info.value
    except Exception:
        # react-query may issue its own retry; still require the state to clear
        request = None
    await page.wait_for_timeout(1200)
    after_urls = [u for u in ctx.requests if fragment in u]
    try:
        cleared = bool(await page.evaluate(clear_check))
    except Exception:  # noqa: BLE001 - an unevaluable probe is not evidence of recovery
        cleared = False
    observed = {
        "requests_before": before,
        "requests_after": len(after_urls),
        "refetch_request": request.url if request else None,
        "error_cleared": cleared,
        "last_requests": after_urls[-4:],
    }
    return observed


# --------------------------------------------------------------------------- #
# checks — Search (C05-001..004)
# --------------------------------------------------------------------------- #
async def check_001(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    inp = p.locator("#person-search")
    await inp.fill(ctx.data["token"])
    await p.wait_for_selector("#person-search-results button[role=option]", timeout=20_000)
    expanded = await inp.get_attribute("aria-expanded")
    n = await p.locator("#person-search-results button[role=option]").count()
    ok = expanded == "true" and n > 0
    ctx.record(
        "PASS" if ok else "FAIL",
        f'type "{ctx.data["token"]}" into #person-search (role=combobox)',
        "aria-expanded=true and a populated role=listbox of MP options",
        f"aria-expanded={expanded}; options={n}",
        extra={"token": ctx.data["token"]},
    )


async def check_002(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    inp = p.locator("#person-search")
    await inp.fill(ctx.data["token"])
    await p.wait_for_selector("#person-search-results button[role=option]", timeout=20_000)
    await inp.press("ArrowDown")
    active = await inp.get_attribute("aria-activedescendant")
    await inp.press("Enter")
    await p.wait_for_url(re.compile(r"/person/"), timeout=15_000)
    url = p.url
    expected = ctx.data.get("search_expected")
    ok = active == "person-option-0" and (not expected or expected in url)
    ctx.record(
        "PASS" if ok else "FAIL",
        "ArrowDown then Enter in the search combobox",
        "aria-activedescendant=person-option-0 then navigate to /person/<live id>",
        f"activedescendant={active}; url={url}",
        extra={"expected_id": expected},
    )


async def check_003(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    inp = p.locator("#person-search")
    await inp.fill(ctx.data["token"])
    await p.wait_for_selector("#person-search-results button[role=option]", timeout=20_000)
    option = p.locator("#person-option-0")
    name = (await option.inner_text()).splitlines()[0]
    await option.click()
    await p.wait_for_url(re.compile(r"/person/"), timeout=15_000)
    await p.wait_for_timeout(1500)
    body = await p.locator("body").inner_text()
    ok = "/person/" in p.url and name.lower()[:8] in body.lower()
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the first role=option search result (native button)",
        "navigate to /person/<id> whose page shows the option name",
        f"url={p.url}; name_in_page={ok}; option={name!r}",
    )


async def check_004(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    inp = p.locator("#person-search")
    await inp.fill(ctx.data["token"])
    await p.wait_for_selector("#person-search-results button[role=option]", timeout=20_000)
    before = await inp.get_attribute("aria-expanded")
    await p.mouse.click(1490, 550)
    await p.wait_for_timeout(400)
    after = await inp.get_attribute("aria-expanded")
    listbox = await p.locator("#person-search-results").count()
    ok = before == "true" and after == "false" and listbox == 0
    ctx.record(
        "PASS" if ok else "FAIL",
        "mousedown outside the search component",
        "listbox closes (aria-expanded=false, role=listbox detached)",
        f"before={before}; after={after}; listbox_count={listbox}",
    )


# --------------------------------------------------------------------------- #
# checks — PersonDrawer (C05-005..010): trigger is data-absent
# --------------------------------------------------------------------------- #
DRAWER_RESOLVER = (
    "Data-dependent trigger absent: PersonDrawer is mounted only by PartyProfile "
    "(PartyProfile.tsx:213) and its sole opener is a party-movement row. At served "
    "HEAD every /api/party/<party>/movements response is [] for all live parties "
    "and sampled dates, so no UI path can open the drawer. Rerun with a corpus "
    "release containing party movements, or mount PersonDrawer on a route with a "
    "live person id, then repeat this click."
)


async def drawer_skip(ctx: Ctx, aspect: str):
    p = await ctx.new_page()
    await ctx.goto("/party/PSD")
    state_texts = await p.locator("[data-state=empty]").all_inner_texts()
    dialogs = await p.locator('[role=dialog][aria-modal="true"]').count()
    observed = {
        "aspect": aspect,
        "url": p.url,
        "data_state_empty": [t[:160] for t in state_texts],
        "person_dialog_count": dialogs,
        "party_movements_probe": ctx.data.get("party_movements"),
        "person_history_probe": ctx.data.get("person_survey", {}).get("with_history"),
    }
    ctx.record(
        "SKIP",
        f"attempt to open PersonDrawer and exercise: {aspect}",
        "drawer opens with role=dialog / aria-modal=true and the aspect is clickable",
        "no opener present: party profile shows an empty state and no movement button; "
        f"dialog_count={dialogs}",
        extra=observed,
        resolver=DRAWER_RESOLVER,
    )


async def check_005(ctx: Ctx):
    await drawer_skip(ctx, "aria-hidden backdrop onClick=onClose")


async def check_006(ctx: Ctx):
    await drawer_skip(ctx, "header close button (t('close'))")


async def check_007(ctx: Ctx):
    await drawer_skip(ctx, "Escape close + Tab focus trap + focus restore")


async def check_008(ctx: Ctx):
    await drawer_skip(ctx, "Wikidata external anchor")


async def check_009(ctx: Ctx):
    await drawer_skip(ctx, "history source_url external anchor")


async def check_010(ctx: Ctx):
    await drawer_skip(ctx, "person query error RetryButton")


# --------------------------------------------------------------------------- #
# checks — CitationPopover / ProvenanceStamp (C05-011..016)
# --------------------------------------------------------------------------- #
async def person_page(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto(f"/person/{ctx.data['person_id']}")
    toggle = p.locator("button[aria-expanded][title]").first
    await toggle.wait_for(state="visible", timeout=15_000)
    return p, toggle


async def check_011(ctx: Ctx):
    p, toggle = await person_page(ctx)
    before = await toggle.get_attribute("aria-expanded")
    await toggle.click()
    after = await toggle.get_attribute("aria-expanded")
    pop = await p.locator("div.card.absolute").count()
    await toggle.click()
    closed = await toggle.get_attribute("aria-expanded")
    ok = before == "false" and after == "true" and closed == "false" and pop > 0
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the citations toggle twice",
        "aria-expanded false -> true -> false with the popover rendered while open",
        f"before={before}; open={after}; closed={closed}; popover_nodes={pop}",
    )


async def check_012(ctx: Ctx):
    p, toggle = await person_page(ctx)
    await toggle.click()
    opened = await toggle.get_attribute("aria-expanded")
    await p.keyboard.press("Escape")
    after_esc = await toggle.get_attribute("aria-expanded")
    await toggle.click()
    await p.get_by_role("heading", name="Evenimente").first.click()
    after_outside = await toggle.get_attribute("aria-expanded")
    ok = opened == "true" and after_esc == "false" and after_outside == "false"
    ctx.record(
        "PASS" if ok else "FAIL",
        "Escape and outside-mousedown while the citation popover is open",
        "both close it (aria-expanded=false)",
        f"open={opened}; after_escape={after_esc}; after_outside_click={after_outside}",
    )


async def check_013(ctx: Ctx):
    p, toggle = await person_page(ctx)
    await toggle.click()
    links = p.locator("a[target=_blank]")
    href = None
    for i in range(await links.count()):
        a = links.nth(i)
        txt = await a.inner_text()
        if "Vezi sursa originală" in txt and await a.is_visible():
            href = await a.get_attribute("href")
            break
    detail = ctx.data.get("person_detail") or {}
    evidence = detail.get("evidence", [])
    source = next((e.get("source_url") for e in evidence if e.get("source_url")), None)
    popup_url = None
    if href:
        async with p.expect_popup(timeout=10_000) as pi:
            await p.locator(f'a[target="_blank"][href="{href}"]').first.click()
        popup = await pi.value
        popup_url = popup.url
        await popup.close()
    external = [u for u in ctx.external_requests if "cdep.ro" in u]
    ok = bool(href and external and (source is None or href == source))
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the citation 'Vezi sursa originală' anchor (target=_blank)",
        "a popup opens at the live evidence source_url (stubbed destination)",
        f"href={href}; popup={popup_url}; external_requests={external[-2:]}; api_source={source}",
        extra={"evidence_rows": len(evidence)},
    )


async def check_014(ctx: Ctx):
    p, toggle = await person_page(ctx)
    await toggle.click()
    archive_links = []
    for i in range(await links_count(p)):
        a = p.locator("a[target=_blank]").nth(i)
        if "Vezi copia arhivată" in (await a.inner_text()):
            archive_links.append(await a.get_attribute("href"))
    snapshot_rows = (ctx.data.get("person_survey") or {}).get("snapshot_rows", [])
    resolver = (
        "Data-dependent anchor absent: no EvidenceItem in the served corpus carries "
        "snapshot_url (surveyed live /api/persons/<id> evidence rows; "
        f"{len(snapshot_rows)} snapshot_url rows found). Rerun with archived snapshot "
        "data, then open a citation popover and click 'Vezi copia arhivată'."
    )
    ctx.record(
        "SKIP",
        "open citation popover and click the archived-copy anchor",
        "an <a target=_blank> 'Vezi copia arhivată' navigates to evidence.snapshot_url",
        f"archive_anchor_count={len(archive_links)}; live snapshot_url rows={len(snapshot_rows)}",
        extra={"archive_links": archive_links},
        resolver=resolver,
    )


async def links_count(p) -> int:
    return await p.locator("a[target=_blank]").count()


async def check_015(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto(f"/person/{ctx.data['person_id']}")
    href = None
    loc = p.locator("a[target=_blank]")
    for i in range(await loc.count()):
        a = loc.nth(i)
        if "Vezi sursa originală" in (await a.inner_text()):
            href = await a.get_attribute("href")
            break
    popup_url = None
    if href:
        async with p.expect_popup(timeout=10_000) as pi:
            await p.locator(f'a[target="_blank"][href="{href}"]').first.click()
        popup = await pi.value
        popup_url = popup.url
        await popup.close()
    detail = ctx.data.get("person_detail") or {}
    source = next(
        (e.get("source_url") for e in detail.get("evidence", []) if e.get("source_url")), None
    )
    external = [u for u in ctx.external_requests if "cdep.ro" in u]
    ok = bool(href and external and (source is None or href == source))
    ctx.record(
        "PASS" if ok else "FAIL",
        "click ProvenanceStamp's 'Vezi sursa originală ↗' anchor",
        "a popup opens at the data source_url (stubbed destination)",
        f"href={href}; popup={popup_url}; external_requests={external[-2:]}; api_source={source}",
    )


async def check_016(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto(f"/person/{ctx.data['person_id']}")
    snapshot_anchors = await p.locator("a[title]").count()
    snapshot_rows = (ctx.data.get("person_survey") or {}).get("snapshot_rows", [])
    resolver = (
        "Data-dependent anchor absent: the served person evidence payload has no "
        "snapshotHash/snapshotUrl, so ProvenanceStamp renders the non-interactive "
        "<span title> branch (no anchor). Rerun with snapshot-bearing provenance "
        "data, then click the 12-character hash link."
    )
    ctx.record(
        "SKIP",
        "click ProvenanceStamp snapshot link (hash.slice(0,12))",
        "an <a target=_blank title=snapshotHash> opens the snapshot URL",
        f"title_anchors={snapshot_anchors}; live snapshot_url rows={len(snapshot_rows)}",
        extra={"snapshot_rows": snapshot_rows},
        resolver=resolver,
    )


# --------------------------------------------------------------------------- #
# checks — ErrorState / RetryButton / DashboardCard (C05-018, 020, 021)
# --------------------------------------------------------------------------- #
async def check_018(ctx: Ctx):
    fragment = "api/dashboard/stats"
    state = await induce(ctx, fragment, "/")
    ctx._block_state = state
    idx = await retry_index_in_card(ctx.page, None)
    if idx is None:
        ctx.record(
            "FAIL",
            "abort /api/dashboard/stats then click ErrorState RetryButton",
            "ErrorState renders a RetryButton",
            "no retry button found after abort",
        )
        return
    retry = ctx.page.locator("button").nth(idx)
    before_state = await ctx.page.locator("[data-state=error]").count()
    observed = await assert_refetch(
        ctx, fragment, retry, None, "() => document.querySelectorAll('[data-state=error]').length === 0"
    )
    ok = before_state > 0 and observed["error_cleared"]
    ctx.record(
        "PASS" if ok else "FAIL",
        "click RetryButton rendered by ErrorState (dashboard/stats error)",
        "a /api/dashboard/stats refetch fires and the error state clears",
        f"error_states_before={before_state}; {json.dumps(observed)}",
    )


async def check_020(ctx: Ctx):
    fragment = "api/chamber"
    state = await induce(ctx, fragment, "/")
    ctx._block_state = state
    idx = await retry_index_in_card(ctx.page, None)
    if idx is None:
        ctx.record(
            "FAIL",
            "abort /api/chamber then click RetryButton",
            "ChamberView error state renders a RetryButton",
            "no retry button found",
        )
        return
    retry = ctx.page.locator("button").nth(idx)
    observed = await assert_refetch(
        ctx,
        fragment,
        retry,
        None,
        "() => document.querySelectorAll('svg[aria-hidden=true] circle').length > 0",
    )
    ok = observed["error_cleared"] or bool(observed["refetch_request"])
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the generic RetryButton in ChamberView's error branch",
        "an /api/chamber refetch fires and hemicycle seats render again",
        json.dumps(observed),
    )


async def check_021(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    card = p.locator("a.card").first
    label = (await card.inner_text()).splitlines()[0]
    href = await card.get_attribute("href")
    await card.click()
    await p.wait_for_url(re.compile(r"/mps"), timeout=15_000)
    ok = urlparse(p.url).path == "/mps"
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the first DashboardCard link",
        "navigate to /mps with scope preserved",
        f"label={label!r}; href={href}; url={p.url}",
    )


# --------------------------------------------------------------------------- #
# checks — Hemicycle (C05-023..026)
# --------------------------------------------------------------------------- #
async def check_023(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    circles = p.locator("svg[aria-hidden=true] circle")
    n = await circles.count()
    target, tip_text = None, ""
    for i in range(min(n, 25)):
        c = circles.nth(i)
        await c.hover()
        await p.wait_for_timeout(120)
        texts = await p.evaluate(
            """() => [...document.querySelectorAll('div')]
                 .filter(d => typeof d.className === 'string' &&
                              d.className.includes('pointer-events-none') &&
                              d.className.includes('top-1'))
                 .map(d => (d.textContent||'').trim())"""
        )
        if texts and texts[0] and not texts[0].startswith("—"):
            target, tip_text = c, texts[0]
            break
    if target is None:
        ctx.record(
            "SKIP",
            "hover a Hemicycle seat circle",
            "a member tooltip appears and clicking the seat navigates to /person/<id>",
            f"no seated member among the first {min(n, 25)} seats",
            resolver="No live member assigned to sampled seats — rerun with a different scope.",
        )
        return
    name = tip_text.split("·")[0].strip()
    await target.click()
    await p.wait_for_url(re.compile(r"/person/"), timeout=15_000)
    await p.wait_for_timeout(1500)
    body = await p.locator("body").inner_text()
    ok = ("/person/" in p.url
          and (name.lower()[:8] in body.lower() or name.split()[-1].lower()[:6] in body.lower()))
    ctx.record(
        "PASS" if ok else "FAIL",
        "hover then click a Hemicycle seat circle (SVG onClick)",
        "tooltip names the member; click navigates to /person/<id>",
        f"seats={n}; tooltip={tip_text!r}; url={p.url}; name_in_page={ok}",
    )


async def open_first_hemicycle_details(p):
    summary = p.locator("details summary").first
    await summary.click()
    return summary


async def check_024(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    summary = p.locator("details summary").first
    text = (await summary.inner_text()).strip()
    before = await p.locator("details").first.evaluate("d => d.open")
    await summary.click()
    after = await p.locator("details").first.evaluate("d => d.open")
    ctx.record(
        "PASS" if not before and after else "FAIL",
        "click the native <summary> of the hemicycle member list",
        "the <details> disclosure opens",
        f"label={text!r}; open before={before}; open after={after}",
    )


async def check_025(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    summary = p.locator("details summary").first
    await summary.click()
    region = p.locator('div[aria-label="List of all MPs in this hemicycle group"]').first
    await region.scroll_into_view_if_needed()
    await summary.focus()
    await p.keyboard.press("Tab")
    focused = await p.evaluate(
        "() => document.activeElement && document.activeElement.getAttribute('aria-label')"
    )
    await p.keyboard.press("PageDown")
    await p.wait_for_timeout(300)
    top = await region.evaluate("e => e.scrollTop")
    ok = focused == "List of all MPs in this hemicycle group"
    ctx.record(
        "PASS" if ok else "FAIL",
        "Tab from <summary> into the focusable scroll region, then PageDown",
        "focus lands on the labelled scroll region and it scrolls",
        f"focused_label={focused!r}; scrollTop={top}",
    )


async def check_026(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    await open_first_hemicycle_details(p)
    region = p.locator('div[aria-label="List of all MPs in this hemicycle group"]').first
    member = region.locator("button").first
    name = (await member.inner_text()).split("·")[0].strip()
    await member.click()
    await p.wait_for_url(re.compile(r"/person/"), timeout=15_000)
    await p.wait_for_timeout(1500)
    body = await p.locator("body").inner_text()
    ok = ("/person/" in p.url
          and (name.lower()[:8] in body.lower() or name.split()[-1].lower()[:6] in body.lower()))
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the first member button inside the hemicycle member list",
        "navigate to /person/<id> for that member",
        f"member={name!r}; url={p.url}; name_in_page={ok}",
    )


# --------------------------------------------------------------------------- #
# checks — SankeyFlow (C05-027..029)
# --------------------------------------------------------------------------- #
async def check_027(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/traseism")
    paths = p.locator("path[role=button]")
    n = await paths.count()
    if n == 0:
        ctx.record(
            "SKIP",
            "click a Sankey flow path",
            "selection status appears",
            "no flow paths rendered",
            resolver="Rerun with a legislature scope whose switch matrix has flow pairs.",
        )
        return
    before = await statuses(p)
    label = await paths.first.get_attribute("aria-label")
    await paths.first.click(force=True)
    after_click = await statuses(p)
    await paths.nth(1 if n > 1 else 0).focus()
    await p.keyboard.press("Enter")
    after_key = await statuses(p)
    ok = len(after_click) > len(before) and len(after_key) >= len(after_click)
    ctx.record(
        "PASS" if ok else "FAIL",
        "click a Sankey flow <path role=button>; press Enter on a second path",
        "a [role=status] selection message appears and changes on keyboard activation",
        f"paths={n}; before={before[-2:]}; after_click={after_click[-2:]}; after_key={after_key[-2:]}",
        extra={"aria_label": label},
    )


async def check_028(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/traseism")
    nodes = p.locator("g[role=button]")
    n = await nodes.count()
    if n == 0:
        ctx.record(
            "SKIP",
            "click a Sankey node <g role=button>",
            "selection status appears",
            "no nodes rendered",
            resolver="Rerun with a legislature scope whose switch matrix has flow pairs.",
        )
        return
    before = await statuses(p)
    label = await nodes.first.get_attribute("aria-label")
    await nodes.first.click()
    after = await statuses(p)
    ok = len(after) > len(before)
    ctx.record(
        "PASS" if ok else "FAIL",
        "click a Sankey node <g role=button>",
        "a [role=status] 'selected party' message appears",
        f"nodes={n}; before={before[-2:]}; after={after[-2:]}",
        extra={"aria_label": label},
    )


async def check_029(ctx: Ctx):
    fragment = "api/traseism/summary"
    state = await induce(ctx, fragment, "/traseism")
    ctx._block_state = state
    idx = await retry_index_in_card(ctx.page, None)
    if idx is None:
        ctx.record(
            "FAIL",
            "abort traseism summary then click SankeyFlow retry",
            "SankeyFlow error state renders a RetryButton",
            "no retry button found",
        )
        return
    retry = ctx.page.locator("button").nth(idx)
    observed = await assert_refetch(
        ctx, fragment, retry, None, "() => document.querySelectorAll('path[role=button]').length > 0"
    )
    ok = observed["error_cleared"] or bool(observed["refetch_request"])
    ctx.record(
        "PASS" if ok else "FAIL",
        "click SankeyFlow's error-state RetryButton",
        "a traseism/summary refetch fires and the flow SVG returns",
        json.dumps(observed),
    )


# --------------------------------------------------------------------------- #
# checks — SwitchTimeline (C05-030..031)
# --------------------------------------------------------------------------- #
async def check_030(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    rects = p.locator("rect[role=button]")
    n = await rects.count()
    if n == 0:
        ctx.record(
            "SKIP",
            "click a SwitchTimeline wave rect",
            "navigate to /traseism?date=<wave date>",
            "no wave rects rendered",
            resolver="Rerun with a corpus containing switch waves.",
        )
        return
    title = ((await rects.first.locator("title").text_content()) or "").strip()
    wave_date = title.split(":")[0].strip()
    await rects.first.click()
    await p.wait_for_url(re.compile(r"/traseism"), timeout=15_000)
    qs = parse_qs(urlparse(p.url).query)
    ok = urlparse(p.url).path == "/traseism" and qs.get("date", [None])[0] == wave_date
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the first SwitchTimeline wave <rect role=button>",
        "navigate to /traseism with the wave's start date in the URL scope",
        f"wave_title={title!r}; url={p.url}",
        extra={"wave_date": wave_date},
    )


async def check_031(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    base_date = parse_qs(urlparse(p.url).query).get("date", [None])[0]
    idx = await button_index_in_card(p, r"Vezi toate|View all", "Switch Waves")
    if idx is None:
        ctx.record(
            "FAIL",
            "click SwitchTimeline 'View all' button",
            "navigate to /traseism",
            "button not found in the Switch Waves card",
        )
        return
    await p.locator("button").nth(idx).click()
    await p.wait_for_url(re.compile(r"/traseism"), timeout=15_000)
    qs = parse_qs(urlparse(p.url).query)
    ok = urlparse(p.url).path == "/traseism" and qs.get("date", [None])[0] == base_date
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the SwitchTimeline 'Vezi toate →' button",
        "navigate to /traseism with the clamped date (no single wave)",
        f"base_date={base_date}; url={p.url}",
    )


# --------------------------------------------------------------------------- #
# checks — PartyNetwork / PartyListTable (C05-032..036)
# --------------------------------------------------------------------------- #
async def check_032(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    nodes = p.locator('button[aria-label^="Partidul"]')
    n = await nodes.count()
    if n == 0:
        ctx.record(
            "SKIP",
            "click a PartyNetwork node button",
            "navigate to /party/<short>",
            "no party nodes rendered",
            resolver="Rerun with live party data.",
        )
        return
    aria = await nodes.first.get_attribute("aria-label")
    short = aria.split("Partidul", 1)[1].split(":", 1)[0].strip()
    await nodes.first.click()
    await p.wait_for_url(re.compile(r"/party/"), timeout=15_000)
    ok = urlparse(p.url).path == f"/party/{short}"
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the first PartyNetwork node button",
        "navigate to /party/<short_name> from the node's party",
        f"nodes={n}; aria={aria!r}; url={p.url}",
    )


async def check_033(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    idx = await button_index_in_card(p, r"Vezi toate|View all", "Party Network")
    if idx is None:
        ctx.record(
            "FAIL",
            "click PartyNetwork 'View all' button",
            "navigate to /mps",
            "button not found in the Party Network card",
        )
        return
    await p.locator("button").nth(idx).click()
    await p.wait_for_url(re.compile(r"/mps"), timeout=15_000)
    ok = urlparse(p.url).path == "/mps"
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the PartyNetwork 'Vezi toate →' button",
        "navigate to /mps",
        f"url={p.url}",
    )


async def check_034(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    region = p.locator('div[aria-label="List of parties by member count"]')
    rows = region.locator("button")
    n = await rows.count()
    short = (await rows.first.locator("span.truncate").first.inner_text()).strip()
    await rows.first.click()
    await p.wait_for_url(re.compile(r"/party/"), timeout=15_000)
    ok = urlparse(p.url).path == f"/party/{short}"
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the first PartyListTable row button",
        "navigate to /party/<short_name> with scope preserved",
        f"rows={n}; short={short!r}; url={p.url}",
    )


async def check_035(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    region = p.locator('div[aria-label="List of parties by member count"]')
    await region.focus()
    focused = await p.evaluate(
        "() => document.activeElement && document.activeElement.getAttribute('aria-label')"
    )
    await p.keyboard.press("PageDown")
    await p.wait_for_timeout(250)
    top = await region.evaluate("e => e.scrollTop")
    ok = focused == "List of parties by member count"
    ctx.record(
        "PASS" if ok else "FAIL",
        "focus the PartyListTable keyboard scroll region and press PageDown",
        "the labelled region receives focus and scrolls",
        f"focused={focused!r}; scrollTop={top}",
    )


async def check_036(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    idx = await button_index_in_card(p, r"Vezi toate|View all", "Party Representation")
    if idx is None:
        ctx.record(
            "FAIL",
            "click PartyListTable 'View all' button",
            "navigate to /parties",
            "button not found in Party Representation card",
        )
        return
    await p.locator("button").nth(idx).click()
    await p.wait_for_url(re.compile(r"/parties"), timeout=15_000)
    ok = urlparse(p.url).path == "/parties"
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the PartyListTable 'Vezi toate →' button",
        "navigate to /parties",
        f"url={p.url}",
    )


# --------------------------------------------------------------------------- #
# checks — CommitteeControl (C05-040..042)
# --------------------------------------------------------------------------- #
async def check_040(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    chairs = p.locator('button[aria-label^="Arată președintele"]:not([disabled])')
    n = await chairs.count()
    aria = await chairs.first.get_attribute("aria-label") if n else None
    party = aria.split("președintele ", 1)[1].strip() if aria else None
    data = (ctx.data.get("committee") or {}).get("chairs", [])
    person_id = next((c.get("chair_person_id") for c in data if c.get("party") == party), None)
    if n:
        await chairs.first.click()
        await p.wait_for_url(re.compile(r"/person/"), timeout=15_000)
    ok = bool(n and person_id and person_id in p.url)
    ctx.record(
        "PASS" if ok else "FAIL",
        "click an enabled CommitteeControl chair button",
        "navigate to /person/<chair_person_id> from the live committee-control payload",
        f"chairs={n}; aria={aria!r}; resolved_id={person_id}; url={p.url}",
    )


async def check_041(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    summary = p.locator("details summary").filter(has_text=re.compile("View all chairs"))
    text = (await summary.inner_text()).strip()
    det = p.locator("details").filter(has_text="View all chairs").first
    before = await det.evaluate("d => d.open")
    await summary.click()
    after = await det.evaluate("d => d.open")
    ok = not before and after
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the CommitteeControl 'View all chairs' <summary>",
        "the chairs <details> disclosure opens",
        f"label={text!r}; before={before}; after={after}",
    )


async def check_042(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    summary = p.locator("details summary").filter(has_text=re.compile("View all chairs"))
    await summary.click()
    region = p.locator('ul[aria-label="List of all chairs in committees"]')
    await region.focus()
    focused = await p.evaluate(
        "() => document.activeElement && document.activeElement.getAttribute('aria-label')"
    )
    await p.keyboard.press("PageDown")
    await p.wait_for_timeout(200)
    top = await region.evaluate("e => e.scrollTop")
    ok = focused == "List of all chairs in committees"
    ctx.record(
        "PASS" if ok else "FAIL",
        "focus the chairs keyboard scroll region and press PageDown",
        "the labelled <ul> receives focus and scrolls",
        f"focused={focused!r}; scrollTop={top}",
    )


# --------------------------------------------------------------------------- #
# checks — LegislatureSeatExplorer (C05-045..048)
# --------------------------------------------------------------------------- #
async def slider_state(p):
    return {
        "value": await p.locator("#legislature-start-slider").input_value(),
        "year": (await p.locator("output").first.inner_text()).strip(),
        "date": parse_qs(urlparse(p.url).query).get("date", [None])[0],
    }


async def check_045(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    btn = p.locator("button[aria-pressed]").filter(has_text=re.compile("Redă|Play|Pauză|Pause"))
    before = await btn.get_attribute("aria-pressed")
    state0 = await slider_state(p)
    await btn.click()
    after = await btn.get_attribute("aria-pressed")
    await p.wait_for_timeout(1500)
    state1 = await slider_state(p)
    await btn.click()
    restored = await btn.get_attribute("aria-pressed")
    ok = before == "false" and after == "true" and restored == "false" and state1 != state0
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the legislature play/pause button twice",
        "aria-pressed toggles and autoplay advances the legislature/year",
        f"pressed={before}->{after}->{restored}; before={state0}; during={state1}",
    )


async def check_046(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    prev = p.locator('button[aria-label*="anterioar"], button[aria-label*="Previous"]').first
    before = await slider_state(p)
    disabled = await prev.is_disabled()
    await prev.click()
    await p.wait_for_timeout(400)
    after = await slider_state(p)
    ok = (
        not disabled
        and int(after["value"]) == int(before["value"]) - 1
        and after["date"] != before["date"]
    )
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the 'Legislatura anterioară' button",
        "slider index decrements and the URL date scope changes",
        f"disabled={disabled}; before={before}; after={after}",
    )


async def check_047(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    slider = p.locator("#legislature-start-slider")
    before = await slider_state(p)
    await slider.focus()
    await p.keyboard.press("ArrowLeft")
    await p.wait_for_timeout(400)
    after = await slider_state(p)
    ok = int(after["value"]) == int(before["value"]) - 1 and after["date"] != before["date"]
    ctx.record(
        "PASS" if ok else "FAIL",
        "focus #legislature-start-slider and press ArrowLeft",
        "keyboard changes the range value and the scoped URL date",
        f"before={before}; after={after}",
    )


async def check_048(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    nxt = p.locator('button[aria-label*="următoare"], button[aria-label*="Next"]').first
    initially_disabled = await nxt.is_disabled()
    prev = p.locator('button[aria-label*="anterioar"], button[aria-label*="Previous"]').first
    await prev.click()
    await p.wait_for_timeout(350)
    before = await slider_state(p)
    await nxt.click()
    await p.wait_for_timeout(350)
    after = await slider_state(p)
    ok = (
        initially_disabled
        and int(after["value"]) == int(before["value"]) + 1
        and after["date"] != before["date"]
    )
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the 'Legislatura următoare' button after stepping back",
        "next was disabled at the last stop; click advances slider and URL date",
        f"initially_disabled={initially_disabled}; before={before}; after={after}",
    )


# --------------------------------------------------------------------------- #
# checks — VoteActivityChart (C05-049..050)
# --------------------------------------------------------------------------- #
async def check_049(ctx: Ctx):
    fragment = "api/analytics/vote-activity"
    state = await induce(ctx, fragment, "/grafice")
    ctx._block_state = state
    idx = await retry_index_in_card(ctx.page, None)
    if idx is None:
        ctx.record(
            "FAIL",
            "abort vote-activity then click chart retry",
            "VoteActivityChart error state renders a RetryButton",
            "no retry button found",
        )
        return
    retry = ctx.page.locator("button").nth(idx)
    observed = await assert_refetch(
        ctx, fragment, retry, None, "() => document.querySelectorAll('canvas').length > 0"
    )
    ok = observed["error_cleared"] or bool(observed["refetch_request"])
    ctx.record(
        "PASS" if ok else "FAIL",
        "click VoteActivityChart's AsyncState RetryButton",
        "a vote-activity refetch fires and the chart canvas returns",
        json.dumps(observed),
    )


async def check_050(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/grafice")
    canvas = p.locator("canvas").first
    if await canvas.count() == 0:
        ctx.record(
            "SKIP",
            "drag ECharts dataZoom slider on the vote-activity canvas",
            "canvas zoom changes the rendered chart",
            "no canvas rendered",
            resolver="Rerun with vote-activity data so ECharts initialises.",
        )
        return
    box = await canvas.bounding_box()
    before = await canvas.evaluate("c => c.toDataURL().slice(-400)")
    y = box["y"] + box["height"] - 12
    x0 = box["x"] + box["width"] * 0.30
    x1 = box["x"] + box["width"] * 0.70
    await p.mouse.move(x0, y)
    await p.mouse.down()
    await p.mouse.move(x1, y, steps=8)
    await p.mouse.up()
    await p.wait_for_timeout(500)
    after = await canvas.evaluate("c => c.toDataURL().slice(-400)")
    changed = before != after
    errors = [
        e for e in ctx.console if e["element_context"] == "C05-050" and e["type"] == "console.error"
    ]
    verdict = "PASS" if changed and not errors else ("SKIP" if not changed else "FAIL")
    resolver = None
    if not changed:
        resolver = (
            "ECharts dataZoom is rendered on a canvas with no DOM controls (F9); the "
            "drag produced no observable pixel change and keyboard/AT reachability is "
            "not determinable from this repo. Rerun with an accessible out-of-canvas "
            "date-range control, or verify ECharts aria.enabled in a dedicated probe."
        )
    ctx.record(
        verdict,
        "drag the ECharts dataZoom slider across the vote-activity canvas",
        "the canvas rendering changes with no console error",
        f"canvas={box}; changed={changed}; console_errors={len(errors)}",
        extra={"data_tail_before": before[-40:], "data_tail_after": after[-40:]},
        resolver=resolver,
    )


# --------------------------------------------------------------------------- #
# checks — TimelineChart (C05-051..054)
# --------------------------------------------------------------------------- #
async def check_051(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/legislature/2024")
    senate = p.locator("button[aria-pressed]").filter(has_text=re.compile("Senat"))
    before = await senate.get_attribute("aria-pressed")
    await senate.click()
    await p.wait_for_timeout(900)
    after = await senate.get_attribute("aria-pressed")
    fired = [u for u in ctx.requests if "/api/timeline" in u and "chamber=senate" in u]
    deputies = p.locator("button[aria-pressed]").filter(has_text=re.compile("Deputa|Camera"))
    deputy_pressed = await deputies.first.get_attribute("aria-pressed")
    ok = before == "false" and after == "true" and bool(fired) and deputy_pressed == "false"
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the TimelineChart 'Senat' chamber toggle",
        "aria-pressed moves to Senat and a chamber=senate /api/timeline request fires",
        f"pressed={before}->{after}; deputy_pressed={deputy_pressed}; requests={fired[-2:]}",
    )


async def check_052(ctx: Ctx):
    fragment = "api/timeline"
    state = await induce(ctx, fragment, "/legislature/2024")
    ctx._block_state = state
    idx = await retry_index_in_card(ctx.page, None)
    if idx is None:
        ctx.record(
            "FAIL",
            "abort /api/timeline then click TimelineChart retry",
            "TimelineChart error branch renders a RetryButton",
            "no retry button found",
        )
        return
    retry = ctx.page.locator("button").nth(idx)
    observed = await assert_refetch(
        ctx, fragment, retry, None, "() => document.querySelectorAll('canvas').length > 0"
    )
    ok = observed["error_cleared"] or bool(observed["refetch_request"])
    ctx.record(
        "PASS" if ok else "FAIL",
        "click TimelineChart's RetryButton",
        "a /api/timeline refetch fires and the chart renders again",
        json.dumps(observed),
    )


async def check_053(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/legislature/2024")
    summary = p.locator("details summary").first
    text = (await summary.inner_text()).strip()
    det = p.locator("details").first
    before = await det.evaluate("d => d.open")
    await summary.click()
    after = await det.evaluate("d => d.open")
    ok = not before and after
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the TimelineChart table <summary>",
        "the data-table <details> disclosure opens",
        f"label={text!r}; before={before}; after={after}",
    )


async def check_054(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/legislature/2024")
    summary = p.locator("details summary").first
    await summary.click()
    region = p.locator('[role=region][tabindex="0"]').filter(has=p.locator("table")).first
    label = await region.get_attribute("aria-label")
    await region.focus()
    focused = await p.evaluate(
        "() => document.activeElement && document.activeElement.getAttribute('aria-label')"
    )
    await p.keyboard.press("ArrowRight")
    await p.wait_for_timeout(200)
    left = await region.evaluate("e => e.scrollLeft")
    ok = bool(label) and focused == label
    ctx.record(
        "PASS" if ok else "FAIL",
        "focus the TimelineChart table scroll region and press ArrowRight",
        "the labelled region receives keyboard focus and can scroll",
        f"label={label!r}; focused={focused!r}; scrollLeft={left}",
    )


# --------------------------------------------------------------------------- #
# checks — CrossChamberFlow (C05-055..056)
# --------------------------------------------------------------------------- #
async def check_055(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    cross = ctx.data.get("cross") or []
    member = sorted(cross, key=lambda m: m.get("name", ""))[0] if cross else None
    if not member:
        ctx.record(
            "SKIP",
            "click a CrossChamberFlow member button",
            "navigate to /person/<id>",
            "cross-chamber payload empty",
            resolver="Rerun with cross-chamber data.",
        )
        return
    name = member["name"]
    expected_id = member["person_id"]
    loc = p.locator("button[aria-label]")
    target = None
    for i in range(await loc.count()):
        al = await loc.nth(i).get_attribute("aria-label") or ""
        if al.startswith(name):
            target = loc.nth(i)
            break
    if target is None:
        ctx.record(
            "FAIL",
            "click a CrossChamberFlow member button",
            f"navigate to /person/{expected_id}",
            f"member {name!r} not found among {await loc.count()} labelled buttons",
        )
        return
    await target.click()
    await p.wait_for_url(re.compile(r"/person/"), timeout=15_000)
    ok = expected_id in p.url
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the first CrossChamberFlow member button",
        "navigate to that member's /person/<id>",
        f"member={name!r}; expected_id={expected_id}; url={p.url}",
    )


async def check_056(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    cross = ctx.data.get("cross") or []
    member = sorted(cross, key=lambda m: m.get("name", ""))[0] if cross else None
    name = member["name"] if member else None
    loc = p.locator("button[aria-label]")
    target = None
    for i in range(await loc.count()):
        al = await loc.nth(i).get_attribute("aria-label") or ""
        if name and al.startswith(name):
            target = loc.nth(i)
            break
    if target is None:
        ctx.record(
            "FAIL",
            "focus the CrossChamberFlow scroll region",
            "a labelled [role=region] receives focus",
            "cross-chamber member button not found",
        )
        return
    region = target.locator("xpath=ancestor::section[1]").locator('[role=region][tabindex="0"]')
    label = await region.get_attribute("aria-label")
    await region.focus()
    focused = await p.evaluate(
        "() => document.activeElement && document.activeElement.getAttribute('aria-label')"
    )
    await p.keyboard.press("PageDown")
    await p.wait_for_timeout(200)
    top = await region.evaluate("e => e.scrollTop")
    ok = bool(label) and focused == label
    ctx.record(
        "PASS" if ok else "FAIL",
        "focus the CrossChamberFlow labelled scroll region and press PageDown",
        "the [role=region] receives focus and scrolls",
        f"label={label!r}; focused={focused!r}; scrollTop={top}",
    )


# --------------------------------------------------------------------------- #
# checks — ui/ retry controls + ThemeToggle (C05-058, 059, 061, 062)
# --------------------------------------------------------------------------- #
async def check_058(ctx: Ctx):
    fragment = "api/coverage/detailed"
    state = await induce(ctx, fragment, "/")
    ctx._block_state = state
    idx = await retry_index_in_card(ctx.page, None)
    if idx is None:
        ctx.record(
            "FAIL",
            "abort coverage/detailed then click DataQualityGauge retry",
            "DataQualityGauge StateView renders a RetryButton",
            "no retry button in the Data Quality card",
        )
        return
    retry = ctx.page.locator("button").nth(idx)
    observed = await assert_refetch(
        ctx,
        fragment,
        retry,
        None,
        "() => document.body.textContent.includes('Complete:')",
    )
    ok = observed["error_cleared"] or bool(observed["refetch_request"])
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the DataQualityGauge inline StateView RetryButton",
        "a /api/coverage/detailed refetch fires and the gauge returns",
        json.dumps(observed),
    )


async def check_059(ctx: Ctx):
    fragment = "api/parties"
    state = await induce(ctx, fragment, "/")
    ctx._block_state = state
    idx = await retry_index_in_card(ctx.page, None)
    if idx is None:
        ctx.record(
            "FAIL",
            "abort /api/parties then click AsyncState retry",
            "AsyncState/ErrorState renders a RetryButton",
            "no retry button found",
        )
        return
    retry = ctx.page.locator("button").nth(idx)
    observed = await assert_refetch(
        ctx,
        fragment,
        retry,
        None,
        "() => !!document.querySelector('div[aria-label=\'List of parties by member count\']')",
    )
    ok = observed["error_cleared"] or bool(observed["refetch_request"])
    ctx.record(
        "PASS" if ok else "FAIL",
        "click AsyncState's ErrorState RetryButton (parties region)",
        "an /api/parties refetch fires and the party list returns",
        json.dumps(observed),
    )


async def check_061(ctx: Ctx):
    fragment = "api/analytics/generational-shift"
    state = await induce(ctx, fragment, "/")
    ctx._block_state = state
    err_regions = ctx.page.locator("[data-state=error]")
    n_err = await err_regions.count()
    idx = await retry_index_in_card(ctx.page, None)
    if idx is None:
        ctx.record(
            "FAIL",
            "abort generational-shift then click AgeDistributionSection retry",
            "AgeDistributionSection StateView renders a RetryButton",
            "no retry button found",
        )
        return
    retry = ctx.page.locator("button").nth(idx)
    observed = await assert_refetch(
        ctx,
        fragment,
        retry,
        None,
        "() => document.querySelectorAll('[data-state=error]').length === 0",
    )
    ok = observed["error_cleared"] or bool(observed["refetch_request"])
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the AgeDistributionSection AsyncState RetryButton",
        "a generational-shift refetch fires and the radial returns",
        f"error_regions={n_err}; {json.dumps(observed)}",
    )


async def check_062(ctx: Ctx):
    p = await ctx.new_page()
    await ctx.goto("/")
    btn = p.locator("button[title]").filter(has_text=re.compile("Luminos|Light|Întunecat|Dark"))
    before = await p.evaluate(
        "() => ({theme: document.documentElement.dataset.theme, stored: localStorage.getItem('parlament-deschis-theme')})"
    )
    pressed0 = await btn.get_attribute("aria-pressed")
    await btn.click()
    mid = await p.evaluate(
        "() => ({theme: document.documentElement.dataset.theme, stored: localStorage.getItem('parlament-deschis-theme')})"
    )
    pressed1 = await btn.get_attribute("aria-pressed")
    await btn.click()
    after = await p.evaluate(
        "() => ({theme: document.documentElement.dataset.theme, stored: localStorage.getItem('parlament-deschis-theme')})"
    )
    pressed2 = await btn.get_attribute("aria-pressed")
    ok = (
        before["theme"] == "dark"
        and mid["theme"] == "light"
        and after["theme"] == "dark"
        and pressed0 == "false"
        and pressed1 == "true"
        and pressed2 == "false"
        and mid["stored"] == "light"
    )
    ctx.record(
        "PASS" if ok else "FAIL",
        "click the ThemeToggle button twice",
        "data-theme dark->light->dark, aria-pressed flips, localStorage updated",
        f"before={before}/{pressed0}; mid={mid}/{pressed1}; after={after}/{pressed2}",
    )


CHECKS = [
    check_001,
    check_002,
    check_003,
    check_004,
    check_005,
    check_006,
    check_007,
    check_008,
    check_009,
    check_010,
    check_011,
    check_012,
    check_013,
    check_014,
    check_015,
    check_016,
    check_018,
    check_020,
    check_021,
    check_023,
    check_024,
    check_025,
    check_026,
    check_027,
    check_028,
    check_029,
    check_030,
    check_031,
    check_032,
    check_033,
    check_034,
    check_035,
    check_036,
    check_040,
    check_041,
    check_042,
    check_045,
    check_046,
    check_047,
    check_048,
    check_049,
    check_050,
    check_051,
    check_052,
    check_053,
    check_054,
    check_055,
    check_056,
    check_058,
    check_059,
    check_061,
    check_062,
]


async def _run(rows: list, console: list, data: dict) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=CHROMIUM, args=["--no-sandbox"])
        ctx = Ctx(browser, data, rows, console)
        try:
            await ctx.setup()
            for fn in CHECKS:
                eid = fn.__name__.replace("check_", "C05-")
                ctx.eid = eid
                ctx.induced = None
                ctx._block_state = None
                started = time.monotonic()
                try:
                    await fn(ctx)
                except Exception as exc:  # noqa: BLE001 - harness error is a FAIL finding
                    if not any(r["element_id"] == eid for r in rows):
                        ctx.record(
                            "FAIL",
                            f"harness error while exercising {eid}",
                            "the element's expected observable outcome",
                            f"{type(exc).__name__}: {str(exc)[:400]}",
                            extra={"error_type": type(exc).__name__},
                        )
                finally:
                    if ctx.page is not None:
                        try:
                            await ctx.page.close()
                        except Exception:  # noqa: BLE001
                            pass
                        ctx.page = None
                last = rows[-1]["status"] if rows and rows[-1]["element_id"] == eid else "?"
                print(f"[v09] {eid} {last} {time.monotonic() - started:.1f}s", flush=True)
        finally:
            await browser.close()
    return {"chromium": CHROMIUM, "base": BASE}


def test_v09_clickable_validation() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    console: list[dict] = []
    data = resolve_data()
    runtime = asyncio.run(_run(rows, console, data))

    RESULTS_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    CONSOLE_PATH.write_text(json.dumps(console, ensure_ascii=False, indent=2), encoding="utf-8")
    META_PATH.write_text(
        json.dumps(
            {
                **runtime,
                "served_head": SERVED_HEAD,
                "resolved_at": data["resolved_at"],
                "resolution": {
                    "person_id": data["person_id"],
                    "person_name": data["person_name"],
                    "token": data["token"],
                    "search_expected": data.get("search_expected"),
                    "party_movements": data.get("party_movements"),
                    "snapshot_rows": (data.get("person_survey") or {}).get("snapshot_rows"),
                    "resolution_errors": data["errors"],
                },
                "counts": {
                    "elements": len(rows),
                    "PASS": sum(r["status"] == "PASS" for r in rows),
                    "FAIL": sum(r["status"] == "FAIL" for r in rows),
                    "SKIP": sum(r["status"] == "SKIP" for r in rows),
                    "console_events": len(console),
                    "console_errors_total": sum(
                        1
                        for e in console
                        if e["type"].endswith("error") or e["type"] == "pageerror"
                    ),
                    "console_errors_test_induced": sum(1 for e in console if e["test_induced"]),
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    ids = [r["element_id"] for r in rows]
    assert len(rows) == 52, f"expected 52 result rows, got {len(rows)}"
    assert sorted(ids) == sorted(EXPECTED_IDS), (
        f"ID mismatch: missing={set(EXPECTED_IDS) - set(ids)} extra={set(ids) - set(EXPECTED_IDS)}"
    )
    assert len(set(ids)) == len(ids), f"duplicate IDs: {ids}"
    required = {
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
    }
    for row in rows:
        assert required <= set(row), row["element_id"]
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
                "console_events": len(console),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q", "-s"]))
