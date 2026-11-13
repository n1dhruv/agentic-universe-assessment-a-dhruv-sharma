# Phase 3: Customer Lead Ingestion

Status: Complete. Target: 75 minutes. Dependencies: Phases 1–2.

## Outcome

Both workflows produce valid, deduplicated leads with accurate rejection and warning counts.

## Work

1. Load workflow schemas and map normalized headers against field names and aliases. Ignore unmatched columns.
2. Normalize supported phones, dates, non-negative decimals, strings, and enums exactly as the assignment specifies. Use `Decimal`, not floating point, for money.
3. Skip fully blank rows. Number only nonblank data rows, starting at one.
4. Validate fields in schema order. Keep one rejection reason: the first required-field failure or invalid phone. Store row location and reason without PII.
5. Convert invalid optional values to null. Count warnings only after the row is accepted.
6. Merge by workflow and canonical phone. Preserve original batch; later valid rows overwrite only non-null fields.
7. Keep missing optional values distinct from defaults. Resolve defaults after merging so a later blank language never overwrites an existing language.
8. Persist input row, rejection, duplicate-merge, and warning counts once per imported source.

## Completion checks

- [x] Both schema files drive the same generic ingestion path.
- [x] Header aliases, date formats, phone formats, and currency prefixes work.
- [x] Impossible dates and invalid optional fields produce the right results.
- [x] Rejected rows produce no leads or field-warning counts.
- [x] Multiple failures select the first rejection in schema order.
- [x] Duplicate merging preserves first batch and previous non-null values.
- [x] Re-ingesting a source changes neither records nor counters.

## Evidence

Verified on 2026-11-13:

- `.venv/bin/python -m pytest -q`: 55 passed in 0.27 seconds (52 Phase 3 tests and 3 Phase 2 regression tests).
- Imported both seed-42 drops into the isolated `var/phase3-demo.sqlite3` database with separate keys.
- Drop 1: 4 files, 1515 nonblank rows, 71 rejected rows, 29 merged duplicates, 83 field warnings.
- Drop 2: 2 files, 542 nonblank rows, 37 rejected rows, 28 merged duplicates, 39 field warnings.
- Final state: 1892 unique leads, 108 rejections, 6 lead source markers, 0 events. Total field warnings: 122.
- Repeat import: 0 files imported, 6 skipped, all new-work counters zero; the entire logical database dump remained identical.
- Rejection totals: invalid phone 42; missing customer name 25; missing order ID 13; missing phone 14; missing policy number 14.
- Verified conservation: 2057 input rows - 108 rejected - 57 merged duplicates = 1892 unique leads.
- Tests cover both schemas, alias normalization, required-field priority, blank-row numbering, optional warnings, first batch preservation, non-null merging, deferred defaults, rollback/retry, changed-file rejection, workflow isolation, exact persisted counters, and explicit CLI scope.
- Parent-directory and sequential ingestion match on controlled fixtures. No event processing was implemented or credited.

## What this phase does, in simple words

The program reads each customer spreadsheet. It tidies column names, phones, dates, money, and language codes. A row missing required information is rejected with one reason. A bad optional value becomes empty and records a warning. If the customer already exists in the same workflow, new usable values update that customer. Blank or invalid optional values do not erase earlier good information. The original upload batch stays attached to the customer.

All customer values are encrypted before storage. A keyed phone fingerprint finds repeated customers. Defaults are resolved after merging using `apply_defaults`; a default is not saved as if it came from a new row.

## Self-test commands

Run from the project root. This example uses its own database and keys, leaving the default database alone.

```bash
cd /home/dhruv/assessment-a
.venv/bin/python -m pytest -q
.venv/bin/python -m solution init --db var/my-phase3.sqlite3 --key-file var/my-phase3.keys.json
.venv/bin/python -m solution ingest data --leads-only --db var/my-phase3.sqlite3 --key-file var/my-phase3.keys.json
```

Expected with the current Phase 4 suite: 83 tests pass (55 were present at Phase 3 delivery). For a fresh `my-phase3` database and the supplied seed-42 data, the import prints:

```json
{"duplicate_lead_rows_merged": 57, "field_warnings": 122, "imported_files": 6, "lead_rows_rejected": 108, "lead_rows_total": 2057, "scope": "leads_only", "skipped_files": 0}
```

Run the same import again. Expected:

```json
{"duplicate_lead_rows_merged": 0, "field_warnings": 0, "imported_files": 0, "lead_rows_rejected": 0, "lead_rows_total": 0, "scope": "leads_only", "skipped_files": 6}
```

These CLI counters describe newly processed files for that invocation. Earlier counts remain stored in the database. If you reuse an already imported database, skipping files is the correct first-run output too.

Inspect safe counts, without printing private customer values:

```bash
.venv/bin/python - <<'CHECK'
import sqlite3
connection = sqlite3.connect('file:var/my-phase3.sqlite3?mode=ro', uri=True)
for table in ('leads', 'rejections', 'sources', 'events'):
    print(table, connection.execute(f'SELECT count(*) FROM {table}').fetchone()[0])
connection.close()
CHECK
```

Expected:

```text
leads 1892
rejections 108
sources 6
events 0
```

## Decisions and phase boundary

- Phase 3 required `--leads-only`; since Phase 4 it is optional. It still leaves event files and event source markers untouched when selected.
- Lead files use their logical path inside a drop plus a content digest. Changing an imported logical file fails the transaction; corrected inputs require a fresh database.
- Duplicate headers mapping to one schema field and rows with extra unlabelled values fail the entire drop. Short rows treat absent cells as missing.
- Empty optional values do not count as warnings. Invalid optional values do, including values on valid duplicate rows.
- Money uses half-up rounding. Dates use explicit English month names independent of the machine locale.
- The supplied schemas require only strings and phone. No rejection policy is invented for hypothetical invalid required date/decimal/enum fields.
- Reporting, CSV rejection export, event matching, and event quality counters remain later-phase work.
- Stop after this phase; do not start Phase 4 until the user requests it.
