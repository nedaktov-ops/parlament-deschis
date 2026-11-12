"""Normalization: Romanian diacritics, person-name canonicalization, and
organization label canonicalization (group renames like POT→UPR).
"""

from __future__ import annotations

import re
import unicodedata

# Romanian-specific letters that NFKD does not fully decompose.
_RO_MAP = str.maketrans(
    {
        "ă": "a", "â": "a", "î": "i", "ș": "s", "ț": "t",
        "ş": "s", "ţ": "t",  # cedilla variants (older encodings)
        "Ă": "a", "Â": "a", "Î": "i", "Ș": "s", "Ț": "t",
        "Ş": "s", "Ţ": "t",
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
    "pot": "UPR",       # Partidul Oamenilor Tineri → Uniunea Populară Română (2026)
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
}


def normalize_org_label(label: str) -> str:
    s = strip_diacritics(label).lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def canonical_group_short(label: str) -> str | None:
    """Map a group label to its canonical short name, or None if unknown.

    Handles the common 'Grupul parlamentar al X' / 'Grupul parlamentar X'
    wrappers by extracting the trailing acronym.
    """
    norm = normalize_org_label(label)
    # Direct alias hit.
    if norm in _GROUP_ALIASES:
        return _GROUP_ALIASES[norm]
    # Try the last token (acronym) after stripping wrapper words.
    tokens = norm.split()
    for t in reversed(tokens):
        if t in _GROUP_ALIASES:
            return _GROUP_ALIASES[t]
    return None