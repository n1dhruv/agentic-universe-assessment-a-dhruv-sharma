# Phase 6: Correctness and Repeatability Verification

Status: Not started. Target: 75 minutes. Dependencies: Phases 1–5.

## Outcome

Evidence that the core meets the contract on known examples and varied generated inputs.

## Test strategy

Use small, readable fixtures with independently calculated answers for exact correctness. Add meaningful tests alongside earlier phases; this phase fills gaps and runs the complete checks.

### Focused rules

- Headers, aliases, whitespace, blank-row numbering, and rejection order.
- Valid and invalid phones, four supported date formats, enum values, and currency rounding.
- Rejected rows excluded from warning counts; null-aware merging and default handling.
- Duplicate IDs, malformed lines, unknown dispositions, and final orphan classification.
- Late customers, late call events, phone-free overrides, and timestamp ordering.
- All buckets, terminal versus successful dispositions, and success-changing overrides.
- Missing initiation, distinct daily success, latest-call selection, and IST boundaries.
- Exact output headers, ordering, decimals, booleans, empty fields, and empty reports.
- Wrong or missing keys, plaintext PII absence, and transaction rollback.

### End-to-end scenarios

1. Import seed `42` drop 1 and inspect a report before drop 2.
2. Import drop 2 and confirm late-link resolution.
3. Snapshot reports, logical database records, and counters. Re-import both drops; confirm nothing changes.
4. In a fresh database, ingest the parent data directory in the same drop order; compare all report bytes.
5. Repeat broader smoke and invariant checks with seeds `7` and `99`. Do not hardcode seed-specific totals.
6. Reopen the database in another process and generate identical reports.
7. Inject an ingestion failure and retry; compare results against an uninterrupted import.

Logical comparisons exclude incidental SQLite file layout. Seed checks are not an independent correctness oracle. Use exact fixtures for that purpose.

## Completion checks

- [ ] `python -m pytest` passes.
- [ ] All five hand-calculated expected outputs match.
- [ ] Re-ingestion and combined-versus-sequential checks pass.
- [ ] Multiple generated seeds complete without broken invariants.
- [ ] Privacy and rollback checks pass.
- [ ] Actual timings and remaining limitations are recorded.

## Evidence

Pending: record commands, pass/fail summaries, seeds, timings, and any unresolved failures. No large-dataset performance claim is required.
