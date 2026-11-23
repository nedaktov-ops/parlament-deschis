"""V-10 clickable validation — cross-cutting destinations, guards and AT paths.

Fleet plan: Parlament Deschis Obsidian vault/20-DIRECTION/
CLICK-VALIDATION-FLEET-2026-11-23.md (V-10 row, §2; test contract §3)
Inventory slices:
  * 40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md — 10 dead IDs
  * 40-FRONTEND/CLICK-INV-C06-DESTINATIONS-2026-11-22.md — 100 targets
  * 40-FRONTEND/CLICK-INV-C07-HARNESS-2026-11-22.md — 6 checks
  * 60-EVIDENCE/LINK-URL-REACHABILITY-2026-11-22.md — 6 probed URL literals

This file is strictly read-only with respect to the product: it parses source,
runs two read-only guard scripts as subprocesses, and drives ONE system
Chromium at the read-only local dev server http://127.0.0.1:5188. No axe run,
no product code / vault / data / config / git edits, no network probe of
external hosts (the dated 2026-11-22 probe is reused by source comparison).

Artifacts (all under /tmp/opencode/click-validation/v10-*):
  v10-results.json      -- 116 flat rows (gate-compatible schema)
  v10-targets.json      -- the 100 C06 target rows (separate list)
  v10-checks.json       -- the 6 C07 check rows (separate list)
  v10-guards.json       -- both guard subprocess captures with exit codes
  v10-console.json      -- every console error/warning + pageerror captured
  v10-url-probe.json    -- the 6 reachability-note literals vs current source
  v10-keyboard.json     -- keyboard-only main-nav traversal capture
  v10-export.json       -- keyboard-only export/print control capture
  v10-evidence-<ID>.json -- one raw per-item capture for each of the 116 items
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import time
from pathlib import Path

from playwright.async_api import async_playwright

REPO = Path(__file__).resolve().parents[2]
OUT = Path("/tmp/opencode/click-validation")
BASE = "http://127.0.0.1:5188"
FLEET_SOURCE_COMMIT = "863b200e1adc70aadb289fdd4df52a7e5be2c483"
INVENTORY_SOURCE_COMMIT = "88112168237e5c37841b785dccd2375f6cc40115"

RESULTS_PATH = OUT / "v10-results.json"
TARGETS_PATH = OUT / "v10-targets.json"
CHECKS_PATH = OUT / "v10-checks.json"
GUARDS_PATH = OUT / "v10-guards.json"
CONSOLE_PATH = OUT / "v10-console.json"
URLPROBE_PATH = OUT / "v10-url-probe.json"
KEYBOARD_PATH = OUT / "v10-keyboard.json"
EXPORT_PATH = OUT / "v10-export.json"

C05_IDS = [
    "C05-017",
    "C05-019",
    "C05-022",
    "C05-037",
    "C05-038",
    "C05-039",
    "C05-043",
    "C05-044",
    "C05-057",
    "C05-060",
]

ROWS: list[dict] = []
CONSOLE_EVENTS: list[dict] = []
CTX = {"item": "bootstrap", "page": "-", "test_induced": False}
BROWSER_EXTRA: dict[str, dict] = {}

SERVED_HEAD = "unknown"
try:
    SERVED_HEAD = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    ).stdout.strip()
except Exception:  # pragma: no cover - metadata only
    pass


# --------------------------------------------------------------------------- #
# generic source helpers
# --------------------------------------------------------------------------- #
def read_rel(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def extract_literal(text: str, start: int) -> tuple[str | None, int]:
    """Read a JS string/template literal, honouring ${...} nesting."""
    quote = text[start]
    if quote not in ('"', "'", "`"):
        return None, start
    i, depth, n = start + 1, 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "$" and i + 1 < n and text[i + 1] == "{":
            depth += 1
            i += 2
            continue
        if ch == "}" and depth:
            depth -= 1
            i += 1
            continue
        if ch == quote and depth == 0:
            return text[start + 1 : i], i + 1
        i += 1
    return None, start


def strip_query(lit: str) -> str:
    """Cut a top-level '?' or a trailing ${...query-builder} interpolation."""
    i, n = 0, len(lit)
    while i < n:
        ch = lit[i]
        if ch == "$" and i + 1 < n and lit[i + 1] == "{":
            depth, j = 1, i + 2
            while j < n and depth:
                if lit[j : j + 2] == "${":
                    depth += 1
                    j += 2
                elif lit[j] == "}":
                    depth -= 1
                    j += 1
                else:
                    j += 1
            if "?" in lit[i + 2 : j - 1]:  # e.g. `${qs ? `?${qs}` : ""}`
                return lit[:i]
            i = j
            continue
        if ch == "?":
            return lit[:i]
        i += 1
    return lit


def collapse_interpolations(s: str) -> str:
    """Replace every ${...} (including nested braces) with a single {p}."""
    out: list[str] = []
    i, n = 0, len(s)
    while i < n:
        if s[i : i + 2] == "${":
            depth, j = 1, i + 2
            while j < n and depth:
                if s[j : j + 2] == "${":
                    depth += 1
                    j += 2
                elif s[j] == "}":
                    depth -= 1
                    j += 1
                else:
                    j += 1
            out.append("{p}")
            i = j
            continue
        out.append(s[i])
        i += 1
    return "".join(out)


def normalize_api(lit: str, absolute: bool = False) -> str:
    s = collapse_interpolations(strip_query(lit))
    # A trailing interpolation appended without '/' (e.g. `/committees${qs}`)
    # is a query suffix, not a path parameter.
    if s.endswith("{p}") and not s.endswith("/{p}"):
        s = s[:-3]
    s = re.sub(r"\{[^}]+\}", "{p}", s)
    s = s.rstrip("/") or "/"
    if not absolute and not s.startswith("/api/"):
        s = "/api" + s
    return s


def pattern_for(path: str) -> re.Pattern[str]:
    return re.compile("^" + re.escape(path).replace(r"\{p\}", "[^/]+") + "$")


def setctx(item: str, page: str = "-", test_induced: bool = False) -> None:
    CTX.update(item=item, page=page, test_induced=test_induced)


def attach_console(page) -> None:
    def on_console(msg) -> None:
        if msg.type in ("error", "warning", "warn"):
            CONSOLE_EVENTS.append(
                {
                    "ts": time.time(),
                    "page": CTX["page"],
                    "item_context": CTX["item"],
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
                "item_context": CTX["item"],
                "test_induced": CTX["test_induced"],
                "type": "pageerror",
                "text": str(exc)[:400],
            }
        )

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)


def add(
    item_id: str,
    category: str,
    source_file_line: str,
    action: str,
    expected: str,
    observed: str,
    verdict: str,
    *,
    extra: dict | None = None,
    resolver: str | None = None,
) -> dict:
    if verdict not in ("PASS", "FAIL", "SKIP"):
        raise ValueError(f"bad verdict {verdict}")
    if verdict == "SKIP" and not resolver:
        raise ValueError(f"SKIP {item_id} needs a named resolver")
    evidence = OUT / f"v10-evidence-{item_id}.json"
    capture = {
        "item_id": item_id,
        "category": category,
        "source_file_line": source_file_line,
        "served_head": SERVED_HEAD,
        "fleet_source_commit": FLEET_SOURCE_COMMIT,
        "inventory_source_commit": INVENTORY_SOURCE_COMMIT,
        "timestamp": time.time(),
        "action": action,
        "expected": expected,
        "observed": observed,
        "verdict": verdict,
        "base": BASE,
        "console_context": dict(CTX),
        "extra": extra or {},
    }
    if resolver:
        capture["resolver"] = resolver
    evidence.write_text(json.dumps(capture, ensure_ascii=False, indent=2), encoding="utf-8")
    row = {
        "element_id": item_id,
        "category": category,
        "source_file_line": source_file_line,
        "action": action,
        "expected": expected,
        "observed": observed,
        "expected_outcome": expected,
        "observed_outcome": observed,
        "verdict": verdict,
        "status": verdict,
        "evidence_path": str(evidence),
        "browser_evidence": BROWSER_EXTRA.get(item_id, {}),
    }
    if resolver:
        row["resolver"] = resolver
    ROWS.append(row)
    return row


# --------------------------------------------------------------------------- #
# 1. C05 — ten dead controls reconciled as designed-absent
# --------------------------------------------------------------------------- #
def repo_grep(pattern: str, include: tuple[str, ...] = (".ts", ".tsx")) -> list[str]:
    rx = re.compile(pattern)
    hits: list[str] = []
    for p in sorted((REPO / "frontend/src").rglob("*")):
        if not p.is_file() or p.suffix not in include:
            continue
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if rx.search(line):
                hits.append(f"{p.relative_to(REPO)}:{n}: {line.strip()[:160]}")
    return hits


def c05_dead() -> None:
    """Confirms W11 removed the dead branches; absence is the expected state."""
    absent_files = ["PartyComparisonMatrix.tsx", "TimeSlider.tsx"]

    def file_grep(rel: str, pattern: str) -> list[str]:
        rx = re.compile(pattern)
        return [
            f"{rel}:{n}: {line.strip()[:160]}"
            for n, line in enumerate(read_rel(rel).splitlines(), 1)
            if rx.search(line)
        ]

    checks = [
        (
            "C05-017",
            "EmptyState CTA branch",
            "frontend/src/components/EmptyState.tsx",
            "onCta|ctaLabel|<button",
            file_grep("frontend/src/components/EmptyState.tsx", "onCta|ctaLabel|<button"),
        ),
        (
            "C05-019",
            "LoadingState retry branch",
            "frontend/src/components/LoadingState.tsx",
            "onRetry|retryLabel|RetryButton",
            file_grep("frontend/src/components/LoadingState.tsx", "onRetry|retryLabel|RetryButton"),
        ),
        (
            "C05-022",
            "DashboardCard onClick button branch",
            "frontend/src/components/DashboardCard.tsx",
            "onClick|<button",
            file_grep("frontend/src/components/DashboardCard.tsx", "onClick|<button"),
        ),
        ("C05-037", "PartyComparisonMatrix cell button", absent_files[0], "component importer", []),
        (
            "C05-038",
            "PartyComparisonMatrix view-all button",
            absent_files[0],
            "component importer",
            [],
        ),
        (
            "C05-039",
            "PartyComparisonMatrix scroll region",
            absent_files[0],
            "component importer",
            [],
        ),
        ("C05-043", "TimeSlider play/pause button", absent_files[1], "component importer", []),
        ("C05-044", "TimeSlider range input", absent_files[1], "component importer", []),
        (
            "C05-057",
            "AgeDistributionRadial interactive arcs",
            "AgeDistributionRadial.tsx",
            "onCohortClick",
            repo_grep("onCohortClick"),
        ),
        (
            "C05-060",
            "AsyncState EmptyState CTA props",
            "frontend/src/components/ui/AsyncState.tsx",
            "onEmptyCta|emptyCtaLabel",
            file_grep("frontend/src/components/ui/AsyncState.tsx", "onEmptyCta|emptyCtaLabel"),
        ),
    ]
    for eid, label, src, pattern, hits in checks:
        setctx(eid)
        if eid in ("C05-037", "C05-038", "C05-039", "C05-043", "C05-044"):
            component = src
            present = (REPO / "frontend/src/components" / component).exists()
            refs = repo_grep(component.replace(".tsx", ""))
            ok = (not present) and not refs
            obs = (
                f"component file present={present}; repo references={len(refs)}; sample={refs[:3]}"
            )
            detail = {"component": component, "references": refs}
        elif eid == "C05-057":
            # Component remains but the interactive branch needs onCohortClick.
            comp = REPO / "frontend/src/components/AgeDistributionRadial.tsx"
            present = comp.exists()
            section = read_rel("frontend/src/components/ui/AgeDistributionSection.tsx")
            caller_passes = "onCohortClick" in section
            ok = present and not hits and not caller_passes
            obs = (
                f"AgeDistributionRadial present={present}; onCohortClick hits={len(hits)}; "
                f"sole caller passes prop={caller_passes}"
            )
            detail = {"hits": hits, "caller_passes": caller_passes}
        else:
            ok = not hits
            obs = f"{label}: supplier/handler hits={len(hits)}; sample={hits[:3]}"
            detail = {"hits": hits, "pattern": pattern}
        add(
            eid,
            "C05-dead",
            src,
            f"source-parsed designed-absence of {label}",
            f"{label} absent or unreachable (removed by W11 repair)",
            obs,
            "PASS" if ok else "FAIL",
            extra=detail,
        )


# --------------------------------------------------------------------------- #
# 2. C06 — 100 destination targets, re-derived from source
# --------------------------------------------------------------------------- #
def registered_routes(router: str) -> list[str]:
    return re.findall(r'path:\s*"([^"]+)"', router)


def route_matches(target: str, route: str) -> bool:
    if target == route:
        return True
    ts, rs = target.strip("/").split("/"), route.strip("/").split("/")
    if len(ts) != len(rs):
        return False
    return all(r.startswith("$") or t == r for t, r in zip(ts, rs, strict=False))


def matched_routes(target: str, routes: list[str]) -> list[str]:
    return [r for r in routes if route_matches(target, r)]


def client_api_calls(text: str) -> list[dict]:
    calls: list[dict] = []
    for m in re.finditer(r"get\s*<[^>]*>\s*\(", text):
        prefix = text[max(0, m.start() - 40) : m.start()]
        if re.search(r"(?:function|const)\s+get\s*$", prefix):
            continue  # the declaration get<T>(path: string), not a call
        window = text[m.end() : m.end() + 160]
        qm = re.search(r"([`\"'])(/)", window)
        if not qm:
            continue
        idx = m.end() + qm.start(1)
        lit, _ = extract_literal(text, idx)
        if lit and lit.startswith("/"):
            calls.append({"line": line_of(text, idx), "literal": lit, "kind": "get"})
    for m in re.finditer(r"withScope\s*\(\s*([`\"'])", text):
        lit, _ = extract_literal(text, m.start(1))
        if lit and lit.startswith("/"):
            calls.append({"line": line_of(text, m.start(1)), "literal": lit, "kind": "withScope"})
    return calls


def backend_routes() -> list[dict]:
    rows: list[dict] = []
    for py in sorted((REPO / "backend/routers").glob("*.py")):
        text = py.read_text(encoding="utf-8")
        pm = re.search(r'APIRouter\s*\(\s*prefix\s*=\s*"([^"]*)"', text)
        prefix = pm.group(1) if pm else ""
        for m in re.finditer(r'@router\.(get|post|put|delete|patch)\s*\(\s*"([^"]*)"', text):
            rows.append(
                {
                    "method": m.group(1),
                    "path": re.sub(r"\{[^}]+\}", "{p}", prefix + m.group(2)),
                    "raw": prefix + m.group(2),
                    "file": str(py.relative_to(REPO)),
                    "line": line_of(text, m.start()),
                }
            )
    return rows


# page-level route literals from C06 §1 (target-literal based, tolerant of line drift)
PAGE_ROUTE_TARGETS = [
    ("pages/LiveDashboard.tsx", "/party/$shortName", "LiveDashboard.tsx:88"),
    ("pages/LiveDashboard.tsx", "/person/$id", "LiveDashboard.tsx:96"),
    ("pages/LiveDashboard.tsx", "/parties", "LiveDashboard.tsx:220"),
    ("pages/LiveDashboard.tsx", "/mps", "LiveDashboard.tsx:261"),
    ("pages/LiveDashboard.tsx", "/traseism", "LiveDashboard.tsx:277"),
    ("pages/LiveDashboard.tsx", "/person/$id", "LiveDashboard.tsx:300"),
    ("pages/SwitchLeaderboard.tsx", "/person/$id", "SwitchLeaderboard.tsx:161"),
    ("pages/PartyComparison.tsx", "/parties", "PartyComparison.tsx:167"),
    ("pages/MpComparison.tsx", "/person/$id", "MpComparison.tsx:195"),
    ("pages/Committees.tsx", "/person/$id", "Committees.tsx:34"),
    ("pages/Committees.tsx", "/person/$id", "Committees.tsx:345"),
    ("pages/PartyTimeline.tsx", "/parties", "PartyTimeline.tsx:128"),
    ("pages/Mps.tsx", "/person/$id", "Mps.tsx:158"),
    ("pages/LegislatureDetail.tsx", "/person/$id", "LegislatureDetail.tsx:195"),
    ("pages/Parties.tsx", "/party/$shortName", "Parties.tsx:46"),
    (
        "components/DashboardCard.tsx",
        "/mps|/traseism|/committees",
        "DashboardCard.tsx:81 (linkTo values LiveDashboard.tsx:140/151/162/174)",
    ),
]

# C06 §3 external URL literals E01..E07, with the 2026-11-22 probe correspondence
EXTERNAL = [
    (
        "E01",
        "https://github.com/nedaktov-ops/parlament-deschis",
        "present",
        "https://github.com/nedaktov-ops/parlament-deschis",
        200,
    ),
    (
        "E02",
        "https://github.com/parlament-deschis",
        "absent-by-design",
        "https://github.com/parlament-deschis",
        404,
    ),
    (
        "E03",
        "https://github.com/nedaktov-ops/parlament-deschis/blob/main/docs/METHODOLOGY.md",
        "present",
        "https://github.com/nedaktov-ops/parlament-deschis/blob/main/docs/METHODOLOGY.md",
        200,
    ),
    (
        "E04",
        "https://www.wikidata.org/wiki/",
        "present-template",
        "https://www.wikidata.org/wiki/Q42",
        200,
    ),
    (
        "E05",
        "https://www.gnu.org/licenses/agpl-3.0.html",
        "present",
        "https://www.gnu.org/licenses/agpl-3.0.html",
        200,
    ),
    (
        "E06",
        "https://creativecommons.org/licenses/by/4.0/",
        "present",
        "https://creativecommons.org/licenses/by/4.0/",
        200,
    ),
    ("E07", "<data-driven href: source_url / snapshot_url / licenses>", "no-literal", None, None),
]

# C06 §4 relative/platform paths (7) + client BASE consistency (1)
RELATIVE = [
    (
        "R01",
        "frontend/src/pages/Report.tsx:172",
        'href="/api/export/report"',
        "vercel.json:7 rewrite + exports.py:25/180",
    ),
    (
        "R02",
        "frontend/src/components/Footer.tsx:66",
        'href="/"',
        "vercel.json:9 catch-all + router.tsx:344",
    ),
    (
        "R03",
        "frontend/src/components/Footer.tsx:74",
        'href="/traseism"',
        "vercel.json:9 catch-all + router.tsx:395",
    ),
    (
        "R04",
        "frontend/src/components/Footer.tsx:82",
        'href="/report"',
        "vercel.json:9 catch-all + router.tsx:466",
    ),
    (
        "R05",
        "frontend/src/components/Footer.tsx:124",
        'href="/coverage"',
        "vercel.json:9 catch-all + router.tsx:402",
    ),
    (
        "R06",
        "frontend/src/router.tsx:232",
        'href="#main-content"',
        "router.tsx main id=main-content",
    ),
    (
        "R07",
        "frontend/src/components/HeaderLogo.tsx:39",
        'src="/api/logo?color=..."',
        "vercel.json:7 rewrite + logo.py:17/64",
    ),
    (
        "R08",
        "frontend/src/api/client.ts:487",
        'const BASE = "/api"',
        "connect-src 'self' (vercel.json:33, backend/main.py:76-77)",
    ),
]


def c06_targets() -> None:
    router = read_rel("frontend/src/router.tsx")
    routes = registered_routes(router)
    client = read_rel("frontend/src/api/client.ts")
    api_calls = client_api_calls(client)
    backend = backend_routes()
    vercel = read_rel("vercel.json")
    read_rel("backend/main.py")

    # -- 27 router.tsx literal targets -------------------------------------
    literals: list[dict] = []
    for rx, kind in [
        (r'<NavLink\s+to="([^"]+)"', "NavLink"),
        (r'<Link\s+to="([^"]+)"', "Link"),
        (r'\bto:\s*"([^"]+)"', "navigate/redirect"),
    ]:
        for m in re.finditer(rx, router):
            literals.append(
                {"line": line_of(router, m.start()), "target": m.group(1), "kind": kind}
            )
    for m in re.finditer(r'href="(/[^"]*)"', router):
        literals.append(
            {"line": line_of(router, m.start()), "target": m.group(1), "kind": "native-href"}
        )
    # the skip link is an in-document fragment, not a route
    fm = re.search(r'href="#main-content"', router)
    if fm:
        literals.append(
            {"line": line_of(router, fm.start()), "target": "#main-content", "kind": "fragment"}
        )

    for lit in literals:
        target = lit["target"]
        if target == "#main-content":
            ok = bool(re.search(r'<main\s+id="main-content"', router))
            obs = f"fragment '#main-content'; <main id=main-content> present={ok}"
            matched: list[str] = ["<in-document fragment>"]
        else:
            matched = matched_routes(target, routes)
            ok = bool(matched)
            obs = f"target={target}; registered routes={len(routes)}; matched={matched}"
        add(
            f"C06-T{len([r for r in ROWS if r['category'] == 'C06-target']) + 1:03d}",
            "C06-target",
            f"frontend/src/router.tsx:{lit['line']}",
            f"resolve literal {lit['kind']} navigation target",
            "target resolves to a registered route",
            obs,
            "PASS" if ok else "FAIL",
            extra={
                "target": target,
                "kind": lit["kind"],
                "matched_routes": matched,
                "registered_routes": routes,
            },
        )

    # -- 16 page-level route literals --------------------------------------
    for rel_path, target_expr, note_line in PAGE_ROUTE_TARGETS:
        text = read_rel("frontend/src/" + rel_path)
        alternatives = target_expr.split("|")
        found = [t for t in alternatives if re.search(re.escape(t).replace(r"\$", r"\$"), text)]
        if rel_path.endswith("DashboardCard.tsx"):
            dash = read_rel("frontend/src/pages/LiveDashboard.tsx")
            found = [t for t in alternatives if t in dash]
        matched = sorted({r for t in found for r in matched_routes(t, routes)})
        ok = bool(found) and bool(matched)
        obs = (
            f"file={'frontend/src/' + rel_path}; target literals found={found}; "
            f"matched routes={matched}"
        )
        add(
            f"C06-T{len([r for r in ROWS if r['category'] == 'C06-target']) + 1:03d}",
            "C06-target",
            note_line,
            "resolve page-level navigation target",
            "target literal still in source and resolves to a registered route",
            obs,
            "PASS" if ok else "FAIL",
            extra={"target_expression": target_expr, "found": found, "matched_routes": matched},
        )

    # -- 40 client.ts API paths (38 get<> calls + 2 export URL builders) ---
    for call in api_calls:
        norm = normalize_api(call["literal"], absolute=(call["kind"] == "withScope"))
        rx = pattern_for(norm)
        matches = [b for b in backend if b["method"] == "get" and rx.match(b["path"])]
        ok = bool(matches)
        obs = (
            f"{call['kind']} literal={call['literal']!r}; effective={norm}; "
            f"backend GET matches={[m['file'] + ':' + str(m['line']) for m in matches]}"
        )
        add(
            f"C06-T{len([r for r in ROWS if r['category'] == 'C06-target']) + 1:03d}",
            "C06-target",
            f"frontend/src/api/client.ts:{call['line']}",
            "parse API path and match a FastAPI decorator",
            "one @router.get decorator with matching prefix and param shape",
            obs,
            "PASS" if ok else "FAIL",
            extra={"literal": call["literal"], "effective_path": norm, "backend_matches": matches},
        )

    # -- 2 hardcoded API URLs outside client.ts -----------------------------
    hardcoded = [
        ("frontend/src/pages/Report.tsx", 172, 'href="/api/export/report"', "/api/export/report"),
        ("frontend/src/components/HeaderLogo.tsx", 39, 'src="/api/logo?color=..."', "/api/logo"),
    ]
    for file, line, quote, eff in hardcoded:
        text = read_rel(file)
        present = quote.split('"')[1].split("?")[0] in text
        rx = pattern_for(eff)
        matches = [b for b in backend if b["method"] == "get" and rx.match(b["path"])]
        ok = present and bool(matches)
        obs = f"literal present={present}; effective={eff}; backend matches={len(matches)}"
        add(
            f"C06-T{len([r for r in ROWS if r['category'] == 'C06-target']) + 1:03d}",
            "C06-target",
            f"{file}:{line}",
            "match hardcoded API URL to decorator",
            "literal unchanged and matched by a GET decorator",
            obs,
            "PASS" if ok else "FAIL",
            extra={"effective_path": eff, "backend_matches": matches},
        )

    # -- 7 external URL literals (also cross-checks the 6 probed literals) --
    probe_rows: list[dict] = []
    for eid, literal, expectation, probed, status in EXTERNAL:
        hits: list[str] = []
        if eid != "E07":
            for p in sorted((REPO / "frontend/src").rglob("*")):
                if (
                    p.is_file()
                    and p.suffix in (".ts", ".tsx")
                    and literal in p.read_text(encoding="utf-8")
                ):
                    hits.append(str(p.relative_to(REPO)))
        if expectation == "present":
            ok = bool(hits)
        elif expectation == "present-template":
            ok = bool(hits)  # template base present, Q42 is a probe-only sample
        elif expectation == "absent-by-design":
            ok = not hits  # L-03 fix removed the bare-org 404 literal
        else:
            ok = False  # E07 has no literal -> SKIP with resolver
        if probed:
            probe_rows.append(
                {
                    "probe_url": probed,
                    "probe_http_status_2026_11_22": status,
                    "source_literal": literal,
                    "expected_source_state": expectation,
                    "current_source_files": hits,
                    "unchanged": ok,
                }
            )
        if eid == "E07":
            add(
                f"C06-T{len([r for r in ROWS if r['category'] == 'C06-target']) + 1:03d}",
                "C06-target",
                "C06 §3 E07 / LINK-URL-REACHABILITY §Limits",
                "verify data-driven external href literals in source",
                "a literal to compare against the dated probe",
                "no literal: href values come from API fields (source_url, snapshot_url, licenses)",
                "SKIP",
                resolver="API payload comparison against the live endpoint "
                "(per LINK-URL-REACHABILITY-2026-11-22.md §Limits)",
                extra={"category": "external-no-literal"},
            )
            continue
        obs = (
            f"literal={literal!r}; expected={expectation}; source files={hits}; "
            f"probe URL={probed} (status {status} on 2026-11-22)"
        )
        add(
            f"C06-T{len([r for r in ROWS if r['category'] == 'C06-target']) + 1:03d}",
            "C06-target",
            f"C06 §3 {eid}",
            "compare probed external URL literal with current source (no network call)",
            f"source literal state '{expectation}' unchanged since the dated probe",
            obs,
            "PASS" if ok else "FAIL",
            extra={
                "literal": literal,
                "source_files": hits,
                "probed_url": probed,
                "probe_status": status,
            },
        )
    OUT.mkdir(parents=True, exist_ok=True)
    URLPROBE_PATH.write_text(
        json.dumps(
            {
                "source_note": "60-EVIDENCE/LINK-URL-REACHABILITY-2026-11-22.md",
                "probe_timestamp": "2026-11-22T20:49:44Z",
                "no_new_network_calls": True,
                "rows": probe_rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # -- 8 relative/platform paths -----------------------------------------
    for rid, src, quote, expectation in RELATIVE:
        file_part = src.split(":")[0]
        text = read_rel(file_part)
        needle = re.sub(r'"[^"]*"$', '"', quote)
        needle = needle.replace('src="/api/logo?color=..."', "/api/logo?color=")
        needle = needle.replace('href="#main-content"', 'href="#main-content"')
        present = needle.strip('"') in text or needle in text
        if rid == "R06":
            present = 'href="#main-content"' in text and 'id="main-content"' in text
        if rid == "R08":
            present = 'BASE = "/api"' in text and "connect-src 'self'" in vercel
        route_part = ""
        if rid in ("R02", "R03", "R04", "R05"):
            path = quote.split('"')[1]
            route_part = f"; registered={bool(matched_routes(path, routes))}"
            present = present and bool(matched_routes(path, routes))
        rewrite_ok = True
        if rid in ("R01", "R07"):
            rewrite_ok = '"/api/:path*"' in vercel
            present = present and rewrite_ok
        obs = f"source literal present={present}; platform expectation={expectation}{route_part}"
        add(
            f"C06-T{len([r for r in ROWS if r['category'] == 'C06-target']) + 1:03d}",
            "C06-target",
            src,
            "check relative path against platform routing config",
            expectation,
            obs,
            "PASS" if present else "FAIL",
            extra={"quote": quote, "platform": expectation, "rewrite_rule_present": rewrite_ok},
        )


# --------------------------------------------------------------------------- #
# 3. C07 — six harness cross-checks + the two guard subprocesses
# --------------------------------------------------------------------------- #
def run_guards() -> list[dict]:
    commands = [
        ("check_routes_nav.mjs", ["node", "scripts/check_routes_nav.mjs"]),
        ("vault_lint.py", ["python3", "scripts/vault_lint.py"]),
    ]
    out = []
    for name, cmd in commands:
        setctx(f"GUARD-{name}")
        t0 = time.time()
        p = subprocess.run(
            cmd, cwd=str(REPO), capture_output=True, text=True, timeout=180, check=False
        )
        out.append(
            {
                "guard": name,
                "command": " ".join(cmd),
                "exit_code": p.returncode,
                "stdout": p.stdout[:8000],
                "stderr": p.stderr[:4000],
                "duration_s": round(time.time() - t0, 3),
            }
        )
    GUARDS_PATH.write_text(
        json.dumps(
            {
                "served_head": SERVED_HEAD,
                "base": BASE,
                "guards": out,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return out


def c07_checks(guards: list[dict]) -> None:
    gmap = {g["guard"]: g for g in guards}
    routes = registered_routes(read_rel("frontend/src/router.tsx"))

    # C07-001 — ui_validate.py static ROUTES list resolves to registered routes
    ui = read_rel("scripts/ui_validate.py")
    declared = re.findall(r'\(\s*"[^"]*"\s*,\s*(f?"([^"]+)"|"([^"]+)")', ui)
    paths = [a or b for a, b in ((m[1], m[2]) for m in declared)]
    # include the f-string person route explicitly (template resolves to /person/$id)
    if 'f"/person/{PERSON_ID}"' in ui:
        paths.append("/person/$id")
    missing = [p for p in paths if not matched_routes(p, routes)]
    add(
        "C07-001",
        "C07-check",
        "scripts/ui_validate.py:47-75",
        "source-parse the 24 static ROUTES and resolve each against the route tree",
        "all declared routes resolve (no browser/axe run in V-10)",
        f"declared={len(paths)}; unmatched={missing}",
        "PASS" if paths and not missing else "FAIL",
        extra={
            "declared_routes": paths,
            "registered_routes": routes,
            "browser_runtime_check": "not in V-10 scope (other agents; no axe)",
        },
    )

    # C07-002 — axe scan explicitly out of V-10 scope
    add(
        "C07-002",
        "C07-check",
        "scripts/ui_validate.py:113-123",
        "axe violation scan (external /tmp/axe.min.js)",
        "zero axe violations",
        "not run: V-10 is forbidden to run axe; file /tmp/axe.min.js exists but is untracked",
        "SKIP",
        resolver="run scripts/ui_validate.py with /tmp/axe.min.js under the lead's "
        "axe gate (C07-002 is a lead-gated check)",
        extra={"axe_file_present": Path("/tmp/axe.min.js").exists()},
    )

    # C07-003 — ui_state_probe.py retries now include an observable click
    probe = read_rel("scripts/ui_state_probe.py")
    has_presence = 'get_by_role("button", name=RETRY)' in probe
    has_click = ".click(" in probe and "expect_request" in probe
    add(
        "C07-003",
        "C07-check",
        "scripts/ui_state_probe.py:81-104",
        "source-parse the retry presence + click contract",
        "retry control presence asserted and click verified by a fired request/state change",
        f"presence selector={has_presence}; click+request assertion={has_click}",
        "PASS" if has_presence and has_click else "FAIL",
        extra={
            "note": "runtime retry clicks belong to the page agents; V-10 does "
            "not run ui_state_probe.py"
        },
    )

    # C07-004 — check_routes_nav.mjs subprocess + vault_lint.py subprocess
    g1, g2 = gmap["check_routes_nav.mjs"], gmap["vault_lint.py"]
    ok = g1["exit_code"] == 0 and g2["exit_code"] == 0
    add(
        "C07-004",
        "C07-check",
        "scripts/check_routes_nav.mjs + scripts/vault_lint.py",
        "run both static guards as subprocesses and record exit codes",
        "both guards exit 0",
        f"check_routes_nav.mjs exit={g1['exit_code']}; vault_lint.py exit={g2['exit_code']}; "
        f"stdout={g1['stdout'].strip()[:200]!r} / {g2['stdout'].strip()[:200]!r}",
        "PASS" if ok else "FAIL",
        extra={
            "guards": [{"command": g["command"], "exit_code": g["exit_code"]} for g in (g1, g2)],
            "artifact": str(GUARDS_PATH),
        },
    )

    # C07-005 — i18n key-diff contract (source-level; no i18n edit)
    i18n = read_rel("scripts/check_i18n_keys.mjs")
    ok = all(s in i18n for s in ("t(", "missing", "fail("))
    add(
        "C07-005",
        "C07-check",
        "scripts/check_i18n_keys.mjs:1-20",
        "source-parse the key-diff guard contract",
        "guard declares missing / asymmetric / duplicate key failures",
        f"literal t() extraction={'t("' in i18n or 't(' in i18n}; fail() present={'fail(' in i18n}",
        "PASS" if ok else "FAIL",
        extra={"note": "locale-key parity only; no route/API/URL claim"},
    )

    # C07-006 — live-feed props scope assertion contract
    lf = read_rel("scripts/check_livefeed_props.mjs")
    ok = all(s in lf for s in ('[40, "senate", "2024"]', '["recent", "2024", "senate"]'))
    add(
        "C07-006",
        "C07-check",
        "scripts/check_livefeed_props.mjs:104-124",
        "source-parse the LiveFeed single-props scope assertion",
        "asserts recentEvents args and queryKey carry legislature/chamber",
        f"args assertion={'[40, "senate", "2024"]' in lf}; "
        f"queryKey assertion={'["recent", "2024", "senate"]' in lf}",
        "PASS" if ok else "FAIL",
        extra={"note": "onSelect is a stub in this guard; click coverage is other agents'"},
    )


# --------------------------------------------------------------------------- #
# 4. Browser — one Chromium, keyboard-only nav + export/print control
# --------------------------------------------------------------------------- #
async def settle(page, ms: int = 700) -> None:
    try:
        await page.wait_for_load_state("networkidle", timeout=7000)
    except Exception:  # bounded wait; a fixed settle follows
        pass
    await page.wait_for_timeout(ms)


async def active_info(page) -> dict:
    return await page.evaluate("""() => {
      const a = document.activeElement;
      if (!a) return {tag:'', text:'', href:'', id:''};
      return {tag: a.tagName, text: (a.innerText||'').trim().slice(0,80),
              href: a.getAttribute('href')||'', id: a.id||'',
              download: a.hasAttribute ? a.hasAttribute('download') : false};
    }""")


async def tab_until(page, predicate, limit: int = 80) -> tuple[bool, dict, int]:
    for step in range(1, limit + 1):
        await page.keyboard.press("Tab")
        info = await active_info(page)
        if predicate(info):
            return True, info, step
    return False, await active_info(page), limit


async def browser_section(browser) -> None:
    # Context accepts downloads so the export control can be keyboard-activated.
    page = await browser.new_page(accept_downloads=True)
    attach_console(page)
    await page.add_init_script(
        "window.__v10PrintCalls = 0; window.print = function(){ window.__v10PrintCalls++; };"
    )
    try:
        # --- keyboard-only main-nav traversal on / ---
        setctx("C06-NAV", "/")
        await page.goto(BASE + "/", wait_until="load", timeout=30_000)
        await settle(page)
        focus_trail: list[dict] = []
        for _ in range(64):
            await page.keyboard.press("Tab")
            focus_trail.append(await active_info(page))
        expected_hrefs = await page.locator("nav a").evaluate_all(
            "(els) => els.map(e => new URL(e.href).pathname)"
        )
        focused_paths = []
        for info in focus_trail:
            if info["tag"] == "A" and info["href"].startswith("/"):
                focused_paths.append(info["href"].split("?")[0])
        nav_reached = [p for p in expected_hrefs if p in focused_paths]
        nav_ok = len(nav_reached) == len(expected_hrefs) and len(expected_hrefs) == 22
        capture = {
            "page": "/",
            "method": "Tab only (no pointer, no programmatic focus)",
            "tabs": len(focus_trail),
            "expected_nav_paths": expected_hrefs,
            "focused_paths": focused_paths,
            "nav_reached": nav_reached,
            "nav_ok": nav_ok,
            "first_trail": focus_trail[:6],
        }
        KEYBOARD_PATH.write_text(
            json.dumps(capture, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        BROWSER_EXTRA["C07-001"] = {
            "keyboard_evidence": str(KEYBOARD_PATH),
            "nav_reached": len(nav_reached),
        }

        # --- Enter-activate one nav link via keyboard only ---
        setctx("C06-NAV-ENTER", "/")
        await page.goto(BASE + "/", wait_until="load", timeout=30_000)
        await settle(page)
        found, info, steps = await tab_until(
            page, lambda i: i["tag"] == "A" and i["href"].startswith("/report")
        )
        activated = False
        if found:
            await page.keyboard.press("Enter")
            try:
                await page.wait_for_url("**/report*", timeout=8000)
                activated = url_path(page.url) == "/report"
            except Exception:
                activated = False
        capture["enter_activation"] = {
            "target": "/report",
            "focused_by_tab": found,
            "tabs": steps,
            "focused": info,
            "url_after_enter": page.url,
            "activated": activated,
        }
        KEYBOARD_PATH.write_text(
            json.dumps(capture, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # --- one export/print control, keyboard only, on /report ---
        setctx("C06-EXPORT", "/report")
        responses: list[dict] = []

        def on_resp(resp) -> None:
            if "/api/export/report" in resp.url:
                responses.append({"status": resp.status, "url": resp.url})

        page.on("response", on_resp)
        await page.goto(BASE + "/report", wait_until="load", timeout=30_000)
        await settle(page)

        pfound, pinfo, psteps = await tab_until(
            page, lambda i: "Printează" in i["text"] or "Print" in i["text"]
        )
        print_called = False
        if pfound:
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(250)
            print_called = bool(await page.evaluate("window.__v10PrintCalls || 0"))

        dfound, dinfo, dsteps = await tab_until(
            page, lambda i: i["tag"] == "A" and i["download"] and "/api/export/report" in i["href"]
        )
        download_info: dict | None = None
        if dfound:
            try:
                async with page.expect_download(timeout=12_000) as dl:
                    await page.keyboard.press("Enter")
                d = await dl.value
                download_info = {"filename": d.suggested_filename, "url": d.url}
            except Exception as exc:  # record, do not hide
                download_info = {"error": f"{type(exc).__name__}: {str(exc)[:160]}"}
        export_capture = {
            "page": "/report",
            "method": "Tab + Enter only",
            "print_control": {
                "tab_reached": pfound,
                "tabs": psteps,
                "focused": pinfo,
                "window_print_called": print_called,
            },
            "export_control": {
                "tab_reached": dfound,
                "tabs": dsteps,
                "focused": dinfo,
                "download": download_info,
                "responses": responses,
            },
            "verdict": "PASS"
            if (pfound and print_called and dfound and any(r["status"] == 200 for r in responses))
            else "FAIL",
        }
        EXPORT_PATH.write_text(
            json.dumps(export_capture, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        # Attach the captures to the report-nav / export-target rows.
        BROWSER_EXTRA["C06-T009"] = {"keyboard_evidence": str(KEYBOARD_PATH)}
        BROWSER_EXTRA["C06-T084"] = {"export_evidence": str(EXPORT_PATH)}
        BROWSER_EXTRA["C06-T093"] = {"export_evidence": str(EXPORT_PATH)}
        capture["export_control"] = export_capture["verdict"]
        KEYBOARD_PATH.write_text(
            json.dumps(capture, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    finally:
        await page.close()


def url_path(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).path


async def run_browser() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path="/usr/bin/chromium", args=["--no-sandbox"]
        )
        try:
            await browser_section(browser)
        finally:
            await browser.close()


# --------------------------------------------------------------------------- #
# pytest entry point
# --------------------------------------------------------------------------- #
def test_v10_crosscut() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    harness_error = None
    guards: list[dict] = []
    try:
        c05_dead()
        c06_targets()
        guards = run_guards()
        c07_checks(guards)
        asyncio.run(run_browser())
    except Exception as exc:  # noqa: BLE001 - a harness error is recorded, not hidden
        harness_error = exc

    # Browser captures are produced after the static rows; attach them now.
    for row in ROWS:
        if row["element_id"] in BROWSER_EXTRA:
            row["browser_evidence"] = BROWSER_EXTRA[row["element_id"]]

    CONSOLE_PATH.write_text(
        json.dumps(
            {
                "served_head": SERVED_HEAD,
                "base": BASE,
                "axe_run": False,
                "events": CONSOLE_EVENTS,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    RESULTS_PATH.write_text(json.dumps(ROWS, ensure_ascii=False, indent=2), encoding="utf-8")
    TARGETS_PATH.write_text(
        json.dumps(
            [r for r in ROWS if r["category"] == "C06-target"], ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )
    CHECKS_PATH.write_text(
        json.dumps([r for r in ROWS if r["category"] == "C07-check"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    ids = [r["element_id"] for r in ROWS]
    targets = [r for r in ROWS if r["category"] == "C06-target"]
    checks = [r for r in ROWS if r["category"] == "C07-check"]
    dead = [r for r in ROWS if r["category"] == "C05-dead"]
    counts = {v: sum(1 for r in ROWS if r["verdict"] == v) for v in ("PASS", "FAIL", "SKIP")}
    print("\n=== V-10 cross-cutting validation summary ===")
    print(f"served HEAD: {SERVED_HEAD}")
    print(
        f"items={len(ids)} (C05-dead={len(dead)} C06-targets={len(targets)} "
        f"C07-checks={len(checks)})"
    )
    print(f"PASS={counts['PASS']} FAIL={counts['FAIL']} SKIP={counts['SKIP']}")
    for g in guards:
        print(f"guard {g['guard']}: exit={g['exit_code']}")
    for r in ROWS:
        if r["verdict"] in ("FAIL", "SKIP"):
            print(
                f"  {r['verdict']} {r['element_id']}: {r['observed'][:180]}"
                + (f" | resolver: {r['resolver']}" if r.get("resolver") else "")
            )
    print(f"console events: {len(CONSOLE_EVENTS)}")
    for ev in CONSOLE_EVENTS:
        print(f"  {ev['type']} [{ev['item_context']}] {ev['text'][:160]}")
    print(f"results: {RESULTS_PATH}")
    print(f"artifacts: {OUT}/v10-*")
    if harness_error is not None:
        print(f"HARNESS ERROR: {type(harness_error).__name__}: {harness_error!r}")

    # Harness-integrity assertions: a FAIL/SKIP is a finding, not a crash.
    expected = (
        set(C05_IDS)
        | {f"C06-T{i:03d}" for i in range(1, 101)}
        | {f"C07-{i:03d}" for i in range(1, 7)}
    )
    assert set(ids) == expected, (
        f"item mismatch: missing={sorted(expected - set(ids))}, "
        f"extra={sorted(set(ids) - expected)}, duplicates="
        f"{sorted({i for i in ids if ids.count(i) > 1})}"
    )
    assert len(targets) == 100 and len(checks) == 6 and len(dead) == 10
    assert harness_error is None, f"harness error: {harness_error!r}"
    assert all(Path(r["evidence_path"]).exists() for r in ROWS)
