"""V-06 clickable validation — C03-015..021 and C02-040..058 (26 elements).

Fleet contract: CLICK-VALIDATION-FLEET-2026-11-23.md §2/§3. This file owns only
itself and the ``/tmp/opencode/click-validation/v06-*`` artifacts. It validates
*behaviour* (URL/scope change, visible text/state, a fired request, a native
disclosure transition, or a resolved in-app destination) against the read-only
local dev server at ``http://127.0.0.1:5188`` — never production.

Routes under test: /committees, /leaderboard, /coverage, /institutional,
/senate-history, /legislature/2024. Dynamic IDs (committee, member, chair,
leaderboard person, movement person, legislature, senate legislature) are
resolved from the live API at runtime; an unresolved ID is a SKIP with a named
resolver, never a silent PASS.

One chromium instance, one page per element, browser closed in ``finally``.
Retry buttons are exercised by aborting one read-only GET until React Query
reaches its error state, then unrouting and clicking Retry; every console error
caused by that injection is labelled ``test_induced`` in v06-console.json and
nothing is suppressed. A FAIL is a finding, not a fix and not a code edit.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from datetime import date as date_cls
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:5188"
BROWSER = "/usr/bin/chromium"
OUT_DIR = Path("/tmp/opencode/click-validation")
RESULTS_PATH = OUT_DIR / "v06-results.json"
CONSOLE_PATH = OUT_DIR / "v06-console.json"

RETRY_RE = re.compile(r"Reîncearcă|Retry|Încearcă")

RE_LIST = re.compile(r"/api/committees\?")
RE_MEMBERS = re.compile(r"/api/committees/[^/]+/members")
RE_CONTROL = re.compile(r"/api/analytics/committee-control")
RE_LEADER = re.compile(r"/api/analytics/switch-leaderboard")
RE_DIM = re.compile(r"/api/coverage/dimensions")
RE_COVDET = re.compile(r"/api/coverage/detailed")
RE_CROSS = re.compile(r"/api/analytics/cross-chamber")
RE_META = re.compile(r"/api/meta(?:\?|$)")
RE_CHAMBER = re.compile(r"/api/chamber\?")
RE_MOVEMENTS = re.compile(r"/api/movements\?")

RESOLVERS = {
    "committee": "GET /api/committees?as_of=<date> -> a committee with a non-empty id (rerun with a live corpus)",
    "member": "GET /api/committees/<id>/members?as_of=<date> -> a member with a non-empty person_id",
    "chair": "GET /api/analytics/committee-control -> a chair with a non-empty chair_person_id",
    "leaderboard": "GET /api/analytics/switch-leaderboard?limit=20 -> data[0].person_id",
    "movement": "GET /api/movements?<page params> -> first event with person.id in the first 20 rows",
    "meta": "GET /api/meta -> legislatures keys (rerun with live metadata)",
    "coverage": "GET /api/coverage/detailed -> a chamber/legislature pair present in the live matrix",
    "senate": "GET /api/coverage/detailed -> a legislature whose chamber == 'senate'",
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
        "params": {k: v[-1] for k, v in urllib.parse.parse_qs(parts.query).items()},
    }


def param(info: dict[str, Any], key: str) -> str | None:
    return info["params"].get(key)


def served_head() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd="/home/nedaktov/parlament-deschis",
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        return out.decode().strip()
    except Exception:  # noqa: BLE001 - identity only, never a verdict
        return "unavailable"


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
    """Per-run state shared by the 26 element cases (no files outside v06-*)."""

    def __init__(self) -> None:
        self.today = date_cls.today().isoformat()
        self.head = served_head()
        self.current_id = "C03-000"
        self.test_induced = False
        self.console: list[dict[str, Any]] = []
        self.requests: list[str] = []
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

    def count(self, pattern: re.Pattern[str]) -> int:
        return sum(1 for url in self.requests if pattern.search(url))


def attach_listeners(page: Any, ctx: Ctx) -> None:
    def on_console(msg: Any) -> None:
        if msg.type == "error":
            ctx.console.append(
                {
                    "ts": datetime.now(UTC).timestamp(),
                    "element": ctx.current_id,
                    "kind": "console.error",
                    "test_induced": ctx.test_induced,
                    "page": ctx.current_page,
                    "text": msg.text[:400],
                }
            )

    def on_pageerror(exc: Any) -> None:
        ctx.console.append(
            {
                "ts": datetime.now(UTC).timestamp(),
                "element": ctx.current_id,
                "kind": "pageerror",
                "test_induced": ctx.test_induced,
                "page": ctx.current_page,
                "text": str(exc)[:400],
            }
        )

    def on_request(req: Any) -> None:
        ctx.requests.append(req.url)

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)
    page.on("request", on_request)


async def settle(page: Any, ctx: Ctx, path: str = "/") -> None:
    """Bounded navigation: load, bounded networkidle, fixed settle (ui_validate.py)."""
    await page.goto(BASE + path, wait_until="load", timeout=40_000)
    try:
        await page.wait_for_load_state("networkidle", timeout=10_000)
    except Exception:  # noqa: BLE001 - bounded fallback to the fixed settle
        pass
    await page.wait_for_timeout(2_000)
    observed = param(url_info(page.url), "date")
    if observed:
        ctx.today = observed


async def wait_path(page: Any, path: str, timeout: int = 20_000) -> None:
    await page.wait_for_function("(p) => location.pathname === p", arg=path, timeout=timeout)


async def wait_param(page: Any, key: str, value: str, timeout: int = 20_000) -> None:
    await page.wait_for_function(
        "([k, v]) => new URL(location.href).searchParams.get(k) === v",
        arg=[key, value],
        timeout=timeout,
    )


async def wait_error_cleared(page: Any, timeout: int = 20_000) -> None:
    await page.wait_for_function(
        "() => document.querySelectorAll('[data-state=\"error\"]').length === 0",
        timeout=timeout,
    )


async def click_person_target(
    page: Any, target: Any, expected_pid: str, label: str, *, kind: str = "link"
) -> Outcome:
    """Assert a real in-app navigation to /person/$id with a title change."""
    href = await target.get_attribute("href") if kind == "link" else None
    text = (await target.inner_text()).strip().replace("\n", " ")[:100]
    expected = "/person/" + urllib.parse.unquote(expected_pid)
    title_before = await page.title()
    await target.click()
    await wait_path(page, expected)
    await page.wait_for_timeout(350)
    title_after = await page.title()
    if title_before == title_after:
        return failed(
            f"clicked {kind} '{text}' (href={href}); path={url_info(page.url)['path']} "
            f"but title did not change ('{title_after}')"
        )
    return passed(
        f"{kind} '{text}' (href={href}) -> path={url_info(page.url)['path']}; "
        f"title '{title_before}' -> '{title_after}'",
        href_before=href,
        url_after=page.url,
        title_before=title_before,
        title_after=title_after,
    )


async def click_person_link(page: Any, link: Any, label: str) -> Outcome:
    """Link case: the destination id comes from the rendered href."""
    href = await link.get_attribute("href")
    match = re.search(r"/person/([^/?#]+)", href or "")
    if not match:
        return failed(f"link '{label}' has no /person/$id href (href={href})")
    return await click_person_target(page, link, match.group(1), label, kind="link")


async def click_person_button(page: Any, button: Any, pid: str, label: str) -> Outcome:
    """Button case: the destination id comes from the resolved live payload."""
    return await click_person_target(page, button, pid, label, kind="button")


async def retry_case(
    page: Any,
    ctx: Ctx,
    *,
    path: str,
    pattern: re.Pattern[str],
    description: str,
    expect: list[re.Pattern[str]],
    after: Callable[[Any], Any],
    prepare: Callable[[Any], Any] | None = None,
    error_selector: str = '[data-state="error"]',
) -> Outcome:
    """Force one read-only GET to fail, then click the real RetryButton.

    The aborted requests are tagged ``test_induced`` in v06-console.json; no
    console message is filtered or suppressed to obtain a PASS.
    """
    state = {"blocked": True, "aborted": 0}

    async def handler(route: Any) -> None:
        if state["blocked"]:
            state["aborted"] += 1
            await route.abort("failed")
        else:
            await route.continue_()

    ctx.test_induced = True
    await page.route(pattern, handler)
    try:
        await settle(page, ctx, path)
        if prepare is not None:
            await prepare(page)
        error_region = page.locator(error_selector).first
        await error_region.wait_for(state="visible", timeout=30_000)
        error_text = (await error_region.inner_text()).strip().replace("\n", " ")[:180]
        retry = error_region.get_by_role("button", name=RETRY_RE)
        retry_count = await retry.count()
        if retry_count < 1:
            return failed(
                f"{description}: error state visible ('{error_text}') but no RetryButton found"
            )
        state["blocked"] = False
        await page.unroute(pattern, handler)
        ctx.test_induced = False
        before = {p.pattern: ctx.count(p) for p in expect}
        await retry.click()
        deadline = asyncio.get_running_loop().time() + 15
        while any(ctx.count(p) <= before[p.pattern] for p in expect):
            if asyncio.get_running_loop().time() > deadline:
                break
            await asyncio.sleep(0.2)
        fired = [f"{p.pattern} +{ctx.count(p) - before[p.pattern]}" for p in expect]
        missing = [p.pattern for p in expect if ctx.count(p) <= before[p.pattern]]
        if missing:
            return failed(
                f"{description}: aborted={state['aborted']}, error '{error_text}', "
                f"RetryButton clicked, but no new request for {missing} (seen {fired})"
            )
        await wait_error_cleared(page)
        observed_after = await after(page)
        return passed(
            f"{description}: aborted attempts={state['aborted']}; error '{error_text}'; "
            f"retry requests [{', '.join(fired)}]; {observed_after}",
            aborted_attempts=state["aborted"],
            retry_requests=fired,
            after=observed_after,
        )
    except Exception as exc:  # noqa: BLE001 - recorded as a FAIL finding
        return failed(
            f"{description}: aborted={state['aborted']}; "
            f"exception {type(exc).__name__}: {str(exc)[:300]}"
        )
    finally:
        state["blocked"] = False
        ctx.test_induced = False
        try:
            await page.unroute(pattern, handler)
        except Exception:  # noqa: BLE001 - best-effort cleanup
            pass


async def after_visible(page: Any, text: str) -> str:
    await page.get_by_text(text, exact=False).first.wait_for(state="visible", timeout=15_000)
    return f"visible text '{text}'"


async def after_h1(page: Any) -> str:
    h1 = page.locator("h1:not(.sr-only)").first
    await h1.wait_for(state="visible", timeout=15_000)
    return f"h1='{(await h1.inner_text()).strip()[:80]}'"


async def after_rows(page: Any) -> str:
    """Count only rendered rows — closed <details> tables are hidden, not absent."""
    await page.wait_for_function(
        "() => Array.from(document.querySelectorAll('table tbody tr'))"
        ".some(tr => tr.getClientRects().length > 0)",
        timeout=15_000,
    )
    count = await page.evaluate(
        "() => Array.from(document.querySelectorAll('table tbody tr'))"
        ".filter(tr => tr.getClientRects().length > 0).length"
    )
    return f"visible table rows={count}"


async def after_chairs(page: Any) -> str:
    await page.wait_for_function(
        "() => document.querySelectorAll('details table tbody tr').length > 0", timeout=15_000
    )
    n = await page.locator("details table tbody tr").count()
    return f"chairs table rows={n}"


async def after_committee_cards(page: Any) -> str:
    await page.wait_for_function(
        "() => document.querySelectorAll('button[aria-expanded]').length > 0", timeout=15_000
    )
    return f"committee cards={await page.locator('button[aria-expanded]').count()}"


async def after_committee_names(page: Any) -> str:
    await page.wait_for_function(
        "() => document.querySelectorAll('.card span.font-medium').length > 0", timeout=15_000
    )
    return f"committee name spans={await page.locator('.card span.font-medium').count()}"


async def after_generic(page: Any) -> str:
    """Locale-independent evidence: error cleared, content rendered, buttons live."""
    body = (await page.inner_text("body")) or ""
    flat = " ".join(body.split())[:140]
    return (
        f"body='{flat}'; buttons={await page.locator('button').count()}; "
        f"cards={await page.locator('.card').count()}; "
        f"error_regions={await page.locator('[data-state="error"]').count()}"
    )


# --- C03: Committees -------------------------------------------------------


async def c03_015(page: Any, ctx: Ctx) -> Outcome:
    """Member ledger link -> /person/$id (data-driven member.person_id)."""
    data, err = ctx.get(f"/api/committees?as_of={ctx.today}")
    if err or not isinstance(data, list) or not data:
        return skipped(f"committee list unavailable: {err}", RESOLVERS["committee"])
    chosen = None
    for committee in data:
        members, merr = ctx.get(f"/api/committees/{committee['id']}/members?as_of={ctx.today}")
        if merr or not isinstance(members, dict):
            continue
        usable = [m for m in (members.get("members") or []) if m.get("person_id")]
        if usable:
            chosen = (committee, usable[0])
            break
    if chosen is None:
        return skipped("no live committee member with a non-empty person_id", RESOLVERS["member"])
    committee, member = chosen
    await settle(page, ctx, "/committees")
    card = page.locator("button[aria-expanded]", has_text=committee["name"]).first
    if await card.count() == 0:
        return skipped(
            f"committee card '{committee['name'][:60]}' not rendered", RESOLVERS["committee"]
        )
    await card.click()
    region = page.locator(f'[role="region"][aria-label="{committee["name"]}"]').first
    try:
        await region.wait_for(state="visible", timeout=20_000)
    except Exception:  # noqa: BLE001 - locate link globally as a fallback
        pass
    link = page.locator(f'a[href*="/person/{member["person_id"]}"]').first
    if await link.count() == 0:
        return skipped(
            f"member link for person_id={member['person_id']} not rendered after expand",
            RESOLVERS["member"],
            committee_id=committee["id"],
        )
    result = await click_person_link(page, link, member.get("name") or "member")
    result.extra.update(
        committee_id=committee["id"], person_id=member["person_id"], expand_required=True
    )
    return result


async def c03_016(page: Any, ctx: Ctx) -> Outcome:
    """Committee card: aria-expanded false -> true -> false + members request."""
    await settle(page, ctx, "/committees")
    button = page.locator("button[aria-expanded]").first
    if await button.count() == 0:
        return skipped("no committee card with aria-expanded rendered", RESOLVERS["committee"])
    name = (await button.inner_text()).strip().replace("\n", " ")[:80]
    before = await button.get_attribute("aria-expanded")
    before_requests = ctx.count(RE_MEMBERS)
    regions_before = await page.locator('[role="region"]').count()
    await button.click()
    await page.wait_for_function(
        "() => document.querySelector('button[aria-expanded]')?.getAttribute('aria-expanded') === 'true'",
        timeout=20_000,
    )
    await page.wait_for_timeout(1_200)
    regions_expanded = await page.locator('[role="region"]').count()
    after_requests = ctx.count(RE_MEMBERS)
    caret = await button.inner_text()
    await button.click()
    await page.wait_for_function(
        "() => document.querySelector('button[aria-expanded]')?.getAttribute('aria-expanded') === 'false'",
        timeout=20_000,
    )
    regions_collapsed = await page.locator('[role="region"]').count()
    if (
        before != "false"
        or after_requests <= before_requests
        or regions_expanded <= regions_before
        or regions_collapsed >= regions_expanded
    ):
        return failed(
            f"card '{name}': aria-expanded {before}->true->false; member requests "
            f"{before_requests}->{after_requests}; regions {regions_before}->{regions_expanded}"
            f"->{regions_collapsed}; button text '{caret.strip()[:80]}'"
        )
    return passed(
        f"card '{name}': aria-expanded {before}->true->false; member request fired "
        f"({before_requests}->{after_requests}); disclosure region {regions_before}->"
        f"{regions_expanded}->{regions_collapsed}; caret toggled",
        member_requests_before=before_requests,
        member_requests_after=after_requests,
        regions=[regions_before, regions_expanded, regions_collapsed],
    )


async def c03_017(page: Any, ctx: Ctx) -> Outcome:
    """Control-index chair link -> /person/$id (data-driven chair_person_id)."""
    data, err = ctx.get("/api/analytics/committee-control")
    chairs = ((data or {}).get("data") or {}).get("chairs") or [] if not err else []
    usable = [c for c in chairs if c.get("chair_person_id")]
    if not usable:
        return skipped(
            f"no live chair with a non-empty chair_person_id ({err})", RESOLVERS["chair"]
        )
    chair = usable[0]
    await settle(page, ctx, "/committees")
    summary = page.locator("details summary").first
    if await summary.count() == 0:
        return skipped("committee control index <details> not rendered", RESOLVERS["chair"])
    await summary.click()
    await page.wait_for_function(
        "() => document.querySelector('details')?.open === true", timeout=15_000
    )
    link = page.locator(f'a[href*="/person/{chair["chair_person_id"]}"]').first
    if await link.count() == 0:
        return skipped(
            f"chair link for person_id={chair['chair_person_id']} not rendered",
            RESOLVERS["chair"],
        )
    result = await click_person_link(page, link, chair.get("chair") or "chair")
    result.extra["chair_person_id"] = chair["chair_person_id"]
    return result


async def c03_018(page: Any, ctx: Ctx) -> Outcome:
    """Native <details>/<summary> 'Show all chairs' disclosure toggles open."""
    await settle(page, ctx, "/committees")
    details = page.locator("details").first
    if await details.count() == 0:
        return skipped("committee control index <details> not rendered", RESOLVERS["chair"])
    summary = details.locator("summary").first
    label = (await summary.inner_text()).strip()
    before = await details.evaluate("el => el.open")
    await summary.click()
    await page.wait_for_function(
        "() => document.querySelector('details')?.open === true", timeout=15_000
    )
    table_visible = await details.locator("table").first.is_visible()
    chair_rows = await details.locator("table tbody tr").count()
    await summary.click()
    await page.wait_for_function(
        "() => document.querySelector('details')?.open === false", timeout=15_000
    )
    after = await details.evaluate("el => el.open")
    if before is not False or after is not False or not table_visible or chair_rows == 0:
        return failed(
            f"summary '{label}': details.open {before}->true->{after}; table_visible="
            f"{table_visible}; chair_rows={chair_rows}"
        )
    return passed(
        f"summary '{label}': details.open false->true->false; chairs table visible with "
        f"{chair_rows} rows while open",
        chair_rows=chair_rows,
    )


async def c03_019(page: Any, ctx: Ctx) -> Outcome:
    """Retry inside an expanded committee's member-error region."""

    async def prepare(p: Any) -> None:
        data, _ = ctx.get(f"/api/committees?as_of={ctx.today}")
        first = (data or [{}])[0]
        card = p.locator("button[aria-expanded]", has_text=first.get("name", "")).first
        if await card.count():
            await card.click()

    return await retry_case(
        page,
        ctx,
        path="/committees",
        pattern=RE_MEMBERS,
        description="C03-019 members.refetch() retry",
        expect=[RE_MEMBERS],
        after=after_rows,
        prepare=prepare,
        error_selector='[role="region"] [data-state="error"]',
    )


