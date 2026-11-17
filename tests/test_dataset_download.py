from __future__ import annotations

import hashlib
import io
import json
from urllib.request import Request

import pytest

from scripts import download_dataset


def _release_response(tag: str, dataset: bytes) -> dict:
    return {
        "tag_name": tag,
        "published_at": "2026-11-14T10:55:25Z",
        "html_url": f"https://github.com/nedaktov-ops/parlament-deschis/releases/tag/{tag}",
        "assets": [
            {
                "name": "parlament.db",
                "url": "https://api.github.com/assets/1",
                "digest": f"sha256:{hashlib.sha256(dataset).hexdigest()}",
            }
        ],
    }


def test_download_dataset_pins_release_and_writes_verified_metadata(tmp_path, monkeypatch):
    tag = "data-123-1"
    dataset = b"verified database asset"
    release = _release_response(tag, dataset)
    requests: list[Request] = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        if request.full_url.endswith(f"/releases/tags/{tag}"):
            return io.BytesIO(json.dumps(release).encode())
        if request.full_url == "https://api.github.com/assets/1":
            return io.BytesIO(dataset)
        raise AssertionError(f"unexpected URL: {request.full_url}")

    monkeypatch.setattr(download_dataset, "urlopen", fake_urlopen)
    destination = tmp_path / "parlament.db"
    metadata_path = tmp_path / "dataset-metadata.json"

    metadata = download_dataset.download_dataset(
        destination,
        release_tag=tag,
        metadata_path=metadata_path,
    )

    assert destination.read_bytes() == dataset
    assert metadata["release_tag"] == tag
    assert metadata["asset_sha256"] == hashlib.sha256(dataset).hexdigest()
    assert json.loads(metadata_path.read_text(encoding="utf-8")) == metadata
    assert f"/releases/tags/{tag}" in requests[0].full_url


def test_download_dataset_checksum_mismatch_preserves_existing_file(tmp_path, monkeypatch):
    tag = "data-123-1"
    destination = tmp_path / "parlament.db"
    destination.write_bytes(b"last known good")
    release = _release_response(tag, b"different data")

    def fake_urlopen(request, timeout):
        if request.full_url.endswith(f"/releases/tags/{tag}"):
            return io.BytesIO(json.dumps(release).encode())
        return io.BytesIO(b"corrupted transfer")

    monkeypatch.setattr(download_dataset, "urlopen", fake_urlopen)

    with pytest.raises(RuntimeError, match="checksum mismatch"):
        download_dataset.download_dataset(destination, release_tag=tag)

    assert destination.read_bytes() == b"last known good"


def test_download_dataset_rejects_unpinned_tag(tmp_path):
    with pytest.raises(ValueError, match="invalid dataset release tag"):
        download_dataset.download_dataset(tmp_path / "parlament.db", release_tag="../latest")


def test_download_dataset_rejects_metadata_path_equal_to_database(tmp_path):
    destination = tmp_path / "parlament.db"
    with pytest.raises(ValueError, match="paths must be different"):
        download_dataset.download_dataset(
            destination,
            release_tag="data-123-1",
            metadata_path=destination,
        )


def test_github_release_asset_redirect_host_is_allowlisted():
    """Regression: a real HEAD probe (2026-11-17) showed GitHub redirects
    release assets to release-assets.githubusercontent.com, not to
    objects.githubusercontent.com. Omitting it made CI's audit download fail
    with UnsafeRedirectError. Pin all observed hosts here.
    """
    assert "release-assets.githubusercontent.com" in download_dataset.ALLOWED_ASSET_HOSTS
    assert "objects.githubusercontent.com" in download_dataset.ALLOWED_ASSET_HOSTS
    assert "api.github.com" in download_dataset.ALLOWED_ASSET_HOSTS

    handler = download_dataset._SafeRedirectHandler()
    from urllib.request import Request

    req = Request("https://api.github.com/assets/1", headers={"Authorization": "Bearer secret"})
    # Same-host redirect forwards the header; cross-host strips it.
    same = handler.redirect_request(req, None, 302, "Found", {}, "https://api.github.com/assets/2")
    assert same.get_header("Authorization") == "Bearer secret"
    redirected = handler.redirect_request(
        req, None, 302, "Found", {}, "https://release-assets.githubusercontent.com/x"
    )
    assert redirected.get_header("Authorization") is None
