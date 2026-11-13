# Submission

## Candidate

- **Name:** Dhruv Sharma
- **Assignment chosen:** A — Interaction Ledger & Reporting Pipeline
- **Time spent:** 8 hours, as estimated by the candidate.
- **Repository:** https://github.com/n1dhruv/agentic-universe-assessment-a-dhruv-sharma
- **Review status:** Local implementation and tests are complete. Candidate walkthrough and external handoff are pending. Reviewer handles and submission email must come from the assignment sender; the supplied README contains placeholders.

## How to run

Python 3.11+ is required. Development and the isolated local rehearsal use Python 3.14.8. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m solution init
python assignment-a-data/tools/generate_data.py --seed 42 --scale small --out data
python -m solution ingest data/drop_1
python -m solution ingest data/drop_2
python -m solution report --out reports/
python -m pytest -q
```

Expected: five report files and 99 passing tests. Generated input, reports, local keys, databases, and virtual environments are excluded from Git. The small hand-calculated files in `tests/fixtures/report_expected/` are required test inputs and are committed.

Repeated imports are safe:

```bash
python -m solution ingest data
python -m solution report --out reports/
```

The parent directory processes child drops in sorted order. Known files are skipped, including their counters. `ingest --leads-only` remains available for customer-only uploads. Pipeline commands accept `--db` and `--key-file`; reporting also requires `--out`. Defaults are `var/assessment.sqlite3` and `var/keys.json`.

## Design

The CLI coordinates schema-driven normalization, transactional SQLite imports, encrypted storage, event linking, and a shared reporting calculation. No HTTP service or external database is needed.

```text
CSV leads + JSONL events
          |
Schema normalization and per-drop transaction
          |
SQLite: encrypted leads/events + import history + rejections/counters
          |
Recalculate event links and quarantine against current customers
          |
Initiated-call facts and effective dispositions
          |
