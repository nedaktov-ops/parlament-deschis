#!/usr/bin/env python3
"""Lint the Parlament Deschis Obsidian vault.

Checks (read-only, stdlib only):
  1. Every Markdown note has valid YAML frontmatter with the required fields.
  2. `type`, `status`, `authority`, `tags` use the closed vocabularies.
  3. Every relative Markdown link resolves to an existing file in the vault.
  4. No banned literal strings (the project's doc-truth gate patterns).
  5. Every non-entry note has at least one inbound link (no orphans).
  6. Generated notes carry `generated: true` and the DO-NOT-EDIT banner.

Usage: python3 scripts/vault_lint.py [--vault PATH]
Exit 0 = clean, 1 = findings, 2 = usage/IO error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED = [
    "id",
    "type",
    "title",
    "description",
    "status",
    "authority",
    "tags",
    "source_paths",
    "created",
    "updated",
    "source_commit",
]
TYPES = {
    "moc",
    "state",
    "gap",
    "decision",
    "task",
    "research",
    "evidence",
    "source-map",
    "runbook",
    "reference",
    "archive",
    "daily",
}
STATUSES = {"active", "stale", "archived", "superseded", "open", "in-progress", "done"}
AUTHORITIES = {"canonical", "mirror", "derived", "historical", "unverified"}
LIFECYCLES = {"active", "stale", "archived"}
DOMAINS = {"project", "frontend", "data", "ops", "research"}
BANNED = [
    "0 JS errors",
    "281.ro",
    "data-20261117-T060923",
    "193 passed",
    "199 pytest",
    "Ready for Deployment",
    "3 expected failures",
    "125 passed",
    "273 known errors",
    '"memberships": 12445',
    '"switches": 7429',
    '"legislatures": 10',
    '"parties": 62',
    '"cross_chamber": 461',
    '"coverage_score": 85',
]
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]*)?\)")
ENTRY = "00-START/START-HERE.md"


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    block = text[4:end]
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if line.startswith((" ", "\t", "#")) or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default="Parlament Deschis Obsidian vault")
    args = ap.parse_args()
    root = Path(args.vault).resolve()
    if not root.is_dir():
        print(f"ERROR: vault not found: {root}", file=sys.stderr)
        return 2

    notes = sorted(root.rglob("*.md"))
    findings: list[str] = []
    inbound: dict[str, int] = {p.relative_to(root).as_posix(): 0 for p in notes}

    for p in notes:
        rel = p.relative_to(root).as_posix()
        text = p.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)

        missing = [k for k in REQUIRED if k not in fm]
        if missing:
            findings.append(f"{rel}: missing frontmatter fields: {', '.join(missing)}")
        if fm.get("type") and fm["type"].strip("'\"") not in TYPES:
            findings.append(f"{rel}: unknown type {fm['type']!r}")
        if fm.get("status") and fm["status"].strip("'\"") not in STATUSES:
            findings.append(f"{rel}: unknown status {fm['status']!r}")
        if fm.get("authority") and fm["authority"].strip("'\"") not in AUTHORITIES:
            findings.append(f"{rel}: unknown authority {fm['authority']!r}")
        for tag in re.findall(r"\S+", fm.get("tags", "").strip("[]")):
            tag = tag.strip("'\",")
            if not tag:
                continue
            facet, _, value = tag.partition("/")
            if facet == "type" and value not in TYPES:
                findings.append(f"{rel}: bad type tag {tag!r}")
            elif facet == "lifecycle" and value not in LIFECYCLES:
                findings.append(f"{rel}: bad lifecycle tag {tag!r}")
            elif facet == "domain" and value not in DOMAINS:
                findings.append(f"{rel}: bad domain tag {tag!r}")
            elif facet not in {"type", "lifecycle", "domain"}:
                findings.append(f"{rel}: unknown tag facet {tag!r}")

        for banned in BANNED:
            if banned in text:
                findings.append(f"{rel}: banned literal {banned!r}")

        for target in LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "#")):
                continue
            resolved = (p.parent / target).resolve()
            try:
                rel_target = resolved.relative_to(root).as_posix()
            except ValueError:
                findings.append(f"{rel}: link escapes vault: {target}")
                continue
            if not resolved.exists():
                findings.append(f"{rel}: broken link -> {target}")
            elif rel_target in inbound:
                inbound[rel_target] += 1

        if rel.startswith("_generated/"):
            if "generated: true" not in text or "DO NOT EDIT" not in text:
                findings.append(f"{rel}: generated note missing banner/frontmatter")
        elif "generated: true" in text:
            findings.append(f"{rel}: generated note outside _generated/")

    # Templates, generated notes and daily notes are tooling artifacts, not
    # content notes: they are intentionally not linked from the MOC.
    tool_prefixes = ("Templates/", "_generated/", "Daily Notes/")
    for rel, count in inbound.items():
        if count == 0 and rel != ENTRY and not rel.startswith(tool_prefixes):
            findings.append(f"{rel}: orphan note (no inbound links)")

    if findings:
        print(f"VAULT LINT FAIL: {len(findings)} finding(s)")
        for f in findings:
            print(f"  - {f}")
        return 1
    print(f"VAULT LINT PASS: {len(notes)} notes, all links/frontmatter/vocabularies clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
