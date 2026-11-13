# Phase 2: Storage and Privacy

Status: Complete. Target: 45 minutes. Dependency: Phase 1.

## Outcome

Persistent SQLite storage with protected private information and safe import transactions.

## Work

1. Create tables for leads, unique immutable events, imported sources, rejected rows, and source-level quality counters.
2. Identify leads by workflow and keyed HMAC of canonical phone. Enforce uniqueness in SQLite. Enforce event ID uniqueness across drops.
3. Keep first batch, schema values, and encrypted PII on leads. Keep non-PII report fields available without exposing private values.
4. Encrypt all schema-marked private fields with authenticated encryption using `cryptography`. Encrypt complete original event bodies before storage; retain only necessary non-PII metadata separately.
5. Generate independent encryption and HMAC keys during `init`. Store them in the ignored key file with owner-only permissions. Preserve existing keys on repeated initialization.
6. Fail clearly when keys are absent, invalid, or do not match the database. Never silently replace keys for an existing database.
7. Track imported source identity using relative logical path and content fingerprint. Skip exact repeats and reject changed previously imported files.
8. Apply each drop's changes in one transaction, including source markers and counters. Keep the ledger immutable; calculate links separately.

Use parameterized SQL and SQLite foreign-key enforcement. Keep schema creation simple; no migration framework is required for a new local project.

## Completion checks

- [x] Records survive closing and reopening the database.
- [x] Uniqueness constraints reject duplicate identities.
- [x] Encryption round trips preserve original values.
- [x] Database values contain no plaintext test names or phone variants.
- [x] Missing or wrong keys fail without modifying data.
- [x] A forced import error rolls back records, markers, and counters.

## Evidence

Pending: record privacy, persistence, constraints, and rollback test results. Never paste secrets into this document.

## Execution evidence and self-check

Implemented authenticated encryption for whole lead/event bodies, keyed HMAC identities, owner-only keys, key/database binding, append-only ledger triggers, and transactions. `.venv/bin/python -m pytest tests/test_storage.py -q`: 3 passed. `.venv/bin/python -m solution init`: succeeded. The forced transaction failure leaves no records or source markers. For your own check, rerun those two commands; initialization preserves existing keys.

## Phase 2 recheck after scope correction

- `.venv/bin/python -m pytest tests/test_storage.py -q`: 3 passed in 0.03 seconds.
- `.venv/bin/python -m solution init`: succeeded without replacing keys.
- An isolated temporary database check confirmed unique lead identities, encrypted customer values absent from raw database bytes, and correct decryption after reopening.
- This verifies storage foundations, not finished ingestion or reporting. Those remain later-phase work.

### Simple explanation and commands

The database is a notebook that remembers information after the program closes. Private customer information is locked before saving. A separate key unlocks it. Phone fingerprints let us match customers without keeping readable phone numbers in database records. Original call diary entries cannot be edited or deleted through normal database operations. If a transaction fails, its unfinished changes are cancelled together.

From the project root, run:

```bash
.venv/bin/python -m solution init
.venv/bin/python -m pytest tests/test_storage.py -v
```

Expected: initialization prints `Database and keys ready; existing data preserved.` The test command reports `3 passed`. Tests use temporary databases and do not change the working database.
