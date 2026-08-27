# ACM export

ACM Digital Library provides the search results as BibTeX rather than as a
table. The ACM-specific converter is `slr/scripts/bib_to_csv.py`.

## Files

- `results.bib`: raw ACM BibTeX export.
- `results.csv`: spreadsheet-friendly ACM conversion.
- `../../scripts/normalize.py`: converts BibTeX and writes the filtered common-schema output.
- `normalized.csv`: ACM records retained for global deduplication.
- `deduplicated.csv`: ACM records remaining after global deduplication.

## Normalize

Run from the repository root:

```sh
python slr/scripts/normalize.py acm
```

The raw BibTeX export is not modified. The converter reads
`slr/dbs/acm/results.bib` and writes `slr/dbs/acm/results.csv` plus the filtered
common-schema `slr/dbs/acm/normalized.csv`. Both CSV files are UTF-8 with a BOM
so they open correctly in Excel and LibreOffice.

## Field Mapping

The converter maps the BibTeX input to the following output fields. Generated
fields are not database identifiers.

| Output field | BibTeX input | Handling |
|---|---|---|
| `source_row` | Entry order | Generated for provenance |
| `entry_type` | Entry type (`@article`, `@inproceedings`, etc.) | Written in lowercase |
| `document_type` | Entry type | Mapped to `Article` or `Conference paper`; `@proceedings` is excluded |
| `title` | `title` | Written for every current entry |
| `year` | `year` | Written for every current entry |
| `doi` | `doi` | Optional; blank when absent |
| `publisher` | `publisher` | Written for every current entry |
| `database` | None | Generated as `acm` in `normalized.csv` |
| `url` | `url` | Written when present |

The filtered `normalized.csv` uses the common schema:

```text
database, source_row, title, year, doi, document_type, url
```

To use another file or output location:

```sh
python slr/scripts/bib_to_csv.py /path/to/export.bib /path/to/results.csv
```

ACM normalized records retain `Article` and `Conference paper` document types.
The proceedings-volume record is excluded because it is not an individual
paper.

ACM participates in global deduplication at the lowest source priority, after
Springer.

## Search query

```text
(
    Title:(
        "reactive programming"
        OR "reactive languages"
        OR "synchronous programming"
        OR "synchronous languages"
        OR "structured concurrency"
        OR "functional reactive programming"
        OR FRP
    )
    OR
    Abstract:(
        "reactive programming"
        OR "reactive languages"
        OR "synchronous programming"
        OR "synchronous languages"
        OR "structured concurrency"
        OR "functional reactive programming"
        OR FRP
    )
    OR
    Keyword:(
        "reactive programming"
        OR "reactive languages"
        OR "synchronous programming"
        OR "synchronous languages"
        OR "structured concurrency"
        OR "functional reactive programming"
        OR FRP
    )
)
AND
(
    Title:(
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
    OR
    Abstract:(
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
    OR
    Keyword:(
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
)
```
