# AI Usage Disclosure

## Tools used

OpenAI Codex/ChatGPT for planning, explanations, implementation, tests, documentation, and local tool execution. The assistant used shell/Python tools and web retrieval of the supplied public starter files.

## What I used them for

- Compared Assessments A and B and chose a manageable core scope with the candidate.
- Broke Assignment A into phases and maintained local plans and progress records.
- Generated the Python CLI, normalization, encrypted SQLite storage, import/linking logic, reports, and tests. Most implementation and test code was AI-generated; it should not be represented as independently typed by the candidate.
- Explained concepts including keyed phone fingerprints, optional-field warnings, idempotency, event linking, SQLite inspection, and report meanings.
- Ran unit/fixture/integration tests and helped prepare the submission documentation.

## What I wrote or decided myself

The candidate chose Assignment A, selected complete core scope, requested one-phase-at-a-time delivery with explanations and runnable commands, reviewed sample input/output behavior, asked about invalid written-out amounts and database inspection, and provided an honest time estimate of 8 hours. The repository retains phase-by-phase commit history.

The assistant proposed and implemented most detailed engineering choices, including SQLite, whole-body encryption, HMAC matching, derived quarantine, and report aggregation. The candidate requested a walkthrough before submission; independent understanding and live modification readiness are not yet claimed.

## Where the AI was wrong or unhelpful

- The assistant moved into Phase 3/4 drafts before the candidate wanted to advance. The candidate requested their removal. Those drafts and tests were removed, then the phases were implemented only after separate requests.
- The initial starter retrieval omitted the unused Assignment B folder. This was discovered during final repository review and the supplied files were restored, without implementing B.
- The initial expected-report fixture folder matched the starter's `reports/` Git ignore pattern. The assistant detected the issue with `git check-ignore`, moved the hand-calculated fixtures to `tests/fixtures/report_expected/`, and reran the report tests.
- GitHub/PyPI network failures initially led to development packages being copied into an isolated local environment. Final verification distinguishes that workaround from an installer-created clean environment and does not claim an online install that was not observed.

## How AI-generated code was verified

- 99 automated tests pass, including independently hand-calculated exact outputs for all five reports.
- Generated seeds 42, 7, and 99 were exercised through separate CLI processes, comparing sequential/combined runs, repeat imports, reopening, and report bytes.
- A deliberately failing import proved rollback and retry; old event ciphertext stayed unchanged during late linking.
- Fixed privacy fixtures and sampled generated records checked PII absence, wrong-key behavior, key permissions, and database integrity.
- The assistant executed the recorded checks. This disclosure does not claim the candidate independently authored, reviewed every line, or reran every command. Candidate walkthrough and final review remain required before sending the submission.
- Clean-setup verification details and limitations are recorded in `doc/phase-07-submission.md`.