async def c03_020(page: Any, ctx: Ctx) -> Outcome:
    return await retry_case(
        page,
        ctx,
        path="/committees",
        pattern=RE_CONTROL,
        description="C03-020 control.refetch() retry",
        expect=[RE_CONTROL],
        after=after_chairs,
    )


async def c03_021(page: Any, ctx: Ctx) -> Outcome:
    return await retry_case(
        page,
        ctx,
        path="/committees",
        pattern=RE_LIST,
        description="C03-021 list.refetch() retry",
        expect=[RE_LIST],
        after=after_committee_cards,
    )


# --- C02: SwitchLeaderboard ------------------------------------------------


async def c02_040(page: Any, ctx: Ctx) -> Outcome:
    return await retry_case(
        page,
        ctx,
        path="/leaderboard",
        pattern=RE_LEADER,
        description="C02-040 leaderboard.refetch() retry",
        expect=[RE_LEADER],
        after=after_h1,
    )


async def c02_041(page: Any, ctx: Ctx) -> Outcome:
    """Shared ScopeControls (chamber + legislature) on /leaderboard."""
    meta, err = ctx.get("/api/meta")
    years = sorted((meta or {}).get("legislatures", {}).keys()) if not err else []
    if not years:
        return skipped(f"legislature options unavailable: {err}", RESOLVERS["meta"])
    year = years[-2] if len(years) > 1 else years[0]
    await settle(page, ctx, "/leaderboard")

    chamber = page.locator("#scope-chamber")
    if await chamber.count() != 1:
        return skipped("leaderboard ScopeControls chamber select not rendered", RESOLVERS["meta"])
    before = ctx.count(RE_LEADER)
    await chamber.select_option("senate")
    await wait_param(page, "chamber", "senate")
    deadline = asyncio.get_running_loop().time() + 12
    while ctx.count(RE_LEADER) <= before and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.2)
    chamber_requests = ctx.count(RE_LEADER) - before
    chamber_url = url_info(page.url)

    # The page early-returns to AsyncState while refetching, which unmounts the
    # controls; reload into a ready state before exercising the second select.
    await settle(page, ctx, "/leaderboard")
    leg = page.locator("#scope-legislature")
    if await leg.count() != 1:
        return skipped(
            "leaderboard ScopeControls legislature select not rendered", RESOLVERS["meta"]
        )
    before2 = ctx.count(RE_LEADER)
    await leg.select_option(year)
    await wait_param(page, "legislature", year)
    deadline = asyncio.get_running_loop().time() + 12
    while ctx.count(RE_LEADER) <= before2 and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.2)
    leg_requests = ctx.count(RE_LEADER) - before2
    leg_url = url_info(page.url)
    if (
        param(chamber_url, "chamber") != "senate"
        or param(leg_url, "legislature") != year
        or chamber_requests < 1
        or leg_requests < 1
    ):
        return failed(
            f"chamber=senate url={chamber_url['url']} requests+{chamber_requests}; "
            f"legislature={year} url={leg_url['url']} requests+{leg_requests}"
        )
    return passed(
        f"chamber select -> chamber=senate ({chamber_requests} leaderboard request(s)); "
        f"legislature select -> legislature={year} ({leg_requests} request(s)); "
        f"final url={leg_url['url']}",
        chamber_requests=chamber_requests,
        legislature_requests=leg_requests,
        final_url=leg_url["url"],
    )


