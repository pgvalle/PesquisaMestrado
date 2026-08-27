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

## Scope

The review considers studies that present, use, or evaluate a reactive
programming language, framework, or library for embedded systems. Final study
selection also considers:

- Availability of an implementation for a common embedded platform, such as
  Arduino, ESP32, or Raspberry Pi.
- Documentation quality.
- Suitability for the case studies defined in the research project.

For each selected study, the review extracts:

- Reactive paradigm.
- Language, library, or tool.
- Target platform.
- Evaluation method.
- Reported benefits.
- Reported limitations.
- Research opportunities.

## General search query

```text
(
  "reactive programming" OR "reactive languages"
  OR "synchronous programming" OR "synchronous languages"
  OR "structured concurrency"
  OR "functional reactive programming" OR FRP
) AND (
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

## Deduplication Rule

The current pipeline uses DOI precedence:

- Records with the same DOI are duplicates even if their titles differ.
- Records with different DOIs are not duplicates even if their titles match.
- Records without a DOI use normalized document title as a fallback.

## Pipeline

Run the complete normalization and deduplication workflow from the repository
root:

```sh
python slr/scripts/run.py
```

The central normalizer applies each database's configured content-type
allowlist while writing `normalized.csv`. The raw exports remain unchanged.
To run normalization without deduplication, use
`python slr/scripts/normalize.py`; database-specific commands are documented in
the corresponding database READMEs.

The pipeline keeps outputs separated by database and writes run-specific counts
and input hashes to `slr/dbs/run_manifest.json`. Counts are deliberately
generated at runtime rather than treated as constants in documentation.

The implementation and test details are documented in
[scripts/README.md](scripts/README.md). The normalized-schema and global audit
commands are documented in [dbs/README.md](dbs/README.md).
