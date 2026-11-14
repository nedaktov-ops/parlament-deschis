import json
from pathlib import Path

import pytest

from pipeline.normalize import canonical_group_short

LABELS = Path(__file__).resolve().parents[1] / "data" / "reference" / "group_labels.json"


def test_every_official_group_title_maps_to_its_acronym():
    raw = json.loads(LABELS.read_text(encoding="utf-8"))
    official_titles = {
        title: acronym for title, acronym in raw.items() if not title.startswith("_")
    }

    assert official_titles
    for title, acronym in official_titles.items():
        assert canonical_group_short(title) == acronym, title


@pytest.mark.parametrize(
    ("title", "acronym"),
    [
        ("Grupul parlamentar al Partidului Mişcarea Populară", "PMP"),
        ("Grupul parlamentar PRO România", "PRO"),
        ("Membri Senatori neafiliaţi Detalii grup parlamentar", "NEAFILIATI"),
    ],
)
def test_documented_official_titles_map_to_acronyms(title, acronym):
    assert canonical_group_short(title) == acronym


def test_unknown_label_has_no_canonical_short_name():
    assert canonical_group_short("Grupul parlamentar al Partidului Inventat") is None
    assert canonical_group_short("") is None
