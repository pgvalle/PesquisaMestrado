#!/usr/bin/env python3
"""Convert the ACM BibTeX export to a spreadsheet-friendly CSV."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bib_to_csv import convert
from scripts.normalize_common import normalize_database


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert ACM BibTeX to results.csv and normalized.csv."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).with_name("results.bib"),
        help="ACM BibTeX export (default: results.bib)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("results.csv"),
        help="CSV output (default: results.csv)",
    )
    args = parser.parse_args()
    try:
        count = convert(args.input, args.output)
        normalized_output, normalized_count = normalize_database(
            "acm", args.output.parent, args.output
        )
    except ValueError as exc:
        print(f"normalize.py: error: {exc}", file=sys.stderr)
        raise SystemExit(2)
    print(f"Wrote {count} ACM records to {args.output.resolve()}")
    print(f"Wrote {normalized_count} filtered records to {normalized_output.resolve()}")
