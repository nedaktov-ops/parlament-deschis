"""Asset declaration extraction from PDF using tabula-py."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import tabula

from pipeline.db import AssetDeclaration, Person, get_session

log = logging.getLogger("parlament.assets")

ASSETS_DIR = Path("data/assets")


@dataclass
class AssetRow:
    person_name: str
    asset_type: str
    value_ron: float | None
    description: str
    year: int
    source_url: str


def extract_assets_from_pdf(pdf_path: Path, year: int, source_url: str) -> list[AssetRow]:
    """Extract asset tables from a PDF declaration."""
    try:
        # Read all tables from PDF
        tables = tabula.read_pdf(str(pdf_path), pages="all", multiple_tables=True)
        log.info(f"Extracted {len(tables)} tables from {pdf_path}")
    except Exception as e:
        log.error(f"Failed to extract tables from {pdf_path}: {e}")
        return []

    assets = []
    for i, table in enumerate(tables):
        # Try to identify asset tables (heuristic: look for columns with "valoare", "suma", "ron", etc.)
        cols = [str(c).lower() for c in table.columns]
        if any(
            kw in " ".join(cols)
            for kw in ["valoare", "suma", "ron", "euro", "asset", "bun", "imobil"]
        ):
            log.debug(f"Table {i} looks like asset table: {cols}")
            # Normalize column names
            table.columns = [str(c).strip().lower() for c in table.columns]

            # Try to find name, asset type, value columns
            name_col = next(
                (
                    c
                    for c in table.columns
                    if any(kw in c for kw in ["nume", "prenume", "declarant", "persoana"])
                ),
                None,
            )
            type_col = next(
                (
                    c
                    for c in table.columns
                    if any(kw in c for kw in ["tip", "categorie", "bun", "asset"])
                ),
                None,
            )
            value_col = next(
                (
                    c
                    for c in table.columns
                    if any(kw in c for kw in ["valoare", "suma", "val", "ron", "euro"])
                ),
                None,
            )
            desc_col = next(
                (
                    c
                    for c in table.columns
                    if any(kw in c for kw in ["descriere", "detalii", "observatii", "localizare"])
                ),
                None,
            )

            if not name_col or not value_col:
                log.debug(f"Table {i} missing required columns, skipping")
                continue

            for _, row in table.iterrows():
                try:
                    name = str(row.get(name_col, "")).strip()
                    if not name or name.lower() in ("nan", "total", "subtotal"):
                        continue

                    asset_type = str(row.get(type_col, "")).strip() if type_col else "unspecified"
                    description = str(row.get(desc_col, "")).strip() if desc_col else ""

                    # Parse value
                    value_str = str(row.get(value_col, "")).strip()
                    value_ron = None
                    if value_str and value_str.lower() not in ("nan", "-", ""):
                        # Remove currency symbols, commas, spaces
                        import re

                        cleaned = re.sub(r"[^\d.,\-]", "", value_str)
                        cleaned = cleaned.replace(".", "").replace(",", ".")
                        try:
                            value_ron = float(cleaned)
                        except ValueError:
                            pass

                    assets.append(
                        AssetRow(
                            person_name=name,
                            asset_type=asset_type,
                            value_ron=value_ron,
                            description=description,
                            year=year,
                            source_url=source_url,
                        )
                    )
                except Exception as e:
                    log.warning(f"Failed to parse row in table {i}: {e}")
                    continue

    return assets


def match_person(session, name: str, year: int) -> str | None:
    """Try to match a person by name and year (legislature)."""
    from sqlalchemy import and_, select

    # Normalize name
    from pipeline.normalize import normalize_name

    norm_name = normalize_name(name)

    # Find persons with similar names in the relevant legislature
    # This is a simplified matching - in production, use the full resolver
    stmt = select(Person).where(
        and_(
            Person.normalized_name.like(f"%{norm_name}%"),
        )
    )
    # This is a simplified implementation
    return None


def import_assets(session, assets: list[AssetRow], year: int) -> int:
    """Import asset declarations into database."""
    imported = 0
    for asset in assets:
        # Try to match person
        person_id = match_person(session, asset.person_name, year)
        if not person_id:
            log.warning(f"Could not match person: {asset.person_name}")
            continue

        # Check if already exists
        from sqlalchemy import and_, select

        existing = session.scalars(
            select(AssetDeclaration).where(
                and_(
                    AssetDeclaration.person_id == person_id,
                    AssetDeclaration.year == year,
                    AssetDeclaration.asset_type == asset.asset_type,
                    AssetDeclaration.value_ron == asset.value_ron,
                )
            )
        ).first()

        if existing:
            continue

        decl = AssetDeclaration(
            person_id=person_id,
            year=year,
            asset_type=asset.asset_type,
            value_ron=asset.value_ron,
            description=asset.description,
            source_url=asset.source_url,
        )
        session.add(decl)
        imported += 1

    session.flush()
    return imported


def process_assets_directory(year: int, dry_run: bool = True) -> dict:
    """Process all PDFs in data/assets/{year}/ directory."""
    year_dir = ASSETS_DIR / str(year)
    if not year_dir.exists():
        return {"error": f"Directory {year_dir} does not exist"}

    pdf_files = list(year_dir.glob("*.pdf"))
    log.info(f"Found {len(pdf_files)} PDF files for {year}")

    session = get_session()
    total_imported = 0
    total_assets = 0

    try:
        for pdf_path in pdf_files:
            log.info(f"Processing {pdf_path.name}")
            assets = extract_assets_from_pdf(pdf_path, year, f"file://{pdf_path}")
            total_assets += len(assets)

            if not dry_run and assets:
                imported = import_assets(session, assets, year)
                total_imported += imported
                session.commit()

        return {
            "year": year,
            "files_processed": len(pdf_files),
            "assets_extracted": total_assets,
            "imported": total_imported if not dry_run else 0,
        }
    finally:
        session.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Extract asset declarations from PDFs")
    parser.add_argument("--year", type=int, required=True, help="Year to process")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Don't write to DB")
    parser.add_argument("--apply", action="store_false", dest="dry_run", help="Write to DB")
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=args.log_level, format="%(levelname)s %(name)s: %(message)s")

    print(f"Processing asset declarations for {args.year} (dry_run={args.dry_run})")
    result = process_assets_directory(args.year, dry_run=args.dry_run)
    print(f"Result: {json.dumps(result, indent=2)}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
