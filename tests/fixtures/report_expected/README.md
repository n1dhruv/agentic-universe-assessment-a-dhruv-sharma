# Hand-calculated report expectations

These files were calculated from the explicit six-customer fixture in `test_reports.py`, not generated from the implementation's output.

- Motor customers A, B, C, D belong to batch 001. E belongs to batch 002. Feedback customer F belongs to batch 001.
- A has two connected calls. A's first call starts one minute before IST midnight. Its override removes success even though a later ordinary set says renewed. A's second call starts after midnight and succeeds.
- B has two telephony-failed calls. C has a failed call, a connected callback-request call, then a new call without an outcome. C keeps the callback as current disposition while last call time advances.
- D has connected/outcome events but no initiated event, so D has zero counted calls. E has two successful calls on one day but contributes one distinct successful customer. F has one successful feedback call.
- On October 2 the motor workflow has seven calls: one A, two B, two C, and two E. Four connected. Successful customers are A and E, so the rate is `0.5714` and success count is two.
- Inputs contain eight nonblank lead rows: six unique accepted customers, one rejected row, and one duplicate A row. E's optional date and language are invalid, producing two warnings.
- Events contain 34 nonblank lines: 32 unique events, one duplicate, and one malformed line. Two unique orphan events and one linked unknown disposition stay outside business reports.
