# Phase 5: Call Facts and Five Reports

Status: Not started. Target: 90 minutes. Dependencies: Phases 1–4.

## Outcome

All five files match the assignment's exact output contract.

## Work

1. Build one shared call-fact calculation layer from all eligible stored events. Count a call only when its linked initiation exists.
2. Determine connected and telephony-failed flags. Choose the latest valid override when present; otherwise choose the latest valid disposition set. Compare occurrence times, not arrival order.
3. Apply customer bucket precedence from the contract. Derive success from effective outcomes, so a later override can remove a previous success.
4. Compute daily distinct successful leads and connectivity using call-initiation dates in IST.
5. Produce these files with the exact headers and sort keys from the supplied README:

| File | Contents |
|---|---|
| `batch_summary.csv` | Customer counts and buckets by original batch |
| `daily_overview.csv` | Daily call, connection, and distinct success metrics |
| `lead_report.csv` | Customer status, masked phone, and latest call information |
| `rejections.csv` | Rejected input locations and reasons, without PII |
| `data_quality.json` | Persisted ingestion counts and final event classifications |

6. Format booleans as `true`/`false`, rates to four decimal places, and timestamps as ISO-8601 in IST. Write empty optional report values as empty cells.
7. Always write CSV headers, including empty results. Use required sort keys first and stable internal identity only to resolve otherwise unspecified ties.
8. Calculate all report content before publishing files. Use temporary files and replacement to avoid partially written individual files; do not claim the entire directory replacement is atomic.

## Completion checks

- [ ] A hand-calculated fixture matches all five expected files.
- [ ] All bucket branches, override precedence, and missing initiation are covered.
- [ ] Current disposition comes from the latest initiated call that has an effective disposition.
- [ ] Daily successes count distinct customers on each call's initiation date.
- [ ] IST midnight boundaries and missing calls are correct.
- [ ] Repeated reporting produces identical bytes without changing database contents.

## Evidence

Pending: record exact fixture comparisons and formatting checks.
