# SLR processing scripts

Each database normalizer applies its own input mapping and content-type filter,
and the global deduplicator operates on the normalized outputs. Raw database
exports are never modified.

## Workflow

Run the complete workflow from the repository root:

```sh
python slr/scripts/run.py
```

This normalizes every database, writes each database's dated normalized CSV, then
runs global deduplication. The workflow writes:

- `slr/dbs/<database>/results-<date>-normalized.csv`: normalized records that passed the database allowlist.
- `slr/dbs/<database>/results-<date>-deduplicated.csv`: records remaining after global deduplication.
- `slr/dbs/results-<date>-duplicates.csv`: duplicate-group audit.
- `slr/dbs/results-<date>-manifest.json`: input hashes, normalization counts, deduplication counts, and rules for the run.

To run individual stages:

```sh
python slr/scripts/normalize.py
python slr/scripts/deduplicate.py
```

Pass one or more database names to normalize only those sources, for example
`python slr/scripts/normalize.py scopus ieee`.

## Normalization

Each `slr/dbs/<database>/normalize.py` reads that database's dated raw export,
applies its local input mapping and content-type allowlist, and writes the
shared normalized schema:

```text
title, doi, year, url
```

The shared columns and database order are defined in `scripts/common.py`. The original title is
preserved. Matching-only normalized values are not written. DOI URLs are
reduced to bare, case-folded DOIs. Document type is used only for each database's
local allowlist and is not emitted.

Database-specific mappings and allowlists are defined in each local normalizer:

| Database | Normalizer | Retained content types |
|---|---|---|
| Scopus | `dbs/scopus/normalize.py` | Article, Conference paper, Book chapter, Book |
| Web of Science | `dbs/wos/normalize.py` | Article, Proceedings Paper, Article; Proceedings Paper, Book, Book Chapter |
| IEEE Xplore | `dbs/ieee/normalize.py` | IEEE Journals, IEEE Conferences, IEEE Books, IEEE Early Access Articles |
| Springer | `dbs/springer/normalize.py` | Article, Conference paper, Chapter, Book |
| ACM Digital Library | `dbs/acm/normalize.py` | Article, Conference paper |

## Deduplication

Deduplication uses DOI precedence:

- A non-empty DOI is the primary identity.
- Same DOI with different titles is a duplicate.
- Same title with different DOIs is not a duplicate.
- Records without a DOI use normalized title as a fallback.
- Records without both a DOI and a usable title are rejected during normalization.

Title fallback normalization decodes HTML entities, removes markup, applies
Unicode NFKC and case-folding, replaces punctuation and other non-alphanumeric
characters with spaces, and collapses whitespace. The original title is never
rewritten.

When a duplicate group occurs, the first record according to `DATABASE_ORDER` in
`scripts/common.py` is kept:

```text
Scopus -> Web of Science -> IEEE Xplore -> Springer -> ACM
```

Within one database, file order breaks ties. The duplicate audit contains the
document title, DOI, matching basis, databases found, occurrence count,
kept database, source rows, and year. Document type is intentionally omitted.

## Requirements

- Python 3.10 or newer.
- LibreOffice (`libreoffice` or `soffice` on `PATH`) for Web of Science `.xls` input.
- No third-party Python packages.

CSV files are read as UTF-8/UTF-8-SIG and pipeline outputs are written as UTF-8
with a BOM for spreadsheet compatibility.

## Tests

Run the synthetic behavior tests with:

```sh
python -m unittest discover -s slr/scripts/tests -v
```

The tests cover:

- Title normalization behavior.
- Content-type normalization and allowlist filtering.
- DOI precedence and title fallback.
- Duplicate handling with same DOI/different title and same title/different DOI.
- ACM BibTeX normalization.
- Database-local input-column mappings and normalized output columns.
