# Phase 4: Event Ledger and Late Linking

Status: Complete. Target: 75 minutes. Dependencies: Phases 1–3.

## Outcome

A deduplicated event history that handles out-of-order delivery and customers arriving later.

## Work

1. Read nonempty JSONL lines and count each physical input line once per source. Count malformed JSON and missing event IDs as malformed.
2. Apply event ID deduplication before link and disposition classification. First observed event wins; duplicate deliveries increment the duplicate counter.
3. Store unique original events encrypted and append-only, including currently unmatched or unknown-disposition events.
4. Normalize UTC, explicit-offset, and naive timestamps. Naive timestamps mean IST; store comparable instants internally.
5. Resolve ordinary events through workflow and normalized phone HMAC. Resolve overrides through workflow and call ID, regardless of line arrival order.
6. Reconsider unresolved links over all stored data after later imports. Do not edit original ledger bodies to attach leads.
7. Compute final-state orphan counts before unknown-disposition counts, respecting the contract's classification precedence. Match disposition codes against the supplied workflow catalogue.
8. Keep source-level line, malformed, and duplicate counts separate from classifications that can change after new data arrives.

## Completion checks

- [x] Duplicate IDs within and across drops count once in the ledger.
- [x] Overrides arriving before ordinary call events eventually link.
- [x] Events become report-eligible when a later lead arrives.
- [x] Permanent orphans remain excluded from business reports.
- [x] Unknown dispositions do not influence call outcomes.
- [x] Final orphan counts shrink correctly after late linking.
- [x] Re-importing a drop changes no counts or ledger records.

## Evidence

Verified on 2026-11-13:

- Before structural move: 55 tests passed in 0.27 seconds. After moving file/transaction ownership into shared ingestion: the same 55 tests passed in 0.28 seconds.
- After Phase 4 behavior and tests: `.venv/bin/python -m pytest -q` reported 83 passed in 0.57 seconds. This includes 28 new event tests and the retained earlier coverage, with the old CLI refusal expectation intentionally updated to full-import support.
- Imported seed-42 drop 1 into `var/phase4-demo.sqlite3`: 4247 nonblank event lines, 4 malformed, 83 duplicates, 4160 unique stored events; 3027 eligible, 1123 orphans, 10 unknown dispositions.
- Imported drop 2: 4498 lines, 4 malformed, 154 duplicates. Final totals: 8745 event lines, 8 malformed, 237 duplicates, 8500 unique stored events; 8020 eligible, 462 orphans, 18 unknown dispositions.
- Resolved 910 earlier orphan events after the second drop. All 4160 earlier encrypted ledger bodies remained byte-for-byte unchanged.
- Drop 2 ingestion plus final classification took 0.4464 seconds in the measured local run. This is a small-dataset observation, not a large-dataset performance claim.
- Repeated parent-directory ingestion skipped all 8 source files, returned zero new-work counts, and left the full logical database dump unchanged.
- A separately initialized combined-directory database produced the same resolved events, quality counts, source counters, and rejections as sequential imports.
- Existing Phase 3 user/demo databases were not modified by the Phase 4 smoke runs.
- No Phase 5 report writer or call-bucket calculations were implemented.

## Simple explanation

Phase 3 made the customer list. Phase 4 reads the call diary. One event says a call started, another says it connected, and another records the outcome.

We save each unique event once. Broken JSON is counted and skipped. Events without a matching customer wait in derived quarantine; they become usable once a later upload provides the customer. Supervisor corrections have no phone, so they find the customer through other events on the same workflow and call ID. Unknown outcome codes are kept for inspection but excluded from usable events.

The original diary stays encrypted and unchanged. Matching and quarantine are recalculated separately using everything imported so far.

## Self-test commands

```bash
cd /home/dhruv/assessment-a
.venv/bin/python -m pytest tests/test_events.py -q
.venv/bin/python -m pytest -q
.venv/bin/python -m solution init --db var/my-phase4.sqlite3 --key-file var/my-phase4.keys.json
.venv/bin/python -m solution ingest data/drop_1 --db var/my-phase4.sqlite3 --key-file var/my-phase4.keys.json
.venv/bin/python -m solution ingest data/drop_2 --db var/my-phase4.sqlite3 --key-file var/my-phase4.keys.json
```

Expected: 28 event tests and 83 total tests pass. On a fresh database, drop 1 imports 5 files and drop 2 imports 3 files. The final `quality` object reports 8745 event lines, 8 malformed events, 237 duplicate deliveries, 462 remaining orphans, and 18 unknown outcomes. The final `event_state` reports 8020 eligible events.

Unlike Phase 3, the default `ingest` now imports both leads and events. The optional `--leads-only` command remains supported and produces the same customer-only output as before. An existing Phase 3 database can be upgraded by running a full import: known customer files are skipped, and event files are added without recounting customer rows.

Repeat all imports:

```bash
.venv/bin/python -m solution ingest data --db var/my-phase4.sqlite3 --key-file var/my-phase4.keys.json
```

Expected: `imported_files` is 0, `skipped_files` is 8, and new-work counters are zero. The nested `quality` and `event_state` values remain the cumulative/current totals, not zeros.

Inspect SQLite with the commands in [check-database.md](check-database.md).

## Interfaces and assumptions

- `solution.ingest.ingest` coordinates lead and event files in one transaction per drop. It defaults to full ingestion; the compatibility `ingest_leads` entry point explicitly selects lead-only mode.
- `solution.events.resolve_events` returns eligible linked events with UTC-aware timestamps and an event-ID-to-reason quarantine map. It writes no database changes.
- `quality_summary` aggregates saved source counters and current final-state classifications. It returns data for inspection/future reporting; it does not write report files.
- The ledger keeps the original event body encrypted. Timestamp normalization happens during validation and when creating linked events; original timestamp strings are preserved.
- Blank JSONL lines are ignored. Invalid JSON, non-object JSON, or absent/empty/non-string event IDs count as malformed. Nonstandard JSON NaN/Infinity constants are rejected as malformed.
- Other unsupported event structures or invalid timestamps abort the drop with a PII-free error rather than inventing unspecified quality categories. A valid duplicate ID is skipped before that extra structural validation.
- Ordinary events must match their own workflow and phone. Only overrides link by workflow and call ID. A call ID pointing to multiple customers does not provide an unambiguous override owner; keep that override orphaned.
- Orphan classification precedes unknown disposition classification. Unknown codes remain in the encrypted ledger but not the eligible stream.
- Rejection-reason maps include observed reasons only. Repeated input files contribute no counters again.
- Missing call initiation is not an event-linking failure. Phase 5 separately requires initiation before counting a call in reports.
- Stop here until the user requests Phase 5.
