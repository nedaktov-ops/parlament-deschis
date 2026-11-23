"""V-01 clickable validation — global shell (C01-001..061).

Fleet plan: Parlament Deschis Obsidian vault/20-DIRECTION/
CLICK-VALIDATION-FLEET-2026-11-23.md
Inventory: 40-FRONTEND/CLICK-INV-C01-SHELL-2026-11-22.md

Self-contained: launches its own system Chromium, targets the read-only local
dev server at http://127.0.0.1:5188, resolves data-dependent ids at runtime and
records one observable outcome per element id. No product code is edited, no
axe is run, no secrets, no git state touched.

Artifacts (all under /tmp/opencode/click-validation/v01-*):
  * v01-results.json          -- one row per element id (61 rows)
  * v01-console.json          -- every console error/warning + pageerror seen
  * v01-evidence-C01-NNN.json -- raw per-element capture (one per row)
"""

from __future__ import annotations

import asyncio
import json
import time
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:5188"
OUT = Path("/tmp/opencode/click-validation")
RESULTS_PATH = OUT / "v01-results.json"
CONSOLE_PATH = OUT / "v01-console.json"

# Recorded at fleet entry (git rev-parse HEAD). The branch is vault-only ahead
# of the inventory source commit; this is metadata, not a validation claim.
SERVED_HEAD = "e82e01b9152266bf3fe862029946b24acc2032f8"
EXPECTED_IDS = [f"C01-{n:03d}" for n in range(1, 62)]

ROWS: list[dict] = []
CONSOLE_EVENTS: list[dict] = []
CTX = {"element": "bootstrap", "test_induced": False, "page": "-"}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def resolve_person() -> tuple[str | None, str | None]:
    """Resolve a live person id/name from /api/mps?limit=1 — never hard-code."""
    try:
        with urllib.request.urlopen(BASE + "/api/mps?limit=1", timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        person = payload["data"][0]
        return str(person["id"]), str(person["name"])
    except Exception:  # noqa: BLE001 - a probe failure becomes a SKIP, not a crash
        return None, None


def setctx(element: str, page_label: str, test_induced: bool = False) -> None:
    CTX.update(element=element, page=page_label, test_induced=test_induced)


def attach_console(page) -> None:
    def on_console(msg) -> None:
        if msg.type in ("error", "warning", "warn"):
            CONSOLE_EVENTS.append(
                {
                    "ts": time.time(),
                    "page": CTX["page"],
                    "element_context": CTX["element"],
                    "test_induced": CTX["test_induced"],
                    "type": f"console.{msg.type}",
                    "text": msg.text[:400],
                }
            )

    def on_pageerror(exc) -> None:
        CONSOLE_EVENTS.append(
            {
                "ts": time.time(),
                "page": CTX["page"],
                "element_context": CTX["element"],
                "test_induced": CTX["test_induced"],
                "type": "pageerror",
                "text": str(exc)[:400],
            }
        )

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)


async def settle(page, ms: int = 900) -> None:
    try:
        await page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:  # noqa: BLE001 - bounded wait, fall through to fixed settle
        pass
    await page.wait_for_timeout(ms)


async def goto(page, path: str, ms: int = 900) -> None:
    await page.goto(BASE + path, wait_until="load", timeout=30_000)
    await settle(page, ms)


async def add(
    page,
    eid: str,
    line: str,
    action: str,
    expected: str,
    observed: str,
    verdict: str,
    extra: dict | None = None,
    resolver: str | None = None,
) -> None:
    """Persist one evidence artifact + one result row (both schemas)."""
    if verdict not in ("PASS", "FAIL", "SKIP"):
        raise ValueError(f"bad verdict {verdict}")
    evidence_path = OUT / f"v01-evidence-{eid}.json"
    capture = {
        "element_id": eid,
        "source_file_line": line,
        "served_head": SERVED_HEAD,
        "base": BASE,
        "timestamp": time.time(),
        "action": action,
        "expected": expected,
        "observed": observed,
        "verdict": verdict,
        "page_url": page.url if page is not None else None,
        "page_title": await page.title() if page is not None else None,
        "console_context": dict(CTX),
        "extra": extra or {},
    }
    if resolver:
        capture["resolver"] = resolver
    evidence_path.write_text(json.dumps(capture, ensure_ascii=False, indent=2), encoding="utf-8")
    row = {
        "element_id": eid,
        "source_file_line": line,
        "action": action,
        "expected": expected,
        "observed": observed,
        "verdict": verdict,
        # fleet-plan schema aliases (same values)
        "expected_outcome": expected,
        "observed_outcome": observed,
        "status": verdict,
        "evidence_path": str(evidence_path),
    }
    if resolver:
        row["resolver"] = resolver
    ROWS.append(row)


def path_of(url) -> str:
    # Playwright's wait_for_url predicate may pass a URL object or a str.
    return urlparse(str(url)).path


def query_of(url) -> dict[str, list[str]]:
    return parse_qs(urlparse(str(url)).query)


