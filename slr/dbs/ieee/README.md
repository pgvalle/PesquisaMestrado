# IEEE Xplore export

IEEE Xplore provides the search results as a CSV export. The structured
Advanced Search configuration and its broader `All Metadata` scope are
documented below.

## Files

- `results.csv`: raw IEEE Xplore export; record count varies with each query export.
- `normalize.py`: converts the raw export to the common SLR schema.
- `normalized.csv`: normalized records used by the global deduplication stage.
- `deduplicated.csv`: records remaining after global DOI/title deduplication.

## Normalize

Run from the repository root:

```sh
python slr/dbs/ieee/normalize.py
```

The raw export is not modified. The normalizer expects these IEEE columns:

| Common field | IEEE Xplore column |
|---|---|
| Title | `Document Title` |
| Authors | `Authors` |
| Year | `Publication Year` |
| DOI | `DOI` |
| Document type | `Document Identifier` |
| URL | `PDF Link` |

It also adds `database` and `source_row`. DOI values are reduced to a bare DOI when
the export contains a DOI URL. Normalization keeps only `IEEE Journals`, `IEEE
Conferences`, `IEEE Books`, and `IEEE Early Access Articles`. Matching-only
normalized values are not written.

## Pipeline

IEEE records are retained when `Document Identifier` is `IEEE Journals`,
`IEEE Conferences`, `IEEE Books`, or `IEEE Early Access Articles`. Run the
complete configured pipeline with:

```sh
python slr/scripts/run_pipeline.py
```

The structured IEEE search uses `All Metadata`, which is broader than a strict
title, abstract, and keyword search. This limitation is documented below and
should be reported in the review methodology.

## Search Strategy

### Database and search mode

IEEE Xplore, using Advanced Search.

Reference help section: `Searching IEEE Xplore > Advanced Search`.

Path supplied:

```text
/Xplorehelp/searching-ieee-xplore/advanced-search
```

### Structured Advanced Search configuration

#### Row 1

- Operator: None / first row
- Field: `All Metadata`
- Search text: `"reactive programming" OR "reactive languages" OR "synchronous programming" OR "synchronous languages" OR "structured concurrency" OR "functional reactive programming" OR FRP`

#### Row 2

- Operator: `AND`
- Field: `All Metadata`
- Search text: `"embedded system" OR "embedded systems" OR "embedded device" OR "embedded devices" OR microcontroller OR microcontrollers OR "single-board computer" OR "single-board computers" OR Arduino OR ESP32 OR "Raspberry Pi" OR "resource-constrained"`

### Conceptual combined query

```text
(
    "reactive programming"
    OR "reactive languages"
    OR "synchronous programming"
    OR "synchronous languages"
    OR "structured concurrency"
    OR "functional reactive programming"
    OR FRP
)
AND
(
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

### Why `All Metadata`

IEEE Xplore exposes individual searchable fields such as Document Title,
Abstract, Index Terms, and Author Keywords, but the structured Advanced Search
interface does not provide a single simple field equivalent to Scopus
`TITLE-ABS-KEY`.

`All Metadata` is therefore a practical approximation for the structured
Advanced Search interface.

### Comparability note

`All Metadata` is broader than Scopus `TITLE-ABS-KEY`. In addition to title,
abstract, and index/keyword information, metadata search can include other
bibliographic metadata. Consequently:

- The IEEE Xplore search may retrieve somewhat broader results than the Scopus search.
- This difference should be documented in the systematic-review methodology.

### Strict-equivalence alternative

If strict title, abstract, and keyword-like field control is required, IEEE
Xplore Command Search is preferable because it supports free-form field
expressions and nested Boolean concepts. The structured Advanced Search
approach above is the simpler practical version.

## Historical Snapshot

The 2026-08-07 export contained 77 records. These counts are historical and
change when the database query is rerun.

### Historical document-type inventory

| `Document Identifier` | Count |
|---|---:|
| IEEE Conferences | 70 |
| IEEE Journals | 7 |
| **Total** | **77** |

### Historical pipeline results

- Content-type filtering excluded 0 records.
- The former title-and-authors deduplication removed 0 records.
