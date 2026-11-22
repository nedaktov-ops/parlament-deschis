"""Disk-backed storage for brand logo files.

The corpus database is a read-only, baked artifact, so logos are kept in a
separate writable directory (`data/assets/logos` by default) with a small JSON
index. No new Python dependencies are required.

All writes are atomic: the file is written to a temporary name and renamed,
then the index is replaced the same way. A reader therefore never sees a
half-written logo or index.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

from backend.config import _rooted

LOGO_DIR = _rooted("PARLAMENT_LOGO_DIR", "data/assets/logos")
INDEX_PATH = LOGO_DIR / "index.json"

MAX_LOGO_BYTES = 512 * 1024
ALLOWED_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}

# Only these SVG elements/attributes are accepted. Event handlers, external
# references, style elements and <script> are rejected outright so an admin
# upload cannot become stored XSS when the logo is served inline.
_SVG_ALLOWED_ELEMENTS = {
    "svg",
    "g",
    "path",
    "circle",
    "ellipse",
    "rect",
    "line",
    "polyline",
    "polygon",
    "defs",
    "title",
    "desc",
}
_SVG_ALLOWED_ATTR_PREFIXES = (
    "d",
    "cx",
    "cy",
    "r",
    "rx",
    "ry",
    "x",
    "y",
    "x1",
    "y1",
    "x2",
    "y2",
    "width",
    "height",
    "viewbox",
    "fill",
    "stroke",
    "opacity",
    "transform",
    "points",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
    "fill-rule",
    "clip-rule",
    "id",
    "class",
    "xmlns",
    "version",
)
_SVG_FORBIDDEN_ATTR = re.compile(r"^(on|href$|xlink:href$|style$)", re.I)


class LogoError(ValueError):
    """Raised for invalid upload input."""


def _utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _validate_svg(data: bytes) -> None:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:  # pragma: no cover - message varies by Python
        raise LogoError("invalid SVG XML") from exc
    for element in root.iter():
        tag = element.tag.split("}", 1)[-1]
        if tag not in _SVG_ALLOWED_ELEMENTS:
            raise LogoError(f"SVG element not allowed: {tag}")
        for name in element.attrib:
            local = name.split("}", 1)[-1].lower()
            if _SVG_FORBIDDEN_ATTR.match(local):
                raise LogoError(f"SVG attribute not allowed: {name}")
            if local not in _SVG_ALLOWED_ATTR_PREFIXES:
                raise LogoError(f"SVG attribute not allowed: {name}")


def _validate(content_type: str, data: bytes) -> None:
    if content_type not in ALLOWED_TYPES:
        raise LogoError("unsupported logo content type")
    if not data:
        raise LogoError("empty logo file")
    if len(data) > MAX_LOGO_BYTES:
        raise LogoError("logo file too large")
    if content_type == "image/svg+xml":
        _validate_svg(data)
    elif content_type == "image/png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise LogoError("invalid PNG signature")
    elif content_type == "image/jpeg" and not data.startswith(b"\xff\xd8\xff"):
        raise LogoError("invalid JPEG signature")
    elif content_type == "image/webp" and not (data[:4] == b"RIFF" and data[8:12] == b"WEBP"):
        raise LogoError("invalid WebP signature")


def _read_index() -> list[dict[str, Any]]:
    if not INDEX_PATH.exists():
        return []
    try:
        value = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return value if isinstance(value, list) else []


def _write_index(items: list[dict[str, Any]]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".index.", suffix=".json", dir=INDEX_PATH.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(items, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(tmp, INDEX_PATH)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def list_logos() -> list[dict[str, Any]]:
    return list(_read_index())


def get_logo(logo_id: str) -> dict[str, Any] | None:
    return next((item for item in _read_index() if item.get("id") == logo_id), None)


def get_active_logo() -> dict[str, Any] | None:
    return next((item for item in _read_index() if item.get("active")), None)


def logo_bytes(item: dict[str, Any]) -> bytes:
    path = LOGO_DIR / item["stored_name"]
    return path.read_bytes()


def save_logo(content_type: str, data: bytes) -> dict[str, Any]:
    _validate(content_type, data)
    LOGO_DIR.mkdir(parents=True, exist_ok=True)
    logo_id = uuid.uuid4().hex
    stored_name = f"{logo_id}{ALLOWED_TYPES[content_type]}"
    target = LOGO_DIR / stored_name
    fd, tmp = tempfile.mkstemp(prefix=".logo.", dir=LOGO_DIR)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

    items = _read_index()
    item = {
        "id": logo_id,
        "stored_name": stored_name,
        "content_type": content_type,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "created_at": _utcnow(),
        "active": not any(existing.get("active") for existing in items),
    }
    items.append(item)
    _write_index(items)
    return item


def activate_logo(logo_id: str) -> dict[str, Any] | None:
    items = _read_index()
    item = next((entry for entry in items if entry.get("id") == logo_id), None)
    if item is None:
        return None
    for entry in items:
        entry["active"] = entry.get("id") == logo_id
    _write_index(items)
    return item


def delete_logo(logo_id: str) -> bool:
    items = _read_index()
    item = next((entry for entry in items if entry.get("id") == logo_id), None)
    if item is None:
        return False
    remaining = [entry for entry in items if entry.get("id") != logo_id]
    if item.get("active") and remaining and not any(e.get("active") for e in remaining):
        remaining[-1]["active"] = True
    _write_index(remaining)
    path = LOGO_DIR / item["stored_name"]
    if path.exists():
        path.unlink()
    return True


__all__ = [
    "ALLOWED_TYPES",
    "LOGO_DIR",
    "MAX_LOGO_BYTES",
    "LogoError",
    "activate_logo",
    "delete_logo",
    "get_active_logo",
    "get_logo",
    "list_logos",
    "logo_bytes",
    "save_logo",
]
