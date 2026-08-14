from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

SLR_DIR = Path(__file__).resolve().parents[2]
if str(SLR_DIR) not in sys.path:
    sys.path.insert(0, str(SLR_DIR))

from scripts.normalize_common import NORMALIZED_COLUMNS
from scripts.pipeline_lib import write_csv
from scripts.strip_duplicates import SOURCE_PRIORITY, strip_duplicates


class NormalizedDeduplicationTests(unittest.TestCase):
    def test_global_deduplication_and_audit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_normalized_test_") as temporary:
            dbs = Path(temporary)
            for database in SOURCE_PRIORITY:
                (dbs / database).mkdir()

            def row(database: str, number: int, title: str, authors: str, doi: str) -> dict[str, str]:
                values = {column: "" for column in NORMALIZED_COLUMNS}
                values.update(
                    database=database,
                    source_row=str(number),
                    title=title,
                    authors=authors,
                    doi=doi,
                )
                return values

            write_csv(
                dbs / "scopus" / "normalized.csv",
                NORMALIZED_COLUMNS,
                [
                    row("scopus", 2, "Shared", "Author", "10.1000/shared"),
                    row("scopus", 3, "No author", "", ""),
                ],
            )
            write_csv(
                dbs / "wos" / "normalized.csv",
                NORMALIZED_COLUMNS,
                [
                    row("wos", 2, "Different title", "Other Author", "10.1000/shared"),
                    row("wos", 3, "Shared", "Other Author", "10.1000/other"),
                ],
            )
            for database in ("ieee", "springer", "acm"):
                write_csv(dbs / database / "normalized.csv", NORMALIZED_COLUMNS, [])

            summaries, group_count = strip_duplicates(dbs)

            self.assertEqual(group_count, 1)
            self.assertEqual([item["duplicates_removed"] for item in summaries], [0, 1, 0, 0, 0])
            self.assertEqual(len(self._read(dbs / "scopus" / "deduplicated.csv")), 2)
            self.assertEqual(len(self._read(dbs / "wos" / "deduplicated.csv")), 1)
            duplicate = self._read(dbs / "duplicates.csv")[0]
            self.assertEqual(duplicate["databases_found"], "scopus; wos")
            self.assertEqual(duplicate["kept_database"], "scopus")
            self.assertEqual(duplicate["occurrence_count"], "2")
            self.assertEqual(duplicate["doi"], "10.1000/shared")
            self.assertEqual(duplicate["match_basis"], "doi")

    @staticmethod
    def _read(path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
