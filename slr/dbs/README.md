# Normalize and deduplicate database exports

Run the normalizer in each database directory from the repository root:

```sh
python SLR/dbs/scopus/normalize.py
python SLR/dbs/wos/normalize.py
python SLR/dbs/ieee/normalize.py
python SLR/dbs/springer/normalize.py
```

ACM exports are provided as BibTeX. Convert the ACM export to a spreadsheet
with:

```sh
python slr/dbs/acm/normalize.py
```

This reads `slr/dbs/acm/results.bib` and writes `slr/dbs/acm/results.csv`.
The ACM converter includes only fields populated for every current entry:
source row, source ID, entry type, title, year, document type, and publisher.
The source ID is the BibTeX citation key. Abstracts and partially populated
fields are intentionally omitted.

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
