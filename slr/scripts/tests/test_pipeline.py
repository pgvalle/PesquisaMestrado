from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

SLR_DIR = Path(__file__).resolve().parents[2]
if str(SLR_DIR) not in sys.path:
    sys.path.insert(0, str(SLR_DIR))

from scripts.deduplicate import run_deduplication
from scripts.filter_content import run_filter
from scripts.pipeline_lib import normalize_content_type, normalize_match_text, write_csv


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


class PipelineTests(unittest.TestCase):
    def test_filter_then_deduplicate_keeps_separate_database_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_pipeline_test_") as temporary:
            root = Path(temporary)
            config_path = root / "pipeline_config.json"
            output_root = root / "output"

            scopus_fields = ["Title", "Authors", "Document Type", "Other"]
            scopus_rows = [
                {
                    "Title": "Shared <i>Title</i>",
                    "Authors": "Smith, J.",
                    "Document Type": "Article",
                    "Other": "scopus winner",
                },
                {
                    "Title": "A Useful Book",
                    "Authors": "Writer A.",
                    "Document Type": "Book",
                    "Other": "book must survive",
                },
                {
                    "Title": "Review Record",
                    "Authors": "Reviewer R.",
                    "Document Type": "Review",
                    "Other": "remove",
                },
                {
                    "Title": "Presentation Record",
                    "Authors": "Presenter P.",
                    "Document Type": "Presentation",
                    "Other": "remove unknown label",
                },
            ]
            springer_fields = ["Item Title", "Authors", "Content Type", "Other"]
            springer_rows = [
                {
                    "Item Title": "shared title",
                    "Authors": "SMITH J",
                    "Content Type": "Conference paper",
                    "Other": "lower-priority duplicate",
                },
                {
                    "Item Title": "A Useful Chapter",
                    "Authors": "Writer B",
                    "Content Type": "Chapter",
                    "Other": "chapter must survive",
                },
                {
                    "Item Title": "Reference Entry",
                    "Authors": "Editor E",
                    "Content Type": "Reference work entry",
                    "Other": "remove",
                },
                {
                    "Item Title": "Missing Author Record",
                    "Authors": "",
                    "Content Type": "Article",
                    "Other": "retain conservatively",
                },
            ]

            write_csv(root / "scopus.csv", scopus_fields, scopus_rows)
            write_csv(root / "springer.csv", springer_fields, springer_rows)
            config_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "source_priority": ["scopus", "springer"],
                        "sources": {
                            "scopus": {
                                "display_name": "Scopus",
                                "input": "scopus.csv",
                                "output_filename": "scopus.csv",
                                "title_column": "Title",
                                "authors_column": "Authors",
                                "content_type_column": "Document Type",
                                "allowed_content_types": [
                                    "Article",
                                    "Conference paper",
                                    "Book chapter",
                                    "Book",
                                ],
                            },
                            "springer": {
                                "display_name": "Springer",
                                "input": "springer.csv",
                                "output_filename": "springer.csv",
                                "title_column": "Item Title",
                                "authors_column": "Authors",
                                "content_type_column": "Content Type",
                                "allowed_content_types": [
                                    "Article",
                                    "Conference paper",
                                    "Chapter",
                                    "Book",
                                ],
                            },
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            filter_summary = run_filter(config_path, output_root)
            self.assertEqual(
                [(item["source"], item["kept_records"], item["excluded_records"]) for item in filter_summary],
                [("scopus", 2, 2), ("springer", 3, 1)],
            )

            dedup_summary = run_deduplication(config_path, output_root)
            self.assertEqual(
                [
                    (
                        item["source"],
                        item["kept_records"],
                        item["duplicates_removed"],
                        item["records_without_complete_title_author_key"],
                    )
                    for item in dedup_summary
                ],
                [("scopus", 2, 0, 0), ("springer", 2, 1, 1)],
            )

            scopus_output = self._read(output_root / "deduplicated" / "scopus.csv")
            springer_output = self._read(output_root / "deduplicated" / "springer.csv")
            self.assertEqual([row["Title"] for row in scopus_output], ["Shared <i>Title</i>", "A Useful Book"])
            self.assertEqual(
                [row["Item Title"] for row in springer_output],
                ["A Useful Chapter", "Missing Author Record"],
            )
            self.assertFalse((output_root / "deduplicated" / "all_databases.csv").exists())

            removed_springer = self._read(
                output_root / "reports" / "duplicates_removed_by_source" / "springer.csv"
            )
            self.assertEqual(len(removed_springer), 1)
            self.assertEqual(removed_springer[0]["Pipeline Duplicate Of Source"], "scopus")

    @staticmethod
    def _read(path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
