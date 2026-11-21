"""Command-line entry point: parlament <command>.

All commands accept --db PATH (default data/parlament.db).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import func, select

from .assets import process_assets_directory
from .coverage import coverage_snapshot, refresh_coverage
from .db import (
    Event,
    Evidence,
    Membership,
    Organization,
    Person,
    SourceLicense,
    get_session,
    init_db,
    make_engine,
    make_session_factory,
)
from .export import write_export
from .ingest import ingest_cdep_group_ledger, ingest_senator_profile, seed_key_events
from .licenses import ensure_source_licenses
from .parse.cdep_group import parse_group_ledger
from .parse.cdep_votes import (
    chamber_for_cam,
    join_nominal,
    normalize_choice,
    parse_day_index,
    parse_nominal_list,
    parse_nominal_page,
)
from .parse.senat_profile import parse_senator_profile
from .poller import run_poll_cycle, start_poller
from .sources.cdep import CdepSource
from .sources.ches import ChesSource
from .sources.client import PoliteClient
from .sources.party_facts import PartyFactsSource
from .sources.senat import SenatSource

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
    # The licence register is setup state: seed it before any data is written.
    licenses = ensure_source_licenses(session)
    seed_key_events(session)
    session.commit()
    print(f"Database initialized; legislature key events and {licenses} licence rows seeded.")
    return 0


def cmd_licenses_seed(args) -> int:
    """Seed the licence register into source_license (idempotent, local only).

    No ``--apply`` gate: unlike the external-fetch ingesters, this only upserts
    fixed rows into its own table, is safe to re-run, and touches no data that
    a previous run did not already own. It follows ``init`` / ``coverage
    --refresh`` (commit directly) rather than the dry-run ingesters.
    """
    session = get_session(args.db)
    try:
        written = ensure_source_licenses(session)  # commits internally
        total = session.scalar(select(func.count()).select_from(SourceLicense))
    finally:
        session.close()
    print(f"licence register seeded: {written} entries written, {total} rows in source_license")
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
            path.read_text(encoding="utf-8"),
            chamber="deputies",
            legislature="2024",
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
            path.read_text(encoding="utf-8"),
            guid=guid,
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
        totals = cdep.ingest_groups(
            session, args.legislature, force=args.force, idg_filter=args.idg
        )
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


def cmd_committees(args) -> int:
    """Ingest cdep.ro committee ledger for a legislature.

    Fetches the committee listing, then for each committee ID fetches the
    member ledger and writes Organisation(classification=\"committee\") rows
    and Membership rows to the DB.  Use ``--dry-run`` to report without
    writing.
    """
    from .sources.cdep_committee import CdepCommitteeSource, parse_committee_list
    from .sources.client import PoliteClient

    db_path = args.db or "data/parlament.db"
    session = get_session(db_path)
    client = PoliteClient()
    legislature = args.legislature
    idc_filter = args.idc

    if args.dry_run:
        # Report from fixtures only; never touches the network or the DB.
        items = parse_committee_list(
            open(f"tests/fixtures/cdep_committee_list_{legislature}.html", encoding="utf-8").read()
        )
        if idc_filter:
            items = [i for i in items if i.idc in idc_filter]
        print(f"Committee list for {legislature}: {len(items)} committees")
        for item in items:
            print(f"  idc={item.idc} name={item.name[:60]}")
        print("Dry run: not writing to DB.")
        session.close()
        return 0

    # Live ingest via the source's own idempotent path: per-committee
    # fragment dedupe, per-committee commit, PipelineRun audit row.
    csrc = CdepCommitteeSource(client)
    items = csrc.fetch_committee_list(legislature)
    print(f"Committee list for {legislature}: {len(items)} committees")

    totals = csrc.ingest_committees(session, legislature, idc_filter=idc_filter or None)
    print(
        f"Committees ingested: {totals['committees']} committees, "
        f"{totals['current']} current members, {totals['former']} former members, "
        f"{totals['persons']} persons, {totals['unchanged']} unchanged"
    )
    session.close()
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
        leg_list = [leg for leg in leg_list if leg >= args.from_leg]
    if args.to_leg:
        leg_list = [leg for leg in leg_list if leg <= args.to_leg]

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
    from .enrich import run_enrichment

    results = run_enrichment(limit=args.limit, dry_run=args.dry_run, legislature=args.legislature)
    print("\nResults:")
    print(f"  Auto-accept: {results['auto_accept']}")
    print(f"  Review queue: {results['review']}")
    print(f"  Rejected: {results['reject']}")
    print(f"  Errors: {results['error']}")
    if args.dry_run:
        print("\nDRY RUN - no changes written. Use --apply to persist.")
    return 0


def cmd_partyfacts(args) -> int:
    """Ingest Party Facts covariates (CC0, Dataverse DOI:10.7910/DVN/TJINLQ).

    Downloads external-parties.csv, parses ROU rows, and matches them to
    existing Organization records by normalized name. Matched organizations
    get their partyfacts_id populated for ideological covariate joins.
    """
    session = get_session(args.db)
    source = PartyFactsSource()
    totals = source.ingest_partyfacts(session)
    print("\nParty Facts ingestion results:")
    print(f"  Rows seen:    {totals['rows_seen']}")
    print(f"  ROU rows:     {totals['rows_rou']}")
    print(f"  Matched:      {totals['rows_matched']}")
    print(f"  Unmatched:    {totals['rows_unmatched']}")
    print(f"  Updated:      {totals['rows_updated']}")
    if args.apply:
        session.commit()
        print("  Changes written to database.")
    else:
        session.rollback()
        print("  DRY RUN - no changes written. Use --apply to persist.")
    return 0


def cmd_ches(args) -> int:
    """Ingest CHES covariates (CC BY 4.0, Dataverse DOI:10.7910/DVN/TJINLQ).

    Downloads the CHES trend CSV, parses ROU rows (country code 12), and
    matches them to existing Organization records by normalized name.
    Matched organizations get their ideology covariates stored in the
    party_ideology table.
    """
    session = get_session(args.db)
    source = ChesSource()
    totals = source.ingest_ches(session)
    print("\nCHES ingestion results:")
    print(f"  Rows seen:    {totals['rows_seen']}")
    print(f"  ROU rows:     {totals['rows_romania']}")
    print(f"  Matched:      {totals['rows_matched']}")
    print(f"  Unmatched:    {totals['rows_unmatched']}")
    print(f"  Updated:      {totals['rows_updated']}")
    if args.apply:
        session.commit()
        print("  Changes written to database.")
    else:
        session.rollback()
        print("  DRY RUN - no changes written. Use --apply to persist.")
    return 0


def cmd_votes_import(args) -> int:
    """Import the official roll-call votes from the locked fixtures.

    Dry run by default: nothing is written until ``--apply`` is given.
    """
    from .votes import import_votes

    session = get_session(args.db)
    report = import_votes(
        session,
        args.fixtures,
        dry_run=args.dry_run,
        vote_ids=args.vote_id or None,
    )
    if args.json:
        print(json.dumps(report.as_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"votes seen:           {report.votes_seen}")
        print(f"positions seen:       {report.positions_seen}")
        print(f"positions resolved:   {report.positions_resolved}")
        print(f"  by scheme:          {report.resolved_by_scheme}")
        print(
            f"positions quarantined:{report.unresolved_count:>6} (rejected: {report.rejected_count})"
        )
        print(f"votes written:        {report.votes_written}")
        print(f"positions written:    {report.positions_written}")
        if report.quarantined:
            print("\nquarantined positions (first 10):")
            for item in report.quarantined[:10]:
                print(f"  {item}")
        if args.dry_run:
            print("\nDRY RUN - nothing was written. Re-run with --apply to persist.")
        else:
            print("\nApplied.")
    return 0


def cmd_ingest_votes(args) -> int:
    """Import official roll-call votes from live cdep.ro feed for a date range.

    Fetches day index XML and nominal lists/pages from cdep.ro, parses,
    resolves person identities, and stores Vote/VotePosition/VoteImportRun.

    Dry run by default: nothing is written until ``--apply`` is given.
    """
    from .db import Vote, VotePosition
    from .votes import (
        SOURCE,
        resolve_position,
    )

    session = get_session(args.db)
    client = PoliteClient()

    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)

    total_votes_seen = 0
    total_votes_written = 0
    total_votes_backfilled = 0
    total_positions_seen = 0
    total_positions_written = 0
    total_unresolved = 0
    total_rejected = 0

    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y%m%d")
        day_url = f"https://www.cdep.ro/ords/pls/steno/evot2015.xml?par1=1&par2={date_str}"

        try:
            result = client.get(day_url)
        except Exception as exc:
            print(f"  {date_str}: fetch failed: {exc}")
            current += timedelta(days=1)
            continue

        day_hash = hashlib.sha256(result.content).hexdigest()
        day_records = parse_day_index(result.content)
        if not day_records:
            current += timedelta(days=1)
            continue

        print(f"  {date_str}: {len(day_records)} vote(s)")

        for record in day_records:
            vote_id = record.vote_id

            # Fetch nominal list XML and nominal page HTML
            nominal_xml_url = (
                f"https://www.cdep.ro/ords/pls/steno/evot2015.xml?par1=2&par2={vote_id}"
            )
            nominal_html_url = (
                f"https://www.cdep.ro/ords/pls/steno/evot2015.nominal?idv={vote_id}&idl=1"
            )

            try:
                nominal_xml_res = client.get(nominal_xml_url)
                nominal_html_res = client.get(nominal_html_url)
            except Exception as exc:
                print(f"    {vote_id}: fetch failed: {exc}")
                total_votes_seen += 1
                total_unresolved += 1
                continue

            html_hash = hashlib.sha256(nominal_html_res.text.encode("utf-8")).hexdigest()

            xml_rows = parse_nominal_list(nominal_xml_res.content)
            page_rows = parse_nominal_page(nominal_html_res.text)
            joined = join_nominal(xml_rows, page_rows)

            total_votes_seen += 1

            # Resolve person identities
            resolutions = []
            for position in joined.positions:
                person_id, scheme, reason = resolve_position(
                    session, position.idm, position.cam, position.legislature
                )
                resolutions.append((position, person_id, scheme))
                if person_id is None:
                    total_unresolved += 1
                    if reason == "mandate_check_failed":
                        total_rejected += 1

            # Determine chamber and legislature
            chamber = chamber_for_cam(getattr(record, "camera", None)) or chamber_for_cam(
                joined.positions[0].cam if joined.positions else None
            )
            legislature = joined.positions[0].legislature if joined.positions else None

            # Create Vote record (check for existing by dedup_key)
            vote_key = f"{SOURCE}:{vote_id}"
            existing = session.scalar(select(Vote).where(Vote.dedup_key == vote_key))
            if existing is None:
                vote = Vote(
                    source=SOURCE,
                    native_vote_id=vote_id,
                    chamber=chamber or "",
                    legislature=legislature,
                    vote_time=getattr(record, "time_vote", None),
                    title_raw=getattr(record, "description", None),
                    present=getattr(record, "present", None),
                    not_voting=getattr(record, "not_voting", None),
                    yes=getattr(record, "yes", None),
                    no=getattr(record, "no", None),
                    abstain=getattr(record, "abstain", None),
                    official_vote_url=nominal_html_res.url,
                    source_url=nominal_xml_res.url,
                    snapshot_hash=day_hash,
                    truth_contract_version=None,
                    positions_incomplete=total_unresolved > 0,
                    dedup_key=vote_key,
                )
                session.add(vote)
                session.flush()
                votes_written_this_run = 1
            else:
                vote = existing
                votes_written_this_run = 0
                # A vote imported before snapshot hashing existed keeps a NULL
                # hash forever: the dedup short-circuit never revisits it.
                # Backfill from the bytes fetched in this run, using the same
                # day-index hash as the create path, but never overwrite
                # provenance that is already present. The audit's
                # vote_evidence check requires every vote to be traceable.
                if not existing.snapshot_hash:
                    existing.snapshot_hash = day_hash
                    total_votes_backfilled += 1
                if not existing.source_url:
                    existing.source_url = nominal_xml_res.url

            # Insert VotePositions
            positions_written_this_run = 0
            for position, person_id, scheme in resolutions:
                if person_id is None:
                    continue
                position_key = f"{vote_key}:{person_id}"
                already = session.scalar(
                    select(VotePosition).where(VotePosition.dedup_key == position_key)
                )
                if already is not None:
                    continue
                session.add(
                    VotePosition(
                        vote_id=vote.id,
                        person_id=person_id,
                        idm_raw=position.idm,
                        cam_raw=position.cam,
                        name_raw=position.name_raw,
                        group_raw=position.group_html or position.group_xml,
                        raw_vote=position.vote_raw,
                        choice=normalize_choice(position.vote_raw),
                        resolution_scheme=scheme,
                        source_url=nominal_html_res.url,
                        snapshot_hash=html_hash,
                        dedup_key=position_key,
                    )
                )
                positions_written_this_run += 1

            total_votes_written += votes_written_this_run
            total_positions_written += positions_written_this_run

        current += timedelta(days=1)

    if args.apply:
        session.commit()
        print("\nApplied:")
        print(f"  votes seen:           {total_votes_seen}")
        print(f"  positions seen:       {total_positions_seen}")
        print(f"  votes written:        {total_votes_written}")
        print(f"  votes backfilled:     {total_votes_backfilled}")
        print(f"  positions written:    {total_positions_written}")
        print(f"  positions quarantined:{total_unresolved} (rejected: {total_rejected})")
    else:
        session.rollback()
        print("\nDRY RUN - nothing was written.")
        print(f"  votes seen:           {total_votes_seen}")
        print(f"  positions seen:       {total_positions_seen}")
        print(f"  would write votes:    {total_votes_written}")
        print(f"  would backfill votes: {total_votes_backfilled}")
        print(f"  would write positions:{total_positions_written}")
        print(f"  would quarantine:     {total_unresolved} (rejected: {total_rejected})")

    return 0


def cmd_assets(args) -> int:
    """Extract asset declarations from PDFs in data/assets/{year}/"""
    result = process_assets_directory(args.year, dry_run=args.dry_run)
    print(f"Result: {result}")
    return 0


def cmd_coverage(args) -> int:
    """Derive and print coverage matrix; optionally refresh coverage table."""
    session = get_session(args.db)
    snapshot = coverage_snapshot(session)
    for row in snapshot:
        print(
            f"{row['chamber']:10} {row['legislature']:8} {row['completeness']:8} persons={row['persons']:4}  {row['note'] or ''}"
        )
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
    from .db import Organization as Org

    open_tenures = session.scalars(
        select(Membership)
        .join(Org, Org.id == Membership.org_id)
        .where(Membership.end_date.is_(None), Org.classification == "group")
    ).all()
    seen = {}
    for m in open_tenures:
        key = (m.person_id, m.org_id, m.chamber)
        if key in seen:
            problems += 1
            print(
                f"FAIL: duplicate open tenure person={m.person_id} org={m.org_id} chamber={m.chamber}"
            )
        seen[key] = m.id

    # Memberships without evidence
    from .db import Evidence

    no_ev = session.scalars(
        select(Membership).where(~Membership.id.in_(select(Evidence.membership_id)))
    ).all()
    if no_ev and args.strict:
        problems += len(no_ev)
        print(f"FAIL: {len(no_ev)} memberships without evidence (strict mode)")

    if problems == 0:
        print("OK: no integrity violations.")
    return 1 if problems else 0


def cmd_audit_corpus(args) -> int:
    """Run the corpus audit and report what it found.

    Warnings are reported but do not fail the run. In strict mode, errors
    fail unless they exactly match an explicitly reviewed baseline.
    """
    import json

    from .audit import Finding, audit, finding_fingerprint

    session = get_session(args.db)
    try:
        report = audit(session)
    finally:
        session.close()

    from collections import Counter

    baseline: Counter[str] = Counter()
    baseline_findings: list[dict] = []
    if args.baseline:
        baseline_data = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        if not isinstance(baseline_data, dict) or baseline_data.get("schema_version") != 1:
            raise ValueError(f"unsupported audit baseline schema: {args.baseline}")
        known_findings = baseline_data.get("findings")
        if not isinstance(known_findings, list) or not all(
            isinstance(value, dict) for value in known_findings
        ):
            raise ValueError(f"invalid audit baseline findings: {args.baseline}")
        if any(finding.get("severity") != "error" for finding in known_findings):
            raise ValueError(f"audit baseline may contain only errors: {args.baseline}")
        baseline_findings = known_findings
        try:
            baseline = Counter(
                finding_fingerprint(Finding(**finding)) for finding in known_findings
            )
        except TypeError as exc:
            raise ValueError(f"invalid audit baseline finding shape: {args.baseline}") from exc
        if baseline_data.get("error_findings", len(known_findings)) != len(known_findings):
            raise ValueError(f"audit baseline finding count does not match: {args.baseline}")

    error_fingerprints = Counter(finding_fingerprint(finding) for finding in report.errors)
    new_errors = error_fingerprints - baseline
    unevaluated_findings = [
        finding for finding in report.findings if finding.context.get("not_evaluated") is True
    ]
    unevaluated_checks = {finding.check for finding in unevaluated_findings}
    unevaluated_baseline = Counter(
        finding_fingerprint(Finding(**finding))
        for finding in baseline_findings
        if finding["check"] in unevaluated_checks
    )
    resolved_baseline_findings = (baseline - unevaluated_baseline) - error_fingerprints

    # A check can be unevaluated for two very different reasons. An absent
    # source-page cache is an environmental limitation the reviewed baseline
    # explicitly tolerates (see test_cli.py). A source that is EMPTY in the
    # database (e.g. every mandate deleted) is data loss: the check silently
    # stopped covering the corpus and the gate must fail. Only the latter is
    # promoted to a gate failure; both keep their "not evaluated" count above.
    data_loss_checks = {
        finding.check
        for finding in unevaluated_findings
        if finding.context.get("reason") not in ("cache_missing",)
        and "missing_scopes" not in finding.context
    }
    lost_baseline_findings = Counter(
        finding_fingerprint(Finding(**finding))
        for finding in baseline_findings
        if finding["check"] in data_loss_checks
    )

    print("corpus audit")
    print("-" * 62)
    for check in report.checks:
        print(
            f"  {check['name']:<24} findings={check['findings']:<5} "
            f"errors={check['errors']:<4} warnings={check['warnings']}"
        )
    print("-" * 62)
    for finding in report.findings:
        if finding.severity == "info":
            continue
        where = " ".join(p for p in (finding.chamber, finding.legislature) if p)
        who = finding.name or (finding.person_id or "")[:8]
        print(f"  [{finding.severity.upper()}] {finding.check} {where} {who}: {finding.detail}")

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(
            json.dumps(report.as_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"report written to {args.json}")

    print(f"\n{len(report.errors)} errors, {len(report.warnings)} warnings")
    if args.baseline:
        print(
            f"{sum((error_fingerprints & baseline).values())} known errors, "
            f"{sum(new_errors.values())} new errors, "
            f"{sum(resolved_baseline_findings.values())} resolved baseline findings, "
            f"{sum(unevaluated_baseline.values())} baseline findings not evaluated"
        )
    if args.strict:
        failures: list[str] = []
        new_count = sum(new_errors.values())
        if new_count:
            failures.append(f"{new_count} new error(s) not present in the baseline")
        resolved_count = sum(resolved_baseline_findings.values())
        if resolved_count:
            # A reviewed baseline error that silently disappears is not an
            # improvement: it usually means a check stopped covering the data
            # (an emptied table, a skipped source). Name the affected checks so
            # the failure is actionable instead of a bare exit code.
            resolved_checks = sorted(
                {
                    finding["check"]
                    for finding in baseline_findings
                    if finding_fingerprint(Finding(**finding)) in resolved_baseline_findings
                }
            )
            failures.append(
                f"{resolved_count} reviewed baseline finding(s) no longer reproduced "
                f"in check(s): {', '.join(resolved_checks)}"
            )
        lost_count = sum(lost_baseline_findings.values())
        if lost_count:
            failures.append(
                f"{lost_count} reviewed baseline finding(s) were not evaluated because "
                f"a source was empty in check(s): {', '.join(sorted(data_loss_checks))}"
            )
        if failures:
            print("STRICT AUDIT FAILED: " + "; ".join(failures))
            return 1
    return 0


def cmd_stats(args) -> int:
    session = get_session(args.db)
    print("persons:     ", session.scalar(select(func.count(Person.id))))
    print("organizations:", session.scalar(select(func.count(Organization.id))))
    print("memberships: ", session.scalar(select(func.count(Membership.id))))
    print("events:      ", session.scalar(select(func.count(Event.id))))
    print("evidence:    ", session.scalar(select(func.count(Evidence.id))))
    from .db import Coverage as Cov
    from .db import Fragment, PipelineRun

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
        sys.executable,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if args.reload:
        cmd.append("--reload")
    return subprocess.call(cmd, env=env)


def cmd_build_corpus(args) -> int:
    """Collect the official cdep.ro corpus and ingest it.

    This is the command that builds a real database: every parliamentary group
    ledger for both chambers and every legislature, plus the MP profiles that
    resolve who a member is across mandates. Cached pages are periodically
    revalidated, while their source hashes remain recorded in the manifest.
    """
    import logging

    from .collect import build_corpus
    from .ingest_corpus import ingest_corpus
    from .sources.client import PoliteClient

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger("parlament.cli")
    if args.current_cache_ttl_hours < 0 or args.historical_cache_ttl_hours < 0:
        raise ValueError("cache TTL hours must not be negative")

    chambers = ["deputies", "senate"] if args.chamber == "both" else [args.chamber]
    all_legislatures = sorted(_load_legislatures())
    current_legislature = all_legislatures[-1] if all_legislatures else None
    legislatures = all_legislatures.copy()
    if args.from_leg:
        legislatures = [y for y in legislatures if y >= args.from_leg]
    if args.to_leg:
        legislatures = [y for y in legislatures if y <= args.to_leg]
    if args.strict and not legislatures:
        log.error("strict corpus collection selected no legislatures")
        return 1

    client = PoliteClient(sleep=args.sleep)
    try:
        corpus = build_corpus(
            client,
            chambers,
            legislatures,
            cache_dir=Path(args.cache),
            force=args.force,
            offline=args.offline,
            current_legislature=current_legislature,
            current_cache_ttl=timedelta(hours=args.current_cache_ttl_hours),
            historical_cache_ttl=timedelta(hours=args.historical_cache_ttl_hours),
        )
    finally:
        client.close()

    log.info(
        "collected %d ledgers, %d profiles, %d persons, %d errors",
        len(corpus.ledgers),
        len(corpus.profiles),
        len(set(corpus.clusters.values())),
        len(corpus.errors),
    )

    if args.strict:
        expected_scopes = {
            (chamber, legislature) for chamber in chambers for legislature in legislatures
        }
        ledger_scopes = {(record.chamber, record.legislature) for record in corpus.ledgers}
        profile_mandates = set(corpus.profiles)
        expected_mandates = {
            (record.chamber, record.legislature, row.idm)
            for record in corpus.ledgers
            for row in record.ledger.current + record.ledger.former + record.ledger.name_only
            if row.idm
        }
        completed_mandates = {
            (mandate.chamber, mandate.legislature, mandate.idm) for mandate in profile_mandates
        }
        failures = list(corpus.errors)
        if len(corpus.rosters) != len(expected_scopes):
            failures.append(
                f"expected {len(expected_scopes)} roster pages, got {len(corpus.rosters)}"
            )
        if len(corpus.index_counts) != len(expected_scopes):
            failures.append(
                f"expected {len(expected_scopes)} group indexes, got {len(corpus.index_counts)}"
            )
        if expected_scopes - ledger_scopes:
            failures.append(f"missing ledger scopes: {sorted(expected_scopes - ledger_scopes)}")
        if expected_mandates - completed_mandates:
            failures.append(
                f"missing {len(expected_mandates - completed_mandates)} profiles referenced by ledgers"
            )
        if failures:
            for failure in failures[:20]:
                log.error("strict corpus collection failed: %s", failure)
            if len(failures) > 20:
                log.error("%d additional source failures omitted", len(failures) - 20)
            return 1

    # The three-view cross-check: the group page, the index count and the
    # roster must agree before a row is treated as a current membership.
    from .crosscheck import reconcile_current_membership

    cross = reconcile_current_membership(corpus)
    for exclusion in cross.exclusions:
        log.info(
            "stale current row removed: %s %s %s - %s (%s)",
            exclusion.chamber,
            exclusion.legislature,
            exclusion.name,
            exclusion.reason,
            exclusion.roster_label,
        )
    for unresolved in cross.unresolved:
        log.info(
            "count not reconcilable: %s %s %s published=%s listed=%s agreeing=%s",
            unresolved["chamber"],
            unresolved["legislature"],
            unresolved["group"],
            unresolved["published"],
            unresolved["listed"],
            unresolved["agreeing"],
        )
    log.info(
        "cross-check: %d groups checked, %d reconciled, %d stale rows removed",
        cross.checked_groups,
        cross.reconciled_groups,
        len(cross.exclusions),
    )

    engine = make_engine(args.db)
    init_db(engine)
    session = make_session_factory(engine)()
    try:
        # data.yml builds data/parlament-real.db here, audits it, then runs
        # scripts/prepare_db.py into the shipped data/parlament.db. Seeding
        # before ingest_corpus is the last point at which the register is
        # present in the DB that prepare_db.py copies into the release.
        licence_rows = ensure_source_licenses(session)
        stats = ingest_corpus(session, corpus)
        session.commit()
    finally:
        session.close()
    print("corpus ingest:", stats)
    print(f"licence register: {licence_rows} rows seeded")

    # Features 2 / 11: committees and switch waves are part of the shippable
    # corpus. The API serves a PINNED release database, so anything not built
    # here stays stale in that release. Verified on the 2026-11-17 release:
    # /api/committees = 23, /api/analytics/switch-waves = 142 (both non-empty).
    session = make_session_factory(engine)()
    try:
        if not args.skip_committees and current_legislature:
            from .sources.cdep_committee import CdepCommitteeSource

            committee_client = PoliteClient()
            try:
                totals = CdepCommitteeSource(committee_client).ingest_committees(
                    session, current_legislature
                )
                session.commit()
                log.info("committee ingest: %s", totals)
                # "committees" counts only *changed* fragments, so a healthy
                # idempotent re-run reports 0 there and all pages in
                # "unchanged". Gate on explicit failure plus a non-empty
                # committee source instead, so re-runs pass while an empty or
                # failed/partial ingest still fails the strict build.
                seen = totals["committees"] + totals["unchanged"]
                if args.strict and (totals.get("status") == "FAILURE" or seen == 0):
                    log.error(
                        "strict: committee ingest status=%s, saw %d committees "
                        "(changed=%d, unchanged=%d)",
                        totals.get("status"),
                        seen,
                        totals["committees"],
                        totals["unchanged"],
                    )
                    return 1
            except Exception as exc:  # noqa: BLE001 - strict gate vs best effort
                if args.strict:
                    log.error("strict: committee ingest failed: %s", exc)
                    return 1
                log.warning("committee ingest failed (non-strict): %s", exc)
            finally:
                committee_client.close()

        # Pure SQL from the events just ingested; signature-based dedupe makes
        # repeated builds idempotent.
        from .analytics import derive_all_switch_waves

        waves = derive_all_switch_waves(session)
        session.commit()
        log.info("switch waves derived: %d", waves)
        if args.strict and waves == 0:
            log.error("strict: no switch waves derived from the corpus")
            return 1
    finally:
        session.close()
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="parlament", description="Parlament Deschis pipeline")
    parser.add_argument("--db", default=None, help="SQLite DB path (default data/parlament.db)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="initialize DB + seed legislatures").set_defaults(fn=cmd_init)

    sub.add_parser(
        "licenses-seed",
        help="seed the 15-entry licence register into source_license (idempotent)",
    ).set_defaults(fn=cmd_licenses_seed)

    p_ingest = sub.add_parser("ingest", help="live polite ingest from cdep.ro/senat.ro")
    p_ingest.add_argument("--legislature", default="2024", help="legislature (e.g. 2024)")
    p_ingest.add_argument("--chamber", choices=["deputies", "senate", "both"], default="both")
    p_ingest.add_argument("--force", action="store_true", help="re-ingest unchanged fragments")
    p_ingest.add_argument("--idg", nargs="*", help="filter cdep group idg")
    p_ingest.add_argument("--limit", type=int, help="limit senat profiles")
    p_ingest.set_defaults(fn=cmd_ingest)

    p_committees = sub.add_parser(
        "committees", help="ingest cdep.ro committee ledger for a legislature"
    )
    p_committees.add_argument("--legislature", default="2024", help="legislature (e.g. 2024)")
    p_committees.add_argument("--idc", nargs="+", help="filter by IDC values (e.g. 1 2 51)")
    p_committees.add_argument("--dry-run", action="store_true", help="report without writing to DB")
    p_committees.set_defaults(fn=cmd_committees)

    p_backfill = sub.add_parser(
        "backfill", help="loop legislatures from reference data (deputies primary)"
    )
    p_backfill.add_argument("--from", dest="from_leg", help="start legislature (e.g. 1990)")
    p_backfill.add_argument("--to", dest="to_leg", help="end legislature (e.g. 2024)")
    p_backfill.add_argument("--chamber", choices=["deputies", "senate", "both"], default="deputies")
    p_backfill.add_argument("--force", action="store_true", help="continue on error")
    p_backfill.add_argument("--limit", type=int, help="limit senat profiles")
    p_backfill.set_defaults(fn=cmd_backfill)

    p_poll = sub.add_parser("poll", help="run live diff/reconcile cycle")
    p_poll.add_argument("--once", action="store_true", help="run single cycle and exit")
    p_poll.add_argument("--foreground", action="store_true", help="run continuous in foreground")
    p_poll.add_argument(
        "--interval", type=int, default=30, help="interval minutes (foreground mode)"
    )
    p_poll.add_argument("--legislature", default="2024", help="legislature to poll")
    p_poll.set_defaults(fn=cmd_poll)

    p_export = sub.add_parser("export", help="export Popolo JSON + CSV datasets")
    p_export.add_argument("--out", default="data/exports", help="output directory")
    p_export.add_argument("--format", default="json,csv", help="comma-separated: json,csv")
    p_export.add_argument("--chamber", choices=["deputies", "senate"], help="filter chamber")
    p_export.add_argument("--legislature", help="filter legislature")
    p_export.set_defaults(fn=cmd_export)

    p_enrich = sub.add_parser(
        "enrich", help="Wikidata cross-check/enrichment (conservative, never fabricates)"
    )
    p_enrich.add_argument("--limit", type=int, default=50, help="max persons to enrich")
    p_enrich.add_argument("--dry-run", action="store_true", help="print actions without writing")
    p_enrich.add_argument(
        "--apply", action="store_false", dest="dry_run", help="write changes to DB"
    )
    p_enrich.add_argument("--legislature", default="2024", help="legislature to enrich")
    p_enrich.set_defaults(fn=cmd_enrich)

    p_partyfacts = sub.add_parser(
        "party-facts",
        help="Ingest Party Facts covariates (CC0, Dataverse DOI:10.7910/DVN/TJINLQ)",
    )
    p_partyfacts.add_argument(
        "--apply",
        action="store_true",
        help="write matched partyfacts_id to organizations (default: dry run, no changes)",
    )
    p_partyfacts.set_defaults(fn=cmd_partyfacts)

    p_ches = sub.add_parser(
        "ches",
        help="Ingest CHES covariates (CC BY 4.0, Dataverse DOI:10.7910/DVN/TJINLQ)",
    )
    p_ches.add_argument(
        "--apply",
        action="store_true",
        help="write matched ideology covariates to database (default: dry run, no changes)",
    )
    p_ches.set_defaults(fn=cmd_ches)

    p_votes = sub.add_parser(
        "votes-import",
        help="import the official cdep.ro roll-call votes from the locked fixtures (dry run by default)",
    )
    p_votes.add_argument(
        "--fixtures",
        default=str(FX / "votes"),
        help="directory holding manifest.json and the vote fixtures",
    )
    p_votes.add_argument(
        "--vote-id",
        action="append",
        help="only import this native vote id (repeatable)",
    )
    p_votes.add_argument(
        "--apply",
        action="store_false",
        dest="dry_run",
        help="write the votes to the database (default: dry run, nothing is written)",
    )
    p_votes.add_argument("--json", action="store_true", help="print the report as JSON")
    p_votes.set_defaults(fn=cmd_votes_import)

    p_ingest_votes = sub.add_parser(
        "ingest-votes",
        help="ingest official cdep.ro roll-call votes from live feed (dry run by default)",
    )
    p_ingest_votes.add_argument(
        "--start-date",
        required=True,
        help="start date (YYYYMMDD, inclusive)",
    )
    p_ingest_votes.add_argument(
        "--end-date",
        required=True,
        help="end date (YYYYMMDD, inclusive)",
    )
    p_ingest_votes.add_argument(
        "--limit-days",
        type=int,
        default=30,
        help="maximum number of days to scan (default 30)",
    )
    p_ingest_votes.add_argument(
        "--apply",
        action="store_true",
        help="write votes to database (default: dry run, nothing is written)",
    )
    p_ingest_votes.set_defaults(fn=cmd_ingest_votes)

    p_assets = sub.add_parser("assets", help="extract asset declarations from PDFs")
    p_assets.add_argument("--year", type=int, required=True, help="year to process")
    p_assets.add_argument("--dry-run", action="store_true", help="print actions without writing")
    p_assets.add_argument("--apply", action="store_false", dest="dry_run", help="write to DB")
    p_assets.set_defaults(fn=cmd_assets)

    p_cov = sub.add_parser("coverage", help="derive and print coverage matrix")
    p_cov.add_argument("--refresh", action="store_true", help="write to coverage table")
    p_cov.set_defaults(fn=cmd_coverage)

    p_verify = sub.add_parser("verify", help="run integrity checks")
    p_verify.add_argument(
        "--strict",
        action="store_true",
        help="also fail when a membership has no evidence row",
    )
    p_verify.set_defaults(fn=cmd_verify)

    sub.add_parser("stats", help="print row counts").set_defaults(fn=cmd_stats)

    p_corpus = sub.add_parser(
        "build-corpus",
        help="collect the official cdep.ro corpus (both chambers, all legislatures) and ingest it",
    )
    p_corpus.add_argument("--chamber", choices=["deputies", "senate", "both"], default="both")
    p_corpus.add_argument("--from", dest="from_leg", help="first legislature (e.g. 1990)")
    p_corpus.add_argument("--to", dest="to_leg", help="last legislature (e.g. 2024)")
    p_corpus.add_argument("--cache", default="data/cache/cdep", help="HTTP cache directory")
    p_corpus.add_argument("--sleep", type=float, default=2.5, help="seconds between requests")
    p_corpus.add_argument("--force", action="store_true", help="refetch even if cached")
    p_corpus.add_argument(
        "--current-cache-ttl-hours",
        type=float,
        default=24,
        help="revalidate current-legislature pages after this many hours",
    )
    p_corpus.add_argument(
        "--historical-cache-ttl-hours",
        type=float,
        default=720,
        help="revalidate historical pages after this many hours (default: 30 days)",
    )
    p_corpus.add_argument(
        "--strict",
        action="store_true",
        help="fail without ingesting if any required source page or profile is missing",
    )
    p_corpus.add_argument(
        "--offline",
        action="store_true",
        help="use only cached responses; never contact the official site",
    )
    p_corpus.add_argument(
        "--skip-committees",
        action="store_true",
        help="skip the live cdep.ro committee ledger (still derives switch waves); "
        "escape hatch if the committee source is temporarily unavailable",
    )
    p_corpus.set_defaults(fn=cmd_build_corpus)

    p_audit = sub.add_parser(
        "audit-corpus",
        help="run the completeness and consistency audit over the corpus",
    )
    p_audit.add_argument(
        "--json",
        default=None,
        help="write the full report as JSON to this path",
    )
    p_audit.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when errors are not present in the optional reviewed baseline",
    )
    p_audit.add_argument(
        "--baseline",
        default=None,
        help="JSON file of reviewed error findings allowed by --strict",
    )
    p_audit.set_defaults(fn=cmd_audit_corpus)

    p_serve = sub.add_parser("serve", help="run FastAPI server via uvicorn")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true")
    p_serve.set_defaults(fn=cmd_serve)

    sub.add_parser("ingest-fixtures", help="load captured fixtures (dev data)").set_defaults(
        fn=cmd_ingest_fixtures
    )

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
