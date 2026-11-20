"""The polite HTTP client must expose the raw response bytes.

Why: the evidence culture of this project hashes the *original* bytes of a
source page. ``FetchResult.text`` is a decoded string, so re-encoding it can
change the bytes (and does for the cdep XML, whose HTTP header says UTF-8
while the XML prolog claims ISO-8859-2). The capture script therefore needs
``FetchResult.content`` to archive byte-exact fixtures.

All requests are served by an in-process fake session: no network, no robots
lookup, no sleeping.
"""

from __future__ import annotations

import pytest

from pipeline.sources.client import CaptchaError, PoliteClient


class _FakeResponse:
    def __init__(self, content: bytes, status_code: int = 200, encoding: str = "utf-8"):
        self.content = content
        self.status_code = status_code
        self.encoding = encoding
        self.headers: dict[str, str] = {}
        self.text = content.decode(encoding, "replace")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeSession:
    """Serves ``robots.txt`` as 404 and everything else with fixed bytes."""

    def __init__(self, body: bytes, status_code: int = 200):
        self.body = body
        self.status_code = status_code
        self.headers: dict[str, str] = {}
        self.requests: list[str] = []

    def get(self, url, headers=None, timeout=None):
        self.requests.append(url)
        if url.endswith("/robots.txt"):
            return _FakeResponse(b"", status_code=404)
        return _FakeResponse(self.body, status_code=self.status_code)

    def close(self) -> None:
        pass


def test_get_exposes_exact_response_bytes():
    raw = b"<?xml version='1.0'?>\n<name>Dr\xc4\x83goescu</name>\n"
    client = PoliteClient(sleep=0)
    client.session = _FakeSession(raw)

    result = client.get("https://www.cdep.ro/ords/pls/steno/evot2015.xml?par1=2&par2=37526")

    assert result.content == raw
    assert result.content.decode("utf-8") == result.text


def test_get_bytes_are_not_rounded_through_text_encoding():
    """A page declared ISO-8859-2 but served as UTF-8 must keep its bytes."""
    raw = b"<x>\xc4\x83</x>"
    client = PoliteClient(sleep=0)
    client.session = _FakeSession(raw)

    result = client.get("https://example.test/page")

    assert result.content == raw
    assert result.text != result.content.decode("iso-8859-2")


@pytest.mark.parametrize("body", [b"<!doctype html>Are you a robot?"])
def test_challenge_page_never_returns_content(body):
    client = PoliteClient(sleep=0)
    client.session = _FakeSession(body)

    with pytest.raises(CaptchaError):
        client.get("https://example.test/challenge")
