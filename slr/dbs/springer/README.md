# Springer Nature Link export

Springer Nature Link provides the search results as a CSV export. The current
export includes the discipline-filtered result set. The search expression,
discipline filters, and broad full-document Keywords scope are documented
below.

## Files

- `results-<date>.csv`: canonical raw Springer export; record count varies with each query export.
- `results-<date>.csv.bak`: retained pre-cleanup export from before the canonical title cleanup.
- `../../scripts/normalize.py`: converts the raw export to the common SLR schema.
- `results-<date>-normalized.csv`: normalized records used by the global deduplication stage.
- `results-<date>-deduplicated.csv`: records remaining after global DOI/title deduplication.

## Normalize

Run from the repository root:

```sh
python slr/scripts/normalize.py springer
```

The raw export is not modified. The normalizer expects these Springer columns:

| Normalized output | Springer column |
|---|---|
| Title | `Item Title` |
| Year | `Publication Year` |
| DOI | `Item DOI` |
| URL | `URL` |

`Content Type` is used only for filtering and is not written to the normalized
file.

DOI values are reduced to a bare DOI when
the export contains a DOI URL. Normalization keeps only `Article`, `Conference
paper`, `Chapter`, and `Book` records. Matching-only normalized values are not
written.

Springer records are retained when `Content Type` is `Article`, `Conference
paper`, `Chapter`, or `Book`

The canonical export was cleaned only by replacing `&#xa0;` with spaces and
`&amp;` with `&` in title cells. The source field values and column structure
were otherwise preserved. Springer’s Keywords search is broader than a strict
title, abstract, and keyword search because terms may occur in the body of a
document.

## Search Strategy

### Field configuration

- Keywords: enter the full Boolean search expression below.
- Title: leave blank.
- Author(s) or Editor(s): leave blank.
- In Journal(s): leave blank.
- Date Published: leave unrestricted unless a date restriction is part of the review protocol.

### Keywords field search query

```text
("reactive programming" OR "reactive languages" OR "synchronous programming" OR "synchronous languages" OR "structured concurrency" OR "functional reactive programming" OR FRP)
AND
("embedded system" OR "embedded systems" OR "embedded device" OR "embedded devices" OR microcontroller OR microcontrollers OR "single-board computer" OR "single-board computers" OR Arduino OR ESP32 OR "Raspberry Pi" OR "resource-constrained")
```

The Keywords field is broader than a title, abstract, and
keywords-only search. It searches across the document, including title,
abstract, and body/full-text content.

### Discipline filters

After executing the Boolean search, results were limited to:

- Computer science
- Engineering
- Mathematics

These discipline filters are part of the executed search strategy but are not encoded in the Boolean query above.
