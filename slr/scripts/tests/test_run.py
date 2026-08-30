from __future__ import annotations

from importlib import import_module
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SLR_DIR = REPOSITORY_ROOT / "slr"
if str(SLR_DIR) not in sys.path:
    sys.path.insert(0, str(SLR_DIR))

from scripts.common import DATABASE_ORDER, write_csv
from scripts.run import run_pipeline


class RunCliTests(unittest.TestCase):
    def test_documented_run_command_can_load(self) -> None:
        result = subprocess.run(
            [sys.executable, "slr/scripts/run.py", "--help"],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Normalize all configured database exports", result.stdout)

    def test_pipeline_uses_local_normalizers_and_global_deduplicator(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_run_test_") as temporary:
            dbs = Path(temporary)
            shared_values = {
                "document_type": "Article",
                "title": "The same article",
                "doi": "10.1000/shared",
                "year": "2024",
                "url": "https://example.test/shared",
            }

            for database in DATABASE_ORDER[:-1]:
                directory = dbs / database
                directory.mkdir()
                module = import_module(f"dbs.{database}.normalize")
                values = {
                    **shared_values,
                    "document_type": module.ALLOWED_CONTENT_TYPES[0],
                }
                source = {
                    (
                        input_column[0]
                        if isinstance(input_column, tuple)
                        else input_column
                    ): values[output_column]
                    for output_column, input_column in module.INPUT_COLUMNS.items()
                }
                write_csv(
                    directory / "results-30.08.2026.csv",
                    list(source),
                    [source],
                )

            acm_directory = dbs / "acm"
            acm_directory.mkdir()
            (acm_directory / "results-30.08.2026.bib").write_text(
                """@article{shared,
title = {The same article},
doi = {10.1000/shared},
year = {2024},
url = {https://example.test/shared}
}
""",
                encoding="utf-8",
            )

            manifest = run_pipeline(dbs)

            self.assertEqual(
                [item["database"] for item in manifest["normalization_summary"]],
                list(DATABASE_ORDER),
            )
            self.assertEqual(
                sum(int(item["records_written"]) for item in manifest["normalization_summary"]),
                5,
            )
            self.assertEqual(manifest["duplicate_groups"], 1)
            self.assertEqual(
                sum(int(item["kept_records"]) for item in manifest["deduplication_summary"]),
                1,
            )


if __name__ == "__main__":
    unittest.main()
