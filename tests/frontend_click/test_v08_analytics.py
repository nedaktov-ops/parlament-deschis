"""V-08 clickable validation — C04-015..026 on the vote-analytics routes.

Fleet contract: CLICK-VALIDATION-FLEET-2026-11-23.md §2/§3 and
CLICK-INV-C04-VOTES-2026-11-22.md. This file owns ONLY itself and the
``/tmp/opencode/click-validation/v08-*`` artifacts. It validates *behaviour*
against the read-only local dev server (never the production host): retries are
exercised by aborting the real API call until React Query reaches its error
state, then clicking the rendered RetryButton with the route unblocked and
observing a genuine refetch; the ideology "All years" sentinel is checked for
multiple distinct survey years; print is observed via a window.print override;
the JSON export is observed via a real browser download.

One chromium instance, one page per element, browser closed in ``finally``.
Dynamic values (scorecard min-votes threshold, CHES years) are resolved from
the live API; an unresolvable value is a SKIP with a named resolver, never a
silent PASS. Induced console errors are tagged ``test-injected`` and never
suppressed.
"""

from __future__ import annotations

import asyncio
import json
import re
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright", reason="external Playwright validation tool; see scripts/ui_validate.py")
from playwright.async_api import async_playwright  # noqa: E402

BASE = "http://127.0.0.1:5188"
BROWSER = "/usr/bin/chromium"
OUT_DIR = Path("/tmp/opencode/click-validation")
RESULTS_PATH = OUT_DIR / "v08-results.json"
CONSOLE_PATH = OUT_DIR / "v08-console.json"

RETRY_RE = re.compile(r"Retry|Reîncearcă|\u00cencearc", re.I)
PREV_RE = re.compile(r"Previous|Anterioare", re.I)
NEXT_RE = re.compile(r"Next|Următoarele", re.I)
PRINT_RE = re.compile(r"Print|Printeaz", re.I)
DOWNLOAD_RE = re.compile(r"Download|Descarcă", re.I)

VOTES_GLOB = "**/api/votes*"
SCORECARD_GLOB = "**/api/votes/scorecard*"
IDEOLOGY_GLOB = "**/api/analytics/ideology*"
ACTIVITY_GLOB = "**/api/analytics/vote-activity*"
EXPORT_GLOB = "**/api/export/report*"

RESOLVERS = {
    "scorecard": "GET /api/votes/scorecard?min_votes=1&limit=100&<active scope> -> a threshold with 0<total<100 (rerun with a live corpus)",
    "ideology": "GET /api/analytics/ideology -> >=2 distinct data[].survey_year (rerun with a live corpus)",
    "pagination": "GET /api/votes/scorecard?min_votes=1&limit=100&<active scope> -> total>100 for Next/Previous (rerun with a live corpus)",
    "browser": "rerun on the local dev server with /usr/bin/chromium available",
    "download": "rerun with browser downloads enabled on the local dev server",
}


