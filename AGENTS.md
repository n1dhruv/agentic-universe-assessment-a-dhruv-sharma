# Assessment A: Agent Instructions

## Goal

Complete the Interaction Ledger & Reporting Pipeline assessment in Python 3.11+. Deliver the required core, tests, and honest submission documentation. Follow the phase plan in [doc/README.md](doc/README.md).

## Current state

Only planning documents exist. Implementation, starter repository setup, data generation, and verification remain pending. Never treat a planned check as a completed check.

## Sources of truth

- Starter repository: https://github.com/AryamannNingombam/sde-assignment-junior-2026
- Assessment contract: `assignment-a-data/README.md`, once the starter is available locally.
- Workflow schemas and disposition catalogue supplied with the starter.
- Supporting terms: `docs/GLOSSARY.md` from the starter.
- The assessment contract takes precedence over this plan. Document ambiguities and implementation assumptions in `SUBMISSION.md`.

## Scope and stack

- Implement Assessment A only. Complete the required core before considering stretch work.
- Use SQLite through Python's `sqlite3`, `cryptography` for privacy, and `pytest` for tests.
- Use standard libraries for CLI parsing, CSV, JSON, dates, and decimal arithmetic.
- No frontend, HTTP API, external service, custom framework, or database server is required.
- Keep implementation in `solution/`, tests in `tests/`, and our phase documents in `doc/`.
- Preserve original assignment files. Update the designated submission templates and add dependencies to the supplied requirements file as needed.

## Data and privacy rules

- Customer identity is workflow plus canonical phone. Preserve the first valid batch permanently.
- Merge later non-null values. Apply defaults after merging, without replacing valid earlier values.
- Keep the unique event ledger append-only. Resolve links and classifications separately.
- Retain orphan events and reconsider them when new leads or related events arrive.
- Encrypt schema-marked PII and complete event bodies before database storage.
- Match phones with keyed HMAC, never an unkeyed hash. Keep keys outside the database and Git.
- Do not log raw rows, phone numbers, names, or event bodies.
- Exclude generated inputs, report outputs, databases, keys, and environment files from Git.

## Processing decisions

- Process drops in supplied order and files in filename order. Import leads before events within a drop.
- Process parent directories by sorted child-drop order through the same ingestion path.
- Record logical source paths relative to a drop and content fingerprints. Skip already imported files entirely, including their counters.
- Reject changes to an already imported logical file; explain that corrected data requires a fresh database.
- Commit each drop atomically. Roll back failed drops, including import markers and counters.
- Derive reports from all stored information. Do not build incremental report caches for the core.
- Interpret naive event times as IST; store normalized instants and report IST dates.
- Break equal event timestamps by event ID. Use Decimal half-up rounding for money. Document these assumptions.

## Working method

- Work through phases in order. Add focused tests with the behavior they verify.
- Keep phase checklists and the progress index accurate. Record commands, outcomes, and material limitations.
- Do not claim generated-seed checks prove exact correctness. Use hand-calculated fixtures for exact report assertions.
- Follow the shared workspace instructions. Postman CLI is installed, but this local file pipeline needs no API tooling.
- Do not publish the solution publicly or send submission messages without explicit user authorization.

## Completion

All five reports match the contract; repeated ingestion changes neither results nor counters; late links resolve; privacy checks and tests pass; clean-checkout commands work; `SUBMISSION.md` and `AI_USAGE.md` are complete and truthful.
