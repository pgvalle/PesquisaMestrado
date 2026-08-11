#!/usr/bin/env python3
"""Stage 2: deduplicate filtered records by normalized title and authors."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.pipeline_lib import (
    PipelineError,
    SourceSpec,
    dedup_key_hash,
    default_config_path,
    default_output_root,
    load_source_specs,
    make_dedup_key,
    read_table,
    reset_directory,
    validate_source_columns,
    write_csv,
)


@dataclass(frozen=True)
class Keeper:
    source: SourceSpec
    filtered_row: int
    title: str
    authors: str


def run_deduplication(config_path: Path, output_root: Path) -> list[dict[str, object]]:
    _, specs = load_source_specs(config_path)
    output_root = output_root.resolve()
    filtered_dir = output_root / "filtered"
    deduplicated_dir = output_root / "deduplicated"
    removed_dir = output_root / "reports" / "duplicates_removed_by_source"
    reports_dir = output_root / "reports"

    reset_directory(deduplicated_dir)
    reset_directory(removed_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    seen: dict[tuple[str, str], Keeper] = {}
    summaries: list[dict[str, object]] = []

    audit_columns = [
        "Pipeline Filtered Row",
        "Pipeline Duplicate Of Source",
        "Pipeline Duplicate Of Filtered Row",
        "Pipeline Dedup Key SHA256",
    ]

    for spec in specs:
        filtered_path = filtered_dir / spec.output_filename
        if not filtered_path.is_file():
            raise PipelineError(
                f"Filtered input is missing for {spec.display_name}: {filtered_path}. "
                "Run filter_content.py first."
            )

        table = read_table(filtered_path)
        validate_source_columns(spec, table)
        for audit_column in audit_columns:
            if audit_column in table.fieldnames:
                raise PipelineError(
                    f"Reserved audit column {audit_column!r} already exists in {filtered_path}"
                )

        kept_rows: list[dict[str, str]] = []
        removed_rows: list[dict[str, str]] = []
        missing_key_records = 0

        for filtered_row, row in enumerate(table.rows, start=2):
            title = row.get(spec.title_column, "")
            authors = row.get(spec.authors_column, "")
            key = make_dedup_key(title, authors)

            if key is None:
                missing_key_records += 1
                kept_rows.append(row)
                continue

            keeper = seen.get(key)
            if keeper is None:
                seen[key] = Keeper(
                    source=spec,
                    filtered_row=filtered_row,
                    title=title,
                    authors=authors,
                )
                kept_rows.append(row)
                continue

            audit_row = dict(row)
            audit_row["Pipeline Filtered Row"] = str(filtered_row)
            audit_row["Pipeline Duplicate Of Source"] = keeper.source.key
            audit_row["Pipeline Duplicate Of Filtered Row"] = str(keeper.filtered_row)
            audit_row["Pipeline Dedup Key SHA256"] = dedup_key_hash(key)
            removed_rows.append(audit_row)

        write_csv(deduplicated_dir / spec.output_filename, table.fieldnames, kept_rows)
        write_csv(
            removed_dir / spec.output_filename,
            [*table.fieldnames, *audit_columns],
            removed_rows,
        )

        summaries.append(
            {
                "source": spec.key,
                "database": spec.display_name,
                "filtered_records": len(table.rows),
                "kept_records": len(kept_rows),
                "duplicates_removed": len(removed_rows),
                "records_without_complete_title_author_key": missing_key_records,
                "deduplicated_file": str(deduplicated_dir / spec.output_filename),
            }
        )

    summary_fields = [
        "source",
        "database",
        "filtered_records",
        "kept_records",
        "duplicates_removed",
        "records_without_complete_title_author_key",
        "deduplicated_file",
    ]
    write_csv(reports_dir / "deduplication_summary.csv", summary_fields, summaries)
    return summaries


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Deduplicate the stage-1 filtered files by normalized title and authors. "
            "Survivors remain in separate database files."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=default_config_path(),
        help="Pipeline JSON configuration (default: scripts/pipeline_config.json)",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=default_output_root(),
        help="Pipeline output directory (default: SLR/pipeline_output)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        summaries = run_deduplication(args.config, args.output_root)
    except PipelineError as exc:
        print(f"deduplicate.py: error: {exc}", file=sys.stderr)
        return 2

    print("Deduplication complete (priority order from pipeline_config.json):")
    for summary in summaries:
        print(
            f"- {summary['database']}: {summary['filtered_records']} filtered, "
            f"{summary['kept_records']} kept, "
            f"{summary['duplicates_removed']} duplicates removed"
        )
    print(f"Deduplicated files: {args.output_root.resolve() / 'deduplicated'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