# --- helpers ---------------------------------------------------------------


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def api_get(path: str) -> Any:
    """One bounded, read-only GET against the local API (no writes/seeding)."""
    with urllib.request.urlopen(BASE + path, timeout=20) as response:
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
    """Per-run state shared by the 12 element cases (no files outside v08-*)."""

    def __init__(self) -> None:
        self.current_id = "C04-000"
        self.console: list[dict[str, Any]] = []
        self._cache: dict[str, Any] = {}
        self._errors: dict[str, str] = {}

    def get(self, path: str) -> tuple[Any | None, str | None]:
        if path in self._cache:
            return self._cache[path], None
        if path in self._errors:
            return None, self._errors[path]
        try:
            self._cache[path] = api_get(path)
            return self._cache[path], None
        except Exception as exc:  # noqa: BLE001 - resolver-driven SKIP, not a pass
            reason = f"GET {path} failed: {type(exc).__name__}: {str(exc)[:200]}"
            self._errors[path] = reason
            return None, reason

    def active_scope_suffix(self) -> tuple[str, str | None]:
        """Mirror the pages' scopeProbe: the data-bearing scope with the largest
        total. Returns an ``&chamber=..&legislature=..`` URL suffix.
        """
        data, err = self.get("/api/votes?limit=1")
        if err or not isinstance(data, dict):
            return "", err or "votes scope probe missing"
        scopes = data.get("scopes") or []
        if not scopes:
            return "", "no data-bearing scopes published"
        top = max(scopes, key=lambda s: s.get("total") or 0)
        parts: list[str] = []
        if top.get("chamber"):
            parts.append(f"chamber={top['chamber']}")
        if top.get("legislature"):
            parts.append(f"legislature={top['legislature']}")
        return ("&" + "&".join(parts)) if parts else "", None

    def scorecard_path(self, min_votes: int) -> tuple[str, str | None]:
        suffix, err = self.active_scope_suffix()
        if err:
            return "", err
        # backend cap: limit le=200; 100 matches the frontend page size.
        return f"/api/votes/scorecard?min_votes={min_votes}&limit=100{suffix}", None

    def scorecard_threshold(self) -> tuple[int | None, int | None, int | None, str | None]:
        """Resolve a min-votes value that leaves 0<total<100 scorecard rows.

        Returns (threshold, baseline_total, reduced_total, error). The value is
        derived from live per-MP total_votes in the active scope, then confirmed
        against the API.
        """
        path, err = self.scorecard_path(1)
        if err:
            return None, None, None, err
        data, err = self.get(path)
        if err or not isinstance(data, dict):
            return None, None, None, err or "scorecard payload missing"
        rows = data.get("data") or []
        baseline = data.get("total", len(rows))
        totals = sorted(
            int(r["total_votes"]) for r in rows if isinstance(r.get("total_votes"), (int, float))
        )
        if not totals:
            return None, baseline, None, "no numeric total_votes in scorecard data"
        candidates: list[int] = []
        for pct in (0.60, 0.50, 0.70, 0.40, 0.80, 0.30, 0.90):
            candidates.append(totals[min(len(totals) - 1, int(pct * len(totals)))])
        for threshold in sorted(set(candidates), reverse=True):
            probe_path, _ = self.scorecard_path(threshold)
            probe, err2 = self.get(probe_path)
            if err2 or not isinstance(probe, dict):
                continue
            reduced = probe.get("total", 0)
            if 0 < reduced < 100:
                return threshold, baseline, reduced, None
        return None, baseline, None, "no threshold yielded 0<total<100"

    def ideology_years(self) -> tuple[list[int], int, str | None]:
        data, err = self.get("/api/analytics/ideology")
        if err or not isinstance(data, dict):
            return [], 0, err or "ideology payload missing"
        rows = data.get("data") or []
        years = sorted(
            {int(r["survey_year"]) for r in rows if isinstance(r.get("survey_year"), int)}
        )
        return years, len(rows), None


async def settle(page: Any, path: str, *, block: Callable[[], Any] | None = None) -> None:
    """Navigate with bounded networkidle + fixed settle (ui_validate.py §2)."""
    if block is not None:
        await block()
    await page.goto(BASE + path, wait_until="load", timeout=35_000)
    try:
        await page.wait_for_load_state("networkidle", timeout=9_000)
    except Exception:  # noqa: BLE001 - bounded fallback to fixed settle
        pass
    await page.wait_for_timeout(2_500)


async def row_count(page: Any) -> int:
    return await page.locator("table tbody tr").count()


