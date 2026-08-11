#!/usr/bin/env python3
"""Stage 1: filter each database export by its configured content-type allowlist."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.pipeline_lib import (
    PipelineError,
    default_config_path,
    default_output_root,
    load_source_specs,
    normalize_content_type,
    read_table,
    reset_directory,
    validate_source_columns,
    write_csv,
)


def run_filter(config_path: Path, output_root: Path) -> list[dict[str, object]]:
    _, specs = load_source_specs(config_path)
    output_root = output_root.resolve()
    filtered_dir = output_root / "filtered"
    excluded_dir = output_root / "reports" / "excluded_by_source"
    reports_dir = output_root / "reports"

    reset_directory(filtered_dir)
    reset_directory(excluded_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, object]] = []

    for spec in specs:
        table = read_table(spec.input_path)
        validate_source_columns(spec, table)

        allowed = {normalize_content_type(value) for value in spec.allowed_content_types}
        kept_rows: list[dict[str, str]] = []
        excluded_rows: list[dict[str, str]] = []
        observed: Counter[str] = Counter()

        audit_row_column = "Pipeline Source Row"
        audit_reason_column = "Pipeline Exclusion Reason"
        for audit_column in (audit_row_column, audit_reason_column):
            if audit_column in table.fieldnames:
                raise PipelineError(
                    f"Reserved audit column {audit_column!r} already exists in {spec.input_path}"
                )

        for source_row, row in enumerate(table.rows, start=2):
            raw_type = row.get(spec.content_type_column, "")
            normalized_type = normalize_content_type(raw_type)
            observed[raw_type.strip() or "<blank>"] += 1
            if normalized_type in allowed:
                kept_rows.append(row)
            else:
                audit_row = dict(row)
                audit_row[audit_row_column] = str(source_row)
                audit_row[audit_reason_column] = "Content type is not in the configured allowlist"
                excluded_rows.append(audit_row)

        filtered_path = filtered_dir / spec.output_filename
        excluded_path = excluded_dir / spec.output_filename
        write_csv(filtered_path, table.fieldnames, kept_rows)
        write_csv(
            excluded_path,
            [*table.fieldnames, audit_row_column, audit_reason_column],
            excluded_rows,
        )

        summaries.append(
            {
                "source": spec.key,
                "database": spec.display_name,
                "input_file": str(spec.input_path),
                "filtered_file": str(filtered_path),
                "input_records": len(table.rows),
                "kept_records": len(kept_rows),
                "excluded_records": len(excluded_rows),
                "allowed_content_types": " | ".join(spec.allowed_content_types),
                "observed_content_types": json.dumps(
                    dict(sorted(observed.items())), ensure_ascii=False, sort_keys=True
                ),
            }
        )

    summary_fields = [
        "source",
        "database",
        "input_file",
        "filtered_file",
        "input_records",
        "kept_records",
        "excluded_records",
        "allowed_content_types",
        "observed_content_types",
    ]
    write_csv(reports_dir / "filter_summary.csv", summary_fields, summaries)
    return summaries


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Filter each configured SLR database export by content type. "
            "Outputs remain separated by database."
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
        summaries = run_filter(args.config, args.output_root)
    except PipelineError as exc:
        print(f"filter_content.py: error: {exc}", file=sys.stderr)
        return 2

    print("Content filtering complete:")
    for summary in summaries:
        print(
            f"- {summary['database']}: {summary['input_records']} input, "
            f"{summary['kept_records']} kept, {summary['excluded_records']} excluded"
        )
    print(f"Filtered files: {args.output_root.resolve() / 'filtered'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
