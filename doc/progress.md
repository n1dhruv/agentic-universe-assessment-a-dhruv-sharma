# Assessment A: Project Progress

Last updated: 2026-11-13, 19:44 IST.

## Current summary

| Measure | Current state |
|---|---|
| Required project completion | **56.8% — 25 of 44 acceptance checks verified** |
| Phases complete | **4 of 7** |
| Planning documentation | Complete for the agreed core scope |
| Implementation | Phases 1–4 complete; report generation remains Not started |
| Application tests | 83 passed, including 28 new event tests and earlier regression coverage |
| Submission readiness | Not ready |
| Active work | Stopped after Phase 4; awaiting the user's request for Phase 5 |
| Known implementation bugs | None found in current checks; reports are not implemented |

Planning and tracking are complete preparation tasks. They do not count as completed assessment functionality.

## How completion is measured

The baseline is the 44 acceptance checkboxes in the seven phase documents. Each verified checkbox has equal weight:

```text
Completion percentage = verified acceptance checks / total acceptance checks × 100
```

Display the percentage to one decimal place when nonzero. This measures accepted deliverables, not hours spent or lines of code. Checkboxes vary in effort, so it is not a time-remaining estimate. A phase is complete only when all its checks pass and evidence is recorded. Overall 100% also requires all completion gates to pass and no unresolved required-core blockers.

If scope changes, record the reason, changed checks, old and new denominator, and effect on completion. Never remove failing checks to increase the percentage. Work outside the phase plan earns no completion credit unless it satisfies an existing check or an explicitly documented scope addition.

## Phase status

| Phase | Status | Verified checks | Completion | Remaining outcome |
|---|---|---:|---:|---|
| [1: Setup](phase-01-project-setup.md) | Complete | 5/5 | 100.0% | Verified; see phase evidence |
| [2: Storage and privacy](phase-02-storage-and-privacy.md) | Complete | 6/6 | 100.0% | Verified; see phase evidence |
| [3: Lead ingestion](phase-03-lead-ingestion.md) | Complete | 7/7 | 100.0% | Verified; see Phase 3 evidence |
| [4: Event ledger](phase-04-event-ledger.md) | Complete | 7/7 | 100.0% | Verified; see Phase 4 evidence |
| [5: Reports](phase-05-reports.md) | Not started | 0/6 | 0.0% | Pending |
| [6: Verification](phase-06-verification.md) | Not started | 0/6 | 0.0% | Pending |
| [7: Submission](phase-07-submission.md) | Not started | 0/7 | 0.0% | Pending |
| **Total** | **In progress** | **25/44** | **56.8%** | **Complete required core** |

## Completed work and activity history

Keep this history chronological and append new entries. Correct older claims with a new entry rather than silently rewriting history.

### LOG-001 — Project directory created

- Date: 2026-11-13.
- Category: Preparation; outside implementation phases.
- Request: Create a new project folder for Assessment A.
- Change: Created `/home/dhruv/assessment-a`.
- Verification: Directory listing confirmed the empty project folder existed.
- Completion impact: None; no phase acceptance check was completed.

### LOG-002 — Implementation plan documented

- Date: 2026-11-13.
- Category: Planning; outside implementation phases.
- Request: Create a documentation folder, a separate file for each phase, and agent instructions.
- Change: Added root `AGENTS.md`, `doc/README.md`, and seven phase documents.
- Decisions: Python and SQLite; complete required core first; seven implementation phases with explicit acceptance checks and evidence sections.
- Verification: A Python filesystem check confirmed nine nonempty documents and resolved every local Markdown link.
- Result: The implementation plan is available locally. Starter import, application code, datasets, and tests remain pending.
- Completion impact: None; planning documentation is tracked separately from required assessment delivery.

### LOG-003 — Central progress tracking established