Five CSV/JSON reports
```

| Table | Purpose and constraints |
|---|---|
| `metadata` | Binds the database to its encryption/matching keys using a key fingerprint. |
| `sources` | Logical relative file path, SHA-256 content digest, and per-file input counters. |
| `leads` | One record per `(workflow_id, phone_token)`; first batch is permanent; complete normalized values are encrypted. |
| `events` | Globally unique event ID and encrypted original body. SQLite triggers reject updates and deletes. |
| `rejections` | Source, workflow, batch, nonblank row number, and reason; no input values. |

Fernet authenticated encryption protects entire customer and event bodies, including all schema-marked PII. Canonical phones are stored inside ciphertext; a separate keyed HMAC permits matching without plaintext phone columns. Independent keys live in an ignored owner-only file. Existing initialization preserves keys; a missing/wrong key fails rather than replacing it. Keep the keys separately if the database needs to be recoverable.

Each drop commits atomically. Lead files are processed before event files. The first valid lead creates its batch identity; later non-null values merge into its encrypted record. Defaults are resolved after merging, without turning an empty later field into an overwrite.

Event linking and quarantine are derived in memory from the unchanged ledger and all currently available leads. An unmatched event can become eligible after another upload. Ordinary events link by workflow and phone; overrides link through unambiguous workflow/call ownership. Orphans are classified before unknown dispositions. Unknown codes stay stored but do not enter the eligible stream.

Reports share one initiated-call model, so buckets, daily figures, and customer details use the same outcomes. Rendering uses a consistent SQLite read transaction. Files are fully rendered and staged before individual atomic replacements; reporting writes no database records.

## Decisions and assumptions

| Decision | Reason / alternative |
|---|---|
| SQLite and application-side aggregation | Sufficient for the required local core; avoids database-server setup. SQL aggregation remains a possible improvement. |
| Source identity is the path relative to a drop plus a content digest | Repeat imports do not recount malformed or duplicate deliveries. A changed previously imported logical path fails; replay/correction support would need explicit history handling. |
| Reject duplicate mapped headers or extra unlabelled CSV cells | The specification provides no precedence policy. Short rows instead treat absent cells as missing. |
| Half-up Decimal rounding to two places | Deterministic currency arithmetic; written-out amounts are invalid optional values, not guessed numbers. |
| Invalid optional values become null; defaults resolve after merges | Earlier valid information survives later blank/invalid optional fields. Warnings count only accepted rows. |
| Non-object JSON and absent/empty/non-string IDs count as malformed | Other unsupported structures/timestamps abort the drop with a payload-free error. NaN/Infinity are invalid JSON. Duplicate IDs are skipped before extra structural validation. |
| Preserve original event strings; normalize instants to UTC for calculations | Naive timestamps mean IST. All report dates/times are converted to IST. |
| Overrides outrank ordinary disposition sets | Within either class, greatest `(occurred_at, event_id)` wins; event ID resolves equal-time ambiguity. |
| Earliest initiation establishes a call if distinct initiation entries exist | Count one deterministic call rather than duplicate attempts. Calls are scoped by workflow, call ID, and linked customer. |
| Ambiguous override ownership remains orphaned | Do not guess if a workflow/call points at multiple customers. Supplied generated data normally has one customer per call ID. |
| Current disposition comes from the newest initiated call with an outcome | A newer call lacking an outcome still changes last-call time but does not erase the previous known disposition. |
| Distinct daily successes use call-initiation dates | Several successful calls to one customer on that date count once. Later overrides can revoke an earlier effective success. |
| Equal reference sort ties use canonical phone internally | Stable across independent keys and insertion orders; full phone is never exported. |
| Quality reason map contains observed reasons | Unobserved reasons are omitted. Other quality counters are numeric zero when appropriate. |

## Failure modes and limits

- Bad customer rows are rejected with one schema-ordered reason. Invalid optional values produce accepted-row warnings.
- Duplicate files do nothing; duplicate event deliveries increment counters once per new source file and do not replace ledger bodies.
- Unmatched/unknown events remain encrypted and outside business results; links and counts are recalculated after later data.
- A failed drop rolls back customer merges, new events, rejections, source markers, and counters together.
- Wrong keys fail. Output destinations conflicting with the database or CLI key file are rejected.
- Calculation/staging failure preserves existing reports. A failure during final file replacements can leave a mixture of old and new report versions; the five-file directory is not replaced atomically as a unit.
- Loss of the separate keys makes the corresponding encrypted data unrecoverable. Rotation and managed key storage are not implemented.
- Reports and event resolution read all stored records. Large-scale memory/performance targets, concurrent writers, actual power loss/SIGKILL, and all filesystem-failure cases were not tested.
- Original starter assets were retrieved through the web tool because shell GitHub access failed. The initially omitted Assignment B materials were restored unchanged; no Assignment B solution was implemented. Existing local project commit history is retained, rather than claiming original upstream Git history.
- A fresh local clone/snapshot and a newly created venv installed all declared dependencies with pip from local wheels reconstructed from existing cached distributions. `pip check`, the documented pipeline, and all 99 tests passed (17.63 seconds). Public-registry access and remote GitHub operations were unavailable; the Phase 7 guide records the exact method and handoff blockers.

## Testing

Run `python -m pytest -q`: 99 tests.

Coverage includes field normalization and aliases; rejection priority and row numbering; defaults and non-null merges; encryption, key validation, append-only triggers, and rollback; duplicate/malformed events; late customers and phone-free overrides; IST boundaries; all buckets; exact five-file hand-calculated expectations; success revocation; stable formatting/sorting; staging failures; and protected output paths.

Process-level tests generate fresh small datasets for seeds 42, 7, and 99. Each checks sequential versus combined imports using independent keys, byte-identical reports, repeat-import invariance, reopening in new processes, input-count conservation, and cross-report totals. Seed 42 additionally injects an invalid event after partial drop work, proves rollback, restores the input, and compares retry with an uninterrupted run.

Privacy checks include fixed known-PII fixtures plus 33 sampled customer records in each generated sequential/combined database, absent raw key material, owner-only key permissions, and SQLite integrity/foreign-key checks. These are not an exhaustive audit of every possible input. Generated-seed consistency is not an independent official answer key; hand-calculated fixtures establish exact known answers separately.

## Results

Phase 6 full-suite run: 99 passed, no failures/errors/skips, about 17.46 seconds. Complete generated-data scenarios took 5.9433 seconds (seed 42, including failure/retry), 5.3137 seconds (seed 7), and 5.3537 seconds (seed 99), including subprocess startup, generation, multiple imports/reports, and checks.

| Seed | Unique leads | Counted calls | Unique stored events | Earlier orphans resolved |
|---|---:|---:|---:|---:|
| 42 | 1892 | 2536 | 8500 | 910 |
| 7 | 1886 | 2544 | 8561 | 951 |
| 99 | 1901 | 2592 | 8690 | 1056 |

Seed 42 produced 6 batch rows, 33 daily rows, 1892 lead rows, and 108 rejection rows. It had 1467 connected calls. Quality totals: 2057 lead rows, 57 merged duplicates, 122 warnings, 8745 event lines, 8 malformed lines, 237 duplicate deliveries, 462 remaining orphans, and 18 unknown dispositions. Repeated sample reporting took approximately 0.3001 seconds. These are small-data measurements, not a large-dataset performance claim.

## If I had another day

1. Measure the supplied large dataset and profile memory before choosing SQL aggregation or materialized projections.
2. Add explicit corrected-file replay/backfill and key-rotation procedures.
3. Make whole-report-set publication versioned and add process-kill/concurrent-access tests.
4. Document managed keys, backups, scheduling, and operational recovery for a production deployment.
