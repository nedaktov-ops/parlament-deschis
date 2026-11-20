"""Build isolation: the official corpus build must never touch the votes.

The daily build collects the official cdep.ro/senat.ro corpus. The roll-call
vote importer is a **separate, third-party-dependent** feature. If the vote
code were wired into the corpus build, a vot-parlament.ro outage could stop
the daily dataset release - the exact failure mode the architecture forbids.

This test reads the real build path (not a copy of it) and fails if any
reference to the vote pipeline appears in it.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pipeline.cli

REPO = Path(__file__).resolve().parent.parent

FORBIDDEN_TOKENS = (
    "votes-import",
    "votes_import",
    "import_votes",
    "votes_cdep",
    "votes_thirdparty",
    "vot-parlament",
    "vot_parlament",
)


def _sources() -> dict[str, str]:
    files = [
        REPO / "scripts" / "prepare_db.py",
        REPO / "backend" / "main.py",
        REPO / "Dockerfile",
        REPO / ".github" / "workflows" / "ci.yml",
        REPO / ".github" / "workflows" / "data.yml",
    ]
    out: dict[str, str] = {}
    for path in files:
        assert path.exists(), f"build path file missing: {path}"
        out[str(path.relative_to(REPO))] = path.read_text(encoding="utf-8")
    out["pipeline/cli.py:cmd_build_corpus"] = inspect.getsource(pipeline.cli.cmd_build_corpus)
    return out


def test_the_official_build_never_references_the_vote_pipeline():
    offenders: list[str] = []
    for name, source in _sources().items():
        lowered = source.lower()
        for token in FORBIDDEN_TOKENS:
            if token.lower() in lowered:
                offenders.append(f"{name} contains {token!r}")
    assert not offenders, "vote code leaked into the official build path:\n" + "\n".join(offenders)


def test_the_vote_importer_is_not_wired_into_any_workflow():
    for workflow in ("ci.yml", "data.yml"):
        source = (REPO / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
        assert "votes-import" not in source
        assert "capture_vote_fixtures" not in source


def test_the_capture_script_is_not_imported_by_the_runtime_pipeline():
    for path in sorted((REPO / "pipeline").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "capture_vote_fixtures" not in source
