# Web of Science export

Web of Science Core Collection provides the current export as an Excel
workbook. The search formulation and the Topic-field comparability caveat are
documented below.

## Files

- `results-<date>.xls`: raw Web of Science export; record count varies with each query export.
- `normalize.py`: converts the workbook and maps its columns to the common four-field schema.
- `results-<date>-normalized.csv`: normalized records used by the global deduplication stage.
- `results-<date>-deduplicated.csv`: records remaining after global DOI/title deduplication.

## Normalize

Run from the repository root:

```sh
python slr/scripts/normalize.py wos
```

To convert the workbook without running the rest of the pipeline:

```sh
python slr/dbs/wos/normalize.py results-<date>.xls results-<date>-normalized.csv
```

The normalizer extracts these source columns when available and writes
`title`, `doi`, `year`, and `url`: `Article Title`, `DOI`, `Publication Year`,
and `Web of Science Record`. `Document Type` is used only for filtering.
All other columns are ignored.

For Excel input, the normalizer uses the first worksheet and requires LibreOffice
(`libreoffice` or `soffice`) on `PATH` to convert the workbook to CSV. A CSV
export can also be passed directly. The raw export is not modified.

The expected field mapping is:

| Normalized output | Web of Science column |
|---|---|
| Title | `Article Title` |
| Year | `Publication Year` |
| DOI | `DOI` or `DOI Link` |
| URL | `Web of Science Record` |

DOI values are reduced to a bare DOI when
the export contains a DOI URL. Normalization keeps only `Article`, `Proceedings
Paper`, `Article; Proceedings Paper`, `Book`, and `Book Chapter` records.
Matching-only normalized values are not written.

Web of Science records are retained when `Document Type` is `Article`,
`Proceedings Paper`, `Article; Proceedings Paper`, `Book`, or `Book Chapter`.

## Search query

```text
TS=(
    "reactive programming"
    OR "reactive languages"
    OR "synchronous programming"
    OR "synchronous languages"
    OR "structured concurrency"
    OR "functional reactive programming"
    OR FRP
)
AND
TS=(
    "embedded system"
    OR "embedded systems"
    OR "embedded device"
    OR "embedded devices"
    OR microcontroller
    OR microcontrollers
    OR "single-board computer"
    OR "single-board computers"
    OR Arduino
    OR ESP32
    OR "Raspberry Pi"
    OR "resource-constrained"
)
```