async def c02_042(page: Any, ctx: Ctx) -> Outcome:
    """'Show top' limit select -> URL limit + scoped refetch + fewer rows."""
    await settle(page, ctx, "/leaderboard")
    # The limit select is the only one with a value="10" option (the
    # ScopeControls selects carry chamber names and legislature years).
    select = page.locator('select:has(option[value="10"])').first
    options = await select.locator("option").all_text_contents()
    if "10" not in [o.strip() for o in options]:
        return skipped("leaderboard limit select has no '10' option", RESOLVERS["leaderboard"])
    initial_rows = await page.locator("table tbody tr").count()
    before = ctx.count(RE_LEADER)
    await select.select_option("10")
    await wait_param(page, "limit", "10")
    deadline = asyncio.get_running_loop().time() + 12
    while ctx.count(RE_LEADER) <= before and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.2)
    await page.wait_for_timeout(800)
    info = url_info(page.url)
    after_rows = await page.locator("table tbody tr").count()
    requests = ctx.count(RE_LEADER) - before
    if param(info, "limit") != "10" or requests < 1 or after_rows > 10:
        return failed(
            f"limit select: url={info['url']}; requests+{requests}; rows {initial_rows}->{after_rows}"
        )
    return passed(
        f"limit select 20->10: url limit={param(info, 'limit')}, leaderboard request+{requests}, "
        f"visible rows {initial_rows}->{after_rows} (<=10)",
        rows_before=initial_rows,
        rows_after=after_rows,
        requests=requests,
    )


