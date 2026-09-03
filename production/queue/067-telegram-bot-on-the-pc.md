line: production (the channel)
spec: Jafar's Director's Console rulings, 2026-09-03. FIRST ITEM AFTER THE MONDAY RESET.
acceptance: the bot runs on the PC and, proven by a real run on Jafar's machine rather than by a selftest here, (1) pushes a Blocking item within a minute of it being routed, (2) sends the morning brief, (3) sends every new gallery item as an image with one caption line, (4) sends decision cards whose option buttons WRITE THE RULING into production/decision-queue.md, (5) requests the budget reading with numeric quick-replies for BOTH meters, at most twice a day and only when the next batch would approach the ceiling, (6) accepts typed notes and voice memos, transcribed locally, filed against the item they answer
max_sessions: 2
status: READY 2026-09-03, BLOCKED on Jafar creating the bot and providing its token and chat id (decision-queue card, due before Monday 14:00). engine-specialist or content-wrangler.

## The one rule that makes it the channel and not a notifier

IT IS THE SEND PATH AND IT CALLS `tools/producer-check.py` ITSELF. Nothing
unchecked leaves. Today the resident runs the check by hand, which works only
while a human remembers; when this lands, forgetting stops being possible.

## Its silence is the dead-man signal

Ruled 2026-09-03, replacing the third-party ping that runner.md used to offer.
If the bot goes quiet the studio is down, and that is the signal rather than an
absence of one. This is also why the liveness row (queue 066) is pulled and
never pushed: a heartbeat is banned from the register, so the console carries
liveness and the bot's silence carries death.

## What cannot be tested here, said plainly

Every external host is blocked from the build container, so NOTHING in this
item can be exercised where it is written. Its first real run on Jafar's PC is
its accepting case, exactly like every .bat in this repo. Write it so that
first run is maximally informative: one dispatch that answers every question it
can rather than a series of blind attempts, which is the lesson fifteen CI runs
paid for on the voice corpus.

## Configuration

Token and chat id live in the uncommitted `tools/runner/config.local`, which
already exists as the pattern. Neither is ever committed, printed, or included
in an error message.