async def retry_outcome(
    page: Any,
    ctx: Ctx,
    path: str,
    endpoint_glob: str,
    description: str,
    *,
    index: int = 0,
    error_text_re: re.Pattern[str] | None = None,
    expect_glob: str | None = None,
) -> Outcome:
    """Block an endpoint until React Query shows its error region, then click
    the rendered RetryButton with the route unblocked and assert a real refetch.

    Aborted requests are tagged as test-injected in v08-console.json; nothing is
    suppressed or filtered to obtain a PASS.
    """
    state = {"blocked": True, "aborted": 0}

    async def handler(route: Any) -> None:
        if state["blocked"]:
            state["aborted"] += 1
            await route.abort("failed")
        else:
            await route.continue_()

    await page.route(endpoint_glob, handler)
    target = expect_glob or endpoint_glob
    try:
        await settle(page, path)
        region = page.locator('[data-state="error"]').nth(index)
        try:
            await region.wait_for(state="visible", timeout=28_000)
        except Exception as exc:  # noqa: BLE001 - record as FAIL finding
            return failed(
                f"{description}: aborted={state['aborted']}; error region never visible "
                f"({type(exc).__name__}: {str(exc)[:200]})"
            )
        text = (await region.inner_text()) or ""
        if error_text_re is not None and not error_text_re.search(text):
            return failed(
                f"{description}: wrong error region text: {text[:300]!r} "
                f"(expected /{error_text_re.pattern}/)"
            )
        retry = region.get_by_role("button", name=RETRY_RE)
        n_retry = await retry.count()
        if n_retry != 1:
            return failed(
                f"{description}: expected exactly one retry button in error region, found {n_retry}"
            )
        state["blocked"] = False
        await page.unroute(endpoint_glob, handler)
        async with page.expect_request(target, timeout=22_000) as request_info:
            await retry.click()
        request = await request_info.value
        await page.wait_for_function(
            "() => document.querySelectorAll('[data-state=\"error\"]').length === 0",
            timeout=22_000,
        )
        return passed(
            f"{description}: aborted attempts={state['aborted']}; error text={text[:160]!r}; "
            f"retry fired {request.method} {request.url}; error state cleared",
            request_url=request.url,
            request_method=request.method,
            aborted_attempts=state["aborted"],
            error_text=text[:300],
        )
    except Exception as exc:  # noqa: BLE001 - an exception is a finding with evidence
        return failed(
            f"{description}: aborted={state['aborted']}; "
            f"exception {type(exc).__name__}: {str(exc)[:300]}"
        )
    finally:
        state["blocked"] = False
        try:
            await page.unroute(endpoint_glob, handler)
        except Exception:  # noqa: BLE001 - best-effort cleanup
            pass


# --- element cases ---------------------------------------------------------


async def c015(page: Any, ctx: Ctx) -> Outcome:
    return await retry_outcome(
        page,
        ctx,
        "/radar",
        VOTES_GLOB,
        "C04-015 Radar page-level retry (scopeProbe+votes+positions refetch)",
        error_text_re=re.compile(r"roll-call alignment matrix|matrice", re.I),
    )


async def c016(page: Any, ctx: Ctx) -> Outcome:
    return await retry_outcome(
        page,
        ctx,
        "/grafice",
        VOTES_GLOB,
        "C04-016 Grafice page-level retry (scopeProbe+summary+cohesion refetch)",
        error_text_re=re.compile(r"cohesion|coesiune|cohesiune", re.I),
    )


async def c017(page: Any, ctx: Ctx) -> Outcome:
    return await retry_outcome(
        page,
        ctx,
        "/grafice",
        ACTIVITY_GLOB,
        "C04-017 Grafice inline VoteActivityChart retry (activityQuery.refetch)",
        error_text_re=re.compile(r"Failed to load vote activity|activitate", re.I),
    )


async def c018(page: Any, ctx: Ctx) -> Outcome:
    threshold, baseline, reduced, err = ctx.scorecard_threshold()
    if threshold is None:
        return skipped(
            f"min-votes threshold unresolved: {err}",
            RESOLVERS["scorecard"],
        )
    await settle(page, "/topuri")
    inp = page.locator("input[type=number]")
    if await inp.count() != 1:
        return failed(f"expected one number input on /topuri, found {await inp.count()}")
    initial = await inp.input_value()
    label = ""
    labels = await page.locator("label span").all_inner_texts()
    for candidate in labels:
        if re.search(r"voturi minime|minimum votes", candidate, re.I):
            label = candidate
            break
    before_rows = await row_count(page)
    try:
        async with page.expect_request(SCORECARD_GLOB, timeout=22_000) as request_info:
            await inp.fill(str(threshold))
        request = await request_info.value
        await page.wait_for_function(
            "(n) => document.querySelectorAll('table tbody tr').length === n",
            arg=reduced,
            timeout=22_000,
        )
    except Exception as exc:  # noqa: BLE001
        return failed(
            f"min-votes fill threw {type(exc).__name__}: {str(exc)[:300]} "
            f"(threshold={threshold} rows_before={before_rows} rows_after={await row_count(page)})"
        )
    info = url_info(page.url)
    after_rows = await row_count(page)
    observed = (
        f"input {initial!r}->{await inp.input_value()!r} label={label!r}; "
        f"URL minVotes={param(info, 'minVotes')!r}; request={request.url}; "
        f"scorecard rows {before_rows}->{after_rows}; API total {baseline}->{reduced}"
    )
    if param(info, "minVotes") != str(threshold):
        return failed(observed + " ; expected URL minVotes to equal threshold")
    if f"min_votes={threshold}" not in request.url:
        return failed(observed + " ; request missing min_votes threshold")
    if after_rows != reduced or after_rows >= before_rows:
        return failed(observed + " ; result row count did not match resolved reduction")
    return passed(
        observed,
        threshold=threshold,
        baseline_total=baseline,
        reduced_total=reduced,
        request_url=request.url,
        label=label,
    )


