# Normalize and deduplicate database exports

Normalize every database from the repository root with the central normalizer:

```sh
python slr/scripts/normalize.py
```

ACM exports are provided as BibTeX. Convert the ACM export to a spreadsheet
with:

```sh
python slr/scripts/normalize.py acm
```

This reads `slr/dbs/acm/results.bib` and writes `slr/dbs/acm/results.csv`.
The ACM converter includes fields populated for every entry plus an optional
DOI column: source row, entry type, title, year, DOI, document type, and
publisher. Abstracts and other partially populated fields are intentionally
omitted.

Each command reads that directory's `results.csv` or `results.xls`, applies its
document-type allowlist, and writes a filtered `normalized.csv`. The source export
is never modified. Web of Science `.xls` input requires LibreOffice.

Then remove duplicates globally:

```sh
python slr/scripts/strip_duplicates.py
```

This writes `deduplicated.csv` inside each database directory and writes the unified
audit file `slr/dbs/duplicates.csv`. Deduplication uses DOI precedence: records with
the same non-empty DOI are duplicates even when titles differ; records with different
DOIs are not duplicates even when titles match. Records without a DOI fall back to a
normalized title comparison. Survivor priority is Scopus, Web of Science, IEEE,
Springer, then ACM; file order breaks ties within one database.

The duplicate audit reports document title, authors, DOI, matching basis, source
database, source rows, and year. Document type metadata is intentionally omitted
from this audit.

Title normalization used for the no-DOI fallback decodes HTML entities, removes
markup, applies Unicode NFKC and case folding, changes punctuation to spaces, and
collapses whitespace. DOI normalization removes DOI URL wrappers and case-folds the
identifier. Matching-only normalized values are not written to normalized CSV files.