- Date: 2026-11-13.
- Category: Process improvement; outside implementation phases.
- Request: Track all project progress, fixes, unplanned work, and completion percentage.
- Change: Added this ledger, phase completion counts, issue tracking, verification history, and update rules. Linked tracking from agent instructions and the roadmap.
- Verification: Counted the phase acceptance checkboxes: 5 + 6 + 7 + 7 + 6 + 6 + 7 = 44. Document/link consistency verification is recorded below.
- Completion impact: Baseline established at 0/44, or 0%. No application behavior changed.

### LOG-004 — Progress ledger moved into doc

- Date: 2026-11-13.
- Category: Documentation organization; outside implementation phases.
- Request: Keep the progress ledger inside `doc/`.
- Change: Moved root `progress.md` to `doc/progress.md`; updated agent instructions, roadmap references, and phase links.
- Verification: Filesystem and local Markdown link checks confirm the new location and references.
- Completion impact: None; implementation remains 0/44 (0%).


### BUILD-001 — Phase 1 verified

- Date: 2026-11-13.
- Category: Planned implementation.
- Change and verification: Created CLI help, restored the supplied Assessment A assets through web retrieval, generated seed 42 (4247 and 4498 event lines), and verified Git ignores. Run `.venv/bin/python -m solution --help` and `.venv/bin/python assignment-a-data/tools/generate_data.py --seed 42 --scale small --out data`. Python 3.14.8 is used. Git/PyPI DNS failed; offline resolver attempts also failed. Copied installed cryptography 50.0.1, cffi 2.1.1, pytest 9.1.1 and supporting distributions into the isolated venv; crypto round-trip and pytest imports pass. Original Git history could not be fetched; existing project history is preserved. Clean internet dependency installation is not yet verified.
- Completion: 5/44 checks (11.4%).


### BUILD-002 — Phase 2 verified

- Date: 2026-11-13.
- Category: Planned implementation.
- Change and verification: Implemented authenticated encryption for whole lead/event bodies, keyed HMAC identities, owner-only keys, key/database binding, append-only ledger triggers, and transactions. `.venv/bin/python -m pytest tests/test_storage.py -q`: 3 passed. `.venv/bin/python -m solution init`: succeeded. The forced transaction failure leaves no records or source markers. For your own check, rerun those two commands; initialization preserves existing keys.
- Completion: 11/44 checks (25.0%).

### LOG-005 — Enforced one-phase-at-a-time delivery and rechecked Phase 2

- Date: 2026-11-13.
- Category: User scope correction, verification, and progress-record correction.
- Reason: The user requested completing and explaining Phases 1–2 before proceeding further.
- Existing work disclosed: `solution/normalize.py`, `solution/ingest.py`, `tests/conftest.py`, `tests/test_normalize.py`, and `tests/test_leads.py` were already written before the interruption. The normalization/lead checks reported 35 passed. Phase 4 has a partial ingestion draft, but event linking/classification and all reports are unfinished. These drafts earn no additional acceptance credit.
- Changes this batch: Updated `AGENTS.md` to require stopping after each phase, corrected stale summary/dependency statements, and added plain-language explanations and self-test commands to the Phase 1 and Phase 2 documents. No application code changed.
- Verification: `.venv/bin/python -m pytest tests/test_storage.py -q` reported 3 passed in 0.03 seconds. CLI help and repeated initialization passed. An isolated temporary-database check also proved customer-identity uniqueness, encrypted lead persistence, and decryption after reopening.
- Boundary: Stop after Phase 2. Resume later phases only when the user requests them.
- Completion impact: Remains 11/44 checks, 25.0%; two phases accepted.
- Limitation: Internet dependency installation and clean-checkout reproduction remain unverified; local dependency distributions were copied into the isolated environment because DNS and offline resolution failed.

### LOG-006 — Removed premature Phase 3/4 implementation

