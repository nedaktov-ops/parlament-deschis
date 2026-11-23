"""V-02 clickable validation — C02-001..020 on the LiveDashboard route ``/``.

Fleet contract: CLICK-VALIDATION-FLEET-2026-11-23.md §2/§3. This file owns only
itself and the ``/tmp/opencode/click-validation/v02-*`` artifacts. It validates
*behaviour* (URL/scope change, visible state, a fired request, or a designed
no-op) against the read-only local dev server, not the production host.

One chromium instance, one page per element, browser closed in ``finally``.
Data-driven IDs (person, party, chair, wave, member) are resolved from the live
API at runtime; a failed resolution is a SKIP with a named resolver, never a
silent PASS.
"""

from __future__ import annotations

import asyncio
import json
import re
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from datetime import date as date_cls
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright", reason="external Playwright validation tool; see scripts/ui_validate.py")
from playwright.async_api import async_playwright  # noqa: E402

BASE = "http://127.0.0.1:5188"
BROWSER = "/usr/bin/chromium"
OUT_DIR = Path("/tmp/opencode/click-validation")
RESULTS_PATH = OUT_DIR / "v02-results.json"
CONSOLE_PATH = OUT_DIR / "v02-console.json"

RETRY_RE = re.compile(r"Reîncearcă|Retry|Încearcă")
VIEW_ALL_RE = re.compile(r"Vezi toate|View all")
PREV_RE = re.compile(r"Legislatura anterioară|Previous legislature")
NEXT_RE = re.compile(r"Legislatura următoare|Next legislature")

