# Phase 6: Correctness and Repeatability Verification

Status: Complete. Target: 75 minutes. Dependencies: Phases 1–5.

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

- [x] `python -m pytest` passes.
- [x] All five hand-calculated expected outputs match.
- [x] Re-ingestion and combined-versus-sequential checks pass.
- [x] Multiple generated seeds complete without broken invariants.
- [x] Privacy and rollback checks pass.
- [x] Actual timings and remaining limitations are recorded.

## Evidence

Verified on 2026-11-13:

- Focused baseline: `.venv/bin/python -m pytest tests/test_storage.py tests/test_reports.py -q` reported 16 passed in 0.37 seconds. This includes the exact five-file hand-calculated fixture and existing privacy/rollback cases.
- Added three process-level integration tests in `tests/test_end_to_end.py`, one each for fresh seeds 42, 7, and 99. Inputs, databases, and reports are generated in pytest temporary directories; existing user artifacts remain untouched.
- Full command: `.venv/bin/python -m pytest -q --junitxml=var/phase6/verification.xml -o junit_logging=all` reported 99 passed in 17.46 seconds, with zero failures, errors, or skips.
- Structured JUnit duration: 17.452 seconds. Per-seed timings below include generation, subprocess startup, imports, repeated reports, privacy sampling, and state comparisons. They are not ingestion-only benchmarks.
- Every seed passed report-after-drop-1 checks, late linking, unchanged earlier ciphertext, replay invariance, byte-identical fresh combined imports, canonical decrypted state equality, and reporting after reopening in new processes.
- Injected an unsupported event after valid drop-2 customer and event work for seed 42. The CLI failed safely, the entire logical database matched its pre-drop state, and regenerated reports matched the partial reports exactly. Restoring the input and retrying then matched a fresh uninterrupted import.
- SQLite integrity and foreign-key checks passed. On each sequential and combined database, byte scans checked schema-marked private fields from 33 sampled leads, full and national phone forms, absent raw key material, and owner-only key permissions. Fixed known-PII fixtures also passed.
- Independent input row/line counts matched data-quality totals. Event and lead conservation, batch/customer bucket agreement, per-workflow daily/customer call totals, sort orders, masking, booleans, IST offsets, and rate formatting passed.
- No application source changed and no product bug was found in this phase.
- Raw run artifacts are ignored under `var/phase6/verification.xml` and `var/phase6/summary.json`; commit the test source and this concise evidence, not those generated artifacts.

## Measured seed results

| Seed | Unique customers | Counted calls | Stored unique events | Earlier orphans resolved | Complete scenario seconds |
|---|---:|---:|---:|---:|---:|
| 42 | 1892 | 2536 | 8500 | 910 | 5.9433 |
| 7 | 1886 | 2544 | 8561 | 951 | 5.3137 |
| 99 | 1901 | 2592 | 8690 | 1056 | 5.3537 |

All three seeds produced byte-identical five-file reports between sequential imports and fresh combined imports using independent keys. All three retained unchanged data and counters after repeat ingestion. Failure injection/retry was exercised on seed 42 only; a false value for `failure_rollback_and_retry` in another seed's raw summary means not exercised for that seed, not a failed test.

## In simple words

This phase checked the work rather than adding a feature. We made three different fake customer/call datasets and ran the program as separate terminal processes. We checked the same information gives the same answers, reading files twice adds nothing, and closing/reopening the program loses nothing.

We also deliberately broke one incoming file after some work had already happened. The program cancelled that unfinished upload. After fixing the file, retrying produced the same answers as a run that never failed.

## Commands you can run

Run the complete suite:

```bash
cd /home/dhruv/assessment-a
.venv/bin/python -m pytest -q
```

Expected: `99 passed`. The measured run took about 17 seconds on this machine; your duration can differ.

Run only the new full-pipeline checks and show their safe count/timing summaries:

```bash
.venv/bin/python -m pytest tests/test_end_to_end.py -q -s
```

Expected: one `PHASE6_RESULT` summary each for seeds 42, 7, and 99, followed by `3 passed`. No private customer values or keys are printed. Tests create temporary inputs and databases; they do not alter the example database you inspected earlier.

Inspect the saved result from the agent's run:

```bash
.venv/bin/python -m json.tool var/phase6/summary.json
```

If you want to save a new machine-readable test report:

```bash
.venv/bin/python -m pytest -q --junitxml=var/phase6/verification.xml -o junit_logging=all
```

The JSON summary is a saved extraction from the original run; rerunning pytest updates the XML, not that saved JSON automatically. The pytest pass/fail result and new XML are authoritative for a new run.

## Limits and remaining work

- Generated-seed comparisons prove repeatability and consistency, not equality with an unavailable official answer key. The hand-calculated fixtures separately prove exact known examples.
- Random-data privacy scans sample 33 leads per database. They supplement the fixed known-PII tests and encrypted-body storage design; they are not an exhaustive audit of every possible input.
- Failure injection exercises transaction rollback/retry. Actual `SIGKILL`, power loss, concurrent writers, and every possible filesystem failure were not tested.
- The large dataset and under-two-minute stretch target were not attempted.
- Fresh dependency installation is still unverified because earlier GitHub/PyPI DNS requests failed. The current local environment works; clean-checkout setup belongs to Phase 7.
- Real submission handles/email and the final documentation/handoff remain Phase 7 work.
- Stop here until the user requests Phase 7.
