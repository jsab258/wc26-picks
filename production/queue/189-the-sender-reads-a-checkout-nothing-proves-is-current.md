line: infrastructure (the channel)
spec: The outbox sweep step and the decision-cards step in
  ledger-install-supervisor-task.yml assert that the checkout they read CONTAINS the
  commit the run was started for, print both shas, and REFUSE to send when it does not.
acceptance: a run whose checkout is behind refuses with both shas named and sends
  nothing; a run whose checkout contains the run's commit sends normally. Both watched,
  the accepting case first.
max_sessions: 1
status: READY 2026-09-09, and it is BLOCKING for the channel being actionable.
  MEASURED, on the first real cards pass: it sent six cards from the queue as it stood
  BEFORE that morning's edits, including one card the studio had deliberately withdrawn
  and missing the two added that day, printing waitingTotal=6 where the branch said 7.
  THE CAUSE IS A DEFERRAL, NOT A BUG. install-scheduled-task.ps1:153 skips the CI resync
  while a supervisor is running, correctly, because pc-watcher resyncs every pass. That
  makes freshness another process's property on another process's timer, and the sending
  steps read the checkout with nothing asserting it is current. Push at 08:41, step at
  08:42:29.
  LINE 1 OF THE EVIDENCE FILE IS TRUE AND MISLEADING TOGETHER: it names the commit CI
  ran FOR, not the commit the checkout was AT. Until now nothing needed to tell those
  apart, and .claude/rules/ci.md's rule that line 1 names the commit is satisfied by the
  wrong one of the two.
  REFUSING COSTS ONE ROUND TRIP. Sending cost him a card he cannot act on and hid the
  one he had asked for that morning.
