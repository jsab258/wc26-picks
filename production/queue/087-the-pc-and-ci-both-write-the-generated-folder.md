line: infrastructure (the PC channel)
spec: found 2026-09-04 when UPDATE FROM CLAUDE.bat aborted a pull for Jafar
acceptance: a pull on the PC after a local generation run succeeds without a human moving files by hand; proven by planting the exact collision (an untracked generated file that an incoming commit also carries) and watching the update path survive it
max_sessions: 1
status: READY 2026-09-04. engine-specialist, small. THIS BLOCKS JAFAR AT THE MOMENT HE MOST WANTS THE PULL, so it outranks its size.

## What happened, verbatim from his screen

    error: The following untracked working tree files would be overwritten by merge:
            ledger/Assets/StreamingAssets/Decals/generated/PROGRESS.txt
            ledger/Assets/StreamingAssets/Decals/generated/made.json
    Please move or remove them before you merge.
    Aborting

He was pulling to get the Telegram bot. The update stopped and he had to be
told what to type.

## The collision, which is a design fault and not an accident

TWO WRITERS OWN ONE DIRECTORY. The imagegen run on his PC writes
`PROGRESS.txt` and `made.json` there as it works, untracked and local. CI also
COMMITS its own copies of the same paths, in this instance in the commit
`Meridian pictures from 991aabf`. Git refuses to overwrite an untracked file
with a tracked one, correctly, so every pull after a local run aborts until a
human intervenes.

This will happen again on every single local generation run followed by a
pull. It is not rare and it is not his fault.

## The specific danger, and why the fix is not "delete them"

`made.json` is the RESUME RECORD. Its own first line reads: "Delete this file
to have everything made again, or delete one PNG to have just that one made
again." The run it describes took 56 minutes and produced 41 plates. An
instruction that says delete, given in a hurry, costs an hour of his GPU and he
would have no way to know until the next run started remaking everything.

So the safe instruction is MOVE, and the safe fix must not depend on anyone
remembering that.

## Routes, and the question to settle first

The question is which writer owns those two paths, and it must be answered
before anything is changed:
- If they are LOCAL RUN STATE, they belong in `.gitignore` and CI must stop
  committing them. The pull then never collides.
- If they are EVIDENCE that CI is right to commit, then the PC must write its
  own copies somewhere else, outside the tracked tree.

Do not pick by taste. Look at who reads them: if any tool or gate reads the
committed copy, they are evidence; if only the next local run reads them, they
are run state. Print the readers rather than asserting them.

## The update path needs a guard either way

`UPDATE FROM CLAUDE.bat` should detect this exact abort and either resolve it
by moving the offending files aside with a suffix and saying so, or print the
move commands ready to paste. Failing with a raw git error and "tell Claude
what it printed" is the behaviour that cost this round trip.

## Both halves

Accepting: plant an untracked file at a path an incoming commit carries, run
the update path, and watch it complete with the local file preserved under a
new name and named on screen.
Rejecting: a genuine local EDIT to a tracked file must still stop the pull
rather than being silently moved aside, because that is real work and the
whole point of the abort.