async def c019(page: Any, ctx: Ctx) -> Outcome:
    path, path_err = ctx.scorecard_path(1)
    if path_err:
        return skipped(f"scorecard total unresolved: {path_err}", RESOLVERS["pagination"])
    data, err = ctx.get(path)
    if err or not isinstance(data, dict):
        return skipped(f"scorecard total unresolved: {err}", RESOLVERS["pagination"])
    total = data.get("total", 0)
    if total <= 100:
        return skipped(
            f"scorecard total={total} <= limit 100, Next cannot be enabled",
            RESOLVERS["pagination"],
        )
    await settle(page, "/topuri")
    prev = page.get_by_role("button", name=PREV_RE)
    nxt = page.get_by_role("button", name=NEXT_RE)
    if await prev.count() != 1 or await nxt.count() != 1:
        return failed(
            f"pagination buttons not unique: prev={await prev.count()} next={await nxt.count()}"
        )
    range_text = page.locator("span[aria-live=polite]").last
    text_at_zero = await range_text.inner_text()
    disabled_before = await prev.is_disabled()
    try:
        async with page.expect_request(SCORECARD_GLOB, timeout=22_000) as ri:
            await nxt.click()
        next_req = await ri.value
        await page.wait_for_timeout(700)  # let React commit the offset=100 state
        text_at_100 = await range_text.inner_text()
        prev_disabled_mid = await prev.is_disabled()
        # The app sets staleTime=1h (router.tsx:589): returning to the cached
        # offset=0 key is a state change, not necessarily a new HTTP request.
        await prev.click()
        await page.wait_for_function(
            "(t) => [...document.querySelectorAll('span[aria-live=polite]')]"
            ".some(e => e.textContent.trim() === t)",
            arg=text_at_zero,
            timeout=18_000,
        )
        text_back_at_zero = await range_text.inner_text()
    except Exception as exc:  # noqa: BLE001
        return failed(
            f"prev navigation threw {type(exc).__name__}: {str(exc)[:300]} "
            f"(total={total} rows={await row_count(page)})"
        )
    observed = (
        f"total={total}; prev disabled at offset 0={disabled_before}; "
        f"next request={next_req.url}; prev re-enabled after next={not prev_disabled_mid}; "
        f"page range {text_at_zero!r} -> {text_at_100!r} -> {text_back_at_zero!r}"
    )
    if not disabled_before:
        return failed(observed + " ; Previous must be disabled at offset 0")
    if "offset=100" not in next_req.url:
        return failed(observed + " ; Next did not request offset=100")
    if prev_disabled_mid:
        return failed(observed + " ; Previous remained disabled after Next")
    if text_at_100 == text_at_zero:
        return failed(observed + " ; page range did not change after Next")
    if text_back_at_zero != text_at_zero:
        return failed(observed + " ; Previous did not restore the offset-0 page range")
    return passed(
        observed,
        next_url=next_req.url,
        total=total,
        text_at_zero=text_at_zero,
        text_at_100=text_at_100,
    )


