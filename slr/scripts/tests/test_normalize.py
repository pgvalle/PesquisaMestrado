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

from scripts.normalize import normalize_all
from dbs.acm.normalize import normalize as normalize_acm
from dbs.scopus.normalize import normalize as normalize_scopus
from scripts.common import (
    OUTPUT_COLUMNS,
    make_dedup_key,
    normalize_content_type,
    normalize_match_text,
    write_csv,
)


class NormalizeTests(unittest.TestCase):
    def test_csv_normalizers_use_local_input_mappings(self) -> None:
        for database in ("scopus", "ieee", "springer"):
            with self.subTest(database=database), tempfile.TemporaryDirectory(
                prefix=f"slr_{database}_normalizer_test_"
            ) as temporary:
                module = import_module(f"dbs.{database}.normalize")
                directory = Path(temporary)
                input_path = directory / "results-30.08.2026.csv"
                output_path = directory / "results-30.08.2026-normalized.csv"
                values = {
                    "document_type": module.ALLOWED_CONTENT_TYPES[0],
                    "title": f"A {database} article",
                    "doi": f"10.1000/{database}",
                    "year": "2024",
                    "url": f"https://example.test/{database}",
                }
                source = {
                    input_column: values[output_column]
                    for output_column, input_column in module.INPUT_COLUMNS.items()
                }
                write_csv(input_path, list(source), [source])

                self.assertEqual(module.normalize(input_path, output_path), 1)
                with output_path.open(encoding="utf-8-sig", newline="") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(list(rows[0]), OUTPUT_COLUMNS)
                self.assertEqual(
                    rows[0], {column: values[column] for column in OUTPUT_COLUMNS}
                )

    def test_match_normalization_is_case_markup_and_punctuation_insensitive(self) -> None:
        self.assertEqual(
            normalize_match_text("  A &amp; B: <i>Reactive</i>—System  "),
            "a b reactive system",
        )

    def test_content_type_normalization_preserves_compound_label(self) -> None:
        self.assertEqual(
            normalize_content_type(" Article ;  Proceedings Paper "),
            "article; proceedings paper",
        )

    def test_dedup_key_uses_doi_then_title(self) -> None:
        self.assertEqual(make_dedup_key("A title", ""), ("title", "a title"))
        self.assertEqual(make_dedup_key("A title", "10.1000/ABC"), ("doi", "10.1000/abc"))
        self.assertIsNone(make_dedup_key("", ""))

    def test_normalizer_rejects_records_without_usable_identity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_normalizer_test_") as temporary:
            directory = Path(temporary)
            fields = ["Title", "Year", "DOI", "Document Type", "Link"]
            write_csv(
                directory / "results-30.08.2026.csv",
                fields,
                [
                    {
                        "Title": "<i>!!!</i>",
                        "Year": "2024",
                        "DOI": "",
                        "Document Type": "Article",
                        "Link": "",
                    },
                    {
                        "Title": "   ",
                        "Year": "2024",
                        "DOI": "",
                        "Document Type": "Article",
                        "Link": "",
                    },
                ],
            )

            output = directory / "results-30.08.2026-normalized.csv"
            count = normalize_scopus(directory / "results-30.08.2026.csv", output)

            self.assertEqual(count, 0)
            with output.open(encoding="utf-8-sig", newline="") as handle:
                self.assertEqual(list(csv.DictReader(handle)), [])

    def test_normalizer_applies_content_type_allowlist(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_normalizer_test_") as temporary:
            directory = Path(temporary)
            fields = ["EID", "Title", "Year", "DOI", "Document Type", "Link"]
            write_csv(
                directory / "results-30.08.2026.csv",
                fields,
                [
                    {
                        "EID": "2-s2.0-article",
                        "Title": "An article",
                        "Year": "2024",
                        "DOI": "10.1000/article",
                        "Document Type": "Article",
                        "Link": "https://example.test/article",
                    },
                    {
                        "EID": "2-s2.0-review",
                        "Title": "A review",
                        "Year": "2024",
                        "DOI": "10.1000/review",
                        "Document Type": "Review",
                        "Link": "https://example.test/review",
                    },
                ],
            )

            output = directory / "results-30.08.2026-normalized.csv"
            count = normalize_scopus(directory / "results-30.08.2026.csv", output)

            self.assertEqual(count, 1)
            self.assertEqual(output.name, "results-30.08.2026-normalized.csv")
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row["title"] for row in rows], ["An article"])

    def test_normalize_all_discovers_dated_export(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_normalizer_test_") as temporary:
            dbs = Path(temporary)
            directory = dbs / "scopus"
            directory.mkdir()
            write_csv(
                directory / "results-30.08.2026.csv",
                ["Title", "Year", "DOI", "Document Type", "Link"],
                [
                    {
                        "Title": "A dated article",
                        "Year": "2024",
                        "DOI": "10.1000/dated",
                        "Document Type": "Article",
                        "Link": "",
                    }
                ],
            )

            summary = normalize_all(dbs, ("scopus",))

            self.assertEqual(
                summary[0]["input_file"],
                str(directory / "results-30.08.2026.csv"),
            )
            self.assertEqual(
                summary[0]["normalized_file"],
                str(directory / "results-30.08.2026-normalized.csv"),
            )

    def test_acm_normalize_all_preserves_dated_stem(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_acm_normalizer_test_") as temporary:
            dbs = Path(temporary)
            directory = dbs / "acm"
            directory.mkdir()
            raw_path = directory / "results-30.08.2026.bib"
            raw_path.write_text(
                """@article{example,
title = {A dated ACM article},
year = {2024},
doi = {10.1000/dated-acm}
}
""",
                encoding="utf-8",
            )

            summary = normalize_all(dbs, ("acm",))

            self.assertEqual(
                summary[0]["normalized_file"],
                str(directory / "results-30.08.2026-normalized.csv"),
            )
            self.assertTrue(raw_path.is_file())

    def test_acm_normalizer_preserves_url(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_acm_normalizer_test_") as temporary:
            directory = Path(temporary)
            input_path = directory / "results-30.08.2026.bib"
            input_path.write_text(
                """@inproceedings{example,
title = {An ACM paper},
doi = {10.1000/acm},
year = {2024},
url = {https://doi.org/10.1000/acm}
}
""",
                encoding="utf-8",
            )
            output = directory / "results-30.08.2026-normalized.csv"
            count = normalize_acm(input_path, output)

            self.assertEqual(count, 1)
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["url"], "https://doi.org/10.1000/acm")


if __name__ == "__main__":
    unittest.main()
