# Normalize and deduplicate database exports

Normalize every database from the repository root with the central normalizer:

```sh
python slr/scripts/normalize.py
```

ACM exports are provided as BibTeX. Normalize the ACM export with:

```sh
python slr/scripts/normalize.py acm
```

This reads `slr/dbs/acm/results-<date>.bib` and writes the normalized
`slr/dbs/acm/results-<date>-normalized.csv` file. It writes only title, DOI, year,
and URL. The entry type is used only for filtering. Abstracts, publisher data,
citation keys, entry types, and other fields are intentionally omitted.

Each database-local normalizer reads its own dated export, applies its
document-type allowlist, and writes a filtered `results-<date>-normalized.csv`.
The source export is never modified. Web of Science Excel input requires
LibreOffice.

Then remove duplicates globally:

```sh
python slr/scripts/deduplicate.py
```

This writes `results-<date>-deduplicated.csv` inside each database directory and
writes the unified audit file `slr/dbs/results-<date>-duplicates.csv`.
Deduplication uses the `DATABASE_ORDER` in `slr/scripts/common.py` and DOI
precedence: records with
the same non-empty DOI are duplicates even when titles differ; records with different
DOIs are not duplicates even when titles match. Records without a DOI fall back to a
normalized title comparison. Survivor priority is Scopus, Web of Science, IEEE,
Springer, then ACM; file order breaks ties within one database.
Records without both a DOI and a usable title are rejected during normalization.

The duplicate audit reports document title, DOI, matching basis, source
database, source rows, and year. Document type metadata is intentionally omitted
from this audit.

Title normalization used for the no-DOI fallback decodes HTML entities, removes
markup, applies Unicode NFKC and case folding, changes punctuation to spaces, and
collapses whitespace. DOI normalization removes DOI URL wrappers and case-folds the
identifier. Matching-only normalized values are not written to normalized CSV files.
