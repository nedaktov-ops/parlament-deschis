"""Raw snapshot store: decouples fetched source data from the normalized model
(HowTheyVote Fragment pattern). Each fetch is archived on disk by content hash
and recorded as a Fragment row; unchanged content is skipped via SHA256.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Fragment

SNAPSHOT_DIR = Path("data/snapshots")


def checksum(content: str | bytes) -> str:
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def archive_snapshot(source: str, content: str | bytes, ext: str = "html") -> tuple[str, Path]:
    """Write content to data/snapshots/<source>/<hash>.<ext>; return (hash, path)."""
    h = checksum(content)
    directory = SNAPSHOT_DIR / source
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{h}.{ext}"
    if not path.exists():
        path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
    return h, path


def latest_checksum(session: Session, source: str, group_key: str) -> str | None:
    stmt = (
        select(Fragment.checksum)
        .where(Fragment.source_name == source, Fragment.group_key == group_key)
        .order_by(Fragment.timestamp.desc())
        .limit(1)
    )
    return session.scalars(stmt).first()


def record_fragment(
    session: Session,
    *,
    model: str,
    source_name: str,
    group_key: str,
    content: str | bytes,
    source_id: str | None = None,
    source_url: str | None = None,
    data: dict | None = None,
    ext: str = "html",
    force: bool = False,
) -> tuple[Fragment | None, bool]:
    """Archive + record a fragment. Returns (fragment, changed).

    If the content checksum matches the latest fragment for this group_key and
    force is False, returns (None, False) — skip unchanged.
    """
    h = checksum(content)
    if not force and latest_checksum(session, source_name, group_key) == h:
        return None, False
    _, path = archive_snapshot(source_name, content, ext)
    frag = Fragment(
        model=model,
        source_name=source_name,
        source_id=source_id,
        source_url=source_url,
        group_key=group_key,
        checksum=h,
        data=data or {},
        snapshot_path=str(path),
    )
    session.add(frag)
    session.flush()
    return frag, True
