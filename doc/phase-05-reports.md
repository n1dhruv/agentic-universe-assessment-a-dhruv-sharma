# Phase 5: Call Facts and Five Reports

Status: Complete. Target: 90 minutes. Dependencies: Phases 1–4.

## Outcome

All five files match the assignment's exact output contract.

## Work

1. Build one shared call-fact calculation layer from all eligible stored events. Count a call only when its linked initiation exists.
2. Determine connected and telephony-failed flags. Choose the latest valid override when present; otherwise choose the latest valid disposition set. Compare occurrence times, not arrival order.
3. Apply customer bucket precedence from the contract. Derive success from effective outcomes, so a later override can remove a previous success.
4. Compute daily distinct successful leads and connectivity using call-initiation dates in IST.
5. Produce these files with the exact headers and sort keys from the supplied README:

| File | Contents |
|---|---|
| `batch_summary.csv` | Customer counts and buckets by original batch |
| `daily_overview.csv` | Daily call, connection, and distinct success metrics |
| `lead_report.csv` | Customer status, masked phone, and latest call information |
| `rejections.csv` | Rejected input locations and reasons, without PII |
| `data_quality.json` | Persisted ingestion counts and final event classifications |

6. Format booleans as `true`/`false`, rates to four decimal places, and timestamps as ISO-8601 in IST. Write empty optional report values as empty cells.
7. Always write CSV headers, including empty results. Use required sort keys first and stable internal identity only to resolve otherwise unspecified ties.
8. Calculate all report content before publishing files. Use temporary files and replacement to avoid partially written individual files; do not claim the entire directory replacement is atomic.

## Completion checks

- [x] A hand-calculated fixture matches all five expected files.
- [x] All bucket branches, override precedence, and missing initiation are covered.
- [x] Current disposition comes from the latest initiated call that has an effective disposition.
- [x] Daily successes count distinct customers on each call's initiation date.
- [x] IST midnight boundaries and missing calls are correct.
- [x] Repeated reporting produces identical bytes without changing database contents.

## Evidence

Verified on 2026-11-13:

- Baseline before implementation: `.venv/bin/python -m pytest -q` reported 83 passed in 0.48 seconds.
- New report tests: 13 passed. All five outputs exactly match independently hand-calculated fixture files, including headers, ordering, blank fields, booleans, rates, and timestamps.
- Full regression suite: 96 passed in 0.79 seconds.
- Fixture path correction: the original `tests/fixtures/reports` directory was ignored by the starter's `reports/` rule. Moved the expectations to `tests/fixtures/report_expected`; all six fixture documents are visible to Git, and the 13 report tests passed again in 0.40 seconds.
- CLI smoke check: `report` printed `Wrote five report files.` and wrote only the five required artifacts to `reports/phase5-demo`.
- Sample CSV data-row counts: batch summary 6, daily overview 33, lead report 1892, rejections 108. These counts exclude the header row.
- Sample totals: 2536 counted calls and 1467 connected calls. Daily and customer totals agree. Batch counts sum to 1892 customers and each batch's buckets sum to its total.
- Sample quality: 2057 lead rows, 108 rejected, 57 merged duplicates, 122 field warnings; 8745 event lines, 8 malformed, 237 duplicates, 462 orphans, and 18 unknown dispositions.
- Measured sample report generation: 0.3001 seconds. This is a small-dataset observation, not the large-data stretch target.
- Repeated reports were byte-identical and the complete logical database dump remained unchanged.
- Failure tests cover staging errors and accidental output collisions with database/key files.
- Phase 6's broader multi-seed and completion audit has not been performed or credited.

## Simple explanation

The customer list and call diary are already stored. This phase reads them and answers: who was called, who answered, what happened, and which customers are finished?

A call counts only when its start entry exists. A supervisor correction takes priority over the ordinary outcome. Several diary events can belong to one call; 8500 stored events in the sample become 2536 counted calls, not 8500 calls.

