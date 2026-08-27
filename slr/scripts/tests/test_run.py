from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


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


if __name__ == "__main__":
    unittest.main()
