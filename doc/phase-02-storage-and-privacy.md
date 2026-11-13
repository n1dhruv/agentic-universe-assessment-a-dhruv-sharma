# Phase 2: Storage and Privacy

Status: Not started. Target: 45 minutes. Dependency: Phase 1.

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

- [ ] Records survive closing and reopening the database.
- [ ] Uniqueness constraints reject duplicate identities.
- [ ] Encryption round trips preserve original values.
- [ ] Database values contain no plaintext test names or phone variants.
- [ ] Missing or wrong keys fail without modifying data.
- [ ] A forced import error rolls back records, markers, and counters.

## Evidence

Pending: record privacy, persistence, constraints, and rollback test results. Never paste secrets into this document.
