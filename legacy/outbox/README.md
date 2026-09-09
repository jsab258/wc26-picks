# Retired outbox messages

STATUS: LOG. A message here was written, never sent, and can no longer be sent.

WHY IT IS UNDER legacy/ AND NOT UNDER production/outbox/, decided after two
attempts that each failed a gate and each failure was the gate working. The
producer register walks the outbox tree and requires EVERY .md in it to carry a
register suffix or be a README; a retired message carries neither, so it failed
with "the name carries no register" wherever in that tree it sat. Before that, a
name ending .expired produced a file kind no rule classified and the attribution
check said so: "1 unclassified of 4819 walked: .expired x1". THE ANSWER IS THAT A
RETIRED MESSAGE IS NOT AN OUTBOX FILE AT ALL. It leaves the tree, keeping a known
extension, and legacy/ is where this project already puts superseded text.

WHY THE DIRECTORY EXISTS, added 2026-09-09. The sweep tries every file in
`production/outbox/` on every pass and writes a refusal record for each one it
cannot send. One message, `2026-09-03-batch-landed-and-the-wait.unprompted.md`,
had accumulated 483 refusal records by 9 September: it fails four register rules
at once, including a deadline 70 hours in the past, and it is marked HISTORICAL
in its own first line because the Unreal run it asks about is gone and the street
it promised now shows its textures. IT CANNOT EVER BE SENT, and every sweep was
paying to discover that again and writing a file to say so.

THE GUARD WAS NOT WRONG. Refusing a message whose deadline has passed is the
register working, and the 483 records are 483 correct decisions. What was wrong
was leaving the input in front of it for six days.

HOW A FILE IS RETIRED, and it is a RENAME rather than a marker or an exemption.
The register reads a message's kind off its NAME SUFFIX, so a file ending
`.unprompted.md` is an unprompted message wherever it sits, and moving it into
this directory left it in the register's scope and failing. So the register suffix is
REPLACED rather than appended to: `...batch-landed-and-the-wait.unprompted.md`
becomes `...batch-landed-and-the-wait.EXPIRED.md`. That takes it out of the
register's suffix match and the sweep's glob with no edit to the message itself,
no marker inserted into a historical text and no new exemption in the checker.
THE NAME IS THE MECHANISM, which is the same rule this project uses for staging
evidence.

AND THE EXTENSION STAYS `.md` ON PURPOSE. The first attempt appended `.expired`,
which produced a file kind no rule classified, and the attribution check caught it
at once: "every file kind walked is ruled asset or not-asset (1 unclassified of
4819 walked): .expired x1". A retirement that invents an extension buys a second
problem. Keep a known one.

WHAT MOVING A FILE HERE MEANS: the message is kept, because a message that was
written is part of the record whether or not it crossed, and it is out of the
sweep's path. It is never edited to make it sendable; a superseded message is
rewritten as a NEW message with today's facts, or it is not sent at all.
