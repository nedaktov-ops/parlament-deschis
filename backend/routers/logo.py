"""Logo storage API.

Reads are public so the site header can render the brand mark. Writes require
the same fail-closed admin token as the other administrative endpoints.
"""

from __future__ import annotations

import re
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response

from backend import logo_store
from backend.routers.api import _require_admin_token

router = APIRouter(prefix="/api/logo", tags=["logo"])

# An SVG loaded through <img> cannot inherit the page's CSS `color`, so any
# `currentColor` paint would resolve to black and disappear on the dark header.
# The client passes a theme-appropriate sky accent; the default is the bright
# variant with 8.33:1 contrast on the dark (#0f172a) header.
LOGO_ACCENT = "#38bdf8"
_SAFE_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def _tint_svg(data: bytes, color: str | None = None) -> bytes:
    accent = color if color and _SAFE_COLOR.match(color) else LOGO_ACCENT
    text = data.decode("utf-8")
    match = re.search(r"<svg\b[^>]*>", text)
    if match is None:
        return data
    tag = match.group(0)
    if re.search(r"\scolor\s*=", tag):
        tag = re.sub(r"\scolor\s*=\s*[\"'][^\"']*[\"']", f' color="{accent}"', tag, count=1)
    else:
        tag = f'{tag[:-1]} color="{accent}">'
    text = text[: match.start()] + tag + text[match.end() :]

    # The authored opacity ladder reads well at 200px but too faint at the
    # 36px header size. Lift every shape to at least 0.55 while keeping the
    # relative layering, so the mark stays legible in both themes.
    def boost(value: re.Match[str]) -> str:
        alpha = float(value.group(1))
        return f' opacity="{min(1.0, max(0.55, alpha * 1.25)):.2f}"'

    text = re.sub(r'\sopacity="([0-9.]+)"', boost, text)
    return text.encode("utf-8")


def _public(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if key != "stored_name"}


def _logo_response(item: dict[str, Any], color: str | None = None) -> Response:
    # The app-wide security middleware supplies CSP, nosniff and no-store
    # headers; the upload sanitiser rejects scripts and event handlers in SVG.
    content = logo_store.logo_bytes(item)
    if item["content_type"] == "image/svg+xml":
        content = _tint_svg(content, color)
    return Response(content=content, media_type=item["content_type"])


@router.get("")
def active_logo(color: Annotated[str | None, Query()] = None) -> Response:
    item = logo_store.get_active_logo()
    if item is None:
        raise HTTPException(status_code=404, detail="no logo stored")
    return _logo_response(item, color)


@router.get("/list")
def list_logos() -> dict[str, Any]:
    return {"status": "ok", "data": [_public(item) for item in logo_store.list_logos()]}


@router.get("/{logo_id}")
def logo_by_id(logo_id: str, color: Annotated[str | None, Query()] = None) -> Response:
    item = logo_store.get_logo(logo_id)
    if item is None:
        raise HTTPException(status_code=404, detail="logo not found")
    return _logo_response(item, color)


@router.post("")
async def upload_logo(
    request: Request,
    x_admin_token: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    _require_admin_token(x_admin_token, "logo upload", request=request)
    content_type = (request.headers.get("content-type") or "").split(";", 1)[0].strip()
    data = await request.body()
    try:
        item = logo_store.save_logo(content_type, data)
    except logo_store.LogoError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok", "data": _public(item)}


@router.post("/{logo_id}/activate")
def activate_logo(
    logo_id: str,
    request: Request,
    x_admin_token: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    _require_admin_token(x_admin_token, "logo activation", request=request)
    item = logo_store.activate_logo(logo_id)
    if item is None:
        raise HTTPException(status_code=404, detail="logo not found")
    return {"status": "ok", "data": _public(item)}


@router.delete("/{logo_id}")
def delete_logo(
    logo_id: str,
    request: Request,
    x_admin_token: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    _require_admin_token(x_admin_token, "logo deletion", request=request)
    if not logo_store.delete_logo(logo_id):
        raise HTTPException(status_code=404, detail="logo not found")
    return {"status": "ok", "deleted": logo_id}
