# SLR processing scripts

The central normalizer applies database-specific content-type filtering, and
the global deduplicator operates on its normalized outputs. Raw database
exports are never modified and no temporary raw-column pipeline outputs are
created.

## Workflow

Run the complete workflow from the repository root:

```sh
python slr/scripts/run_pipeline.py
```

This normalizes every database, writes each database's `normalized.csv`, then
runs global deduplication. The workflow writes:

- `slr/dbs/<database>/normalized.csv`: normalized records that passed the database allowlist.
- `slr/dbs/<database>/deduplicated.csv`: records remaining after global deduplication.
- `slr/dbs/duplicates.csv`: duplicate-group audit.
- `slr/dbs/run_manifest.json`: input hashes, normalization counts, deduplication counts, and rules for the run.

To run individual stages:

```sh
python slr/scripts/normalize.py
python slr/scripts/strip_duplicates.py
```

Pass one or more database names to normalize only those sources, for example
`python slr/scripts/normalize.py scopus ieee`.

## Normalization

The normalizer reads each database's raw `results.csv` or `results.xls`, applies
its database-specific content-type allowlist, and writes the common normalized
schema:

```text
database, source_row, title, authors, year, doi, document_type, url
```

The original title and author values are preserved. Matching-only normalized
values are not written. DOI URLs are reduced to bare, case-folded DOIs.

The allowlists are defined in `scripts/normalize_common.py`:

| Database | Retained content types |
|---|---|
| Scopus | Article, Conference paper, Book chapter, Book |
| Web of Science | Article, Proceedings Paper, Article; Proceedings Paper, Book, Book Chapter |
| IEEE Xplore | IEEE Journals, IEEE Conferences, IEEE Books, IEEE Early Access Articles |
| Springer | Article, Conference paper, Chapter, Book |
| ACM Digital Library | Article, Conference paper |

## Deduplication

Deduplication uses DOI precedence:

- A non-empty DOI is the primary identity.
- Same DOI with different titles is a duplicate.
- Same title with different DOIs is not a duplicate.
- Records without a DOI use normalized title as a fallback.

Title fallback normalization decodes HTML entities, removes markup, applies
Unicode NFKC and case-folding, replaces punctuation and other non-alphanumeric
characters with spaces, and collapses whitespace. The original title is never
rewritten.

When a duplicate group occurs, the first record according to this priority is
kept:

```text
Scopus -> Web of Science -> IEEE Xplore -> Springer -> ACM
```

Within one database, file order breaks ties. The duplicate audit contains the
document title, authors, DOI, matching basis, databases found, occurrence count,
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
- ACM BibTeX conversion.
