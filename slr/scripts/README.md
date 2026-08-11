# SLR filtering and deduplication pipeline

This directory contains a reproducible two-stage pipeline for the database exports in
`PesquisaMestrado/SLR`.

The pipeline **does not merge the databases into one bibliographic file**. Every stage
writes one output CSV per database and preserves that database's original columns.

## Pipeline stages

### 1. Content-type filtering

```sh
python scripts/filter_content.py
```

The script reads the configured Scopus, Web of Science, IEEE Xplore, and Springer
exports. It writes separate files to:

```text
pipeline_output/filtered/scopus.csv
pipeline_output/filtered/wos.csv
pipeline_output/filtered/ieee.csv
pipeline_output/filtered/springer.csv
```

Filtering uses explicit per-database allowlists in `pipeline_config.json`:

| Database | Content types kept |
|---|---|
| Scopus | Article, Conference paper, Book chapter, Book |
| Web of Science | Article, Proceedings Paper, Article; Proceedings Paper, Book, Book Chapter |
| IEEE Xplore | IEEE Journals, IEEE Conferences, IEEE Books, IEEE Early Access Articles |
| Springer | Article, Conference paper, Chapter, Book |

This keeps books and book chapters. Reviews, conference reviews, reference-work
entries, presentations, and any other unlisted or unknown content labels are excluded.
Unknown values are excluded deliberately rather than silently accepted.

Excluded rows remain available separately by source under:

```text
pipeline_output/reports/excluded_by_source/
```

The filter summary is written to:

```text
pipeline_output/reports/filter_summary.csv
```

### 2. Title-and-authors deduplication

```sh
python scripts/deduplicate.py
```

This stage reads the separate stage-1 files, compares records globally, and writes
separate survivor files to:

```text
pipeline_output/deduplicated/scopus.csv
pipeline_output/deduplicated/wos.csv
pipeline_output/deduplicated/ieee.csv
pipeline_output/deduplicated/springer.csv
```

A duplicate is defined by the pair:

```text
(normalized title, normalized authors)
```

The normalization rule is deterministic:

1. Decode HTML/XML entities for matching only.
2. Remove markup tags for matching only.
3. Apply Unicode NFKC normalization.
4. Apply Unicode-aware lowercase conversion (`casefold`).
5. Replace punctuation and other non-alphanumeric characters with spaces.
6. Collapse repeated whitespace.
7. Require both normalized title and normalized authors to be non-empty.

Original title and author values are never rewritten by deduplication. A record with a
missing title or missing authors is retained conservatively and is not matched against
other records.

This is an exact normalized-key rule. It does not use fuzzy title matching, DOI
fallbacks, or guessed author identities. Consequently, exports that represent the
same authors differently (for example, full names versus initials) may remain as
separate records. This limitation is intentional and makes the procedure reproducible.

When a key occurs more than once, the first record according to this source priority is
kept:

```text
Scopus -> Web of Science -> IEEE Xplore -> Springer
```

Within one database, the first occurrence in file order is kept. Change
`source_priority` in `pipeline_config.json` to use a different deterministic priority.

Removed duplicates are audited separately per source under:

```text
pipeline_output/reports/duplicates_removed_by_source/
```

The deduplication summary is written to:

```text
pipeline_output/reports/deduplication_summary.csv
```

## Run the complete pipeline

From `PesquisaMestrado/SLR`:

```sh
python scripts/run_pipeline.py
```

This runs content filtering first and deduplication second. It also writes a manifest
containing source hashes, rules, priority, and record counts:

```text
pipeline_output/reports/run_manifest.json
```

## Current reference run

Using the four exports present on 2026-08-07:

| Stage | Records |
|---|---:|
| Input | 1,411 |
| After content-type filtering | 1,375 |
| After title-and-authors deduplication | 1,294 |

Filtering excluded 36 records: 23 from Scopus, 1 from Web of Science, 0 from IEEE
Xplore, and 12 from Springer. Deduplication removed 81 records: 14 from Scopus, 59
from Web of Science, 0 from IEEE Xplore, and 8 from Springer.

These values are a reference for the current source files, not hard-coded expectations.
The manifest records input hashes so a later run can identify changed exports.

## Requirements

- Python 3.10 or newer.
- LibreOffice (`libreoffice` or `soffice` on `PATH`) for `.xls` and `.xlsx` inputs.

No third-party Python packages are required. CSV files are read as UTF-8/UTF-8-SIG and
pipeline CSV outputs are written as UTF-8 with a BOM for spreadsheet compatibility.

LibreOffice's command-line CSV conversion exports the active/first worksheet. Excel
inputs used by this pipeline must contain their bibliographic table in that worksheet.
If LibreOffice is unavailable, export the workbook as UTF-8 CSV and update the input
path in `pipeline_config.json`.

## Configuration

`pipeline_config.json` records, for each database:

- Input path.
- Output filename.
- Title column.
- Authors column.
- Content-type column.
- Allowed content types.
- Cross-database source priority.

When adding a database, add its schema and allowlist to the configuration instead of
copying and modifying a database-specific script.

## Tests

From `PesquisaMestrado/SLR`:

```sh
python -m unittest discover -s scripts/tests -v
```

The tests verify that:

- Books and chapters survive filtering.
- Reviews, presentations, reference entries, and unknown labels are excluded.
- Matching ignores case, markup, and punctuation.
- Source priority determines which duplicate survives.
- Missing-author records are retained.
- Outputs remain separated by database.
