# Licențe / Licensing

Parlament Deschis separates the license of the **software** from the license of the
**generated data**.

| Material | License | Canonical text |
| --- | --- | --- |
| Source code (`pipeline/`, `backend/`, `frontend/`, tests, scripts) | **AGPL-3.0-or-later** | [`../../LICENSE`](../../LICENSE) · <https://www.gnu.org/licenses/agpl-3.0.txt> |
| Generated data and exports (Popolo JSON, CSV, coverage matrix, derived events) | **CC-BY-4.0** | [`CC-BY-4.0.txt`](CC-BY-4.0.txt) · <https://creativecommons.org/licenses/by/4.0/legalcode> |
| Archived source pages in `data/snapshots/` | Copyright remains with the respective chamber | See “Archived source pages” below. |
| Wikidata facts used for enrichment | CC0 1.0 (Wikidata) | <https://www.wikidata.org/wiki/Wikidata:Licensing> |

This file is a summary, not legal advice. The canonical license texts control.

---

## 1. Code — AGPL-3.0-or-later

The software is free software: you can redistribute it and/or modify it under the terms of
the GNU Affero General Public License as published by the Free Software Foundation, either
version 3 of the License, or (at your option) any later version.

The full text is committed at the repository root as [`LICENSE`](../../LICENSE). It was
fetched from <https://www.gnu.org/licenses/agpl-3.0.txt>.

The AGPL's network-use clause matters for a hosted deployment: if you run a modified
version as a network service, users interacting with it remotely must be offered the
corresponding source. Keep the license notices and make the source available.

`pyproject.toml` declares `license = { text = "AGPL-3.0-or-later" }`. If you add a
dependency, check that its license is compatible with AGPL-3.0-or-later before merging.

---

## 2. Data — CC-BY-4.0

Generated data is licensed under the **Creative Commons Attribution 4.0 International**
license. You are free to share and adapt the data for any purpose, including commercially,
provided you give appropriate credit, link to the license, and indicate if changes were
made.

The full legal code is committed at [`CC-BY-4.0.txt`](CC-BY-4.0.txt). It was fetched from
<https://creativecommons.org/licenses/by/4.0/legalcode.txt>.

### Required attribution

Use the following attribution (or an equivalent that preserves the same information):

> **Parlament Deschis** — Romanian Parliament transparency tracker.
> Data licensed under CC-BY-4.0: <https://creativecommons.org/licenses/by/4.0/>.
> Project: <https://github.com/parlament-deschis>.
> Facts sourced from the official publications of the Camera Deputaților and Senat.

In Romanian:

> **Parlament Deschis** — tracker de transparență pentru Parlamentul României.
> Date sub licența CC-BY-4.0: <https://creativecommons.org/licenses/by/4.0/>.
> Proiect: <https://github.com/parlament-deschis>.
> Fapte extrase din publicațiile oficiale ale Camerei Deputaților și Senatului.

### What to preserve

- The attribution above.
- The `source_url` and `confidence` fields where present, so readers can verify a fact.
- A note if you modified, merged, or filtered the data.
- The `meta` block in `popolo.json`, which records the licenses, generator, scope, and
  counts.

CC-BY-4.0 does **not** grant rights in the underlying source pages beyond what the source
site permits. Attributing Parlament Deschis is not a substitute for respecting the
chambers' terms.

---

## 3. Archived source pages

`data/snapshots/` contains byte-for-byte captures of official pages, stored by SHA-256
content hash. They exist for one reason: to let a reader verify a cited fact after the live
page changes or disappears.

- **Copyright remains with the respective chamber** (Camera Deputaților / Senat) and the
  original authors. The project does not claim ownership of the page content.
- Snapshots are **evidence**, not a redistribution of the chamber website. Do not republish
  full archived pages as a standalone dataset.
- Citations should point to the **original URL** first, with the archived copy as a
  verification aid.
- The pipeline honors `robots.txt`, identifies itself, paces requests, and stops on a
  CAPTCHA or challenge. It does not bypass access controls.
- If a rights holder asks for an archived copy to be removed, remove the snapshot and keep
  the original source URL as the citation. Do not silently rewrite the historical record.
- If a source's terms change and prohibit archival, stop ingestion for that source and
  update [`../../docs/METHODOLOGY.md`](../../docs/METHODOLOGY.md).

Snapshots are gitignored and are not part of the distributed repository; a deployment that
publishes them is responsible for complying with the source site's terms.

---

## 4. Official source sites

The primary sources are the official publications of the Romanian Parliament:

| Site | Content used | Terms / access |
| --- | --- | --- |
| <https://www.cdep.ro> | Parliamentary group index and dated member ledgers (`structura2015.gp`) | Official public pages. The pipeline honors `robots.txt`, uses an identifying User-Agent, paces requests, and stops on challenges. |
| <https://www.senat.ro> | Senator profiles (`FisaSenator.aspx`), group rosters (`ComponentaGrupuri.aspx`), sitemap | Same rules. |

The pipeline's compliance behavior is implemented in `pipeline/sources/client.py` and
documented in the README and methodology:

- `robots.txt` is checked before fetching; a disallowed URL raises and stops that source.
- At most one request per second per host; the default pause is 2.5 seconds.
- Conditional GET with `ETag` / `Last-Modified`; unchanged content is skipped.
- `429` waits for `Retry-After`; `5xx` uses exponential backoff.
- CAPTCHA/challenge pages are a hard stop — never bypassed.

If you reuse data from this project, you are responsible for checking the current terms of
the original sites as well.

---

## 5. Third-party data

- **Wikidata** is used for conservative enrichment (birth dates, QIDs). Wikidata data is
  CC0 1.0; the project records the QID so the provenance is visible. Wikidata is never the
  primary source for a membership or a tenure date.
- **Group colors and RO/EN display names** in `data/reference/groups.json` are project
  reference data, contributed under the same CC-BY-4.0 terms as the generated data.
- **Legislature dates** in `data/reference/legislatures.json` are reference data derived
  from public term boundaries; they are contributed under CC-BY-4.0.

---

## 6. Files in this directory

| File | Purpose |
| --- | --- |
| `README.md` | This licensing summary. |
| `CC-BY-4.0.txt` | Canonical Creative Commons Attribution 4.0 International legal code (UTF-8). |

The AGPL-3.0 text lives at the repository root in [`LICENSE`](../../LICENSE) so that GitHub
and other tools detect it automatically.

---

## 7. Questions

If a proposed use is unclear — especially a bulk redistribution of snapshots, a commercial
product that incorporates the data, or a modification that changes the meaning of a fact —
open an issue in the project repository before publishing. When in doubt, cite the source,
keep the licenses, and do not imply that Parlament Deschis or the chambers endorse your
use.