- Date: 2026-11-13.
- Category: User-requested removal and CLI correction.
- Reason: The user requested removing all unfinished Phase 3/4 drafts before proceeding.
- Removed: `solution/normalize.py`, `solution/ingest.py`, `tests/conftest.py`, `tests/test_normalize.py`, and `tests/test_leads.py`, plus their compiled caches and stale pytest cache entries.
- Preserved: Phase 1 command scaffolding, Phase 2 storage/privacy code and tests, starter schemas/generator, current database and keys, and all phase planning documents.
- CLI correction: Removed imports and execution paths for draft ingestion/reporting. The future `ingest` and `report` command placeholders return exit status 1 with a clear not-implemented message before touching storage.
- Documentation: Reset Phases 3 and 4 to Not started in the roadmap, phase documents, and tracker. Earlier draft history is retained as an accurate historical record; the code no longer exists.
- Verification: `.venv/bin/python -m pytest -q` reported 3 passed in 0.04 seconds. Subprocess checks confirmed help and initialization succeed, both placeholders fail clearly without tracebacks, only Phase 1/2 Python sources remain, and working database/key bytes remain unchanged.
- Completion impact: None; 11/44 verified checks (25.0%) and 2/7 complete phases.
- Remaining work: Stop here. Start Phase 3 only when requested by the user.

### LOG-007 — Phase 3 authorized and started

- Date: 2026-11-13.
- Request: Explain the phone fingerprint and implement Phase 3 only.
- Decision: Require `ingest --leads-only` during this phase so skipping event files is explicit. Reuse Phase 2 encryption and transaction storage.
- Verification: Reviewed local lead rules, both schemas, source code, tests, and the clean Git working tree before implementation.
- Completion impact: None until the Phase 3 acceptance checks pass; currently 11/44 (25.0%).

### BUILD-003 — Phase 3 completed and verified

- Date: 2026-11-13.
- Category: Authorized Phase 3 implementation only.
- Changes: Added `solution/normalize.py` and `solution/leads.py`, connected explicit `ingest --leads-only` to the CLI, and added `tests/test_normalize.py` and `tests/test_leads.py`. Updated the phase guide, roadmap, and submission assumptions.
- Behavior: Schema-driven customer validation, aliases, accepted-row warnings, reason-only rejection storage, keyed phone matching, encrypted non-null merges, permanent first batch, deferred defaults, source-level counters, repeat skipping, and per-drop rollback. No event importer or event-linking draft was created.
- Verification: `.venv/bin/python -m pytest -q`: 55 passed in 0.27 seconds. CLI help and `git diff --check` passed. Imported seed-42 drops into the separate phase3-demo database and verified 1892 leads, 108 rejections, 57 merges, 122 warnings, 6 sources, and 0 events.
- Repeat verification: Ingesting the parent data directory afterward skipped all 6 files and left the complete logical database dump unchanged. Sample count conservation passed.
- Decisions: Temporary phase boundary requires `--leads-only`; exact source changes and ambiguous CSV headers fail safely. Detailed rules and reusable commands are in the Phase 3 guide and `SUBMISSION.md`.
- Fixes/failed attempts: No failing test or implementation fix occurred in this Phase 3 run. Added a specific regression case to prove later invalid optional values preserve earlier valid values; all tests remained green.
- Completion impact: Phase 3 receives 7 checks; total 18/44 (40.9%), 3/7 phases complete.
- Boundary: Stop here. Phase 4 remains Not started, and reports remain unavailable. Private handoff details and clean dependency installation remain open.

### LOG-008 — Phase 4 authorized and baseline checked

- Date: 2026-11-13.
- Request: Explain how to inspect SQLite and complete Phase 4 only.
- Discovery: `sqlite3` is installed. The user's populated database is `var/my-phase3.sqlite3`: 951 motor-renewal leads and 941 feedback leads. Supplied read-only table/count/rejection queries.
- Baseline: `.venv/bin/python -m pytest -q`: 55 passed in 0.27 seconds. Git working tree was clean.
- Implementation decision: Move existing drop/source transaction ownership into a shared ingestion module, preserving lead-only behavior and old databases. Add event ingestion and derived event classification separately; do not change the original encrypted ledger.
- Completion impact: None yet; 18/44 verified checks (40.9%). Phase 5 remains Not started.

