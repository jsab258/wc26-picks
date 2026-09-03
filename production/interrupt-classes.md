# Interrupt classes and routing

STATUS: LIVE. Ruled by Jafar 2026-09-03 (the Director's Console). Read by the
Producer before anything is sent, and by the dashboard when it decides what
belongs on the glance. The class is a FIELD on a decision-queue card, not a
judgement made at send time, so routing is data.

## The four classes

| class | what it means | route | pushed? |
|---|---|---|---|
| BLOCKING | the studio has stopped, or is about to do something irreversible | Telegram, now | yes |
| DECISION | a real fork with a safe default | the morning brief | no |
| REVIEW | something to look at | the weekly | no |
| FYI | worth recording, needs nobody | the console only | never |

BLOCKING is the only class that pushes. Everything below it is PULLED: it
waits on the console, or it rides the next brief. A thing that could have
waited until morning and did not is a process fault, not a courtesy.

IRREVERSIBLE ITEMS WAIT FOR JAFAR BY DEFAULT AND NEVER GUESS. An irreversible
step with no ruling is BLOCKING and the studio stops in front of it; it does
not pick the safe-looking option and report afterwards. This is the one place
where stopping is cheaper than being wrong, because the class exists precisely
for the actions that cannot be undone.

A DECISION card carries what the queue already requires of every card: two to
four options, a recommendation, a default if he says nothing, and a deadline
no shorter than 24 hours. A card with a safe default is a DECISION. A card
with no safe default is BLOCKING, and the absence of the default is what makes
it one.

## The field

Every card in `production/decision-queue.md` carries one line:

    CLASS: BLOCKING | DECISION | REVIEW | FYI

Missing is not a class. A card with no CLASS line is UNCLASSIFIED and is
reported as unclassified by every reader, never quietly routed as FYI, because
a default route is how a Blocking item ends up on a page nobody opened.

## The record, and why it exists before any threshold

Every routed interrupt appends one row to `production/interrupt-log.tsv`.
`tools/blocking-count.py` reads that record and prints Blocking pushes per
week, with the count of what it walked.

Jafar ruled that more than two Blocking pushes in a week is a process fault to
be investigated and not a tolerance to raise. THAT BOUND IS NOT SET YET AND IS
NOT A GATE. The counter ships first and prints the series; the number gets
read off real weeks. Rule 2: no threshold this project has not measured.

The same record carries a DISPUTE column, because Jafar ruled that
Producer-versus-resident disagreement about what is Blocking is a health
metric. A row records the disagreement when the two disagreed about its class.
Until rows exist, the counter prints the words nothing measured for that
figure rather than a zero: zero disagreements and nobody writing them down
look identical otherwise, and only one of them is good news.