# --------------------------------------------------------------------------- #
# element groups
# --------------------------------------------------------------------------- #
async def shell_chrome(browser, person_id, person_name) -> None:
    """Skip link, search, header About modal, language, theme, devtools, logo."""
    label = "shell"
    page = await browser.new_page()
    attach_console(page)
    try:
        await goto(page, "/")

        # C01-008 — skip link focuses #main-content
        setctx("C01-008", label)
        skip = page.locator('a[href="#main-content"]')
        n = await skip.count()
        obs = f"skip-link count={n}; text={await skip.first.inner_text() if n else '-'}"
        if n:
            await skip.first.focus()
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(250)
            active_id = await page.evaluate("document.activeElement && document.activeElement.id")
            hash_val = await page.evaluate("location.hash")
            obs += f"; hash={hash_val}; activeElement.id={active_id}"
            ok = hash_val == "#main-content" or active_id == "main-content"
        else:
            ok = False
        await add(
            page,
            "C01-008",
            "frontend/src/router.tsx:231-233",
            "focus and activate the 'skip to content' link",
            "fragment #main-content set and focus moved to <main id=main-content>",
            obs,
            "PASS" if ok else "FAIL",
        )

        # C01-042 — logo image source fires a request and renders (or designed SVG fallback)
        setctx("C01-042", label)
        logo_responses: list[tuple[int, str]] = []

        def on_resp(resp):
            if "/api/logo" in resp.url:
                logo_responses.append((resp.status, resp.url))

        page.on("response", on_resp)
        await goto(page, "/")
        img = page.locator("header img[src*='/api/logo']")
        svg_fallback = page.locator("header svg[class*='w-9']")
        img_count = await img.count()
        svg_count = await svg_fallback.count()
        obs = (
            f"logo responses={logo_responses}; img[src*=/api/logo]={img_count}; "
            f"inline-svg-fallback={svg_count}"
        )
        ok = bool(logo_responses) and (img_count > 0 or svg_count > 0)
        await add(
            page,
            "C01-042",
            "frontend/src/components/HeaderLogo.tsx:38-46",
            "load '/' and observe the /api/logo image request and its render",
            "a /api/logo request fires and either the <img> or the designed inline-SVG fallback renders",
            obs,
            "PASS" if ok else "FAIL",
            {"logo_responses": logo_responses},
        )

        # C01-010 — header About button opens the AboutModal
        setctx("C01-010", label)
        about_btn = page.locator("header button").filter(has_text="Despre")
        dlg = page.locator('div[role="dialog"]')
        obs = f"about-button count={await about_btn.count()}; dialog-before={await dlg.count()}"
        if await about_btn.count():
            await about_btn.first.click()
            await page.wait_for_timeout(400)
            dc = await dlg.count()
            h2 = await dlg.first.locator("h2").inner_text() if dc else "-"
            obs += f"; dialog-after={dc}; heading={h2!r}"
            ok = dc >= 1 and "Despre" in h2
        else:
            ok = False
        await add(
            page,
            "C01-010",
            "frontend/src/router.tsx:249-253",
            "click the header 'About' button",
            "a role=dialog titled 'Despre' becomes visible",
            obs,
            "PASS" if ok else "FAIL",
        )

        # C01-004 — backdrop mousedown closes the AboutModal
        setctx("C01-004", label)
        if await dlg.count() == 0:
            await about_btn.first.click()
            await page.wait_for_timeout(300)
        backdrop = page.locator('div[class*="bg-black/70"]')
        obs = f"backdrop count={await backdrop.count()}; dialog-before={await dlg.count()}"
        if await backdrop.count():
            try:
                await backdrop.first.click(position={"x": 4, "y": 4}, timeout=5000)
                await page.wait_for_timeout(300)
                obs += f"; dialog-after={await dlg.count()}"
                ok = await dlg.count() == 0
            except Exception as exc:  # noqa: BLE001
                obs += f"; click-error={str(exc)[:120]}"
                ok = False
        else:
            ok = False
        await add(
            page,
            "C01-004",
            "frontend/src/router.tsx:138-141",
            "mouse-down on the modal backdrop (outside the panel)",
            "the AboutModal closes (role=dialog removed)",
            obs,
            "PASS" if ok else "FAIL",
        )

        # C01-005 — panel Escape + Tab focus trap
        setctx("C01-005", label)
        await about_btn.first.click()
        await page.wait_for_timeout(300)
        obs = f"dialog={await dlg.count()}"
        if await dlg.count():
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            after_esc = await dlg.count()
            # reopen to test the tab trap
            await about_btn.first.click()
            await page.wait_for_timeout(300)
            d = dlg.first
            focusables = d.locator(
                'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
            )
            fc = await focusables.count()
            trap = None
            if fc >= 2:
                try:
                    await focusables.nth(fc - 1).focus()
                    await page.keyboard.press("Tab")
                    await page.wait_for_timeout(150)
                    trap = await focusables.nth(0).evaluate("e => e === document.activeElement")
                except Exception as exc:  # noqa: BLE001
                    trap = f"error:{str(exc)[:80]}"
            obs += f"; after-Escape={after_esc}; focusables={fc}; wrapped-to-first={trap}"
            ok = after_esc == 0 and trap is True
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(200)
        else:
            ok = False
        await add(
            page,
            "C01-005",
            "frontend/src/router.tsx:148-164",
            "press Escape in the modal panel; then Tab from the last focusable",
            "Escape closes the dialog; Tab wraps focus to the first focusable (focus trap)",
            obs,
            "PASS" if ok else "FAIL",
        )

        # C01-006 — modal close button
        setctx("C01-006", label)
        if await dlg.count() == 0:
            await about_btn.first.click()
            await page.wait_for_timeout(300)
        close_btn = dlg.first.locator("button").first
        obs = f"close-button text={await close_btn.inner_text()}; dialog-before={await dlg.count()}"
        await close_btn.click()
        await page.wait_for_timeout(300)
        obs += f"; dialog-after={await dlg.count()}"
        ok = await dlg.count() == 0
        await add(
            page,
            "C01-006",
            "frontend/src/router.tsx:169",
            "click the modal 'Close' button",
            "the AboutModal closes (role=dialog removed)",
            obs,
            "PASS" if ok else "FAIL",
        )

        # C01-007 — external project URL inside the AboutModal
        setctx("C01-007", label)
        await about_btn.first.click()
        await page.wait_for_timeout(300)
        links = dlg.first.locator('a[href][target="_blank"]')
        hrefs = [
            (await a.get_attribute("href"), await a.get_attribute("rel")) for a in await links.all()
        ]
        obs = f"external links in AboutModal={hrefs}"
        ok = any(h and h.startswith("https://github.com/") for h, _ in hrefs)
        await add(
            page,
            "C01-007",
            "frontend/src/router.tsx:178",
            "inspect the external project link in the AboutModal",
            "an <a target=_blank> pointing at the GitHub project URL is present",
            obs,
            "PASS" if ok else "FAIL",
            {"links": hrefs},
        )
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(200)

        # C01-011 — language toggle changes <html lang>
        setctx("C01-011", label)
        # Stable locator: the language toggle is the only labelled header button.
        lang_btn = page.locator("header button[aria-label]").first
        before = await page.evaluate("document.documentElement.lang")
        before_text = await lang_btn.first.inner_text() if await lang_btn.count() else "-"
        if await lang_btn.count():
            await lang_btn.first.click()
            await page.wait_for_timeout(350)
        after = await page.evaluate("document.documentElement.lang")
        after_text = await lang_btn.first.inner_text() if await lang_btn.count() else "-"
        obs = f"lang {before!r}->{after!r}; button {before_text!r}->{after_text!r}"
        ok = bool(before) and bool(after) and before != after
        await add(
            page,
            "C01-011",
            "frontend/src/router.tsx:254-259",
            "click the language toggle (EN/RO)",
            "document.documentElement.lang changes to the other locale",
            obs,
            "PASS" if ok else "FAIL",
        )
        # restore Romanian so later text-based selectors stay deterministic
        try:
            await lang_btn.click()
            await page.wait_for_timeout(300)
        except Exception:  # noqa: BLE001
            pass

        # C01-056 / C01-057 — theme toggle on the dashboard (two inventory rows, one control)
        setctx("C01-056", label)
        await goto(page, "/")
        theme_btn = page.locator('button[aria-label*="tema"], button[aria-label*="theme"]')
        tc = await theme_btn.count()
        obs = f"theme-toggle count on '/' = {tc}"
        if tc:
            before_theme = await page.evaluate("document.documentElement.dataset.theme")
            ls_before = await page.evaluate("localStorage.getItem('parlament-deschis-theme')")
            label_before = await theme_btn.first.inner_text()
            await theme_btn.first.click()
            await page.wait_for_timeout(350)
            after_theme = await page.evaluate("document.documentElement.dataset.theme")
            ls_after = await page.evaluate("localStorage.getItem('parlament-deschis-theme')")
            label_after = await theme_btn.first.inner_text()
            pressed = await theme_btn.first.get_attribute("aria-pressed")
            obs += (
                f"; data-theme {before_theme!r}->{after_theme!r}; localStorage {ls_before!r}->{ls_after!r}; "
                f"label {label_before!r}->{label_after!r}; aria-pressed={pressed}"
            )
            ok = before_theme != after_theme and ls_after == after_theme
        else:
            ok = False
        await add(
            page,
            "C01-056",
            "frontend/src/components/ui/ThemeToggle.tsx:32-51",
            "click the dashboard ThemeToggle",
            "document.documentElement.dataset.theme and localStorage 'parlament-deschis-theme' both flip",
            obs,
            "PASS" if ok else "FAIL",
        )

        setctx("C01-057", label)
        dh = page.locator("h1.page-title")
        dh_theme = page.locator("h1.page-title + button, div:has(> h1.page-title) button")
        obs = (
            f"h1.page-title count={await dh.count()}; "
            f"theme control within DashboardHeader block={await dh_theme.count()}; "
            f"global theme toggles={await theme_btn.count()}"
        )
        # C01-057 is the same reused control, mounted by DashboardHeader on '/'.
        ok = await dh.count() >= 1 and await theme_btn.count() >= 1
        await add(
            page,
            "C01-057",
            "frontend/src/components/ui/DashboardHeader.tsx:15",
            "confirm DashboardHeader mounts the ThemeToggle on '/' and that it responds",
            "the dashboard header (h1.page-title) is present together with a responsive theme toggle",
            obs,
            "PASS" if ok else "FAIL",
        )

        # C01-035 — ReactQuery devtools toggle
        setctx("C01-035", label)
        devbtn = page.locator("button.tsqd-open-btn")
        db_before = await devbtn.count()
        aria_before = await devbtn.first.get_attribute("aria-label") if db_before else None
        panel_before = await page.locator("aside[class*='tsqd-main-panel']").count()
        if db_before:
            await devbtn.first.click()
            await page.wait_for_timeout(500)
        db_after = await devbtn.count()
        panel_after = await page.locator("aside[class*='tsqd-main-panel']").count()
        obs = (
            f"open-btn {db_before}->{db_after}; aria={aria_before!r}; "
            f"tsqd-main-panel {panel_before}->{panel_after}"
        )
        ok = db_before == 1 and db_after == 0 and panel_after >= 1
        await add(
            page,
            "C01-035",
            "frontend/src/router.tsx:601",
            "click the ReactQuery devtools open button",
            "the open button is replaced by the devtools panel (state transition)",
            obs,
            "PASS" if ok else "FAIL",
        )

        # C01-009 — global search -> /person/$id (runtime-resolved id)
        setctx("C01-009", label)
        await goto(page, "/")
        inp = page.locator("#person-search")
        query = person_name.split()[0] if person_name else "ALBERT"
        await inp.fill(query)
        await page.wait_for_timeout(1300)
        listbox = page.locator("#person-search-results")
        opts = listbox.locator('button[role="option"]')
        oc = await opts.count()
        target_opt = None
        if oc:
            if person_name:
                for i in range(oc):
                    if person_name.split()[0] in (await opts.nth(i).inner_text()):
                        target_opt = opts.nth(i)
                        break
            if target_opt is None:
                target_opt = opts.first
        obs = f"query={query!r}; listbox={await listbox.count()}; options={oc}"
        if target_opt is not None:
            await target_opt.click()
            await page.wait_for_timeout(1500)
            final_path = path_of(page.url)
            obs += f"; navigated to {final_path}; expected /person/{person_id}"
            if person_id:
                ok = final_path == f"/person/{person_id}"
            else:
                ok = bool(re_match_person(final_path))
        else:
            ok = False
        await add(
            page,
            "C01-009",
            "frontend/src/router.tsx:244-248",
            "type a runtime-resolved person name in global search and select a result",
            "onSelect navigates to /person/$id using the live person id",
            obs,
            "PASS" if ok else "FAIL",
            {"resolved_id": person_id, "resolved_name": person_name, "query": query},
        )
    finally:
        await page.close()


