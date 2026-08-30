from __future__ import annotations

import csv
from importlib import import_module
import sys
import tempfile
import unittest
from pathlib import Path

SLR_DIR = Path(__file__).resolve().parents[2]
if str(SLR_DIR) not in sys.path:
    sys.path.insert(0, str(SLR_DIR))

_acm_normalizer = import_module("dbs.acm.normalize")
from scripts.common import OUTPUT_COLUMNS

normalize = _acm_normalizer.normalize
entry_to_row = _acm_normalizer.entry_to_row
parse_bibtex = _acm_normalizer.parse_bibtex


class AcmNormalizeTests(unittest.TestCase):
    def test_parser_handles_nested_braces_and_latex_accents(self) -> None:
        entries = parse_bibtex(
            r'''@inproceedings{example,
                title = {A {Functional} Example},
                year = {2024},
                booktitle = {Proceedings},
                abstract = {Text with a comma, and a closing brace: {x}.},
                month = mar
            }'''
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["title"], "A {Functional} Example")
        self.assertNotIn("booktitle", entries[0])
        self.assertNotIn("abstract", entries[0])

    def test_decoder_handles_escaped_symbols(self) -> None:
        entries = parse_bibtex(r"""@article{example, title = {A \& B \% test}}""")
        self.assertEqual(entry_to_row(entries[0])["title"], "A & B % test")

    def test_normalize_writes_expected_columns_and_values(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_bib_test_") as temporary:
            root = Path(temporary)
            source = root / "input.bib"
            output = root / "output.csv"
            source.write_text(
                """@article{10.1234/example,
title = {A test article},
year = {2020},
journal = {Test Journal},
doi = {10.1234/example},
url = {https://doi.org/10.1234/example},
abstract = {An abstract},
keywords = {reactive programming, embedded systems},
month = mar
}
""",
                encoding="utf-8",
            )

            self.assertEqual(normalize(source, output), 1)
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(list(rows[0]), OUTPUT_COLUMNS)
            self.assertEqual(set(rows[0]), set(OUTPUT_COLUMNS))
            self.assertNotIn("document_type", rows[0])
            self.assertNotIn("source_row", rows[0])
            self.assertNotIn("entry_type", rows[0])
            self.assertNotIn("bibtex_key", rows[0])
            self.assertEqual(rows[0]["doi"], "10.1234/example")
            self.assertEqual(rows[0]["url"], "https://doi.org/10.1234/example")
            self.assertNotIn("publisher", rows[0])
            self.assertNotIn("abstract", rows[0])


if __name__ == "__main__":
    unittest.main()
