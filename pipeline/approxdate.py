"""Romanian approximate-date parsing.

Official chamber pages express dates at varying precision: a full day
("15 iun. 2026", "01.12.2024"), a month ("mai 2026"), or a year ("2024").
We never fabricate a day that the source did not publish. Instead an
ApproxDate carries an [earliest, latest] window plus the original string and
a precision tag (YYYY / YYYY-MM / YYYY-MM-DD), following the parlparse model.
"""

from __future__ import annotations

import calendar
import re
import unicodedata
from dataclasses import dataclass
from datetime import date

# Romanian month names and common abbreviations, normalized (no diacritics,
# lowercase). Maps to month number 1..12.
_MONTHS: dict[str, int] = {}
_FULL = {
    1: ["ianuarie"],
    2: ["februarie"],
    3: ["martie"],
    4: ["aprilie"],
    5: ["mai"],
    6: ["iunie"],
    7: ["iulie"],
    8: ["august"],
    9: ["septembrie"],
    10: ["octombrie"],
    11: ["noiembrie"],
    12: ["decembrie"],
}
_ABBR = {
    1: ["ian"],
    2: ["feb"],
    3: ["mar", "mart"],
    4: ["apr"],
    5: ["mai"],
    6: ["iun"],
    7: ["iul"],
    8: ["aug"],
    9: ["sep", "sept"],
    10: ["oct"],
    11: ["nov", "noi"],
    12: ["dec"],
}
for _num, _names in _FULL.items():
    for _n in _names:
        _MONTHS[_n] = _num
for _num, _names in _ABBR.items():
    for _n in _names:
        _MONTHS[_n] = _num


def _strip_diacritics(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def _norm(s: str) -> str:
    return _strip_diacritics(s).lower().strip()


# Numeric formats: 01.12.2024 / 1.12.2024 / 01/12/2024 / 2024-12-01
_NUMERIC_DMY = re.compile(r"^(\d{1,2})[./](\d{1,2})[./](\d{4})$")
_NUMERIC_YMD = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
# Textual: "15 iun. 2026", "1 septembrie 2024", "15 iunie 2026"
_TEXT_DMY = re.compile(r"^(\d{1,2})\s+([a-z.]+)\s+(\d{4})$")
# Month-year: "mai 2026", "septembrie 2024"
_TEXT_MY = re.compile(r"^([a-z.]+)\s+(\d{4})$")
# Year only
_YEAR = re.compile(r"^(\d{4})$")

# Leading/trailing connective words seen on the pages (longest-first).
_LEAD = re.compile(
    r"^(de la data de|de la data|incepand cu|incepand din|de la|din|data de|data)\s+", re.I
)
_TRAIL = re.compile(r"\s*(până|pana|pina).*$", re.I)


@dataclass(frozen=True)
class ApproxDate:
    earliest: date
    latest: date
    precision: str  # "YYYY" | "YYYY-MM" | "YYYY-MM-DD"
    source_string: str

    @property
    def is_exact(self) -> bool:
        return self.earliest == self.latest

    def iso(self) -> str:
        """Best single representative date (the earliest bound)."""
        return self.earliest.isoformat()

    def overlaps(self, other: ApproxDate) -> bool:
        return self.earliest <= other.latest and other.earliest <= self.latest

    def contains(self, d: date) -> bool:
        return self.earliest <= d <= self.latest

    def to_dict(self) -> dict:
        return {
            "earliest": self.earliest.isoformat(),
            "latest": self.latest.isoformat(),
            "precision": self.precision,
            "source_string": self.source_string,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ApproxDate:
        return cls(
            earliest=date.fromisoformat(d["earliest"]),
            latest=date.fromisoformat(d["latest"]),
            precision=d["precision"],
            source_string=d.get("source_string", ""),
        )


def _month_token(tok: str) -> int | None:
    t = _norm(tok).rstrip(".")
    return _MONTHS.get(t)


def _mk(y: int, m: int, d: int, src: str) -> ApproxDate:
    day = date(y, m, d)
    return ApproxDate(day, day, day.isoformat(), src)


def parse_ro_date(raw: str | None) -> ApproxDate | None:
    """Parse a single Romanian date expression into an ApproxDate.

    Returns None when the input carries no recognizable date. Handles the
    connective prefixes ("din", "de la data de") and truncates trailing
    "până în ..." ranges (use parse_ro_range for both endpoints).
    """
    if not raw:
        return None
    src = raw.strip()
    s = src
    while True:
        stripped = _LEAD.sub("", s).strip()
        if stripped == s:
            break
        s = stripped
    s = _TRAIL.sub("", s).strip()
    s = s.rstrip(".").strip()
    if not s:
        return None
    low = _norm(s)

    m = _NUMERIC_DMY.match(low)
    if m:
        d, mo, y = int(m[1]), int(m[2]), int(m[3])
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return _mk(y, mo, d, src)
    m = _NUMERIC_YMD.match(low)
    if m:
        y, mo, d = int(m[1]), int(m[2]), int(m[3])
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return _mk(y, mo, d, src)
    m = _TEXT_DMY.match(low)
    if m:
        d, tok, y = int(m[1]), m[2], int(m[3])
        mo = _month_token(tok)
        if mo and 1 <= d <= 31:
            return _mk(y, mo, d, src)
    m = _TEXT_MY.match(low)
    if m:
        tok, y = m[1], int(m[2])
        mo = _month_token(tok)
        if mo:
            last = calendar.monthrange(y, mo)[1]
            return ApproxDate(date(y, mo, 1), date(y, mo, last), f"{y:04d}-{mo:02d}", src)
    m = _YEAR.match(low)
    if m:
        y = int(m[1])
        return ApproxDate(date(y, 1, 1), date(y, 12, 31), f"{y:04d}", src)
    return None


# Range separators: "din X - până în Y", "X – Y", "X - Y", "X până în Y"
_RANGE_SPLIT = re.compile(r"\s*(?:[-–—]|până\s+în|pana\s+in|până|pana|->|→)\s*", re.I)


def parse_ro_range(raw: str | None) -> tuple[ApproxDate | None, ApproxDate | None]:
    """Parse a "from ... to ..." expression into (start, end) ApproxDates.

    A single date yields (date, None) meaning open-ended. "din X" alone is a
    start. Trailing "până în Y" gives the end. Never invents an endpoint.
    """
    if not raw:
        return None, None
    src = raw.strip()
    # Normalize the common "din X - până în Y" into two clean halves.
    work = _LEAD.sub("", src).strip()
    # Split on explicit range markers.
    parts = _RANGE_SPLIT.split(work)
    parts = [p.strip() for p in parts if p and p.strip()]
    if len(parts) >= 2:
        start = parse_ro_date(parts[0])
        end = parse_ro_date(parts[-1])
        return start, end
    # Single expression.
    single = parse_ro_date(work)
    return single, None


def parse_ro_date_or_none(raw: str | None) -> date | None:
    """Convenience: exact representative date or None."""
    ad = parse_ro_date(raw)
    return ad.earliest if ad else None
