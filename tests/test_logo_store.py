"""Back-end storage and API contract for brand logo files."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import backend.logo_store as store

SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4" fill="currentColor" opacity="0.25"/></svg>'
PNG = b"\x89PNG\r\n\x1a\n" + b"x" * 32


@pytest.fixture()
def logo_env(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "LOGO_DIR", tmp_path / "logos")
    monkeypatch.setattr(store, "INDEX_PATH", tmp_path / "logos" / "index.json")
    return store


def test_save_list_activate_delete(logo_env):
    first = logo_env.save_logo("image/svg+xml", SVG)
    second = logo_env.save_logo("image/png", PNG)
    assert first["active"] is True
    assert second["active"] is False
    assert logo_env.get_active_logo()["id"] == first["id"]
    assert len(logo_env.list_logos()) == 2
    assert logo_env.logo_bytes(first) == SVG

    logo_env.activate_logo(second["id"])
    assert logo_env.get_active_logo()["id"] == second["id"]

    assert logo_env.delete_logo(second["id"]) is True
    assert logo_env.get_active_logo()["id"] == first["id"]
    assert logo_env.get_logo(second["id"]) is None


def test_upload_validation(logo_env):
    with pytest.raises(logo_env.LogoError):
        logo_env.save_logo("application/x-msdownload", b"MZ")
    with pytest.raises(logo_env.LogoError):
        logo_env.save_logo("image/png", b"not a png")
    with pytest.raises(logo_env.LogoError):
        logo_env.save_logo(
            "image/svg+xml",
            b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        )
    with pytest.raises(logo_env.LogoError):
        logo_env.save_logo(
            "image/svg+xml", b'<svg xmlns="http://www.w3.org/2000/svg"><path onclick="x()"/></svg>'
        )
    with pytest.raises(logo_env.LogoError):
        logo_env.save_logo("image/svg+xml", b"x" * (logo_env.MAX_LOGO_BYTES + 1))


def test_logo_api_requires_admin_token_and_serves_active(logo_env, monkeypatch):
    monkeypatch.setenv("PARLAMENT_ADMIN_TOKEN", "test-token")
    from backend.main import create_app

    with TestClient(create_app()) as client:
        assert client.get("/api/logo").status_code == 404
        assert (
            client.post(
                "/api/logo", content=SVG, headers={"Content-Type": "image/svg+xml"}
            ).status_code
            == 401
        )

        uploaded = client.post(
            "/api/logo",
            content=SVG,
            headers={"Content-Type": "image/svg+xml", "X-Admin-Token": "test-token"},
        )
        assert uploaded.status_code == 200, uploaded.text
        logo_id = uploaded.json()["data"]["id"]

        served = client.get("/api/logo")
        assert served.status_code == 200
        assert b"<svg" in served.content and b"currentColor" in served.content
        assert len(served.content) >= len(SVG)
        assert served.headers["content-type"].startswith("image/svg+xml")
        assert b'color="#38bdf8"' in served.content
        assert b'opacity="0.55"' in served.content  # boosted small-size legibility
        tinted = client.get("/api/logo?color=%230369a1")
        assert b'color="#0369a1"' in tinted.content
        assert b"currentColor" in served.content  # palette applied via root color
        assert "default-src 'self'" in served.headers.get("content-security-policy", "")

        listed = client.get("/api/logo/list")
        assert listed.status_code == 200
        assert listed.json()["data"][0]["id"] == logo_id
        assert "stored_name" not in listed.json()["data"][0]

        assert (
            client.post(
                f"/api/logo/{logo_id}/activate", headers={"X-Admin-Token": "test-token"}
            ).status_code
            == 200
        )
        assert (
            client.delete(
                f"/api/logo/{logo_id}", headers={"X-Admin-Token": "test-token"}
            ).status_code
            == 200
        )
        assert client.get("/api/logo").status_code == 404
