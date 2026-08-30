from __future__ import annotations

import csv
from importlib import import_module
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SLR_DIR = Path(__file__).resolve().parents[2]
if str(SLR_DIR) not in sys.path:
    sys.path.insert(0, str(SLR_DIR))

_wos_normalizer = import_module("dbs.wos.normalize")
from scripts.common import OUTPUT_COLUMNS

normalize = _wos_normalizer.normalize


LIBREOFFICE = shutil.which("libreoffice") or shutil.which("soffice")


@unittest.skipUnless(LIBREOFFICE, "LibreOffice is required for WOS Excel normalization")
class WosNormalizeTests(unittest.TestCase):
    def test_normalize_writes_only_requested_columns(self) -> None:
        with tempfile.TemporaryDirectory(prefix="slr_excel_test_") as temporary:
            root = Path(temporary)
            source_csv = root / "source.csv"
            with source_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(
                    [
                        "Document Type",
                        "Article Title",
                        "DOI",
                        "Publication Year",
                        "Web of Science Record",
                        "Authors",
                        "Abstract",
                    ]
                )
                writer.writerow(
                    [
                        "Proceedings Paper",
                        "An Excel article",
                        "10.1000/excel",
                        "2024",
                        "https://example.test/record",
                        "An Author",
                        "An abstract",
                    ]
                )

            profile_uri = (root / "libreoffice-profile").resolve().as_uri()
            subprocess.run(
                [
                    LIBREOFFICE,
                    f"-env:UserInstallation={profile_uri}",
                    "--headless",
                    "--convert-to",
                    "xls",
                    "--outdir",
                    str(root),
                    str(source_csv),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            source_xls = root / "source.xls"
            self.assertTrue(source_xls.is_file())

            output = root / "output.csv"
            self.assertEqual(normalize(source_xls, output), 1)
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(list(rows[0]), OUTPUT_COLUMNS)
            self.assertNotIn("document_type", rows[0])
            self.assertEqual(rows[0]["title"], "An Excel article")
            self.assertEqual(rows[0]["doi"], "10.1000/excel")
            self.assertEqual(rows[0]["year"], "2024")
            self.assertEqual(rows[0]["url"], "https://example.test/record")
            self.assertNotIn("Authors", rows[0])
            self.assertNotIn("Abstract", rows[0])
            self.assertNotIn("Document Type", rows[0])
            self.assertNotIn("Article Title", rows[0])


if __name__ == "__main__":
    unittest.main()