async def c02_043(page: Any, ctx: Ctx) -> Outcome:
    data, err = ctx.get("/api/analytics/switch-leaderboard?limit=20")
    rows = (data or {}).get("data") or [] if not err else []
    if not rows or not rows[0].get("person_id"):
        return skipped(f"leaderboard person id unavailable: {err}", RESOLVERS["leaderboard"])
    entry = rows[0]
    await settle(page, ctx, "/leaderboard")
    link = page.locator(f'a[href*="/person/{entry["person_id"]}"]').first
    if await link.count() == 0:
        return skipped("leaderboard person link not rendered", RESOLVERS["leaderboard"])
    return await click_person_link(page, link, entry.get("name") or "row")


async def c02_044(page: Any, ctx: Ctx) -> Outcome:
    """External methodology anchor: click opens a popup at the exact href."""
    expected = "https://github.com/nedaktov-ops/parlament-deschis/blob/main/docs/METHODOLOGY.md"
    await settle(page, ctx, "/leaderboard")
    anchor = page.locator(f'a[href="{expected}"]').first
    if await anchor.count() == 0:
        return skipped("methodology anchor not rendered", RESOLVERS["browser"])
    href = await anchor.get_attribute("href")
    target = await anchor.get_attribute("target")
    rel = await anchor.get_attribute("rel")
    context = page.context
    route_pattern = re.compile(r"https://github\.com/")

    async def fulfill(route: Any) -> None:
        await route.fulfill(
            status=200, content_type="text/html", body="<html><title>methodology</title></html>"
        )

    await context.route(route_pattern, fulfill)
    popup = None
    try:
        async with page.expect_popup(timeout=15_000) as popup_info:
            await anchor.click()
        popup = await popup_info.value
        observed = ""
        try:
            await popup.wait_for_url(expected, timeout=15_000)
            observed = popup.url
        except Exception:  # noqa: BLE001 - fall back to whatever URL committed
            observed = popup.url
    except Exception as exc:  # noqa: BLE001 - recorded as a FAIL finding
        return failed(
            f"methodology anchor click did not yield a popup: {type(exc).__name__}: {str(exc)[:250]}"
        )
    finally:
        if popup is not None:
            try:
                await popup.close()
            except Exception:  # noqa: BLE001
                pass
        await context.unroute(route_pattern, fulfill)
    if observed != expected or target != "_blank" or "noreferrer" not in (rel or ""):
        return failed(f"anchor href={href} target={target} rel={rel}; popup url={observed}")
    return passed(
        f"anchor '{expected}' (target={target}, rel={rel}) clicked -> popup navigated to {observed}",
        popup_url=observed,
        target=target,
        rel=rel,
    )


