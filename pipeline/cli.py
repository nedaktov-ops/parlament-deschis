"""Command-line entry point: parlament <command>.

All commands accept --db PATH (default data/parlament.db).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import subprocess
from datetime import date
from pathlib import Path

from sqlalchemy import func, select

from .db import (
    Coverage,
    Evidence,
    Event,
    KeyEvent,
    Membership,
    Organization,
    Person,
    get_session,
)
from .ingest import ingest_cdep_group_ledger, ingest_senator_profile, seed_key_events
from .sources.cdep import CdepSource
from .sources.senat import SenatSource
from .poller import run_poll_cycle, start_poller
from .export import write_export, build_popolo, csv_for, CSV_DATASETS
from .coverage import coverage_snapshot, refresh_coverage
from .parse.cdep_group import parse_group_ledger
from .parse.senat_profile import parse_senator_profile
from .approxdate import parse_ro_date

FX = Path(__file__).parent.parent / "tests" / "fixtures"
REF = Path(__file__).parent.parent / "data" / "reference"


def _load_legislatures() -> dict:
    path = REF / "legislatures.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _get_legislature_dates(leg: str) -> tuple[date | None, date | None]:
    legs = _load_legislatures()
    if leg in legs:
        start = date.fromisoformat(legs[leg]["start"]) if legs[leg]["start"] else None
        end = date.fromisoformat(legs[leg]["end"]) if legs[leg]["end"] else None
        return start, end
    return None, None


def cmd_init(args) -> int:
    session = get_session(args.db)
    seed_key_events(session)
    session.commit()
    print("Database initialized and legislature key events seeded.")
    return 0


def cmd_ingest_fixtures(args) -> int:
    """Load the captured official-page fixtures into the DB (development data)."""
    session = get_session(args.db)
    seed_key_events(session)
    for fn, idg in [("cdep_group_upr.html", 9), ("cdep_group_psd.html", 1)]:
        path = FX / fn
        if not path.exists():
            continue
        ledger = parse_group_ledger(
            path.read_text(encoding="utf-8"), chamber="deputies", legislature="2024",
            source_url=f"https://www.cdep.ro/ords/pls/parlam/structura2015.gp?cam=2&leg=2024&idg={idg}",
        )
        stats = ingest_cdep_group_ledger(session, ledger, legislature="2024")
        print(f"cdep {ledger.meta.short_name}: {stats}")
    senat_fixtures = [
        ("senat_fisa.html", "007FDD23-B531-407E-A067-9C3796420C8C"),
        ("senat_fisa_udmr.html", "3354F56C-A3E7-4CEA-9DDE-E3BD730D7B7F"),
    ]
    for fn, guid in senat_fixtures:
        path = FX / fn
        if not path.exists():
            continue
        prof = parse_senator_profile(
            path.read_text(encoding="utf-8"), guid=guid,
            profile_url=f"https://www.senat.ro/FisaSenator.aspx?ParlamentarID={guid}",
        )
        stats = ingest_senator_profile(session, prof)
        print(f"senat {prof.name}: {stats}")
    session.commit()
    print("Fixtures ingested.")
    return 0


def cmd_ingest(args) -> int:
    """Live polite ingest from cdep.ro and senat.ro for a legislature."""
    from .sources.client import PoliteClient

    session = get_session(args.db)
    seed_key_events(session)
    client = PoliteClient()

    if args.chamber in ("deputies", "both"):
        cdep = CdepSource(client)
        totals = cdep.ingest_groups(session, args.legislature, force=args.force, idg_filter=args.idg)
        print(f"cdep: {totals}")

    if args.chamber in ("senate", "both"):
        senat = SenatSource(client)
        if args.limit:
            totals = senat.ingest_profiles(session, force=args.force, limit=args.limit)
        else:
            totals = senat.ingest_profiles(session, force=args.force)
        print(f"senat: {totals}")

    session.commit()
    return 0


def cmd_backfill(args) -> int:
    """Loop legislatures from data/reference/legislatures.json (deputies only; senate current only)."""
    from .sources.client import PoliteClient

    session = get_session(args.db)
    seed_key_events(session)
    client = PoliteClient()
    legs = _load_legislatures()

    leg_list = sorted(legs.keys())
    if args.from_leg:
        leg_list = [l for l in leg_list if l >= args.from_leg]
    if args.to_leg:
        leg_list = [l for l in leg_list if l <= args.to_leg]

    print(f"Backfilling legislatures: {leg_list}")
    cdep = CdepSource(client)

    for leg in leg_list:
        print(f"\n=== Legislature {leg} ===")
        try:
            totals = cdep.ingest_groups(session, leg, force=args.force)
            print(f"  cdep: {totals}")
        except Exception as exc:
            print(f"  cdep FAILED: {exc}")
            if not args.force:
                print("  Use --force to continue on error")
                return 1

    # Senate: only current legislature is discoverable via sitemap
    if args.chamber in ("senate", "both"):
        print("\n=== Senate (current only — sitemap limitation) ===")
        senat = SenatSource(client)
        totals = senat.ingest_profiles(session, force=args.force, limit=args.limit)
        print(f"  senat: {totals}")

    session.commit()
    return 0


def cmd_poll(args) -> int:
    """Run live diff/reconcile cycle. --once runs once; --foreground runs continuous with interval."""
    session = get_session(args.db)
    if args.once:
        results = run_poll_cycle(session, args.legislature)
        print(json.dumps(results, indent=2, default=str))
        return 0

    if args.foreground:
        print(f"Starting poller every {args.interval} minutes (Ctrl+C to stop)...")
        scheduler = start_poller(args.interval, args.legislature, args.db)
        try:
            import signal
            signal.signal(signal.SIGINT, lambda *_: scheduler.shutdown())
            signal.signal(signal.SIGTERM, lambda *_: scheduler.shutdown())
            while scheduler.running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.shutdown()
            print("\nPoller stopped.")
        return 0

    print("Use --once or --foreground --interval N")
    return 1


def cmd_export(args) -> int:
    """Export Popolo JSON + CSV datasets to --out directory."""
    session = get_session(args.db)
    formats = tuple(args.format.split(","))
    result = write_export(
        session, args.out, chamber=args.chamber, legislature=args.legislature, formats=formats
    )
    print(f"Written {len(result['files'])} files to {args.out}:")
    for f in result["files"]:
        print(f"  {f}")
    print(f"Counts: {result['counts']}")
    return 0


def cmd_enrich(args) -> int:
    """Wikidata cross-check/enrichment (conservative, never fabricates)."""
    # Placeholder: implement in pipeline/enrich.py
    print("Wikidata enrichment not yet wired (see docs/RESEARCH.md for plan).")
    print("Required: pipeline/enrich.py with SPARQL batch + local cache + disambiguation.")
    return 0


def cmd_coverage(args) -> int:
    """Derive and print coverage matrix; optionally refresh coverage table."""
    session = get_session(args.db)
    snapshot = coverage_snapshot(session)
    for row in snapshot:
        print(f"{row['chamber']:10} {row['legislature']:8} {row['completeness']:8} persons={row['persons']:4}  {row['note'] or ''}")
    if args.refresh:
        n = refresh_coverage(session)
        session.commit()
        print(f"\nRefreshed {n} coverage rows in DB.")
    return 0


def cmd_verify(args) -> int:
    """Integrity checks: no inverted intervals, no orphan memberships, duplicate open tenures, evidence presence."""
    session = get_session(args.db)
    problems = 0

    # Inverted intervals
    inverted = session.scalars(
        select(Membership).where(
            Membership.end_date.is_not(None), Membership.start_date > Membership.end_date
        )
    ).all()
    if inverted:
        problems += len(inverted)
        print(f"FAIL: {len(inverted)} inverted intervals")

    # Orphan memberships
    persons = {p.id for p in session.scalars(select(Person))}
    orgs = {o.id for o in session.scalars(select(Organization))}
    for m in session.scalars(select(Membership)):
        if m.person_id not in persons or m.org_id not in orgs:
            problems += 1
            print(f"FAIL: orphan membership {m.id}")

    # Duplicate open tenures (same person, same org_class=group, same chamber)
    from sqlalchemy import select
    from .db import Organization as Org
    open_tenures = session.scalars(
        select(Membership).join(Org, Org.id == Membership.org_id)
        .where(Membership.end_date.is_(None), Org.classification == "group")
    ).all()
    seen = {}
    for m in open_tenures:
        key = (m.person_id, m.org_id, m.chamber)
        if key in seen:
            problems += 1
            print(f"FAIL: duplicate open tenure person={m.person_id} org={m.org_id} chamber={m.chamber}")
        seen[key] = m.id

    # Memberships without evidence
    no_ev = session.scalars(
        select(Membership).where(
            ~Membership.id.in_(select(Event.membership_id).where(Event.membership_id.is_not(None)))
        )
    ).all()
    # Note: evidence is on Evidence.membership_id, not Event
    from .db import Evidence
    no_ev = session.scalars(
        select(Membership).where(
            ~Membership.id.in_(select(Evidence.membership_id))
        )
    ).all()
    if no_ev and args.strict:
        problems += len(no_ev)
        print(f"FAIL: {len(no_ev)} memberships without evidence (strict mode)")

    if problems == 0:
        print("OK: no integrity violations.")
    return 1 if problems else 0


def cmd_stats(args) -> int:
    session = get_session(args.db)
    print("persons:     ", session.scalar(select(func.count(Person.id))))
    print("organizations:", session.scalar(select(func.count(Organization.id))))
    print("memberships: ", session.scalar(select(func.count(Membership.id))))
    print("events:      ", session.scalar(select(func.count(Event.id))))
    print("evidence:    ", session.scalar(select(func.count(Evidence.id))))
    from .db import Fragment, PipelineRun, Coverage as Cov
    print("fragments:   ", session.scalar(select(func.count(Fragment.id))))
    print("pipeline_run:", session.scalar(select(func.count(PipelineRun.id))))
    print("coverage:    ", session.scalar(select(func.count(Cov.id))))
    return 0


def cmd_serve(args) -> int:
    """Run the FastAPI server via uvicorn."""
    os.chdir(Path(__file__).parent.parent)
    env = os.environ.copy()
    if args.db:
        env["PARLAMENT_DB"] = str(Path(args.db).resolve())
    cmd = [
        sys.executable, "-m", "uvicorn", "backend.main:app",
        "--host", args.host, "--port", str(args.port),
    ]
    if args.reload:
        cmd.append("--reload")
    return subprocess.call(cmd, env=env)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="parlament", description="Parlament Deschis pipeline")
    parser.add_argument("--db", default=None, help="SQLite DB path (default data/parlament.db)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="initialize DB + seed legislatures").set_defaults(fn=cmd_init)

    p_ingest = sub.add_parser("ingest", help="live polite ingest from cdep.ro/senat.ro")
    p_ingest.add_argument("--legislature", default="2024", help="legislature (e.g. 2024)")
    p_ingest.add_argument("--chamber", choices=["deputies", "senate", "both"], default="both")
    p_ingest.add_argument("--force", action="store_true", help="re-ingest unchanged fragments")
    p_ingest.add_argument("--idg", nargs="*", help="filter cdep group idg")
    p_ingest.add_argument("--limit", type=int, help="limit senat profiles")
    p_ingest.set_defaults(fn=cmd_ingest)

    p_backfill = sub.add_parser("backfill", help="loop legislatures from reference data (deputies primary)")
    p_backfill.add_argument("--from", dest="from_leg", help="start legislature (e.g. 1990)")
    p_backfill.add_argument("--to", dest="to_leg", help="end legislature (e.g. 2024)")
    p_backfill.add_argument("--chamber", choices=["deputies", "senate", "both"], default="deputies")
    p_backfill.add_argument("--force", action="store_true", help="continue on error")
    p_backfill.add_argument("--limit", type=int, help="limit senat profiles")
    p_backfill.set_defaults(fn=cmd_backfill)

    p_poll = sub.add_parser("poll", help="run live diff/reconcile cycle")
    p_poll.add_argument("--once", action="store_true", help="run single cycle and exit")
    p_poll.add_argument("--foreground", action="store_true", help="run continuous in foreground")
    p_poll.add_argument("--interval", type=int, default=30, help="interval minutes (foreground mode)")
    p_poll.add_argument("--legislature", default="2024", help="legislature to poll")
    p_poll.set_defaults(fn=cmd_poll)

    p_export = sub.add_parser("export", help="export Popolo JSON + CSV datasets")
    p_export.add_argument("--out", default="data/exports", help="output directory")
    p_export.add_argument("--format", default="json,csv", help="comma-separated: json,csv")
    p_export.add_argument("--chamber", choices=["deputies", "senate"], help="filter chamber")
    p_export.add_argument("--legislature", help="filter legislature")
    p_export.set_defaults(fn=cmd_export)

    p_enrich = sub.add_parser("enrich", help="Wikidata cross-check/enrichment (placeholder)")
    p_enrich.add_argument("--limit", type=int, default=50, help="max persons to enrich")
    p_enrich.add_argument("--dry-run", action="store_true", help="print actions without writing")
    p_enrich.set_defaults(fn=cmd_enrich)

    p_cov = sub.add_parser("coverage", help="derive and print coverage matrix")
    p_cov.add_argument("--refresh", action="store_true", help="write to coverage table")
    p_cov.set_defaults(fn=cmd_coverage)

    sub.add_parser("verify", help="run integrity checks").set_defaults(fn=cmd_verify)

    sub.add_parser("stats", help="print row counts").set_defaults(fn=cmd_stats)

    p_serve = sub.add_parser("serve", help="run FastAPI server via uvicorn")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true")
    p_serve.set_defaults(fn=cmd_serve)

    sub.add_parser("ingest-fixtures", help="load captured fixtures (dev data)").set_defaults(fn=cmd_ingest_fixtures)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())