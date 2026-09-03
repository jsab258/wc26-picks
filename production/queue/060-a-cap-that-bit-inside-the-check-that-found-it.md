line: infrastructure (the evidence channel)
spec: this file
acceptance: (1) the attribution check's failure text announces its own cap in the standing form, `(+N more not shown)`, with N measured rather than implied; (2) the same sweep over every check whose text reaches the verification footer: any that can truncate a list must announce it, and the sweep reports how many checks were examined and how many could truncate, so a zero here carries its denominator; (3) a rejecting fixture with more offending files than the cap allows, watched to print the notice, and an accepting fixture under the cap, watched to print no notice, accepting case run first
max_sessions: 1
status: READY 2026-09-03. instrument-builder, small. Found 3 September when the check went red on the Unreal frames.

## The finding

`tools/attribution-check.py` went red because five Unreal frames landed in a
directory it had never seen. Correct behaviour, and the message it put in the
verification footer read:

    ATTRIBUTION: no asset files live outside a directory this file knows
    about (2763 asset file(s) of 3972 walked, ex...

It stops at `ex...`. The five filenames, which are the entire actionable
content of the failure, are not in it. They were recovered only by running
the checker directly, outside the channel a commit is supposed to be judged
from.

## Why this one is worth a queue item rather than a shrug

THE STANDING RULE IS THAT EVERY CAP ANNOUNCES WHEN IT BITES, and it exists
because of a `| head -N` that outgrew its input and read as "three of five
systems failed" when nothing was broken. This is the same fault in the
opposite direction: not a number made wrong, but a fault made unreadable.

It is worse than the average instance for two reasons. First, it is in the
FAILURE path, which is the one path whose whole job is to tell a reader what
to do next; a truncated success line costs curiosity, a truncated failure
line costs a diagnosis. Second, it happened inside a check that had just
worked perfectly, so the fault arrived wearing the clothes of a success and
would have been read as one.

## What made it visible

Nothing did. A reader who trusted the footer would have known only that
attribution failed for some file whose name begins with "ex", which is not
even a filename: it is the start of the word "examined". Guessing from that
prefix would have sent the next session hunting for a file that does not
exist.

## Not in scope

Do not widen the cap, and do not remove it. A footer that dumps an unbounded
list is the fault this cap was added to prevent, and swapping one failure for
its opposite is not a fix. The cap stays and it says what it ate.
