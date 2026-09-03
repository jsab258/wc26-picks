line: infrastructure (the guards)
spec: found 2026-09-03 while asking why "22 queue items ready" had not moved in a day
acceptance: the queue-depth gate reads production/queue/ and its printed count changes when a file is added there; plus a rejecting case proving the FLOOR can still fire, planted by pointing the tool at a fixture tree with too few ready items
max_sessions: 1
status: READY 2026-09-03. instrument-builder. SCOPE CEILING: repoint the tool and prove both outcomes. Migration of any remaining content out of the retired file is a SEPARATE reported next step, not this task.

## The fault

`tools/queue-check.py` line 38:

    QUEUE = ROOT / "game-design" / "queue.md"

That file was SUPERSEDED BY THE V2 RESPEC ON 31 AUGUST. The live queue is
`production/queue/`, said by CLAUDE.md line 137 and by the watchdog prompt in
those words. So the queue-depth gate that runs inside `ledger/verify.py` on
every commit has spent four days measuring a retired document.

Counted rather than asserted, 2026-09-03:

    queue-check:                    22 item(s), 22 ready to start now
    production/queue/*.md on disk:  70 files
    of those, `status: READY`:      47

The gate has never seen one of the 47. Three items were added to the live
queue today (076, 077, 078) and the printed number did not move, which is what
prompted the look. A reading that cannot move is the fault this project has a
standing rule about, and here the cause is not a frozen sampler but a tool
pointed at the wrong world.

## Why this is dangerous in the quiet direction

The gate exists so the queue cannot run dry unnoticed. Read the failure the
right way round: if `production/queue/` emptied completely tomorrow, this gate
would stay GREEN, because its 22 items live in a file nobody works from any
more. It cannot warn about the thing it was built to warn about. The noisy
direction (a false QUEUE TOO THIN) would at least announce itself.

Note also that `ledger/verify.py` mentions `production/queue/` exactly once,
at line 3930, and that is a cadence-scope FIXTURE string rather than a reading.
Nothing in the verification suite counts the live queue at all.

## What the fix must not do

Do not delete or empty `game-design/queue.md` as part of this. Its content is
a separate question and this task is about where the gate looks. Deleting it
would also make the fix untestable against the before state.

## Both outcomes, accepting first

Accepting: point the tool at `production/queue/`, run it, and show the count
matching a number counted independently on the same tree. Then add one file
and show the count move by one. That second half is the part that proves the
reading is live rather than merely different.

Rejecting: the FLOOR must still be able to fire. Point the tool at a fixture
directory holding fewer ready items than the floor and show it refuse, with
the count named. A gate that cannot fail is the ratchet, and repointing a
ratchet at fresh data leaves it a ratchet.
