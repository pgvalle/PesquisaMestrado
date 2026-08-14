# Systematic literature review

This directory contains the database exports, preprocessing pipeline, audit
outputs, and documentation for the systematic literature review.

Database-specific information belongs in the corresponding README:

- [ACM Digital Library](dbs/acm/README.md)
- [IEEE Xplore](dbs/ieee/README.md)
- [Scopus](dbs/scopus/README.md)
- [Springer Nature Link](dbs/springer/README.md)
- [Web of Science](dbs/wos/README.md)

Those READMEs contain each source's search strategy, field scope, query,
filters, export format, normalization mapping, historical inventory, and
source-specific preprocessing notes. They are the authoritative location for
database-level information.

## Historical Snapshot

The historical preprocessing snapshot was recorded on **2026-08-07**. Counts
from that snapshot are audit information, not fixed expectations for future
queries. New database exports can change all counts.

The former four-source snapshot contained 1,411 records before filtering. The
former content-type filtering stage retained 1,375 records. The historical
title-and-authors deduplication stage retained 1,294 records.

ACM was not included in that historical four-source total. ACM is now handled
separately through the converter documented in its database README.

### Historical normalized aggregate

This cross-database inventory grouped source labels only for reporting:

| Group | Count |
|---|---:|
| Conference paper / Proceedings paper | 718 |
| Article | 382 |
| Book chapter / Chapter | 264 |
| Conference review | 22 |
| Article; Proceedings Paper hybrid | 7 |
| Reference work entry | 6 |
| Living reference work entry | 6 |
| Book | 4 |
| Review | 2 |
| **Total** | **1,411** |

For this historical inventory only:

- Springer `Chapter` and Scopus `Book chapter` were grouped as book chapters.
- Web of Science `Proceedings Paper`, IEEE `IEEE Conferences`, and `Conference paper` were grouped as conference papers/proceedings papers.
- IEEE `IEEE Journals` was grouped as articles.
- Web of Science hybrid records remained separate to prevent double-counting.

## Current Deduplication Rule

The current pipeline uses DOI precedence:

- A non-empty DOI is the primary identity.
- Records with the same DOI are duplicates even if their titles differ.
- Records with different DOIs are not duplicates even if their titles match.
- Records without a DOI use normalized document title as a fallback.
- A record without both DOI and title raises `AssertionError` and stops processing.
- Matching-only normalized values are not written to normalized CSV files.

The current rule is intentionally distinct from the historical
title-and-authors rule used for the 2026-08-07 snapshot.

## Pipeline

Run database normalizers as described in the database READMEs. Then run the
normalization and deduplication workflow from the repository root:

Each database normalizer applies its configured content-type allowlist while
writing `normalized.csv`. The raw exports remain unchanged.

```sh
python slr/scripts/run_pipeline.py
```

The pipeline keeps outputs separated by database and writes run-specific counts
and input hashes to `slr/dbs/run_manifest.json`. Counts are deliberately
generated at runtime rather than treated as constants in documentation.

The implementation and test details are documented in
[scripts/README.md](scripts/README.md). The normalized-schema and global audit
commands are documented in [dbs/README.md](dbs/README.md).

## Historical Validation

The historical run validated that:

- All four source, filtered, and deduplicated outputs parsed successfully.
- Filter and duplicate audit counts matched the source-to-output differences.
- Books and chapters were not removed by content-type filtering.
- The former title-and-authors key did not appear more than once in the historical deduplicated outputs.

These checks describe the historical run. The current tests use synthetic
fixtures to verify behavior independently of live database result counts,
including DOI precedence, title fallback, and the missing-identity assertion.
