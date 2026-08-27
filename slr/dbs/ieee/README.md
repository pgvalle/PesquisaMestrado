# IEEE Xplore export

IEEE Xplore provides the search results as a CSV export. The structured
Advanced Search configuration and its broader `All Metadata` scope are
documented below.

## Files

- `results.csv`: raw IEEE Xplore export; record count varies with each query export.
- `../../scripts/normalize.py`: converts the raw export to the common SLR schema.
- `normalized.csv`: normalized records used by the global deduplication stage.
- `deduplicated.csv`: records remaining after global DOI/title deduplication.

## Normalize

Run from the repository root:

```sh
python slr/scripts/normalize.py ieee
```

The raw export is not modified. The normalizer expects these IEEE columns:

| Common field | IEEE Xplore column |
|---|---|
| Title | `Document Title` |
| Year | `Publication Year` |
| DOI | `DOI` |
| Document type | `Document Identifier` |
| URL | `PDF Link` |

It also adds `database` and `source_row`. DOI values are reduced to a bare DOI when
the export contains a DOI URL. Normalization keeps only `IEEE Journals`, `IEEE
Conferences`, `IEEE Books`, and `IEEE Early Access Articles`. Matching-only
normalized values are not written.

Records are retained when `Document Identifier` is `IEEE Journals`,
`IEEE Conferences`, `IEEE Books`, or `IEEE Early Access Articles`.

## Search Query

See the [docs](https://ieeexplore.ieee.org/Xplorehelp/searching-ieee-xplore/advanced-search) for advanced search.
The search search uses the `All Metadata` specifier by default, which is broader than a strict title, abstract, and keyword search.

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
