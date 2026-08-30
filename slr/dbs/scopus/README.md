# Scopus export

Scopus provides the search results as a CSV export. The search formulation and
the subject-area exclusions used for this export are documented below.

## Files

- `results-<date>.csv`: raw Scopus export; record count varies with each query export.
- `../../scripts/normalize.py`: converts the raw export to the common SLR schema.
- `results-<date>-normalized.csv`: normalized records used by the global deduplication stage.
- `results-<date>-deduplicated.csv`: records remaining after global DOI/title deduplication.

## Normalize

Run from the repository root:

```sh
python slr/scripts/normalize.py scopus
```

The raw export is not modified. The normalizer expects these Scopus columns:

| Normalized output | Scopus column |
|---|---|
| Title | `Title` |
| Year | `Year` |
| DOI | `DOI` |
| URL | `Link` |

`Document Type` is used only for filtering and is not written to the normalized
file.

DOI values are reduced to a bare DOI when
the export contains a DOI URL. Normalization keeps only `Article`, `Conference
paper`, `Book chapter`, and `Book` records. Matching-only normalized values are
not written.

Records are retained when `Document Type` is `Article`, `Conference
paper`, `Book chapter`, or `Book`. Run the complete configured pipeline with:

```sh
python slr/scripts/run.py
```

## Search query

```text
TITLE-ABS-KEY(
    "reactive programming"
    OR "reactive languages"
    OR "synchronous programming"
    OR "synchronous languages"
    OR "structured concurrency"
    OR "functional reactive programming"
    OR FRP
)
AND
TITLE-ABS-KEY(
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

## Additional subject-area filtering

After running the query, the retrieved results were filtered by excluding:

- Materials Science
- Physics and Astronomy

This filter was part of the executed search strategy but is not encoded in the
query. Apply these exclusions in Scopus to reproduce the original result set.
