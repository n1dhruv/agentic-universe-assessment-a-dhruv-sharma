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
| Full ingestion is the default; optional `--leads-only` keeps customer-only imports available | Both paths share transactions and source tracking without recounting old customer files | Separate incompatible import tools |
| Keep null values in stored merged records; resolve defaults with `apply_defaults` | A default from a blank later upload must not overwrite an earlier valid value | Persist defaults on each incoming row |
| Reject changed imported source paths | Replacing earlier input would require replaying merge history and counters | Automatic correction/replay |
| Fail the drop on duplicate mapped headers or unlabelled extra CSV values | No column precedence or recovery policy is specified | Guessing which input value to use |
| Round decimals half-up to two places | Deterministic currency rounding using Decimal | Binary floating point or half-even rounding |
| Recalculate event links and quarantine from current data | Late customer and call events can resolve old orphans without mutating the original ledger | Persist and update link/status columns in the event ledger |
| Key call ownership by workflow plus call ID; quarantine ambiguous overrides | An override without a phone must not guess between multiple customer identities | Link by call ID alone |
| Treat non-object JSON and unusable event IDs as malformed; fail a drop on other unsupported event structures or timestamps | The supplied contract only defines a narrow malformed category; avoid silently inventing counters or leaking payloads in errors | Silently skip structurally unsupported events |
| Store original event bodies encrypted; normalize UTC/offset/naive-IST timestamps for linked-event use | Preserve the original diary while comparing actual instants consistently | Replace original ledger timestamp strings |
| Classify orphans before unknown outcomes; keep unknown codes out of the eligible event stream | Follow classification precedence and permit later reclassification after linking | Count unresolved unknown outcomes in both categories |
| Share call facts across every business report | All reports must use the same initiation, connection, and effective-outcome rules | Reimplement outcome logic independently in each report |
| Prefer overrides over ordinary sets; break equal occurrence timestamps by event ID | Preserve supervisor corrections and deterministic output even with out-of-order delivery | Choose whichever event arrived last |
| Use earliest initiation when distinct initiation events exist for a call | Count one call and give it one deterministic start date | Count every initiation as another call |
| Scope calls by workflow, call ID, and linked lead | Prevent inconsistent other-customer events from changing a customer's totals | Group by call ID alone |
| Sort equal external references by canonical phone internally | Remain deterministic across insertion orders and independently generated secret keys | Sort by database IDs or HMAC values |
| Stage all outputs, then atomically replace individual files | Avoid half-written individual files and preserve existing reports on calculation/staging failure | Write final files directly or claim atomic replacement of the entire directory |
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
