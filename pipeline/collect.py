"""Collect the official cdep.ro corpus: both chambers, every legislature.

cdep.ro serves the whole Parliament from one application (``structura2015``)::

    cam=2   Chamber of Deputies        cam=1   Senate
    leg     legislature start year      idg     parliamentary group id (0 = unaffiliated)

The dated group ledgers (``gp?cam=&leg=&idg=``) are the only historical roster
the site publishes: the alphabetical MP list (``mp?cam=&leg=``) ignores ``leg``
and always returns the current legislature, so it cannot be used for history.

Every response is cached on disk with its SHA-256 and appended to a manifest, so
a re-run costs no requests, is reproducible, and every ingested row can be
traced back to the exact bytes it came from.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

import requests

from .parse.cdep_group import GroupLedger, parse_group_ledger, parse_group_list
from .parse.cdep_profile import DeputyProfile, MandateRef, parse_deputy_profile
from .parse.cdep_roster import Roster, parse_roster
from .sources.client import PoliteClient

log = logging.getLogger("parlament.collect")

BASE = "https://www.cdep.ro/ords/pls/parlam/structura2015"
CAM = {"deputies": "2", "senate": "1"}
CHAMBERS = ("deputies", "senate")
CACHE_ROOT = Path("data/cache/cdep")
DEFAULT_CACHE_TTL = timedelta(days=1)


def group_list_url(chamber: str, legislature: str) -> str:
    return f"{BASE}.gp?idl=1&cam={CAM[chamber]}&leg={legislature}"


def group_ledger_url(chamber: str, legislature: str, idg: str) -> str:
    return f"{BASE}.gp?cam={CAM[chamber]}&leg={legislature}&idg={idg}"


def profile_url(chamber: str, legislature: str, idm: str) -> str:
    return f"{BASE}.mp?idm={idm}&cam={CAM[chamber]}&leg={legislature}"


def roster_url(chamber: str, legislature: str) -> str:
    """The alphabetical roster of a legislature (a second view of the same data)."""
    return f"{BASE}.de?par=A&cam={CAM[chamber]}&leg={legislature}"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


@dataclass
class LedgerRecord:
    chamber: str
    legislature: str
    idg: str
    url: str
    sha256: str
    ledger: GroupLedger
    fetched_at: datetime


@dataclass
class ProfileRecord:
    mandate: MandateRef
    url: str
    sha256: str | None
    profile: DeputyProfile | None
    error: str | None = None


@dataclass
class Corpus:
    ledgers: list[LedgerRecord] = field(default_factory=list)
    profiles: dict[MandateRef, ProfileRecord] = field(default_factory=dict)
    # the roster view of each chamber/legislature, used as a cross-check
    rosters: list[Roster] = field(default_factory=list)
    # The member count the group index publishes for every group, per scope:
    # (chamber, legislature) -> {idg: count}. The index is the source's own
    # head-count, and it is what makes the three-view cross-check decidable.
    index_counts: dict[tuple[str, str], dict[str, int]] = field(default_factory=dict)
    # mandate -> stable person key
    clusters: dict[MandateRef, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def mandates(self) -> set[MandateRef]:
        return set(self.profiles) | set(self.clusters)


class _Union:
    """Minimal union-find over mandate keys."""

    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # path compression
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        # Keep the lexicographically smaller root so the cluster key is stable.
        if rb < ra:
            ra, rb = rb, ra
        self.parent[rb] = ra


def _cache_paths(cache_dir: Path, chamber: str, legislature: str, stem: str) -> tuple[Path, Path]:
    d = cache_dir / chamber / legislature
    return d / f"{stem}.html", d / f"{stem}.meta.json"


def fetch_cached(
    client: PoliteClient,
    url: str,
    html_path: Path,
    *,
    force: bool = False,
    offline: bool = False,
    cache_ttl: timedelta = DEFAULT_CACHE_TTL,
) -> tuple[str, str, datetime]:
    """Return cached source text, revalidating entries older than ``cache_ttl``."""
    meta_path = html_path.with_suffix(".meta.json")
    if cache_ttl < timedelta(0):
        raise ValueError("cache_ttl must not be negative")
    cached: tuple[dict, str, datetime, datetime] | None = None
    if html_path.exists() and meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            cached_text = html_path.read_text(encoding="utf-8", errors="replace")
            fetched_at = datetime.fromisoformat(meta["fetched_at"])
            last_checked_at = datetime.fromisoformat(
                meta.get("last_checked_at", meta["fetched_at"])
            )
            if fetched_at.tzinfo is None:
                fetched_at = fetched_at.replace(tzinfo=UTC)
            if last_checked_at.tzinfo is None:
                last_checked_at = last_checked_at.replace(tzinfo=UTC)
            if meta.get("url") != url or meta.get("sha256") != _sha256(cached_text):
                raise ValueError("cache URL or SHA-256 does not match its metadata")
            cached = meta, cached_text, fetched_at, last_checked_at
        except (OSError, ValueError, KeyError, TypeError) as exc:
            if offline:
                raise RuntimeError(
                    f"no valid cached source page is available for offline use: {url}"
                ) from exc
            log.warning("ignoring invalid cached source page %s", html_path, exc_info=True)

    if cached is not None:
        meta, cached_text, fetched_at, last_checked_at = cached
        if offline or (
            not force
            and timedelta(0) <= datetime.now(UTC) - last_checked_at.astimezone(UTC) < cache_ttl
        ):
            return cached_text, meta["sha256"], fetched_at
        if not force:
            res = client.get(
                url,
                cached_text=cached_text,
                etag=meta.get("etag"),
                last_modified=meta.get("last_modified"),
            )
            now = datetime.now(UTC)
            if res.status == 304:
                meta["last_checked_at"] = now.isoformat()
                meta["status"] = res.status
                if res.etag:
                    meta["etag"] = res.etag
                if res.last_modified:
                    meta["last_modified"] = res.last_modified
                _atomic_write_text(
                    meta_path, json.dumps(meta, ensure_ascii=False)
                )
                return cached_text, meta["sha256"], fetched_at
            return _store_response(
                html_path,
                meta_path,
                url,
                res.text,
                res.status,
                res.etag,
                res.last_modified,
            )

    if offline:
        raise RuntimeError(f"no cached source page is available for offline use: {url}")

    res = client.get(url, conditional=False)
    return _store_response(
        html_path,
        meta_path,
        url,
        res.text,
        res.status,
        res.etag,
        res.last_modified,
    )


def _store_response(
    html_path: Path,
    meta_path: Path,
    url: str,
    text: str,
    status: int,
    etag: str | None,
    last_modified: str | None,
) -> tuple[str, str, datetime]:
    now = datetime.now(UTC)
    digest = _sha256(text)
    metadata = {
        "url": url,
        "sha256": digest,
        "fetched_at": now.isoformat(),
        "last_checked_at": now.isoformat(),
        "status": status,
        "etag": etag,
        "last_modified": last_modified,
    }
    _atomic_write_text(html_path, text)
    _atomic_write_text(meta_path, json.dumps(metadata, ensure_ascii=False))
    return text, digest, now


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    try:
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _append_manifest(cache_dir: Path, record: dict) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    with (cache_dir / "manifest.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _is_group_ledger_page(page: str) -> bool:
    """Does this page hold a specific group, or is it the generic index?

    cdep answers an unknown ``idg`` with the generic "Grupuri parlamentare"
    page (the group index), which carries no member tables. A real group page
    has a title naming the group and at least one member table.
    """
    title_match = re.search(r"(?is)<title>(.*?)</title>", page)
    title = title_match.group(1).strip() if title_match else ""
    if title and title.lower() in {"grupuri parlamentare", "parliamentary groups"}:
        return False
    if re.search(r"(?is)Grupul\s+parlamentar\s+\w", page):
        return True
    return bool(re.search(r"(?is)<th[^>]*>\s*(?:Nume|Func)", page))


def discover_group_ids(
    client: PoliteClient,
    chamber: str,
    legislature: str,
    known: set[str],
    *,
    cache_dir: Path | None = None,
    force: bool = False,
    offline: bool = False,
    cache_ttl: timedelta = DEFAULT_CACHE_TTL,
    max_extra: int = 12,
    tail_misses: int = 4,
) -> dict[str, str]:
    """Find group pages that the index does NOT list.

    The group index on cdep.ro omits some groups (the 2016-2020 Deputies
    index hides the ALDE group entirely, which silently removed 40 dated
    memberships and the switches that go with them). The ids are simply
    sequential integers per chamber and legislature, so the missing ones are
    found by probing the gaps around the known ids.

    Returns a mapping of idg -> cached page path for the discovered groups.
    """
    cache_dir = cache_dir or CACHE_ROOT
    known_nums = sorted({int(i) for i in known if i.isdigit()})
    if not known_nums:
        return {}
    candidates: set[int] = set()
    for n in known_nums:
        for offset in range(1, max_extra + 1):
            candidate = n + offset
            if candidate not in known_nums:
                candidates.add(candidate)
    candidates.update(range(0, max(known_nums) + 1))
    candidates = {c for c in candidates if str(c) not in known}

    found: dict[str, str] = {}
    misses_in_a_row = 0
    for idg in sorted(candidates):
        if str(idg) in known:
            continue
        url = group_ledger_url(chamber, legislature, str(idg))
        path = cache_dir / chamber / legislature / f"group_{idg}.html"
        try:
            page, _digest, _fetched = fetch_cached(
                client, url, path, force=force, offline=offline, cache_ttl=cache_ttl
            )
        except requests.HTTPError as exc:
            if exc.response is None or exc.response.status_code not in {404, 410}:
                raise
            log.info("group probe returned %s for %s", exc.response.status_code, url)
            misses_in_a_row += 1
            continue
        if _is_group_ledger_page(page):
            found[str(idg)] = url
            misses_in_a_row = 0
        else:
            misses_in_a_row += 1
            # Stop once we are clearly past the end of the id space.
            if misses_in_a_row >= tail_misses and idg > max(known_nums):
                break
    if found:
        log.info(
            "%s %s: index lists %d groups, probing found %d more",
            chamber,
            legislature,
            len(known),
            len(found),
        )
    return found


def collect_roster(
    client: PoliteClient,
    chamber: str,
    legislature: str,
    *,
    cache_dir: Path | None = None,
    force: bool = False,
    offline: bool = False,
    cache_ttl: timedelta = DEFAULT_CACHE_TTL,
) -> Roster:
    """Fetch and parse the alphabetical roster of one legislature.

    The roster is a second view of the same source data as the group ledgers.
    Comparing the two is how we prove that no member was dropped.
    """
    cache_dir = cache_dir or CACHE_ROOT
    url = roster_url(chamber, legislature)
    page, digest, fetched = fetch_cached(
        client,
        url,
        cache_dir / chamber / legislature / "roster.html",
        force=force,
        offline=offline,
        cache_ttl=cache_ttl,
    )
    _append_manifest(
        cache_dir,
        {
            "kind": "roster",
            "chamber": chamber,
            "legislature": legislature,
            "url": url,
            "sha256": digest,
            "fetched_at": fetched.isoformat(),
        },
    )
    roster = parse_roster(page, chamber=chamber, legislature=legislature, source_url=url)
    log.info(
        "%s %s roster: current=%d former=%d",
        chamber,
        legislature,
        len(roster.current),
        len(roster.former),
    )
    return roster


def collect_legislature(
    client: PoliteClient,
    chamber: str,
    legislature: str,
    *,
    cache_dir: Path | None = None,
    force: bool = False,
    offline: bool = False,
    cache_ttl: timedelta = DEFAULT_CACHE_TTL,
    discover: bool = True,
) -> list[LedgerRecord]:
    """Fetch the group index and every group ledger for one chamber/legislature."""
    cache_dir = cache_dir or CACHE_ROOT
    out: list[LedgerRecord] = []
    list_url = group_list_url(chamber, legislature)
    html, digest, fetched = fetch_cached(
        client,
        list_url,
        cache_dir / chamber / legislature / "list.html",
        force=force,
        offline=offline,
        cache_ttl=cache_ttl,
    )
    _append_manifest(
        cache_dir,
        {
            "kind": "group_list",
            "chamber": chamber,
            "legislature": legislature,
            "url": list_url,
            "sha256": digest,
            "fetched_at": fetched.isoformat(),
        },
    )
    items = parse_group_list(html)
    if not items:
        log.warning("no groups parsed for %s %s (url=%s)", chamber, legislature, list_url)

    # The index is not authoritative: probe for the groups it omits.
    extra: dict[str, str] = {}
    if discover:
        extra = discover_group_ids(
            client,
            chamber,
            legislature,
            {item.idg for item in items},
            cache_dir=cache_dir,
            force=force,
            offline=offline,
            cache_ttl=cache_ttl,
        )

    for item in items:
        out.append(
            _fetch_ledger(
                client,
                chamber,
                legislature,
                item.idg,
                name=item.name,
                short_name=item.short_name,
                cache_dir=cache_dir,
                force=force,
                offline=offline,
                cache_ttl=cache_ttl,
            )
        )

    for idg, url in sorted(extra.items(), key=lambda kv: int(kv[0])):
        record = _fetch_ledger(
            client,
            chamber,
            legislature,
            idg,
            name=None,
            short_name=None,
            cache_dir=cache_dir,
            force=force,
            url=url,
            offline=offline,
            cache_ttl=cache_ttl,
        )
        if record is not None:
            out.append(record)
    return out


def _fetch_ledger(
    client: PoliteClient,
    chamber: str,
    legislature: str,
    idg: str,
    *,
    name: str | None,
    short_name: str | None,
    cache_dir: Path,
    force: bool,
    url: str | None = None,
    offline: bool = False,
    cache_ttl: timedelta = DEFAULT_CACHE_TTL,
) -> LedgerRecord | None:
    """Fetch and parse one group ledger page."""
    url = url or group_ledger_url(chamber, legislature, idg)
    page, page_digest, page_fetched = fetch_cached(
        client,
        url,
        cache_dir / chamber / legislature / f"group_{idg}.html",
        force=force,
        offline=offline,
        cache_ttl=cache_ttl,
    )
    _append_manifest(
        cache_dir,
        {
            "kind": "group_ledger",
            "chamber": chamber,
            "legislature": legislature,
            "idg": idg,
            "url": url,
            "sha256": page_digest,
            "fetched_at": page_fetched.isoformat(),
        },
    )
    ledger = parse_group_ledger(page, chamber=chamber, legislature=legislature, source_url=url)
    # Some group pages carry no header of their own (the 2016 PMP page).
    # The group index is the authoritative sibling listing, so use it.
    if not ledger.meta.name or ledger.meta.name == "Unknown":
        ledger.meta.name = name or ledger.meta.name
    if not ledger.meta.short_name:
        ledger.meta.short_name = short_name
    log.info(
        "%s %s idg=%s: current=%d former=%d name_only=%d",
        chamber,
        legislature,
        idg,
        len(ledger.current),
        len(ledger.former),
        len(ledger.name_only),
    )
    return LedgerRecord(
        chamber=chamber,
        legislature=legislature,
        idg=idg,
        url=url,
        sha256=page_digest,
        ledger=ledger,
        fetched_at=page_fetched,
    )


def mandates_in_ledgers(ledgers: list[LedgerRecord]) -> set[MandateRef]:
    """Every (chamber, legislature, idm) that appears in a group ledger."""
    found: set[MandateRef] = set()
    for rec in ledgers:
        rows = rec.ledger.current + rec.ledger.former + rec.ledger.name_only
        for row in rows:
            if row.idm:
                found.add(MandateRef(rec.chamber, rec.legislature, row.idm))
    return found


def collect_profiles(
    client: PoliteClient,
    mandates: set[MandateRef],
    *,
    cache_dir: Path | None = None,
    force: bool = False,
    offline: bool = False,
    cache_ttl_by_legislature: dict[str, timedelta] | None = None,
    progress_every: int = 25,
) -> dict[MandateRef, ProfileRecord]:
    """Fetch one MP profile per mandate and return the parsed records.

    The profile's "Mandate parlamentar" block links all of a person's mandates,
    so a single fetch can resolve many mandates at once; the caller still
    fetches per mandate here because it cannot know the links beforehand.

    With ``offline=True`` only already-cached profiles are used and nothing is
    requested: that rebuilds the database from the archive without touching
    the official site.
    """
    cache_dir = cache_dir or CACHE_ROOT
    out: dict[MandateRef, ProfileRecord] = {}
    ordered = sorted(mandates, key=lambda m: (m.legislature, m.chamber, m.idm))
    for i, mandate in enumerate(ordered, 1):
        url = profile_url(mandate.chamber, mandate.legislature, mandate.idm)
        path = cache_dir / mandate.chamber / mandate.legislature / f"profile_{mandate.idm}.html"
        if offline and not path.exists():
            out[mandate] = ProfileRecord(mandate, url, None, None, error="not cached")
            continue
        try:
            cache_ttl = (cache_ttl_by_legislature or {}).get(
                mandate.legislature, DEFAULT_CACHE_TTL
            )
            page, digest, fetched = fetch_cached(
                client,
                url,
                path,
                force=force,
                offline=offline,
                cache_ttl=cache_ttl,
            )
        except Exception as exc:  # noqa: BLE001 - one bad profile must not stop the run
            log.warning("profile fetch failed %s: %s", url, exc)
            out[mandate] = ProfileRecord(mandate, url, None, None, error=str(exc))
            continue
        _append_manifest(
            cache_dir,
            {
                "kind": "profile",
                "chamber": mandate.chamber,
                "legislature": mandate.legislature,
                "idm": mandate.idm,
                "url": url,
                "sha256": digest,
                "fetched_at": fetched.isoformat(),
            },
        )
        try:
            profile = parse_deputy_profile(
                page,
                idm=mandate.idm,
                legislature=mandate.legislature,
                chamber=mandate.chamber,
                profile_url=url,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("profile parse failed %s: %s", url, exc)
            out[mandate] = ProfileRecord(mandate, url, digest, None, error=str(exc))
            continue
        out[mandate] = ProfileRecord(mandate, url, digest, profile)
        if i % progress_every == 0:
            log.info("profiles %d/%d", i, len(ordered))
    return out


def cluster_mandates(
    profiles: dict[MandateRef, ProfileRecord],
    *,
    extra: set[MandateRef] | None = None,
) -> dict[MandateRef, str]:
    """Resolve mandates to stable persons using the profile mandate graph.

    ``idm`` is per-mandate, so the same MP appears under a different id in each
    legislature. The profile links every mandate of a person, so those links
    form the identity graph. Mandates with no profile stay isolated: they are
    never merged by name (that is what created cross-chamber false positives).
    """
    uf = _Union()
    all_mandates: set[MandateRef] = set(extra or ())
    for mandate, record in profiles.items():
        all_mandates.add(mandate)
        if record.profile is None:
            continue
        for other in record.profile.mandates:
            all_mandates.add(other)
            uf.union(mandate.key, other.key)

    clusters: dict[MandateRef, str] = {}
    for mandate in all_mandates:
        root = uf.find(mandate.key)
        clusters[mandate] = f"cdep-person:{root}"
    return clusters


def build_corpus(
    client: PoliteClient,
    chambers: list[str],
    legislatures: list[str],
    *,
    cache_dir: Path | None = None,
    force: bool = False,
    offline: bool = False,
    current_legislature: str | None = None,
    current_cache_ttl: timedelta = timedelta(days=1),
    historical_cache_ttl: timedelta = timedelta(days=30),
) -> Corpus:
    """Collect every group ledger, then every profile, then resolve identities."""
    cache_dir = cache_dir or CACHE_ROOT
    _atomic_write_text(cache_dir / "manifest.jsonl", "")
    latest_legislature = current_legislature or max(legislatures, default=None)
    cache_ttl_by_legislature = {
        legislature: (
            current_cache_ttl if legislature == latest_legislature else historical_cache_ttl
        )
        for legislature in legislatures
    }
    corpus = Corpus()
    for chamber in chambers:
        for legislature in legislatures:
            cache_ttl = cache_ttl_by_legislature[legislature]
            corpus.ledgers.extend(
                collect_legislature(
                    client,
                    chamber,
                    legislature,
                    cache_dir=cache_dir,
                    force=force,
                    offline=offline,
                    cache_ttl=cache_ttl,
                )
            )
            roster = collect_roster(
                client,
                chamber,
                legislature,
                cache_dir=cache_dir,
                force=force,
                offline=offline,
                cache_ttl=cache_ttl,
            )
            corpus.rosters.append(roster)
            # The index publishes the member count of every group it lists.
            corpus.index_counts[(chamber, legislature)] = collect_index_counts(
                cache_dir, chamber, legislature
            )
    corpus.profiles = collect_profiles(
        client,
        mandates_in_ledgers(corpus.ledgers),
        cache_dir=cache_dir,
        force=force,
        offline=offline,
        cache_ttl_by_legislature=cache_ttl_by_legislature,
    )
    corpus.clusters = cluster_mandates(corpus.profiles, extra=mandates_in_ledgers(corpus.ledgers))
    corpus.errors = [r.error for r in corpus.profiles.values() if r.error]
    return corpus


def collect_index_counts(cache_dir: Path | None, chamber: str, legislature: str) -> dict[str, int]:
    """The member count the group index publishes for every listed group."""
    cache_dir = cache_dir or CACHE_ROOT
    path = cache_dir / chamber / legislature / "list.html"
    if not path.exists():
        return {}
    try:
        items = parse_group_list(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:  # noqa: BLE001
        return {}
    return {item.idg: item.count for item in items if item.count is not None}
