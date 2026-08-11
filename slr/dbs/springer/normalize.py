#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.normalize_common import database_main

if __name__ == "__main__":
    raise SystemExit(database_main("springer"))
