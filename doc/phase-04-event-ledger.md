# Phase 4: Event Ledger and Late Linking

Status: Not started. Target: 75 minutes. Dependencies: Phases 1–3.

## Outcome

A deduplicated event history that handles out-of-order delivery and customers arriving later.

## Work

1. Read nonempty JSONL lines and count each physical input line once per source. Count malformed JSON and missing event IDs as malformed.
2. Apply event ID deduplication before link and disposition classification. First observed event wins; duplicate deliveries increment the duplicate counter.
3. Store unique original events encrypted and append-only, including currently unmatched or unknown-disposition events.
4. Normalize UTC, explicit-offset, and naive timestamps. Naive timestamps mean IST; store comparable instants internally.
5. Resolve ordinary events through workflow and normalized phone HMAC. Resolve overrides through workflow and call ID, regardless of line arrival order.
6. Reconsider unresolved links over all stored data after later imports. Do not edit original ledger bodies to attach leads.
7. Compute final-state orphan counts before unknown-disposition counts, respecting the contract's classification precedence. Match disposition codes against the supplied workflow catalogue.
8. Keep source-level line, malformed, and duplicate counts separate from classifications that can change after new data arrives.

## Completion checks

- [ ] Duplicate IDs within and across drops count once in the ledger.
- [ ] Overrides arriving before ordinary call events eventually link.
- [ ] Events become report-eligible when a later lead arrives.
- [ ] Permanent orphans remain excluded from business reports.
- [ ] Unknown dispositions do not influence call outcomes.
- [ ] Final orphan counts shrink correctly after late linking.
- [ ] Re-importing a drop changes no counts or ledger records.

## Evidence

Pending: record late-linking, ordering, deduplication, and classification tests.
