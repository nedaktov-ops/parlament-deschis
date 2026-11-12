"""Wikidata enrichment for Romanian MPs.

Uses Wikidata Reconciliation API for individual lookups + local cache.
Conservative: never fabricates data; only writes high-confidence matches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import requests
from rapidfuzz import fuzz

from .db import get_session
from .db import Person, PersonIdentifier

log = logging.getLogger("parlament.enrich")

CACHE_DB = Path("data/wikidata_cache.db")
RECONCILE_ENDPOINT = "https://wikidata-reconciliation.wmcloud.org/en/api"
USER_AGENT = "ParlamentDeschis/1.0 (+https://github.com/parlament-deschis; civic transparency)"
RATE_LIMIT_SEC = 0.5  # 2 req/sec (reconciliation API is faster)
AUTO_ACCEPT_THRESHOLD = 95.0
REVIEW_THRESHOLD = 80.0


@dataclass
class WikidataCandidate:
    qid: str
    label: str
    birth_date: Optional[date]
    party_label: Optional[str]
    chamber_label: Optional[str]
    score: float = 0.0
    raw: dict = None

    def to_dict(self):
        d = asdict(self)
        d['birth_date'] = self.birth_date.isoformat() if self.birth_date else None
        d['raw'] = self.raw
        return d

    @classmethod
    def from_dict(cls, d):
        d = dict(d)  # Make a copy
        birth_date = None
        if d.get('birth_date'):
            birth_date = date.fromisoformat(d['birth_date'])
        raw = d.pop('raw', None)
        d.pop('birth_date', None)  # Remove to avoid duplicate
        return cls(**d, birth_date=birth_date, raw=raw)


@dataclass
class EnrichmentResult:
    person_id: str
    action: str  # "auto_accept", "review", "reject", "cached", "error"
    candidate: Optional[WikidataCandidate] = None
    reason: str = ""


def init_cache_db() -> sqlite3.Connection:
    """Initialize local cache database."""
    CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reconcile_cache (
            person_key TEXT PRIMARY KEY,  -- name|birth_year|legislature|chamber
            candidates_json TEXT NOT NULL,
            scored_at REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entity_cache (
            qid TEXT PRIMARY KEY,
            entity_json TEXT NOT NULL,
            fetched_at REAL NOT NULL
        )
    """)
    conn.commit()
    return conn


def _person_key(name: str, birth_year: Optional[int], legislature: str, chamber: str) -> str:
    """Generate cache key for person."""
    return f"{name}|{birth_year or 'unknown'}|{legislature}|{chamber}"


def _legislature_dates(legislature: str) -> tuple[Optional[date], Optional[date]]:
    """Get legislature start/end dates from reference data."""
    ref_path = Path("data/reference/legislatures.json")
    if ref_path.exists():
        data = json.loads(ref_path.read_text(encoding="utf-8"))
        if legislature in data:
            leg = data[legislature]
            start = date.fromisoformat(leg["start"]) if leg["start"] else None
            end = date.fromisoformat(leg["end"]) if leg["end"] else None
            return start, end
    return None, None


