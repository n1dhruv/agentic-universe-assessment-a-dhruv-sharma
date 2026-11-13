# Phase 7: Documentation and Submission Preparation

Status: Technical preparation verified; candidate walkthrough/final review pending. Target: 30 minutes. Dependencies: Phases 1–6.

## Outcome

A reviewable private project that another person can run from a clean checkout.

## Work

1. Complete `SUBMISSION.md` with candidate details, honest time spent, exact commands, database design, privacy approach, assumptions, failure handling, test coverage, measured results, and prioritized next steps.
2. Document event timestamp tie-breaking, half-up money rounding, changed-source rejection, post-merge defaults, and full-data report calculation.
3. Complete `AI_USAGE.md` truthfully, including planning, coding assistance, actual corrections, and verification. Do not invent examples or personal contributions.
4. Run a clean-checkout rehearsal: environment creation, dependency installation, local key/database initialization, data generation, both imports, report generation, and tests.
5. Inspect Git changes and tracked files for generated data, reports, databases, keys, `.env` files, and unintended changes to starter assets.
6. Confirm the user can explain customer identity, HMAC versus encryption, late linking, append-only events, idempotency, and report calculations.
7. Obtain real reviewer handles and destination email from the assignment sender; the starter currently contains placeholders. Prepare the private repository and handoff details. Publishing or sending the submission requires explicit user authorization.

## Completion checks

- [x] Clean-checkout commands work without undocumented manual steps.
- [ ] Both submission templates contain accurate information. Drafts are complete, but candidate walkthrough/final review of personal and AI-use claims remains pending; no independent understanding is claimed.
- [x] No secrets or generated artifacts are tracked.
- [x] Starter assets remain intact except intended template/dependency updates.
- [x] Timings and limitations reflect actual evidence.
- [x] Required core is complete, or remaining gaps are explicitly disclosed.
- [x] Submission destination is identified or recorded as a handoff blocker.

## Evidence

Verified on 2026-11-13:

- Candidate identity from repository configuration: Dhruv Sharma. The candidate explicitly provided an 8-hour effort estimate.
- Completed `SUBMISSION.md` and `AI_USAGE.md` with setup/run/test commands, schema/design, assumptions, measured results, limitations, and honest extensive AI-assistance disclosure. Candidate requested a walkthrough before submission; final personal review remains pending.
- Added `doc/walkthrough.md`, `doc/submission-email.md`, and `doc/submission-checklist.md`. Email is a draft, not a sent message.
- The existing remote is `assessment-a`, pointing to `https://github.com/n1dhruv/agentic-universe-assessment-a-dhruv-sharma.git`; branch main.
- `gh repo view ... --json visibility,url,defaultBranchRef` failed to connect to api.github.com. `git ls-remote` failed DNS. Private visibility, final remote synchronization, reviewer access, and delivery are not verified.
- Compared eight existing starter assets with web-retrieved source text. Restored nine omitted supplied files: the Assignment B README, fixtures and mock package, plus the original solution README. No B solution was added. Seventeen known starter assets match the resulting local source digest manifest.
- Reviewed intended Git files for generated inputs/reports, databases, keys, environments, private-key blocks, and common actual access-token patterns; none found. The supplied B fixtures contain synthetic customer records and a test webhook configuration; those are original starter assets, not newly generated outputs or real credentials.
- Fresh clone/snapshot: created a local clone with `git clone --no-hardlinks`, overlaid only intended source/document additions, and copied no venv, key, database, generated data, or report artifacts.
- Created a new environment with `python3 -m venv .venv`. Installed all declared dependencies with pip using an explicit local wheel source. These wheels were reconstructed from existing local cached/installed distributions because public-registry requests were unavailable. This is installer-based verification, not copying the development environment.
- `python -m pip check`: no broken requirements. Initialization, original generator seed 42, both ingests, and all five reports succeeded from that clean copy.
- Clean-copy full suite: 99 passed in 17.63 seconds; JUnit time 17.623 seconds. No failures or errors.
- The development environment's missing pip was also repaired with bundled ensurepip and all root requirements were installed from the same local wheel source.
- Local generated verification artifacts stay ignored under `var/phase7/`. Public-registry downloads, remote repository state, reviewer access, and email delivery remain unverified.
- Six of seven phase acceptance checks are verified. The final template-review gate is intentionally withheld until the requested candidate walkthrough/review is complete. No checklist denominator was changed.

## Clean-setup commands and exact verification method

The reviewer-facing commands are in [SUBMISSION.md](../SUBMISSION.md). Normal installation uses:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The local environment could not reach the public package registry, so the actual rehearsal substituted this explicitly documented installer source:

```bash
python -m pip install --no-index --find-links /tmp/assessment-a-phase7-tools/wheels -r requirements.txt
python -m pip check
```

That `/tmp` wheelhouse is a local verification artifact, not a repository dependency or a promised portable download. It contains re-created wheels from packages already present on this machine. On a network-enabled reviewer machine, use normal `pip install -r requirements.txt`. Online downloading was not verified here.

The rehearsal then ran the same initialization, data generation, drop-1/drop-2 ingestion, report, and pytest commands documented for reviewers. The fresh copy lives under `/tmp/assessment-a-phase7-tools/clean-repo`; no existing user database was modified. CPython 3.14.8 was tested; other supported Python versions were not exercised in this final rehearsal.

## Before sending

1. Complete the requested [code walkthrough](walkthrough.md) and candidate review of `SUBMISSION.md`/`AI_USAGE.md`.
2. Obtain the actual reviewer usernames and email from the assignment sender; the supplied README has placeholders.
3. Verify the repository is PRIVATE, upload the final reviewed commit, and confirm reviewer access from a network-enabled environment.
4. Send the reviewed [email draft](submission-email.md) and record delivery evidence.

The assignment requires the candidate to understand and defend submitted code. A walkthrough document does not itself prove understanding, and passing tests does not prove an email was sent. Detailed handoff commands are in [submission-checklist.md](submission-checklist.md).
