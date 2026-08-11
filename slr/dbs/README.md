# Normalize and deduplicate database exports

Run the normalizer in each database directory from the repository root:

```sh
python SLR/dbs/scopus/normalize.py
python SLR/dbs/wos/normalize.py
python SLR/dbs/ieee/normalize.py
python SLR/dbs/springer/normalize.py
```

Each command reads that directory's `results.csv` or `results.xls` and writes
`normalized.csv`. The source export is never modified. Web of Science `.xls` input
requires LibreOffice.

Then remove duplicates globally:

```sh
python SLR/scripts/strip_duplicates.py
```

This writes `deduplicated.csv` inside each database directory and writes the unified
audit file `SLR/dbs/duplicates.csv`. A duplicate requires both normalized title and
normalized authors to be equal. Rows missing either value are retained. Survivor
priority is Scopus, Web of Science, IEEE, then Springer; file order breaks ties within
one database.

The normalization used for matching decodes HTML entities, removes markup, applies
Unicode NFKC and case folding, changes punctuation to spaces, and collapses whitespace.
It does not perform fuzzy matching or infer that initials and full author names identify
the same person.
