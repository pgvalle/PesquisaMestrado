# ACM export

ACM Digital Library provides the search results as BibTeX rather than as a
table. The ACM-specific converter is `bib_to_csv.py`. Convert the export from
the repository root with:

```sh
python slr/dbs/acm/normalize.py
```

This reads `slr/dbs/acm/results.bib` and writes both `slr/dbs/acm/results.csv`
and the filtered common-schema `slr/dbs/acm/normalized.csv`.
The CSV is UTF-8 with a BOM so it opens correctly in Excel and LibreOffice.
It contains fields populated for every entry in the current ACM export plus an
optional DOI column: source row, entry type, title, year, DOI, document type,
and publisher. DOI is blank when the BibTeX entry does not provide one.
Abstracts and other partially populated fields are intentionally omitted.

### Omitted BibTeX fields

The converter does not export these fields:

- `abstract`: omitted by design, even when present.
- `author`: not present on every entry.
- `address`, `articleno`, `booktitle`, `isbn`, `issn`, `issue_date`, `journal`,
  `keywords`, `location`, `month`, `number`, `numpages`, `pages`, `series`,
  `url`, and `volume`: not present on every entry.
- `bibtex_key`: not exported; DOI is the cross-database identifier, with
  `source_row` retained only for provenance.

`booktitle` and `journal` are publication venues, not document titles, so they
are not included in the review CSV.

ACM normalized records retain `Article` and `Conference paper` document types.
The proceedings-volume record is excluded because it is not an individual
paper. ACM participates in global deduplication at the lowest source priority,
after Springer.

To use another file or output location:

```sh
python slr/dbs/acm/normalize.py --input /path/to/export.bib --output /path/to/results.csv
```

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
