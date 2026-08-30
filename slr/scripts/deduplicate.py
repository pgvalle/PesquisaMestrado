#!/usr/bin/env python3
"""Remove global DOI or title duplicates from normalized database files."""

from __future__ import annotations

import argparse
from importlib import import_module
import sys
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common import (
    DATABASE_ORDER,
    OUTPUT_COLUMNS,
    PipelineError,
    append_filename_suffix,
    make_dedup_key,
    read_table,
    write_csv,
)


DUPLICATE_COLUMNS = [
    "title",
    "doi",
    "match_basis",
    "databases_found",
    "occurrence_count",
    "kept_database",
    "source_rows",
    "year",
]


def _complete_key(row: dict[str, str]) -> tuple[str, str] | None:
    return make_dedup_key(row.get("title", ""), row.get("doi", ""))


def _display_name(database: str) -> str:
    return import_module(f"dbs.{database}.normalize").DISPLAY_NAME


def _find_normalized_path(database_dir: Path, database: str) -> Path:
    candidates = sorted(
        path
        for path in database_dir.glob("results-*-normalized.csv")
        if path.is_file()
    )
    if not candidates:
        raise PipelineError(
            f"Missing dated normalized file in {database_dir}; "
            "run scripts/normalize.py first"
        )
    if len(candidates) > 1:
        names = ", ".join(path.name for path in candidates)
        raise PipelineError(
            f"Multiple dated normalized files for {database}: {names}; "
            "select one run before deduplicating"
        )
    return candidates[0].resolve()


def _result_base_path(normalized_path: Path) -> Path:
    suffix = "-normalized"
    if not normalized_path.stem.endswith(suffix):
        raise PipelineError(f"Unexpected normalized filename: {normalized_path}")
    base_stem = normalized_path.stem[: -len(suffix)]
    return normalized_path.with_name(f"{base_stem}{normalized_path.suffix}")


def _deduplicated_output_path(normalized_path: Path) -> Path:
    return append_filename_suffix(_result_base_path(normalized_path), "-deduplicated")


def _duplicates_output_path(
    dbs_dir: Path, normalized_paths: Mapping[str, Path]
) -> Path:
    base_names = {_result_base_path(path).name for path in normalized_paths.values()}
    if len(base_names) != 1:
        names = ", ".join(sorted(base_names))
        raise PipelineError(
            "Normalized files must share one dated result stem; found: " + names
        )
    base_name = next(iter(base_names))
    return dbs_dir / f"{Path(base_name).stem}-duplicates.csv"


def strip_duplicates(
    dbs_dir: Path, normalized_paths: Mapping[str, Path] | None = None
) -> tuple[list[dict[str, object]], int]:
    dbs_dir = dbs_dir.resolve()
    normalized_paths = normalized_paths or {}
    tables = {}
    selected_paths: dict[str, Path] = {}
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    for database in DATABASE_ORDER:
        path = normalized_paths.get(database)
        if path is None:
            path = _find_normalized_path(dbs_dir / database, database)
        else:
            path = Path(path).resolve()
        if not path.is_file():
            raise PipelineError(
                f"Missing {path}; run scripts/normalize.py first"
            )
        table = read_table(path)
        missing = sorted(set(OUTPUT_COLUMNS) - set(table.fieldnames))
        if missing:
            raise PipelineError(f"Normalized file {path} is missing columns: {missing}")
        selected_paths[database] = path
        rows = []
        for source_row, source in enumerate(table.rows, start=2):
            row = dict(source)
            row["database"] = database
            row["source_row"] = str(source_row)
            rows.append(row)
            key = _complete_key(row)
            if key is None:
                raise PipelineError(
                    f"Normalized file {path} contains a record without a title or DOI "
                    f"at source row {row.get('source_row', '') or 'unknown'}"
                )
            groups[key].append(row)
        tables[database] = rows

    duplicate_keys = {key for key, rows in groups.items() if len(rows) > 1}
    kept_ids = {id(rows[0]) for rows in groups.values()}
    summaries: list[dict[str, object]] = []

    for database in DATABASE_ORDER:
        table = tables[database]
        survivors = []
        removed = 0
        for row in table:
            key = _complete_key(row)
            if key is None:
                continue
            if key not in duplicate_keys or id(row) in kept_ids:
                survivors.append(row)
            else:
                removed += 1
        output = _deduplicated_output_path(selected_paths[database])
        write_csv(output, OUTPUT_COLUMNS, survivors)
        summaries.append(
            {
                "database": database,
                "normalized_file": str(selected_paths[database]),
                "input_records": len(table),
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
    write_csv(_duplicates_output_path(dbs_dir, selected_paths), DUPLICATE_COLUMNS, duplicate_rows)
    return summaries, len(duplicate_rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deduplicate all dated normalized database CSV files."
    )
    parser.add_argument(
        "--dbs-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "dbs",
        help="Directory containing the configured database folders (default: SLR/dbs)",
    )
    args = parser.parse_args()
    try:
        summaries, duplicate_groups = strip_duplicates(args.dbs_dir)
    except PipelineError as exc:
        print(f"deduplicate.py: error: {exc}", file=sys.stderr)
        return 2
    for summary in summaries:
        print(
            f"{_display_name(str(summary['database']))}: "
            f"{summary['kept_records']}/{summary['input_records']} kept "
            f"({summary['duplicates_removed']} removed)"
        )
    print(f"Duplicate groups: {duplicate_groups}")
    audit_path = _duplicates_output_path(
        args.dbs_dir.resolve(),
        {
            str(summary["database"]): Path(str(summary["normalized_file"]))
            for summary in summaries
        },
    )
    print(f"Audit file: {audit_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
