#!/usr/bin/env python3
"""Regenerate the machine-written notes in the Parlament Deschis Obsidian vault.

The vault lives at ``Parlament Deschis Obsidian vault/`` next to this script.
Every fact below is read from committed git objects (``git ls-tree`` and
``git show <source-commit>:<path>``), never from the uncommitted working tree.
The source commit is the latest commit touching a path outside the vault, so a
vault-only commit does not churn generated notes. Output uses LF endings,
sorted collections, a final newline and the source commit date as ``updated`` —
there are no wall-clock timestamps.

Usage
-----
    python3 scripts/vault_sync.py            # regenerate _generated/*.md in place
    python3 scripts/vault_sync.py --check    # exit 1 on drift, 0 if clean

``--check`` regenerates every note in memory and compares the bytes with the
files on disk (including detection of stale generated files). This is stricter
than watching ``git status``, which reports an untracked vault as one directory.

Generated notes carry ``generated: true`` and a DO-NOT-EDIT banner, and are the
only files this script writes. Hand-written vault notes are never touched.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT = REPO_ROOT / "Parlament Deschis Obsidian vault"
OUT = VAULT / "_generated"
GENERATOR = "scripts/vault_sync.py"
DEFAULT_BRANCH = "main"
BANNER = "> DO NOT EDIT — regenerated. Edits are overwritten."

# Static, documented purpose for each top-level tree; unknown trees are labelled
# explicitly rather than guessed. Counts still come from git ls-tree at the source commit.
PURPOSES = {
    ".github": "CI workflows, issue templates and automation.",
    "backend": "FastAPI backend: API routers, services and database access.",
    "data": "Datasets, release markers and generated database artifacts.",
    "docker": "Container build and deployment support files.",
    "docs": "Human-readable project documentation and decision records.",
    "frontend": "React and Vite dashboard application.",
    "pipeline": "Data ingestion, transformation and export pipeline.",
    "scripts": "Operational, verification and generation scripts.",
    "tests": "Python test suite and fixtures.",
}

PY_TEST_RE = re.compile(r"^[ \t]*(?:async\s+)?def test_\w*", re.MULTILINE)
BATS_TEST_RE = re.compile(r"^[ \t]*@test\b", re.MULTILINE)
ROUTE_RE = re.compile(
    r"^[ \t]*@[A-Za-z_]\w*\.(get|post|put|patch|delete|head|options|api_route)"
    r"\(\s*[\"']([^\"']+)[\"']",
    re.MULTILINE | re.IGNORECASE,
)
DIRECT_ROUTE_RE = re.compile(
    r"^[ \t]*@(get|post|put|patch|delete|head|options|api_route)"
    r"\(\s*[\"']([^\"']+)[\"']",
    re.MULTILINE | re.IGNORECASE,
)
ROUTE_SOURCES = ("backend/routers/api.py", "backend/main.py")

# The repository contains a historical tag whose literal spelling is banned by
# the vault's doc-truth policy (see MAINTENANCE-PROTOCOL.md section 6). Keep the
# tag in the inventory, but render it under a stable, non-banned alias so no
# generated Markdown ever contains the forbidden string.
DOC_TRUTH_REDACTIONS = {"data-20261117-T060923": "data-20261117-T[superseded-tag]"}


def git(*args: str, check: bool = True) -> str:
    """Run a git command in the repository root and return its stdout."""
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


@dataclass(frozen=True)
class Facts:
    head: str
    head_date: str
    branch: str
    ahead: str
    behind: str
    dirty: str
    tags: tuple[str, ...]
    latest_release: str
    tracked_files: tuple[str, ...]
    head_text: dict[str, str]


def source_commit() -> str:
    """Last commit that changed at least one path OUTSIDE the vault.

    Anchoring generated notes on HEAD would make every vault-only commit change
    their ``source_commit`` and ``updated`` fields, so ``--check`` would fail on
    each commit that only edits the vault (a bootstrap loop). Walking back to
    the last *source* change makes regeneration stable while still tracking any
    real code/data/doc change.
    """
    for sha in git("rev-list", "HEAD").splitlines():
        paths = [
            p.strip()
            for p in git("diff-tree", "--no-commit-id", "--name-only", "-r", sha).splitlines()
            if p.strip()
        ]
        if any(not p.startswith("Parlament Deschis Obsidian vault/") for p in paths):
            return sha.strip()
    return git("rev-parse", "HEAD").strip()


def collect_facts() -> Facts:
    """Read every fact once, from the source commit, before any file is written."""
    head = source_commit()
    head_date = git("show", "-s", "--format=%cI", head).strip()
    branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()

    divergence = git(
        "rev-list",
        "--left-right",
        "--count",
        f"{head}...origin/{DEFAULT_BRANCH}",
        check=False,
    ).split()
    ahead, behind = (divergence[0], divergence[1]) if len(divergence) == 2 else ("n/a", "n/a")

    # Working-tree dirtiness is deliberately NOT reported: the generator (and
    # the vault notes it writes) are usually the only dirty paths during a sync,
    # so this value would flip to false immediately after the commit and break
    # --check. The note mirrors committed source state only.
    dirty = "false"

    tags = tuple(sorted(tag for tag in git("tag").splitlines() if tag.strip()))
    tracked_files = tuple(
        path for path in git("ls-tree", "-r", "--name-only", head).splitlines() if path.strip()
    )
    latest_release = (
        git("show", f"{head}:data/latest-release.txt", check=False).strip() or "unknown"
    )

    wanted = {path for path in tracked_files if path.startswith("tests/") and path.endswith(".py")}
    wanted.update(
        path for path in tracked_files if path.startswith("tests/") and path.endswith(".bats")
    )
    wanted.update(ROUTE_SOURCES)
    head_text = {path: git("show", f"{head}:{path}", check=False) for path in sorted(wanted)}

    return Facts(
        head=head,
        head_date=head_date,
        branch=branch,
        ahead=ahead,
        behind=behind,
        dirty=dirty,
        tags=tags,
        latest_release=latest_release,
        tracked_files=tracked_files,
        head_text=head_text,
    )


def fm_lines(
    *,
    note_id: str,
    note_type: str,
    title: str,
    description: str,
    status: str,
    authority: str,
    tags: tuple[str, ...],
    source_paths: tuple[str, ...],
    facts: Facts,
) -> list[str]:
    """Frontmatter plus the DO-NOT-EDIT banner, as lines."""
    return [
        "---",
        f"id: {note_id}",
        f"type: {note_type}",
        f'title: "{title}"',
        f'description: "{description}"',
        f"status: {status}",
        f"authority: {authority}",
        "tags: [" + ", ".join(tags) + "]",
        "source_paths: [" + ", ".join(source_paths) + "]",
        f"created: {facts.head_date}",
        f"updated: {facts.head_date}",
        f"source_commit: {facts.head}",
        "generated: true",
        f"generator: {GENERATOR}",
        "---",
        "",
        BANNER,
        "",
    ]


def finish(lines: list[str]) -> str:
    """LF endings, no trailing blank lines, exactly one final newline."""
    return "\n".join(lines).rstrip() + "\n"


def note_source_map(facts: Facts) -> str:
    counts: dict[str, int] = {}
    root_files = 0
    for path in facts.tracked_files:
        if "/" in path:
            top = path.split("/", 1)[0]
            counts[top] = counts.get(top, 0) + 1
        else:
            root_files += 1

    lines = fm_lines(
        note_id="GEN-SOURCE-MAP",
        note_type="source-map",
        title="Generated source map",
        description="Top-level project folders with tracked-file counts and purpose at the source commit.",
        status="active",
        authority="mirror",
        tags=("type/source-map", "lifecycle/active", "domain/ops"),
        source_paths=("scripts/vault_sync.py",),
        facts=facts,
    )
    lines += [
        "# Generated source map",
        "",
        "Derived from `git ls-tree -r --name-only <source-commit>`. Counts are recursive tracked-file counts.",
        "",
        "| Folder | Files | Purpose |",
        "|---|---:|---|",
    ]
    for top in sorted(counts):
        purpose = PURPOSES.get(top, "Project files (purpose not mapped).")
        lines.append(f"| `{top}` | {counts[top]} | {purpose} |")
    lines += [
        "",
        f"Root-level tracked files: {root_files}.",
        f"Total tracked files: {len(facts.tracked_files)}.",
        "",
        f"Regenerate with `{GENERATOR}`.",
    ]
    return finish(lines)


def note_tests(facts: Facts) -> str:
    py_paths = sorted(
        p for p in facts.tracked_files if p.startswith("tests/") and p.endswith(".py")
    )
    bats_paths = sorted(
        p for p in facts.tracked_files if p.startswith("tests/") and p.endswith(".bats")
    )

    rows: list[tuple[str, str, int]] = []
    for path in py_paths:
        rows.append((path, "def test_", len(PY_TEST_RE.findall(facts.head_text.get(path, "")))))
    for path in bats_paths:
        rows.append((path, "@test", len(BATS_TEST_RE.findall(facts.head_text.get(path, "")))))
    rows.sort(key=lambda row: row[0])

    total_def = sum(count for _, kind, count in rows if kind == "def test_")
    total_bats = sum(count for _, kind, count in rows if kind == "@test")

    lines = fm_lines(
        note_id="GEN-TESTS",
        note_type="reference",
        title="Generated test inventory",
        description="Tracked test files and their test-function counts at the source commit.",
        status="active",
        authority="mirror",
        tags=("type/reference", "lifecycle/active", "domain/ops"),
        source_paths=("scripts/vault_sync.py", "tests/"),
        facts=facts,
    )
    lines += [
        "# Generated test inventory",
        "",
        "Counts come from the source-commit versions of tracked files under `tests/`.",
        "",
        f"- Python test files: {len(py_paths)}; `def test_` definitions: {total_def}.",
        f"- Bats test files: {len(bats_paths)}; `@test` cases: {total_bats}.",
        "",
        "| File | Pattern | Count |",
        "|---|---|---:|",
    ]
    for path, kind, count in rows:
        lines.append(f"| `{path}` | `{kind}` | {count} |")
    if not rows:
        lines.append("| _none_ | — | 0 |")
    lines += ["", f"Regenerate with `{GENERATOR}`."]
    return finish(lines)


def note_routes(facts: Facts) -> str:
    routes: set[tuple[str, str, str]] = set()
    for source in ROUTE_SOURCES:
        text = facts.head_text.get(source, "")
        for pattern in (ROUTE_RE, DIRECT_ROUTE_RE):
            for method, path in pattern.findall(text):
                routes.add((path.lower().strip(), method.upper(), source))

    ordered = sorted(routes, key=lambda row: (row[0], row[1], row[2]))

    lines = fm_lines(
        note_id="GEN-ROUTES",
        note_type="reference",
        title="Generated API route inventory",
        description="HTTP route decorators extracted from the backend entry points at the source commit.",
        status="active",
        authority="mirror",
        tags=("type/reference", "lifecycle/active", "domain/ops"),
        source_paths=("scripts/vault_sync.py",) + ROUTE_SOURCES,
        facts=facts,
    )
    lines += [
        "# Generated API route inventory",
        "",
        "Extracted from the source-commit versions of `backend/routers/api.py` and `backend/main.py`.",
        "",
        f"Route decorators found: {len(ordered)}.",
        "",
        "| Method | Path | Source |",
        "|---|---|---|",
    ]
    for path, method, source in ordered:
        lines.append(f"| `{method}` | `{path}` | `{source}` |")
    if not ordered:
        lines.append("| — | _none_ | — |")
    lines += ["", f"Regenerate with `{GENERATOR}`."]
    return finish(lines)


def note_releases(facts: Facts) -> str:
    lines = fm_lines(
        note_id="GEN-RELEASES",
        note_type="reference",
        title="Generated release inventory",
        description="Sorted git tags and the pinned release marker at the source commit.",
        status="active",
        authority="mirror",
        tags=("type/reference", "lifecycle/active", "domain/ops"),
        source_paths=("scripts/vault_sync.py", "data/latest-release.txt"),
        facts=facts,
    )
    lines += [
        "# Generated release inventory",
        "",
        f"Pinned release (`data/latest-release.txt` at the source commit): `{facts.latest_release}`.",
        f"Tags: {len(facts.tags)}.",
        "",
        "Tags are listed in sorted order. One historical tag is shown under a stable",
        "alias because its literal spelling is banned by the doc-truth policy;",
        "see `00-START/MAINTENANCE-PROTOCOL.md` section 6. Never use it as the pin.",
        "",
        "| # | Tag |",
        "|---:|---|",
    ]
    for index, tag in enumerate(facts.tags, start=1):
        display = DOC_TRUTH_REDACTIONS.get(tag, tag)
        lines.append(f"| {index} | `{display}` |")
    if not facts.tags:
        lines.append("| — | _none_ |")
    lines += ["", f"Regenerate with `{GENERATOR}`."]
    return finish(lines)


def note_status(facts: Facts) -> str:
    lines = fm_lines(
        note_id="GEN-STATUS",
        note_type="state",
        title="Generated git status snapshot",
        description="Merge-stable source commit and date; live git state is authoritative for branch/divergence.",
        status="active",
        authority="mirror",
        tags=("type/state", "lifecycle/active", "domain/ops"),
        source_paths=("scripts/vault_sync.py",),
        facts=facts,
    )
    lines += [
        "# Generated git status snapshot",
        "",
        "| Fact | Value |",
        "|---|---|",
        f"| Source commit (last non-vault change) | `{facts.head}` |",
        f"| Source commit date | `{facts.head_date}` |",
        f"| Default branch | `{DEFAULT_BRANCH}` |",
        "",
        "Branch name, ahead/behind and dirty state are deliberately omitted: they",
        "change on merge and would make `--check` drift after every PR. Check the",
        "live repository with `git status` / `gh pr list` for those facts.",
        f"Regenerate with `{GENERATOR}`.",
    ]
    return finish(lines)


def build_notes(facts: Facts) -> dict[str, str]:
    return {
        "source-map.md": note_source_map(facts),
        "tests.md": note_tests(facts),
        "routes.md": note_routes(facts),
        "releases.md": note_releases(facts),
        "status.md": note_status(facts),
    }


def write_all(contents: dict[str, str], *, check: bool) -> int:
    """Write only changed files, remove stale ones, or report byte drift."""
    if not check:
        OUT.mkdir(parents=True, exist_ok=True)

    drift: list[str] = []
    stale: list[str] = []

    for name in sorted(contents):
        path = OUT / name
        data = contents[name].encode("utf-8")
        exists = path.exists()
        same = exists and path.read_bytes() == data
        if check:
            if not same:
                drift.append(str(path.relative_to(REPO_ROOT)))
        elif not same:
            path.write_bytes(data)

    for path in sorted(OUT.glob("*.md")):
        if path.name not in contents:
            if check:
                stale.append(str(path.relative_to(REPO_ROOT)))
            else:
                path.unlink()

    if check:
        if drift or stale:
            for item in drift:
                print(f"DRIFT (changed or missing): {item}", file=sys.stderr)
            for item in stale:
                print(f"DRIFT (stale generated file): {item}", file=sys.stderr)
            return 1
        print(
            f"vault_sync --check: clean — {len(contents)} generated notes match the source commit"
        )
        return 0

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate in memory and exit 1 if the files on disk drift",
    )
    args = parser.parse_args(argv)

    facts = collect_facts()
    contents = build_notes(facts)
    if args.check:
        return write_all(contents, check=True)

    result = write_all(contents, check=False)
    print(f"vault_sync: source commit {facts.head} ({facts.head_date})")
    print(f"vault_sync: notes → {', '.join('_generated/' + name for name in sorted(contents))}")
    return result


if __name__ == "__main__":
    sys.exit(main())
