"""Targeted state-system probe for R-05 (companion to scripts/ui_validate.py).

For each route, three scenarios:
  abort  -> [data-state="error"] + retry control + NO [data-state="empty"]
  slow   -> [data-state="loading"] and no "0"/"0%" inside [data-moment]
  empty  -> [data-state="empty"] + NO [data-state="error"] + no retry control

Usage: python3 scripts/ui_state_probe.py [base_url]
Requires system python3 with playwright + /usr/bin/chromium (same as ui_validate.py).
"""

from __future__ import annotations

import asyncio
import re
import sys
from urllib.parse import urlparse

from playwright.async_api import async_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5180").rstrip("/")
AXE_PATH = "/tmp/axe.min.js"

ROUTES = [
    ("demographics", "/demographics"),
    ("party-timeline", "/party-timeline"),
    ("coverage", "/coverage"),
    ("senate-history", "/senate-history"),
    ("coalitions", "/coalitions"),
    ("radar", "/radar"),
    ("grafice", "/grafice"),
    ("topuri", "/topuri"),
    ("ideology", "/ideology"),
]

RETRY = re.compile(r"retry|re[îi]ncearc|try again", re.I)
ZERO = re.compile(r"^\s*0+(?:[.,]0+)?%?\s*$")


def _empty_body(path: str) -> str:
    # These endpoints return a bare array; others wrap in {data: []}.
    if (
        "/coverage/detailed" in path
        or "/coverage/dimensions" in path
        or "/analytics/switch-waves" in path
    ):
        return "[]"
    return '{"status":"ok","data":[],"data_exists":false,"count":0}'


async def _probe(browser, name: str, route: str, mode: str) -> list[str]:
    errors: list[str] = []
    page = await browser.new_page()

    async def abort(route_):
        await route_.abort()

    async def slow(route_):
        await asyncio.sleep(2.0)
        await route_.continue_()

    async def empty(route_):
        # Keep the app shell working: meta/health feed the header and footer,
        # not the page data region under test.
        path = urlparse(route_.request.url).path
        if path in ("/api/meta", "/api/health"):
            await route_.continue_()
            return
        await route_.fulfill(
            status=200,
            content_type="application/json",
            body=_empty_body(path),
        )

    # Root-anchored: a bare "**/api/**" also matches Vite's /src/api/client.ts
    # module request and would abort the app bundle itself.
    await page.route(f"{BASE}/api/**", {"abort": abort, "slow": slow, "empty": empty}[mode])
    try:
        await page.goto(BASE + route, wait_until="domcontentloaded", timeout=30_000)
        if mode == "abort":
            await page.wait_for_selector('[data-state="error"]', timeout=8_000)
            if await page.locator('[data-state="empty"]').count():
                errors.append("error branch also rendered empty copy")
            if not await page.get_by_role("button", name=RETRY).count():
                errors.append("error branch has no retry control")
        elif mode == "slow":
            await page.wait_for_selector('[data-state="loading"]', timeout=2_000)
            for moment in await page.locator("[data-moment]").all():
                if ZERO.match((await moment.inner_text()) or ""):
                    errors.append("zero rendered as a fact while loading")
        else:
            await page.wait_for_selector('[data-state="empty"]', timeout=8_000)
            if await page.locator('[data-state="error"]').count():
                errors.append("empty branch also rendered error copy")
            if await page.get_by_role("button", name=RETRY).count():
                errors.append("empty branch offers retry (error/empty conflated)")
        # No axe regressions in any of the three pending states.
        await page.add_script_tag(path=AXE_PATH)
        violations = await page.evaluate(
            "async () => (await axe.run(document, {resultTypes:['violations']}))"
            ".violations.map(v => v.id)"
        )
        if violations:
            errors.append("axe: " + ", ".join(violations))
    except Exception as exc:  # noqa: BLE001 - probe must report, never crash
        errors.append(f"{mode}: {str(exc)[:160]}")
    finally:
        await page.close()
    return errors


async def main() -> int:
    failures = 0
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path="/usr/bin/chromium", args=["--no-sandbox"]
        )
        for name, route in ROUTES:
            route_errors: list[str] = []
            for mode in ("abort", "slow", "empty"):
                for msg in await _probe(browser, name, route, mode):
                    route_errors.append(f"[{mode}] {msg}")
            status = "OK " if not route_errors else "FAIL"
            failures += len(route_errors)
            print(f"[{status}] {name:16s} {route:22s} {len(route_errors)} findings")
            for msg in route_errors:
                print("   - " + msg)
        await browser.close()
    if failures:
        print(f"\nSTATE PROBE FAIL: {failures} findings")
        return 1
    print(f"\nSTATE PROBE PASS: {len(ROUTES)} routes × 3 scenarios, 0 failures")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
