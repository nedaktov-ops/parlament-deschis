"""Backfill explicit party memberships from group memberships with on_behalf_of_id."""

from __future__ import annotations

import uuid

from sqlalchemy import and_, select

from pipeline.db import Membership, Organization, get_session


def backfill_party_memberships():
    """Create explicit party memberships from group memberships with on_behalf_of_id."""
    session = get_session()

    try:
        # Get all group memberships that have a party (on_behalf_of_id)
        group_memberships = session.scalars(
            select(Membership).where(
                Membership.org_id.in_(
                    select(Organization.id).where(Organization.classification == "group")
                ),
                Membership.on_behalf_of_id.isnot(None),
            )
        ).all()

        print(f"Found {len(group_memberships)} group memberships with party affiliation")

        created = 0
        for gm in group_memberships:
            # Check if party membership already exists
            existing = session.scalars(
                select(Membership)
                .join(Organization, Organization.id == Membership.org_id)
                .where(
                    and_(
                        Membership.person_id == gm.person_id,
                        Membership.org_id == gm.on_behalf_of_id,
                        Organization.classification == "party",
                    )
                )
            ).first()

            if existing:
                continue

            # Create party membership
            party_membership = Membership(
                id=str(uuid.uuid4()),
                person_id=gm.person_id,
                org_id=gm.on_behalf_of_id,
                on_behalf_of_id=None,  # Party memberships don't have a party behind them
                chamber=gm.chamber,
                legislature=gm.legislature,
                role=gm.role,
                importance=gm.importance,
                start_date=gm.start_date,
                end_date=gm.end_date,
                start_precision=gm.start_precision,
                end_precision=gm.end_precision,
                start_reason=gm.start_reason,
                end_reason=gm.end_reason,
                confidence=gm.confidence,
                source_url=gm.source_url,
                group_acronym_at_event=gm.group_acronym_at_event,
            )
            session.add(party_membership)
            created += 1

        session.commit()
        print(f"Created {created} party memberships")

        # Verify
        from sqlalchemy import func

        party_count = session.scalar(
            select(func.count()).select_from(
                select(Membership)
                .join(Organization, Organization.id == Membership.org_id)
                .where(Organization.classification == "party")
                .subquery()
            )
        )
        print(f"Total party memberships after backfill: {party_count}")

    finally:
        session.close()


if __name__ == "__main__":
    backfill_party_memberships()