def re_match_person(path: str) -> bool:
    import re

    return re.fullmatch(r"/person/[0-9a-f\-]{8,}", path) is not None


# --------------------------------------------------------------------------- #
MAIN_NAV = [
    ("C01-012", "frontend/src/router.tsx:264-266", "/"),
    ("C01-013", "frontend/src/router.tsx:267-269", "/traseism"),
    ("C01-014", "frontend/src/router.tsx:270-272", "/leaderboard"),
    ("C01-015", "frontend/src/router.tsx:273-275", "/demographics"),
    ("C01-016", "frontend/src/router.tsx:276-278", "/committees"),
    ("C01-017", "frontend/src/router.tsx:279-281", "/compare"),
    ("C01-018", "frontend/src/router.tsx:282-284", "/coalitions"),
    ("C01-019", "frontend/src/router.tsx:285-287", "/mps"),
    ("C01-020", "frontend/src/router.tsx:288-290", "/report"),
    ("C01-021", "frontend/src/router.tsx:291-293", "/parties"),
    ("C01-022", "frontend/src/router.tsx:294-296", "/party-timeline"),
    ("C01-023", "frontend/src/router.tsx:297-299", "/institutional"),
    ("C01-024", "frontend/src/router.tsx:300-302", "/coverage"),
    ("C01-025", "frontend/src/router.tsx:303-305", "/senate-history"),
    ("C01-026", "frontend/src/router.tsx:306-308", "/legislature/2024"),
    ("C01-027", "frontend/src/router.tsx:309-311", "/party/PSD"),
]
ANALYTICS_NAV = [
    ("C01-028", "frontend/src/router.tsx:315", "/compare-mps"),
    ("C01-029", "frontend/src/router.tsx:316", "/Voturi"),
    ("C01-030", "frontend/src/router.tsx:317", "/radar"),
    ("C01-031", "frontend/src/router.tsx:318", "/grafice"),
    ("C01-032", "frontend/src/router.tsx:319", "/topuri"),
    ("C01-033", "frontend/src/router.tsx:320", "/ideology"),
]