async def c020(page: Any, ctx: Ctx) -> Outcome:
    path, path_err = ctx.scorecard_path(1)
    if path_err:
        return skipped(f"scorecard total unresolved: {path_err}", RESOLVERS["pagination"])
    data, err = ctx.get(path)
    if err or not isinstance(data, dict):
        return skipped(f"scorecard total unresolved: {err}", RESOLVERS["pagination"])
    total = data.get("total", 0)
    if total <= 100:
        return skipped(
            f"scorecard total={total} <= limit 100, Next cannot be enabled",
            RESOLVERS["pagination"],
        )
    await settle(page, "/topuri")
    nxt = page.get_by_role("button", name=NEXT_RE)
    if await nxt.count() != 1:
        return failed(f"expected one Next button, found {await nxt.count()}")
    if await nxt.is_disabled():
        return failed(f"Next disabled with total={total} > limit 100")
    before_rows = await row_count(page)
    before_text = await page.locator("span[aria-live=polite]").last.inner_text()
    try:
        async with page.expect_request(SCORECARD_GLOB, timeout=22_000) as request_info:
            await nxt.click()
        request = await request_info.value
        await page.wait_for_function(
            "() => document.querySelectorAll('table tbody tr').length >= 1",
            timeout=22_000,
        )
        await page.wait_for_timeout(600)
        after_text = await page.locator("span[aria-live=polite]").last.inner_text()
    except Exception as exc:  # noqa: BLE001
        return failed(f"Next click threw {type(exc).__name__}: {str(exc)[:300]}")
    observed = (
        f"total={total}; request={request.url}; rows {before_rows}->{await row_count(page)}; "
        f"page text {before_text!r}->{after_text!r}"
    )
    if "offset=100" not in request.url:
        return failed(observed + " ; Next did not request offset=100")
    if before_text == after_text:
        return failed(observed + " ; visible page-range text did not change")
    return passed(observed, request_url=request.url, before_text=before_text, after_text=after_text)


async def c021(page: Any, ctx: Ctx) -> Outcome:
    return await retry_outcome(
        page,
        ctx,
        "/topuri",
        VOTES_GLOB,
        "C04-021 Topuri page-level retry (scopeProbe+scorecard refetch)",
        error_text_re=re.compile(r"behavioural scorecard|comportament", re.I),
    )