# --- C02: CoverageView -----------------------------------------------------


async def c02_045(page: Any, ctx: Ctx) -> Outcome:
    return await retry_case(
        page,
        ctx,
        path="/coverage",
        pattern=RE_DIM,
        description="C02-045 coverage.refetch()+dimensions.refetch() retry",
        expect=[RE_DIM, RE_COVDET],
        after=after_rows,
    )


async def c02_046(page: Any, ctx: Ctx) -> Outcome:
    """Coverage chamber + legislature ScopeControls filter the visible matrix."""
    data, err = ctx.get("/api/coverage/detailed")
    rows = data if (not err and isinstance(data, list)) else []
    if not rows:
        return skipped(f"coverage matrix unavailable: {err}", RESOLVERS["coverage"])
    chamber = "deputies" if any(r.get("chamber") == "deputies" for r in rows) else "senate"
    year = next(
        (
            r.get("legislature")
            for r in rows
            if r.get("chamber") == chamber and r.get("legislature")
        ),
        None,
    )
    if not year:
        return skipped("no legislature in live coverage matrix", RESOLVERS["coverage"])
    await settle(page, ctx, "/coverage")
    sel = page.locator("#scope-chamber")
    if await sel.count() != 1:
        return skipped("coverage chamber select not rendered", RESOLVERS["coverage"])
    count_before = await page.locator("table tbody tr").count()
    await sel.select_option(chamber)
    await wait_param(page, "chamber", chamber)
    await wait_error_cleared(page)
    await page.wait_for_timeout(800)
    count_chamber = await page.locator("table tbody tr").count()
    info_chamber = url_info(page.url)

    await settle(page, ctx, "/coverage")
    leg = page.locator("#scope-legislature")
    if await leg.count() != 1:
        return skipped("coverage legislature select not rendered", RESOLVERS["coverage"])
    await leg.select_option(str(year))
    await wait_param(page, "legislature", str(year))
    await wait_error_cleared(page)
    await page.wait_for_timeout(800)
    count_both = await page.locator("table tbody tr").count()
    info = url_info(page.url)
    if (
        param(info_chamber, "chamber") != chamber
        or param(info, "legislature") != str(year)
        or count_chamber >= count_before
        or count_both >= count_chamber
    ):
        return failed(
            f"coverage filters: chamber url={info_chamber['url']}, legislature url={info['url']}; "
            f"rows {count_before}->{count_chamber}->{count_both}"
        )
    return passed(
        f"chamber={chamber} -> rows {count_before}->{count_chamber} (url {info_chamber['url']}); "
        f"legislature={year} -> rows {count_chamber}->{count_both} (url {info['url']})",
        rows=[count_before, count_chamber, count_both],
        chamber_url=info_chamber["url"],
        final_url=info["url"],
    )


# --- C02: InstitutionalView ------------------------------------------------


async def c02_047(page: Any, ctx: Ctx) -> Outcome:
    """Native date input -> replace-URL navigate + both as_of-scoped refetches."""
    await settle(page, ctx, "/institutional")
    field = page.locator("#institutional-as-of")
    if await field.count() != 1:
        return skipped("institutional date input not rendered", RESOLVERS["browser"])
    current = await field.input_value()
    chosen = "2024-01-01" if current != "2024-01-01" else "2020-01-01"
    before_committees = ctx.count(RE_LIST)
    before_cross = ctx.count(RE_CROSS)
    title_before = await page.title()
    await field.fill(chosen)
    await field.dispatch_event("change")
    await wait_param(page, "date", chosen)
    deadline = asyncio.get_running_loop().time() + 12
    while (
        ctx.count(RE_LIST) <= before_committees or ctx.count(RE_CROSS) <= before_cross
    ) and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.2)
    await page.wait_for_timeout(600)
    info = url_info(page.url)
    d_committees = ctx.count(RE_LIST) - before_committees
    d_cross = ctx.count(RE_CROSS) - before_cross
    urls = [u for u in ctx.requests if ("as_of=" + chosen) in u]
    if d_committees < 1 or d_cross < 1 or param(info, "date") != chosen or not urls:
        return failed(
            f"date {current}->{chosen}: url={info['url']}; committees+{d_committees}; "
            f"cross-chamber+{d_cross}; as_of urls={urls[:4]}"
        )
    return passed(
        f"date input {current}->{chosen}: URL date={param(info, 'date')} (title '{title_before}'"
        f"->'{await page.title()}'); committees request+{d_committees}, cross-chamber+{d_cross}; "
        f"e.g. {urls[-1][:160]}",
        chosen_date=chosen,
        committees_requests=d_committees,
        cross_requests=d_cross,
        url=info["url"],
    )


async def c02_048(page: Any, ctx: Ctx) -> Outcome:
    return await retry_case(
        page,
        ctx,
        path="/institutional",
        pattern=RE_LIST,
        description="C02-048 committees.refetch() retry",
        expect=[RE_LIST],
        after=after_committee_names,
    )


async def c02_049(page: Any, ctx: Ctx) -> Outcome:
    return await retry_case(
        page,
        ctx,
        path="/institutional",
        pattern=RE_CROSS,
        description="C02-049 crossChamber.refetch() retry",
        expect=[RE_CROSS],
        after=after_rows,
    )


# --- C02: SenateHistory ----------------------------------------------------