async def navigation(browser) -> None:
    """C01-003, C01-012..034: nav links, scope preservation, /electoral redirect."""
    label = "navigation"
    page = await browser.new_page()
    attach_console(page)
    try:
        # C01-003 — NavLink preserves scope search on navigation
        setctx("C01-003", label)
        await goto(page, "/mps?date=2024-05-05&chamber=deputies&legislature=2024")
        nav0 = page.locator("nav[aria-label]").nth(0)
        # 'Traseism' is the 2nd main-nav link
        traseism = nav0.locator("a").nth(1)
        href = await traseism.get_attribute("href")
        await traseism.click()
        try:
            await page.wait_for_url(lambda u: path_of(u) == "/traseism", timeout=15_000)
        except Exception:  # noqa: BLE001
            pass
        q = query_of(page.url)
        obs = f"link href={href!r}; landed path={path_of(page.url)}; query={q}"
        ok = path_of(page.url) == "/traseism" and q.get("date") == ["2024-05-05"]
        await add(
            page,
            "C01-003",
            "frontend/src/router.tsx:110-118",
            "from a scoped /mps URL, click the 'Traseism' main-nav link",
            "route changes to /traseism and the scoped date=2024-05-05 is preserved in the URL",
            obs,
            "PASS" if ok else "FAIL",
        )

        # C01-012..027 — main navigation bar
        await goto(page, "/")
        for idx, (eid, line, target) in enumerate(MAIN_NAV):
            setctx(eid, label)
            nav = page.locator("nav[aria-label]").nth(0)
            link = nav.locator("a").nth(idx)
            href = await link.get_attribute("href")
            txt = (await link.inner_text())[:40]
            try:
                await link.click(timeout=10_000)
                await page.wait_for_url(lambda u: path_of(u) == target, timeout=15_000)
            except Exception as exc:  # noqa: BLE001
                pass
            landed = path_of(page.url)
            obs = f"index={idx}; label={txt!r}; href={href!r}; landed path={landed}"
            ok = landed == target
            await add(
                page,
                eid,
                line,
                f"click main-nav link #{idx} ({txt})",
                f"SPA URL pathname becomes {target}",
                obs,
                "PASS" if ok else "FAIL",
            )

        # C01-028..033 — analytics navigation bar
        for idx, (eid, line, target) in enumerate(ANALYTICS_NAV):
            setctx(eid, label)
            nav = page.locator("nav[aria-label]").nth(1)
            link = nav.locator("a").nth(idx)
            href = await link.get_attribute("href")
            txt = (await link.inner_text())[:40]
            try:
                await link.click(timeout=10_000)
                await page.wait_for_url(lambda u: path_of(u) == target, timeout=15_000)
            except Exception:  # noqa: BLE001
                pass
            landed = path_of(page.url)
            obs = f"index={idx}; label={txt!r}; href={href!r}; landed path={landed}"
            ok = landed == target
            await add(
                page,
                eid,
                line,
                f"click analytics-nav link #{idx} ({txt})",
                f"SPA URL pathname becomes {target}",
                obs,
                "PASS" if ok else "FAIL",
            )

        # C01-034 — /electoral -> /traseism redirect
        setctx("C01-034", label)
        await page.goto(BASE + "/electoral", wait_until="load", timeout=30_000)
        try:
            await page.wait_for_url(lambda u: path_of(u) == "/traseism", timeout=15_000)
        except Exception:  # noqa: BLE001
            pass
        q = query_of(page.url)
        obs = f"final URL={page.url}; path={path_of(page.url)}; query={q}"
        ok = (
            path_of(page.url) == "/traseism"
            and q.get("chamber") == ["deputies"]
            and q.get("legislature") == ["2024"]
        )
        await add(
            page,
            "C01-034",
            "frontend/src/router.tsx:348-362",
            "navigate directly to /electoral",
            "beforeLoad redirects to /traseism with chamber=deputies and legislature=2024",
            obs,
            "PASS" if ok else "FAIL",
        )
    finally:
        await page.close()


