#!/usr/bin/env python3
"""Run all database normalizers followed by global deduplication."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.normalize import normalize_all
from scripts.normalize_common import SPECS
from scripts.pipeline_lib import PipelineError, file_sha256
from scripts.strip_duplicates import SOURCE_PRIORITY, strip_duplicates


def run_pipeline(dbs_dir: Path) -> dict[str, object]:
    dbs_dir = dbs_dir.resolve()
    inputs: list[dict[str, str]] = []

    for database in SOURCE_PRIORITY:
        database_dir = dbs_dir / database
        input_path = database_dir / SPECS[database].input_filename
        if database == "acm":
            input_path = database_dir / "results.bib"
        inputs.append(
            {
                "database": database,
                "path": str(input_path),
                "sha256": file_sha256(input_path),
            }
        )

    normalization_summary = normalize_all(dbs_dir, SOURCE_PRIORITY)
    deduplication_summary, duplicate_groups = strip_duplicates(dbs_dir)
    manifest = {
        "pipeline_version": 3,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "source_priority": list(SOURCE_PRIORITY),
        "normalization": (
            "Each database normalizer applies its configured content-type allowlist; "
            "raw exports remain unchanged."
        ),
        "deduplication_rule": {
            "primary_field": "doi",
            "fallback_field": "title",
            "same_doi_different_title": "duplicate",
            "same_title_different_doi": "not duplicate",
        },
        "inputs": inputs,
        "normalization_summary": normalization_summary,
        "deduplication_summary": deduplication_summary,
        "duplicate_groups": duplicate_groups,
    }
    manifest_path = dbs_dir / "run_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize all configured database exports and deduplicate them."
    )
    parser.add_argument(
        "--dbs-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "dbs",
        help="Directory containing the database folders (default: slr/dbs)",
    )
    args = parser.parse_args()
    try:
        manifest = run_pipeline(args.dbs_dir)
    except PipelineError as exc:
        print(f"run_pipeline.py: error: {exc}", file=sys.stderr)
        return 2

    total_normalized = sum(
        int(item["records_written"]) for item in manifest["normalization_summary"]
    )
    total_deduplicated = sum(
        int(item["kept_records"]) for item in manifest["deduplication_summary"]
    )
    print("SLR pipeline complete:")
    print(f"- Records after database normalization/filtering: {total_normalized}")
    print(f"- Records after DOI/title deduplication: {total_deduplicated}")
    print(f"- Run manifest: {args.dbs_dir.resolve() / 'run_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
