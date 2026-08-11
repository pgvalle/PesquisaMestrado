#!/usr/bin/env python3
"""Create a common-schema CSV from one database export."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.pipeline_lib import PipelineError, normalize_match_text, read_table, write_csv


NORMALIZED_COLUMNS = [
    "database",
    "source_row",
    "source_id",
    "title",
    "authors",
    "normalized_title",
    "normalized_authors",
    "year",
    "doi",
    "publication_title",
    "document_type",
    "url",
]


@dataclass(frozen=True)
class NormalizationSpec:
    key: str
    display_name: str
    input_filename: str
    columns: dict[str, str | None]


SPECS = {
    "scopus": NormalizationSpec(
        key="scopus",
        display_name="Scopus",
        input_filename="results.csv",
        columns={
            "source_id": "EID", "title": "Title", "authors": "Authors",
            "year": "Year", "doi": "DOI", "publication_title": "Source title",
            "document_type": "Document Type", "url": "Link",
        },
    ),
    "wos": NormalizationSpec(
        key="wos",
        display_name="Web of Science",
        input_filename="results.xls",
        columns={
            "source_id": "UT (Unique WOS ID)", "title": "Article Title", "authors": "Authors",
            "year": "Publication Year", "doi": "DOI Link", "publication_title": "Source Title",
            "document_type": "Document Type", "url": "Web of Science Record",
        },
    ),
    "ieee": NormalizationSpec(
        key="ieee",
        display_name="IEEE",
        input_filename="results.csv",
        columns={
            "source_id": None, "title": "Document Title", "authors": "Authors",
            "year": "Publication Year", "doi": "DOI", "publication_title": "Publication Title",
            "document_type": "Document Identifier", "url": "PDF Link",
        },
    ),
    "springer": NormalizationSpec(
        key="springer",
        display_name="Springer",
        input_filename="results.csv",
        columns={
            "source_id": None, "title": "Item Title", "authors": "Authors",
            "year": "Publication Year", "doi": "Item DOI", "publication_title": "Publication Title",
            "document_type": "Content Type", "url": "URL",
        },
    ),
}


_DOI_RE = re.compile(r"(?:https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/\S+)", re.IGNORECASE)


def normalize_doi(value: str) -> str:
    """Return a bare DOI when the export supplies a DOI URL."""
    value = (value or "").strip()
    match = _DOI_RE.search(value)
    return match.group(1).rstrip(".,;)") if match else value


def normalize_database(database: str, database_dir: Path | None = None) -> tuple[Path, int]:
    try:
        spec = SPECS[database]
    except KeyError as exc:
        raise PipelineError(f"Unknown database {database!r}") from exc

    directory = (database_dir or Path(__file__).resolve().parent.parent / "dbs" / database).resolve()
    input_path = directory / spec.input_filename
    output_path = directory / "normalized.csv"
    table = read_table(input_path)

    required = {column for column in spec.columns.values() if column}
    missing = sorted(required - set(table.fieldnames))
    if missing:
        raise PipelineError(f"{spec.display_name} export is missing columns: {missing}")

    rows: list[dict[str, str]] = []
    for source_row, source in enumerate(table.rows, start=2):
        row = {name: (source.get(column, "") if column else "") for name, column in spec.columns.items()}
        row["database"] = spec.key
        row["source_row"] = str(source_row)
        if not row["source_id"]:
            row["source_id"] = row["doi"] or f"{spec.key}:row:{source_row}"
        row["doi"] = normalize_doi(row["doi"])
        row["normalized_title"] = normalize_match_text(row["title"])
        row["normalized_authors"] = normalize_match_text(row["authors"])
        rows.append(row)

    write_csv(output_path, NORMALIZED_COLUMNS, rows)
    return output_path, len(rows)


def database_main(database: str) -> int:
    parser = argparse.ArgumentParser(description=f"Normalize the {SPECS[database].display_name} export.")
    parser.add_argument("--database-dir", type=Path, help="Override the directory containing results.*")
    args = parser.parse_args()
    try:
        output, count = normalize_database(database, args.database_dir)
    except PipelineError as exc:
        print(f"normalize.py: error: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {count} records to {output}")
    return 0
