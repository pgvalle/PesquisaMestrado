#!/usr/bin/env python3
"""Shared CSV and identity utilities for the SLR pipeline."""

from __future__ import annotations

import csv
import hashlib
import html
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


class PipelineError(RuntimeError):
    """Raised when an input or pipeline configuration is invalid."""


@dataclass
class Table:
    fieldnames: list[str]
    rows: list[dict[str, str]]


OUTPUT_COLUMNS = [
    "title",
    "doi",
    "year",
    "url",
]

DATABASE_ORDER = (
    "scopus",
    "wos",
    "ieee",
    "springer",
    "acm",
)


_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_SEMICOLON_SPACE_RE = re.compile(r"\s*;\s*")
_DOI_RE = re.compile(r"(?:https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/\S+)", re.IGNORECASE)


def _read_csv(path: Path) -> Table:
    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except FileNotFoundError as exc:
        raise PipelineError(f"Input file not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise PipelineError(f"Input is not valid UTF-8: {path}: {exc}") from exc

    with handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise PipelineError(f"CSV has no header: {path}")
        fieldnames = list(reader.fieldnames)
        if len(fieldnames) != len(set(fieldnames)):
            raise PipelineError(f"CSV contains duplicate column names: {path}")

        rows: list[dict[str, str]] = []
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise PipelineError(f"CSV row {row_number} has extra columns: {path}")
            missing_values = [name for name in fieldnames if row.get(name) is None]
            if missing_values:
                raise PipelineError(
                    f"CSV row {row_number} is missing values for columns {missing_values}: {path}"
                )
            rows.append({name: row[name] for name in fieldnames})

    return Table(fieldnames=fieldnames, rows=rows)


def read_table(path: Path) -> Table:
    if path.suffix.casefold() != ".csv":
        raise PipelineError(f"Expected a CSV input: {path}")
    return _read_csv(path)


def write_csv(
    path: Path,
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fieldnames),
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def append_filename_suffix(
    path: Path, suffix: str, extension: str | None = None
) -> Path:
    """Append a stage suffix before the extension without changing the directory."""
    output_extension = extension if extension is not None else path.suffix
    return path.with_name(f"{path.stem}{suffix}{output_extension}")


def find_dated_input(directory: Path, suffix: str | Sequence[str]) -> Path:
    """Find the single dated raw export with one of the requested suffixes."""
    directory = directory.resolve()
    suffixes = (suffix,) if isinstance(suffix, str) else tuple(suffix)
    candidates = sorted(
        {
            path
            for current_suffix in suffixes
            for path in directory.glob(f"results-*{current_suffix}")
            if path.is_file()
            and not path.stem.endswith(("-normalized", "-deduplicated"))
        }
    )
    if not candidates:
        raise PipelineError(
            f"Missing dated input in {directory}; expected results-*"
            f"{{{', '.join(suffixes)}}}"
        )
    if len(candidates) > 1:
        names = ", ".join(path.name for path in candidates)
        raise PipelineError(
            f"Multiple dated inputs in {directory}: {names}; "
            "keep one dated input per database"
        )
    return candidates[0].resolve()


def normalized_output_path(input_path: Path) -> Path:
    """Return the common-schema output path for a dated raw input."""
    return append_filename_suffix(input_path, "-normalized", ".csv")


def _source_value(
    row: Mapping[str | None, object], source_columns: str | Sequence[str] | None
) -> str:
    if source_columns is None:
        return ""
    columns = (source_columns,) if isinstance(source_columns, str) else source_columns
    for column in columns:
        value = row.get(column, "")
        if isinstance(value, list):
            value = value[0] if value else ""
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def normalize_records(
    rows: Iterable[Mapping[str | None, object]],
    output_path: Path,
    input_columns: Mapping[str, str | Sequence[str] | None],
    allowed_content_types: Iterable[str],
) -> int:
    """Map database rows into the shared output schema and apply local filters."""
    allowed = {normalize_content_type(value) for value in allowed_content_types}
    normalized_rows: list[dict[str, str]] = []
    for source in rows:
        document_type = _source_value(source, input_columns.get("document_type"))
        row = {
            column: _source_value(source, input_columns.get(column))
            for column in OUTPUT_COLUMNS
        }
        row["doi"] = normalize_doi(row["doi"])
        if normalize_content_type(document_type) not in allowed:
            continue
        if make_dedup_key(row["title"], row["doi"]) is None:
            continue
        normalized_rows.append(row)

    write_csv(output_path, OUTPUT_COLUMNS, normalized_rows)
    return len(normalized_rows)


def normalize_csv_export(
    input_path: Path,
    output_path: Path,
    input_columns: Mapping[str, str],
    allowed_content_types: Iterable[str],
) -> int:
    """Read a CSV export, validate its local columns, and normalize it."""
    table = read_table(input_path)
    missing = sorted(set(input_columns.values()) - set(table.fieldnames))
    if missing:
        raise PipelineError(f"Input file {input_path} is missing columns: {missing}")
    return normalize_records(table.rows, output_path, input_columns, allowed_content_types)


def normalize_content_type(value: str) -> str:
    text = html.unescape(value or "").replace("\u00a0", " ")
    text = unicodedata.normalize("NFKC", text).casefold().strip()
    text = _SEMICOLON_SPACE_RE.sub("; ", text)
    return _WHITESPACE_RE.sub(" ", text)


def normalize_doi(value: str) -> str:
    """Return a case-insensitive bare DOI for matching and output."""
    value = (value or "").strip()
    match = _DOI_RE.search(value)
    return match.group(1).rstrip(".,;)").casefold() if match else value.casefold()


def normalize_match_text(value: str) -> str:
    """Normalize a title string for exact deterministic matching.

    The source value is not modified. For the key only, entities and markup are
    flattened, Unicode is normalized and case-folded, punctuation becomes spaces,
    and repeated whitespace is collapsed.
    """

    text = html.unescape(value or "").replace("\u00a0", " ")
    text = _TAG_RE.sub(" ", text)
    text = unicodedata.normalize("NFKC", text).casefold()
    text = "".join(character if character.isalnum() else " " for character in text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def make_dedup_key(title: str, doi: str) -> tuple[str, str] | None:
    """Use DOI first, title second, or no key when neither is usable."""
    normalized_doi = normalize_doi(doi)
    if normalized_doi:
        return "doi", normalized_doi

    normalized_title = normalize_match_text(title)
    if not normalized_title:
        return None
    return "title", normalized_title


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