### BUILD-004 — Phase 4 completed and verified

- Date: 2026-11-13.
- Category: Authorized Phase 4 implementation and compatibility-preserving extraction.
- Change: Added encrypted unique event ingestion, malformed/duplicate counters, UTC timestamp normalization, derived linking/quarantine, workflow-specific catalogue checks, and cumulative quality summaries in `solution/events.py`. Shared source/drop ownership is in `solution/ingest.py`; `solution/leads.py` retains its customer-only compatibility API. CLI defaults to full import and still supports `--leads-only`.
- Behavior: Ordinary events match their own workflow and phone fingerprint. Overrides match unambiguous workflow/call ownership. New customers or other call events can resolve old orphans. Unknown outcomes are excluded from eligible events. Original ledger bodies never change.
- Regression evidence: 55 tests passed before extraction and the same 55 passed immediately afterward. After feature implementation, 83 tests passed in 0.57 seconds, including 28 new event tests. Updated the previous CLI-refusal test because full import is now intentionally available.
- Sample verification: Separate Phase 4 demo imported both seed-42 drops: 1892 leads, 108 rejections, 8 source files, 8745 event lines, 8 malformed, 237 duplicates, and 8500 unique stored events. Final classification: 8020 eligible, 462 orphan, 18 unknown dispositions.
- Late-link evidence: 910 earlier orphan events resolved after drop 2. All 4160 earlier encrypted event bodies remained unchanged. Small-data drop-2 ingestion/classification measured 0.4464 seconds; no large-data claim made.
- Repeat/combined evidence: All 8 repeated sources skipped; logical database dump unchanged. Fresh combined-directory ingestion matched sequential event resolution, quality, source counters, and rejections. Existing Phase 3 user/demo databases were left unchanged.
- User documentation: Added `doc/check-database.md` with verified read-only SQLite commands, safe encrypted previews, and quality-count inspection. Updated Phase 4 commands, roadmap, current Phase 3 CLI notes, and submission assumptions.
- Failures/fixes: No failing test or product bug fix occurred in this Phase 4 run. The necessary ownership extraction was bracketed by the same passing regression suite.
- Completion impact: 7 Phase 4 checks accepted; total 25/44 (56.8%), 4/7 phases complete.
- Boundary: Stop here. No Phase 5 report writer, call buckets, or report aggregation was added. Clean dependency installation and submission destination remain open.

## Fixes and unplanned changes

| ID | Date | Type | Change and reason | Verification | State |
|---|---|---|---|---|---|
| EXTRA-001 | 2026-11-13 | Tracking improvement | Added a central progress ledger at the user's request; the original plan had only phase-level evidence | Baseline checklist count and document consistency checks | Complete |

EXTRA-002: Corrected stale progress claims and recorded early Phase 3/4 drafts. The agent had moved beyond the intended phase boundary; the user clarified delivery must stop after each phase. No implementation fix was needed in the Phase 2 recheck.

EXTRA-003: Removed premature Phase 3/4 drafts and corrected CLI placeholders to avoid imports of missing implementation modules. Verification passed; details are in LOG-006.

EXTRA-004: Added the requested SQLite inspection guide. Shared import ownership was extracted to make combined lead/event imports atomic; this was necessary Phase 4 work and preserved the customer-only API. No extra completion checks were added.

For every future fix, add an activity entry describing the symptom, cause, changed behavior, affected files, verification, and remaining limitations. Record failed attempts and reverted changes too, with their outcomes.

## Issues, dependencies, and blockers

