# Web of Science export

Web of Science Core Collection provides the current export as an Excel
workbook. The search formulation and the Topic-field comparability caveat are
documented below.

## Files

- `results.xls`: raw Web of Science export; record count varies with each query export.
- `../../scripts/normalize.py`: converts the workbook to the common SLR schema.
- `normalized.csv`: normalized records used by the global deduplication stage.
- `deduplicated.csv`: records remaining after global DOI/title deduplication.

## Normalize

Run from the repository root:

```sh
python slr/scripts/normalize.py wos
```

The normalizer uses the first worksheet and requires LibreOffice (`libreoffice`
or `soffice`) on `PATH` to convert the workbook to CSV. The raw workbook is not
modified.

The expected field mapping is:

| Common field | Web of Science column |
|---|---|
| Title | `Article Title` |
| Year | `Publication Year` |
| DOI | `DOI Link` |
| Document type | `Document Type` |
| URL | `Web of Science Record` |

It also adds `database` and `source_row`. DOI values are reduced to a bare DOI when
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

Compact copy/paste version:

```text
TS=("reactive programming" OR "reactive languages" OR "synchronous programming" OR "synchronous languages" OR "structured concurrency" OR "functional reactive programming" OR FRP) AND TS=("embedded system" OR "embedded systems" OR "embedded device" OR "embedded devices" OR microcontroller OR microcontrollers OR "single-board computer" OR "single-board computers" OR Arduino OR ESP32 OR "Raspberry Pi" OR "resource-constrained")
```
