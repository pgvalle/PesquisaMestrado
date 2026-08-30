#!/usr/bin/env python3
"""Normalize one or more database exports into the common SLR schema."""

from __future__ import annotations

import argparse
from importlib import import_module
import sys
from collections.abc import Iterable
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common import (
    DATABASE_ORDER,
    PipelineError,
    find_dated_input,
    normalized_output_path,
)


def normalize_all(
    dbs_dir: Path, databases: Iterable[str] = DATABASE_ORDER
) -> list[dict[str, object]]:
    """Normalize the selected databases and return a per-database summary."""
    dbs_dir = dbs_dir.resolve()
    summary: list[dict[str, object]] = []

    for database in databases:
        database_dir = dbs_dir / database
        normalizer = import_module(f"dbs.{database}.normalize")
        raw_path = find_dated_input(database_dir, normalizer.INPUT_SUFFIX)
        output_path = normalized_output_path(raw_path)
        count = normalizer.normalize(raw_path, output_path)
        summary.append(
            {
                "database": database,
                "input_file": str(raw_path),
                "records_written": count,
                "normalized_file": str(output_path),
            }
        )

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize all configured database exports into the common SLR schema."
    )
    parser.add_argument(
        "databases",
        nargs="*",
        choices=DATABASE_ORDER,
        default=DATABASE_ORDER,
        help="Databases to normalize (default: all)",
    )
    parser.add_argument(
        "--dbs-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "dbs",
        help="Directory containing the database folders (default: slr/dbs)",
    )
    args = parser.parse_args()
    try:
        summary = normalize_all(args.dbs_dir, args.databases)
    except (PipelineError, ValueError) as exc:
        print(f"normalize.py: error: {exc}", file=sys.stderr)
        return 2

    for item in summary:
        print(
            f"{item['database']}: wrote {item['records_written']} records "
            f"to {item['normalized_file']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
