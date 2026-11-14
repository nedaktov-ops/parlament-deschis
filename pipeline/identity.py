"""Identity resolution: per-term source ids → stable person, with conservative
matching and auditable, reversible merges.

Resolution order (parlparse): official identifier+scheme → dated name match →
unique-only fallback (never guess). cdep `idm` and senat GUID are per-term, so
they are stored as identifiers scoped to a legislature, not as the person key.
"""

from __future__ import annotations

from datetime import date

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import (
    Event,
    MatchReview,
    Membership,
    MergeAudit,
    Person,
    PersonIdentifier,
    PersonName,
)
from .normalize import name_sort_key, normalize_name

AUTO_MERGE_THRESHOLD = 95.0
REVIEW_THRESHOLD = 80.0


def _find_by_identifier(session, scheme, identifier, legislature) -> Person | None:
    stmt = select(PersonIdentifier).where(
        PersonIdentifier.scheme == scheme,
        PersonIdentifier.identifier == identifier,
    )
    if legislature is None:
        stmt = stmt.where(PersonIdentifier.legislature.is_(None))
    else:
        stmt = stmt.where(PersonIdentifier.legislature == legislature)
    ident = session.scalars(stmt).first()
    return ident.person if ident else None


def _has_conflicting_identifier(session, person, scheme, identifier, legislature) -> bool:
    """True if person already holds a different id of the same scheme+term."""
    for ident in person.identifiers:
        if (
            ident.scheme == scheme
            and ident.identifier != identifier
            and (ident.legislature == legislature)
        ):
            return True
    return False


def _name_candidates(session, name: str) -> list[Person]:
    """Indexed lookup by normalized name or order-insensitive sort key, across
    canonical names and dated aliases. Avoids loading every person."""
    norm = normalize_name(name)
    key = name_sort_key(name)
    ids: set[str] = set()
    for p in session.scalars(
        select(Person).where((Person.normalized_name == norm) | (Person.sort_key == key))
    ):
        ids.add(p.id)
    for pn in session.scalars(
        select(PersonName).where(
            (PersonName.normalized_name == norm) | (PersonName.sort_key == key)
        )
    ):
        ids.add(pn.person_id)
    if not ids:
        return []
    return list(session.scalars(select(Person).where(Person.id.in_(ids))))


class PersonResolver:
    def __init__(self, session: Session):
        self.session = session

    def resolve(
        self,
        *,
        scheme: str,
        identifier: str,
        name: str,
        legislature: str | None = None,
        birth_date: date | None = None,
        chamber: str | None = None,
        on_date: date | None = None,
    ) -> tuple[Person, bool]:
        """Return (person, created). Never guesses an ambiguous match."""
        existing = _find_by_identifier(self.session, scheme, identifier, legislature)
        if existing is not None:
            return existing, False

        # Unique-only name fallback, excluding candidates that carry a
        # conflicting official identifier in the same source+legislature
        # (two different idm/GUID in one term are two different people, even
        # if their names are identical).
        candidates = _name_candidates(self.session, name)
        if birth_date:
            candidates = [
                p for p in candidates if p.birth_date is None or p.birth_date == birth_date
            ]
        candidates = [
            p
            for p in candidates
            if not _has_conflicting_identifier(self.session, p, scheme, identifier, legislature)
        ]
        if len(candidates) == 1:
            person = candidates[0]
            self._add_identifier(person, scheme, identifier, legislature)
            return person, False

        # Create a new person.
        person = Person(
            canonical_name=name.strip(),
            normalized_name=normalize_name(name),
            sort_key=name_sort_key(name),
            birth_date=birth_date,
            match_status="unmatched",
        )
        self.session.add(person)
        self.session.flush()
        self.session.add(
            PersonName(
                person_id=person.id,
                type="name",
                name=name.strip(),
                normalized_name=normalize_name(name),
                sort_key=name_sort_key(name),
            )
        )
        self._add_identifier(person, scheme, identifier, legislature)
        return person, True

    def _add_identifier(self, person, scheme, identifier, legislature):
        self.session.add(
            PersonIdentifier(
                person_id=person.id,
                scheme=scheme,
                identifier=identifier,
                legislature=legislature,
            )
        )

    def flag_review(self, person_a: Person, person_b: Person, score: float, reason: str):
        self.session.add(
            MatchReview(person_a=person_a.id, person_b=person_b.id, score=score, reason=reason)
        )


