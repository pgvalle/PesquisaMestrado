# ACM export

ACM Digital Library provides the search results as BibTeX rather than as a
table. The ACM-specific converter is `bib_to_csv.py`. Convert the export from
the repository root with:

```sh
python slr/dbs/acm/normalize.py
```

This reads `slr/dbs/acm/results.bib` and writes `slr/dbs/acm/results.csv`.
The CSV is UTF-8 with a BOM so it opens correctly in Excel and LibreOffice.
It contains only fields populated for every entry in the current ACM export:
source row, source ID, entry type, title, year, document type, and publisher.
The source ID is the BibTeX citation key. Abstracts and partially populated
fields are intentionally omitted.

To use another file or output location:

```sh
python slr/dbs/acm/normalize.py --input /path/to/export.bib --output /path/to/results.csv
```
