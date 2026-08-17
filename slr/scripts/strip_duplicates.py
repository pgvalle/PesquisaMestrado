#!/usr/bin/env python3
"""Remove global DOI or title duplicates from normalized database files."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.normalize_common import NORMALIZED_COLUMNS, SPECS
from scripts.pipeline_lib import PipelineError, make_dedup_key, read_table, write_csv


SOURCE_PRIORITY = ("scopus", "wos", "ieee", "springer", "acm")
DUPLICATE_COLUMNS = [
    "title",
    "authors",
    "doi",
    "match_basis",
    "databases_found",
    "occurrence_count",
    "kept_database",
    "source_rows",
    "year",
]


def _complete_key(row: dict[str, str]) -> tuple[str, str]:
    return make_dedup_key(row.get("title", ""), row.get("doi", ""))


def strip_duplicates(dbs_dir: Path) -> tuple[list[dict[str, object]], int]:
    dbs_dir = dbs_dir.resolve()
    tables = {}
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    for database in SOURCE_PRIORITY:
        path = dbs_dir / database / "normalized.csv"
        if not path.is_file():
            raise PipelineError(
                f"Missing {path}; run scripts/normalize.py first"
            )
        table = read_table(path)
        missing = sorted(set(NORMALIZED_COLUMNS) - set(table.fieldnames))
        if missing:
            raise PipelineError(f"Normalized file {path} is missing columns: {missing}")
        tables[database] = table
        for row in table.rows:
            key = _complete_key(row)
            groups[key].append(row)

    duplicate_keys = {key for key, rows in groups.items() if len(rows) > 1}
    kept_ids = {id(rows[0]) for rows in groups.values()}
    summaries: list[dict[str, object]] = []

    for database in SOURCE_PRIORITY:
        table = tables[database]
        survivors = []
        removed = 0
        for row in table.rows:
            key = _complete_key(row)
            if key not in duplicate_keys or id(row) in kept_ids:
                survivors.append(row)
            else:
                removed += 1
        output = dbs_dir / database / "deduplicated.csv"
        write_csv(output, NORMALIZED_COLUMNS, survivors)
        summaries.append(
            {
                "database": database,
                "input_records": len(table.rows),
                "kept_records": len(survivors),
                "duplicates_removed": removed,
                "output": str(output),
            }
        )

    duplicate_rows = []
    for key, occurrences in groups.items():
        if len(occurrences) < 2:
            continue
        keeper = occurrences[0]
        databases = list(dict.fromkeys(row["database"] for row in occurrences))
        duplicate_rows.append(
            {
                "title": keeper["title"],
                "authors": keeper["authors"],
                "doi": keeper["doi"],
                "match_basis": key[0],
                "databases_found": "; ".join(databases),
                "occurrence_count": len(occurrences),
                "kept_database": keeper["database"],
                "source_rows": "; ".join(
                    f"{row['database']}:{row['source_row']}" for row in occurrences
                ),
                "year": keeper["year"],
            }
        )
    duplicate_rows.sort(key=lambda row: (str(row["match_basis"]), str(row["doi"]), str(row["title"])))
    write_csv(dbs_dir / "duplicates.csv", DUPLICATE_COLUMNS, duplicate_rows)
    return summaries, len(duplicate_rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deduplicate all normalized database CSV files.")
    parser.add_argument(
        "--dbs-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "dbs",
        help="Directory containing scopus, wos, ieee, and springer (default: SLR/dbs)",
    )
    args = parser.parse_args()
    try:
        summaries, duplicate_groups = strip_duplicates(args.dbs_dir)
    except PipelineError as exc:
        print(f"strip_duplicates.py: error: {exc}", file=sys.stderr)
        return 2
    for summary in summaries:
        print(
            f"{SPECS[summary['database']].display_name}: "
            f"{summary['kept_records']}/{summary['input_records']} kept "
            f"({summary['duplicates_removed']} removed)"
        )
    print(f"Duplicate groups: {duplicate_groups}")
    print(f"Audit file: {args.dbs_dir.resolve() / 'duplicates.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
