#!/usr/bin/env python3
"""Create a common-schema CSV from one database export."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.pipeline_lib import (
    PipelineError,
    normalize_content_type,
    normalize_doi,
    read_table,
    write_csv,
)


NORMALIZED_COLUMNS = [
    "database",
    "source_row",
    "title",
    "authors",
    "year",
    "doi",
    "document_type",
    "url",
]


@dataclass(frozen=True)
class NormalizationSpec:
    key: str
    display_name: str
    input_filename: str
    columns: dict[str, str | None]
    allowed_content_types: tuple[str, ...]


SPECS = {
    "scopus": NormalizationSpec(
        key="scopus",
        display_name="Scopus",
        input_filename="results.csv",
        columns={
            "title": "Title", "authors": "Authors",
            "year": "Year", "doi": "DOI",
            "document_type": "Document Type", "url": "Link",
        },
        allowed_content_types=("Article", "Conference paper", "Book chapter", "Book"),
    ),
    "wos": NormalizationSpec(
        key="wos",
        display_name="Web of Science",
        input_filename="results.xls",
        columns={
            "title": "Article Title", "authors": "Authors",
            "year": "Publication Year", "doi": "DOI Link",
            "document_type": "Document Type", "url": "Web of Science Record",
        },
        allowed_content_types=(
            "Article",
            "Proceedings Paper",
            "Article; Proceedings Paper",
            "Book",
            "Book Chapter",
        ),
    ),
    "ieee": NormalizationSpec(
        key="ieee",
        display_name="IEEE",
        input_filename="results.csv",
        columns={
            "title": "Document Title", "authors": "Authors",
            "year": "Publication Year", "doi": "DOI",
            "document_type": "Document Identifier", "url": "PDF Link",
        },
        allowed_content_types=(
            "IEEE Journals",
            "IEEE Conferences",
            "IEEE Books",
            "IEEE Early Access Articles",
        ),
    ),
    "springer": NormalizationSpec(
        key="springer",
        display_name="Springer",
        input_filename="results.csv",
        columns={
            "title": "Item Title", "authors": "Authors",
            "year": "Publication Year", "doi": "Item DOI",
            "document_type": "Content Type", "url": "URL",
        },
        allowed_content_types=("Article", "Conference paper", "Chapter", "Book"),
    ),
    "acm": NormalizationSpec(
        key="acm",
        display_name="ACM Digital Library",
        input_filename="results.csv",
        columns={
            "title": "title", "authors": "authors",
            "year": "year", "doi": "doi",
            "document_type": "document_type", "url": "url",
        },
        allowed_content_types=("Article", "Conference paper"),
    ),
}


def normalize_database(
    database: str,
    database_dir: Path | None = None,
    input_path: Path | None = None,
) -> tuple[Path, int]:
    try:
        spec = SPECS[database]
    except KeyError as exc:
        raise PipelineError(f"Unknown database {database!r}") from exc

    directory = (database_dir or Path(__file__).resolve().parent.parent / "dbs" / database).resolve()
    input_path = (input_path or directory / spec.input_filename).resolve()
    output_path = directory / "normalized.csv"
    table = read_table(input_path)

    required = {column for column in spec.columns.values() if column}
    missing = sorted(required - set(table.fieldnames))
    if missing:
        raise PipelineError(f"{spec.display_name} export is missing columns: {missing}")

    rows: list[dict[str, str]] = []
    allowed = {normalize_content_type(value) for value in spec.allowed_content_types}
    for source_row, source in enumerate(table.rows, start=2):
        row = {name: (source.get(column, "") if column else "") for name, column in spec.columns.items()}
        row["database"] = spec.key
        row["source_row"] = str(source_row)
        row["doi"] = normalize_doi(row["doi"])
        if not row["title"].strip() and not row["doi"]:
            raise AssertionError(
                f"{spec.display_name} row {source_row} must contain a title or DOI"
            )
        if normalize_content_type(row["document_type"]) not in allowed:
            continue
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
