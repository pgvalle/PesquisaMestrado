#!/usr/bin/env python3
"""Normalize an ACM BibTeX export into the shared CSV schema.

The parser intentionally uses only the Python standard library so that ACM
exports can be converted without installing a BibTeX package.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import unicodedata
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
    write_csv,
)

DISPLAY_NAME = "ACM Digital Library"
INPUT_SUFFIX = ".bib"
INPUT_COLUMNS = {
    "title": "title",
    "doi": "doi",
    "year": "year",
    "url": "url",
}
ALLOWED_CONTENT_TYPES = ("Article", "Conference paper")


class BibTeXError(ValueError):
    """Raised when a BibTeX input cannot be parsed safely."""


_ENTRY_START_RE = re.compile(r"@\s*([A-Za-z]+)\s*([({])")
_FIELD_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_:-]*")


def _matching_delimiter(text: str, start: int, opening: str) -> int:
    closing = ")" if opening == "(" else "}"
    depth = 1
    in_quote = False
    escaped = False

    for position in range(start + 1, len(text)):
        character = text[position]
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if in_quote:
            if character == '"':
                in_quote = False
            continue
        if character == '"':
            in_quote = True
        elif character == opening:
            depth += 1
        elif character == closing:
            depth -= 1
            if depth == 0:
                return position

    raise BibTeXError("BibTeX entry has no closing delimiter")


def _first_top_level_comma(body: str) -> int:
    brace_depth = 0
    in_quote = False
    escaped = False
    for position, character in enumerate(body):
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if in_quote:
            if character == '"':
                in_quote = False
            continue
        if character == '"':
            in_quote = True
        elif character == "{":
            brace_depth += 1
        elif character == "}":
            brace_depth -= 1
        elif character == "," and brace_depth == 0:
            return position
    return -1


def _read_value_atom(text: str, position: int) -> tuple[str, int]:
    while position < len(text) and text[position].isspace():
        position += 1
    if position >= len(text):
        raise BibTeXError("BibTeX field has no value")

    if text[position] == "{":
        end = _matching_delimiter(text, position, "{")
        return text[position + 1 : end], end + 1

    if text[position] == '"':
        value_start = position + 1
        position += 1
        escaped = False
        while position < len(text):
            character = text[position]
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                return text[value_start:position], position + 1
            position += 1
        raise BibTeXError("BibTeX quoted value has no closing quote")

    value_start = position
    while position < len(text) and text[position] not in ",#}":
        position += 1
    return text[value_start:position].strip(), position


def _parse_entry(entry_type: str, body: str) -> dict[str, str]:
    comma = _first_top_level_comma(body)
    if comma < 0:
        raise BibTeXError(f"{entry_type} entry has no citation key")
    key = body[:comma].strip()
    if not key:
        raise BibTeXError(f"{entry_type} entry has an empty citation key")

    fields: dict[str, str] = {"entry_type": entry_type.casefold()}
    extracted_fields = set(INPUT_COLUMNS.values())
    position = comma + 1
    while position < len(body):
        while position < len(body) and (body[position].isspace() or body[position] == ","):
            position += 1
        if position >= len(body):
            break

        match = _FIELD_NAME_RE.match(body, position)
        if not match:
            raise BibTeXError(f"Invalid field near: {body[position:position + 30]!r}")
        field_name = match.group(0).casefold()
        position = match.end()
        while position < len(body) and body[position].isspace():
            position += 1
        if position >= len(body) or body[position] != "=":
            raise BibTeXError(f"Field {field_name!r} has no equals sign")
        position += 1

        atoms: list[str] = []
        while True:
            atom, position = _read_value_atom(body, position)
            atoms.append(atom)
            while position < len(body) and body[position].isspace():
                position += 1
            if position < len(body) and body[position] == "#":
                position += 1
                continue
            break
        if field_name in extracted_fields:
            fields[field_name] = "".join(atoms).strip()

    return fields


def parse_bibtex(text: str) -> list[dict[str, str]]:
    """Return parsed bibliographic entries, excluding comments and strings."""
    entries: list[dict[str, str]] = []
    position = 0
    while True:
        match = _ENTRY_START_RE.search(text, position)
        if match is None:
            break
        end = _matching_delimiter(text, match.end() - 1, match.group(2))
        entry_type = match.group(1).casefold()
        if entry_type not in {"comment", "preamble", "string"}:
            entries.append(_parse_entry(entry_type, text[match.end() : end]))
        position = end + 1
    return entries


_ACCENTS = {
    "'": {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú", "A": "Á", "E": "É", "I": "Í", "O": "Ó", "U": "Ú"},
    "`": {"a": "à", "e": "è", "i": "ì", "o": "ò", "u": "ù", "A": "À", "E": "È", "I": "Ì", "O": "Ò", "U": "Ù"},
    '"': {"a": "ä", "e": "ë", "i": "ï", "o": "ö", "u": "ü", "A": "Ä", "E": "Ë", "I": "Ï", "O": "Ö", "U": "Ü"},
    "~": {"a": "ã", "n": "ñ", "o": "õ", "A": "Ã", "N": "Ñ", "O": "Õ"},
    "^": {"a": "â", "e": "ê", "i": "î", "o": "ô", "u": "û", "A": "Â", "E": "Ê", "I": "Î", "O": "Ô", "U": "Û"},
    "c": {"c": "ç", "C": "Ç"},
}
_ACCENT_RE = re.compile(r"\\([\'`\"~^c])\s*\{?([A-Za-z])\}?")
_COMMAND_RE = re.compile(r"\\(?:[A-Za-z]+|.)")


def decode_tex(value: str) -> str:
    """Decode common BibTeX LaTeX escapes while retaining readable text."""
    value = html.unescape(value or "")

    def replace_accent(match: re.Match[str]) -> str:
        accent, character = match.groups()
        return _ACCENTS.get(accent, {}).get(character, character)

    value = _ACCENT_RE.sub(replace_accent, value)
    value = value.replace(r"\ss", "ß").replace(r"\ae", "æ").replace(r"\AE", "Æ")
    value = value.replace(r"\oe", "œ").replace(r"\OE", "Œ").replace(r"\o", "ø").replace(r"\O", "Ø")
    value = re.sub(r"\\([&%$#_{}])", r"\1", value)
    value = _COMMAND_RE.sub("", value)
    value = value.replace("{", "").replace("}", "").replace("~", " ")
    value = unicodedata.normalize("NFC", value)
    return re.sub(r"\s+", " ", value).strip()


def _field(entry: dict[str, str], *names: str) -> str:
    for name in names:
        value = entry.get(name, "")
        if value:
            return decode_tex(value)
    return ""


def _document_type(entry_type: str) -> str:
    return {
        "article": "Article",
        "inproceedings": "Conference paper",
        "conference": "Conference paper",
        "incollection": "Book chapter",
        "inbook": "Book chapter",
        "book": "Book",
        "proceedings": "Proceedings",
        "techreport": "Report",
        "phdthesis": "Thesis",
        "mastersthesis": "Thesis",
    }.get(entry_type, entry_type.replace("_", " ").title())


def entry_to_row(entry: dict[str, str]) -> dict[str, str]:
    entry_type = entry["entry_type"]
    row = {column: "" for column in OUTPUT_COLUMNS}
    row["document_type"] = _document_type(entry_type)
    for output_column, input_column in INPUT_COLUMNS.items():
        row[output_column] = _field(entry, input_column)
    return row


def normalize(input_path: Path, output_path: Path) -> int:
    try:
        text = input_path.read_text(encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise BibTeXError(f"Input file not found: {input_path}") from exc
    except UnicodeDecodeError as exc:
        raise BibTeXError(f"Input is not valid UTF-8: {input_path}: {exc}") from exc

    entries = parse_bibtex(text)
    allowed = {normalize_content_type(value) for value in ALLOWED_CONTENT_TYPES}
    rows = []
    for entry in entries:
        row = entry_to_row(entry)
        row["doi"] = normalize_doi(row["doi"])
        if normalize_content_type(row["document_type"]) not in allowed:
            continue
        if make_dedup_key(row["title"], row["doi"]) is None:
            continue
        rows.append(row)
    write_csv(output_path, OUTPUT_COLUMNS, rows)
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize an ACM BibTeX export.")
    parser.add_argument("input", type=Path, nargs="?", help="BibTeX input file")
    parser.add_argument("output", type=Path, nargs="?", help="CSV output file")
    args = parser.parse_args()
    try:
        input_path = args.input or find_dated_input(Path(__file__).parent, INPUT_SUFFIX)
        output_path = args.output or normalized_output_path(input_path)
        count = normalize(input_path, output_path)
    except (BibTeXError, PipelineError) as exc:
        print(f"normalize.py: error: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {count} records to {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
