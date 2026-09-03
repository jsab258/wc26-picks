line: infrastructure (the Producer register)
spec: found by the Producer 2026-09-03 while writing the first real message; confirmed by the resident against the code before filing
acceptance: production/outbox/2026-09-03-batch-landed-and-the-wait.unprompted.md passes the gate at a simulated now of 2026-09-08, with a rejecting case proving a message still AWAITING an answer is still refused for a short deadline
max_sessions: 1
status: READY 2026-09-03. URGENT: the live tree goes red at 2026-09-05T09:01Z with nobody touching it. instrument-builder.

## The fault, proven rather than argued

`tools/producer-check.py` line 488 calls `deadline_hours(item["deadline"], now)`
where `now` is wall-clock, fed from `datetime.datetime.now()` in `main`. A
`DEADLINE 2026-09-06.` line measures to 09:00 on that date, and
`MIN_DEADLINE_HOURS = 24` refuses anything under a day.

Run against the real function, not from reading it:

    2026-09-03T16:30  hours=  64.5  PASS
    2026-09-05T08:00  hours=  25.0  PASS
    2026-09-05T09:00  hours=  24.0  PASS
    2026-09-05T09:01  hours=  24.0  FAIL

The gate runs inside `ledger/verify.py`, so from 09:01 on 5 September the
footer is deleted and NO COMMIT CAN LAND until someone edits a message that
was correct when it was written and has since been served.

## Why the selftest cannot see it, which is the more general fault

Every selftest calls `check(..., FIXTURE_NOW)` with a frozen
`datetime.datetime(2026, 9, 3, 12, 0)` (line 695). A frozen clock is right for
a fixture and is exactly why this class of fault survives: the accepting case
was watched at one instant and the instrument is read at every instant after.
The rule is a guard whose input includes the current time, and no case in the
suite advances it.

## What the rule is FOR, and the distinction it does not draw

The bound exists so the Producer cannot hand Jafar a decision with four hours
on it. That is a property of a message ABOUT TO BE SENT. Once a message is
sent, the deadline is a historical fact and re-checking it against the clock
asks whether a served deadline is still in the future, which is not a
question about quality. The README rules that sent messages STAY in the
outbox, so every message this project ever sends will eventually hit this.

## Two routes, and a preference

1. A SENT MARKER the gate honours: the deadline rule is skipped for a message
   already sent, and the marker is machine-written by the sender rather than
   typed, so it cannot be used to wave a draft through.
2. PIN THE GATE'S CLOCK to the message's own date prefix, so a file dated
   2026-09-03 is always checked as it was on 2026-09-03.

Route 2 is preferred: it needs no new state, it makes the check idempotent
over time by construction, and the date is already in the filename because the
naming convention put it there. Route 1 adds a flag that can be set wrongly.
The single-file check keeps wall-clock `now`, because there the question
really is "is this deadline far enough away to send".

## The test that must exist, both halves

Accepting: the live message above, at a simulated now of 2026-09-08, passes.
Rejecting: a message dated today with a deadline four hours out is still
refused by the single-file check. A fix that makes both cases pass has
disabled the rule rather than repaired it.
