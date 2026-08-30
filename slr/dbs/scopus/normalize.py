#!/usr/bin/env python3
"""Normalize a Scopus export into the shared CSV schema."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common import (
    PipelineError,
    find_dated_input,
    normalize_csv_export,
    normalized_output_path,
)


DISPLAY_NAME = "Scopus"
INPUT_SUFFIX = ".csv"
INPUT_COLUMNS = {
    "title": "Title",
    "year": "Year",
    "doi": "DOI",
    "document_type": "Document Type",
    "url": "Link",
}
ALLOWED_CONTENT_TYPES = ("Article", "Conference paper", "Book chapter", "Book")


def normalize(input_path: Path, output_path: Path) -> int:
    return normalize_csv_export(
        input_path, output_path, INPUT_COLUMNS, ALLOWED_CONTENT_TYPES
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize a Scopus export.")
    parser.add_argument("input", type=Path, nargs="?", help="CSV input file")
    parser.add_argument("output", type=Path, nargs="?", help="CSV output file")
    args = parser.parse_args()
    try:
        input_path = args.input or find_dated_input(Path(__file__).parent, INPUT_SUFFIX)
        output_path = args.output or normalized_output_path(input_path)
        count = normalize(input_path, output_path)
    except PipelineError as exc:
        print(f"normalize.py: error: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {count} records to {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
