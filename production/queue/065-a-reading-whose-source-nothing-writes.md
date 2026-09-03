line: infrastructure (instruments)
spec: game-design/decision-2026-09-03-directors-console-step-2.md, ruling C
acceptance: a check that fails when any live reader derives a value from a file nothing writes any more; it names the reader, the dead source and the date the source was retired; shipped with its selftype fixtures, accepting case first (a reader pointed at a written file passes) and rejecting (a reader pointed at a retired one fails)
max_sessions: 1
status: READY 2026-09-03. instrument-builder. Found by one repoint leaving three readers behind.

## The finding

The dashboard's needs-you count read `game-design/decisions-pending.md`, a
file the project had stopped writing to. It was correct on the day it was
caught ONLY BY COINCIDENCE: the retired file still carries the same card as
history, so the two agreed at that instant and would have diverged silently
the moment a card was added to the queue or struck from the old file.

Repointing the dashboard did not discharge it. A director reading the tree
found THREE more readers still on the dead file: the console artifact itself,
which was repointed at the source and never regenerated; the process rule in
`operations.md` for "anything needing him"; and a READY queue card. All three
are now fixed, and finding them by hand is the argument for the check.

## Why the existing machinery does not cover it

The `SOURCES` list handles a file that MOVED. This is a file that STAYED and
stopped being written. Constitution law 8 says a stale document is a failing
test and nothing enforces it for this shape: a reader can point at a real,
present, parseable file forever after that file stopped meaning anything.

A retired file is the dangerous case precisely because it still parses.

## The shape

Retirement should be declarable rather than inferred: a file that carries a
RETIRED banner with a date is the rejecting fixture, and any live reader
naming it is the failure. Inferring "nothing writes this" from history is the
harder version and is not what this item asks for.
