#!/usr/bin/env python3
"""Run content filtering followed by cross-database deduplication."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.deduplicate import run_deduplication
from scripts.filter_content import run_filter
from scripts.pipeline_lib import (
    PipelineError,
    default_config_path,
    default_output_root,
    file_sha256,
    load_source_specs,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the reproducible SLR filter-then-deduplicate pipeline."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=default_config_path(),
        help="Pipeline JSON configuration (default: scripts/pipeline_config.json)",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=default_output_root(),
        help="Pipeline output directory (default: SLR/pipeline_output)",
    )
    return parser.parse_args()


def run_pipeline(config_path: Path, output_root: Path) -> dict[str, Any]:
    config, specs = load_source_specs(config_path)
    filter_summary = run_filter(config_path, output_root)
    deduplication_summary = run_deduplication(config_path, output_root)

    manifest = {
        "pipeline_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "configuration_file": str(config_path.resolve()),
        "source_priority": config["source_priority"],
        "deduplication_rule": {
            "fields": ["title", "authors"],
            "normalization": (
                "HTML entities decoded; markup removed for the key only; Unicode NFKC; "
                "Unicode case-folding; non-alphanumeric characters replaced by spaces; "
                "whitespace collapsed"
            ),
            "missing_field_behavior": (
                "Records missing a normalized title or authors value are retained and not matched"
            ),
        },
        "inputs": [
            {
                "source": spec.key,
                "database": spec.display_name,
                "path": str(spec.input_path),
                "sha256": file_sha256(spec.input_path),
            }
            for spec in specs
        ],
        "filter_summary": filter_summary,
        "deduplication_summary": deduplication_summary,
    }

    reports_dir = output_root.resolve() / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = reports_dir / "run_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    args = _parse_args()
    try:
        manifest = run_pipeline(args.config, args.output_root)
    except PipelineError as exc:
        print(f"run_pipeline.py: error: {exc}", file=sys.stderr)
        return 2

    total_input = sum(int(item["input_records"]) for item in manifest["filter_summary"])
    total_filtered = sum(int(item["kept_records"]) for item in manifest["filter_summary"])
    total_deduplicated = sum(
        int(item["kept_records"]) for item in manifest["deduplication_summary"]
    )
    print("SLR pipeline complete:")
    print(f"- Input records: {total_input}")
    print(f"- After content filtering: {total_filtered}")
    print(f"- After title+authors deduplication: {total_deduplicated}")
    print(f"- Separate outputs: {args.output_root.resolve() / 'deduplicated'}")
    print(f"- Audit reports: {args.output_root.resolve() / 'reports'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