| ID | Item | Impact | Status / next action |
|---|---|---|---|
| DEP-001 | Direct Git retrieval failed | Original starter Git history was unavailable | Resolved for A assets: retrieved supplied files through the web tool; existing local history preserved |
| DEP-003 | PyPI DNS and offline dependency resolution failed | Normal dependency installation is unverified | Local environment works using copied installed distributions; clean dependency install remains a Phase 7 limitation |
| DEP-002 | Reviewer handles and submission email are placeholders in the starter | Final handoff needs real destination details | Pending: obtain from the assignment sender before submission |

Network retrieval failures were investigated and worked around for local development. DEP-002 and DEP-003 remain open. The user authorized Phase 4; it is now complete. Stop before Phase 5.

## Verification history

| ID | Date | Check | Result | What it establishes |
|---|---|---|---|---|
| VERIFY-001 | 2026-11-13 | Filesystem inspection after folder creation | Passed | Project folder exists |
| VERIFY-002 | 2026-11-13 | Nonempty-file and local-link check for initial nine documents | Passed | Initial plan documents exist and their local links resolve |
| VERIFY-003 | 2026-11-13 | Count phase acceptance checkboxes | Passed: 44 unchecked, 0 checked | Initial implementation completion is 0% |
| VERIFY-004 | 2026-11-13 | Python filesystem validation of all ten documents, local Markdown links, and checklist totals | Passed: 10 nonempty documents, links resolve, 0/44 checks verified | Progress tracking and documentation references are consistent; no application behavior tested |

Current suite: 83 passing tests covering customer ingestion, event ingestion/linking, and storage regressions. The earlier removed drafts remain historical; the new implementations were separately authorized. All report generation remains unimplemented.

### Historical verification — draft removal

- `.venv/bin/python -m pytest -q`: 3 passed.
- CLI help/init: passed.
- Future ingest/report placeholders: expected exit 1, clear messages, no traceback.
- File inventory and database/key byte-preservation checks: passed.

### Historical verification — Phase 3

- `.venv/bin/python -m pytest -q`: 55 passed.
- `ingest --leads-only` imports only customer files; no event markers or ledger records created.
- Seed 42: 2057 rows = 1892 unique leads + 108 rejected rows + 57 merged duplicate rows.
- Re-ingestion: 6 files skipped, all new-work counters zero, logical database unchanged.
- `git diff --check`: passed.

### Latest verification — Phase 4

- `.venv/bin/python -m pytest -q`: 83 passed.
- Separate sample databases prove sequential/combined equality and repeat-import invariance.
- Event conservation: 8745 lines - 8 malformed - 237 duplicates = 8500 stored events = 8020 eligible + 462 orphan + 18 unknown.
- Earlier orphan resolution and unchanged original ciphertext verified.
- Read-only SQLite queries for the user's Phase 3 database verified.

## Next actions

1. User may inspect SQLite and run the Phase 4 self-tests in its guide.
2. Stop until the user requests Phase 5.
3. When requested, derive call/customer facts and generate the five contracted report files.

## Mandatory update protocol

- Read this file before starting project work. Update it after each meaningful work batch and before handing work back to the user.
- Record phase work, fixes, unexpected discoveries, dependency/configuration changes, failed attempts, reversions, and work outside the plan.
- Each activity entry needs an ID, date, category, reason, concrete change, verification result, completion impact, and any remaining work.
- Name affected files and exact verification commands when available. Never include secrets or raw PII.
- Distinguish `Implemented, unverified` from verified completion. Log failed and skipped checks honestly.
- Keep phase checkboxes, evidence sections, this summary, and the roadmap status table consistent.
- Recalculate verified counts and percentage after changes. Reopen a check and reduce completion if a regression invalidates previous evidence.
- Maintain open issues with their impact, next action, and resolution evidence. Do not erase resolved issues; mark them resolved.
- Keep planning estimates separate from actual recorded effort. Do not invent elapsed work time.
- If only documentation changed, record that explicitly and do not imply application tests passed.