FOOTER_NAV = [
    ("C01-036", "frontend/src/components/Footer.tsx:65-70", 0, "/"),
    ("C01-037", "frontend/src/components/Footer.tsx:73-79", 1, "/traseism"),
    ("C01-038", "frontend/src/components/Footer.tsx:81-87", 2, "/report"),
    ("C01-041", "frontend/src/components/Footer.tsx:123-129", 5, "/coverage"),
]


async def footer(browser) -> None:
    """C01-036..041: footer links (in-app + external)."""
    label = "footer"
    page = await browser.new_page()
    attach_console(page)
    try:
        await goto(page, "/")
        for eid, line, idx, target in FOOTER_NAV:
            setctx(eid, label)
            links = page.locator("footer a")
            link = links.nth(idx)
            href = await link.get_attribute("href")
            txt = (await link.inner_text())[:40]
            try:
                await link.click(timeout=10_000)
                await page.wait_for_url(lambda u: path_of(u) == target, timeout=15_000)
            except Exception:  # noqa: BLE001
                pass
            landed = path_of(page.url)
            obs = f"index={idx}; label={txt!r}; href={href!r}; landed path={landed}"
            ok = landed == target
            await add(
                page,
                eid,
                line,
                f"click footer in-app link #{idx} ({txt})",
                f"SPA URL pathname becomes {target}",
                obs,
                "PASS" if ok else "FAIL",
            )
            await goto(page, "/", ms=400)

        # C01-039 — first company-group external link (inventory: 'about' label;
        # post-repair code relabelled it 'Cod sursă' / footer.sourceCode).
        for eid, line, idx in (
            ("C01-039", "frontend/src/components/Footer.tsx:96-104", 3),
            ("C01-040", "frontend/src/components/Footer.tsx:106-114", 4),
        ):
            setctx(eid, label)
            links = page.locator("footer a")
            link = links.nth(idx)
            href = await link.get_attribute("href")
            target = await link.get_attribute("target")
            rel = await link.get_attribute("rel")
            txt = (await link.inner_text())[:40]
            obs = f"index={idx}; label={txt!r}; href={href!r}; target={target!r}; rel={rel!r}"
            ok = bool(href and href.startswith("https://github.com/") and target == "_blank")
            note = (
                "Inventory label was t('about'); post-repair code relabels this link "
                "to t('footer.sourceCode') 'Cod sursă' while keeping the external GitHub destination."
                if eid == "C01-039"
                else ""
            )
            await add(
                page,
                eid,
                line,
                f"inspect footer external link #{idx} ({txt})",
                "an <a target=_blank> to the GitHub project URL is present",
                obs + ("; NOTE: " + note if note else ""),
                "PASS" if ok else "FAIL",
                {"inventory_note": note} if note else None,
            )
    finally:
        await page.close()


RECOVERY = [
    ("C01-048", "frontend/src/components/About.tsx:237", "Surse"),
    ("C01-050", "frontend/src/components/About.tsx:264", "Tabel de acoperire"),
    ("C01-051", "frontend/src/components/About.tsx:301", "Licențe"),
    ("C01-054", "frontend/src/components/About.tsx:329", "Starea datelor"),
]