RESOLVERS = {
    "mps": "GET /api/mps?limit=1 -> data[0].id (rerun with a live corpus)",
    "parties": "GET /api/parties -> data[0].short_name (rerun with a live corpus)",
    "meta": "GET /api/meta -> legislatures (rerun with live metadata)",
    "chamber": "GET /api/chamber?chamber=deputies&as_of=<active start> -> groups[0].members[0]",
    "committee": "GET /api/analytics/committee-control?as_of=<date> -> a chair with a non-empty chair_person_id",
    "waves": "GET /api/analytics/switch-waves -> one wave with a start_date",
    "cross": "GET /api/analytics/cross-chamber?as_of=<date> -> data[0]",
    "events": "GET /api/events/recent?limit=40&chamber=senate&legislature=2024 -> first event with person.id",
    "browser": "rerun on the local dev server with /usr/bin/chromium available",
}


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def api_get(path: str) -> Any:
    """One bounded, read-only GET against the local API (no writes, no seeding)."""
    with urllib.request.urlopen(BASE + path, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def url_info(url: str) -> dict[str, Any]:
    parts = urllib.parse.urlsplit(url)
    return {
        "url": url,
        "path": parts.path,
        "params": {k: v for k, v in urllib.parse.parse_qs(parts.query).items()},
    }


def param(info: dict[str, Any], key: str) -> str | None:
    values = info["params"].get(key)
    return values[0] if values else None


def legislature_stops(meta: dict[str, Any]) -> list[dict[str, str]]:
    """Mirror of frontend/src/utils/legislatureStops.ts (pure, sorted by start)."""
    stops = []
    for key, value in (meta.get("legislatures") or {}).items():
        start = value.get("start")
        if isinstance(start, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", start):
            stops.append({"id": str(key), "start": start, "year": start[:4]})
    return sorted(stops, key=lambda s: s["start"])


def stop_index(stops: list[dict[str, str]], day: str) -> int:
    """Mirror of frontend/src/utils/stopIndexForDate.ts."""
    if not stops:
        return -1
    index = 0
    for i, stop in enumerate(stops):
        if stop["start"] > day:
            break
        index = i
    return index


class Outcome:
    __slots__ = ("verdict", "observed", "resolver", "extra")

    def __init__(
        self,
        verdict: str,
        observed: str,
        resolver: str | None = None,
        **extra: Any,
    ) -> None:
        self.verdict = verdict
        self.observed = observed
        self.resolver = resolver
        self.extra = extra


def passed(observed: str, **extra: Any) -> Outcome:
    return Outcome("PASS", observed, **extra)


def failed(observed: str, **extra: Any) -> Outcome:
    return Outcome("FAIL", observed, **extra)


def skipped(observed: str, resolver: str, **extra: Any) -> Outcome:
    return Outcome("SKIP", observed, resolver, **extra)


class Ctx:
    """Per-run state shared by the 20 element cases (no files outside v02-*)."""

    def __init__(self) -> None:
        self.today = date_cls.today().isoformat()
        self.current_id = "C02-000"
        self.console: list[dict[str, Any]] = []
        self._cache: dict[str, Any] = {}
        self._cache_errors: dict[str, str] = {}

    def get(self, path: str) -> tuple[Any | None, str | None]:
        if path in self._cache:
            return self._cache[path], None
        if path in self._cache_errors:
            return None, self._cache_errors[path]
        try:
            self._cache[path] = api_get(path)
            return self._cache[path], None
        except Exception as exc:  # noqa: BLE001 - resolver-driven SKIP, not a pass
            reason = f"GET {path} failed: {type(exc).__name__}: {str(exc)[:200]}"
            self._cache_errors[path] = reason
            return None, reason

    @property
    def stops(self) -> list[dict[str, str]]:
        meta, _ = self.get("/api/meta")
        return legislature_stops(meta or {})

    @property
    def active_start(self) -> str | None:
        stops = self.stops
        index = stop_index(stops, self.today)
        return stops[index]["start"] if 0 <= index < len(stops) else None


async def settle(page: Any, ctx: Ctx, *, block: Callable[[], Any] | None = None) -> None:
    """Navigate to '/' with bounded networkidle + fixed settle (ui_validate.py §2)."""
    if block is not None:
        await block()
    await page.goto(BASE + "/", wait_until="load", timeout=35_000)
    try:
        await page.wait_for_load_state("networkidle", timeout=9_000)
    except Exception:  # noqa: BLE001 - bounded fallback to the fixed settle
        pass
    await page.wait_for_timeout(2_500)
    observed_date = param(url_info(page.url), "date")
    if observed_date:
        ctx.today = observed_date


async def wait_path(page: Any, path: str, timeout: int = 15_000) -> None:
    await page.wait_for_function("(p) => location.pathname === p", arg=path, timeout=timeout)


async def nav_outcome(
    page: Any,
    ctx: Ctx,
    expected_path: str,
    *,
    extra_params: dict[str, str] | None = None,
) -> Outcome:
    """Assert a client-side navigation happened with the expected scope."""
    await wait_path(page, expected_path)
    await page.wait_for_timeout(350)
    info = url_info(page.url)
    observed = f"path={info['path']} params={json.dumps(info['params'], ensure_ascii=False)} title={await page.title()}"
    if info["path"] != expected_path:
        return failed(f"expected path {expected_path}; observed {observed}")
    # Per-case params override the default "today" date (e.g. a clicked wave
    # carries its own start_date), so resolve the expectation once, here.
    expectations = {"date": ctx.today, **(extra_params or {})}
    for key, value in expectations.items():
        if param(info, key) != value:
            return failed(f"expected {key}={value}; observed {observed}")
    return passed(observed, url_after=info["url"])


async def retry_outcome(
    page: Any,
    ctx: Ctx,
    endpoint_glob: str,
    error_index: int,
    description: str,
) -> Outcome:
    """Abort the endpoint until React Query reaches its error state, then click
    the region's RetryButton with the route unblocked and assert a real refetch.

    Aborted requests are tagged as injected in v02-console.json; no console
    message is suppressed or filtered.
    """
    state = {"blocked": True, "aborted": 0}

    async def handler(route: Any) -> None:
        if state["blocked"]:
            state["aborted"] += 1
            await route.abort("failed")
        else:
            await route.continue_()

    await page.route(endpoint_glob, handler)

    async def block() -> None:
        return None

    await settle(page, ctx, block=block)
    error_region = page.locator('[data-state="error"]').nth(error_index)
    try:
        await error_region.wait_for(state="visible", timeout=25_000)
        label = f"{description}: aborted attempts={state['aborted']}, error region visible"
        retry = error_region.get_by_role("button", name=RETRY_RE)
        if await retry.count() != 1:
            return failed(
                f"{label}; expected exactly one retry button in error region, found {await retry.count()}"
            )
        state["blocked"] = False
        await page.unroute(endpoint_glob, handler)
        async with page.expect_request(endpoint_glob, timeout=20_000) as request_info:
            await retry.click()
        request = await request_info.value
        await page.wait_for_function(
            "() => document.querySelectorAll('[data-state=\"error\"]').length === 0",
            timeout=20_000,
        )
        return passed(
            f"{label}; retry fired {request.method} {request.url}; error state cleared",
            request_url=request.url,
            aborted_attempts=state["aborted"],
        )
    except Exception as exc:  # noqa: BLE001 - recorded as a FAIL finding
        return failed(
            f"{description}: aborted attempts={state['aborted']}; "
            f"exception {type(exc).__name__}: {str(exc)[:300]}"
        )
    finally:
        state["blocked"] = False
        try:
            await page.unroute(endpoint_glob, handler)
        except Exception:  # noqa: BLE001 - best-effort cleanup
            pass


# --- element cases ---------------------------------------------------------


async def c001(page: Any, ctx: Ctx) -> Outcome:
    return await retry_outcome(
        page, ctx, "**/api/dashboard/stats*", 0, "C02-001 dashboardStats.refetch()"
    )


async def card_case(page: Any, ctx: Ctx, path: str, index: int) -> Outcome:
    await settle(page, ctx)
    cards = page.locator(f'a:has(span.sr-only)[href^="{path}?"]')
    count = await cards.count()
    if count <= index:
        return skipped(
            f"expected >= {index + 1} dashboard card(s) linking to {path}; found {count}",
            "dashboard stat cards must render with ready stats data — rerun with a live /api/dashboard/stats payload",
        )
    card = cards.nth(index)
    href = await card.get_attribute("href")
    label = (await card.inner_text()).strip().replace("\n", " ")[:90]
    await card.click()
    result = await nav_outcome(page, ctx, path)
    result.extra["href_before_click"] = href
    result.extra["card_label"] = label
    if result.verdict == "PASS":
        result.observed = f"card '{label}' (href={href}) -> {result.observed}"
    return result


async def c002(page: Any, ctx: Ctx) -> Outcome:
    return await card_case(page, ctx, "/mps", 0)


async def c003(page: Any, ctx: Ctx) -> Outcome:
    return await card_case(page, ctx, "/mps", 1)


async def c004(page: Any, ctx: Ctx) -> Outcome:
    return await card_case(page, ctx, "/traseism", 0)


async def c005(page: Any, ctx: Ctx) -> Outcome:
    return await card_case(page, ctx, "/committees", 0)


async def c006(page: Any, ctx: Ctx) -> Outcome:
    """C02-006: play/pause + legislature slider write date+legislature to URL."""
    await settle(page, ctx)
    stops = ctx.stops
    if len(stops) < 2:
        return skipped(
            f"only {len(stops)} legislature stop(s) rendered",
            RESOLVERS["meta"],
        )
    slider = page.locator("#legislature-start-slider")
    await slider.wait_for(state="visible", timeout=15_000)
    index = int(await slider.input_value())
    active = stops[index]
    seen: list[str] = []

    prev = page.get_by_role("button", name=PREV_RE)
    nxt = page.get_by_role("button", name=NEXT_RE)
    if index <= 0:
        return skipped(
            f"initial legislature index={index}; previous legislature unavailable",
            "open '/' with a date after the first legislature start and rerun",
        )

    target = stops[index - 1]
    await prev.click()
    await page.wait_for_function(
        "(v) => new URL(location.href).searchParams.get('date') === v",
        arg=target["start"],
        timeout=15_000,
    )
    after_prev = url_info(page.url)
    if param(after_prev, "legislature") != target["id"]:
        return failed(f"prev: expected legislature={target['id']}; observed {after_prev['url']}")
    seen.append(f"prev -> date={target['start']} legislature={target['id']}")

    await nxt.click()
    await page.wait_for_function(
        "(v) => new URL(location.href).searchParams.get('date') === v",
        arg=active["start"],
        timeout=15_000,
    )
    after_next = url_info(page.url)
    if param(after_next, "legislature") != active["id"]:
        return failed(f"next: expected legislature={active['id']}; observed {after_next['url']}")
    seen.append(f"next -> date={active['start']} legislature={active['id']}")

    play = page.get_by_role("button", name=re.compile(r"^Redă$|^Play$"))
    if await play.is_disabled():
        return passed(
            "; ".join(seen) + "; play/pause disabled under prefers-reduced-motion (designed no-op)"
        )
    before_play = param(url_info(page.url), "date")
    await play.click()
    await page.wait_for_function(
        "(p) => document.querySelector('button[aria-pressed=\"true\"]') !== null",
        timeout=5_000,
    )
    seen.append("play -> aria-pressed=true")
    try:
        await page.wait_for_function(
            "(d) => new URL(location.href).searchParams.get('date') !== d",
            arg=before_play,
            timeout=6_000,
        )
        seen.append(f"autoplay -> date={param(url_info(page.url), 'date')}")
    except Exception:  # noqa: BLE001 - observed as a finding, not a silent pass
        return failed(
            "play toggled but autoplay did not change the scope date within 6s: " + "; ".join(seen)
        )
    pause = page.get_by_role("button", name=re.compile(r"^Pauză$|^Pause$"))
    await pause.click()
    # The pause button's own label flips back to "play" on click, so wait for
    # the *play* control, not for the (now gone) pause name.
    resumed = page.get_by_role("button", name=re.compile(r"^Redă$|^Play$"))
    await resumed.wait_for(state="visible", timeout=5_000)
    if await resumed.get_attribute("aria-pressed") != "false":
        return failed("pause did not clear aria-pressed: " + "; ".join(seen))
    seen.append("pause -> aria-pressed=false, play label restored")
    return passed("; ".join(seen))


async def c007(page: Any, ctx: Ctx) -> Outcome:
    """C02-007: hemicycle member button (keyboard path) -> /person/$id."""
    await settle(page, ctx)
    if not ctx.active_start:
        return skipped("no active legislature start resolved", RESOLVERS["meta"])
    groups, err = ctx.get(f"/api/chamber?chamber=deputies&as_of={ctx.active_start}")
    if err or not groups or not groups.get("groups"):
        return skipped(err or "no chamber groups returned", RESOLVERS["chamber"])
    member = None
    for group in groups["groups"]:
        if group.get("members"):
            member = group["members"][0]
            break
    if not member or not member.get("person_id") or not member.get("name"):
        return skipped("no member with person_id/name in chamber payload", RESOLVERS["chamber"])
    details = page.locator("details").nth(0)
    await details.evaluate("(el) => { el.open = true; }")
    button = details.get_by_role("button", name=re.compile("^" + re.escape(member["name"])))
    if await button.count() == 0:
        return skipped(
            f"member '{member['name']}' from /api/chamber not present in the rendered member list",
            RESOLVERS["chamber"] + " — rerun with the same as_of date the dashboard sampled",
        )
    await button.first.click()
    result = await nav_outcome(page, ctx, f"/person/{member['person_id']}")
    if result.verdict == "PASS":
        result.observed = f"member '{member['name']}' ({member['person_id']}) -> {result.observed}"
    return result


async def first_party(ctx: Ctx) -> tuple[dict[str, Any] | None, str | None]:
    payload, err = ctx.get("/api/parties")
    if err or not payload or not payload.get("data"):
        return None, err or "no parties returned"
    party = next((p for p in payload["data"] if p.get("short_name")), None)
    if not party:
        return None, "no party with a non-empty short_name"
    return party, None


async def c008(page: Any, ctx: Ctx) -> Outcome:
    """C02-008: party row button -> /party/$shortName with scope."""
    await settle(page, ctx)
    party, err = await first_party(ctx)
    if err:
        return skipped(err, RESOLVERS["parties"])
    short = party["short_name"]
    # React emits no whitespace between the rank and name <span>s, so match
    # the raw textContent shape "#1PSD" rather than a whitespace-separated name.
    button = page.locator("button").filter(has_text=re.compile(r"#\d+" + re.escape(short)))
    if await button.count() == 0:
        return skipped(f"party row for '{short}' not rendered", RESOLVERS["parties"])
    await button.first.click()
    result = await nav_outcome(page, ctx, f"/party/{short}")
    if result.verdict == "PASS":
        result.observed = f"party row '{short}' -> {result.observed}"
    return result


async def view_all_case(page: Any, ctx: Ctx, index: int, expected_path: str, label: str) -> Outcome:
    await settle(page, ctx)
    buttons = page.get_by_role("button", name=VIEW_ALL_RE)
    count = await buttons.count()
    if count <= index:
        return skipped(
            f"found {count} 'View all' buttons, expected at least {index + 1}",
            "dashboard data regions must render in ready state — rerun with a live payload",
        )
    button = buttons.nth(index)
    text = (await button.inner_text()).strip()
    await button.click()
    result = await nav_outcome(page, ctx, expected_path)
    result.extra["view_all_label"] = f"{label}: '{text}' (index {index})"
    if result.verdict == "PASS":
        result.observed = f"'{text}' [{label}] -> {result.observed}"
    return result


async def c009(page: Any, ctx: Ctx) -> Outcome:
    return await view_all_case(page, ctx, 0, "/parties", "party list")


async def c010(page: Any, ctx: Ctx) -> Outcome:
    return await retry_outcome(page, ctx, "**/api/parties", 0, "C02-010 party list refetch()")


async def c011(page: Any, ctx: Ctx) -> Outcome:
    """C02-011: enabled chair bar -> /person/$id; disabled bar is a designed no-op."""
    await settle(page, ctx)
    payload, err = ctx.get(f"/api/analytics/committee-control?as_of={ctx.today}")
    if err or not payload or not payload.get("data"):
        return skipped(err or "no committee-control data", RESOLVERS["committee"])
    data = payload["data"]
    top = sorted(data.get("parties") or [], key=lambda p: p.get("chairs", 0), reverse=True)[:5]
    chosen = None
    for party in top:
        chair = next(
            (c for c in data.get("chairs") or [] if c.get("party") == party.get("party")), None
        )
        if chair and chair.get("chair_person_id"):
            chosen = chair
            break
    if not chosen:
        return skipped(
            "no top-5 party has a chair with a non-empty chair_person_id",
            RESOLVERS["committee"],
        )
    party_name = chosen["party"]
    button = page.get_by_role(
        "button",
        name=re.compile(r"(Arată președintele|Show chair for)\s+" + re.escape(party_name)),
    )
    if await button.count() == 0:
        return skipped(f"chair button for '{party_name}' not rendered", RESOLVERS["committee"])
    chair_button = button.first
    if await chair_button.is_disabled():
        return passed(
            f"chair bar for '{party_name}' is disabled (no chair_person_id) — designed no-op"
        )
    await chair_button.click()
    result = await nav_outcome(page, ctx, f"/person/{chosen['chair_person_id']}")
    if result.verdict == "PASS":
        result.observed = f"chair '{chosen['chair']}' / {party_name} -> {result.observed}"
    return result


async def c012(page: Any, ctx: Ctx) -> Outcome:
    return await retry_outcome(
        page, ctx, "**/api/analytics/committee-control*", 0, "C02-012 committeeControl.refetch()"
    )


async def c013(page: Any, ctx: Ctx) -> Outcome:
    return await retry_outcome(
        page, ctx, "**/api/coverage/detailed", 0, "C02-013 coverageDetailed.refetch()"
    )


async def c014(page: Any, ctx: Ctx) -> Outcome:
    return await retry_outcome(page, ctx, "**/api/parties", 1, "C02-014 party network refetch()")


async def c015(page: Any, ctx: Ctx) -> Outcome:
    """C02-015: PartyNetwork node -> /party/$shortName."""
    await settle(page, ctx)
    party, err = await first_party(ctx)
    if err:
        return skipped(err, RESOLVERS["parties"])
    short = party["short_name"]
    button = page.get_by_role(
        "button", name=re.compile(r"(Partidul|Party)\s+" + re.escape(short) + r":")
    )
    if await button.count() == 0:
        return skipped(f"party network node for '{short}' not rendered", RESOLVERS["parties"])
    await button.first.click()
    result = await nav_outcome(page, ctx, f"/party/{short}")
    if result.verdict == "PASS":
        result.observed = f"network node '{short}' -> {result.observed}"
    return result


async def c016(page: Any, ctx: Ctx) -> Outcome:
    return await view_all_case(page, ctx, 1, "/mps", "party network")


async def c017(page: Any, ctx: Ctx) -> Outcome:
    return await retry_outcome(
        page, ctx, "**/api/analytics/switch-waves*", 0, "C02-017 switchWaves.refetch()"
    )


async def c018(page: Any, ctx: Ctx) -> Outcome:
    """C02-018: a wave bar and the timeline 'View all' both route to /traseism."""
    trace: list[dict[str, str]] = []

    def mark(step: str) -> None:
        trace.append({"step": step, "url": page.url})

    await settle(page, ctx)
    mark("dashboard-before-wave")
    waves, err = ctx.get("/api/analytics/switch-waves")
    if err or not waves:
        return skipped(err or "no switch waves returned", RESOLVERS["waves"])
    rects = page.locator('svg rect[role="button"]')
    count = await rects.count()
    if count == 0:
        return skipped("no wave <rect role=button> rendered", RESOLVERS["waves"])
    rect = rects.first
    label = await rect.get_attribute("aria-label") or ""
    match = re.search(r"\d{4}-\d{2}-\d{2}", label)
    if not match:
        return skipped(f"wave aria-label has no ISO date: {label!r}", RESOLVERS["waves"])
    wave_date = match.group(0)
    await rect.click()
    await wait_path(page, "/traseism")
    mark("after-wave-rect-click")
    first = await nav_outcome(page, ctx, "/traseism", extra_params={"date": wave_date})
    trace.append({"step": "wave-rect-result", "url": page.url, "detail": first.observed})
    if first.verdict == "FAIL":
        return failed(
            f"wave rect '{label}' (expected date={wave_date}) -> {first.observed}",
            trace=trace,
            wave_label=label,
        )
    observed = [f"wave rect '{label}' -> {first.observed}"]

    await settle(page, ctx)
    await wait_path(page, "/")
    mark("dashboard-before-view-all")
    buttons = page.get_by_role("button", name=VIEW_ALL_RE)
    if await buttons.count() < 3:
        return skipped(
            f"found {await buttons.count()} 'View all' buttons, expected the timeline's third",
            "switch wave timeline must render in ready state — rerun with a live /api/analytics/switch-waves payload",
            trace=trace,
        )
    text = (await buttons.nth(2).inner_text()).strip()
    await buttons.nth(2).click()
    await wait_path(page, "/traseism")
    mark("after-view-all-click")
    second = await nav_outcome(page, ctx, "/traseism", extra_params={"date": ctx.today})
    trace.append({"step": "view-all-result", "url": page.url, "detail": second.observed})
    if second.verdict == "FAIL":
        return failed(
            f"timeline 'View all' '{text}' (expected date={ctx.today}) -> {second.observed}",
            trace=trace,
            view_all_label=text,
        )
    observed.append(f"timeline 'View all' '{text}' -> {second.observed}")
    note = (
        "wave-specific chamber/legislature are not carried (handler hardcodes "
        "chamber=deputies, legislature=undefined) — recorded, not repaired"
    )
    return passed("; ".join(observed) + f"; NOTE: {note}", wave_count=len(waves), trace=trace)


async def c019(page: Any, ctx: Ctx) -> Outcome:
    """C02-019: cross-chamber member -> /person/$id."""
    await settle(page, ctx)
    payload, err = ctx.get(f"/api/analytics/cross-chamber?as_of={ctx.today}")
    if err or not payload or not payload.get("data"):
        return skipped(err or "no cross-chamber members returned", RESOLVERS["cross"])
    person = payload["data"][0]
    if not person.get("person_id") or not person.get("name"):
        return skipped("cross-chamber row lacks person_id/name", RESOLVERS["cross"])
    button = page.get_by_role("button", name=re.compile("^" + re.escape(person["name"])))
    if await button.count() == 0:
        return skipped(f"cross-chamber member '{person['name']}' not rendered", RESOLVERS["cross"])
    await button.first.click()
    result = await nav_outcome(page, ctx, f"/person/{person['person_id']}")
    if result.verdict == "PASS":
        result.observed = f"cross-chamber member '{person['name']}' -> {result.observed}"
    return result


async def c020(page: Any, ctx: Ctx) -> Outcome:
    """C02-020: LiveFeed event row -> /person/$id."""
    await settle(page, ctx)
    events, err = ctx.get("/api/events/recent?limit=40&chamber=senate&legislature=2024")
    if err or not events:
        return skipped(err or "no recent events returned", RESOLVERS["events"])
    event = next(
        (e for e in events if e.get("person", {}).get("id") and e.get("person", {}).get("name")),
        None,
    )
    if not event:
        return skipped("no recent event with a resolvable person", RESOLVERS["events"])
    person = event["person"]
    region = page.get_by_role("region", name=re.compile(r"Activitate recentă|Recent activity"))
    if await region.count() == 0:
        return skipped(
            "LiveFeed region not rendered", "rerun with a live /api/events/recent payload"
        )
    button = region.get_by_role("button").filter(has_text=person["name"])
    if await button.count() == 0:
        return skipped(f"feed row for '{person['name']}' not rendered", RESOLVERS["events"])
    await button.first.click()
    result = await nav_outcome(page, ctx, f"/person/{person['id']}")
    if result.verdict == "PASS":
        result.observed = (
            f"feed row '{person['name']}' ({event.get('event_date')}) -> {result.observed}"
        )
    return result


CASES: list[dict[str, Any]] = [
    {
        "id": "C02-001",
        "line": "LiveDashboard.tsx:128",
        "action": "force stats error; click RetryButton",
        "expected": "a new /api/dashboard/stats request fires and the error state clears",
        "fn": c001,
    },
    {
        "id": "C02-002",
        "line": "LiveDashboard.tsx:132-142 (linkTo :140)",
        "action": "click 'Members of Parliament' stat card",
        "expected": "URL /mps with date scope preserved",
        "fn": c002,
    },
    {
        "id": "C02-003",
        "line": "LiveDashboard.tsx:143-153 (linkTo :151)",
        "action": "click 'Memberships' stat card",
        "expected": "URL /mps with date scope preserved",
        "fn": c003,
    },
    {
        "id": "C02-004",
        "line": "LiveDashboard.tsx:154-164 (linkTo :162)",
        "action": "click 'All observed affiliation changes' stat card",
        "expected": "URL /traseism with date scope preserved",
        "fn": c004,
    },
    {
        "id": "C02-005",
        "line": "LiveDashboard.tsx:165-176 (linkTo :174)",
        "action": "click 'Committees' stat card",
        "expected": "URL /committees with date scope preserved",
        "fn": c005,
    },
    {
        "id": "C02-006",
        "line": "LiveDashboard.tsx:201",
        "action": "click prev/next, play and pause the legislature slider",
        "expected": "URL date+legislature change; play toggles aria-pressed and auto-advances",
        "fn": c006,
    },
    {
        "id": "C02-007",
        "line": "LiveDashboard.tsx:202",
        "action": "expand hemicycle member list; click a member button",
        "expected": "URL /person/<resolved person_id> with scope",
        "fn": c007,
    },
    {
        "id": "C02-008",
        "line": "LiveDashboard.tsx:219",
        "action": "click a party row button in Party Representation",
        "expected": "URL /party/<resolved short_name> with scope",
        "fn": c008,
    },
    {
        "id": "C02-009",
        "line": "LiveDashboard.tsx:220",
        "action": "click party list 'View all'",
        "expected": "URL /parties with scope",
        "fn": c009,
    },
    {
        "id": "C02-010",
        "line": "LiveDashboard.tsx:214",
        "action": "force /api/parties error; click party list RetryButton",
        "expected": "a new /api/parties request fires and the error state clears",
        "fn": c010,
    },
    {
        "id": "C02-011",
        "line": "LiveDashboard.tsx:227",
        "action": "click the enabled committee chair bar for a resolved party",
        "expected": "URL /person/<resolved chair_person_id>, or a disabled bar as designed no-op",
        "fn": c011,
    },
    {
        "id": "C02-012",
        "line": "LiveDashboard.tsx:229",
        "action": "force committee-control error; click RetryButton",
        "expected": "a new /api/analytics/committee-control request fires and the error clears",
        "fn": c012,
    },
    {
        "id": "C02-013",
        "line": "LiveDashboard.tsx:234",
        "action": "force coverage error; click RetryButton",
        "expected": "a new /api/coverage/detailed request fires and the error clears",
        "fn": c013,
    },
    {
        "id": "C02-014",
        "line": "LiveDashboard.tsx:255",
        "action": "force /api/parties error; click party network RetryButton",
        "expected": "a new /api/parties request fires and the error clears",
        "fn": c014,
    },
    {
        "id": "C02-015",
        "line": "LiveDashboard.tsx:260",
        "action": "click a PartyNetwork node",
        "expected": "URL /party/<resolved short_name> with scope",
        "fn": c015,
    },
    {
        "id": "C02-016",
        "line": "LiveDashboard.tsx:261",
        "action": "click party network 'View all'",
        "expected": "URL /mps with scope",
        "fn": c016,
    },
    {
        "id": "C02-017",
        "line": "LiveDashboard.tsx:272",
        "action": "force switch-waves error; click RetryButton",
        "expected": "a new /api/analytics/switch-waves request fires and the error clears",
        "fn": c017,
    },
    {
        "id": "C02-018",
        "line": "LiveDashboard.tsx:277",
        "action": "click a wave bar, then the timeline 'View all'",
        "expected": "URL /traseism with the wave date (today for 'View all')",
        "fn": c018,
    },
    {
        "id": "C02-019",
        "line": "LiveDashboard.tsx:289",
        "action": "click a cross-chamber member button",
        "expected": "URL /person/<resolved person_id> with scope",
        "fn": c019,
    },
    {
        "id": "C02-020",
        "line": "LiveDashboard.tsx:300",
        "action": "click a LiveFeed event row with a person",
        "expected": "URL /person/<resolved person_id> with scope",
        "fn": c020,
    },
]


def make_console_listener(ctx: Ctx, element_id: str, case_kind: str) -> Callable[[Any], None]:
    def on_console(message: Any) -> None:
        if message.type != "error":
            return
        ctx.console.append(
            {
                "at": now_iso(),
                "element_id": element_id,
                "kind": "console.error",
                "text": message.text[:500],
                "context": "retry-request-aborted-by-test"
                if case_kind == "retry"
                else "navigation",
            }
        )

    return on_console


def make_pageerror_listener(ctx: Ctx, element_id: str) -> Callable[[Any], None]:
    def on_pageerror(exc: Any) -> None:
        ctx.console.append(
            {
                "at": now_iso(),
                "element_id": element_id,
                "kind": "pageerror",
                "text": str(exc)[:500],
                "context": "uncaught exception",
            }
        )

    return on_pageerror


async def run_case(browser: Any, case: dict[str, Any], ctx: Ctx) -> dict[str, Any]:
    element_id = case["id"]
    ctx.current_id = element_id
    page = await browser.new_page()
    page.set_default_timeout(20_000)
    page.set_default_navigation_timeout(35_000)
    requests: list[dict[str, str]] = []
    console_start = len(ctx.console)
    before_url = ""
    outcome: Outcome | None = None

    try:
        page.on(
            "console",
            make_console_listener(
                ctx,
                element_id,
                "retry"
                if element_id in {"C02-001", "C02-010", "C02-012", "C02-013", "C02-014", "C02-017"}
                else "navigation",
            ),
        )
        page.on("pageerror", make_pageerror_listener(ctx, element_id))
        page.on(
            "request",
            lambda req: (
                requests.append({"method": req.method, "url": req.url})
                if "/api/" in req.url and len(requests) < 250
                else None
            ),
        )
        raw = await case["fn"](page, ctx)
        outcome = raw if isinstance(raw, Outcome) else failed(f"case returned {type(raw).__name__}")
    except Exception as exc:  # noqa: BLE001 - an exception is a finding with evidence
        outcome = failed(f"harness exception: {type(exc).__name__}: {str(exc)[:400]}")
    finally:
        before_url = page.url or ""
        shot = OUT_DIR / f"v02-shot-{element_id}.png"
        try:
            await page.screenshot(path=str(shot), timeout=10_000)
        except Exception:  # noqa: BLE001 - evidence best effort
            pass
        try:
            await page.close()
        except Exception:  # noqa: BLE001 - browser is closed by run_all's finally
            pass

    assert outcome is not None
    evidence_path = OUT_DIR / f"v02-evidence-{element_id}.json"
    evidence = {
        "element_id": element_id,
        "source_file_line": case["line"],
        "action": case["action"],
        "expected": case["expected"],
        "observed": outcome.observed,
        "verdict": outcome.verdict,
        "resolver": outcome.resolver,
        "url_at_capture": before_url,
        "screenshot": str(shot),
        "api_requests": requests,
        "console_errors": ctx.console[console_start:],
        "extra": outcome.extra,
        "captured_at": now_iso(),
    }
    write_json(evidence_path, evidence)
    row = {
        "element_id": element_id,
        "source_file_line": case["line"],
        "action": case["action"],
        "expected": case["expected"],
        "observed": outcome.observed,
        "verdict": outcome.verdict,
        # fleet-contract aliases (CLICK-VALIDATION-FLEET §3 row schema)
        "expected_outcome": case["expected"],
        "observed_outcome": outcome.observed,
        "status": outcome.verdict,
        "evidence_path": str(evidence_path),
    }
    if outcome.resolver:
        row["resolver"] = outcome.resolver
    return row


async def run_all(cases: list[dict[str, Any]], ctx: Ctx) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=BROWSER, args=["--no-sandbox"])
        try:
            for case in cases:
                rows.append(await run_case(browser, case, ctx))
        finally:
            await browser.close()
    return rows


def test_v02_overview_clickables() -> None:
    ctx = Ctx()
    rows: list[dict[str, Any]] = []
    try:
        rows = asyncio.run(run_all(CASES, ctx))
    finally:
        # Artifacts are written even if the harness itself raises.
        write_json(RESULTS_PATH, rows)
        write_json(
            CONSOLE_PATH,
            {
                "base": BASE,
                "browser": BROWSER,
                "captured_at": now_iso(),
                "events": ctx.console,
                "counts": {
                    "total": len(ctx.console),
                    "console_error": sum(e["kind"] == "console.error" for e in ctx.console),
                    "pageerror": sum(e["kind"] == "pageerror" for e in ctx.console),
                    "test_injected": sum(
                        e["context"] == "retry-request-aborted-by-test" for e in ctx.console
                    ),
                },
            },
        )

    assert len(rows) == 20, f"expected 20 element rows, got {len(rows)}"
    counts = {v: sum(r["verdict"] == v for r in rows) for v in ("PASS", "FAIL", "SKIP")}
    print("V-02 verdicts:", counts, "results:", RESULTS_PATH, "console:", CONSOLE_PATH)
    failures = [f"{r['element_id']}: {r['observed']}" for r in rows if r["verdict"] == "FAIL"]
    assert not failures, "click validation FAILs:\n" + "\n".join(failures)
