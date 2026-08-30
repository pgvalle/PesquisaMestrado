#!/usr/bin/env python3
"""Run all database normalizers followed by global deduplication."""

from __future__ import annotations

import argparse
from importlib import import_module
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.normalize import normalize_all
from scripts.common import DATABASE_ORDER, PipelineError, file_sha256, find_dated_input
from scripts.deduplicate import strip_duplicates


def run_pipeline(dbs_dir: Path) -> dict[str, object]:
    dbs_dir = dbs_dir.resolve()
    input_paths: dict[str, Path] = {
        database: find_dated_input(
            dbs_dir / database,
            import_module(f"dbs.{database}.normalize").INPUT_SUFFIX,
        )
        for database in DATABASE_ORDER
    }
    result_stems = {path.stem for path in input_paths.values()}
    if len(result_stems) != 1:
        names = ", ".join(sorted(result_stems))
        raise PipelineError(
            "All database exports must share one dated result stem; found: " + names
        )
    result_stem = next(iter(result_stems))
    inputs: list[dict[str, str]] = []

    for database in DATABASE_ORDER:
        input_path = input_paths[database]
        inputs.append(
            {
                "database": database,
                "path": str(input_path),
                "sha256": file_sha256(input_path),
            }
        )

    normalization_summary = normalize_all(dbs_dir, DATABASE_ORDER)
    normalized_paths = {
        str(item["database"]): Path(str(item["normalized_file"]))
        for item in normalization_summary
    }
    deduplication_summary, duplicate_groups = strip_duplicates(
        dbs_dir, normalized_paths
    )
    manifest_path = dbs_dir / f"{result_stem}-manifest.json"
    manifest = {
        "pipeline_version": 3,
        "manifest_file": str(manifest_path),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "source_priority": list(DATABASE_ORDER),
        "normalization": (
            "Each database normalizer applies its configured content-type allowlist; "
            "raw exports remain unchanged."
        ),
        "deduplication_rule": {
            "primary_field": "doi",
            "fallback_field": "title",
            "missing_both": "rejected during normalization",
            "same_doi_different_title": "duplicate",
            "same_title_different_doi": "not duplicate",
        },
        "inputs": inputs,
        "normalization_summary": normalization_summary,
        "deduplication_summary": deduplication_summary,
        "duplicate_groups": duplicate_groups,
    }
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
        print(f"run.py: error: {exc}", file=sys.stderr)
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
    print(f"- Run manifest: {manifest['manifest_file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
