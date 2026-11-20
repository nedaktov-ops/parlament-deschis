"""Capture byte-exact roll-call vote fixtures from the official sources.

Dev-only tool. It is **not** part of the runtime pipeline and it is never
called by the daily build (see the build-isolation test): a third-party
outage must never block the official corpus.

What it does
------------
1. Fetches each target through ``PoliteClient`` - so the project's own
   User-Agent is sent, ``robots.txt`` is honoured, requests are paced and a
   CAPTCHA/challenge page stops the run instead of being bypassed.
2. Writes the **raw response bytes** to ``tests/fixtures/votes/``. The bytes
   are never re-encoded, because cdep.ro serves UTF-8 while its XML prolog
   claims ISO-8859-2 (see FIELD-MAP.md).
3. Writes ``manifest.json``: for every file the source URL, HTTP status,
   byte count and SHA-256. The manifest is the authority - a fixture whose
   hash does not match the manifest is corrupt and every importer must abort.

Usage
-----
    uv run python scripts/capture_vote_fixtures.py
    uv run python scripts/capture_vote_fixtures.py --force   # re-capture

Existing fixtures are never overwritten silently: if the live bytes differ
from the locked fixture the run reports DRIFT and exits non-zero, so a
changed upstream page becomes a reviewed decision instead of an accident.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.sources.client import PoliteClient  # noqa: E402

CDEP = "https://www.cdep.ro/ords/pls/steno"
VOT_PARLAMENT = "https://vot-parlament.ro"

# (filename, url, kind, extra)
#   kind "raw"    -> the whole response body is stored
#   kind "head"   -> only the first N lines of a CSV are stored (the export is
#                    ~1.7 MB; the contract we assert is the header + rows)
TARGETS: tuple[tuple[str, str, str, int], ...] = (
    (
        "cdep_evot2015_day_20261118.xml",
        f"{CDEP}/evot2015.xml?par1=1&par2=20261118",
        "raw",
        0,
    ),
    (
        "cdep_evot2015_day_20261110.xml",
        f"{CDEP}/evot2015.xml?par1=1&par2=20261110",
        "raw",
        0,
    ),
    (
        "cdep_evot2015_nominal_37526.xml",
        f"{CDEP}/evot2015.xml?par1=2&par2=37526",
        "raw",
        0,
    ),
    (
        "cdep_evot2015_nominal_37526.html",
        f"{CDEP}/evot2015.nominal?idv=37526&idl=1",
        "raw",
        0,
    ),
    (
        "cdep_evot2015_nominal_37492.html",
        f"{CDEP}/evot2015.nominal?idv=37492&idl=1",
        "raw",
        0,
    ),
    (
        "vot_parlament_votes_export_head.csv",
        f"{VOT_PARLAMENT}/votes/export.csv",
        "head",
        50,
    ),
    (
        "vot_parlament_vote_37526.json",
        f"{VOT_PARLAMENT}/votes/37526.json",
        "raw",
        0,
    ),
    (
        "vot_parlament_api_votes_37526_404.html",
        f"{VOT_PARLAMENT}/api/votes/37526",
        "raw",
        0,
    ),
)

POLICY = "polite-v1"
CAPTURED_BY = "scripts/capture_vote_fixtures.py"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _head_lines(data: bytes, count: int) -> bytes:
    """Keep the first ``count`` lines, byte-exact, including their endings."""
    if count <= 0:
        return data
    kept: list[bytes] = []
    count_lines = 0
    for line in data.splitlines(keepends=True):
        kept.append(line)
        count_lines += 1
        if count_lines >= count:
            break
    return b"".join(kept)


def _fetch(client: PoliteClient, url: str) -> tuple[int, bytes]:
    """Return (http_status, raw_bytes). A 404 body is data we want to lock."""
    try:
        result = client.get(url)
    except requests.HTTPError as exc:
        response = exc.response
        if response is None:
            raise
        return response.status_code, response.content
    content = result.content if result.content is not None else result.text.encode("utf-8")
    return result.status, content


def capture(out_dir: Path, manifest_path: Path, *, sleep: float, force: bool) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    client = PoliteClient(sleep=sleep)
    entries: list[dict] = []
    drift: list[str] = []

    for filename, url, kind, extra in TARGETS:
        status, raw = _fetch(client, url)
        stored = _head_lines(raw, extra) if kind == "head" else raw
        target = out_dir / filename

        if target.exists() and not force:
            existing = target.read_bytes()
            if existing != stored:
                drift.append(f"{filename}: stored {len(existing)} B != live {len(stored)} B")
                continue
        target.write_bytes(stored)

        entries.append(
            {
                "path": filename,
                "source_url": url,
                "http_status": status,
                "byte_count": len(stored),
                "sha256": _sha256(stored),
                "capture_kind": kind,
                "captured_at": datetime.now(UTC).isoformat(),
                "captured_by": CAPTURED_BY,
                "policy": POLICY,
            }
        )
        print(f"captured {filename}: HTTP {status}, {len(stored)} bytes, sha256={_sha256(stored)}")

    if drift:
        print("\nDRIFT detected (locked fixtures differ from the live sources):")
        for line in drift:
            print(f"  - {line}")
        print("\nRe-run with --force to replace them, and review the diff before committing.")
        return 1

    manifest = {
        "captured_by": CAPTURED_BY,
        "captured_at": datetime.now(UTC).isoformat(),
        "policy": POLICY,
        "sources": {
            "cdep": {
                "base_url": CDEP,
                "licence": "official parliamentary facts (OGL-ROU-1.0)",
                "robots": "https://www.cdep.ro/robots.txt disallows /declaratii/ only",
            },
            "vot_parlament": {
                "base_url": VOT_PARLAMENT,
                "licence": "CC BY 4.0 - cross-check / contract only, never the source of a row",
                "robots": "User-agent: * Allow: / (training bots are disallowed)",
            },
        },
        "files": entries,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"\nmanifest written: {manifest_path} ({len(entries)} files)")
    return 0


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(root / "tests" / "fixtures" / "votes"))
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--sleep", type=float, default=2.5, help="seconds between requests")
    parser.add_argument("--force", action="store_true", help="overwrite locked fixtures")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    manifest_path = Path(args.manifest) if args.manifest else out_dir / "manifest.json"
    return capture(out_dir, manifest_path, sleep=args.sleep, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