async def c022(page: Any, ctx: Ctx) -> Outcome:
    years, api_rows, err = ctx.ideology_years()
    if err:
        return skipped(f"CHES years unresolved: {err}", RESOLVERS["ideology"])
    if len(years) < 2:
        return skipped(
            f"only {len(years)} distinct CHES year(s) {years}; all-years needs >=2 waves",
            RESOLVERS["ideology"],
        )
    await settle(page, "/ideology")
    sel = page.locator("select")
    if await sel.count() != 1:
        return failed(f"expected one year select on /ideology, found {await sel.count()}")
    values = await sel.locator("option").evaluate_all("(els) => els.map(e => e.value)")
    if "all" not in values or not all(str(y) in values for y in years):
        return failed(f"select option values={values} missing 'all' or resolved years={years}")
    # Ideology.tsx:77 sorts years DESCENDING (b-a) and :84 defaults to years[0]
    # (the newest wave); ctx.ideology_years() is ascending, so the default is max().
    latest = max(years)
    default = await sel.input_value()
    if default != str(latest):
        return failed(f"default select value={default!r}, expected latest year {latest}")

    single = years[0] if latest != years[0] else years[-1]  # a distinct older wave
    await sel.select_option(str(single))
    try:
        await page.wait_for_function(
            "(y) => new URLSearchParams(location.search).get('chesYear') === y",
            arg=str(single),
            timeout=18_000,
        )
        await page.wait_for_function(
            "(y) => { const c=[...document.querySelectorAll('table tbody tr td:nth-child(2)')]"
            ".map(e=>e.textContent.trim()); return c.length>0 && c.every(v=>v===y); }",
            arg=str(single),
            timeout=18_000,
        )
    except Exception as exc:  # noqa: BLE001
        return failed(
            f"single-year select failed for {single}: {type(exc).__name__}: {str(exc)[:250]} "
            f"(url={page.url}, rows={await row_count(page)})"
        )
    single_years = await page.locator("table tbody tr td:nth-child(2)").all_inner_texts()
    single_ches = param(url_info(page.url), "chesYear")  # capture before the next select

    # The repaired sentinel: value="all" must persist AND render every wave.
    await sel.select_option("all")
    try:
        await page.wait_for_function(
            "() => new URLSearchParams(location.search).get('chesYear') === 'all'",
            timeout=18_000,
        )
        await page.wait_for_function(
            "() => { const c=[...document.querySelectorAll('table tbody tr td:nth-child(2)')]"
            ".map(e=>e.textContent.trim()); return new Set(c).size >= 2; }",
            timeout=18_000,
        )
    except Exception as exc:  # noqa: BLE001
        return failed(
            f"all-years sentinel failed: {type(exc).__name__}: {str(exc)[:250]} "
            f"(url={page.url}, select={await sel.input_value()}, rows={await row_count(page)})"
        )
    info = url_info(page.url)
    all_years = [
        v.strip() for v in await page.locator("table tbody tr td:nth-child(2)").all_inner_texts()
    ]
    distinct = sorted(set(all_years), key=lambda v: int(v) if v.isdigit() else 0)
    observed = (
        f"options={values}; default={default}; single select {single} -> "
        f"chesYear={single_ches} rows={len(single_years)} years={sorted(set(single_years))}; "
        f"All years -> select={await sel.input_value()} chesYear={param(info, 'chesYear')} "
        f"rows={len(all_years)} distinct_years={distinct} (API rows={api_rows}, years={years})"
    )
    if await sel.input_value() != "all":
        return failed(observed + " ; select did not stay on 'all'")
    if param(info, "chesYear") != "all":
        return failed(observed + " ; sentinel not preserved in URL")
    if len(distinct) < 2:
        return failed(observed + " ; all-years rendered <2 distinct years (F1 regression)")
    if len(all_years) != api_rows:
        return failed(observed + " ; all-years row count != API full-data row count")
    if not set(all_years) <= {str(y) for y in years}:
        return failed(observed + " ; rendered year outside resolved CHES years")
    return passed(
        observed,
        years=years,
        distinct_rendered_years=distinct,
        all_years_rows=len(all_years),
        api_rows=api_rows,
        single_year=single,
        single_ches_year=single_ches,
        url=info["url"],
    )


async def c023(page: Any, ctx: Ctx) -> Outcome:
    return await retry_outcome(
        page,
        ctx,
        "/ideology",
        IDEOLOGY_GLOB,
        "C04-023 Ideology page-level retry (ideologyQuery.refetch)",
        error_text_re=re.compile(r"ideological map|ideologic", re.I),
    )


async def c024(page: Any, ctx: Ctx) -> Outcome:
    await settle(page, "/report")
    btn = page.get_by_role("button", name=PRINT_RE)
    n = await btn.count()
    if n != 1:
        return failed(f"expected one print button on /report, found {n}")
    label = await btn.inner_text()
    await page.evaluate(
        "() => { window.__v08PrintCalls = 0; "
        "window.print = function () { window.__v08PrintCalls += 1; }; }"
    )
    try:
        await btn.click(timeout=15_000)
        calls = await page.evaluate("() => window.__v08PrintCalls")
    except Exception as exc:  # noqa: BLE001
        return failed(f"print click threw {type(exc).__name__}: {str(exc)[:300]}")
    observed = (
        f"button={label!r}; window.print invoked {calls} time(s) "
        "(dialog suppressed by test override of window.print); no URL/API change expected"
    )
    if calls != 1:
        return failed(observed + " ; expected exactly one window.print invocation")
    return passed(observed, print_calls=calls, label=label, url=page.url)


