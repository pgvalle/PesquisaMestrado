#!/usr/bin/env python3
"""Shared utilities for the SLR filtering and deduplication pipeline."""

from __future__ import annotations

import csv
import hashlib
import html
import re
import shutil
import subprocess
import tempfile
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


def _libreoffice_executable() -> str:
    executable = shutil.which("libreoffice") or shutil.which("soffice")
    if not executable:
        raise PipelineError(
            "Reading .xls/.xlsx files requires LibreOffice. Install LibreOffice, "
            "or export the workbook as UTF-8 CSV and update the database normalizer."
        )
    return executable


def _read_excel_via_libreoffice(path: Path) -> Table:
    if not path.is_file():
        raise PipelineError(f"Input file not found: {path}")

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
            str(path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise PipelineError(f"LibreOffice failed to convert {path}: {detail}")

        expected = temporary_path / f"{path.stem}.csv"
        if expected.is_file():
            converted = expected
        else:
            candidates = sorted(temporary_path.glob("*.csv"))
            if len(candidates) != 1:
                detail = (result.stdout + result.stderr).strip()
                raise PipelineError(
                    f"Could not identify converted CSV for {path}. LibreOffice output: {detail}"
                )
            converted = candidates[0]
        return _read_csv(converted)


def read_table(path: Path) -> Table:
    suffix = path.suffix.casefold()
    if suffix == ".csv":
        return _read_csv(path)
    if suffix in {".xls", ".xlsx"}:
        return _read_excel_via_libreoffice(path)
    raise PipelineError(f"Unsupported input format {path.suffix!r}: {path}")


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
    """Normalize a title or author string for exact deterministic matching.

    The source value is not modified. For the key only, entities and markup are
    flattened, Unicode is normalized and case-folded, punctuation becomes spaces,
    and repeated whitespace is collapsed.
    """

    text = html.unescape(value or "").replace("\u00a0", " ")
    text = _TAG_RE.sub(" ", text)
    text = unicodedata.normalize("NFKC", text).casefold()
    text = "".join(character if character.isalnum() else " " for character in text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def make_dedup_key(title: str, doi: str) -> tuple[str, str]:
    """Use DOI as the primary key and title only when DOI is unavailable."""
    normalized_doi = normalize_doi(doi)
    if normalized_doi:
        return "doi", normalized_doi

    normalized_title = normalize_match_text(title)
    if not normalized_title:
        raise AssertionError("Every record must contain a title or DOI")
    return "title", normalized_title


def dedup_key_hash(key: tuple[str, str]) -> str:
    return hashlib.sha256((key[0] + "\x1f" + key[1]).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