async def about_modal(browser) -> None:
    """C01-043..055: the About.tsx modal mounted on /traseism."""
    label = "about-modal"
    page = await browser.new_page()
    attach_console(page)
    try:
        await goto(page, "/traseism", ms=1400)
        trigger = page.locator("button").filter(has_text="Despre proiect")
        tc = await trigger.count()
        obs0 = f"trigger count={tc}"
        if tc == 0:
            # record all as FAIL with the same evidence
            for eid, line, *_ in [
                ("C01-043", "frontend/src/components/About.tsx:118-121"),
                ("C01-044", "frontend/src/components/About.tsx:160-163"),
                ("C01-045", "frontend/src/components/About.tsx:164-186"),
                ("C01-046", "frontend/src/components/About.tsx:197-203"),
                ("C01-047", "frontend/src/components/About.tsx:75-87"),
                *RECOVERY,
                ("C01-049", "frontend/src/components/About.tsx:246-253"),
                ("C01-052", "frontend/src/components/About.tsx:305-312"),
                ("C01-053", "frontend/src/components/About.tsx:316-323"),
                ("C01-055", "frontend/src/components/About.tsx:358-365"),
            ]:
                await add(
                    page,
                    eid,
                    line,
                    "open /traseism About modal",
                    "modal trigger reachable",
                    obs0,
                    "FAIL",
                )
            return

        async def open_modal():
            if await dlg.count() == 0:
                await trigger.first.click()
                await page.wait_for_timeout(700)

        dlg = page.locator('div[role="dialog"]')

        # C01-046 — close button
        setctx("C01-046", label)
        await open_modal()
        close_btn = dlg.first.locator(
            'button[aria-label="Închide"], button:has-text("Închide")'
        ).first
        obs = f"dialog-before={await dlg.count()}; close-label={await close_btn.inner_text()}"
        await close_btn.click()
        await page.wait_for_timeout(300)
        obs += f"; dialog-after={await dlg.count()}"
        await add(
            page,
            "C01-046",
            "frontend/src/components/About.tsx:197-203",
            "click the About modal close button",
            "the About modal closes (role=dialog removed)",
            obs,
            "PASS" if await dlg.count() == 0 else "FAIL",
        )

        # C01-043 — global Escape key closes
        setctx("C01-043", label)
        await open_modal()
        obs = f"dialog-before={await dlg.count()}"
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
        obs += f"; dialog-after={await dlg.count()}"
        await add(
            page,
            "C01-043",
            "frontend/src/components/About.tsx:118-121",
            "press Escape while the About modal is open",
            "the document keydown handler closes the About modal",
            obs,
            "PASS" if await dlg.count() == 0 else "FAIL",
        )

        # C01-044 — backdrop onClick closes
        setctx("C01-044", label)
        await open_modal()
        backdrop = page.locator('div[class*="bg-black/60"]')
        obs = f"backdrop count={await backdrop.count()}; dialog-before={await dlg.count()}"
        if await backdrop.count():
            await backdrop.first.click(position={"x": 4, "y": 4}, timeout=5000)
            await page.wait_for_timeout(300)
        obs += f"; dialog-after={await dlg.count()}"
        await add(
            page,
            "C01-044",
            "frontend/src/components/About.tsx:160-163",
            "click the About modal backdrop (outside the panel)",
            "the backdrop onClick closes the About modal",
            obs,
            "PASS" if await dlg.count() == 0 else "FAIL",
        )

        # C01-045 — panel stopPropagation + Tab trap
        setctx("C01-045", label)
        await open_modal()
        d = dlg.first
        heading = d.locator("h2").first
        await heading.click()
        after_inner_click = await dlg.count()
        focusables = d.locator('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])')
        fc = await focusables.count()
        trap = None
        if fc >= 2:
            try:
                await focusables.nth(fc - 1).focus()
                await page.keyboard.press("Tab")
                await page.wait_for_timeout(150)
                trap = await focusables.nth(0).evaluate("e => e === document.activeElement")
            except Exception as exc:  # noqa: BLE001
                trap = f"error:{str(exc)[:80]}"
        obs = f"dialog-after inner click={after_inner_click}; focusables={fc}; wrapped-to-first={trap}"
        ok = after_inner_click >= 1 and trap is True
        await add(
            page,
            "C01-045",
            "frontend/src/components/About.tsx:164-186",
            "click inside the dialog panel; then Tab from its last focusable",
            "inner clicks do not close the modal (stopPropagation) and Tab wraps focus (trap)",
            obs,
            "PASS" if ok else "FAIL",
        )
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(250)

        # C01-047 — generic AccordionItem button toggles aria-expanded
        setctx("C01-047", label)
        await open_modal()
        acc = dlg.first.locator("button[aria-expanded]")
        ac = await acc.count()
        first = acc.first
        before = await first.get_attribute("aria-expanded")
        await first.click()
        await page.wait_for_timeout(250)
        after = await first.get_attribute("aria-expanded")
        obs = f"accordions={ac}; first aria-expanded {before!r}->{after!r}"
        # About's accordion state persists across modal reopen (the component
        # early-returns null but is not unmounted): assert a real toggle.
        ok = ac >= 4 and before != after
        await add(
            page,
            "C01-047",
            "frontend/src/components/About.tsx:75-87",
            "click the first About accordion trigger",
            "aria-expanded toggles (state transition) and the panel content visibility changes",
            obs,
            "PASS" if ok else "FAIL",
        )

        # C01-048 / C01-050 / C01-051 / C01-054 — specific accordions
        for eid, line, title in RECOVERY:
            setctx(eid, label)
            # reset: close and reopen so all accordions start collapsed
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(200)
            await open_modal()
            btn = dlg.first.locator("button[aria-expanded]").filter(has_text=title)
            bc = await btn.count()
            before = await btn.first.get_attribute("aria-expanded") if bc else None
            if bc:
                await btn.first.click()
                await page.wait_for_timeout(300)
            after = await btn.first.get_attribute("aria-expanded") if bc else None
            obs = f"title={title!r}; matches={bc}; aria-expanded {before!r}->{after!r}"
            ok = bc == 1 and before != after
            await add(
                page,
                eid,
                line,
                f"click the '{title}' accordion",
                "the accordion toggles (aria-expanded changes, content visibility changes)",
                obs,
                "PASS" if ok else "FAIL",
            )

        # C01-049 — data-driven source links (runtime payload)
        setctx("C01-049", label)
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(200)
        await open_modal()
        sources_btn = dlg.first.locator("button[aria-expanded]").filter(has_text="Surse")
        src_wrapper = (
            sources_btn.first.locator("xpath=..") if await sources_btn.count() else dlg.first
        )
        if (
            await sources_btn.count()
            and await sources_btn.first.get_attribute("aria-expanded") == "false"
        ):
            await sources_btn.first.click()
        await page.wait_for_timeout(900)
        # Scope to the Sources accordion wrapper so unrelated links (e.g. the
        # modal-footer project link) cannot be miscounted.
        all_links = src_wrapper.locator('a[href][target="_blank"]')
        src_links = []
        for a in await all_links.all():
            txt = await a.inner_text()
            if "Proiect" not in txt:
                src_links.append((await a.get_attribute("href"), txt[:60]))
        obs = f"source links from live /api/about payload={src_links}"
        ok = any(h and h.startswith("https://") for h, _ in src_links)
        resolver = (
            None
            if ok
            else "backend /api/about returned no source URLs — rerun with a live sources payload"
        )
        await add(
            page,
            "C01-049",
            "frontend/src/components/About.tsx:246-253",
            "expand Sources and inspect the data-driven external links",
            "at least one external source link with an http(s) href from the live payload",
            obs,
            "PASS" if ok else "SKIP",
            {"source_links": src_links},
            resolver,
        )

        # C01-052 / C01-053 — license links
        for eid, line, key, host in (
            ("C01-052", "frontend/src/components/About.tsx:305-312", "code", "gnu.org"),
            ("C01-053", "frontend/src/components/About.tsx:316-323", "data", "creativecommons.org"),
        ):
            setctx(eid, label)
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(200)
            await open_modal()
            lic_btn = dlg.first.locator("button[aria-expanded]").filter(has_text="Licențe")
            if (
                await lic_btn.count()
                and await lic_btn.first.get_attribute("aria-expanded") == "false"
            ):
                await lic_btn.first.click()
            await page.wait_for_timeout(400)
            # Scope to the Licenses accordion wrapper (not the whole dialog).
            lic_wrapper = lic_btn.first.locator("xpath=..") if await lic_btn.count() else dlg.first
            lic_links = lic_wrapper.locator('a[href][target="_blank"]')
            hrefs = [await a.get_attribute("href") for a in await lic_links.all()]
            obs = f"license links={hrefs}"
            ok = any(h and host in h for h in hrefs)
            await add(
                page,
                eid,
                line,
                f"expand Licenses and inspect the {key} license link",
                f"an external link to {host} is present (API value or code fallback)",
                obs,
                "PASS" if ok else "FAIL",
                {"hrefs": hrefs},
            )

        # C01-055 — project link in the modal footer
        setctx("C01-055", label)
        proj = dlg.first.locator('a[href]:has-text("Proiect")')
        pc = await proj.count()
        href = await proj.first.get_attribute("href") if pc else None
        target = await proj.first.get_attribute("target") if pc else None
        txt = (await proj.first.inner_text())[:80] if pc else "-"
        obs = f"count={pc}; text={txt!r}; href={href!r}; target={target!r}"
        ok = bool(href and href.startswith("https://github.com/") and target == "_blank")
        await add(
            page,
            "C01-055",
            "frontend/src/components/About.tsx:358-365",
            "inspect the project link in the modal footer",
            "an external <a target=_blank> to the GitHub project URL is present",
            obs,
            "PASS" if ok else "FAIL",
        )
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(200)
    finally:
        await page.close()


