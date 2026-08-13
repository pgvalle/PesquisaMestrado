from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[3]
ACM_DIR = PROJECT_DIR / "slr" / "dbs" / "acm"
if str(ACM_DIR) not in sys.path:
    sys.path.insert(0, str(ACM_DIR))

from bib_to_csv import CSV_COLUMNS, convert, entry_to_row, parse_bibtex


class BibToCsvTests(unittest.TestCase):
    def test_parser_handles_nested_braces_and_latex_accents(self) -> None:
        entries = parse_bibtex(
            r'''@inproceedings{example,
                author = {B{"a}renz, Manuel and Le Mou{"e}l, Fr{\'e}d{\'e}ric},
                title = {A {Functional} Example},
                year = {2024},
                booktitle = {Proceedings},
                abstract = {Text with a comma, and a closing brace: {x}.},
                month = mar
            }'''
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["title"], "A {Functional} Example")

    def test_decoder_handles_escaped_symbols(self) -> None:
        entries = parse_bibtex(r"""@article{example, title = {A \& B \% test}}""")
        self.assertEqual(entry_to_row(entries[0], 1)["title"], "A & B % test")

    def test_conversion_writes_expected_columns_and_values(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_bib_test_") as temporary:
            root = Path(temporary)
            source = root / "input.bib"
            output = root / "output.csv"
            source.write_text(
                """@article{10.1234/example,
author = {Doe, Jane and Smith, John},
title = {A test article},
year = {2020},
journal = {Test Journal},
doi = {10.1234/example},
abstract = {An abstract},
keywords = {reactive programming, embedded systems},
month = mar
}
""",
                encoding="utf-8",
            )

            self.assertEqual(convert(source, output), 1)
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(list(rows[0]), CSV_COLUMNS)
            self.assertEqual(rows[0]["source_id"], "10.1234/example")
            self.assertNotIn("bibtex_key", rows[0])
            self.assertEqual(rows[0]["document_type"], "Article")
            self.assertEqual(rows[0]["publisher"], "")
            self.assertNotIn("abstract", rows[0])


if __name__ == "__main__":
    unittest.main()
