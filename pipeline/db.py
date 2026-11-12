"""SQLAlchemy models + SQLite (WAL) store.

Popolo vocabulary, bitemporal (valid-time vs transaction-time), event-sourced.
One codebase serves both chambers via a chamber enum. Every membership carries
provenance, confidence and date precision; closed tenures are immutable.
"""

from __future__ import annotations

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

# --- Enumerations (stored as strings for SQLite portability) ---------------
CHAMBERS = ("deputies", "senate")
ORG_CLASS = (
    "chamber", "group", "party", "committee", "bureau",
    "delegation", "friendship", "other",
)
CONFIDENCE = ("official_ledger", "official_profile", "derived", "community")
CONFIDENCE_RANK = {c: i for i, c in enumerate(CONFIDENCE)}  # lower = stronger
REASONS = (
    "CHANGED_PARTY", "WHIP_REMOVED", "WHIP_RESTORED", "DIED", "RESIGNED",
    "BY_ELECTION", "GENERAL_ELECTION", "UNKNOWN",
)
EVIDENCE_TYPES = ("official_ledger", "profile", "jo", "intervention", "scrutin", "other")
EVENT_TYPES = (
    "join", "leave", "switch_group", "switch_party", "group_founded",
    "group_renamed", "committee_join", "committee_leave", "role_change",
    "mandate_start", "mandate_end",
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
    # Party genealogy
    previous_party_id: Mapped[str | None] = mapped_column(ForeignKey("organization.id"), nullable=True)
    successor_party_id: Mapped[str | None] = mapped_column(ForeignKey("organization.id"), nullable=True)

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
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    person: Mapped[Person] = relationship()
    org: Mapped[Organization] = relationship(foreign_keys=[org_id])
    party: Mapped[Organization | None] = relationship(foreign_keys=[on_behalf_of_id])

    __table_args__ = (
        UniqueConstraint("org_id", "person_id", "post_id", "end_date", name="uq_stint"),
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
    person_id: Mapped[str | None] = mapped_column(ForeignKey("person.id"), nullable=True, index=True)
    chamber: Mapped[str | None] = mapped_column(String(16), nullable=True)
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
    summary_ro: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    dedup_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)


class SwitchWave(Base):
    """Cluster of party switches detected within a time window, optionally labeled with a trigger event."""
    __tablename__ = "switch_wave"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g., "Post-2020 election wave"
    start_date: Mapped[date] = mapped_column(Date, index=True)
    end_date: Mapped[date] = mapped_column(Date, index=True)
    switch_count: Mapped[int] = mapped_column(Integer, default=0)
    trigger_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # WAVE_TRIGGERS
    trigger_event: Mapped[str | None] = mapped_column(Text, nullable=True)  # human-readable description
    legislature: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    chamber: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    __table_args__ = (
        Index("ix_switch_wave_leg_chamber", "legislature", "chamber"),
    )


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
DEFAULT_DB_PATH = Path(os.environ.get("PARLAMENT_DB", "data/parlament.db"))


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


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def get_session(db_path: str | Path | None = None) -> Session:
    engine = make_engine(db_path)
    init_db(engine)
    return make_session_factory(engine)()