"""Cross-check the current membership against the source's own other views.

The chamber publishes the same fact in three places:

1. the **group ledger** (``structura2015.gp``) - the per-group roster, with
   the dated membership intervals;
2. the **group index** (``structura2015.gp?idl=1``) - the per-group member
   count ("N Membri");
3. the **alphabetical roster** (``structura2015.de?par=A``) - the per-MP
   view, with each member's constituency and their group.

A row in a group's current table can be **stale**: the chamber keeps the
row of a member who has already left the party. The 2020 AUR page lists
two members whose party cell is empty, and the roster says both are
unaffiliated; the 2020 Senate PNL page lists a deputy whose party cell
says PSD. The index count agrees with the roster in every one of those
cases, and the page is the outlier.

The rule used here is deliberately **conservative**: a row is only taken
out of the current membership when the rows that *do* agree with the
other two views are exactly as many as the count the index publishes. If
that is not the case, nothing is removed, the disagreement is left in the
data, and the audit reports it. The tool never guesses which of two
published views is right.

Two further signals are handled the same way:

* a member the roster lists as **former** (they left Parliament) cannot
  be a current member of a group;
* a group page that publishes **no dates at all** for the unaffiliated
  bucket is a historical list - the members it names sat unaffiliated at
  some point in that legislature.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .normalize import canonical_group_short

log = logging.getLogger("parlament.crosscheck")

# The label used for a member the roster lists without a group.
NO_GROUP = ""


@dataclass
class Exclusion:
    """One row removed from a group's current membership, with the reason."""

    chamber: str
    legislature: str
    idg: str
    group: str
    name: str
    idm: str | None
    roster_label: str
    reason: str


@dataclass
class CrossCheckReport:
    exclusions: list[Exclusion] = field(default_factory=list)
    unresolved: list[dict] = field(default_factory=list)
    reconciled_groups: int = 0
    checked_groups: int = 0

    def as_dict(self) -> dict:
        return {
            "exclusions": [e.__dict__ for e in self.exclusions],
            "unresolved": self.unresolved,
            "reconciled_groups": self.reconciled_groups,
            "checked_groups": self.checked_groups,
        }


def canonical_roster_label(label: str | None) -> str:
    """Canonical form of the group label the roster publishes."""
    if label is None:
        return NO_GROUP
    text = label.strip()
    if not text:
        return NO_GROUP
    short = canonical_group_short(text)
    if short:
        return short.upper()
    return text.upper()


def _roster_maps(roster) -> tuple[dict[str, tuple[str | None, str]], set[str]]:
    """(idm -> (group id, group label)) for the serving members, and the former ones."""
    current: dict[str, tuple[str | None, str]] = {}
    for row in roster.current:
        if not row.idm:
            continue
        gid = row.group_id
        if gid is None and row.group and row.group.strip().isdigit():
            # In one legislature template the roster shows the bare group
            # number instead of a link; it is the same id.
            gid = row.group.strip()
        current[row.idm] = (gid, canonical_roster_label(row.group))
    former = {row.idm for row in roster.former if row.idm}
    return current, former


def reconcile_current_membership(
    corpus,
) -> CrossCheckReport:
    """Remove the stale rows from the current membership, where it is provable.

    ``corpus`` must carry the rosters and the index counts (see
    :func:`pipeline.collect.build_corpus`). Every removed row is reported,
    with the view that contradicted it.
    """
    report = CrossCheckReport()

    rosters = {}
    for roster in getattr(corpus, "rosters", []) or []:
        rosters[(roster.chamber, roster.legislature)] = roster
    index_counts = getattr(corpus, "index_counts", {}) or {}

    for rec in corpus.ledgers:
        key = (rec.chamber, rec.legislature)
        roster = rosters.get(key)
        if roster is None:
            continue
        published = index_counts.get(key, {}).get(rec.idg)
        if published is None:
            # A group the index does not list (a dissolved group found by
            # probing) has no published count to reconcile against.
            continue
        report.checked_groups += 1

        roster_current, roster_former = _roster_maps(roster)
        page_label = canonical_roster_label(rec.ledger.meta.short_name or rec.ledger.meta.name)
        candidates = list(rec.ledger.current) + list(rec.ledger.name_only)
        if not candidates:
            continue

        agree = 0
        stale: list = []
        for row in candidates:
            if not row.idm:
                continue
            if row.idm in roster_former:
                stale.append((row, "FORMER", "the roster lists this member as former"))
                continue
            info = roster_current.get(row.idm)
            if info is None:
                # The roster does not mention this member: nothing is known
                # about them, so the row is left alone.
                continue
            gid, label = info
            if gid is not None:
                if gid == rec.idg:
                    agree += 1
                else:
                    stale.append(
                        (
                            row,
                            label or gid,
                            f"the roster puts this member in group {gid}, not in {rec.idg}",
                        )
                    )
            elif label == page_label:
                agree += 1
            else:
                stale.append(
                    (
                        row,
                        label,
                        f"the roster puts this member in {label or 'no group'}, "
                        f"not in {page_label}",
                    )
                )

        if agree != published:
            # The count the source publishes cannot be reproduced from the
            # roster, so nothing is removed: the disagreement is reported.
            report.unresolved.append(
                {
                    "chamber": rec.chamber,
                    "legislature": rec.legislature,
                    "idg": rec.idg,
                    "group": rec.ledger.meta.short_name or rec.ledger.meta.name,
                    "published": published,
                    "listed": len(candidates),
                    "agreeing": agree,
                    "reason": "the published count does not match the roster",
                }
            )
            continue

        if not stale:
            report.reconciled_groups += 1
            continue

        # The exclusion is applied only because it makes the page agree with
        # the count the source itself publishes.
        #
        # Only the **dated** current table is corrected. A page that lists
        # members without dates is a historical list (the unaffiliated
        # bucket is published that way in the 1990-2012 legislatures), and
        # the people on it are members of that group even when they have
        # left Parliament in the meantime - their tenure is dated from the
        # other tenures of the same mandate.
        for row, label, reason in stale:
            if row not in rec.ledger.current:
                continue
            rec.ledger.current.remove(row)
            report.exclusions.append(
                Exclusion(
                    chamber=rec.chamber,
                    legislature=rec.legislature,
                    idg=rec.idg,
                    group=rec.ledger.meta.short_name or rec.ledger.meta.name,
                    name=row.name,
                    idm=row.idm,
                    roster_label=label,
                    reason=reason,
                )
            )
        report.reconciled_groups += 1

    if report.exclusions:
        log.info(
            "cross-check removed %d stale rows from the current membership",
            len(report.exclusions),
        )
    return report