def _fetch_entity(conn: sqlite3.Connection, qid: str) -> Optional[dict]:
    """Fetch full Wikidata entity with local caching."""
    cached = conn.execute(
        "SELECT entity_json, fetched_at FROM entity_cache WHERE qid = ?",
        (qid,)
    ).fetchone()

    if cached:
        entity_json, fetched_at = cached
        if time.time() - fetched_at < 30 * 24 * 3600:  # 30 days TTL
            return json.loads(entity_json)

    # Rate limiting
    time.sleep(RATE_LIMIT_SEC)

    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 429:
                wait = min(60 * (2 ** attempt), 300)
                log.warning("Entity fetch 429, waiting %ds", wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            entity = data.get("entities", {}).get(qid, {})
            conn.execute(
                "INSERT OR REPLACE INTO entity_cache VALUES (?, ?, ?)",
                (qid, json.dumps(entity), time.time())
            )
            conn.commit()
            return entity
        except requests.RequestException as e:
            log.warning("Entity fetch attempt %d failed for %s: %s", attempt + 1, qid, e)
            if attempt == 2:
                return None
            time.sleep(2 ** attempt)

    return None


def _reconcile_person(
    conn: sqlite3.Connection,
    name: str,
    birth_year: Optional[int],
    legislature: str,
    chamber: str
) -> list[WikidataCandidate]:
    """Reconcile a person via Wikidata Reconciliation API."""
    key = _person_key(name, birth_year, legislature, chamber)

    cached = conn.execute(
        "SELECT candidates_json FROM reconcile_cache WHERE person_key = ?",
        (key,)
    ).fetchone()

    if cached:
        candidates = [WikidataCandidate.from_dict(c) for c in json.loads(cached[0])]
        log.debug("Reconcile cache hit for %s", key)
        return candidates

    # Build reconciliation query
    query = {
        "query": name,
        "limit": 10,
        "type": "Q5"  # human
    }

    url = RECONCILE_ENDPOINT
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    params = {"queries": json.dumps({"q0": query})}

    time.sleep(RATE_LIMIT_SEC)

    try:
        # Use GET with queries parameter (correct format for this API)
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        log.warning("Reconciliation API failed: %s", e)
        # Retry once with longer timeout
        try:
            time.sleep(2)
            resp = requests.get(url, params=params, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e2:
            log.warning("Reconciliation API retry failed: %s", e2)
            return []

    candidates = []
    results = data.get("q0", {}).get("result", [])

    for r in results:
        qid = r.get("id", "").split("/")[-1]
        label = r.get("name", "")
        score = r.get("score", 0)

        # Fetch full entity for details
        entity = _fetch_entity(conn, qid)
        if not entity:
            continue

        # Extract birth date
        birth_date = None
        claims = entity.get("claims", {})
        if "P569" in claims:
            for claim in claims["P569"]:
                mainsnak = claim.get("mainsnak", {})
                datavalue = mainsnak.get("datavalue", {})
                if datavalue.get("type") == "time":
                    time_val = datavalue["value"]["time"]
                    try:
                        birth_date = datetime.strptime(time_val[1:11], "%Y-%m-%d").date()
                        break
                    except ValueError:
                        pass

        # Extract party (P102)
        party_label = None
        if "P102" in claims:
            for claim in claims["P102"]:
                mainsnak = claim.get("mainsnak", {})
                datavalue = mainsnak.get("datavalue", {})
                if datavalue.get("type") == "wikibase-entityid":
                    party_qid = datavalue["value"]["id"]
                    party_label = party_qid

        # Determine chamber from position held (P39)
        chamber_label = None
        if "P39" in claims:
            for claim in claims["P39"]:
                mainsnak = claim.get("mainsnak", {})
                datavalue = mainsnak.get("datavalue", {})
                if datavalue.get("type") == "wikibase-entityid":
                    pos_qid = datavalue["value"]["id"]
                    if pos_qid == "Q18635844":
                        chamber_label = "Chamber of Deputies"
                    elif pos_qid == "Q18635845":
                        chamber_label = "Senate"

        candidates.append(WikidataCandidate(
            qid=qid,
            label=label,
            birth_date=birth_date,
            party_label=party_label,
            chamber_label=chamber_label,
            score=float(score),
            raw={"entity": entity, "reconcile_result": r}
        ))

    # Cache results
    conn.execute(
        "INSERT OR REPLACE INTO reconcile_cache VALUES (?, ?, ?)",
        (key, json.dumps([c.to_dict() for c in candidates]), time.time())
    )
    conn.commit()

    return candidates


def _score_candidate(person: Person, candidate: WikidataCandidate, legislature: str, chamber: str) -> float:
    """Score a Wikidata candidate against a local person."""
    # Name similarity (primary)
    name_score = fuzz.token_sort_ratio(person.canonical_name, candidate.label)

    # Birth year match (strong signal)
    birth_bonus = 0
    if person.birth_date and candidate.birth_date:
        if person.birth_date.year == candidate.birth_date.year:
            birth_bonus = 20
        elif abs(person.birth_date.year - candidate.birth_date.year) <= 1:
            birth_bonus = 10
        else:
            birth_bonus = -30

    # Chamber match
    chamber_bonus = 0
    if candidate.chamber_label:
        if (chamber == "deputies" and "deput" in candidate.chamber_label.lower()) or \
           (chamber == "senate" and "senat" in candidate.chamber_label.lower()):
            chamber_bonus = 10
        else:
            chamber_bonus = -20

    return min(100.0, max(0.0, name_score + birth_bonus + chamber_bonus))


def enrich_person(
    session,
    person: Person,
    legislature: str,
    chamber: str,
    cache_conn: sqlite3.Connection,
    dry_run: bool = False
) -> EnrichmentResult:
    """Enrich a single person with Wikidata data."""
    birth_year = person.birth_date.year if person.birth_date else None
    candidates = _reconcile_person(cache_conn, person.canonical_name, birth_year, legislature, chamber)

    if not candidates:
        return EnrichmentResult(person.id, "reject", reason="no candidates from reconciliation")

    best = max(candidates, key=lambda c: c.score)

    if best.score >= AUTO_ACCEPT_THRESHOLD:
        if not dry_run:
            if not person.wikidata_qid:
                person.wikidata_qid = best.qid
            if not person.birth_date and best.birth_date:
                person.birth_date = best.birth_date
            session.flush()
        return EnrichmentResult(person.id, "auto_accept", best, f"score={best.score:.1f}")

    elif best.score >= REVIEW_THRESHOLD:
        if not dry_run:
            # Store in cache DB review table
            cache_conn.execute("""
                CREATE TABLE IF NOT EXISTS wikidata_review (
                    id TEXT PRIMARY KEY,
                    person_id TEXT NOT NULL,
                    candidate_qid TEXT NOT NULL,
                    candidate_label TEXT NOT NULL,
                    score REAL NOT NULL,
                    reason TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at REAL NOT NULL
                )
            """)
            import uuid
            cache_conn.execute("""
                INSERT INTO wikidata_review (id, person_id, candidate_qid, candidate_label, score, reason, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """, (str(uuid.uuid4()), person.id, best.qid, best.label, best.score,
                  f"Wikidata candidate: {best.label} ({best.qid})", time.time()))
            cache_conn.commit()
        return EnrichmentResult(person.id, "review", best, f"score={best.score:.1f}")

    else:
        return EnrichmentResult(person.id, "reject", best, f"best score={best.score:.1f} below threshold")


def run_enrichment(limit: Optional[int] = None, dry_run: bool = True, legislature: str = "2024") -> dict:
    """Run enrichment for all persons in a legislature."""
    session = get_session()
    cache_conn = init_cache_db()

    try:
        from sqlalchemy import select
        from .db import Membership

        stmt = select(Person).join(Membership).where(
            Membership.legislature == legislature
        ).distinct()

        if limit:
            stmt = stmt.limit(limit)

        persons = list(session.scalars(stmt))

        results = {"auto_accept": 0, "review": 0, "reject": 0, "error": 0, "details": []}

        for person in persons:
            chambers = {m.chamber for m in person.memberships if m.legislature == legislature}
            chamber = "deputies" if "deputies" in chambers else "senate"

            try:
                result = enrich_person(session, person, legislature, chamber, cache_conn, dry_run)
                results[result.action] += 1
                results["details"].append({
                    "person_id": person.id,
                    "name": person.canonical_name,
                    "action": result.action,
                    "reason": result.reason,
                    "candidate_qid": result.candidate.qid if result.candidate else None,
                    "candidate_score": result.candidate.score if result.candidate else None,
                })
            except Exception as e:
                log.exception("Enrichment failed for %s", person.canonical_name)
                results["error"] += 1
                results["details"].append({
                    "person_id": person.id,
                    "name": person.canonical_name,
                    "action": "error",
                    "reason": str(e),
                })

            if not dry_run:
                session.commit()

        return results

    finally:
        session.close()
        cache_conn.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Wikidata enrichment for Romanian MPs")
    parser.add_argument("--limit", type=int, help="Max persons to process")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Don't write changes")
    parser.add_argument("--apply", action="store_false", dest="dry_run", help="Write changes to DB")
    parser.add_argument("--legislature", default="2024", help="Legislature to enrich")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args(argv)

    logging.basicConfig(level=args.log_level, format="%(levelname)s %(name)s: %(message)s")

    print(f"Starting enrichment: legislature={args.legislature}, dry_run={args.dry_run}, limit={args.limit}")
    results = run_enrichment(limit=args.limit, dry_run=args.dry_run, legislature=args.legislature)

    print(f"\nResults:")
    print(f"  Auto-accept: {results['auto_accept']}")
    print(f"  Review queue: {results['review']}")
    print(f"  Rejected: {results['reject']}")
    print(f"  Errors: {results['error']}")

    if args.dry_run:
        print("\nDRY RUN - no changes written. Use --apply to persist.")
    else:
        print("\nChanges committed to database.")

    report_path = Path(f"data/enrichment_report_{args.legislature}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    report_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"Report saved to {report_path}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())