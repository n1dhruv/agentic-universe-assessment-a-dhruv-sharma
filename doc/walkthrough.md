# Code Walkthrough Before Submission

The candidate requested this walkthrough before submitting. Reading it is preparation, not proof that every line is understood. Open the linked modules and run the commands; ask about anything you cannot explain.

## 1. The whole program

Imagine two notebooks: a customer list and a call diary. The program cleans the customer list, stores it safely, matches diary entries to customers, then calculates reports.

```text
python -m solution
        |
        +-- init: create keys and database
        +-- ingest: read customer CSVs, then call JSONL files
        +-- report: calculate facts and write five files
```

Start in [solution/__main__.py](../solution/__main__.py). `argparse` reads the command and filenames. The CLI calls storage, ingestion, or reporting, closes connections, and returns clear errors without printing input records.

## 2. Cleaning one customer row

Read [solution/normalize.py](../solution/normalize.py) and [solution/leads.py](../solution/leads.py).

- Header aliases let `Mobile No` and `phone` map to the same field.
- Phone cleanup makes formatting variants into the same canonical Indian number.
- Dates become ISO dates. Money uses `Decimal` and rounds to two places.
- Required missing fields or an invalid phone reject the row. The first failure in schema order wins.
- Invalid optional fields become null and produce warnings. `twelve thousand` is not guessed as a numeric amount.
- Blank rows do not affect row counts. Warnings from rejected rows do not count.

A workflow is a type of work: renewals or feedback. One phone in both workflows represents two workflow-specific customers.

## 3. Encryption and phone fingerprints

Read [solution/storage.py](../solution/storage.py).

Encryption is a locked box. The program can open it with the encryption key. Complete normalized customer values and original event bodies go into these boxes.

HMAC is a secret matching label. The same canonical phone and matching key produce the same label. It is used to find an existing customer, not to recover the phone. Recovering the phone requires decrypting the customer record.

Two independent keys are generated in a local key file with owner-only permissions. The database records a fingerprint of the keys so the wrong key file is rejected. The key file is excluded from Git.

The database's unique `(workflow_id, phone_token)` constraint prevents duplicate customer identities even if application code tries to insert them.

## 4. Merge, repeat imports, and rollback

Read [solution/ingest.py](../solution/ingest.py).

If Alice appears again with a new valid premium, update the premium. If the later premium is blank or invalid, preserve the earlier value. Her first valid upload batch remains unchanged. Defaults are resolved after merging rather than saved as new updates.

There are two kinds of duplicate:

- A repeated file: `sources` remembers the logical path and content digest. Skip it entirely, including all its counters.
- A repeated event inside a new file: the event ID is already stored. Count a duplicate delivery, but do not insert or replace the event.

A transaction groups one drop's database changes. If a later file in that drop fails, SQLite cancels its earlier inserts, merges, counters, rejections, and source markers together. Earlier committed drops stay intact.

## 5. Event linking and quarantine

Read [solution/events.py](../solution/events.py).

Each JSONL line is one diary entry, such as call started or customer answered. Broken JSON is counted and skipped. Unique valid entries are encrypted and saved once.

Ordinary events match customers through workflow and normalized phone. An override has no phone: find the other events with the same workflow/call ID and use their unambiguous customer identity.

An orphan is an entry whose customer cannot yet be found. Do not delete it. Recalculate links from all current data. If the customer arrives tomorrow, yesterday's entry can become usable without rewriting it.

An unknown disposition is an outcome code absent from that workflow's supplied catalogue. Keep the original event, but exclude it from usable outcomes. Check orphan status before unknown disposition status so the counts do not overlap.

`resolve_events` returns usable linked entries and quarantine reasons. It does not update the ledger. SQL triggers also reject edits/deletes to stored events.

## 6. What reports calculate

Read [solution/reports.py](../solution/reports.py).

`build_call_facts` groups eligible entries belonging to the same call/customer. A call counts only if a start entry exists. Connected and telephony-failed flags come from the relevant entries.

For the outcome, the latest valid supervisor override wins. If there is no override, use the latest valid ordinary disposition. Compare occurrence timestamps, not arrival order.

Customer buckets follow this order:

1. No counted calls: `yet_to_reach_out`.
2. Any terminal effective outcome: `completed`.
3. Every counted call has a telephony failure: `in_progress_telephony_failed`.
4. Otherwise: `in_progress_dialed`.

Daily figures use the IST date of call initiation. Two successful calls to one customer on a day count as one successful customer. A later correction can remove an earlier effective success.

`last_call_at` is the newest call start. `current_disposition` is the outcome of the newest started call that has an outcome; a newer unanswered call does not erase the earlier known outcome.

The renderer reads one consistent database snapshot. All output is calculated and staged before replacing final files. Individual files cannot be half-written, but all five replacements are not one atomic directory operation.

## 7. Run and inspect

From the project root, use the existing development environment:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m solution --help
.venv/bin/python -m solution report --out reports/walkthrough --db var/phase4-demo.sqlite3 --key-file var/phase4-demo.keys.json
head -n 7 reports/walkthrough/batch_summary.csv
```

Expected: 99 tests pass; CLI help lists commands; the report command writes five files. The supplied example has 1892 customers and 2536 counted calls. Multiple diary entries belong to each call.

For a clean clone, use the setup commands in [SUBMISSION.md](../SUBMISSION.md), not machine-specific paths from earlier progress notes.

## 8. Explain these before sending

Practice answering in your own words:

- Why do differently formatted phone numbers match? Why are encryption and HMAC both needed?
- What exactly prevents a repeated upload from increasing counts?
- Why can a later customer upload fix an earlier orphan without changing the event?
- What happens if ingestion fails after some rows were already merged?
- Why can a later override change a previously generated success count?
- Which outputs contain masked phones, and why are generated inputs, databases, and keys absent from Git?

The interviewer may ask for a live change. Trace the owning function and its tests before changing code; do not claim independent understanding until you can do that.
