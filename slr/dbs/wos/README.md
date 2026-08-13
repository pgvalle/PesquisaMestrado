# Web of Science export

Web of Science Core Collection provides the current export as an Excel
workbook. The search formulation and the Topic-field comparability caveat are
documented in `search_strategy.txt`.

## Files

- `results.xls`: raw Web of Science export; 113 records in the current dataset.
- `normalize.py`: converts the workbook to the common SLR schema.
- `normalized.csv`: normalized records used by the global deduplication stage.
- `deduplicated.csv`: records remaining after global title-and-author deduplication.

## Normalize

Run from the repository root:

```sh
python slr/dbs/wos/normalize.py
```

The normalizer uses the first worksheet and requires LibreOffice (`libreoffice`
or `soffice`) on `PATH` to convert the workbook to CSV. The raw workbook is not
modified.

The expected field mapping is:

| Common field | Web of Science column |
|---|---|
| Source ID | `UT (Unique WOS ID)` |
| Title | `Article Title` |
| Authors | `Authors` |
| Year | `Publication Year` |
| DOI | `DOI Link` |
| Publication title | `Source Title` |
| Document type | `Document Type` |
| URL | `Web of Science Record` |

It also adds `database`, `source_row`, `normalized_title`, and
`normalized_authors`. DOI values are reduced to a bare DOI when the export
contains a DOI URL.

## Pipeline

Web of Science records are retained when `Document Type` is `Article`,
`Proceedings Paper`, `Article; Proceedings Paper`, `Book`, or `Book Chapter`.
Run the complete configured pipeline with:

```sh
python slr/scripts/run_pipeline.py
```

The source search field is `TS=` (Topic), which also includes Keywords Plus;
this makes it slightly broader than Scopus `TITLE-ABS-KEY`. See
`search_strategy.txt` for the exact query and methodological note.
