"""Normalization: Romanian diacritics, person-name canonicalization, and
organization label canonicalization (group renames like POT→UPR).
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

# Romanian-specific letters that NFKD does not fully decompose.
_RO_MAP = str.maketrans(
    {
        "ă": "a",
        "â": "a",
        "î": "i",
        "ș": "s",
        "ț": "t",
        "ş": "s",
        "ţ": "t",  # cedilla variants (older encodings)
        "Ă": "a",
        "Â": "a",
        "Î": "i",
        "Ș": "s",
        "Ț": "t",
        "Ş": "s",
        "Ţ": "t",
    }
)


def strip_diacritics(s: str) -> str:
    s = s.translate(_RO_MAP)
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def normalize_name(name: str) -> str:
    """Canonical key for a person name: no diacritics, lowercase, single
    spaces, hyphens→space. Order is preserved as given (we do not guess
    surname/given order); blocking uses the whole normalized string.
    """
    s = strip_diacritics(name).lower()
    s = s.replace("-", " ").replace(".", " ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def name_tokens(name: str) -> set[str]:
    return set(normalize_name(name).split())


def name_sort_key(name: str) -> str:
    """A order-insensitive key (sorted tokens) so 'Popescu Ion' and
    'Ion Popescu' block together. Used only as a candidate signal, never as
    the sole merge criterion.
    """
    return " ".join(sorted(name_tokens(name)))


# --- Organization canonicalization ---------------------------------------
# Group short labels that refer to the same organization across renames or
# spelling variants. Key = canonical short name. This is reference data; the
# authoritative founding/rename dates come from the official ledger.
_GROUP_ALIASES: dict[str, str] = {
    "pot": "UPR",  # Partidul Oamenilor Tineri → Uniunea Populară Română (2026)
    "upr": "UPR",
    "psd": "PSD",
    "pnl": "PNL",
    "usr": "USR",
    "aur": "AUR",
    "udmr": "UDMR",
    "sos": "SOS",
    "sos romania": "SOS",
    "minoritati": "MINORITATI",
    "minorităţi": "MINORITATI",
    "neafiliati": "NEAFILIATI",
    "neafiliați": "NEAFILIATI",
    # The chamber publishes the same bucket with the singular in some rows
    # ("neafiliat"), and the two must not become two different groups.
    "neafiliat": "NEAFILIATI",
}


def normalize_org_label(label: str) -> str:
    s = strip_diacritics(label).lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _load_group_labels() -> dict[str, str]:
    """Load the reference table of official group titles -> canonical short names.

    The keys are the titles published by cdep.ro for every group in every
    legislature and both chambers; the values are the public acronyms. This is
    reference data, not something inferred from the scraped rows.
    """
    path = Path(__file__).resolve().parent.parent / "data" / "reference" / "group_labels.json"
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        normalize_org_label(k): v
        for k, v in raw.items()
        if not k.startswith("_") and isinstance(v, str)
    }


_GROUP_LABELS: dict[str, str] | None = None


def canonical_group_short(label: str) -> str | None:
    """Map a group label to its canonical short name, or None if unknown.

    Resolution order:
      1. the reference table of official group titles (data/reference/group_labels.json);
      2. the small alias table for acronyms and spelling variants;
      3. an acronym that is already the label itself.
    """
    global _GROUP_LABELS
    if _GROUP_LABELS is None:
        _GROUP_LABELS = _load_group_labels()

    norm = normalize_org_label(label)
    if not norm:
        return None

    known = _GROUP_LABELS.get(norm)
    if known:
        return known

    # Direct alias hit.
    if norm in _GROUP_ALIASES:
        return _GROUP_ALIASES[norm]
    # Try the last token (acronym) after stripping wrapper words.
    tokens = norm.split()
    for t in reversed(tokens):
        if t in _GROUP_ALIASES:
            return _GROUP_ALIASES[t]
    # Already an acronym-like label (short, no spaces) -> uppercase it.
    if len(norm) <= 6 and norm.isalnum():
        return norm.upper()
    return None
