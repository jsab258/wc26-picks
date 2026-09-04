line: infrastructure (the Producer register)
spec: game-design/decision-2026-09-04-ruling-077-deadline-clock-pin.md, section 2
acceptance: a message accepted by the pre-send check carries a machine-written accepting instant, the gate measures its deadlines from that instant rather than from midnight, and a message with no stamp is refused by the gate with the reason named; both cases as fixtures, accepting first
max_sessions: 1
status: READY 2026-09-04. instrument-builder, small.

## The gap the pin does not close

Queue 077 pinned the gate's clock to the ISO date in each filename, and that
was the right fix for the landmine: the gate's reading is now always LARGER
than any send-check reading taken later the same day, so an accepted send can
never go red at commit. Midnight was chosen for exactly that property and the
ruling upholds it.

But a date is a day, not an instant, and that is the residue. A writer who
never runs the pre-send check can commit a file dated today carrying a
next-day ISO deadline at 23:00. The gate reads that as 09:00 the following
morning against midnight today, so 33.0 hours, comfortably over the floor,
while the real headroom is about 10 hours. The floor is stated in hours and
the gate is measuring days.

## Why this is a rule 6 gap and not a rounding complaint

NOTHING IN THE TREE PROVES THE SEND CHECK EVER RAN. It is a command a human
types, its result reaches no file, and the gate cannot tell a message that
passed it from one that skipped it. Built is not running: the send check is
built, and no gate proves the call happened.

## The fix, and the reason it is a stamp rather than a flag

On acceptance the single-file check writes its accepting instant into the file
(`checked-at:` or equivalent), MACHINE-WRITTEN, and the gate pins that file's
deadlines to the stamp rather than to midnight. A stamp cannot be forged by
retyping because the check writes it only on a pass, which is the property the
077 ruling required when it rejected a hand-set exemption marker.

A file with no stamp must be REFUSED by the gate rather than falling back to
midnight, or the fallback becomes the bypass and this task has moved the hole
rather than closed it.

## Both halves, accepting first

Accepting: run the send check on a real message, show the stamp appear, then
run the gate at several clocks and show the same verdict each time with the
stamp named in the per-file line.

Rejecting: a message with a deadline and no stamp is refused, and the finding
says which. Also plant the 23:00 case above and show that it is now refused on
its true headroom rather than accepted on a day boundary.
