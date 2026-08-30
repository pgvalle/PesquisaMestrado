#!/usr/bin/env python3
"""Extract the selected Web of Science columns into a CSV."""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path


CSV_COLUMNS = [
    "document_type",
    "title",
    "doi",
    "year",
    "url",
]


class ExcelError(ValueError):
    """Raised when an Excel input cannot be converted safely."""


_FIELD_ALIASES = {
    "document_type": (
        "Document Type",
        "Document Identifier",
        "Content Type",
        "document_type",
    ),
    "title": ("Article Title", "Document Title", "Item Title", "Title", "title"),
    "doi": ("DOI", "DOI Link", "Item DOI", "doi"),
    "year": ("Publication Year", "Year", "year"),
    "url": ("Web of Science Record", "URL", "Link", "PDF Link", "url"),
}


def _libreoffice_executable() -> str:
    executable = shutil.which("libreoffice") or shutil.which("soffice")
    if not executable:
        raise ExcelError(
            "Converting .xls/.xlsx files requires LibreOffice. Install LibreOffice "
            "or provide a CSV export."
        )
    return executable


def _field(row: Mapping[str | None, str | list[str] | None], *names: str) -> str:
    for name in names:
        value = row.get(name, "")
        if isinstance(value, list):
            value = value[0] if value else ""
        if value:
            return str(value).strip()
    return ""


def _row_to_csv(row: Mapping[str | None, str | list[str] | None]) -> dict[str, str]:
    return {
        column: _field(row, *_FIELD_ALIASES[column]) for column in CSV_COLUMNS
    }


def _read_converted_csv(path: Path) -> list[dict[str, str]]:
    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except FileNotFoundError as exc:
        raise ExcelError(f"LibreOffice did not create a CSV for {path}") from exc
    except UnicodeDecodeError as exc:
        raise ExcelError(f"Converted CSV is not valid UTF-8: {path}: {exc}") from exc

    with handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ExcelError(f"Converted CSV has no header: {path}")
        return [_row_to_csv(row) for row in reader]


def _read_excel(input_path: Path) -> list[dict[str, str]]:
    if not input_path.is_file():
        raise ExcelError(f"Input file not found: {input_path}")

    executable = _libreoffice_executable()
    with tempfile.TemporaryDirectory(prefix="slr_excel_") as temporary:
        temporary_path = Path(temporary)
        profile_uri = (temporary_path / "libreoffice-profile").resolve().as_uri()
        command = [
            executable,
            f"-env:UserInstallation={profile_uri}",
            "--headless",
            "--convert-to",
            "csv",
            "--outdir",
            str(temporary_path),
            str(input_path.resolve()),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise ExcelError(f"LibreOffice failed to convert {input_path}: {detail}")

        converted = temporary_path / f"{input_path.stem}.csv"
        if not converted.is_file():
            candidates = sorted(temporary_path.glob("*.csv"))
            if len(candidates) != 1:
                detail = (result.stdout + result.stderr).strip()
                raise ExcelError(
                    f"Could not identify converted CSV for {input_path}. "
                    f"LibreOffice output: {detail}"
                )
            converted = candidates[0]
        return _read_converted_csv(converted)


def convert(input_path: Path, output_path: Path) -> int:
    """Convert .xls/.xlsx input and write only the configured CSV columns."""
    if input_path.suffix.casefold() not in {".xls", ".xlsx"}:
        raise ExcelError(f"Unsupported input format: {input_path.suffix or '<none>'}")

    rows = _read_excel(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert an Excel export to CSV.")
    parser.add_argument("input", type=Path, help="Excel input (.xls or .xlsx)")
    parser.add_argument("output", type=Path, help="CSV output")
    args = parser.parse_args()
    try:
        count = convert(args.input, args.output)
    except ExcelError as exc:
        print(f"2csv.py: error: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {count} records to {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