def score_match(a: Person, b: Person) -> float:
    """Name similarity plus birth-date agreement. Used to propose merges."""
    base = fuzz.token_sort_ratio(a.canonical_name, b.canonical_name)
    if a.birth_date and b.birth_date:
        if a.birth_date == b.birth_date:
            base = min(100.0, base + 5)
        else:
            base = max(0.0, base - 40)
    if a.wikidata_qid and b.wikidata_qid:
        if a.wikidata_qid == b.wikidata_qid:
            return 100.0
        return 0.0
    return float(base)


def merge_persons(session: Session, winner_id: str, loser_id: str) -> MergeAudit:
    """Auditable merge: winner absorbs loser; old name→alias, old id kept.

    Records reversible operations. Does not delete the loser row (kept for
    audit); memberships/identifiers/names/events are repointed to the winner.
    """
    winner = session.get(Person, winner_id)
    loser = session.get(Person, loser_id)
    if winner is None or loser is None:
        raise ValueError("merge requires two existing persons")
    if winner_id == loser_id:
        raise ValueError("cannot merge a person into itself")

    ops: list[dict] = []
    # Repoint identifiers.
    for ident in list(
        session.scalars(select(PersonIdentifier).where(PersonIdentifier.person_id == loser_id))
    ):
        ops.append(
            {
                "op": "repoint",
                "table": "person_identifier",
                "id": ident.id,
                "from": loser_id,
                "to": winner_id,
            }
        )
        ident.person_id = winner_id
    # Repoint names; the loser's canonical name becomes an alias of the winner.
    loser_name_converted = False
    for pn in list(session.scalars(select(PersonName).where(PersonName.person_id == loser_id))):
        ops.append(
            {
                "op": "repoint",
                "table": "person_name",
                "id": pn.id,
                "from": loser_id,
                "to": winner_id,
            }
        )
        pn.person_id = winner_id
        if pn.name == loser.canonical_name and pn.type == "name":
            pn.type = "alias"
            loser_name_converted = True
    if not loser_name_converted:
        already = session.scalars(
            select(PersonName).where(
                PersonName.person_id == winner_id, PersonName.name == loser.canonical_name
            )
        ).first()
        if already is None:
            alias = PersonName(
                person_id=winner_id,
                type="alias",
                name=loser.canonical_name,
                normalized_name=loser.normalized_name,
                sort_key=name_sort_key(loser.canonical_name),
            )
            session.add(alias)
            ops.append({"op": "append", "table": "person_name", "name": loser.canonical_name})
    # Repoint memberships and events.
    for m in session.scalars(select(Membership).where(Membership.person_id == loser_id)):
        ops.append(
            {"op": "repoint", "table": "membership", "id": m.id, "from": loser_id, "to": winner_id}
        )
        m.person_id = winner_id
    for e in session.scalars(select(Event).where(Event.person_id == loser_id)):
        ops.append(
            {"op": "repoint", "table": "event", "id": e.id, "from": loser_id, "to": winner_id}
        )
        e.person_id = winner_id
    # Absorb birth date / qid if winner lacks them.
    if winner.birth_date is None and loser.birth_date:
        winner.birth_date = loser.birth_date
        ops.append({"op": "replace", "field": "birth_date", "value": str(loser.birth_date)})
    if winner.wikidata_qid is None and loser.wikidata_qid:
        winner.wikidata_qid = loser.wikidata_qid
        ops.append({"op": "replace", "field": "wikidata_qid", "value": loser.wikidata_qid})

    winner.match_status = "merged"
    audit = MergeAudit(winner_id=winner_id, loser_id=loser_id, operations=ops)
    session.add(audit)
    session.flush()
    return audit


def revert_merge(session: Session, audit_id: str) -> None:
    """Reverse a merge using its recorded operations."""
    audit = session.get(MergeAudit, audit_id)
    if audit is None or audit.reverted:
        return
    table_map = {
        "person_identifier": PersonIdentifier,
        "person_name": PersonName,
        "membership": Membership,
        "event": Event,
    }
    for op in reversed(audit.operations):
        if op["op"] == "repoint":
            model = table_map[op["table"]]
            row = session.get(model, op["id"])
            if row is not None:
                row.person_id = op["from"]
        elif op["op"] == "append" and op["table"] == "person_name":
            for pn in session.scalars(
                select(PersonName).where(
                    PersonName.person_id == audit.winner_id,
                    PersonName.name == op["name"],
                    PersonName.type == "alias",
                )
            ):
                session.delete(pn)
    audit.reverted = True
    winner = session.get(Person, audit.winner_id)
    if winner is not None:
        winner.match_status = "unmatched"
    session.flush()
