from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

SLR_DIR = Path(__file__).resolve().parents[2]
if str(SLR_DIR) not in sys.path:
    sys.path.insert(0, str(SLR_DIR))

from scripts.common import DATABASE_ORDER, OUTPUT_COLUMNS, PipelineError, write_csv
from slr.scripts.deduplicate import strip_duplicates


class DeduplicateTests(unittest.TestCase):
    def test_global_deduplication_and_audit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_deduplicate_test_") as temporary:
            dbs = Path(temporary)
            for database in DATABASE_ORDER:
                (dbs / database).mkdir()

            def row(title: str, doi: str) -> dict[str, str]:
                values = {column: "" for column in OUTPUT_COLUMNS}
                values.update(title=title, doi=doi, year="2024")
                return values

            write_csv(
                dbs / "scopus" / "results-30.08.2026-normalized.csv",
                OUTPUT_COLUMNS,
                [
                    row("Shared", "10.1000/shared"),
                    row("No DOI", ""),
                ],
            )
            write_csv(
                dbs / "wos" / "results-30.08.2026-normalized.csv",
                OUTPUT_COLUMNS,
                [
                    row("Different title", "10.1000/shared"),
                    row("Shared", "10.1000/other"),
                ],
            )
            for database in ("ieee", "springer", "acm"):
                write_csv(
                    dbs / database / "results-30.08.2026-normalized.csv",
                    OUTPUT_COLUMNS,
                    [],
                )

            summaries, group_count = strip_duplicates(dbs)

            self.assertEqual(group_count, 1)
            self.assertEqual([item["duplicates_removed"] for item in summaries], [0, 1, 0, 0, 0])
            self.assertEqual(
                len(self._read(dbs / "scopus" / "results-30.08.2026-deduplicated.csv")),
                2,
            )
            self.assertEqual(
                len(self._read(dbs / "wos" / "results-30.08.2026-deduplicated.csv")),
                1,
            )
            duplicate = self._read(dbs / "results-30.08.2026-duplicates.csv")[0]
            self.assertNotIn("duplicate_group_id", duplicate)
            self.assertEqual(duplicate["databases_found"], "scopus; wos")
            self.assertEqual(duplicate["kept_database"], "scopus")
            self.assertEqual(duplicate["occurrence_count"], "2")
            self.assertEqual(duplicate["doi"], "10.1000/shared")
            self.assertEqual(duplicate["match_basis"], "doi")

    def test_rejects_record_without_title_or_doi(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_deduplicate_test_") as temporary:
            dbs = Path(temporary)
            for database in DATABASE_ORDER:
                (dbs / database).mkdir()
                rows = []
                if database == "scopus":
                    row = {column: "" for column in OUTPUT_COLUMNS}
                    rows.append(row)
                write_csv(
                    dbs / database / "results-30.08.2026-normalized.csv",
                    OUTPUT_COLUMNS,
                    rows,
                )

            with self.assertRaisesRegex(PipelineError, "without a title or DOI"):
                strip_duplicates(dbs)

    @staticmethod
    def _read(path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