async def c02_050(page: Any, ctx: Ctx) -> Outcome:
    """Senate-history legislature filter (client-side rows + URL scope)."""
    data, err = ctx.get("/api/coverage/detailed")
    senate_years = (
        sorted(
            {
                str(r.get("legislature"))
                for r in data
                if r.get("chamber") == "senate" and r.get("legislature")
            }
        )
        if not err and isinstance(data, list)
        else []
    )
    if len(senate_years) < 2:
        return skipped(f"senate legislatures unavailable: {err}", RESOLVERS["senate"])
    chosen = senate_years[1]
    await settle(page, ctx, "/senate-history")
    sel = page.locator("#scope-legislature")
    if await sel.count() != 1:
        return skipped("senate-history legislature select not rendered", RESOLVERS["senate"])
    count_before = await page.locator("table tbody tr").count()
    await sel.select_option(chosen)
    await wait_param(page, "legislature", chosen)
    await wait_error_cleared(page)
    await page.wait_for_timeout(700)
    count_after = await page.locator("table tbody tr").count()
    info = url_info(page.url)
    row_years = await page.locator("table tbody tr th").all_text_contents()
    bad = [y for y in row_years if y.strip() not in (chosen, "—")]
    if param(info, "legislature") != chosen or bad or count_after >= count_before:
        return failed(
            f"url={info['url']}; rows {count_before}->{count_after}; rows with other years={bad[:5]}"
        )
    return passed(
        f"legislature select -> legislature={chosen} in URL; senate rows {count_before}->"
        f"{count_after}, all showing the chosen legislature",
        rows_before=count_before,
        rows_after=count_after,
        url=info["url"],
    )


async def c02_051(page: Any, ctx: Ctx) -> Outcome:
    return await retry_case(
        page,
        ctx,
        path="/senate-history",
        pattern=RE_COVDET,
        description="C02-051 senate coverage.refetch() retry",
        expect=[RE_COVDET],
        after=after_rows,
    )


# --- C02: LegislatureDetail ------------------------------------------------


async def c02_052(page: Any, ctx: Ctx) -> Outcome:
    return await retry_case(
        page,
        ctx,
        path="/legislature/2024",
        pattern=RE_META,
        description="C02-052 meta.refetch() retry",
        expect=[RE_META],
        after=after_h1,
    )


async def c02_053(page: Any, ctx: Ctx) -> Outcome:
    return await retry_case(
        page,
        ctx,
        path="/legislature/2024",
        pattern=RE_CHAMBER,
        description="C02-053 chamber.refetch() retry",
        expect=[RE_CHAMBER],
        after=after_generic,
    )


async def c02_054(page: Any, ctx: Ctx) -> Outcome:
    return await retry_case(
        page,
        ctx,
        path="/legislature/2024",
        pattern=RE_MOVEMENTS,
        description="C02-054 movements.refetch() retry",
        expect=[RE_MOVEMENTS],
        after=after_generic,
    )


async def c02_055(page: Any, ctx: Ctx) -> Outcome:
    """Movement row button -> /person/$id (id from the page's own live query)."""
    await settle(page, ctx, "/legislature/2024")
    await wait_error_cleared(page)
    captured = [u for u in ctx.requests if RE_MOVEMENTS.search(u)]
    if not captured:
        return skipped("legislature movements request not observed", RESOLVERS["movement"])
    path = urllib.parse.urlsplit(captured[-1]).path
    query = urllib.parse.urlsplit(captured[-1]).query
    payload, err = ctx.get(path + ("?" + query if query else ""))
    events = payload if not err and isinstance(payload, list) else []
    usable = [e for e in events[:20] if (e.get("person") or {}).get("id")]
    if not usable:
        return skipped(
            f"no movement with person.id in the first 20 rows: {err}", RESOLVERS["movement"]
        )
    event = usable[0]
    pid = event["person"]["id"]
    name = event["person"].get("name") or ""
    button = page.locator(
        '[role="region"][aria-label*="ovement"] button', has_text=re.compile(re.escape(name))
    ).first
    if await button.count() == 0:
        button = page.get_by_role("button", name=re.compile(re.escape(name))).first
    if await button.count() == 0:
        return skipped(f"movement button for '{name}' not rendered", RESOLVERS["movement"])
    if await button.is_disabled():
        return failed(f"movement button for '{name}' is disabled but payload has person.id={pid}")
    result = await click_person_button(page, button, pid, name)
    result.extra.update(person_id=pid, movement_id=event.get("id"), movement_type=event.get("type"))
    return result


# --- C02: ScopeControls shared definitions (validated on /committees) ------


async def c02_056(page: Any, ctx: Ctx) -> Outcome:
    """ScopeControls date input (showDate) on /committees -> URL + as_of refetch."""
    await settle(page, ctx, "/committees")
    field = page.locator("#scope-date")
    if await field.count() != 1:
        return skipped("showDate ScopeControls date input not rendered", RESOLVERS["meta"])
    current = await field.input_value()
    chosen = "2024-01-01" if current != "2024-01-01" else "2020-01-01"
    before_list = ctx.count(RE_LIST)
    before_control = ctx.count(RE_CONTROL)
    await field.fill(chosen)
    await field.dispatch_event("change")
    await wait_param(page, "date", chosen)
    deadline = asyncio.get_running_loop().time() + 12
    while (
        ctx.count(RE_LIST) <= before_list or ctx.count(RE_CONTROL) <= before_control
    ) and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.2)
    info = url_info(page.url)
    dl = ctx.count(RE_LIST) - before_list
    dc = ctx.count(RE_CONTROL) - before_control
    as_of_urls = [u for u in ctx.requests if "as_of=" + chosen in u]
    if param(info, "date") != chosen or dl < 1 or dc < 1 or not as_of_urls:
        return failed(
            f"date {current}->{chosen}: url={info['url']}, list+{dl}, control+{dc}, "
            f"as_of urls={as_of_urls[:3]}"
        )
    return passed(
        f"#scope-date {current}->{chosen}: URL date={param(info, 'date')}; committee list+{dl}, "
        f"control+{dc} requests; e.g. {as_of_urls[-1][:150]}",
        chosen_date=chosen,
        list_requests=dl,
        control_requests=dc,
    )


async def c02_057(page: Any, ctx: Ctx) -> Outcome:
    """ScopeControls chamber select (showChamber) filters the committee list."""
    data, err = ctx.get(f"/api/committees?as_of={ctx.today}")
    expected = (
        len([c for c in data if c.get("chamber") == "senate"])
        if not err and isinstance(data, list)
        else 0
    )
    await settle(page, ctx, "/committees")
    sel = page.locator("#scope-chamber")
    if await sel.count() != 1:
        return skipped("showChamber ScopeControls select not rendered", RESOLVERS["meta"])
    before = await page.locator("button[aria-expanded]").count()
    await sel.select_option("senate")
    await wait_param(page, "chamber", "senate")
    await page.wait_for_timeout(700)
    after = await page.locator("button[aria-expanded]").count()
    info = url_info(page.url)
    if param(info, "chamber") != "senate" or after == before:
        return failed(
            f"chamber select: url={info['url']}; committee cards {before}->{after}; "
            f"API senate committees={expected}"
        )
    return passed(
        f"#scope-chamber -> chamber=senate in URL; committee cards {before}->{after} "
        f"(API senate committees={expected})",
        cards_before=before,
        cards_after=after,
        api_expected=expected,
    )


