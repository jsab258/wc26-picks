line: infrastructure (the Producer loop, the accepting case)
spec: production/NOW.md, "JAFAR'S STANDING ORDER, 2026-09-05", item 1, ACCEPTING CASE clause
acceptance: one supervised run of his exact accepting case, recorded in a dated evidence file where each of the four steps carries its instant and `stepLatencySec` from the previous row's instant AND a committed artifact path or sha read back out of git rather than off disk, printing stepsProven=N/4; a step whose artifact cannot be cited makes the recorder REFUSE to write that line rather than writing an uncited one, proven by planting a missing artifact; a run that did not happen prints the words "nothing measured" with stepsProven=0/4; the run uses the wake route as it will stand on Sunday, and the file names which route that was
max_sessions: 1
status: READY 2026-09-05. LAST of item 1, and it is the week's judged test. instrument-builder or artifact-reader, with Jafar present for two minutes.

## His words, which are the specification

"He sends a question from his phone and gets a register-compliant answer back,
and he taps a button and the queue shows the ruling."

Four steps. Nothing here may substitute a selftest for any of them, and nothing
may substitute the resident's memory of having seen it work. The whole console
is judged on Sunday by whether he can run the week from one Telegram thread, so
this is the instrument for that judgement and not a formality.

## What the evidence file holds

One dated file, banner in the form `tools/docs-check.py` accepts, four rows:

    question   instant, the inbox file the message landed as
    answer     instant, the outbox file and the producer-check verdict for it
    tap        instant, the ruling record
    ruling     instant, the diff to production/decision-queue.md

Each row cites an artifact by path and sha, and the sha is resolved with git
rather than by reading the working tree. That distinction has cost this project
a session once already: a mover that read the working tree silently rewrote the
thing it was proving.

No chat id, no token, no config path in the file. The credential rule ruled
2026-09-04 binds here as everywhere.

## What this is NOT allowed to do

It does not fix anything it finds. If a step fails, the file records the
failure with its denominator and the item goes back to 088, 089 or 090 by name.
A round trip that half worked and was patched mid-run proves nothing about the
path Jafar will use on Sunday.

## Both halves, accepting first

Accepting: the four rows, four artifacts, `stepsProven=4/4`, with the answer's
row naming the register kind it was checked against.

Rejecting: plant a missing artifact for one step and show the recorder refusing
to write that row, so the file cannot claim a step that left no trace. And a
run that never started writes `stepsProven=0/4` and the words "nothing
measured" rather than an absent file, because an absent file reads as nobody
having tried.

## Depends on, and what it blocks

Depends on queue 088, 089 and 090, all three. Blocked until all three land, and
it must not be started on two of them. Blocks nothing, but it is the gate on
whether item 1 is done, and the Sunday judgement reads it.
