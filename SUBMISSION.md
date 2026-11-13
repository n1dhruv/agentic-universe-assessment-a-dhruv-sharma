# Submission

> Replace everything in _italics_. Be concise: bullet points are fine. We read every word.

## Candidate
- **Name:** _
- **Assignment chosen:** _A (Data) / B (Workflow)_
- **Time spent (honest estimate):** _e.g. 7h_

## How to run
```bash
# exact commands from a clean clone: setup, run, test
```
## Design
_Your architecture in a few paragraphs, plus a diagram if it helps. For A: your database schema
and why. For B: your lead state machine (ASCII or Mermaid) and how you guarantee at-most-once
dialling._

## Decisions & assumptions
_Every place where you made a call the spec didn't make for you, and why._

| Decision | Why | Alternative considered |
|---|---|---|
| Phase 3 uses explicit `ingest --leads-only` | Avoids presenting skipped event processing as a complete import while phases are delivered individually | Silent event skipping |
| Keep null values in stored merged records; resolve defaults with `apply_defaults` | A default from a blank later upload must not overwrite an earlier valid value | Persist defaults on each incoming row |
| Reject changed imported source paths | Replacing earlier input would require replaying merge history and counters | Automatic correction/replay |
| Fail the drop on duplicate mapped headers or unlabelled extra CSV values | No column precedence or recovery policy is specified | Guessing which input value to use |
| Round decimals half-up to two places | Deterministic currency rounding using Decimal | Binary floating point or half-even rounding |
## Failure modes considered
_What can go wrong and how your solution handles it (bad input, re-runs, crashes, timeouts,
duplicates...). Also list anything you know is **not** handled._

## Testing
_What you tested, what you didn't, and why._

## Results
_For A: timings, and anything surprising in the data. For B: your `/admin/report` summary from
a full run, ideally one that includes a `kill -9`._

## If I had another day
_What you'd do next, in priority order._