async def c02_058(page: Any, ctx: Ctx) -> Outcome:
    """ScopeControls legislature select (showLegislature) -> URL + control refetch."""
    meta, err = ctx.get("/api/meta")
    years = sorted((meta or {}).get("legislatures", {}).keys()) if not err else []
    if not years:
        return skipped(f"legislature options unavailable: {err}", RESOLVERS["meta"])
    chosen = years[-2] if len(years) > 1 else years[0]
    await settle(page, ctx, "/committees")
    sel = page.locator("#scope-legislature")
    if await sel.count() != 1:
        return skipped("showLegislature ScopeControls select not rendered", RESOLVERS["meta"])
    before = ctx.count(RE_CONTROL)
    await sel.select_option(chosen)
    await wait_param(page, "legislature", chosen)
    deadline = asyncio.get_running_loop().time() + 12
    while ctx.count(RE_CONTROL) <= before and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.2)
    info = url_info(page.url)
    d = ctx.count(RE_CONTROL) - before
    scoped = [u for u in ctx.requests if "legislature=" + chosen in u]
    if param(info, "legislature") != chosen or d < 1 or not scoped:
        return failed(
            f"legislature select -> {chosen}: url={info['url']}, control+{d}, scoped urls={scoped[:3]}"
        )
    return passed(
        f"#scope-legislature -> legislature={chosen} in URL; committee-control request+{d}; "
        f"e.g. {scoped[-1][:150]}",
        chosen_legislature=chosen,
        control_requests=d,
    )


CASES: list[dict[str, Any]] = [
    {
        "id": "C03-015",
        "line": "frontend/src/pages/Committees.tsx:33-40",
        "action": "expand a committee and click a member row's /person/$id link",
        "expected": "client-side navigation to /person/<live person_id> with a title change",
        "fn": c03_015,
    },
    {
        "id": "C03-016",
        "line": "frontend/src/pages/Committees.tsx:96-118",
        "action": "click the committee card button twice (expand, then collapse)",
        "expected": "aria-expanded false->true->false, a member request on expand, disclosure region added/removed",
        "fn": c03_016,
    },
    {
        "id": "C03-017",
        "line": "frontend/src/pages/Committees.tsx:344-351",
        "action": "open the all-chairs table and click a chair's /person/$id link",
        "expected": "client-side navigation to /person/<live chair_person_id> with a title change",
        "fn": c03_017,
    },
    {
        "id": "C03-018",
        "line": "frontend/src/pages/Committees.tsx:318-321",
        "action": "click the native <summary> 'Show all chairs' twice",
        "expected": "details.open false->true->false with the chairs table visible while open",
        "fn": c03_018,
    },
    {
        "id": "C03-019",
        "line": "frontend/src/pages/Committees.tsx:122-129",
        "action": "force a member fetch error, then click its inline Retry",
        "expected": "a new /api/committees/<id>/members request fires and the error state clears",
        "fn": c03_019,
    },
    {
        "id": "C03-020",
        "line": "frontend/src/pages/Committees.tsx:365-372",
        "action": "force a control-index fetch error, then click its inline Retry",
        "expected": "a new committee-control request fires and the error state clears",
        "fn": c03_020,
    },
    {
        "id": "C03-021",
        "line": "frontend/src/pages/Committees.tsx:377-384",
        "action": "force a committee-list fetch error, then click its inline Retry",
        "expected": "a new /api/committees?as_of request fires and the error state clears",
        "fn": c03_021,
    },
    {
        "id": "C02-040",
        "line": "frontend/src/pages/SwitchLeaderboard.tsx:53",
        "action": "force a leaderboard fetch error, then click the full-page Retry",
        "expected": "a new switch-leaderboard request fires and the error state clears",
        "fn": c02_040,
    },
    {
        "id": "C02-041",
        "line": "frontend/src/pages/SwitchLeaderboard.tsx:100",
        "action": "change the ScopeControls chamber and legislature selects",
        "expected": "chamber/legislature written to the URL with a leaderboard refetch for each",
        "fn": c02_041,
    },
    {
        "id": "C02-042",
        "line": "frontend/src/pages/SwitchLeaderboard.tsx:103-113",
        "action": "change the 'Show top' limit select from 20 to 10",
        "expected": "URL limit=10, a scoped leaderboard request, and at most 10 visible rows",
        "fn": c02_042,
    },
    {
        "id": "C02-043",
        "line": "frontend/src/pages/SwitchLeaderboard.tsx:160-167",
        "action": "click a leaderboard row's /person/$id link",
        "expected": "client-side navigation to /person/<live person_id> with a title change",
        "fn": c02_043,
    },
    {
        "id": "C02-044",
        "line": "frontend/src/pages/SwitchLeaderboard.tsx:235-242",
        "action": "click the external 'Full methodology' anchor",
        "expected": "target=_blank popup navigates to the exact GitHub methodology URL",
        "fn": c02_044,
    },
    {
        "id": "C02-045",
        "line": "frontend/src/pages/CoverageView.tsx:116-119",
        "action": "force a coverage-dimensions fetch error, then click full-page Retry",
        "expected": "both coverage/detailed and coverage/dimensions refetch and the error clears",
        "fn": c02_045,
    },
    {
        "id": "C02-046",
        "line": "frontend/src/pages/CoverageView.tsx:128",
        "action": "change the CoverageView chamber and legislature selects",
        "expected": "chamber/legislature in the URL and the visible matrix rows narrowed",
        "fn": c02_046,
    },
    {
        "id": "C02-047",
        "line": "frontend/src/pages/InstitutionalView.tsx:45-56",
        "action": "fill the #institutional-as-of date input with a new date",
        "expected": "URL date changes and both committees/cross-chamber as_of refetches fire",
        "fn": c02_047,
    },
    {
        "id": "C02-048",
        "line": "frontend/src/pages/InstitutionalView.tsx:65",
        "action": "force the institutional committees fetch to fail, then click Retry",
        "expected": "a new /api/committees?as_of request fires and the error clears",
        "fn": c02_048,
    },
    {
        "id": "C02-049",
        "line": "frontend/src/pages/InstitutionalView.tsx:90",
        "action": "force the cross-chamber fetch to fail, then click Retry",
        "expected": "a new cross-chamber request fires and the error clears",
        "fn": c02_049,
    },
    {
        "id": "C02-050",
        "line": "frontend/src/pages/SenateHistory.tsx:75",
        "action": "change the SenateHistory legislature select",
        "expected": "legislature in the URL and only rows for that legislature visible",
        "fn": c02_050,
    },
    {
        "id": "C02-051",
        "line": "frontend/src/pages/SenateHistory.tsx:66",
        "action": "force the senate coverage fetch to fail, then click Retry",
        "expected": "a new /api/coverage/detailed request fires and the error clears",
        "fn": c02_051,
    },
    {
        "id": "C02-052",
        "line": "frontend/src/pages/LegislatureDetail.tsx:66",
        "action": "force the meta fetch to fail, then click Retry",
        "expected": "a new /api/meta request fires and the legislature h1 renders",
        "fn": c02_052,
    },
    {
        "id": "C02-053",
        "line": "frontend/src/pages/LegislatureDetail.tsx:158",
        "action": "force the chamber fetch to fail, then click its inline Retry",
        "expected": "a new /api/chamber request fires and the error clears",
        "fn": c02_053,
    },
    {
        "id": "C02-054",
        "line": "frontend/src/pages/LegislatureDetail.tsx:181",
        "action": "force the movements fetch to fail, then click its inline Retry",
        "expected": "a new /api/movements request fires and the error clears",
        "fn": c02_054,
    },
    {
        "id": "C02-055",
        "line": "frontend/src/pages/LegislatureDetail.tsx:191-213",
        "action": "click an enabled recent-movement row button",
        "expected": "client-side navigation to /person/<live m.person.id> with a title change",
        "fn": c02_055,
    },
    {
        "id": "C02-056",
        "line": "frontend/src/components/ScopeControls.tsx:32-34",
        "action": "fill the showDate #scope-date input on /committees",
        "expected": "URL date changes and committee list + control requests refetch with that as_of",
        "fn": c02_056,
    },
    {
        "id": "C02-057",
        "line": "frontend/src/components/ScopeControls.tsx:40-45",
        "action": "change the showChamber #scope-chamber select on /committees",
        "expected": "URL chamber=senate and the visible committee cards narrowed to that chamber",
        "fn": c02_057,
    },
    {
        "id": "C02-058",
        "line": "frontend/src/components/ScopeControls.tsx:51-55",
        "action": "change the showLegislature #scope-legislature select on /committees",
        "expected": "URL legislature changes and a scoped committee-control request fires",
        "fn": c02_058,
    },
]


