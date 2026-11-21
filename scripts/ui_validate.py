"""Pre-merge UI validation (strategy doc: "Validation Before Merge").

For every feature route:
* page must load and render (no navigation/timeout failure);
* ZERO JS errors: no ``console.error`` and no uncaught ``pageerror``;
* axe-core 4.10.2 accessibility scan: report violations (target 0).

Evidence over assertion: prints a per-route table and exits non-zero if any
JS error occurs or any axe violation is found, so CI/humans can't miss it.

Usage:  python3 scripts/ui_validate.py [base_url]
Expects the Vite dev server (or preview) with /api proxied to a live API.
Requires system python3 with playwright + a Chromium binary (these are not
project dependencies — installing them would bloat the pinned lockfile).
"""

from __future__ import annotations

import asyncio
import json
import sys
import urllib.request

from playwright.async_api import async_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5174").rstrip("/")
AXE_PATH = "/tmp/axe.min.js"


def _resolve_person_id() -> str:
    """Use a person that actually exists in the corpus under test.

    Hard-coding a UUID silently breaks after every data release (new UUIDs),
    producing a 404 that looks like an application defect. Fall back to the
    historical id and report it in the route name only when the API is absent.
    """
    try:
        with urllib.request.urlopen(BASE + "/api/mps?limit=1", timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload["data"][0]["id"]
    except Exception:  # noqa: BLE001 - a validation tool must not crash on probe failure
        return "cb5ca84e-7bba-4d0b-bea8-91b81aa8eb53"


PERSON_ID = _resolve_person_id()

ROUTES: list[tuple[str, str]] = [
    ("overview", "/"),
    ("traseism", "/traseism"),
    ("leaderboard", "/leaderboard"),
    ("demographics", "/demographics"),
    ("committees", "/committees"),
    ("party-compare", "/compare"),
    ("coalitions", "/coalitions"),
    ("mps", "/mps"),
    ("mp-compare", "/compare-mps"),
    ("report", "/report"),
    ("party-timeline", "/party-timeline"),
    ("coverage", "/coverage"),
    ("senate-history", "/senate-history"),
    ("electoral", "/electoral"),
    ("institutional", "/institutional"),
    ("party-profile", "/party/PSD"),
    ("person-deep-dive", f"/person/{PERSON_ID}"),
    ("legislature", "/legislature/2024"),
    # Routes added after the original 18-route gate was defined. They must be
    # scanned too: the newest vote/ideology views are precisely the ones most
    # likely to regress (empty states, lazy chunks, chart JS errors).
    ("parties", "/parties"),
    ("votes", "/Voturi"),
    ("radar", "/radar"),
    ("grafice", "/grafice"),
    ("topuri", "/topuri"),
    ("ideology", "/ideology"),
]


async def check_route(browser, name: str, route: str) -> dict:
    page = await browser.new_page()
    js_errors: list[str] = []

    def on_console(msg):
        if msg.type == "error":
            js_errors.append(f"console.error: {msg.text[:300]}")

    def on_pageerror(exc):
        js_errors.append(f"pageerror: {str(exc)[:300]}")

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)

    nav_error = None
    try:
        await page.goto(BASE + route, wait_until="load", timeout=30_000)
        # Let react-query fetches + lazy chunks settle. Vote-heavy routes issue
        # many parallel position queries, so a fixed short wait used to scan
        # their loading state and report a false h1/axe failure. Prefer network
        # idle, then a bounded settle; never skip the check on timeout.
        try:
            await page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:  # noqa: BLE001 - fall through to the fixed settle
            pass
        await page.wait_for_timeout(4_000)
        # The page must show real content, not an error boundary.
        body_text = (await page.inner_text("body")) or ""
        if not body_text.strip():
            nav_error = "empty body"
        elif "Internal Error" in body_text or "Application error" in body_text:
            nav_error = "error boundary shown"
    except Exception as exc:  # noqa: BLE001 - any navigation failure is a finding
        nav_error = f"goto failed: {str(exc)[:200]}"

    axe_violations: list[tuple[str, int, str]] = []
    axe_error = None
    try:
        await page.add_script_tag(path=AXE_PATH)
        violations = await page.evaluate(
            "async () => (await axe.run(document, {resultTypes: ['violations']}))"
            ".violations.map(v => ({id: v.id, n: v.nodes.length, impact: v.impact}))"
        )
        axe_violations = [(v["id"], v["n"], v["impact"]) for v in violations]
    except Exception as exc:  # noqa: BLE001 - a failed scan is a finding too
        axe_error = str(exc)[:200]

    await page.close()
    return {
        "name": name,
        "route": route,
        "nav_error": nav_error,
        "js_errors": js_errors,
        "axe": axe_violations,
        "axe_error": axe_error,
    }


async def main() -> int:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path="/usr/bin/chromium", args=["--no-sandbox"]
        )
        results = []
        for name, route in ROUTES:
            r = await check_route(browser, name, route)
            results.append(r)
            status = (
                "OK "
                if not (r["nav_error"] or r["js_errors"] or r["axe"] or r["axe_error"])
                else "FAIL"
            )
            js = f"{len(r['js_errors'])} js-err" if r["js_errors"] else "0 js-err"
            if r["axe_error"]:
                axe = "axe-SCAN-ERROR"
            else:
                axe = f"{len(r['axe'])} axe" if r["axe"] else "0 axe"
            nav = r["nav_error"] or "rendered"
            print(f"[{status}] {r['name']:18s} {r['route']:45s} {nav:20s} {js:9s} {axe}")
        await browser.close()

    print("\n--- details ---")
    failed = False
    for r in results:
        if r["nav_error"] or r["js_errors"] or r["axe"] or r["axe_error"]:
            failed = True
            print(f"\n{r['name']} ({r['route']}):")
            if r["nav_error"]:
                print(f"  nav: {r['nav_error']}")
            for e in r["js_errors"]:
                print(f"  {e}")
            if r["axe_error"]:
                print(f"  axe scan failed: {r['axe_error']}")
            for vid, n, impact in r["axe"]:
                print(f"  axe [{impact}] {vid}: {n} nodes")

    if failed:
        print("\nUI VALIDATION FAIL")
        return 1
    print(f"\nUI VALIDATION PASS: {len(results)} routes, 0 JS errors, 0 axe violations")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