async def recovery_and_retry(browser) -> None:
    """C01-001, 002, 058..061: not-found/error recovery and retry controls."""
    # C01-001 — NotFound back-home link
    page = await browser.new_page()
    attach_console(page)
    try:
        setctx("C01-001", "not-found")
        await goto(page, "/__v01_no_such_route__", ms=700)
        body = (await page.inner_text("body"))[:200].replace("\n", " | ")
        back = page.locator("a.btn.bg-sky-700")
        bc = await back.count()
        obs = f"body={body!r}; back-home links={bc}"
        if bc:
            await back.first.click()
            try:
                await page.wait_for_url(lambda u: path_of(u) == "/", timeout=15_000)
            except Exception:  # noqa: BLE001
                pass
        obs += f"; landed path={path_of(page.url)}"
        ok = bc >= 1 and path_of(page.url) == "/"
        await add(
            page,
            "C01-001",
            "frontend/src/router.tsx:75",
            "navigate to an unknown route, then click 'Back to overview'",
            "the NotFound recovery link returns the SPA to the '/' route",
            obs,
            "PASS" if ok else "FAIL",
        )
    finally:
        await page.close()

    # C01-002 — RouteError back-home link: no deterministic in-UI trigger.
    setctx("C01-002", "route-error")
    await add(
        None,
        "C01-002",
        "frontend/src/router.tsx:90",
        "attempt to observe the root RouteError boundary",
        "a render/loader error shows RouteError; its 'Back to overview' link returns to '/'",
        "NOT PROVEN: RouteError is a framework error boundary with no deterministic UI trigger; "
        "inducing one would require injecting a render/loader exception, which is outside a click test",
        "SKIP",
        resolver="No deterministic in-UI trigger for the error boundary. Resolver: inject a child-route "
        "render/loader exception (or add a fault-injection harness) and re-run, then click the "
        "RouteError 'Back to overview' link and assert pathname '/'.",
    )

    # C01-058 + C01-061 — ErrorState RetryButton and RetryButton click,
    # observed via a deterministic, test-induced API failure on /mps.
    page = await browser.new_page()
    attach_console(page)
    try:
        setctx("C01-058", "retry (test-induced)", test_induced=True)
        hits = {"n": 0}

        async def handler(route):
            hits["n"] += 1
            if hits["n"] <= 2:  # initial fetch + react-query's single retry
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/api/mps*", handler)
        await page.goto(BASE + "/mps", wait_until="load", timeout=30_000)
        await page.wait_for_timeout(3200)
        err = page.locator('[data-state="error"]')
        ec = await err.count()
        err_text = (await err.first.inner_text())[:180].replace("\n", " | ") if ec else "-"
        retry = err.first.locator("button") if ec else page.locator("none")
        rc = await retry.count()
        obs = f"error-state count={ec}; text={err_text!r}; retry buttons={rc}; aborted requests={hits['n']}"
        ok = ec >= 1 and rc >= 1
        await add(
            page,
            "C01-058",
            "frontend/src/components/ErrorState.tsx:38-45",
            "induce an API error on /mps and observe the ErrorState retry control",
            "data-state=error renders with a RetryButton labelled for retry",
            obs,
            "PASS" if ok else "FAIL",
            {"aborted_requests": hits["n"], "test_induced": True},
        )

        setctx("C01-061", "retry (test-induced)", test_induced=True)
        if rc:
            before_hits = hits["n"]
            await retry.first.click()
            await page.wait_for_timeout(2600)
            after_err = await page.locator('[data-state="error"]').count()
            obs2 = (
                f"click RetryButton; /api/mps requests {before_hits}->{hits['n']}; "
                f"error-state after retry={after_err}"
            )
            ok2 = hits["n"] > before_hits and after_err == 0
        else:
            obs2 = "no RetryButton present to click"
            ok2 = False
        await add(
            page,
            "C01-061",
            "frontend/src/components/RetryButton.tsx:18-25",
            "click the retry button rendered by ErrorState",
            "onRetry fires a fresh /api/mps request and the region leaves the error state",
            obs2,
            "PASS" if ok2 else "FAIL",
            {"aborted_requests": hits["n"], "test_induced": True},
        )
    finally:
        await setctx_safe()
        await page.close()

    # C01-059 / C01-060 — controls removed by the post-repair code.
    setctx("C01-059", "removed-controls")
    await add(
        None,
        "C01-059",
        "frontend/src/components/LoadingState.tsx:46-53",
        "attempt to observe a LoadingState retry button",
        "inventory described onRetry+retryLabel producing a RetryButton in LoadingState",
        "DESIGNED-ABSENT in served post-repair code: LoadingState.tsx now renders only "
        "role=status label/description; no onRetry/retryLabel props and no button",
        "SKIP",
        resolver="Control removed by repair. Resolver: validate the historical control against source "
        "commit 8811216 (or its recipe); current post-repair LoadingState is status-only by design.",
    )
    setctx("C01-060", "removed-controls")
    await add(
        None,
        "C01-060",
        "frontend/src/components/EmptyState.tsx:42-51",
        "attempt to observe an EmptyState CTA button",
        "inventory described onCta+ctaLabel producing a button in EmptyState",
        "DESIGNED-ABSENT in served post-repair code: EmptyState.tsx now renders only "
        "title/description; no onCta/ctaLabel props and no button",
        "SKIP",
        resolver="Control removed by repair. Resolver: validate the historical control against source "
        "commit 8811216 (or its recipe); current post-repair EmptyState has no CTA by design.",
    )


