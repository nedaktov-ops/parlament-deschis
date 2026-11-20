"""Importer for the official roll-call votes.

Policy (the reason this module is small and cautious):

* **Never create a person.** A vote position is stored only against a person
  that already exists in our corpus and is identified by the chamber's own
  id (``idm``). Anything else is quarantined in the import report.
* **Never resolve by name.** Names are carried as evidence, never used to
  merge identities.
* **Dry run writes nothing.** Not a single row - the report is returned to
  the caller and printed by the CLI.
* **A corrupted fixture aborts everything.** The manifest's SHA-256 is
  verified before any row is written.
* **The official numbers are cross-checked.** When the vot-parlament export
  fixture is present, the official totals must match it, otherwise the import
  aborts (``VoteContractError``) and nothing is written.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import Mandate, PersonIdentifier, Vote, VoteImportRun, VotePosition
from .parse.cdep_votes import (
    chamber_for_cam,
    join_nominal,
    normalize_choice,
    parse_day_index,
    parse_nominal_list,
    parse_nominal_page,
)
from .parse.vot_parlament import ContractError, parse_export_csv

log = logging.getLogger("parlament.votes")

SOURCE = "cdep"
PARSER_VERSION = "cdep-votes-1"
RESOLVER_VERSION = "idm-lookup-1"
POLICY_VERSION = "no-fabrication-1"

DAY_FILE_PREFIX = "cdep_evot2015_day_"
NOMINAL_FILE_PREFIX = "cdep_evot2015_nominal_"


class ManifestMismatch(RuntimeError):
    """A fixture does not match the SHA-256 recorded in the manifest."""


class VoteContractError(RuntimeError):
    """The official totals and the independent cross-check disagree."""


@dataclass
class ImportReport:
    """What the importer saw, what it resolved and what it refused to guess."""

    votes_seen: int = 0
    votes_written: int = 0
    positions_seen: int = 0
    positions_written: int = 0
    positions_resolved: int = 0
    unresolved_count: int = 0
    rejected_count: int = 0
    resolved_by_scheme: dict[str, int] = field(
        default_factory=lambda: {"cdep_mandate": 0, "cdep_idm": 0, "cdep_person": 0}
    )
    quarantined: list[dict] = field(default_factory=list)
    applied: bool = False
    manifest_sha: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest(fixtures_dir: Path) -> tuple[dict, str]:
    """Verify every fixture against the manifest; return (manifest, sha).

    The manifest is the authority: a fixture whose bytes do not hash to the
    recorded value aborts the import before any write.
    """
    fixtures_dir = Path(fixtures_dir)
    manifest_path = fixtures_dir / "manifest.json"
    raw_manifest = manifest_path.read_bytes()
    manifest = json.loads(raw_manifest.decode("utf-8"))
    for entry in manifest.get("files", []):
        path = fixtures_dir / entry["path"]
        if not path.exists():
            raise ManifestMismatch(f"fixture missing: {entry['path']}")
        data = path.read_bytes()
        if len(data) != entry["byte_count"]:
            raise ManifestMismatch(
                f"{entry['path']}: {len(data)} bytes on disk, manifest says {entry['byte_count']}"
            )
        digest = _sha256(data)
        if digest != entry["sha256"]:
            raise ManifestMismatch(
                f"{entry['path']}: sha256 {digest} does not match manifest {entry['sha256']}"
            )
    return manifest, _sha256(raw_manifest)


def _manifest_sources(manifest: dict) -> dict[str, str]:
    return {entry["path"]: entry["source_url"] for entry in manifest.get("files", [])}


def _manifest_hashes(manifest: dict) -> dict[str, str]:
    return {entry["path"]: entry["sha256"] for entry in manifest.get("files", [])}


def _has_mandate(session: Session, person_id: str, chamber: str, legislature: str) -> bool:
    count = session.scalar(
        select(func.count())
        .select_from(Mandate)
        .where(
            Mandate.person_id == person_id,
            Mandate.chamber == chamber,
            Mandate.legislature == legislature,
        )
    )
    return bool(count)


def resolve_position(
    session: Session, idm: str, cam: str | None, legislature: str | None
) -> tuple[str | None, str | None, str | None]:
    """Resolve an official chamber id to a person in our corpus.

    Returns ``(person_id, scheme, reason)``. ``person_id`` is ``None`` when
    the position cannot be tied to a person; ``reason`` then says why.

    Resolution order (identifier only, never by name):

    1. ``cdep_mandate`` - ``<chamber>:<legislature>:<idm>``;
    2. ``cdep_idm``    - the bare id, accepted only if that person really has
       a mandate in this chamber and legislature;
    3. ``cdep_person`` - the person-level id, same mandate check.
    """
    chamber = chamber_for_cam(cam)
    if chamber is None or not legislature:
        return None, None, "unknown_chamber"

    row = session.execute(
        select(PersonIdentifier.person_id).where(
            PersonIdentifier.scheme == "cdep_mandate",
            PersonIdentifier.identifier == f"{chamber}:{legislature}:{idm}",
            PersonIdentifier.legislature == legislature,
        )
    ).first()
    if row:
        return row[0], "cdep_mandate", None

    rejected = False
    for scheme, identifier in (
        ("cdep_idm", idm),
        ("cdep_person", f"cdep-person:{chamber}:{legislature}:{idm}"),
    ):
        row = session.execute(
            select(PersonIdentifier.person_id).where(
                PersonIdentifier.scheme == scheme,
                PersonIdentifier.identifier == identifier,
                PersonIdentifier.legislature == legislature
                if scheme == "cdep_idm"
                else PersonIdentifier.legislature.is_(None),
            )
        ).first()
        if not row:
            continue
        person_id = row[0]
        if _has_mandate(session, person_id, chamber, legislature):
            return person_id, scheme, None
        rejected = True

    return None, None, "mandate_check_failed" if rejected else "no_identifier"


def _cross_check(fixtures_dir: Path, vote_id: str, day_record) -> str | None:
    """Compare the official totals with the independent vot-parlament export.

    Returns the truth-contract version when the check passed, ``None`` when
    there is nothing to compare with.
    """
    csv_path = fixtures_dir / "vot_parlament_votes_export_head.csv"
    if not csv_path.exists() or day_record is None:
        return None
    try:
        _header, rows = parse_export_csv(csv_path.read_text(encoding="utf-8"))
    except ContractError as exc:
        raise VoteContractError(f"the cross-check export changed its contract: {exc}") from exc
    match = next((r for r in rows if r.get("native_vote_id") == vote_id), None)
    if match is None:
        return None
    comparisons = (
        ("present", "official_present"),
        ("yes", "official_yes"),
        ("no", "official_no"),
        ("abstain", "official_abstain"),
        ("not_voting", "official_not_voted"),
    )
    for ours, theirs in comparisons:
        expected = int(match[theirs])
        actual = getattr(day_record, ours)
        if actual is None or actual != expected:
            raise VoteContractError(
                f"vote {vote_id}: cdep {ours}={actual} but the cross-check says {theirs}={expected}"
            )
    return match.get("truth_contract_version")


def import_votes(
    session: Session,
    fixtures_dir: str | Path,
    *,
    dry_run: bool = True,
    source: str = SOURCE,
    vote_ids: list[str] | None = None,
) -> ImportReport:
    """Import the official roll-call votes from the locked fixtures."""
    fixtures_dir = Path(fixtures_dir)
    manifest, manifest_sha = load_manifest(fixtures_dir)
    sources = _manifest_sources(manifest)
    hashes = _manifest_hashes(manifest)

    report = ImportReport(manifest_sha=manifest_sha)

    day_records: dict[str, object] = {}
    for path in sorted(fixtures_dir.glob(f"{DAY_FILE_PREFIX}*.xml")):
        for record in parse_day_index(path.read_bytes()):
            day_records[record.vote_id] = record

    for xml_path in sorted(fixtures_dir.glob(f"{NOMINAL_FILE_PREFIX}*.xml")):
        vote_id = xml_path.stem.rsplit("_", 1)[-1]
        if vote_ids and vote_id not in vote_ids:
            continue
        html_path = fixtures_dir / f"{NOMINAL_FILE_PREFIX}{vote_id}.html"
        if not html_path.exists():
            log.warning("nominal page missing for vote %s (%s)", vote_id, xml_path.name)
            continue

        xml_rows = parse_nominal_list(xml_path.read_bytes())
        page_rows = parse_nominal_page(html_path.read_text(encoding="utf-8"))
        joined = join_nominal(xml_rows, page_rows)
        day_record = day_records.get(vote_id)

        report.votes_seen += 1
        report.positions_seen += len(xml_rows)

        for row in joined.unmatched_xml:
            report.unresolved_count += 1
            report.quarantined.append(
                {
                    "vote_id": vote_id,
                    "reason": "unmatched_name",
                    "name_raw": f"{row.given_name} {row.family_name}",
                }
            )
        for name in joined.ambiguous_names:
            report.unresolved_count += 1
            report.quarantined.append(
                {"vote_id": vote_id, "reason": "ambiguous_name", "name_raw": name}
            )
        for disagreement in joined.disagreements:
            report.unresolved_count += 1
            report.quarantined.append(
                {"vote_id": vote_id, "reason": "vote_token_disagreement", **disagreement}
            )

        resolutions: list[tuple[object, str | None, str | None]] = []
        for position in joined.positions:
            person_id, scheme, reason = resolve_position(
                session, position.idm, position.cam, position.legislature
            )
            resolutions.append((position, person_id, scheme))
            if person_id is None:
                report.unresolved_count += 1
                if reason == "mandate_check_failed":
                    report.rejected_count += 1
                report.quarantined.append(
                    {
                        "vote_id": vote_id,
                        "reason": reason,
                        "idm_raw": position.idm,
                        "cam_raw": position.cam,
                        "name_raw": position.name_raw,
                        "raw_vote": position.vote_raw,
                    }
                )
                continue
            report.positions_resolved += 1
            report.resolved_by_scheme[scheme] = report.resolved_by_scheme.get(scheme, 0) + 1

        truth_contract = _cross_check(fixtures_dir, vote_id, day_record)

        if dry_run:
            continue

        chamber = chamber_for_cam(getattr(day_record, "camera", None)) or chamber_for_cam(
            joined.positions[0].cam if joined.positions else None
        )
        legislature = joined.positions[0].legislature if joined.positions else None
        vote_key = f"{source}:{vote_id}"
        existing = session.scalar(select(Vote).where(Vote.dedup_key == vote_key))
        if existing is None:
            vote = Vote(
                source=source,
                native_vote_id=vote_id,
                chamber=chamber or "",
                legislature=legislature,
                vote_time=getattr(day_record, "time_vote", None),
                title_raw=getattr(day_record, "description", None),
                present=getattr(day_record, "present", None),
                not_voting=getattr(day_record, "not_voting", None),
                yes=getattr(day_record, "yes", None),
                no=getattr(day_record, "no", None),
                abstain=getattr(day_record, "abstain", None),
                official_vote_url=sources.get(html_path.name),
                source_url=sources.get(xml_path.name, sources.get(html_path.name, "")),
                snapshot_hash=hashes.get(xml_path.name),
                truth_contract_version=truth_contract,
                positions_incomplete=report.unresolved_count > 0,
                dedup_key=vote_key,
            )
            session.add(vote)
            session.flush()
            report.votes_written += 1
        else:
            vote = existing

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
                    source_url=sources.get(html_path.name, ""),
                    snapshot_hash=hashes.get(html_path.name),
                    dedup_key=position_key,
                )
            )
            report.positions_written += 1

    if not dry_run:
        report.applied = True
        run_key = f"votes:{manifest_sha}:{PARSER_VERSION}:{RESOLVER_VERSION}:{POLICY_VERSION}"
        run = session.scalar(select(VoteImportRun).where(VoteImportRun.dedup_key == run_key))
        if run is None:
            run = VoteImportRun(dedup_key=run_key)
            session.add(run)
        run.manifest_sha = manifest_sha
        run.parser_version = PARSER_VERSION
        run.resolver_version = RESOLVER_VERSION
        run.policy_version = POLICY_VERSION
        run.dry_run = False
        run.applied = True
        run.votes_seen = report.votes_seen
        run.votes_written = report.votes_written
        run.positions_seen = report.positions_seen
        run.positions_written = report.positions_written
        run.unresolved_count = report.unresolved_count
        run.rejected_count = report.rejected_count
        run.report = {
            "resolved_by_scheme": report.resolved_by_scheme,
            "quarantined": report.quarantined[:500],
        }
        session.commit()

    return report