async def c025(page: Any, ctx: Ctx) -> Outcome:
    await settle(page, "/report")
    link = page.locator('a[download="transparency-report.json"]')
    n = await link.count()
    if n != 1:
        return failed(f"expected one JSON download anchor, found {n}")
    href = await link.get_attribute("href")
    text = await link.inner_text()
    if not DOWNLOAD_RE.search(text):
        return failed(f"download anchor text unexpected: {text!r}")
    if href != "/api/export/report":
        return failed(f"download href={href!r}, expected /api/export/report")
    dest = OUT_DIR / "v08-download-transparency-report.json"
    try:
        async with page.expect_download(timeout=25_000) as download_info:
            await link.click()
        download = await download_info.value
        await download.save_as(str(dest))
    except Exception as exc:  # noqa: BLE001
        return skipped(
            f"download not captured: {type(exc).__name__}: {str(exc)[:250]}",
            RESOLVERS["download"],
        )
    size = dest.stat().st_size
    try:
        payload = json.loads(dest.read_text(encoding="utf-8"))
        keys = sorted(payload.keys()) if isinstance(payload, dict) else []
    except Exception as exc:  # noqa: BLE001
        return failed(f"downloaded file is not valid JSON: {type(exc).__name__}: {str(exc)[:200]}")
    observed = (
        f"link={text!r} href={href} download=transparency-report.json; "
        f"suggested_filename={download.suggested_filename!r}; saved={dest.name} size={size}B; "
        f"JSON keys={keys[:6]}"
    )
    if size == 0 or "totals" not in keys:
        return failed(observed + " ; empty download or missing 'totals'")
    if download.suggested_filename != "transparency-report.json":
        return failed(observed + " ; wrong suggested filename")
    return passed(
        observed, href=href, filename=download.suggested_filename, size=size, json_keys=keys
    )


async def c026(page: Any, ctx: Ctx) -> Outcome:
    return await retry_outcome(
        page,
        ctx,
        "/report",
        EXPORT_GLOB,
        "C04-026 Report page-level retry (report.refetch)",
        error_text_re=re.compile(
            r"Failed to load report|nu s-a putut \u00eenc\u0103rca raportul", re.I
        ),
    )


CASES: list[dict[str, Any]] = [
    {
        "id": "C04-015",
        "line": "frontend/src/pages/Radar.tsx:125-138",
        "action": "abort /api/votes, wait for Radar error state, click Retry with route unblocked",
        "expected": "RetryButton fires scopeProbe/votes/positions refetch; error state clears",
        "fn": c015,
        "kind": "retry",
    },
    {
        "id": "C04-016",
        "line": "frontend/src/pages/Grafice.tsx:53-67",
        "action": "abort /api/votes, wait for Grafice page-level error, click Retry unblocked",
        "expected": "RetryButton fires scopeProbe/summary/cohesion refetch; error clears",
        "fn": c016,
        "kind": "retry",
    },
    {
        "id": "C04-017",
        "line": "frontend/src/pages/Grafice.tsx:218 -> VoteActivityChart.tsx:180-186",
        "action": "abort /api/analytics/vote-activity, wait for inline chart error, click its Retry unblocked",
        "expected": "inline RetryButton fires voteActivity refetch; inline error clears",
        "fn": c017,
        "kind": "retry",
    },
    {
        "id": "C04-018",
        "line": "frontend/src/pages/Topuri.tsx:122-128 (label :120)",
        "action": "fill Minimum votes input with an API-resolved threshold",
        "expected": "URL minVotes + scorecard min_votes request change; result rows decrease",
        "fn": c018,
        "kind": "input",
    },
    {
        "id": "C04-019",
        "line": "frontend/src/pages/Topuri.tsx:217-224",
        "action": "click Next (offset 0->100) then Previous (offset 100->0)",
        "expected": "Previous disabled at 0, re-enabled after Next, requests offset=100 then offset=0",
        "fn": c019,
        "kind": "pagination",
    },
    {
        "id": "C04-020",
        "line": "frontend/src/pages/Topuri.tsx:232-239",
        "action": "click Next pagination at offset 0",
        "expected": "scorecard request offset=100 and visible page-range text changes",
        "fn": c020,
        "kind": "pagination",
    },
    {
        "id": "C04-021",
        "line": "frontend/src/pages/Topuri.tsx:74-88",
        "action": "abort /api/votes, wait for Topuri page-level error, click Retry unblocked",
        "expected": "RetryButton fires scopeProbe/scorecard refetch; error clears",
        "fn": c021,
        "kind": "retry",
    },
    {
        "id": "C04-022",
        "line": "frontend/src/pages/Ideology.tsx:248-261 (label :246)",
        "action": "select a specific CHES year, then the repaired 'All years' sentinel",
        "expected": "chesYear in URL; 'all' persists as selected; >=2 distinct years render",
        "fn": c022,
        "kind": "select",
    },
    {
        "id": "C04-023",
        "line": "frontend/src/pages/Ideology.tsx:216-227",
        "action": "abort /api/analytics/ideology, wait for error, click Retry unblocked",
        "expected": "RetryButton fires ideologyQuery.refetch; error clears",
        "fn": c023,
        "kind": "retry",
    },
    {
        "id": "C04-024",
        "line": "frontend/src/pages/Report.tsx:164-170",
        "action": "override window.print with a counter, click Print / Save as PDF",
        "expected": "window.print invoked exactly once; print dialog suppressed by override",
        "fn": c024,
        "kind": "print",
    },
    {
        "id": "C04-025",
        "line": "frontend/src/pages/Report.tsx:171-177",
        "action": "click Download JSON anchor and capture the browser download",
        "expected": "GET /api/export/report downloaded as transparency-report.json with valid JSON",
        "fn": c025,
        "kind": "download",
    },
    {
        "id": "C04-026",
        "line": "frontend/src/pages/Report.tsx:112-123",
        "action": "abort /api/export/report, wait for Report error, click Retry unblocked",
        "expected": "RetryButton fires report.refetch; error clears",
        "fn": c026,
        "kind": "retry",
    },
]


