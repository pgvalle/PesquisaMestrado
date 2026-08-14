# ACM export

ACM Digital Library provides the search results as BibTeX rather than as a
table. The ACM-specific converter is `bib_to_csv.py`.

## Files

- `results.bib`: raw ACM BibTeX export.
- `results.csv`: spreadsheet-friendly ACM conversion.
- `normalize.py`: converts BibTeX and writes the filtered common-schema output.
- `normalized.csv`: ACM records retained for global deduplication.
- `deduplicated.csv`: ACM records remaining after global deduplication.

## Normalize

Run from the repository root:

```sh
python slr/dbs/acm/normalize.py
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
| `authors` | `author` | Author names decoded and separated with `; ` |
| `year` | `year` | Written for every current entry |
| `doi` | `doi` | Optional; blank when absent |
| `publisher` | `publisher` | Written for every current entry |
| `database` | None | Generated as `acm` in `normalized.csv` |
| `url` | `url` | Written when present |

The filtered `normalized.csv` uses the common schema:

```text
database, source_row, title, authors, year, doi, document_type, url
```

To use another file or output location:

```sh
python slr/dbs/acm/normalize.py --input /path/to/export.bib --output /path/to/results.csv
```

## Pipeline

ACM normalized records retain `Article` and `Conference paper` document types.
The proceedings-volume record is excluded because it is not an individual
paper. Run the complete configured pipeline with:

```sh
python slr/scripts/run_pipeline.py
```

ACM participates in global deduplication at the lowest source priority, after
Springer.

## Search Strategy

### Database

ACM Digital Library.

### Goal

Approximate a title, abstract, and keywords search.

### Field limitation

ACM does not provide a single direct equivalent of Scopus `TITLE-ABS-KEY` in
the same simple form. Title, Abstract, and Keyword are exposed separately.

### Preferred conceptual formulation

For each concept group, search Title OR Abstract OR Keyword. Then combine the
two concept groups with AND.

### Expanded query representation

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

### Compact representation

```text
(Title:("reactive programming" OR "reactive languages" OR "synchronous programming" OR "synchronous languages" OR "structured concurrency" OR "functional reactive programming" OR FRP) OR Abstract:("reactive programming" OR "reactive languages" OR "synchronous programming" OR "synchronous languages" OR "structured concurrency" OR "functional reactive programming" OR FRP) OR Keyword:("reactive programming" OR "reactive languages" OR "synchronous programming" OR "synchronous languages" OR "structured concurrency" OR "functional reactive programming" OR FRP))
AND
(Title:("embedded system" OR "embedded systems" OR "embedded device" OR "embedded devices" OR microcontroller OR microcontrollers OR "single-board computer" OR "single-board computers" OR Arduino OR ESP32 OR "Raspberry Pi" OR "resource-constrained") OR Abstract:("embedded system" OR "embedded systems" OR "embedded device" OR "embedded devices" OR microcontroller OR microcontrollers OR "single-board computer" OR "single-board computers" OR Arduino OR ESP32 OR "Raspberry Pi" OR "resource-constrained") OR Keyword:("embedded system" OR "embedded systems" OR "embedded device" OR "embedded devices" OR microcontroller OR microcontrollers OR "single-board computer" OR "single-board computers" OR Arduino OR ESP32 OR "Raspberry Pi" OR "resource-constrained"))
```

### Practical interface note

ACM's graphical Advanced Search interface can make cross-field OR
combinations awkward because separate Search Within rows are commonly combined
with AND.

### Fallback

If the field-specific construction is impractical in the interface, use the
Anywhere field with:

```text
("reactive programming" OR "reactive languages" OR "synchronous programming" OR "synchronous languages" OR "structured concurrency" OR "functional reactive programming" OR FRP)
AND
("embedded system" OR "embedded systems" OR "embedded device" OR "embedded devices" OR microcontroller OR microcontrollers OR "single-board computer" OR "single-board computers" OR Arduino OR ESP32 OR "Raspberry Pi" OR "resource-constrained")
```

### Fallback limitation

Anywhere is broader than a title, abstract, and keywords-only search and may
match terms occurring elsewhere in the document or full text.

### Methodological note

If the fallback is used, document that ACM was searched using a broader field
scope than Scopus `TITLE-ABS-KEY`.
