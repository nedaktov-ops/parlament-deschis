"""SQLAlchemy models + SQLite (WAL) store.

Popolo vocabulary, bitemporal (valid-time vs transaction-time), event-sourced.
One codebase serves both chambers via a chamber enum. Every membership carries
provenance, confidence and date precision; closed tenures are immutable.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

log = logging.getLogger("parlament.db")

# user_version is the migration gate for one-off, destructive data fixes (the
# legacy cross-chamber group merge below). A database prepared for shipping by
# scripts/prepare_db.py carries this version, so a read-only runtime copy never
# replays the merge. Bump it only when adding another one-off data migration.
SCHEMA_VERSION = 1

# --- Enumerations (stored as strings for SQLite portability) ---------------
CHAMBERS = ("deputies", "senate")
ORG_CLASS = (
    "chamber",
    "group",
    "party",
    "committee",
    "bureau",
    "delegation",
    "friendship",
    "other",
)
CONFIDENCE = ("official_ledger", "official_profile", "derived", "community")
CONFIDENCE_RANK = {c: i for i, c in enumerate(CONFIDENCE)}  # lower = stronger
REASONS = (
    "CHANGED_PARTY",
    "WHIP_REMOVED",
    "WHIP_RESTORED",
    "DIED",
    "RESIGNED",
    "BY_ELECTION",
    "GENERAL_ELECTION",
    "UNKNOWN",
)
EVIDENCE_TYPES = ("official_ledger", "profile", "jo", "intervention", "scrutin", "other")
EVENT_TYPES = (
    "join",
    "join_party",
    "leave",
    "switch_group",
    "switch_party",
    "group_founded",
    "group_renamed",
    "committee_join",
    "committee_leave",
    "role_change",
    "mandate_start",
    "mandate_end",
)
WAVE_TRIGGERS = ("election", "government_formation", "party_congress", "coalition_breakup", "other")
RUN_STATUS = ("SUCCESS", "FAILURE", "DATA_UNAVAILABLE", "DATA_UNCHANGED")
MATCH_STATUS = ("auto", "review", "unmatched", "merged")


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Person(Base):
    __tablename__ = "person"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    canonical_name: Mapped[str] = mapped_column(String(255))
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)
    sort_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    wikidata_qid: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    match_status: Mapped[str] = mapped_column(String(16), default="unmatched")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    identifiers: Mapped[list[PersonIdentifier]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )
    names: Mapped[list[PersonName]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )
    memberships: Mapped[list[Membership]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )


class PersonIdentifier(Base):
    __tablename__ = "person_identifier"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    person_id: Mapped[str] = mapped_column(ForeignKey("person.id"), index=True)
    scheme: Mapped[str] = mapped_column(String(32))  # cdep_idm / senat_guid / ep_uuid / wikidata
    identifier: Mapped[str] = mapped_column(String(128))
    legislature: Mapped[str | None] = mapped_column(String(16), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    person: Mapped[Person] = relationship(back_populates="identifiers")
    __table_args__ = (
        UniqueConstraint("scheme", "identifier", "legislature", name="uq_identifier"),
    )


class PersonName(Base):
    __tablename__ = "person_name"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    person_id: Mapped[str] = mapped_column(ForeignKey("person.id"), index=True)
    type: Mapped[str] = mapped_column(String(16), default="name")  # name / alias
    name: Mapped[str] = mapped_column(String(255))
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)
    sort_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    person: Mapped[Person] = relationship(back_populates="names")


class Organization(Base):
    __tablename__ = "organization"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    classification: Mapped[str] = mapped_column(String(16), index=True)
    name: Mapped[str] = mapped_column(String(512))
    normalized_name: Mapped[str] = mapped_column(String(512), index=True)
    short_name: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    alt_labels: Mapped[list | None] = mapped_column(JSON, nullable=True)
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("organization.id"), nullable=True)
    wikidata_qid: Mapped[str | None] = mapped_column(String(32), nullable=True)
    founding_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    dissolution_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    localised_labels: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    chamber: Mapped[str | None] = mapped_column(String(16), nullable=True)
    legislature: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    # Party genealogy
    previous_party_id: Mapped[str | None] = mapped_column(
        ForeignKey("organization.id"), nullable=True
    )
    successor_party_id: Mapped[str | None] = mapped_column(
        ForeignKey("organization.id"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("classification", "normalized_name", "founding_date", name="uq_org"),
    )


class Post(Base):
    __tablename__ = "post"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    org_id: Mapped[str] = mapped_column(ForeignKey("organization.id"), index=True)
    label: Mapped[str] = mapped_column(String(255))
    role_type: Mapped[str] = mapped_column(String(16), default="seat")  # seat / leadership
    importance: Mapped[int] = mapped_column(Integer, default=0)
    maximum_memberships: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Mandate(Base):
    """One parliamentary mandate: a person in one chamber in one legislature.

    This is the backbone of the verification layer. A mandate is published by
    the chamber (the profile page carries the validation date), while the
    group tenures that make it up come from the group ledgers. Comparing the
    two proves whether the ledgers are complete: every day of a mandate must
    be covered by exactly one group tenure.
    """

    __tablename__ = "mandate"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    person_id: Mapped[str] = mapped_column(ForeignKey("person.id"), index=True)
    chamber: Mapped[str] = mapped_column(String(16), index=True)
    legislature: Mapped[str | None] = mapped_column(String(16), index=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_precision: Mapped[str | None] = mapped_column(String(10), nullable=True)
    end_precision: Mapped[str | None] = mapped_column(String(10), nullable=True)
    constituency: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    snapshot_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[str] = mapped_column(String(32), default="official_profile")

    person: Mapped[Person] = relationship()

    __table_args__ = (
        UniqueConstraint("person_id", "chamber", "legislature", name="uq_mandate"),
        Index("ix_mandate_scope", "chamber", "legislature"),
    )


class Membership(Base):
    __tablename__ = "membership"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    person_id: Mapped[str] = mapped_column(ForeignKey("person.id"), index=True)
    org_id: Mapped[str] = mapped_column(ForeignKey("organization.id"), index=True)
    post_id: Mapped[str | None] = mapped_column(ForeignKey("post.id"), nullable=True)
    on_behalf_of_id: Mapped[str | None] = mapped_column(
        ForeignKey("organization.id"), nullable=True
    )  # party behind a group membership (Popolo)
    chamber: Mapped[str] = mapped_column(String(16), index=True)
    legislature: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=0)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_precision: Mapped[str | None] = mapped_column(String(10), nullable=True)
    end_precision: Mapped[str | None] = mapped_column(String(10), nullable=True)
    start_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    end_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[str] = mapped_column(String(32), default="derived")
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    group_acronym_at_event: Mapped[str | None] = mapped_column(String(64), nullable=True)
    member_party_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # The name exactly as the source published it. Kept beside the person
    # reference so the ledger stays readable even when the identity
    # resolution is uncertain (OpenStates keeps the same denormalised name
    # on its memberships).
    member_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    person: Mapped[Person] = relationship()
    org: Mapped[Organization] = relationship(foreign_keys=[org_id])
    party: Mapped[Organization | None] = relationship(foreign_keys=[on_behalf_of_id])

    # ``uq_stint`` is declared as an expression index in ``_PARTIAL_INDEXES``
    # below, not as a UNIQUE constraint here: a plain constraint containing
    # post_id is inert because post_id is NULL on every shipped row.
    __table_args__ = (
        Index("ix_membership_person_end", "person_id", "end_date"),
        Index("ix_membership_org_end", "org_id", "end_date"),
    )


class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    membership_id: Mapped[str] = mapped_column(ForeignKey("membership.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    snapshot_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AssetDeclaration(Base):
    __tablename__ = "asset_declaration"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    person_id: Mapped[str] = mapped_column(ForeignKey("person.id"), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    asset_type: Mapped[str] = mapped_column(String(64))
    value_ron: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Fragment(Base):
    __tablename__ = "fragment"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    model: Mapped[str] = mapped_column(String(64), index=True)
    source_name: Mapped[str] = mapped_column(String(64), index=True)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_now)
    group_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    checksum: Mapped[str] = mapped_column(String(64), index=True)
    data: Mapped[dict] = mapped_column(JSON)
    snapshot_path: Mapped[str | None] = mapped_column(String(512), nullable=True)


class PipelineRun(Base):
    __tablename__ = "pipeline_run"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32))
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rows: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class Event(Base):
    __tablename__ = "event"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    type: Mapped[str] = mapped_column(String(32), index=True)
    person_id: Mapped[str | None] = mapped_column(
        ForeignKey("person.id"), nullable=True, index=True
    )
    chamber: Mapped[str | None] = mapped_column(String(16), nullable=True)
    legislature: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    from_org_id: Mapped[str | None] = mapped_column(ForeignKey("organization.id"), nullable=True)
    to_org_id: Mapped[str | None] = mapped_column(ForeignKey("organization.id"), nullable=True)
    post_id: Mapped[str | None] = mapped_column(ForeignKey("post.id"), nullable=True)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    precision: Mapped[str | None] = mapped_column(String(10), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[str] = mapped_column(String(32), default="derived")
    group_acronym_at_event: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Provenance: every event must be traceable to the publication it came from.
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    snapshot_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    summary_ro: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    dedup_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)


class SwitchWave(Base):
    """Cluster of party switches detected within a time window, optionally labeled with a trigger event."""

    __tablename__ = "switch_wave"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    label: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # e.g., "Post-2020 election wave"
    start_date: Mapped[date] = mapped_column(Date, index=True)
    end_date: Mapped[date] = mapped_column(Date, index=True)
    switch_count: Mapped[int] = mapped_column(Integer, default=0)
    trigger_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # WAVE_TRIGGERS
    trigger_event: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # human-readable description
    legislature: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    chamber: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    __table_args__ = (Index("ix_switch_wave_leg_chamber", "legislature", "chamber"),)


class KeyEvent(Base):
    __tablename__ = "key_event"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    type: Mapped[str] = mapped_column(String(32))  # legislature / election
    chamber: Mapped[str | None] = mapped_column(String(16), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Vacancy(Base):
    __tablename__ = "vacancy"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    chamber: Mapped[str] = mapped_column(String(16))
    post_id: Mapped[str | None] = mapped_column(ForeignKey("post.id"), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reason: Mapped[str | None] = mapped_column(String(32), nullable=True)


class MatchReview(Base):
    __tablename__ = "match_review"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    person_a: Mapped[str] = mapped_column(ForeignKey("person.id"))
    person_b: Mapped[str] = mapped_column(ForeignKey("person.id"))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/approved/rejected
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Coverage(Base):
    __tablename__ = "coverage"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    chamber: Mapped[str] = mapped_column(String(16))
    legislature: Mapped[str | None] = mapped_column(String(16), nullable=True)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    completeness: Mapped[str] = mapped_column(String(16), default="partial")  # full/partial/none
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class MergeAudit(Base):
    """Auditable, reversible person merges (openstates compute_merge pattern)."""

    __tablename__ = "merge_audit"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    winner_id: Mapped[str] = mapped_column(ForeignKey("person.id"))
    loser_id: Mapped[str] = mapped_column(String(36))
    operations: Mapped[list] = mapped_column(JSON)  # list of {op, table, ...}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    reverted: Mapped[bool] = mapped_column(Boolean, default=False)


# --- Engine / session ------------------------------------------------------
# Resolve the default DB against the repository root (not the process CWD) so
# the CLI, the API and GraphQL all read the same file regardless of where they
# are launched. Explicit paths passed by callers stay CWD-relative.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_env_db = os.environ.get("PARLAMENT_DB")
if _env_db:
    _p = Path(_env_db).expanduser()
    DEFAULT_DB_PATH = _p if _p.is_absolute() else (_PROJECT_ROOT / _p)
else:
    DEFAULT_DB_PATH = _PROJECT_ROOT / "data" / "parlament.db"


def make_engine(db_path: str | Path | None = None, echo: bool = False):
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}", echo=echo, future=True)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA busy_timeout=5000")
        cur.close()

    return engine


def init_db(engine) -> None:
    Base.metadata.create_all(engine)
    ensure_schema(engine)


# Columns added after a database file was first created. SQLite has no
# "ALTER TABLE ... IF NOT EXISTS COLUMN", so they are applied conditionally.
_ADDED_COLUMNS: dict[str, dict[str, str]] = {
    "event": {
        "source_url": "VARCHAR(1024)",
        "legislature": "VARCHAR(16)",
        "snapshot_hash": "VARCHAR(64)",
    },
    "membership": {
        # The "Partid" cell published in some group ledgers. It is the member's
        # own party, not the party's group, it is absent from several group
        # tables and it is not dated - so it is stored verbatim as evidence
        # and never used as the affiliation behind a group.
        "member_party_label": "VARCHAR(128)",
        # The name exactly as the source published it.
        "member_name": "VARCHAR(255)",
    },
    "organization": {
        "legislature": "VARCHAR(16)",
    },
}

# SQLite treats NULL as distinct from every other value, so a UNIQUE
# constraint that contains a nullable column does not constrain the NULL
# case. These partial indexes close the three holes that matter:
#   * duplicate OPEN tenures (end_date IS NULL)
#   * duplicate GLOBAL person identifiers (legislature IS NULL)
#   * duplicate organisations whose founding date is unknown
_PARTIAL_INDEXES: tuple[str, ...] = (
    # A parliamentary group is one institution across time: the same title
    # ("Grupul parlamentar al Partidului Social Democrat") is the same
    # organisation in every legislature and in both chambers. A member's
    # tenure in it is therefore scoped by chamber and legislature, and the
    # uniqueness has to be scoped the same way - otherwise a deputy who was
    # in PSD in 1992 and again in 1996 would collide, because both tenures
    # are open.
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_membership_open_stint_scope "
    "ON membership(org_id, person_id, COALESCE(post_id, ''), "
    "COALESCE(chamber, ''), COALESCE(legislature, '')) WHERE end_date IS NULL",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_identifier_global "
    "ON person_identifier(scheme, identifier) WHERE legislature IS NULL",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_org_name "
    "ON organization(classification, normalized_name) WHERE founding_date IS NULL",
    # The old ``uq_stint`` UNIQUE (org_id, person_id, post_id, end_date) never
    # fired: post_id is NULL on all 7358 shipped rows and SQLite treats NULL
    # as distinct. Re-express that intent as an expression index so NULL
    # post_id (and the other optional scope columns) participate in
    # uniqueness. The key mirrors the 6-column identity used to build the
    # corpus, so exact-duplicate stints are now rejected on write.
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_stint "
    "ON membership(org_id, person_id, COALESCE(post_id, ''), COALESCE(chamber, ''), "
    "COALESCE(legislature, ''), COALESCE(end_date, ''), COALESCE(start_date, ''))",
    # uq_stint includes post_id, which was NULL on every shipped row, so the
    # old constraint treated each key as distinct and duplicate CLOSED stints
    # slipped through. This partial index closes that hole for future rows.
    # It cannot be created on a database that still contains the legacy
    # duplicates: ensure_schema now FAILS FAST instead of swallowing it.
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_membership_closed_stint "
    "ON membership(org_id, person_id, COALESCE(post_id, ''), COALESCE(chamber, ''), "
    "COALESCE(legislature, ''), end_date, COALESCE(start_date, '')) WHERE end_date IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_membership_leg_chamber ON membership(legislature, chamber)",
    # Foreign keys that are actually used as query predicates (verified with
    # EXPLAIN QUERY PLAN): party-membership lookups and event from/to joins.
    # Other FKs (organization.parent_id/previous_party_id/successor_party_id,
    # membership.post_id, event.post_id, vacancy.post_id) are only read by PK or
    # selected, never filtered on, so indexing them would add write cost for no
    # gain. event.post_id / membership.post_id are also 100% NULL in the corpus.
    "CREATE INDEX IF NOT EXISTS ix_membership_on_behalf_of ON membership(on_behalf_of_id)",
    "CREATE INDEX IF NOT EXISTS ix_event_from_org_id ON event(from_org_id)",
    "CREATE INDEX IF NOT EXISTS ix_event_to_org_id ON event(to_org_id)",
)


def _merge_legacy_cross_chamber_groups(conn) -> None:
    duplicates = conn.exec_driver_sql(
        "SELECT classification, normalized_name FROM organization "
        "WHERE classification = 'group' AND founding_date IS NULL "
        "GROUP BY classification, normalized_name HAVING COUNT(*) > 1"
    ).all()
    merged = 0
    comparable_fields = (
        "name",
        "short_name",
        "alt_labels",
        "color",
        "parent_id",
        "wikidata_qid",
        "founding_date",
        "dissolution_date",
        "localised_labels",
        "previous_party_id",
        "successor_party_id",
    )

    for classification, normalized_name in duplicates:
        rows = (
            conn.exec_driver_sql(
                "SELECT * FROM organization WHERE classification = ? "
                "AND normalized_name = ? AND founding_date IS NULL ORDER BY id",
                (classification, normalized_name),
            )
            .mappings()
            .all()
        )
        if (
            len(rows) != 2
            or {row["chamber"] for row in rows} != {"deputies", "senate"}
            or any(
                tuple(row[field] for field in comparable_fields)
                != tuple(rows[0][field] for field in comparable_fields)
                for row in rows[1:]
            )
        ):
            continue

        org_ids = [row["id"] for row in rows]
        placeholders = ", ".join("?" for _ in org_ids)
        open_conflict = conn.exec_driver_sql(
            "SELECT 1 FROM membership WHERE org_id IN (" + placeholders + ") "
            "AND end_date IS NULL GROUP BY person_id, COALESCE(post_id, ''), "
            "chamber, COALESCE(legislature, '') HAVING COUNT(*) > 1 LIMIT 1",
            tuple(org_ids),
        ).first()
        closed_conflict = conn.exec_driver_sql(
            "SELECT 1 FROM membership WHERE org_id IN (" + placeholders + ") "
            "AND end_date IS NOT NULL AND post_id IS NOT NULL "
            "GROUP BY person_id, post_id, end_date HAVING COUNT(*) > 1 LIMIT 1",
            tuple(org_ids),
        ).first()
        if open_conflict or closed_conflict:
            continue

        canonical_id = next(row["id"] for row in rows if row["chamber"] == "deputies")
        for duplicate_id in org_ids:
            if duplicate_id == canonical_id:
                continue
            for table, column in (
                ("organization", "parent_id"),
                ("organization", "previous_party_id"),
                ("organization", "successor_party_id"),
                ("post", "org_id"),
                ("membership", "org_id"),
                ("membership", "on_behalf_of_id"),
                ("event", "from_org_id"),
                ("event", "to_org_id"),
            ):
                conn.exec_driver_sql(
                    f"UPDATE {table} SET {column} = ? WHERE {column} = ?",
                    (canonical_id, duplicate_id),
                )
            conn.exec_driver_sql("DELETE FROM organization WHERE id = ?", (duplicate_id,))
        conn.exec_driver_sql("UPDATE organization SET chamber = NULL WHERE id = ?", (canonical_id,))
        merged += 1

    if merged:
        log.info("merged %d legacy cross-chamber parliamentary group records", merged)


def ensure_schema(engine) -> None:
    """Bring an existing SQLite file up to the current schema.

    Safe to call repeatedly: columns are added only when missing and indexes
    are created with IF NOT EXISTS. An index that cannot be created (because
    a legacy database still contains duplicates) is a hard error: it is never
    swallowed into a startup warning, because that silently shipped databases
    without ``ux_membership_closed_stint``. The one-off, destructive data
    merge runs at most once, gated by ``user_version``.
    """
    with engine.begin() as conn:
        version = conn.exec_driver_sql("PRAGMA user_version").scalar()
        needs_migration = (version or 0) < SCHEMA_VERSION

        # The first version of the open-stint index was not scoped by
        # chamber and legislature, so it rejected a member who held an open
        # tenure in the same group in two different legislatures. The scoped
        # index replaces it; the old one has to go first, because SQLite
        # would otherwise keep enforcing it.
        legacy = conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='ux_membership_open_stint'"
        ).first()
        if legacy:
            conn.exec_driver_sql("DROP INDEX ux_membership_open_stint")
        for table, columns in _ADDED_COLUMNS.items():
            existing = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})")}
            for name, ddl in columns.items():
                if name not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")

        # Destructive one-off migration: only for un-migrated databases. A
        # shipped/read-only runtime DB is already at SCHEMA_VERSION, so this
        # merge (which UPDATEs and DELETEs organization rows) never runs there.
        if needs_migration:
            _merge_legacy_cross_chamber_groups(conn)

        # Fail fast. A duplicate that blocks one of these indexes is a data
        # defect, not a condition to log and ignore: the old try/except left
        # the shipped DB without ux_membership_closed_stint on every launch.
        for ddl in _PARTIAL_INDEXES:
            conn.exec_driver_sql(ddl)

        # Mark the migration done only after every step succeeded.
        if needs_migration:
            conn.exec_driver_sql(f"PRAGMA user_version = {SCHEMA_VERSION}")


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def get_session(db_path: str | Path | None = None) -> Session:
    engine = make_engine(db_path)
    init_db(engine)
    return make_session_factory(engine)()
