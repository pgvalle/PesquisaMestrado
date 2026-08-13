# Springer Nature Link export

Springer Nature Link provides the search results as a CSV export. The current
export includes the discipline-filtered result set. The search expression,
discipline filters, and broad full-document Keywords scope are documented in
`search_strategy.txt`.

## Files

- `results.csv`: canonical raw Springer export; 877 records in the current dataset.
- `results.csv.bak`: retained pre-cleanup export from before the canonical title cleanup.
- `normalize.py`: converts the raw export to the common SLR schema.
- `normalized.csv`: normalized records used by the global deduplication stage.
- `deduplicated.csv`: records remaining after global title-and-author deduplication.

## Normalize

Run from the repository root:

```sh
python slr/dbs/springer/normalize.py
```

The raw export is not modified. The normalizer expects these Springer columns:

| Common field | Springer column |
|---|---|
| Source ID | Item DOI, with a generated row ID when DOI is blank |
| Title | `Item Title` |
| Authors | `Authors` |
| Year | `Publication Year` |
| DOI | `Item DOI` |
| Publication title | `Publication Title` |
| Document type | `Content Type` |
| URL | `URL` |

It also adds `database`, `source_row`, `normalized_title`, and
`normalized_authors`. DOI values are reduced to a bare DOI when the export
contains a DOI URL.

## Pipeline

Springer records are retained when `Content Type` is `Article`, `Conference
paper`, `Chapter`, or `Book`. Run the complete configured pipeline with:

```sh
python slr/scripts/run_pipeline.py
```

The canonical export was cleaned only by replacing `&#xa0;` with spaces and
`&amp;` with `&` in title cells. The source field values and column structure
were otherwise preserved. Springer’s Keywords search is broader than a strict
title, abstract, and keyword search because terms may occur in the body of a
document.
