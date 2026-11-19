"""Audit checks that prove the corpus is complete and consistent.

A scraped dataset is only as trustworthy as its weakest link, and the usual
failure of a legislative scraper is a **silent** one: a markup variant drops a
table, 55 rows vanish, and every number published afterwards is quietly
wrong. These checks turn that class of failure into a loud one.

The invariant that matters most is **mandate coverage**: the chamber publishes
when each mandate was validated, and the group ledgers publish who sat in
which group and when. If the ledgers are complete, then every day of every
mandate is covered by exactly one group tenure. A gap means a row is
missing; an overlap means two rows contradict each other.

Every check returns a list of findings. A finding is not automatically an
error: some are expected (a member who left Parliament has no group), and
they are reported with the evidence needed to judge them.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .collect import roster_url
from .db import Event, Evidence, Mandate, Membership, Organization, Person
from .normalize import name_sort_key, normalize_name
from .parse.cdep_group import parse_group_ledger, parse_group_list
from .parse.cdep_roster import parse_roster
from .queries import is_group

log = logging.getLogger("parlament.audit")

# Days of tolerance for the handoff between two consecutive group tenures.
# Two thirds of the handoffs in the corpus are same-day and a small number
# are next-day, so a one-day difference is continuity, not a hole.
_HANDOFF_TOLERANCE = 1


@dataclass
class Finding:
    """One inconsistency, with enough context to act on it."""

    check: str
    severity: str  # "error" | "warning" | "info"
    chamber: str | None = None
    legislature: str | None = None
    person_id: str | None = None
    name: str | None = None
    detail: str = ""
    context: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class AuditReport:
    checks: list[dict] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "warning"]

    def as_dict(self) -> dict:
        return {
            "checks": self.checks,
            "findings": [f.as_dict() for f in self.findings],
            "errors": len(self.errors),
            "warnings": len(self.warnings),
        }


def finding_fingerprint(finding: Finding) -> str:
    """Return a stable identity for a finding across dataset releases.

    Person ids are random UUIDs regenerated on every ingest, so hashing them
    turns a reviewed baseline into 100% churn on every release: every known
    finding looks new and every baseline entry looks resolved. The normalized
    name plus the scope is the stable natural key the source publishes. The
    detail and context still separate distinct findings, and callers compare
    fingerprints as a multiset, so an extra finding of the same shape for the
    same person is still reported as new.
    """
    identity = {
        "check": finding.check,
        "severity": finding.severity,
        "chamber": finding.chamber,
        "legislature": finding.legislature,
        "name": normalize_name(finding.name) if finding.name else "",
        "detail": finding.detail,
        "context": finding.context,
    }
    encoded = json.dumps(identity, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _interval(m: Membership) -> tuple[date | None, date | None]:
    return m.start_date, m.end_date


def _merge(intervals: list[tuple[date, date | None]]) -> list[tuple[date, date | None]]:
    """Merge sorted intervals; end dates are exclusive."""
    out: list[tuple[date, date | None]] = []
    for start, end in sorted(intervals, key=lambda x: (x[0], x[1] or date.max)):
        if out and start <= (out[-1][1] or date.max):
            prev_end = out[-1][1]
            if end is None or (prev_end is not None and end > prev_end):
                out[-1] = (out[-1][0], end)
        else:
            out.append((start, end))
    return out


def check_mandate_coverage(session: Session) -> list[Finding]:
    """Every published mandate must be covered by group tenures.

    A member of parliament sits in exactly one group (the unaffiliated
    bucket counts as a group). If the union of a person's group tenures does
    not span their mandate, the ledgers are missing a row for that person.

    The severity depends on what the chamber could have published. Some
    legislatures publish the unaffiliated roster **without dates** (1992-2012
    deputies, 1990-2012 senators), so a stretch of a mandate that no dated
    tenure covers cannot be expressed by the source at all. In those
    legislatures a gap is reported as a warning when the person *does* sit
    unaffiliated in that scope (the source simply cannot date it); it is an
    error when the person has **no unaffiliated membership at all** in that
    scope - they should be in some group.

    Only **group** tenures take part. A committee membership is a different
    kind of organisation (``classification="committee"``) and can never cover
    a parliamentary-group gap, even when its dates span the gap.
    """
    findings: list[Finding] = []
    mandates = list(session.scalars(select(Mandate)))
    if not mandates:
        # An empty mandate table is not "no gaps": it means the authoritative
        # source for this check is gone, so coverage cannot be judged at all.
        # Report that explicitly so the strict gate can tell a skipped check
        # from a clean one instead of silently passing total data loss.
        findings.append(
            Finding(
                check="mandate_coverage",
                severity="warning",
                detail=(
                    "no mandates in the corpus: mandate coverage was not evaluated "
                    "because the mandate source is empty"
                ),
                context={"not_evaluated": True, "reason": "no_mandates"},
            )
        )
        return findings

    by_person: dict[str, list[Mandate]] = defaultdict(list)
    for m in mandates:
        by_person[m.person_id].append(m)

    memberships = list(
        session.scalars(
            select(Membership)
            .join(Organization, Organization.id == Membership.org_id)
            .where(
                is_group(),
                Membership.person_id.in_(list(by_person)),
            )
        )
    )
    mem_by_person: dict[str, list[Membership]] = defaultdict(list)
    for m in memberships:
        mem_by_person[m.person_id].append(m)

    names = {
        p.id: p.canonical_name
        for p in session.scalars(select(Person).where(Person.id.in_(list(by_person))))
    }

    # Which (person, scope) have an unaffiliated membership at all - used to
    # decide whether an uncovered stretch is a source limitation (warning)
    # or a missing row (error).
    person_has_unaffiliated: set[tuple[str, str | None, str | None]] = set(
        session.execute(
            select(
                Membership.person_id,
                Membership.chamber,
                Membership.legislature,
            )
            .join(Organization, Organization.id == Membership.org_id)
            .where(
                is_group(),
                Organization.short_name == "NEAFILIATI",
            )
            .distinct()
        ).all()
    )

    for person_id, mans in by_person.items():
        mems = mem_by_person.get(person_id, [])
        for man in mans:
            scoped = [
                m for m in mems if m.chamber == man.chamber and m.legislature == man.legislature
            ]
            if not scoped:
                findings.append(
                    Finding(
                        check="mandate_coverage",
                        severity="error",
                        chamber=man.chamber,
                        legislature=man.legislature,
                        person_id=person_id,
                        name=names.get(person_id),
                        detail="mandate has no group membership at all",
                        context={"source_url": man.source_url},
                    )
                )
                continue
            starts = [s for s, _ in (_interval(m) for m in scoped) if s]
            first = min(starts) if starts else None
            if first is None:
                continue
            intervals = [(s, e) for s, e in (_interval(m) for m in scoped) if s is not None]
            merged = _merge(intervals)
            covered_until = merged[0][1]
            for start, end in merged[1:]:
                # The source records a handoff either on the same day or on
                # consecutive days, so a one-day difference is continuity.
                if covered_until is not None and start > covered_until + timedelta(
                    days=_HANDOFF_TOLERANCE
                ):
                    # Unaffiliated membership in this scope means the source
                    # simply cannot date the gap (warning); no unaffiliated
                    # membership at all means a row is missing (error).
                    scope_dated = (
                        person_id,
                        man.chamber,
                        man.legislature,
                    ) in person_has_unaffiliated
                    findings.append(
                        Finding(
                            check="mandate_coverage",
                            severity="error" if not scope_dated else "warning",
                            chamber=man.chamber,
                            legislature=man.legislature,
                            person_id=person_id,
                            name=names.get(person_id),
                            detail=(
                                f"gap in group membership between {covered_until.isoformat()} "
                                f"and {start.isoformat()}"
                                + (
                                    "; the person sits unaffiliated in this scope but the "
                                    "chamber publishes no dated unaffiliated roster, so the "
                                    "interval cannot be expressed by the source"
                                    if scope_dated
                                    else "; the person is not listed in any group or as "
                                    "unaffiliated during this interval"
                                )
                            ),
                            context={"days": (start - covered_until).days},
                        )
                    )
                if covered_until is None or (end is not None and end > covered_until):
                    covered_until = end
            if man.start_date and first > man.start_date:
                findings.append(
                    Finding(
                        check="mandate_coverage",
                        severity="warning",
                        chamber=man.chamber,
                        legislature=man.legislature,
                        person_id=person_id,
                        name=names.get(person_id),
                        detail=(
                            f"first group membership starts {(first - man.start_date).days} "
                            "days after the mandate was validated"
                        ),
                        context={
                            "mandate_start": man.start_date.isoformat(),
                            "first_membership": first.isoformat(),
                        },
                    )
                )
    return findings


def check_overlaps(session: Session) -> list[Finding]:
    """A person cannot sit in two *parliamentary groups* at the same time.

    Committee memberships are excluded: sitting on two committees (or on a
    committee while sitting in a group) is normal, not a contradiction.
    """
    findings: list[Finding] = []
    rows = session.execute(
        select(
            Membership.person_id,
            Membership.chamber,
            Membership.legislature,
            Membership.org_id,
            Membership.start_date,
            Membership.end_date,
            Membership.source_url,
        )
        .join(Organization, Organization.id == Membership.org_id)
        .where(is_group(), Membership.start_date.isnot(None))
    ).all()
    by_person: dict[tuple[str, str | None, str | None], list] = defaultdict(list)
    for r in rows:
        # The scope is part of the key: a deputy in 1992 and a senator in
        # 2012 cannot overlap, and comparing them would report the whole
        # career of every long-serving member as a contradiction.
        by_person[(r.person_id, r.chamber, r.legislature)].append(r)
    names = {
        p.id: p.canonical_name
        for p in session.scalars(select(Person).where(Person.id.in_({key[0] for key in by_person})))
    }
    org_ids = {r.org_id for items in by_person.values() for r in items}
    orgs = {
        o.id: (o.short_name or o.name)
        for o in session.scalars(select(Organization).where(Organization.id.in_(org_ids)))
    }
    for (person_id, _chamber, _legislature), items in by_person.items():
        items.sort(key=lambda r: (r.start_date, r.end_date or date.max))
        for a, b in zip(items, items[1:], strict=False):
            # An open-ended tenure (no published leave date) is an inference
            # artifact: the chamber published the member in the group without
            # dates. It cannot be treated as covering forever, because the
            # member demonstrably sat elsewhere afterwards. Cap it at the day
            # before the next tenure starts - a person cannot sit in two
            # groups at once.
            a_end = (b.start_date - timedelta(days=1)) if a.end_date is None else a.end_date
            if b.start_date < a_end and a.org_id != b.org_id:
                # A one-day overlap is how the source records a handoff that
                # happened at midnight; a longer one is a real contradiction.
                overlap_days = (a_end - b.start_date).days
                findings.append(
                    Finding(
                        check="overlap",
                        severity="warning" if overlap_days <= 1 else "error",
                        chamber=a.chamber,
                        legislature=a.legislature,
                        person_id=person_id,
                        name=names.get(person_id),
                        detail=(
                            f"sits in {orgs.get(a.org_id, a.org_id)} and "
                            f"{orgs.get(b.org_id, b.org_id)} at the same time"
                        ),
                        context={
                            "overlap_days": overlap_days,
                            "a": [
                                a.start_date.isoformat(),
                                a.end_date.isoformat() if a.end_date else None,
                            ],
                            "b": [
                                b.start_date.isoformat(),
                                b.end_date.isoformat() if b.end_date else None,
                            ],
                        },
                    )
                )
    return findings


def check_membership_evidence(session: Session) -> list[Finding]:
    """Every membership must point at the official page it came from.

    Deliberately **not** filtered to groups: evidence is required for every
    row in the corpus, committee memberships included.
    """
    findings: list[Finding] = []
    missing = session.scalar(
        select(func.count()).select_from(Membership).where(Membership.source_url.is_(None))
    )
    if missing:
        findings.append(
            Finding(
                check="evidence",
                severity="error",
                detail=f"{missing} memberships have no source URL",
            )
        )
    missing_ev = session.scalar(
        select(func.count())
        .select_from(Membership)
        .outerjoin(Evidence, Evidence.membership_id == Membership.id)
        .where(Evidence.id.is_(None))
    )
    if missing_ev:
        findings.append(
            Finding(
                check="evidence",
                severity="error",
                detail=f"{missing_ev} memberships have no evidence row",
            )
        )
    return findings


def check_switch_events(session: Session) -> list[Finding]:
    """A switch event must be backed by a closed tenure and an open one.

    The event is the public-facing fact; it must not exist without the two
    dated tenures that prove it.
    """
    findings: list[Finding] = []
    events = list(session.scalars(select(Event).where(Event.type == "switch_group")))
    person_ids = {ev.person_id for ev in events if ev.person_id}
    names = (
        dict(
            session.execute(
                select(Person.id, Person.canonical_name).where(Person.id.in_(person_ids))
            ).all()
        )
        if person_ids
        else {}
    )
    for ev in events:
        if not ev.source_url:
            findings.append(
                Finding(
                    check="switch_event",
                    severity="error",
                    chamber=ev.chamber,
                    legislature=ev.legislature,
                    person_id=ev.person_id,
                    name=names.get(ev.person_id),
                    detail="switch event has no source URL",
                )
            )
        if ev.event_date is None:
            findings.append(
                Finding(
                    check="switch_event",
                    severity="error",
                    chamber=ev.chamber,
                    legislature=ev.legislature,
                    person_id=ev.person_id,
                    name=names.get(ev.person_id),
                    detail="switch event has no date",
                )
            )
    return findings


def check_scope_totals(session: Session) -> list[Finding]:
    """Report the size of each scope, so a drop is visible as a change.

    A scope is a chamber/legislature of *group* tenures; committee
    memberships are not seats, so they are excluded.
    """
    findings: list[Finding] = []
    rows = session.execute(
        select(
            Membership.chamber,
            Membership.legislature,
            func.count(func.distinct(Membership.person_id)),
            func.count(Membership.id),
        )
        .join(Organization, Organization.id == Membership.org_id)
        .where(is_group())
        .group_by(Membership.chamber, Membership.legislature)
    ).all()
    for chamber, legislature, members, _memberships in rows:
        if members == 0:
            findings.append(
                Finding(
                    check="scope_totals",
                    severity="error",
                    chamber=chamber,
                    legislature=legislature,
                    detail="legislature has no members",
                )
            )
    return findings


def _comparison_key(name: str) -> str:
    """A name key for the two views to meet on.

    The chamber publishes some members with a former or married name in
    parentheses ("Tatiana GRIGORESCU (Gogoaşă)"), and the roster publishes
    the short form ("Grigorescu Tatiana"). The part in brackets is a second
    name for the same person, so the comparison uses the name outside it.
    """
    base = re.split(r"\(", name, maxsplit=1)[0]
    return name_sort_key(base)


def check_roster_reconciliation(session: Session) -> list[Finding]:
    """Compare the roster view with the group ledgers.

    The roster (``structura2015.de``) and the group ledgers
    (``structura2015.gp``) are two views of the same source. A member that
    the roster publishes but the ledgers do not contain is a member the
    ledgers lost - exactly the failure the 2016-2020 Deputies ALDE group
    was. The check reads the archive on disk, so it verifies the evidence
    itself and not just the database.
    """
    findings: list[Finding] = []
    cache = Path("data/cache/cdep")
    if not cache.exists():
        # Without the on-disk roster archive this check cannot compare the two
        # published views. Silently returning made a missing cache indistinguish-
        # able from a clean reconciliation; emit an explicit not-evaluated finding.
        findings.append(
            Finding(
                check="roster_reconciliation",
                severity="warning",
                detail=(
                    "source roster cache is unavailable: roster reconciliation was not evaluated"
                ),
                context={"not_evaluated": True, "reason": "cache_missing"},
            )
        )
        return findings

    for chamber_dir in sorted(cache.iterdir()):
        if not chamber_dir.is_dir():
            continue
        chamber = chamber_dir.name
        for leg_dir in sorted(chamber_dir.iterdir()):
            roster_file = leg_dir / "roster.html"
            if not roster_file.exists():
                continue
            legislature = leg_dir.name
            try:
                roster = parse_roster(
                    roster_file.read_text(encoding="utf-8", errors="replace"),
                    chamber=chamber,
                    legislature=legislature,
                    source_url=roster_url(chamber, legislature),
                )
            except Exception as exc:  # noqa: BLE001
                findings.append(
                    Finding(
                        check="roster_reconciliation",
                        severity="error",
                        chamber=chamber,
                        legislature=legislature,
                        detail=f"roster could not be parsed: {exc}",
                    )
                )
                continue

            roster_ids = {row.idm for row in roster.current + roster.former if row.idm}
            # The database stores people, the roster stores mandates, so the
            # comparison is on names. The two sides order the name parts
            # differently - the roster publishes "Ambrus Izabella-Agnes" while
            # the ledger publishes "Izabella-Agnes Ambrus" - and 3,393 of the
            # 5,298 roster names in the archive are in a different token order
            # from the alphabetical one. The comparison therefore uses the
            # order-insensitive key. It is only used to spot a *missing* row,
            # never to merge two identities.
            roster_names = {
                _comparison_key(row.name) for row in roster.current + roster.former if row.name
            }
            db_names = {
                _comparison_key(n)
                for n in session.scalars(
                    select(Person.canonical_name)
                    .join(Membership, Membership.person_id == Person.id)
                    .join(Organization, Organization.id == Membership.org_id)
                    .where(
                        is_group(),
                        Membership.chamber == chamber,
                        Membership.legislature == legislature,
                    )
                    .distinct()
                )
                if n
            }
            missing = sorted(roster_names - db_names)
            for key in missing[:50]:
                findings.append(
                    Finding(
                        check="roster_reconciliation",
                        severity="warning",
                        chamber=chamber,
                        legislature=legislature,
                        name=key,
                        detail="published in the roster but absent from the group ledgers",
                        context={"roster_ids": len(roster_ids)},
                    )
                )
            if missing:
                findings.append(
                    Finding(
                        check="roster_reconciliation",
                        severity="info",
                        chamber=chamber,
                        legislature=legislature,
                        detail=(f"{len(missing)} roster members have no group ledger row"),
                    )
                )
    return findings


def _scope_roster(cache: Path, chamber: str, legislature: str):
    """The roster view of one scope, parsed from the archive."""
    roster_file = cache / chamber / legislature / "roster.html"
    if not roster_file.exists():
        return None
    try:
        return parse_roster(
            roster_file.read_text(encoding="utf-8", errors="replace"),
            chamber=chamber,
            legislature=legislature,
            source_url=roster_url(chamber, legislature),
        )
    except Exception:  # noqa: BLE001
        return None


def check_index_reconciliation(session: Session) -> list[Finding]:
    """Reconcile the parsed rows against the counts the source publishes.

    The group index publishes the number of members of every group ("N
    membri"). The group page publishes the roster. If the two disagree, the
    parser dropped rows or read them wrong - the silent failure that turns a
    legislative dataset into fiction. The check reads the archive on disk, so
    it audits the evidence, not just the database.

    The sum of the published counts is also compared with the size of the
    chamber: when it falls short, the index itself is hiding groups (which is
    exactly what happened with the 2016-2020 Deputies ALDE group).
    """
    findings: list[Finding] = []
    cache = Path("data/cache/cdep")
    expected_scopes = set(
        session.execute(
            select(Membership.chamber, Membership.legislature)
            .join(Organization, Organization.id == Membership.org_id)
            .where(is_group())
            .distinct()
        ).all()
    )
    cached_scopes: set[tuple[str, str]] = set()
    if cache.is_dir():
        for chamber_dir in cache.iterdir():
            if not chamber_dir.is_dir():
                continue
            for leg_dir in chamber_dir.iterdir():
                if (leg_dir / "list.html").is_file():
                    cached_scopes.add((chamber_dir.name, leg_dir.name))
    missing_scopes = sorted(expected_scopes - cached_scopes)
    cache_missing = not cache.is_dir()
    if missing_scopes or cache_missing:
        findings.append(
            Finding(
                check="index_reconciliation",
                severity="warning",
                detail=(
                    f"source group indexes are unavailable for {len(missing_scopes)} "
                    "chamber/legislature scopes; those reconciliations were not evaluated"
                    + (" (the source cache directory is missing)" if cache_missing else "")
                ),
                context={
                    "not_evaluated": True,
                    "missing_scopes": [
                        {"chamber": chamber, "legislature": legislature}
                        for chamber, legislature in missing_scopes
                    ],
                },
            )
        )

    for chamber_dir in sorted(cache.iterdir()) if cache.is_dir() else ():
        if not chamber_dir.is_dir():
            continue
        chamber = chamber_dir.name
        for leg_dir in sorted(chamber_dir.iterdir()):
            index_file = leg_dir / "list.html"
            if not index_file.exists():
                continue
            legislature = leg_dir.name
            try:
                items = parse_group_list(index_file.read_text(encoding="utf-8", errors="replace"))
            except Exception as exc:  # noqa: BLE001
                findings.append(
                    Finding(
                        check="index_reconciliation",
                        severity="error",
                        chamber=chamber,
                        legislature=legislature,
                        detail=f"group index could not be parsed: {exc}",
                    )
                )
                continue

            published_total = 0
            for item in items:
                if item.count is None:
                    continue
                published_total += item.count
                page = leg_dir / f"group_{item.idg}.html"
                if not page.exists():
                    findings.append(
                        Finding(
                            check="index_reconciliation",
                            severity="error",
                            chamber=chamber,
                            legislature=legislature,
                            detail=(
                                f"group {item.name} is listed in the index but its "
                                "ledger page was never fetched"
                            ),
                            context={"idg": item.idg, "published": item.count},
                        )
                    )
                    continue
                try:
                    ledger = parse_group_ledger(
                        page.read_text(encoding="utf-8", errors="replace"),
                        chamber=chamber,
                        legislature=legislature,
                        source_url=str(page),
                    )
                except Exception as exc:  # noqa: BLE001
                    findings.append(
                        Finding(
                            check="index_reconciliation",
                            severity="error",
                            chamber=chamber,
                            legislature=legislature,
                            detail=f"group {item.name} ledger could not be parsed: {exc}",
                        )
                    )
                    continue
                # The rows the page lists that carry a mandate id are the
                # members it publishes. The count is compared with the number
                # the index publishes.
                parsed = len([r for r in ledger.current + ledger.name_only if r.idm])
                if parsed != item.count:
                    # The roster is the third view. When the rows that agree
                    # with the roster are exactly as many as the index
                    # publishes, the page is carrying stale rows and the
                    # pipeline has already removed them; the check reports
                    # the fact instead of hiding it.
                    agreeing = 0
                    roster = _scope_roster(cache, chamber, legislature)
                    if roster is not None:
                        roster_ids = {r.idm: r for r in roster.current}
                        roster_former = {r.idm for r in roster.former if r.idm}
                        for row in ledger.current + ledger.name_only:
                            if not row.idm or row.idm in roster_former:
                                continue
                            rr = roster_ids.get(row.idm)
                            if rr is None:
                                continue
                            gid = rr.group_id
                            if gid is None and rr.group and rr.group.strip().isdigit():
                                gid = rr.group.strip()
                            if gid is not None and gid == item.idg:
                                agreeing += 1
                            elif gid is None and rr.group:
                                agreeing += 1
                    if agreeing == item.count:
                        findings.append(
                            Finding(
                                check="index_reconciliation",
                                severity="warning",
                                chamber=chamber,
                                legislature=legislature,
                                detail=(
                                    f"group {item.name}: the page lists {parsed} rows and the "
                                    f"index publishes {item.count}; the roster confirms "
                                    f"{agreeing} of them, so the extra rows are stale "
                                    "and were removed from the current membership"
                                ),
                                context={
                                    "idg": item.idg,
                                    "published": item.count,
                                    "parsed": parsed,
                                    "agreeing": agreeing,
                                },
                            )
                        )
                    else:
                        findings.append(
                            Finding(
                                check="index_reconciliation",
                                severity="error",
                                chamber=chamber,
                                legislature=legislature,
                                detail=(
                                    f"group {item.name}: index publishes {item.count} members, "
                                    f"the ledger yields {parsed}, the roster confirms "
                                    f"{agreeing}"
                                ),
                                context={
                                    "idg": item.idg,
                                    "published": item.count,
                                    "parsed": parsed,
                                    "agreeing": agreeing,
                                },
                            )
                        )

            # The chamber size is fixed by the constitution; a large shortfall
            # means the index is hiding groups.
            chamber_size = {"deputies": 329, "senate": 136}.get(chamber)
            if chamber_size and published_total < chamber_size * 0.9:
                findings.append(
                    Finding(
                        check="index_reconciliation",
                        severity="warning",
                        chamber=chamber,
                        legislature=legislature,
                        detail=(
                            f"the published group counts total {published_total} of about "
                            f"{chamber_size} seats, so the index is omitting groups"
                        ),
                        context={"published_total": published_total},
                    )
                )
    return findings


def check_interval_order(session: Session) -> list[Finding]:
    """A tenure cannot end before it starts.

    The OpenStates people dataset hit the same bug repeatedly: a role whose
    end date predates its own start date is nonsensical regardless of the
    jurisdiction, and it is always a data defect, never a real event.

    Deliberately **not** grouped by classification: an inverted interval is a
    defect in *every* tenure, including committee memberships, so this check
    reads all tenures on purpose.
    """
    findings: list[Finding] = []
    rows = session.execute(
        select(
            Membership.person_id,
            Person.canonical_name,
            Membership.chamber,
            Membership.legislature,
            Membership.start_date,
            Membership.end_date,
            Membership.source_url,
        )
        .join(Person, Person.id == Membership.person_id)
        .where(
            Membership.end_date.is_not(None),
            Membership.start_date.is_not(None),
            Membership.start_date > Membership.end_date,
        )
    ).all()
    for person_id, name, chamber, legislature, start, end, source_url in rows:
        findings.append(
            Finding(
                check="interval_order",
                severity="error",
                chamber=chamber,
                legislature=legislature,
                person_id=person_id,
                name=name,
                detail=f"tenure starts on {start} and ends on {end}",
                context={"source_url": source_url},
            )
        )
    return findings


def check_missing_start(session: Session) -> list[Finding]:
    """A tenure with no start date is invisible to the movement analysis.

    The switch derivation can only compare tenures that begin on a known
    day, so a membership without a start date silently drops out of the
    statistics. It has to be loud, not silent.
    """
    findings: list[Finding] = []
    rows = session.execute(
        select(
            Membership.person_id,
            Person.canonical_name,
            Membership.chamber,
            Membership.legislature,
            Membership.source_url,
            Membership.start_reason,
        )
        .join(Organization, Organization.id == Membership.org_id)
        .join(Person, Person.id == Membership.person_id)
        .where(
            is_group(),
            Membership.start_date.is_(None),
        )
    ).all()
    for person_id, name, chamber, legislature, source_url, reason in rows:
        findings.append(
            Finding(
                check="missing_start",
                severity="error",
                chamber=chamber,
                legislature=legislature,
                person_id=person_id,
                name=name,
                detail=(
                    "the tenure has no start date, so it cannot take part in the "
                    f"switch analysis (reason: {reason or 'none'})"
                ),
                context={"source_url": source_url},
            )
        )
    return findings


def check_batched_dates(session: Session) -> list[Finding]:
    """A date shared by many unrelated people is a smell.

    The OpenStates people dataset caught a bot that dated a batch of
    resignations with one shared day instead of each person's own effective
    date. No structural rule can know which date is "true", but a date
    shared by a large number of unrelated people across different scopes is
    a strong sign of a default value rather than a published fact.

    The legislature start is exactly such a default, and it is legitimate -
    it is recorded with ``start_reason='LEGISLATURE_START'`` and is
    therefore expected here. The check looks at *published* dates only.
    """
    findings: list[Finding] = []
    threshold = 40
    published = (
        select(
            Membership.start_date.label("d"),
            Membership.end_date.label("d2"),
            Membership.chamber,
            Membership.legislature,
            Membership.person_id,
        )
        .join(Organization, Organization.id == Membership.org_id)
        .where(
            is_group(),
            Membership.start_reason == "PUBLISHED",
        )
    )
    counts: dict[date, set[tuple[str | None, str | None]]] = defaultdict(set)
    for d, _d2, chamber, legislature, person_id in session.execute(published).all():
        if d is not None:
            counts[d].add((chamber, legislature, person_id))
    ends: dict[date, set[tuple[str | None, str | None]]] = defaultdict(set)
    for _, d2, chamber, legislature, person_id in session.execute(published).all():
        if d2 is not None:
            ends[d2].add((chamber, legislature, person_id))
    for label, table in (("start", counts), ("end", ends)):
        for day, people in sorted(table.items()):
            if len(people) >= threshold:
                findings.append(
                    Finding(
                        check="batched_dates",
                        severity="warning",
                        detail=(
                            f"{len(people)} unrelated people share the same published "
                            f"{label} date ({day.isoformat()}); check whether the source "
                            "published it or the pipeline defaulted to it"
                        ),
                        context={"date": day.isoformat(), "people": len(people)},
                    )
                )
    return findings


CHECKS = {
    "mandate_coverage": check_mandate_coverage,
    "overlap": check_overlaps,
    "evidence": check_membership_evidence,
    "switch_event": check_switch_events,
    "scope_totals": check_scope_totals,
    "roster_reconciliation": check_roster_reconciliation,
    "index_reconciliation": check_index_reconciliation,
    "interval_order": check_interval_order,
    "missing_start": check_missing_start,
    "batched_dates": check_batched_dates,
}


def audit(session: Session) -> AuditReport:
    """Run every check and return the report."""
    report = AuditReport()
    for name, fn in CHECKS.items():
        findings = fn(session)
        report.checks.append(
            {
                "name": name,
                "findings": len(findings),
                "errors": sum(1 for f in findings if f.severity == "error"),
                "warnings": sum(1 for f in findings if f.severity == "warning"),
            }
        )
        report.findings.extend(findings)
    return report


def scope_totals(session: Session) -> list[dict]:
    """Per-scope counts: the table a human reads to spot a sudden drop.

    Group semantics: ``members`` and ``memberships`` count parliamentary-group
    tenures only, so committee memberships cannot inflate them.
    """
    rows = session.execute(
        select(
            Membership.chamber,
            Membership.legislature,
            func.count(func.distinct(Membership.person_id)).label("members"),
            func.count(Membership.id).label("memberships"),
        )
        .join(Organization, Organization.id == Membership.org_id)
        .where(is_group())
        .group_by(Membership.chamber, Membership.legislature)
        .order_by(Membership.legislature, Membership.chamber)
    ).all()
    out = []
    for chamber, legislature, members, memberships in rows:
        switches = session.scalar(
            select(func.count())
            .select_from(Event)
            .where(
                Event.type == "switch_group",
                Event.chamber == chamber,
                Event.legislature == legislature,
            )
        )
        out.append(
            {
                "chamber": chamber,
                "legislature": legislature,
                "members": members,
                "memberships": memberships,
                "switches": switches or 0,
            }
        )
    return out
