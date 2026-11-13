# Assessment A: Implementation Roadmap

Build a local Python pipeline that reads messy customer and call files, stores safe records in SQLite, and writes five exact reports.

## Phase index

| Phase | Target | Status | Definition |
|---|---:|---|---|
| 1 | 30 min | Complete | [Project setup](phase-01-project-setup.md) |
| 2 | 45 min | Complete | [Storage and privacy](phase-02-storage-and-privacy.md) |
| 3 | 75 min | Complete | [Lead ingestion](phase-03-lead-ingestion.md) |
| 4 | 75 min | Complete | [Event ledger](phase-04-event-ledger.md) |
| 5 | 90 min | Complete | [Reports](phase-05-reports.md) |
| 6 | 75 min | Complete | [Verification](phase-06-verification.md) |
| 7 | 30 min | Not started | [Submission preparation](phase-07-submission.md) |

Total target: 7 focused hours, plus 1 hour for fixes. These are estimates, not recorded time. See progress.md for verified implementation status.

## Intended interfaces

Run from the project root:

```bash
python -m solution init
python -m solution ingest data/drop_1
python -m solution ingest data/drop_2
python -m solution report --out reports/
python -m pytest
```

Support `--db` and `--key-file` on pipeline commands for isolated runs. `init` creates local keys and database. A parent directory such as `data/` may also be ingested; its drops must be processed in sorted order.

## Architecture

Keep command parsing, normalization, storage/privacy, ingestion, and report calculations separate. Share one call-fact calculation layer across reports.

```text
CSV leads + JSONL events
          |
Schema validation and normalization
          |
SQLite: encrypted records + import history + quality statistics
          |
Resolve links and effective call outcomes
          |
Five report files
```

## Delivery boundaries

Complete all required core behavior. No frontend, API, Temporal, Postgres deployment, or large-dataset performance target is included. Preserve starter materials, disclose AI assistance, and prepare a private submission.

The original specification governs exact fields and rules: https://github.com/AryamannNingombam/sde-assignment-junior-2026/blob/main/assignment-a-data/README.md

## Progress protocol

The central record is [progress.md](progress.md). It tracks completion percentage, phase status, every meaningful change, fixes, unplanned work, failed attempts, verification, and blockers. Update it after each work batch and before handing work back.

Mark phases `In progress` or `Complete` only as work advances. Tick completion checks only after verification. Add actual commands and results to each phase's evidence section. Keep this index and the central tracker synchronized. Phase 7 closes only after a clean-checkout rehearsal.

## Phase 3 delivery

Customer-only imports are implemented. Follow [Phase 3 self-test commands](phase-03-lead-ingestion.md) and use `ingest --leads-only` explicitly. Full call-event ingestion is implemented in Phase 4 and report generation in Phase 5. Current verified completion is recorded in [progress.md](progress.md).

## Phase 4 delivery

Default `ingest` now handles customer and call-event files. See [Phase 4](phase-04-event-ledger.md) for tests and expected counts, and [SQLite inspection](check-database.md) for read-only database commands. Phase 5 report generation is now complete; Phase 6 verification is now complete; Phase 7 remains Not started.

## Phase 5 delivery

The five report files are implemented. See [Phase 5](phase-05-reports.md) for plain-language explanations, exact fixture coverage, commands, and sample counts. Latest sample artifacts are under `reports/phase5-demo/` and are excluded from Git. Phase 6 has now been separately authorized and completed; stop before Phase 7 until requested.

## Phase 6 delivery

The full suite passes 99 tests, including three fresh-seed subprocess scenarios. See [Phase 6 evidence and commands](phase-06-verification.md) for measured results, failure recovery, privacy scope, and limitations. No application code changed during verification. Phase 7 remains Not started.