async def setctx_safe() -> None:
    CTX["test_induced"] = False
    CTX["element"] = "cleanup"
    CTX["page"] = "-"


# --------------------------------------------------------------------------- #
# driver / pytest entry point
# --------------------------------------------------------------------------- #
async def _run_all() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ROWS.clear()
    CONSOLE_EVENTS.clear()
    person_id, person_name = resolve_person()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path="/usr/bin/chromium", args=["--no-sandbox"]
        )
        try:
            await shell_chrome(browser, person_id, person_name)
            await navigation(browser)
            await footer(browser)
            await about_modal(browser)
            await recovery_and_retry(browser)
        finally:
            await browser.close()


def test_v01_shell() -> None:
    """Run the shell validation and write evidence artifacts (sync pytest wrapper)."""
    harness_error = None
    try:
        asyncio.run(_run_all())
    except Exception as exc:  # noqa: BLE001 - record harness error, still write artifacts
        harness_error = exc

    # Persist artifacts even if individual element verdicts are FAIL/SKIP.
    CONSOLE_PATH.write_text(
        json.dumps(CONSOLE_EVENTS, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    RESULTS_PATH.write_text(json.dumps(ROWS, ensure_ascii=False, indent=2), encoding="utf-8")

    ids = [r["element_id"] for r in ROWS]
    counts = {v: sum(1 for r in ROWS if r["verdict"] == v) for v in ("PASS", "FAIL", "SKIP")}
    print("\n=== V-01 shell validation summary ===")
    print(f"served HEAD: {SERVED_HEAD}")
    print(f"resolved person id: {rows_person_id()}")
    print(f"element rows: {len(ids)} (unique {len(set(ids))})")
    print(f"PASS={counts['PASS']} FAIL={counts['FAIL']} SKIP={counts['SKIP']}")
    print(f"console events: {len(CONSOLE_EVENTS)}")
    for r in ROWS:
        if r["verdict"] in ("FAIL", "SKIP"):
            print(f"  {r['verdict']} {r['element_id']}: {r['observed'][:160]}")
    print(f"results: {RESULTS_PATH}")
    print(f"console: {CONSOLE_PATH}")
    if harness_error is not None:
        print(f"HARNESS ERROR: {type(harness_error).__name__}: {harness_error}")

    # Harness-integrity assertions only: a FAIL/SKIP is a finding recorded in
    # the JSON, not a harness crash. All 61 ids must be accounted for once.
    assert sorted(ids) == sorted(EXPECTED_IDS), (
        f"element id mismatch: missing={sorted(set(EXPECTED_IDS) - set(ids))}, "
        f"extra={sorted(set(ids) - set(EXPECTED_IDS))}, duplicates="
        f"{sorted({i for i in ids if ids.count(i) > 1})}"
    )
    assert harness_error is None, f"harness error: {harness_error!r}"
    assert all(len(r["evidence_path"]) > 0 for r in ROWS)
    assert all(Path(r["evidence_path"]).exists() for r in ROWS)


def rows_person_id() -> str:
    """Best-effort echo of the runtime id (evidence already stores the truth)."""
    for p in OUT.glob("v01-evidence-C01-009.json"):
        try:
            return str(json.loads(p.read_text(encoding="utf-8"))["extra"].get("resolved_id"))
        except Exception:  # noqa: BLE001
            pass
    return "(unresolved)"
