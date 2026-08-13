# Scopus export

Scopus provides the search results as a CSV export. The search formulation and
the subject-area exclusions used for this export are documented in
`search_strategy.txt`.

## Files

- `results.csv`: raw Scopus export; 344 records in the current dataset.
- `normalize.py`: converts the raw export to the common SLR schema.
- `normalized.csv`: normalized records used by the global deduplication stage.
- `deduplicated.csv`: records remaining after global title-and-author deduplication.

## Normalize

Run from the repository root:

```sh
python slr/dbs/scopus/normalize.py
```

The raw export is not modified. The normalizer expects these Scopus columns:

| Common field | Scopus column |
|---|---|
| Source ID | `EID` |
| Title | `Title` |
| Authors | `Authors` |
| Year | `Year` |
| DOI | `DOI` |
| Publication title | `Source title` |
| Document type | `Document Type` |
| URL | `Link` |

It also adds `database`, `source_row`, `normalized_title`, and
`normalized_authors`. DOI values are reduced to a bare DOI when the export
contains a DOI URL.

## Pipeline

Scopus records are retained when `Document Type` is `Article`, `Conference
paper`, `Book chapter`, or `Book`. Run the complete configured pipeline with:

```sh
python slr/scripts/run_pipeline.py
```

The Scopus search scope, including the exclusion of Materials Science and
Physics and Astronomy, is documented in `search_strategy.txt`.