async def run_case(browser: Any, case: dict[str, Any], ctx: Ctx) -> dict[str, Any]:
    element_id = case["id"]
    ctx.current_id = element_id
    ctx.current_page = "initial"
    ctx.test_induced = False
    ctx.requests = []
    console_start = len(ctx.console)
    page = await browser.new_page()
    page.set_default_timeout(25_000)
    attach_listeners(page, ctx)
    try:
        outcome: Outcome = await case["fn"](page, ctx)
    except Exception as exc:  # noqa: BLE001 - harness error recorded as a FAIL finding
        outcome = failed(f"harness exception {type(exc).__name__}: {str(exc)[:300]}")
    before_url = page.url
    shot = OUT_DIR / f"v06-shot-{element_id}.png"
    try:
        await page.screenshot(path=str(shot), full_page=False, timeout=15_000)
    except Exception:  # noqa: BLE001 - evidence screenshot is best-effort
        pass
    finally:
        await page.close()

    evidence_path = OUT_DIR / f"v06-evidence-{element_id}.json"
    evidence = {
        "element_id": element_id,
        "source_file_line": case["line"],
        "served_head": ctx.head,
        "base": BASE,
        "action": case["action"],
        "expected": case["expected"],
        "observed": outcome.observed,
        "verdict": outcome.verdict,
        "resolver": outcome.resolver,
        "url_at_capture": before_url,
        "screenshot": str(shot) if shot.exists() else None,
        "api_requests": ctx.requests[-40:],
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


async def run_all(ctx: Ctx) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pw = None
    browser = None
    try:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(executable_path=BROWSER, args=["--no-sandbox"])
        only = {part.strip() for part in os.environ.get("V06_ONLY", "").split(",") if part.strip()}
        for case in CASES:
            if only and case["id"] not in only:
                continue
            rows.append(await run_case(browser, case, ctx))
    finally:
        if browser is not None:
            await browser.close()
        if pw is not None:
            await pw.stop()
    return rows


def test_v06_institutional_clickables() -> None:
    ctx = Ctx()
    rows: list[dict[str, Any]] = []
    try:
        rows = asyncio.run(run_all(ctx))
    finally:
        # Artifacts are written even if the harness itself raises.
        write_json(RESULTS_PATH, rows)
        write_json(
            CONSOLE_PATH,
            {
                "base": BASE,
                "browser": BROWSER,
                "served_head": ctx.head,
                "captured_at": now_iso(),
                "events": ctx.console,
                "counts": {
                    "total": len(ctx.console),
                    "console_error": sum(e["kind"] == "console.error" for e in ctx.console),
                    "pageerror": sum(e["kind"] == "pageerror" for e in ctx.console),
                    "test_induced": sum(1 for e in ctx.console if e["test_induced"]),
                    "unlabelled": sum(1 for e in ctx.console if not e["test_induced"]),
                },
            },
        )

    ids = [r["element_id"] for r in rows]
    assert len(rows) == 26, f"expected 26 element rows, got {len(rows)}"
    assert len(set(ids)) == len(ids), f"duplicate element IDs: {ids}"
    assert set(ids) == {c["id"] for c in CASES}, "assigned slice not completely executed"
    required = {
        "element_id",
        "source_file_line",
        "action",
        "expected_outcome",
        "observed_outcome",
        "status",
        "evidence_path",
    }
    for row in rows:
        assert required <= set(row), f"schema violation: {row.get('element_id')}"
        assert Path(row["evidence_path"]).exists(), f"missing evidence: {row['element_id']}"
    counts = {v: sum(r["verdict"] == v for r in rows) for v in ("PASS", "FAIL", "SKIP")}
    print("V-06 verdicts:", counts, "results:", RESULTS_PATH, "console:", CONSOLE_PATH)
    for row in rows:
        if row["verdict"] != "PASS":
            print(
                f"  {row['verdict']} {row['element_id']}: {row['observed'][:240]} "
                f"(resolver={row.get('resolver')})"
            )
    # A FAIL/SKIP is a finding with evidence, not a harness error; the fleet
    # supervisor triages it. Harness integrity (26 unique rows + evidence) is
    # what this gate asserts.
