# Phase 3: Customer Lead Ingestion

Status: Not started. Target: 75 minutes. Dependencies: Phases 1–2.

## Outcome

Both workflows produce valid, deduplicated leads with accurate rejection and warning counts.

## Work

1. Load workflow schemas and map normalized headers against field names and aliases. Ignore unmatched columns.
2. Normalize supported phones, dates, non-negative decimals, strings, and enums exactly as the assignment specifies. Use `Decimal`, not floating point, for money.
3. Skip fully blank rows. Number only nonblank data rows, starting at one.
4. Validate fields in schema order. Keep one rejection reason: the first required-field failure or invalid phone. Store row location and reason without PII.
5. Convert invalid optional values to null. Count warnings only after the row is accepted.
6. Merge by workflow and canonical phone. Preserve original batch; later valid rows overwrite only non-null fields.
7. Keep missing optional values distinct from defaults. Resolve defaults after merging so a later blank language never overwrites an existing language.
8. Persist input row, rejection, duplicate-merge, and warning counts once per imported source.

## Completion checks

- [ ] Both schema files drive the same generic ingestion path.
- [ ] Header aliases, date formats, phone formats, and currency prefixes work.
- [ ] Impossible dates and invalid optional fields produce the right results.
- [ ] Rejected rows produce no leads or field-warning counts.
- [ ] Multiple failures select the first rejection in schema order.
- [ ] Duplicate merging preserves first batch and previous non-null values.
- [ ] Re-ingesting a source changes neither records nor counters.

## Evidence

Pending: record normalization and merge test results plus sample import counts without customer information.
