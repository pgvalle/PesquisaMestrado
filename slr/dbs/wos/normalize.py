#!/usr/bin/env python3
"""Normalize a Web of Science Excel export into the shared CSV schema."""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common import (
    OUTPUT_COLUMNS,
    PipelineError,
    find_dated_input,
    make_dedup_key,
    normalize_content_type,
    normalize_doi,
    normalized_output_path,
    read_table,
    write_csv,
)


DISPLAY_NAME = "Web of Science"
INPUT_SUFFIX = (".xls", ".xlsx", ".csv")


class ExcelError(ValueError):
    """Raised when an Excel input cannot be converted safely."""


INPUT_COLUMNS = {
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
ALLOWED_CONTENT_TYPES = (
    "Article",
    "Proceedings Paper",
    "Article; Proceedings Paper",
    "Book",
    "Book Chapter",
)


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
    normalized = {
        column: _field(row, *INPUT_COLUMNS[column]) for column in OUTPUT_COLUMNS
    }
    normalized["document_type"] = _field(row, *INPUT_COLUMNS["document_type"])
    return normalized


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


def _read_input(input_path: Path) -> list[dict[str, str]]:
    if input_path.suffix.casefold() == ".csv":
        return [_row_to_csv(row) for row in read_table(input_path).rows]
    return _read_excel(input_path)


def normalize(input_path: Path, output_path: Path) -> int:
    """Normalize .xls/.xlsx input and write the shared CSV columns."""
    if input_path.suffix.casefold() not in {".xls", ".xlsx", ".csv"}:
        raise ExcelError(f"Unsupported input format: {input_path.suffix or '<none>'}")

    allowed = {normalize_content_type(value) for value in ALLOWED_CONTENT_TYPES}
    rows = []
    for row in _read_input(input_path):
        row["doi"] = normalize_doi(row["doi"])
        if normalize_content_type(row["document_type"]) not in allowed:
            continue
        if make_dedup_key(row["title"], row["doi"]) is None:
            continue
        rows.append(row)
    write_csv(output_path, OUTPUT_COLUMNS, rows)
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize a Web of Science export.")
    parser.add_argument(
        "input", type=Path, nargs="?", help="Excel or CSV input (.xls, .xlsx, or .csv)"
    )
    parser.add_argument("output", type=Path, nargs="?", help="CSV output")
    args = parser.parse_args()
    try:
        input_path = args.input or find_dated_input(Path(__file__).parent, INPUT_SUFFIX)
        output_path = args.output or normalized_output_path(input_path)
        count = normalize(input_path, output_path)
    except (ExcelError, PipelineError) as exc:
        print(f"normalize.py: error: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {count} records to {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