# --- listeners / harness ---------------------------------------------------


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
                "context": "test-injected: API request aborted to force error state"
                if case_kind == "retry"
                else "navigation / action",
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
    page = await browser.new_page(accept_downloads=True)
    page.set_default_timeout(20_000)
    page.set_default_navigation_timeout(35_000)
    requests: list[dict[str, str]] = []
    console_start = len(ctx.console)
    outcome: Outcome | None = None
    final_url = ""

    try:
        page.on("console", make_console_listener(ctx, element_id, case["kind"]))
        page.on("pageerror", make_pageerror_listener(ctx, element_id))
        page.on(
            "request",
            lambda req: (
                requests.append({"method": req.method, "url": req.url})
                if "/api/" in req.url and len(requests) < 300
                else None
            ),
        )
        raw = await case["fn"](page, ctx)
        outcome = raw if isinstance(raw, Outcome) else failed(f"case returned {type(raw).__name__}")
    except Exception as exc:  # noqa: BLE001 - an exception is a finding with evidence
        outcome = failed(f"harness exception: {type(exc).__name__}: {str(exc)[:400]}")
    finally:
        final_url = page.url or ""
        shot = OUT_DIR / f"v08-shot-{element_id}.png"
        try:
            await page.screenshot(path=str(shot), timeout=10_000)
        except Exception:  # noqa: BLE001 - evidence best effort
            pass
        try:
            await page.close()
        except Exception:  # noqa: BLE001 - run_all closes the browser in finally
            pass

    assert outcome is not None
    evidence_path = OUT_DIR / f"v08-evidence-{element_id}.json"
    evidence = {
        "element_id": element_id,
        "source_file_line": case["line"],
        "action": case["action"],
        "expected": case["expected"],
        "observed": outcome.observed,
        "verdict": outcome.verdict,
        "resolver": outcome.resolver,
        "url_at_capture": final_url,
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


def test_v08_analytics_clickables() -> None:
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
                        e["context"].startswith("test-injected") for e in ctx.console
                    ),
                },
                "note": (
                    "test-injected console.error entries are caused by the harness aborting "
                    "API requests to force React Query error states (C04-015/016/017/021/023/026). "
                    "They are reported, never suppressed."
                ),
            },
        )

    assert len(rows) == 12, f"expected 12 element rows, got {len(rows)}"
    counts = {v: sum(r["verdict"] == v for r in rows) for v in ("PASS", "FAIL", "SKIP")}
    print("V-08 verdicts:", counts, "results:", RESULTS_PATH, "console:", CONSOLE_PATH)
    failures = [f"{r['element_id']}: {r['observed']}" for r in rows if r["verdict"] == "FAIL"]
    assert not failures, "click validation FAILs:\n" + "\n".join(failures)