Customer status follows the required order: untouched, completed, all calls failed at the carrier, or other calls still in progress. Daily figures use Indian dates. Customer successes are counted once per day even if the same customer has several successful calls.

## The five outputs

| File | What to read it for |
|---|---|
| `batch_summary.csv` | Customer totals and progress for each original upload |
| `daily_overview.csv` | Calls, connections, connection rate, and successful customers each day |
| `lead_report.csv` | Each customer's masked phone, status, call counts, and current outcome |
| `rejections.csv` | Where bad customer rows appeared and the reason for rejection |
| `data_quality.json` | Totals for messy input, duplicates, unmatched events, and unknown outcomes |

Names and full phones are not exported. External references are exported as required by the supplied schemas. Original event records remain encrypted and unchanged.

## Self-test commands

The following database was populated by the Phase 4 verification and is available locally:

```bash
cd /home/dhruv/assessment-a
.venv/bin/python -m pytest tests/test_reports.py -q
.venv/bin/python -m pytest -q
.venv/bin/python -m solution report --out reports/phase5-demo --db var/phase4-demo.sqlite3 --key-file var/phase4-demo.keys.json
```

Expected: 13 report tests pass, 96 total tests pass, then `Wrote five report files.`

If using your own Phase 4 database, replace the database/key arguments with `var/my-phase4.sqlite3` and `var/my-phase4.keys.json`.

Open the output folder in your editor or inspect it from the terminal:

```bash
ls reports/phase5-demo
head -n 7 reports/phase5-demo/batch_summary.csv
head -n 5 reports/phase5-demo/daily_overview.csv
.venv/bin/python -m json.tool reports/phase5-demo/data_quality.json
wc -l reports/phase5-demo/*.csv
```

Expected CSV line counts, including the header: batch summary 7, daily overview 34, lead report 1893, rejections 109. Rerunning `report` safely replaces those report files with identical content when the input database has not changed.

To recreate the example from a clean setup later:

```bash
.venv/bin/python assignment-a-data/tools/generate_data.py --seed 42 --scale small --out data
.venv/bin/python -m solution init --db var/my-phase5.sqlite3 --key-file var/my-phase5.keys.json
.venv/bin/python -m solution ingest data --db var/my-phase5.sqlite3 --key-file var/my-phase5.keys.json
.venv/bin/python -m solution report --out reports/my-phase5 --db var/my-phase5.sqlite3 --key-file var/my-phase5.keys.json
```

## Calculation and publication decisions

- One shared `build_call_facts` calculation feeds all business reports. It uses only the Phase 4 eligible event stream.
- A call's latest valid override wins regardless of whether an ordinary set arrived or occurred later. Unknown outcome codes have already been excluded by Phase 4.
- Equal outcome timestamps use event ID as the deterministic tie-breaker. If distinct initiation entries exist for one call, the earliest timestamp/event ID establishes its start.
- Calls are scoped by workflow, call ID, and matched customer, so one customer's ordinary events do not change another customer's facts. Supplied generated data has one customer per call ID.
- The newest call without an outcome still advances `last_call_at`. `current_disposition` comes from the newest initiated call that does have an outcome.
- An override can revoke an earlier success. Neither `ever_success` nor daily successes count superseded successful outcomes.
- Phone is only used internally to produce the masked value and resolve otherwise unspecified equal-reference sort ties independently of insertion order or secret keys.
- Reports use one consistent read transaction, calculate all content first, then stage all files in the destination filesystem. Each final file is replaced atomically. A failure during the final replacement loop can leave mixed report versions; the directory is not atomically replaced as a unit.
- Database files and caller-provided protected paths (including the CLI key file) cannot be replaced by report outputs. Invalid target directories fail with a clear error.
- Observed rejection reasons are exported in the quality map. Empty CSVs still contain headers; empty values are blank cells; quality counters remain numeric zero where appropriate.
- Stop after Phase 5. Phase 6 and Phase 7 remain Not started.
