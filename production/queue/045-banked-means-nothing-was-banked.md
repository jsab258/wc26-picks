line: infrastructure (instruments, the imagegen evidence channel)
spec: this file, from imagegen run 2
acceptance: BANKED is true only when the pictures it names are IN THE COMMIT; a run that generates and commits nothing reads as its own state and never BANKED; remade counts what was remade; both outcomes fixtured against a real commit, not a directory listing
max_sessions: 1
status: READY 2026-09-02. engine-specialist. BLOCKS the free lane: until this is right, a green verdict cannot be trusted to mean pictures exist.

## What run 2 actually did

Run 2 (commit `c685aa93`, "Meridian pictures from 11bc1c1") reported
`steps selftest=success,probe=success,generate=success,attribution=failure,
shaFrom=checkout,stopper=none` and
`done imagegenVerdict=BANKED why=none wroteThisRun=4 failed=0 blankThisRun=0
remade=0`.

THE STOPPER FIX WORKED. `stopper=none` and `shaFrom=checkout` are exactly
what run 2 was dispatched to prove, and it proved them. Generation ran on
the GPU for real: `made.json` records `fascia_mickeys`, `fascia_ritas_pawn`,
`fascia_fish_market` and `fascia_steam_laundry` as "made by this run" at
19:50 to 19:52.

## Fault 1: BANKED, and nothing was banked

`git show --name-only c685aa93 | grep -c png` returns **0**. The commit
carries `manifest.json`, `made.json`, `PROGRESS.txt`, the verdict and the
machine report, AND NOT ONE PICTURE. The four PNGs on disk in this checkout
are the ones committed on 26 August by an earlier run (`cb332751`), not the
ones the GPU made tonight.

So the verdict's headline word is false in the only sense that matters. It
measured the runner's output DIRECTORY, which had the files, rather than the
COMMIT, which did not. A word that means "safely stored" was applied to work
that exists nowhere but a machine nobody can reach.

This is the fault this project exists to catch, arriving inside the newest
instrument on its first successful run. The blank-PNG guard was built with
enormous care and it guarded the wrong boundary.

## Fault 2: remade=0 while four were remade

`remade=0` sits on the same line as `wroteThisRun=4`, and `made.json` says
all four were "made by this run" while all four already existed on disk from
26 August. Either the run remade four files and did not count them, or
`--limit`'s promise that "an item already on disk is skipped for free" did
not hold and four generations of GPU time were spent reproducing what was
already there. Both readings are bad and the numbers cannot tell them apart.

`manifest.json` also carries `status: INCOMPLETE` while the verdict says
BANKED. Two files, one run, opposite claims.

## Also unexplained

`attribution=failure`, not diagnosed here.

## The fix

1. BANKED requires the named pictures to be in the commit. Measure the
   staged set or the commit, never the working directory. A run that
   generates and commits nothing gets its own state with its own word.
2. `remade` counts what was remade, and the accepting fixture is a run that
   remakes something.
3. Reconcile `manifest.status` with the verdict, or say in both which one is
   authoritative and why.
4. Diagnose `attribution=failure`.

## Do not

Do not fix this by making the verdict quieter. The verdict was loud and
precise and wrong about the one word a reader acts on.
