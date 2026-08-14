# Springer Nature Link export

Springer Nature Link provides the search results as a CSV export. The current
export includes the discipline-filtered result set. The search expression,
discipline filters, and broad full-document Keywords scope are documented
below.

## Files

- `results.csv`: canonical raw Springer export; record count varies with each query export.
- `results.csv.bak`: retained pre-cleanup export from before the canonical title cleanup.
- `normalize.py`: converts the raw export to the common SLR schema.
- `normalized.csv`: normalized records used by the global deduplication stage.
- `deduplicated.csv`: records remaining after global DOI/title deduplication.

## Normalize

Run from the repository root:

```sh
python slr/dbs/springer/normalize.py
```

The raw export is not modified. The normalizer expects these Springer columns:

| Common field | Springer column |
|---|---|
| Title | `Item Title` |
| Authors | `Authors` |
| Year | `Publication Year` |
| DOI | `Item DOI` |
| Document type | `Content Type` |
| URL | `URL` |

It also adds `database` and `source_row`. DOI values are reduced to a bare DOI when
the export contains a DOI URL. Normalization keeps only `Article`, `Conference
paper`, `Chapter`, and `Book` records. Matching-only normalized values are not
written.

## Pipeline

Springer records are retained when `Content Type` is `Article`, `Conference
paper`, `Chapter`, or `Book`. Run the complete configured pipeline with:

```sh
python slr/scripts/run_pipeline.py
```

The canonical export was cleaned only by replacing `&#xa0;` with spaces and
`&amp;` with `&` in title cells. The source field values and column structure
were otherwise preserved. Springer’s Keywords search is broader than a strict
title, abstract, and keyword search because terms may occur in the body of a
document.

## Search Strategy

### Database and search mode

Springer Nature Link, using the Advanced Search form.

### Interface limitation

Springer Nature Link does not provide a command-style advanced query language
comparable to Scopus or Web of Science in the form used here. The search is
entered through form fields.

### Field configuration

- Keywords: enter the full Boolean search expression below.
- Title: leave blank.
- Author(s) or Editor(s): leave blank.
- In Journal(s): leave blank.
- Date Published: leave unrestricted unless a date restriction is part of the review protocol.

### Keywords field search query

```text
("reactive programming" OR "reactive languages" OR "synchronous programming" OR "synchronous languages" OR "structured concurrency" OR "functional reactive programming" OR FRP)
AND
("embedded system" OR "embedded systems" OR "embedded device" OR "embedded devices" OR microcontroller OR microcontrollers OR "single-board computer" OR "single-board computers" OR Arduino OR ESP32 OR "Raspberry Pi" OR "resource-constrained")
```

## Historical Snapshot

The 2026-08-07 canonical export contained 877 records. These counts are
historical and change when the database query is rerun.

### Historical content-type inventory

| `Content Type` | Count |
|---|---:|
| Conference paper | 351 |
| Article | 262 |
| Chapter | 251 |
| Reference work entry | 6 |
| Living reference work entry | 6 |
| Book | 1 |
| **Total** | **877** |

### Historical pipeline results

- Content-type filtering excluded 12 records: 6 reference work entries and 6 living reference work entries.
- The former title-and-authors deduplication removed 8 records.
- Books and chapters were retained by the filtering allowlist.

### Historical title cleanup

The canonical `results.csv` export was cleaned in the `Item Title` field:

- 35 cells changed.
- 58 occurrences of `&#xa0;` were replaced with ordinary spaces.
- 4 occurrences of `&amp;` were replaced with ampersands (`&`).
- No target entities remained after cleanup.
- Column names, column order, and content-type counts were unchanged.

The raw filtered export before title cleanup is retained as `results.csv.bak`.

The changed title rows in the historical export were:

1. Row 2: Accident Detection and Emergency Support System for Scooters Based on Edge AI Technology
2. Row 6: Asynchronous Reactive Programming with Modal Types in Haskell
3. Row 8: Writing Internet of Things Applications with Task Oriented Programming
4. Row 13: Mimosa: A Language for Asynchronous Implementation of Embedded Systems Software
5. Row 22: Communication for Task-Oriented Systems with Edge Devices
6. Row 27: Reducing the Power Consumption of IoT with Task-Oriented Programming
7. Row 28: Towards Formal Verification of Hybrid Synchronous Programs with Refinement Types
8. Row 39: Dynamic Resource Manager for Automating Deployments in the Computing Continuum
9. Row 44: A Comprehensive Framework for Turn-Taking Evaluation in Multi-agent Systems: Rotational Periodicity for Scalable Coordination Analysis
10. Row 45: Digital Twins: a Briefing for Formalists
11. Row 47: Quality management approach considering sustainability aspects within the design of wind turbines based on a literature review to explore the state of the art
12. Row 53: Automatic Screening of Invasive Coronary Angiography Images Using Swin Transformer
13. Row 80: Integrating Dual Strengths: A Hybrid Architecture Merging Decentralized Trust with Server-Side Efficiency for Enhanced Secure Transactions
14. Row 83: An Intermediate Program Representation for Optimizing Stream-Based Languages
15. Row 90: An Energy Consumption Model to Change the TBFC Model of the IoT
16. Row 113: A Modular Orthogonal Integration of Operational and Prescriptive Timing Requirements Using TASTD
17. Row 114: Dynamic Composition and Concurrency in I/O Automata: The Ioa++ Framework
18. Row 131: Hardware Implementation of OCaml Using a Synchronous Functional Language
19. Row 141: Shelley: A Framework for Model Checking Call Ordering on Hierarchical Systems
20. Row 145: Actors Upgraded for Variability, Adaptability, and Determinism
21. Row 166: Specification-Based Monitoring in C++
22. Row 167: MIMOS: A Deterministic Model for the Design and Update of Real-Time Systems
23. Row 170: Cause-Effect Reaction Latency in Real-Time Systems
24. Row 310: Environment-Model Based Testing with Differential Evolution in an Industrial Setting
25. Row 348: A Parametric Dataflow Model for the Speed and Distance Monitoring in Novel Train Control Systems
26. Row 372: Intellectual Property (IP) Integration Approach for Data-Flow Parallel Embedded Systems
27. Row 388: Programming with Actors in Java 8
28. Row 489: Bisimulation conversion and verification procedure for goal-based control systems
29. Row 507: AdaStreams: A Type-Based Programming Extension for Stream-Parallelism with Ada 2005
30. Row 530: MARTE vs. AADL for Discrete-Event and Discrete-Time Domains
31. Row 559: Memory-efficient multithreaded code generation from Simulink for heterogeneous MPSoC
32. Row 784: PARADISE: Design Environment for Para llel & Dis tributed, E mbedded Real-Time Systems
33. Row 804: Compositionality in dataflow synchronous languages: specification & code generation
34. Row 862: Formal semantics for Ward & Mellor's transformation schemas and the specification of fault-tolerant systems
35. Row 863: Formal Semantics for Ward & Mellor’s Transformation Schemas

### Discipline filters

After executing the Boolean search, results were limited to:

- Computer science
- Engineering
- Science, humanities and social sciences, multidisciplinary
- Mathematics

These discipline filters are part of the executed search strategy but are not
encoded in the Boolean query above. They must be reapplied in the Springer
Nature Link interface to reproduce the filtered result set. The canonical
export is expected to change when the query is rerun.

### Field-scope note

The Springer Nature Link Keywords field is broader than a title, abstract, and
keywords-only search. It searches across the document, including title,
abstract, and body/full-text content.

### Comparability consequences

- This search is likely to be broader and noisier than Scopus `TITLE-ABS-KEY`.
- A paper may be retrieved because one of the terms appears somewhere in the body text even when it is not a central topic.
- This limitation should be documented in the review methodology when comparing results across databases.

### Suggested methodology description

- Database: Springer Nature Link
- Field: Keywords (full-document search)
- Discipline filters: Computer science; Engineering; Science, humanities and social sciences, multidisciplinary; Mathematics

Search string:

```text
("reactive programming" OR "reactive languages" OR "synchronous programming" OR "synchronous languages" OR "structured concurrency" OR "functional reactive programming" OR FRP)
AND
("embedded system" OR "embedded systems" OR "embedded device" OR "embedded devices" OR microcontroller OR microcontrollers OR "single-board computer" OR "single-board computers" OR Arduino OR ESP32 OR "Raspberry Pi" OR "resource-constrained")
```
