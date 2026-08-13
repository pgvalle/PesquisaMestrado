# IEEE Xplore export

IEEE Xplore provides the search results as a CSV export. The structured
Advanced Search configuration and its broader `All Metadata` scope are
documented in `search_strategy.txt`.

## Files

- `results.csv`: raw IEEE Xplore export; 77 records in the current dataset.
- `normalize.py`: converts the raw export to the common SLR schema.
- `normalized.csv`: normalized records used by the global deduplication stage.
- `deduplicated.csv`: records remaining after global title-and-author deduplication.

## Normalize

Run from the repository root:

```sh
python slr/dbs/ieee/normalize.py
```

The raw export is not modified. The normalizer expects these IEEE columns:

| Common field | IEEE Xplore column |
|---|---|
| Source ID | DOI, with a generated row ID when DOI is blank |
| Title | `Document Title` |
| Authors | `Authors` |
| Year | `Publication Year` |
| DOI | `DOI` |
| Publication title | `Publication Title` |
| Document type | `Document Identifier` |
| URL | `PDF Link` |

It also adds `database`, `source_row`, `normalized_title`, and
`normalized_authors`. DOI values are reduced to a bare DOI when the export
contains a DOI URL.

## Pipeline

IEEE records are retained when `Document Identifier` is `IEEE Journals`,
`IEEE Conferences`, `IEEE Books`, or `IEEE Early Access Articles`. Run the
complete configured pipeline with:

```sh
python slr/scripts/run_pipeline.py
```

The structured IEEE search uses `All Metadata`, which is broader than a strict
title, abstract, and keyword search. This limitation is documented in
`search_strategy.txt` and should be reported in the review methodology.
