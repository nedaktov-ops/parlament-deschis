from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from urllib.request import Request, urlopen

RELEASE_API_URL = "https://api.github.com/repos/nedaktov-ops/parlament-deschis/releases/latest"
USER_AGENT = "parlament-deschis-deployment"


def download_dataset(destination: Path) -> None:
    release_request = Request(
        RELEASE_API_URL,
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT},
    )
    with urlopen(release_request, timeout=30) as response:
        release = json.load(response)

    asset = next(
        (item for item in release.get("assets", []) if item.get("name") == "parlament.db"),
        None,
    )
    if asset is None:
        raise RuntimeError(f"Latest GitHub release has no parlament.db asset: {RELEASE_API_URL}")

    asset_request = Request(
        asset["url"],
        headers={"Accept": "application/octet-stream", "User-Agent": USER_AGENT},
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(asset_request, timeout=300) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: download_dataset.py <destination>")
    download_dataset(Path(sys.argv[1]))
