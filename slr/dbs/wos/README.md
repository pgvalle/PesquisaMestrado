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
| Authors | `Authors` |
| Year | `Publication Year` |
| DOI | `DOI Link` |
| Document type | `Document Type` |
| URL | `Web of Science Record` |

It also adds `database` and `source_row`. DOI values are reduced to a bare DOI when
the export contains a DOI URL. Normalization keeps only `Article`, `Proceedings
Paper`, `Article; Proceedings Paper`, `Book`, and `Book Chapter` records.
Matching-only normalized values are not written.

## Pipeline

Web of Science records are retained when `Document Type` is `Article`,
`Proceedings Paper`, `Article; Proceedings Paper`, `Book`, or `Book Chapter`.
Run the complete configured pipeline with:

```sh
python slr/scripts/run_pipeline.py
```

The source search field is `TS=` (Topic), which also includes Keywords Plus;
this makes it slightly broader than Scopus `TITLE-ABS-KEY`. See the search
strategy below for the exact query and methodological note.

## Search Strategy

### Database

Web of Science Core Collection.

### Search mode

Advanced Search.

### Field scope

`TS=` (Topic), which searches title, abstract, author keywords, and Keywords
Plus.

### Comparability note

Web of Science Topic search is slightly broader than Scopus `TITLE-ABS-KEY`
because `TS=` also includes Keywords Plus.

### Search query

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

### Notes

- `TS=` is the practical Web of Science equivalent of a broad topic search.
- It is not perfectly field-equivalent to Scopus `TITLE-ABS-KEY` because Keywords Plus is included.

## Historical Snapshot

The 2026-08-07 export contained 113 records. These counts are historical and
change when the database query is rerun.

### Historical document-type inventory

| `Document Type` | Count |
|---|---:|
| Proceedings Paper | 70 |
| Article | 35 |
| Article; Proceedings Paper | 7 |
| Review | 1 |
| **Total** | **113** |

### Historical pipeline results

- Content-type filtering excluded 1 record: 1 review.
- The former title-and-authors deduplication removed 59 records.
- The hybrid `Article; Proceedings Paper` value was retained by the filtering allowlist.
