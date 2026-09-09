line: instrument
spec: tools/lint-bootstrap-single.py now proves every self-hosted workflow CALLS the PATH
  bootstrap. It does not prove the call is in a position where it can work. Two orders defeat
  a present call: before any checkout, when the script is not on disk yet, and after the first
  pwsh or bash step, which is the step that needs it. Assert the order and print it per
  workflow.
acceptance: the live tree passes with every workflow's checkout, bootstrap and first shell
  step positions printed, and two planted fixtures fail: one calling before the checkout, one
  calling after the first pwsh step.
max_sessions: 1
status: READY 2026-09-09. BUILT AND THEN DELIBERATELY REMOVED the same session, green at 9 of
  9 on the live tree, because the builder was told to finish the critical path rather than
  deepen. It is filed rather than lost, and it is filed because it is the NEXT VARIANT of the
  fault that cost a render today: the lint proved a property nobody had checked, and the
  property it did not prove is the one a careless edit breaks next.
  The measurement it produced is worth keeping in the item: all nine self-hosted workflows
  currently read checkout=1 bootstrap=2 firstPwshBash=3.
