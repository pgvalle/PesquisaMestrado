# ACM export

ACM Digital Library provides the search results as BibTeX rather than as a
table. The ACM-specific normalizer is `slr/dbs/acm/normalize.py`.

## Files

- `results-<date>.bib`: raw ACM BibTeX export.
- `normalize.py`: maps the BibTeX export to the shared output columns.
- `results-<date>-normalized.csv`: ACM records retained for global deduplication.
- `results-<date>-deduplicated.csv`: ACM records remaining after global deduplication.

## Normalize

Run from the repository root:

```sh
python slr/dbs/acm/normalize.py
```

The raw BibTeX export is not modified. The normalizer reads
`slr/dbs/acm/results-<date>.bib` and writes the filtered common-schema
`slr/dbs/acm/results-<date>-normalized.csv` as UTF-8 with a BOM.

## Field Mapping

The normalizer writes only the following four fields. The entry type is used
internally for filtering and is not emitted.

| Output field | BibTeX input | Handling |
|---|---|---|
| `title` | `title` | Written for every current entry |
| `year` | `year` | Written for every current entry |
| `doi` | `doi` | Optional; blank when absent |
| `url` | `url` | Written when present |

Only `Article` and `Conference paper` entry types are retained.

The filtered `results-<date>-normalized.csv` uses the shared schema:

```text
title, doi, year, url
```

To use another file or output location:

```sh
python slr/dbs/acm/normalize.py /path/to/results-<date>.bib /path/to/results-<date>-normalized.csv
```

ACM records with `Article` and `Conference paper` entry types are retained. The
proceedings-volume record is excluded because it is not an individual paper.

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
