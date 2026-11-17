from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import random
import re
import shutil
import socket
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

logger = logging.getLogger(__name__)

# Only GitHub's own hosts may serve the dataset. The release API supplies the
# asset URL, so trusting it blindly would be SSRF. Verified 2026-11-17 with a
# read-only HEAD probe: api.github.com redirects release assets to
# release-assets.githubusercontent.com (NOT objects.githubusercontent.com,
# which is used for other GitHub assets). Both are GitHub-controlled.
ALLOWED_ASSET_HOSTS = frozenset(
    {
        "api.github.com",
        "objects.githubusercontent.com",
        "release-assets.githubusercontent.com",
    }
)


class UnsafeRedirectError(RuntimeError):
    """Raised when a redirect leaves the GitHub-controlled asset hosts."""


class _SafeRedirectHandler(HTTPRedirectHandler):
    """Follow redirects, but never forward Authorization to another host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is None:
            return None
        new_host = (urlsplit(newurl).hostname or "").lower()
        if new_host not in ALLOWED_ASSET_HOSTS:
            raise UnsafeRedirectError(f"refusing redirect to disallowed host: {new_host!r}")
        original_host = (urlsplit(req.full_url).hostname or "").lower()
        if original_host != new_host:
            redirected.remove_header("Authorization")
        return redirected


_OPENER = build_opener(_SafeRedirectHandler())


def urlopen(request: Request, *, timeout: int):
    """Open a request through the allowlisting, auth-stripping opener."""
    return _OPENER.open(request, timeout=timeout)


_RETRYABLE_EXCEPTIONS = (URLError, HTTPError, socket.timeout, ConnectionError, TimeoutError)

_MAX_ATTEMPTS = 6
_INITIAL_BACKOFF_SECONDS = 2.0
_MAX_BACKOFF_SECONDS = 30.0
_JITTER_SECONDS = 1.0


def _urlopen_with_retry(request: Request, *, timeout: int):
    """Open a URL with exponential backoff and jitter for transient failures.

    Retries on ``URLError``, ``HTTPError``, ``socket.timeout``,
    ``ConnectionError`` and ``TimeoutError`` so that an intermittent cdep.ro
    or GitHub API timeout does not fail the whole download.
    """
    delay = _INITIAL_BACKOFF_SECONDS
    last_error: Exception | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            return urlopen(request, timeout=timeout)
        except _RETRYABLE_EXCEPTIONS as exc:
            last_error = exc
            if attempt == _MAX_ATTEMPTS:
                logger.error(
                    "urlopen failed after %d attempts for %s: %s",
                    _MAX_ATTEMPTS,
                    request.full_url,
                    exc,
                )
                raise
            sleep_for = min(delay, _MAX_BACKOFF_SECONDS) + random.uniform(0, _JITTER_SECONDS)
            logger.warning(
                "urlopen attempt %d/%d failed for %s (%s); retrying in %.1fs",
                attempt,
                _MAX_ATTEMPTS,
                request.full_url,
                exc,
                sleep_for,
            )
            time.sleep(sleep_for)
            delay = min(delay * 2, _MAX_BACKOFF_SECONDS)
    raise last_error  # pragma: no cover - unreachable once max attempts raise


RELEASE_API_URL = "https://api.github.com/repos/nedaktov-ops/parlament-deschis/releases/tags"
USER_AGENT = "parlament-deschis-deployment"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
DEFAULT_RELEASE_TAG = Path(__file__).resolve().parent.parent / "data" / "latest-release.txt"


def _read_release_tag(explicit_tag: str | None) -> str:
    tag = explicit_tag
    if tag is None:
        tag = DEFAULT_RELEASE_TAG.read_text(encoding="utf-8").strip()
    if not tag or not re.fullmatch(r"[A-Za-z0-9._-]+", tag):
        raise ValueError(f"invalid dataset release tag: {tag!r}")
    return tag


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_asset_url(url: str) -> None:
    host = (urlsplit(url).hostname or "").lower()
    if host not in ALLOWED_ASSET_HOSTS:
        raise RuntimeError(f"refusing dataset download from untrusted host: {host!r}")


def download_dataset(
    destination: Path,
    *,
    release_tag: str | None = None,
    metadata_path: Path | None = None,
) -> dict:
    if metadata_path is not None and metadata_path.resolve() == destination.resolve():
        raise ValueError("dataset and metadata paths must be different")
    tag = _read_release_tag(release_tag)
    release_request = Request(
        f"{RELEASE_API_URL}/{quote(tag, safe='')}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            **({"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}),
        },
    )
    with _urlopen_with_retry(release_request, timeout=30) as response:
        release = json.load(response)
    if release.get("tag_name") != tag:
        raise RuntimeError(f"GitHub returned a different release than requested: {tag}")

    asset = next(
        (item for item in release.get("assets", []) if item.get("name") == "parlament.db"),
        None,
    )
    if asset is None:
        raise RuntimeError(f"Dataset release {tag} has no parlament.db asset")
    expected_digest = asset.get("digest")
    if not isinstance(expected_digest, str) or not re.fullmatch(
        r"sha256:[0-9a-f]{64}", expected_digest
    ):
        raise RuntimeError(f"Dataset release {tag} has no valid SHA-256 asset digest")

    _validate_asset_url(asset["url"])
    asset_request = Request(
        asset["url"],
        headers={
            "Accept": "application/octet-stream",
            "User-Agent": USER_AGENT,
            **({"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}),
        },
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "release_tag": tag,
        "published_at": release.get("published_at"),
        "release_url": release.get("html_url"),
        "asset_name": asset["name"],
        "asset_sha256": expected_digest.removeprefix("sha256:"),
    }

    with tempfile.TemporaryDirectory(
        prefix=f".{destination.name}.", dir=destination.parent
    ) as temp_dir:
        temp_destination = Path(temp_dir) / destination.name
        with (
            _urlopen_with_retry(asset_request, timeout=300) as response,
            temp_destination.open("wb") as output,
        ):
            shutil.copyfileobj(response, output)
        actual_digest = _sha256(temp_destination)
        if actual_digest != metadata["asset_sha256"]:
            raise RuntimeError(
                f"Dataset release {tag} checksum mismatch: "
                f"expected {metadata['asset_sha256']}, got {actual_digest}"
            )
        os.replace(temp_destination, destination)

    if metadata_path is not None:
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=metadata_path.parent, delete=False
        ) as temporary:
            temporary.write(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
            temporary_metadata = Path(temporary.name)
        try:
            os.replace(temporary_metadata, metadata_path)
        finally:
            temporary_metadata.unlink(missing_ok=True)
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download a pinned public dataset release.")
    parser.add_argument("destination", type=Path)
    parser.add_argument("--release-tag")
    parser.add_argument("--metadata", type=Path)
    args = parser.parse_args()
    download_dataset(
        args.destination,
        release_tag=args.release_tag,
        metadata_path=args.metadata,
    )
