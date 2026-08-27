from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

SLR_DIR = Path(__file__).resolve().parents[2]
if str(SLR_DIR) not in sys.path:
    sys.path.insert(0, str(SLR_DIR))

from scripts.normalize_common import normalize_database
from scripts.pipeline_lib import make_dedup_key, normalize_content_type, normalize_match_text, write_csv


class NormalizationTests(unittest.TestCase):
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
        self.assertEqual(make_dedup_key("", ""), ("title", ""))

    def test_normalizer_applies_content_type_allowlist(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_normalizer_test_") as temporary:
            directory = Path(temporary)
            fields = ["EID", "Title", "Year", "DOI", "Document Type", "Link"]
            write_csv(
                directory / "results.csv",
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

            output, count = normalize_database("scopus", directory)

            self.assertEqual(count, 1)
            self.assertEqual(output.name, "normalized.csv")
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row["title"] for row in rows], ["An article"])

    def test_normalizer_rejects_record_without_title_or_doi(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_normalizer_test_") as temporary:
            directory = Path(temporary)
            fields = ["Title", "Year", "DOI", "Document Type", "Link"]
            write_csv(
                directory / "results.csv",
                fields,
                [
                    {
                        "Title": "   ",
                        "Year": "2024",
                        "DOI": "",
                        "Document Type": "Article",
                        "Link": "",
                    }
                ],
            )

            output, count = normalize_database("scopus", directory)

            self.assertEqual(count, 0)
            with output.open(encoding="utf-8-sig", newline="") as handle:
                self.assertEqual(list(csv.DictReader(handle)), [])

    def test_acm_normalizer_preserves_url(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_acm_normalizer_test_") as temporary:
            directory = Path(temporary)
            fields = [
                "source_row",
                "entry_type",
                "title",
                "year",
                "doi",
                "document_type",
                "publisher",
                "url",
            ]
            write_csv(
                directory / "results.csv",
                fields,
                [
                    {
                        "source_row": "1",
                        "entry_type": "inproceedings",
                        "title": "An ACM paper",
                        "year": "2024",
                        "doi": "10.1000/acm",
                        "document_type": "Conference paper",
                        "publisher": "ACM",
                        "url": "https://doi.org/10.1000/acm",
                    }
                ],
            )

            output, count = normalize_database("acm", directory)

            self.assertEqual(count, 1)
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["url"], "https://doi.org/10.1000/acm")


if __name__ == "__main__":
    unittest.main()
