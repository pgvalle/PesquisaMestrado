# Scopus export

Scopus provides the search results as a CSV export. The search formulation and
the subject-area exclusions used for this export are documented below.

## Files

- `results.csv`: raw Scopus export; record count varies with each query export.
- `../../scripts/normalize.py`: converts the raw export to the common SLR schema.
- `normalized.csv`: normalized records used by the global deduplication stage.
- `deduplicated.csv`: records remaining after global DOI/title deduplication.

## Normalize

Run from the repository root:

```sh
python slr/scripts/normalize.py scopus
```

The raw export is not modified. The normalizer expects these Scopus columns:

| Common field | Scopus column |
|---|---|
| Title | `Title` |
| Authors | `Authors` |
| Year | `Year` |
| DOI | `DOI` |
| Document type | `Document Type` |
| URL | `Link` |

It also adds `database` and `source_row`. DOI values are reduced to a bare DOI when
the export contains a DOI URL. Normalization keeps only `Article`, `Conference
paper`, `Book chapter`, and `Book` records. Matching-only normalized values are
not written.

## Pipeline

Scopus records are retained when `Document Type` is `Article`, `Conference
paper`, `Book chapter`, or `Book`. Run the complete configured pipeline with:

```sh
python slr/scripts/run_pipeline.py
```

The Scopus search scope, including the exclusion of Materials Science and
Physics and Astronomy, is documented below.

## Search Strategy

### Database

Scopus.

### Search mode

Advanced Search.

### Field scope

`TITLE-ABS-KEY`, which searches document title, abstract, and keywords.

### Search query

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

Compact copy/paste version:

```text
TITLE-ABS-KEY("reactive programming" OR "reactive languages" OR "synchronous programming" OR "synchronous languages" OR "structured concurrency" OR "functional reactive programming" OR FRP) AND TITLE-ABS-KEY("embedded system" OR "embedded systems" OR "embedded device" OR "embedded devices" OR microcontroller OR microcontrollers OR "single-board computer" OR "single-board computers" OR Arduino OR ESP32 OR "Raspberry Pi" OR "resource-constrained")
```

### Additional subject-area filtering

After running the query, the retrieved results were filtered by excluding:

- Materials Science
- Physics and Astronomy

This filter was part of the executed search strategy but is not encoded in the
query. Apply these exclusions in Scopus to reproduce the original result set.

### Notes

- This is the cleanest direct translation of the generic query when the goal is to search title, abstract, and keywords.
- FRP is a broad acronym and may retrieve unrelated results. It can be retained initially and evaluated for noise during screening.

## Historical Snapshot

The 2026-08-07 export contained 344 records. These counts are historical and
change when the database query is rerun.

### Historical document-type inventory

| `Document Type` | Count |
|---|---:|
| Conference paper | 227 |
| Article | 78 |
| Conference review | 22 |
| Book chapter | 13 |
| Book | 3 |
| Review | 1 |
| **Total** | **344** |

### Historical pipeline results

- Content-type filtering excluded 23 records: 22 conference reviews and 1 review.
- The former title-and-authors deduplication removed 14 records.
- Books and chapters were retained by the filtering allowlist.
