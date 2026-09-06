line: studio (the documents gate)
spec: observed twice on 2026-09-06, both times by the resident applying a
  ruling's own amendments.
acceptance: a director's banner cannot place NOT CURRENT outside the window
  docs-check reads, either because the checker says where it looked or because
  the shape is given once and reused
max_sessions: 1
status: READY 2026-09-06. Small, and it is the third time a fixed window has
  cost this project a red for a document that was correct.

## What happened, twice in one day

`tools/docs-check.py` requires the string NOT CURRENT inside `WITHIN_LINES`,
which is 8. Both of today's ruling records wrote a full and accurate banner in
which the phrase landed on line 9 or later, because the banner names the files
the ruling covers and that list is long. Both went red. Both were fixed by
moving four words up.

The documents were never wrong. The checker looked at the first eight lines and
reported what it did not find there as though it were not there at all.

## Why this is not "tell directors to be careful"

They were careful. The banner is written to name what the ruling covers, and a
ruling that covers twelve files has a long banner. The instruction "put NOT
CURRENT in the first eight lines" is a rule about a number nobody reading a
banner is thinking about.

## Two shapes of fix, and the second is better

The checker could say where it looked: "NOT CURRENT not found in the first 8
line(s) of 40 read". That turns a wrong-looking failure into a clear one and
costs one string. It does not stop the failure recurring.

Better: the banner's first three lines are the same shape in every record.
Give that shape once, in the template the directors already follow, with the
status words on the line the checker reads and the file list below it. Then the
window never binds, because nothing long ever precedes it.

## The rule this is an instance of

A FIXED WINDOW IS A BOUND, and this project's own law says a bound must be
measured and must announce when it bites. WITHIN_LINES=8 was neither. It bit
twice today in silence, and the only reason it was cheap is that a human was
reading the failure both times.
