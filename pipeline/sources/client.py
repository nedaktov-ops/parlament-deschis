"""Polite HTTP client for official chamber sites.

Built-in compliance: identifying User-Agent, robots.txt honored, per-host
pacing (<=1 req/s), exponential backoff, conditional GET (ETag/Last-Modified),
429 -> wait, and a hard stop on CAPTCHA/challenge pages (never bypassed).
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

log = logging.getLogger("parlament.client")

USER_AGENT = "ParlamentDeschis/1.0 (+https://github.com/parlament-deschis; civic transparency)"
DEFAULT_SLEEP = 2.5
DEFAULT_TIMEOUT = 25
MAX_RETRIES = 4


class CaptchaError(RuntimeError):
    """Raised when a source returns a CAPTCHA/challenge — stop, never bypass."""


class RobotsDisallowed(RuntimeError):
    """Raised when robots.txt forbids the URL."""


@dataclass
class FetchResult:
    url: str
    status: int
    text: str
    from_cache: bool = False
    etag: str | None = None
    last_modified: str | None = None


@dataclass
class _HostState:
    last_request: float = 0.0
    robots: RobotFileParser | None = None
    robots_checked: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)


class PoliteClient:
    def __init__(
        self,
        sleep: float = DEFAULT_SLEEP,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = USER_AGENT,
        respect_robots: bool = True,
    ):
        self.sleep = sleep
        self.timeout = timeout
        self.user_agent = user_agent
        self.respect_robots = respect_robots
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self._hosts: dict[str, _HostState] = {}
        self._conditional: dict[str, dict] = {}

    def _host(self, url: str) -> _HostState:
        netloc = urlparse(url).netloc
        if netloc not in self._hosts:
            self._hosts[netloc] = _HostState()
        return self._hosts[netloc]

    def _check_robots(self, url: str, host: _HostState) -> None:
        if not self.respect_robots or host.robots_checked:
            return
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        try:
            resp = self.session.get(robots_url, timeout=self.timeout)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
            else:
                rp.parse([])  # no robots → allow all
        except requests.RequestException:
            rp.parse([])
        host.robots = rp
        host.robots_checked = True

    def _pace(self, host: _HostState) -> None:
        with host.lock:
            elapsed = time.monotonic() - host.last_request
            if elapsed < self.sleep:
                time.sleep(self.sleep - elapsed)
            host.last_request = time.monotonic()

    @staticmethod
    def _looks_like_challenge(text: str) -> bool:
        low = text[:4000].lower()
        return any(
            k in low
            for k in [
                "captcha",
                "cf-challenge",
                "are you a robot",
                "access denied",
                "verify you are human",
            ]
        )

    def get(
        self,
        url: str,
        *,
        conditional: bool = True,
        cached_text: str | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> FetchResult:
        host = self._host(url)
        self._check_robots(url, host)
        if self.respect_robots and host.robots and not host.robots.can_fetch(self.user_agent, url):
            raise RobotsDisallowed(url)

        if cached_text is not None:
            self._conditional[url] = {
                "text": cached_text,
                "etag": etag,
                "last_modified": last_modified,
            }

        headers = {}
        if conditional and url in self._conditional:
            cached = self._conditional[url]
            if cached.get("etag"):
                headers["If-None-Match"] = cached["etag"]
            if cached.get("last_modified"):
                headers["If-Modified-Since"] = cached["last_modified"]

        backoff = 2.0
        for attempt in range(MAX_RETRIES):
            self._pace(host)
            try:
                resp = self.session.get(url, headers=headers, timeout=self.timeout)
            except requests.RequestException as exc:
                log.warning("request error %s: %s", url, exc)
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(backoff)
                backoff *= 2
                continue

            if resp.status_code == 304:
                cached = self._conditional.get(url, {})
                if "text" not in cached:
                    raise RuntimeError(f"source returned 304 without a cached response: {url}")
                etag = resp.headers.get("ETag", cached.get("etag"))
                last_modified = resp.headers.get("Last-Modified", cached.get("last_modified"))
                self._conditional[url] = {
                    "text": cached["text"],
                    "etag": etag,
                    "last_modified": last_modified,
                }
                return FetchResult(
                    url,
                    304,
                    cached["text"],
                    from_cache=True,
                    etag=etag,
                    last_modified=last_modified,
                )
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", "60"))
                log.warning("429 from %s, waiting %ss", url, wait)
                time.sleep(min(wait, 120))
                continue
            if resp.status_code >= 500:
                if attempt == MAX_RETRIES - 1:
                    resp.raise_for_status()
                time.sleep(backoff)
                backoff *= 2
                continue

            resp.raise_for_status()
            resp.encoding = resp.encoding or "utf-8"
            text = resp.text
            if self._looks_like_challenge(text):
                raise CaptchaError(url)
            etag = resp.headers.get("ETag")
            lm = resp.headers.get("Last-Modified")
            self._conditional[url] = {"etag": etag, "last_modified": lm, "text": text}
            return FetchResult(url, resp.status_code, text, etag=etag, last_modified=lm)
        raise RuntimeError(f"failed to fetch {url}")

    def close(self):
        self.session.close()
